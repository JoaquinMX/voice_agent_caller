import express from 'express';
import { twiml } from 'twilio';

import {
  stateByCallSid,
  createInitialState,
  getNextSlot,
  promptForSlot,
  confirmSlot,
  finalSummary,
  MAX_ATTEMPTS,
} from './conversation';
import { ConversationState, SlotName } from './types';
import { isValidMxNumber, normalizeFreeText, parseEmail, isValidOrderId } from './validators';
import { makeOutboundCall } from './twilioClient';

const router = express.Router();

function ensureState(callSid: string): ConversationState {
  let state = stateByCallSid.get(callSid);
  if (!state) {
    state = createInitialState();
    stateByCallSid.set(callSid, state);
  }
  return state;
}

function interpretYesNo(text: string): 'yes' | 'no' | null {
  const normalized = text.toLowerCase().normalize('NFD').replace(/[^a-zñ\s]/g, '');
  if (!normalized.trim()) {
    return null;
  }
  const yesPhrases = ['si', 'sí', 'claro', 'correcto', 'así es', 'asi es'];
  const noPhrases = ['no', 'negativo', 'incorrecto'];
  if (yesPhrases.some((phrase) => normalized.includes(phrase))) {
    return 'yes';
  }
  if (noPhrases.some((phrase) => normalized.includes(phrase))) {
    return 'no';
  }
  return null;
}

function respondWithSlotPrompt(
  response: twiml.VoiceResponse,
  state: ConversationState,
  slot: SlotName,
) {
  const status = state.slots[slot];
  if (status.attempts >= MAX_ATTEMPTS) {
    status.skipped = true;
    status.value = null;
    return;
  }
  const gather = response.gather({
    input: 'speech',
    language: 'es-MX',
    speechTimeout: 'auto',
    action: '/voice/collect',
    method: 'POST',
  });
  gather.say({ language: 'es-MX' }, promptForSlot(slot, status.attempts));
  status.attempts += 1;
  state.currentSlot = slot;
  state.pendingConfirmation = null;
}

function respondWithConfirmation(
  response: twiml.VoiceResponse,
  state: ConversationState,
  slot: SlotName,
  value: string,
) {
  state.pendingConfirmation = { slot, value };
  const gather = response.gather({
    input: 'speech',
    language: 'es-MX',
    speechTimeout: 'auto',
    action: '/voice/collect',
    method: 'POST',
  });
  gather.say({ language: 'es-MX' }, confirmSlot(slot, value));
}

function handleSkip(
  response: twiml.VoiceResponse,
  state: ConversationState,
  slot: SlotName,
) {
  const status = state.slots[slot];
  status.skipped = true;
  status.confirmed = false;
  status.value = null;
  state.pendingConfirmation = null;
  response.say({ language: 'es-MX' }, 'Está bien, lo dejamos pendiente.');
  const next = getNextSlot(state);
  state.currentSlot = next;
  if (next) {
    respondWithSlotPrompt(response, state, next);
  } else {
    response.redirect('/voice/complete');
  }
}

function sanitizeOrderId(text: string): string | null {
  const compact = text.replace(/\s+/g, '').toUpperCase();
  if (isValidOrderId(compact)) {
    return compact;
  }
  return null;
}

function getInitialSlot(state: ConversationState): SlotName | null {
  if (state.currentSlot) {
    return state.currentSlot;
  }
  const next = getNextSlot(state);
  state.currentSlot = next;
  return next;
}

router.post('/voice/welcome', (req, res) => {
  const response = new twiml.VoiceResponse();
  const callSid = req.body.CallSid as string;
  if (callSid) {
    ensureState(callSid);
  }
  response.say(
    { language: 'es-MX' },
    'Hola, soy un asistente automático. Estoy aquí para ayudarte con tus datos.',
  );
  response.redirect('/voice/collect');
  res.type('text/xml').send(response.toString());
});

