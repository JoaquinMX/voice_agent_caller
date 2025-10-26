export type SlotName = 'nombre' | 'correo' | 'numero_de_pedido';

export interface SlotStatus {
  value: string | null;
  attempts: number;
  confirmed: boolean;
  skipped: boolean;
}

export interface PendingConfirmation {
  slot: SlotName;
  value: string;
}

export interface ConversationState {
  slots: Record<SlotName, SlotStatus>;
  currentSlot: SlotName | null;
  pendingConfirmation: PendingConfirmation | null;
}
