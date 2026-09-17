export const ALLOWED_TRANSITIONS = Object.freeze({
  ready: ["requesting", "listening", "error"],
  requesting: ["listening", "ready", "error"],
  listening: ["transcribing", "thinking", "ready", "error"],
  transcribing: ["thinking", "interrupted", "ready", "error"],
  thinking: ["speaking", "interrupted", "ready", "error"],
  speaking: ["listening", "interrupted", "ready", "error"],
  interrupted: ["listening", "ready", "error"],
  error: ["ready", "requesting"],
});

export class VoiceStateMachine {
  constructor(initialState = "ready", onTransition = null) {
    if (!(initialState in ALLOWED_TRANSITIONS)) {
      throw new Error(`Unknown initial voice state: ${initialState}`);
    }
    this.state = initialState;
    this.onTransition = onTransition;
    this.history = [{ state: initialState, at: performance.now() }];
  }

  transition(nextState, detail = "") {
    if (!ALLOWED_TRANSITIONS[this.state]?.includes(nextState)) {
      throw new Error(`Invalid voice transition: ${this.state} → ${nextState}`);
    }
    const previous = this.state;
    this.state = nextState;
    const entry = { state: nextState, previous, detail, at: performance.now() };
    this.history.push(entry);
    this.onTransition?.(entry);
    return entry;
  }

  interrupt(detail = "Operator interrupted the active turn") {
    if (!(["transcribing", "thinking", "speaking"].includes(this.state))) {
      return null;
    }
    return this.transition("interrupted", detail);
  }
}

export function pttActionForState(state) {
  if (["ready", "error"].includes(state)) return "start";
  if (state === "listening") return "stop";
  if (["transcribing", "thinking", "speaking"].includes(state)) return "interrupt-and-start";
  return "ignore";
}

export async function performPttAction(action, handlers) {
  if (action === "ignore") return false;
  if (action === "stop") {
    await handlers.stop();
    return true;
  }
  handlers.press();
  if (action === "interrupt-and-start") {
    handlers.interrupt();
    handlers.scheduleStart();
    return true;
  }
  if (action === "start") {
    await handlers.start();
    return true;
  }
  return false;
}

export class PttLatch {
  constructor() {
    this.reset();
  }

  press() {
    this.active = true;
    this.releaseQueued = false;
  }

  release() {
    if (!this.active) return false;
    this.active = false;
    this.releaseQueued = true;
    return true;
  }

  consumeRelease() {
    const queued = this.releaseQueued;
    this.releaseQueued = false;
    return queued;
  }

  reset() {
    this.active = false;
    this.releaseQueued = false;
  }
}

const INTERACTIVE_SELECTOR = "button, a, input, textarea, select, summary, [role='button'], [contenteditable='true']";

export function isPttEligibleTarget(target) {
  return !target?.closest?.(INTERACTIVE_SELECTOR);
}

export function formatCaptureSettings(settings = {}, contextRate = 48_000) {
  const measuredRate = Number(settings.sampleRate);
  const measuredChannels = Number(settings.channelCount);
  if (!measuredRate || !measuredChannels) {
    const analysisRate = Math.round(contextRate / 100) / 10;
    return `${analysisRate} kHz analysis · source format unavailable → 48 kHz mono canonical`;
  }
  const rate = measuredRate;
  const channels = measuredChannels;
  const rateLabel = Number.isInteger(rate / 1000) ? `${rate / 1000}` : `${Math.round(rate / 100) / 10}`;
  if (rate === 48_000 && channels === 1) return "48 kHz · mono capture";
  const channelLabel = channels === 1 ? "mono" : `${channels} ch`;
  return `${rateLabel} kHz · ${channelLabel} capture → 48 kHz mono canonical`;
}

export function shouldAnimateContinuously({ reduceMotion, analyserActive }) {
  return !reduceMotion || analyserActive;
}

export function dbFromRms(rms) {
  if (!Number.isFinite(rms) || rms <= 0) return -96;
  return Math.max(-96, Math.min(0, 20 * Math.log10(rms)));
}

export function levelFromTimeDomain(buffer) {
  if (!buffer?.length) return { rms: 0, peak: 0, normalized: 0, db: -96 };
  let sumSquares = 0;
  let peak = 0;
  for (const byte of buffer) {
    const sample = Math.max(-1, Math.min(1, (byte - 128) / 128));
    sumSquares += sample * sample;
    peak = Math.max(peak, Math.abs(sample));
  }
  const rms = Math.sqrt(sumSquares / buffer.length);
  const db = dbFromRms(rms);
  const normalized = Math.max(0, Math.min(1, (db + 60) / 60));
  return { rms, peak, normalized, db };
}
