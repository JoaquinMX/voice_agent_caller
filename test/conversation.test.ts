import {
  createInitialState,
  getNextSlot,
  promptForSlot,
  finalSummary,
  MAX_ATTEMPTS,
} from '../src/conversation';

import { SlotName } from '../src/types';

describe('conversation helpers', () => {
  it('returns slots in order until confirmed', () => {
    const state = createInitialState();
    expect(getNextSlot(state)).toBe('nombre');
    state.slots.nombre.confirmed = true;
    expect(getNextSlot(state)).toBe('correo');
    state.slots.correo.confirmed = true;
    state.slots.numero_de_pedido.skipped = true;
    expect(getNextSlot(state)).toBeNull();
  });

  it('delivers varied prompts up to max attempts', () => {
    const prompts: string[] = [];
    (['nombre', 'correo', 'numero_de_pedido'] as SlotName[]).forEach((slot) => {
      for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt += 1) {
        prompts.push(promptForSlot(slot, attempt));
      }
    });
    expect(prompts).toHaveLength(9);
    expect(new Set(prompts).size).toBeGreaterThan(3);
  });

  it('summarizes captured information', () => {
    const state = createInitialState();
    state.slots.nombre.value = 'María López';
    state.slots.nombre.confirmed = true;
    state.slots.correo.skipped = true;
    const summary = finalSummary(state);
    expect(summary).toContain('nombre: María López');
    expect(summary).toContain('correo: lo dejamos pendiente');
  });
});
