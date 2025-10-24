import Twilio from 'twilio';

const accountSid = process.env.TWILIO_ACCOUNT_SID;
const authToken = process.env.TWILIO_AUTH_TOKEN;

if (!accountSid || !authToken) {
  // Delay throwing until runtime usage to ease testing without credentials.
  console.warn('Twilio credentials are not fully configured. Outbound calls will fail.');
}

export const twilioClient = accountSid && authToken ? Twilio(accountSid, authToken) : null;

interface MakeOutboundCallParams {
  to: string;
  from: string;
  url: string;
}

export async function makeOutboundCall({ to, from, url }: MakeOutboundCallParams) {
  if (!twilioClient) {
    throw new Error('Twilio client is not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.');
  }

  return twilioClient.calls.create({
    to,
    from,
    url,
    method: 'POST',
  });
}
