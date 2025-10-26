const MX_NUMBER_REGEX = /^\+52\d{10,13}$/;
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/i;

export function isValidMxNumber(e164: string): boolean {
  return MX_NUMBER_REGEX.test(e164);
}

export function parseEmail(text: string): string | null {
  const normalized = text.trim().toLowerCase();
  if (EMAIL_REGEX.test(normalized)) {
    return normalized;
  }
  return null;
}

export function normalizeFreeText(text: string): string {
  return text.replace(/\s+/g, ' ').trim();
}

export function isValidOrderId(text: string): boolean {
  return /^[a-zA-Z0-9-]{3,}$/.test(text.trim());
}
