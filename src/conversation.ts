import { ConversationState, SlotName } from './types';

export const SLOT_ORDER: SlotName[] = ['nombre', 'correo', 'numero_de_pedido'];

const slotPrompts: Record<SlotName, string[]> = {
  nombre: [
    'Hola, soy un asistente automático. ¿Cuál es tu nombre completo?',
    'No te escuché bien. ¿Puedes decirme tu nombre completo, por favor?',
    'Último intento, ¿cuál es tu nombre completo?'
  ],
  correo: [
    '¿Cuál es tu correo electrónico?',
    'Repite tu correo electrónico, por favor.',
    'Último intento, dime tu correo electrónico.'
  ],
  numero_de_pedido: [
    '¿Cuál es tu número de pedido?',
    '¿Me puedes dar tu número de pedido otra vez?',
    'Último intento, ¿cuál es tu número de pedido?'
  ],
};

export const stateByCallSid = new Map<string, ConversationState>();

export const MAX_ATTEMPTS = 3;

export function createInitialState(): ConversationState {
  return {
    slots: {
      nombre: { value: null, attempts: 0, confirmed: false, skipped: false },
      correo: { value: null, attempts: 0, confirmed: false, skipped: false },
      numero_de_pedido: { value: null, attempts: 0, confirmed: false, skipped: false },
    },
    currentSlot: SLOT_ORDER[0],
    pendingConfirmation: null,
  };
}

export function getNextSlot(state: ConversationState): SlotName | null {
  for (const slot of SLOT_ORDER) {
    const status = state.slots[slot];
    if (!status.confirmed && !status.skipped) {
      return slot;
    }
  }
  return null;
}

export function promptForSlot(slot: SlotName, attempt = 0): string {
  const prompts = slotPrompts[slot];
  const index = Math.min(attempt, prompts.length - 1);
  return prompts[index];
}

export function confirmSlot(slot: SlotName, value: string): string {
  return `Entendí: ${value}. ¿Es correcto?`;
}

export function finalSummary(state: ConversationState): string {
  const parts = SLOT_ORDER.map((slot) => {
    const status = state.slots[slot];
    if (status.value) {
      return `${slot.replace(/_/g, ' ')}: ${status.value}`;
    }
    return `${slot.replace(/_/g, ' ')}: lo dejamos pendiente`;
  });
  return `Resumen de la información: ${parts.join('. ')}.`;
}
