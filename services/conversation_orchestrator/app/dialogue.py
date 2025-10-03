from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

from .llm import LLMClient
from .schemas import ConversationMessage, SessionState


@dataclass(frozen=True)
class SlotDefinition:
    name: str
    prompt: str
    hint: str


SLOT_DEFINITIONS: OrderedDict[str, SlotDefinition] = OrderedDict(
    [
        (
            "customer_name",
            SlotDefinition(
                name="customer_name",
                prompt="¿Con quién tengo el gusto? Necesito su nombre completo, por favor.",
                hint="nombre",
            ),
        ),
        (
            "intent",
            SlotDefinition(
                name="intent",
                prompt="¿En qué puedo apoyarte hoy?",
                hint="motivo",
            ),
        ),
        (
            "callback_number",
            SlotDefinition(
                name="callback_number",
                prompt="¿Cuál es un número telefónico de contacto en México?",
                hint="teléfono",
            ),
        ),
    ]
)


class DialogueManager:
    """Hybrid dialogue policy with deterministic slots and LLM fallback."""

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm = llm_client

    async def handle_turn(
        self,
        state: SessionState,
        user_input: str,
        metadata: dict[str, Any],
    ) -> tuple[SessionState, str, dict[str, Any]]:
        state.history.append(ConversationMessage(role="user", content=user_input))
        self._apply_heuristics(state, user_input, metadata)

        next_slot = self._next_missing_slot(state)
        if next_slot:
            definition = SLOT_DEFINITIONS[next_slot]
            response_text = definition.prompt
            directives = {"expected_slot": next_slot, "speaking_style": "conversational"}
        else:
            state.status = "ready"
            response_text = await self._generate_llm_response(state)
            directives = {"speaking_style": "empathetic"}

        state.history.append(ConversationMessage(role="assistant", content=response_text))
        state.turn_index += 1
        return state, response_text, directives

    def _next_missing_slot(self, state: SessionState) -> str | None:
        for slot_name in SLOT_DEFINITIONS:
            if slot_name not in state.slots:
                return slot_name
        return None

    def _apply_heuristics(self, state: SessionState, user_input: str, metadata: dict[str, Any]) -> None:
        lowered = user_input.lower()
        if "customer_name" not in state.slots:
            name = self._extract_name(lowered)
            if not name:
                name = metadata.get("caller_name")
            if name:
                state.slots["customer_name"] = name.title()

        if "intent" not in state.slots:
            intent = self._extract_intent(lowered)
            if intent:
                state.slots["intent"] = intent

        if "callback_number" not in state.slots:
            phone = self._extract_phone(lowered)
            if phone:
                state.slots["callback_number"] = phone

    @staticmethod
    def _extract_name(text: str) -> str | None:
        match = re.search(r"me llamo\s+([a-záéíóúñ\s]+)", text)
        if match:
            return match.group(1).strip()
        match = re.search(r"soy\s+([a-záéíóúñ\s]+)", text)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def _extract_intent(text: str) -> str | None:
        keywords = {
            "factura": "consultar factura",
            "pago": "aclaración de pagos",
            "soporte": "soporte técnico",
            "cita": "agendar cita",
            "información": "solicitar información",
        }
        for keyword, value in keywords.items():
            if keyword in text:
                return value
        return None

    @staticmethod
    def _extract_phone(text: str) -> str | None:
        digits = re.findall(r"\b(\d{10})\b", text)
        if digits:
            return digits[0]
        return None

    async def _generate_llm_response(self, state: SessionState) -> str:
        if self._llm is None:
            return "Perfecto, permíteme validar la información y enseguida continúo contigo."

        prompt_messages = [
            {
                "role": "system",
                "content": (
                    "Eres una agente telefónica mexicana, empática y profesional. "
                    "Confirma datos capturados y ofrece pasos siguientes de forma clara."
                ),
            }
        ]
        for message in state.history[-6:]:
            prompt_messages.append({"role": message.role, "content": message.content})

        slots_summary = ", ".join(f"{k}: {v}" for k, v in state.slots.items())
        prompt_messages.append(
            {
                "role": "system",
                "content": f"Datos recopilados hasta ahora: {slots_summary if slots_summary else 'ninguno'}",
            }
        )

        return await self._llm.generate_response(prompt_messages)
