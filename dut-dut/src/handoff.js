// handoff.js — send the cadence context to an assistant of the user's choosing.
//
// Design constraint: this app never calls an LLM itself. A claude.ai / ChatGPT
// subscription cannot be used programmatically (only separately-metered API
// credits can), so the only way to reach the subscription a user already pays
// for is to hand the text into the chat UI where they are already signed in.
// That also means the app makes zero network requests of its own — nothing
// leaves the browser until the user deliberately sends it.
import { downloadBlob } from './download.js';

// These `?q=` parameters are undocumented per-vendor and can change without
// notice. Clipboard is the guaranteed path and is always offered alongside.
export const DESTINATIONS = [
  { id: 'claude', label: 'Claude', blank: 'https://claude.ai/new', url: q => `https://claude.ai/new?q=${q}` },
  { id: 'chatgpt', label: 'ChatGPT', blank: 'https://chatgpt.com/', url: q => `https://chatgpt.com/?q=${q}` },
  { id: 'gemini', label: 'Gemini', blank: 'https://gemini.google.com/app', url: q => `https://gemini.google.com/app?q=${q}` },
];

// A typical single-section envelope encodes to ~3.3k, so the old 2k-ish "maximum
// compatibility" ceiling would make every send fall back and the destination
// buttons pointless. 4k is still well inside every modern browser (Chrome handles
// ~32k) and leaves headroom under Apache's 8190-byte request-line default.
// These destinations are SPAs that read `?q=` from location.search client-side,
// so an over-long URL surfaces as a visible 414 from a CDN rather than a silent
// truncation — and anything past this limit takes the copy path anyway.
export const URL_LIMIT = 4000;

export function encodedLength(text) {
  return encodeURIComponent(text).length;
}

export function fitsInUrl(text) {
  return encodedLength(text) <= URL_LIMIT;
}

export function buildUrl(dest, text) {
  return dest.url(encodeURIComponent(text));
}

export function copyText(text) {
  return navigator.clipboard.writeText(text);
}

export function downloadMarkdown(text, filename = 'dut-dut-cadence.md') {
  downloadBlob(new Blob([text], { type: 'text/markdown' }), filename);
}

// Opens `dest` with the context prefilled when it fits in a URL. When it does
// not, copies the text and opens an empty chat instead — never truncates, since
// a silently clipped pattern would be explained wrongly.
//
// `open` and `copy` are injectable so the length-guard branch can be tested
// without actually launching tabs.
export function sendTo(dest, text, { open, copy } = {}) {
  const doOpen = open || (u => window.open(u, '_blank', 'noopener,noreferrer'));
  const doCopy = copy || copyText;
  const fits = fitsInUrl(text);
  // Must happen synchronously inside the click handler — awaiting the clipboard
  // first loses the user-gesture context and trips popup blockers.
  const url = fits ? buildUrl(dest, text) : dest.blank;
  doOpen(url);
  if (!fits) doCopy(text);
  return { fellBack: !fits, url };
}
