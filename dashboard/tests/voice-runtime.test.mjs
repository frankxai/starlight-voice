import test from "node:test";
import assert from "node:assert/strict";

import {
  ALLOWED_TRANSITIONS,
  PttLatch,
  VoiceStateMachine,
  dbFromRms,
  formatCaptureSettings,
  isPttEligibleTarget,
  levelFromTimeDomain,
  performPttAction,
  pttActionForState,
  shouldAnimateContinuously,
} from "../voice/voice-runtime.mjs";

test("state machine follows the guided turn contract", () => {
  const machine = new VoiceStateMachine("ready");

  machine.transition("requesting");
  machine.transition("listening");
  machine.transition("transcribing");
  machine.transition("thinking");
  machine.transition("speaking");
  machine.transition("listening");

  assert.equal(machine.state, "listening");
  assert.deepEqual(machine.history.map((entry) => entry.state), [
    "ready",
    "requesting",
    "listening",
    "transcribing",
    "thinking",
    "speaking",
    "listening",
  ]);
});

test("invalid state transitions fail closed", () => {
  const machine = new VoiceStateMachine("ready");

  assert.throws(() => machine.transition("speaking"), /ready.*speaking/i);
  assert.equal(machine.state, "ready");
});

test("interruption returns control to listening", () => {
  const machine = new VoiceStateMachine("listening");
  machine.transition("thinking");
  machine.interrupt();

  assert.equal(machine.state, "interrupted");
  machine.transition("listening");
  assert.equal(machine.state, "listening");
});

test("every declared state has an explicit transition policy", () => {
  const states = ["ready", "requesting", "listening", "transcribing", "thinking", "speaking", "interrupted", "error"];
  assert.deepEqual(Object.keys(ALLOWED_TRANSITIONS).sort(), states.sort());
});

test("time-domain input produces bounded RMS and peak", () => {
  const signal = new Uint8Array([128, 255, 128, 0]);
  const level = levelFromTimeDomain(signal);

  assert.ok(level.rms > 0.6 && level.rms < 0.8);
  assert.equal(level.peak, 1);
  assert.ok(level.normalized >= 0 && level.normalized <= 1);
});

test("decibel conversion handles silence and unity", () => {
  assert.equal(dbFromRms(0), -96);
  assert.equal(dbFromRms(1), 0);
});

test("PTT intent interrupts an active answer before starting a new turn", () => {
  assert.equal(pttActionForState("ready"), "start");
  assert.equal(pttActionForState("error"), "start");
  assert.equal(pttActionForState("listening"), "stop");
  assert.equal(pttActionForState("transcribing"), "interrupt-and-start");
  assert.equal(pttActionForState("thinking"), "interrupt-and-start");
  assert.equal(pttActionForState("speaking"), "interrupt-and-start");
  assert.equal(pttActionForState("requesting"), "ignore");
});

test("Space PTT executes the declared stop action for active capture", async () => {
  const calls = [];
  const handled = await performPttAction("stop", {
    stop: async () => calls.push("stop"),
  });
  assert.equal(handled, true);
  assert.deepEqual(calls, ["stop"]);
});

test("PTT preserves native Space behavior on interactive controls", () => {
  assert.equal(isPttEligibleTarget({ closest: () => ({ tagName: "BUTTON" }) }), false);
  assert.equal(isPttEligibleTarget({ closest: () => null }), true);
});

test("PTT release latch resets after denial before a clean retry", () => {
  const latch = new PttLatch();
  latch.press();
  latch.release();
  assert.equal(latch.consumeRelease(), true);
  assert.equal(latch.consumeRelease(), false);

  latch.press();
  latch.release();
  latch.reset();
  latch.press();
  assert.equal(latch.consumeRelease(), false);
});

test("capture label reports measured format separately from canonical transport", () => {
  assert.equal(formatCaptureSettings({ sampleRate: 48_000, channelCount: 1 }, 48_000), "48 kHz · mono capture");
  assert.equal(
    formatCaptureSettings({ sampleRate: 44_100, channelCount: 2 }, 48_000),
    "44.1 kHz · 2 ch capture → 48 kHz mono canonical",
  );
  assert.equal(
    formatCaptureSettings({}, 48_000),
    "48 kHz analysis · source format unavailable → 48 kHz mono canonical",
  );
});

test("reduced motion loops only for functional live metering", () => {
  assert.equal(shouldAnimateContinuously({ reduceMotion: true, analyserActive: false }), false);
  assert.equal(shouldAnimateContinuously({ reduceMotion: true, analyserActive: true }), true);
  assert.equal(shouldAnimateContinuously({ reduceMotion: false, analyserActive: false }), true);
});
