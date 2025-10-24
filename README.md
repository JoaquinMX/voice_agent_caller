# Voice Agent Caller

A minimal Node.js voice bot that can place outbound calls to Mexico, speak natural Spanish, and run a simple multi-turn information gathering conversation using Twilio Programmable Voice.

## Quick start

1. Copy the environment file and fill in your credentials:
   ```bash
   cp .env.example .env
   ```
2. Install dependencies and start the development server:
   ```bash
   npm install
   npm run dev
   ```
3. Expose your local server with ngrok and set the public base URL:
   ```bash
   ngrok http 3000
   ```
   Update `PUBLIC_BASE_URL` in `.env` with the HTTPS URL from ngrok.
4. In the Twilio Console, configure a voice-capable phone number and set the **Voice webhook** to `POST {PUBLIC_BASE_URL}/voice/welcome`.
5. Test inbound calls by dialing your Twilio number. You should hear Spanish prompts collecting nombre, correo, and número de pedido.
6. Trigger an outbound call (Twilio account must allow international dialing to Mexico):
   ```bash
   npm run call -- +52XXXXXXXXXX
   ```

## Mexico calling notes

- Ensure international dialing to Mexico is enabled on your Twilio account and sufficient balance is available.
- Use E.164 formatting for all phone numbers and comply with any caller ID requirements for calls to Mexico.

## Conversation flow

The conversation collects three pieces of information in order:

1. `nombre`
2. `correo`
3. `numero_de_pedido`

Each slot prompt is delivered in concise, neutral Spanish. Responses are captured with Twilio speech recognition in `es-MX`. After each response the assistant confirms what it heard (`¿Es correcto?`).

If the caller responds negatively or the speech result is missing/low-confidence, the assistant retries up to two additional times with varied phrasing. After three failed attempts for a slot, it is skipped politely (`"lo dejamos pendiente"`) and the flow advances. Email and order number answers receive minimal validation and reprompting when invalid.

At the end of the call, the bot summarizes the collected details in Spanish, thanks the caller, and hangs up. Conversation state is stored in memory keyed by `CallSid`; replace with Redis or another datastore for production use.

## Development notes

- `npm run dev` uses `tsx` for live-reloading TypeScript during development.
- `npm run build` compiles TypeScript to `dist/` for production; run `npm start` to serve compiled code.
- `npm run lint` runs ESLint with TypeScript support and Prettier formatting rules.
- `npm test` runs unit tests with Jest.
- Webhook routes expect `application/x-www-form-urlencoded` bodies as sent by Twilio.

## Security

This project stores conversation state in an in-memory map for simplicity. Do not deploy as-is to production; replace the state store with Redis or another persistent datastore and add authentication to admin endpoints.
