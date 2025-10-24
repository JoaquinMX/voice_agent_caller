import { isValidMxNumber, parseEmail, normalizeFreeText, isValidOrderId } from '../src/validators';

describe('validators', () => {
  it('validates Mexican E.164 numbers', () => {
    expect(isValidMxNumber('+521234567890')).toBe(true);
    expect(isValidMxNumber('+5201234567890')).toBe(true);
    expect(isValidMxNumber('+531234567890')).toBe(false);
    expect(isValidMxNumber('1234567890')).toBe(false);
  });

  it('parses and normalizes email addresses', () => {
    expect(parseEmail('Test@Example.com')).toBe('test@example.com');
    expect(parseEmail('usuario@dominio')).toBeNull();
  });

  it('normalizes free text by trimming whitespace', () => {
    expect(normalizeFreeText('  María   López  ')).toBe('María López');
  });

  it('validates order identifiers', () => {
    expect(isValidOrderId('ABC123')).toBe(true);
    expect(isValidOrderId('A B')).toBe(false);
  });
});
