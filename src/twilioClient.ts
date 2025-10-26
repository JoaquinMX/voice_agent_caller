import Twilio, { Twilio as TwilioClient } from 'twilio';

let cachedClient: TwilioClient | null = null;
let warnedMissingCredentials = false;

export function getTwilioClient(): TwilioClient | null {
  const accountSid = process.env.TWILIO_ACCOUNT_SID;
  const authToken = process.env.TWILIO_AUTH_TOKEN;

  if (!accountSid || !authToken) {
    if (!warnedMissingCredentials) {
      console.warn(
        'Twilio credentials are not fully configured. Outbound calls will fail until they are provided.'
      );
      warnedMissingCredentials = true;
    }
    return null;
  }

  if (!cachedClient) {
    cachedClient = Twilio(accountSid, authToken);
  }

  return cachedClient;
}

interface MakeOutboundCallParams {
  to: string;
  from: string;
  url: string;
}

export async function makeOutboundCall({ to, from, url }: MakeOutboundCallParams) {
  const client = getTwilioClient();

  if (!client) {
    throw new Error('Twilio client is not configured. Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.');
  }

  return client.calls.create({
    to,
    from,
    url,
    method: 'POST',
  });
}