router.post('/voice/collect', (req, res) => {
  const response = new twiml.VoiceResponse();
  const callSid = req.body.CallSid as string;
  if (!callSid) {
    response.say({ language: 'es-MX' }, 'Ocurrió un problema con la llamada.');
    res.type('text/xml').send(response.toString());
    return;
  }
  const state = ensureState(callSid);

  const slotFromState = getInitialSlot(state);
  if (!slotFromState) {
    response.redirect('/voice/complete');
    res.type('text/xml').send(response.toString());
    return;
  }

  const speechResult: string = (req.body.SpeechResult || req.body.TranscriptionText || '').trim();
  const confidenceRaw = req.body.Confidence;
  const confidence = confidenceRaw ? Number(confidenceRaw) : undefined;

  if (state.pendingConfirmation) {
    const { slot, value } = state.pendingConfirmation;
    const status = state.slots[slot];

    if (!speechResult) {
      state.pendingConfirmation = null;
      if (status.attempts >= MAX_ATTEMPTS) {
        handleSkip(response, state, slot);
      } else {
        response.say({ language: 'es-MX' }, 'No escuché tu respuesta. Intentemos otra vez.');
        respondWithSlotPrompt(response, state, slot);
      }
      res.type('text/xml').send(response.toString());
      return;
    }

    const decision = interpretYesNo(speechResult);
    if (decision === 'yes') {
      status.value = value;
      status.confirmed = true;
      state.pendingConfirmation = null;
      state.currentSlot = getNextSlot(state);
      if (!state.currentSlot) {
        response.say({ language: 'es-MX' }, 'Perfecto.');
        response.redirect('/voice/complete');
      } else {
        response.say({ language: 'es-MX' }, 'Perfecto, continuemos.');
        respondWithSlotPrompt(response, state, state.currentSlot);
      }
      res.type('text/xml').send(response.toString());
      return;
    }

    state.pendingConfirmation = null;
    if (status.attempts >= MAX_ATTEMPTS) {
      handleSkip(response, state, slot);
    } else {
      response.say({ language: 'es-MX' }, 'Gracias por avisar. Intentemos de nuevo.');
      respondWithSlotPrompt(response, state, slot);
    }
    res.type('text/xml').send(response.toString());
    return;
  }

  const currentSlot = state.currentSlot as SlotName;
  const status = state.slots[currentSlot];

  const noSpeech = !speechResult;
  const firstAttempt = status.attempts === 0;

  if (noSpeech && firstAttempt) {
    respondWithSlotPrompt(response, state, currentSlot);
    res.type('text/xml').send(response.toString());
    return;
  }

  if (noSpeech) {
    if (status.attempts >= MAX_ATTEMPTS) {
      handleSkip(response, state, currentSlot);
    } else {
      response.say({ language: 'es-MX' }, 'No escuché ninguna respuesta.');
      respondWithSlotPrompt(response, state, currentSlot);
    }
    res.type('text/xml').send(response.toString());
    return;
  }

  if (confidence !== undefined && confidence < 0.6) {
    if (status.attempts >= MAX_ATTEMPTS) {
      handleSkip(response, state, currentSlot);
    } else {
      response.say({ language: 'es-MX' }, 'No estuve seguro de lo que dijiste. Vamos otra vez.');
      respondWithSlotPrompt(response, state, currentSlot);
    }
    res.type('text/xml').send(response.toString());
    return;
  }

  let normalizedValue: string | null = null;
  let valid = true;

  switch (currentSlot) {
    case 'nombre':
      normalizedValue = normalizeFreeText(speechResult);
      valid = normalizedValue.length > 0;
      break;
    case 'correo':
      normalizedValue = parseEmail(speechResult);
      valid = Boolean(normalizedValue);
      break;
    case 'numero_de_pedido':
      normalizedValue = sanitizeOrderId(speechResult);
      valid = Boolean(normalizedValue);
      break;
    default:
      valid = false;
  }

  if (!valid || !normalizedValue) {
    if (status.attempts >= MAX_ATTEMPTS) {
      handleSkip(response, state, currentSlot);
    } else {
      const messages: Record<SlotName, string> = {
        nombre: 'Disculpa, no entendí tu nombre.',
        correo: 'Ese correo no parece válido.',
        numero_de_pedido: 'No reconocí el número de pedido.',
      };
      response.say({ language: 'es-MX' }, `${messages[currentSlot]} Intentémoslo de nuevo.`);
      respondWithSlotPrompt(response, state, currentSlot);
    }
    res.type('text/xml').send(response.toString());
    return;
  }

  respondWithConfirmation(response, state, currentSlot, normalizedValue);
  res.type('text/xml').send(response.toString());
});

router.post('/voice/complete', (req, res) => {
  const response = new twiml.VoiceResponse();
  const callSid = req.body.CallSid as string;
  const state = callSid ? stateByCallSid.get(callSid) : undefined;
  const summary = state ? finalSummary(state) : 'No se registró información.';
  response.say({ language: 'es-MX' }, `${summary} Gracias. ¡Hasta luego!`);
  response.hangup();
  if (callSid) {
    stateByCallSid.delete(callSid);
  }
  res.type('text/xml').send(response.toString());
});

router.post('/dev/call', async (req, res) => {
  const to = req.body.to as string;
  const from = process.env.TWILIO_NUMBER as string;
  const publicBaseUrl = process.env.PUBLIC_BASE_URL;

  if (!to || !isValidMxNumber(to)) {
    return res.status(400).json({ error: 'Número destino inválido. Usa formato E.164 con +52.' });
  }
  if (!from) {
    return res.status(400).json({ error: 'Configura TWILIO_NUMBER en el entorno.' });
  }
  if (!publicBaseUrl) {
    return res.status(400).json({ error: 'Configura PUBLIC_BASE_URL en el entorno.' });
  }

  try {
    const call = await makeOutboundCall({
      to,
      from,
      url: `${publicBaseUrl}/voice/welcome`,
    });
    res.json({ status: 'queued', sid: call.sid });
  } catch (error) {
    console.error('Error creating call', error);
    res.status(500).json({ error: 'No se pudo iniciar la llamada.' });
  }
});

export default router;
