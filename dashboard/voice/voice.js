import {
  PttLatch,
  VoiceStateMachine,
  formatCaptureSettings,
  isPttEligibleTarget,
  levelFromTimeDomain,
  performPttAction,
  pttActionForState,
  shouldAnimateContinuously,
} from "/voice/voice-runtime.mjs";

const $ = (id) => document.getElementById(id);
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const STATE_COPY = {
  ready: {
    mode: "Ready",
    title: "Ready when you are.",
    description: "A user-initiated voice surface for directing Starlight. Your microphone stays local in this experience.",
    transcript: "Press Start listening or run the clearly labelled guided turn.",
    glyph: "S",
    equivalent: "Starlight Voice is ready. Microphone capture is off.",
  },
  requesting: {
    mode: "Permission",
    title: "Opening a private channel.",
    description: "Your browser is asking for microphone access. Capture starts only after you approve it.",
    transcript: "Waiting for the browser microphone decision.",
    glyph: "···",
    equivalent: "Starlight Voice is waiting for microphone permission.",
  },
  listening: {
    mode: "Listening",
    title: "I’m listening.",
    description: "The Signal Core now reflects measured microphone energy. No audio leaves this local surface.",
    transcript: "Local microphone signal is active. Speak naturally, or stop when finished.",
    glyph: "◉",
    equivalent: "Starlight Voice is listening. The live level meter reflects local microphone energy.",
  },
  transcribing: {
    mode: "Transcribing",
    title: "Resolving the signal.",
    description: "The component lane converts only the committed microphone turn into text before reasoning begins.",
    transcript: "Guided turn: speech boundary closed and transcription is being resolved locally in the state model.",
    glyph: "⌁",
    equivalent: "The guided turn is transcribing. No external speech service is being called by this demonstration.",
  },
  thinking: {
    mode: "Routing",
    title: "Routing the intent.",
    description: "A production session would preserve the turn, validate tool schemas and execute approved tools server-side.",
    transcript: "Guided turn: intent committed and waiting for the realtime response.",
    glyph: "◇",
    equivalent: "The guided turn is in the thinking state. No external model call is being made.",
  },
  speaking: {
    mode: "Speaking",
    title: "Starlight is responding.",
    description: "Playback would remain interruptible. This guided state demonstrates timing and control without fabricating a provider connection.",
    transcript: "Guided turn: response playback state. Press Escape to demonstrate barge-in.",
    glyph: "✦",
    equivalent: "The guided turn is in the speaking state. No generated audio is playing.",
  },
  interrupted: {
    mode: "Interrupted",
    title: "You have control.",
    description: "The active turn stopped immediately and the session is returning to a safe idle state.",
    transcript: "Interruption acknowledged. Provider output and tool continuation would be cancelled here.",
    glyph: "×",
    equivalent: "The active guided turn was interrupted by the operator.",
  },
  error: {
    mode: "Signal error",
    title: "Signal interrupted.",
    description: "Microphone capture could not start. Review the browser permission and input device, then try again.",
    transcript: "No audio was captured. Guided mode remains available without microphone access.",
    glyph: "!",
    equivalent: "Microphone capture failed. No audio is being recorded.",
  },
};

const shell = $("voiceShell");
const listenButton = $("listenButton");
const guidedButton = $("guidedButton");
const interruptButton = $("interruptButton");
const canvas = $("signalCore");
const ctx = canvas.getContext("2d", { alpha: true });

let audioContext = null;
let analyser = null;
let mediaStream = null;
let analyserBuffer = null;
let animationFrame = 0;
let currentLevel = { rms: 0, peak: 0, normalized: 0, db: -96 };
let smoothLevel = 0;
let guided = false;
let guidedTimers = [];
const pttLatch = new PttLatch();
let toastTimer = 0;
let canvasWidth = 0;
let canvasHeight = 0;

const machine = new VoiceStateMachine("ready", renderTransition);

function formatState(state) {
  return state.charAt(0).toUpperCase() + state.slice(1);
}

function showToast(message) {
  const toast = $("permissionToast");
  toast.textContent = message;
  toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => {
    toast.hidden = true;
  }, 5200);
}

function appendTrace(entry) {
  const list = $("traceList");
  for (const node of list.querySelectorAll(".trace-node")) node.classList.remove("current");
  const item = document.createElement("li");
  const detail = entry.detail || STATE_COPY[entry.state].transcript;
  item.innerHTML = `<span class="trace-node current" aria-hidden="true"></span><div><strong>${formatState(entry.state)}</strong><small></small></div><time></time>`;
  item.querySelector("small").textContent = detail;
  item.querySelector("time").textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  list.prepend(item);
  while (list.children.length > 5) list.lastElementChild.remove();
}

function renderTransition(entry) {
  const state = entry.state;
  const copy = STATE_COPY[state];
  shell.dataset.state = state;
  $("modeLabel").textContent = copy.mode;
  $("voiceTitle").textContent = copy.title;
  $("stateDescription").textContent = copy.description;
  $("transcriptKicker").textContent = guided ? "Guided turn · local demo" : state === "listening" ? "Local signal" : "Session state";
  $("transcript").textContent = copy.transcript;
  $("coreGlyph").textContent = copy.glyph;
  $("coreState").textContent = state.toUpperCase();
  $("visualEquivalent").textContent = copy.equivalent;
  $("sessionFact").textContent = state === "listening" ? "Local mic active" : guided ? "Guided turn" : "Local surface";
  $("transportBadge").textContent = guided ? "GUIDED" : analyser ? "LOCAL MIC" : "LOCAL";

  listenButton.disabled = ["requesting", "transcribing", "thinking", "speaking", "interrupted"].includes(state);
  guidedButton.disabled = ["requesting", "transcribing", "thinking", "speaking", "interrupted"].includes(state);
  interruptButton.disabled = !["transcribing", "thinking", "speaking"].includes(state);
  $("listenLabel").textContent = state === "listening" && analyser ? "Stop listening" : "Start listening";

  appendTrace(entry);
  ensureAnimation();
}

function clearGuidedTimers() {
  for (const timer of guidedTimers) clearTimeout(timer);
  guidedTimers = [];
}

function scheduleGuided(delay, action) {
  guidedTimers.push(window.setTimeout(action, delay));
}

async function releaseMicrophone() {
  if (mediaStream) {
    for (const track of mediaStream.getTracks()) track.stop();
  }
  mediaStream = null;
  analyser = null;
  analyserBuffer = null;
  if (audioContext && audioContext.state !== "closed") await audioContext.close();
  audioContext = null;
  currentLevel = { rms: 0, peak: 0, normalized: 0, db: -96 };
  updateMeter(currentLevel);
}

async function stopListening(detail = "Microphone capture stopped") {
  await releaseMicrophone();
  if (machine.state !== "ready" && machine.state !== "error") machine.transition("ready", detail);
}

async function startListening() {
  if (machine.state === "listening" && analyser) {
    await stopListening();
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia) {
    pttLatch.reset();
    if (machine.state !== "error") machine.transition("error", "This browser does not expose MediaDevices.getUserMedia");
    showToast("Microphone capture is unavailable in this browser. Guided mode still works.");
    return;
  }

  clearGuidedTimers();
  guided = false;
  if (machine.state === "error") machine.transition("requesting", "Retrying microphone permission");
  else if (machine.state === "ready") machine.transition("requesting", "Microphone permission requested by operator");

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        channelCount: { ideal: 1 },
        sampleRate: { ideal: 48_000 },
      },
      video: false,
    });
    audioContext = new AudioContext({ latencyHint: "interactive", sampleRate: 48_000 });
    if (audioContext.state === "suspended") await audioContext.resume();
    const source = audioContext.createMediaStreamSource(mediaStream);
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 1024;
    analyser.smoothingTimeConstant = 0.72;
    analyserBuffer = new Uint8Array(analyser.fftSize);
    source.connect(analyser);
    const settings = mediaStream.getAudioTracks()[0]?.getSettings?.() || {};
    const captureLabel = formatCaptureSettings(settings, audioContext.sampleRate);
    $("captureFormat").textContent = captureLabel;
    $("captureDetail").textContent = `Measured input: ${captureLabel}. Transport remains disabled in this local surface.`;
    machine.transition("listening", `Local analyser active — ${captureLabel}`);
    if (pttLatch.consumeRelease()) {
      await stopListening("Push-to-talk released");
    }
  } catch (error) {
    await releaseMicrophone();
    pttLatch.reset();
    $("captureFormat").textContent = "Capture unavailable";
    $("captureDetail").textContent = "No measured input format. The canonical transport boundary remains 48 kHz mono PCM16.";
    if (machine.state !== "error") machine.transition("error", error?.name || "Microphone request failed");
    const denied = error?.name === "NotAllowedError";
    showToast(
      denied
        ? "Microphone permission was not granted. Enable it in browser site settings, then try again."
        : "No usable microphone was found. Check the input device, then try again."
    );
  }
}

async function runGuidedTurn() {
  clearGuidedTimers();
  if (analyser) await stopListening("Local microphone released before guided turn");
  if (machine.state === "error") machine.transition("ready", "Guided mode selected without microphone");
  if (machine.state !== "ready") return;

  guided = true;
  machine.transition("listening", "Guided turn started — no microphone or provider call");
  scheduleGuided(900, () => machine.state === "listening" && machine.transition("transcribing", "Speech boundary committed"));
  scheduleGuided(1550, () => machine.state === "transcribing" && machine.transition("thinking", "Intent routed"));
  scheduleGuided(2600, () => machine.state === "thinking" && machine.transition("speaking", "Interruptible response state"));
  scheduleGuided(4400, () => machine.state === "speaking" && machine.transition("listening", "Turn complete"));
  scheduleGuided(5100, () => {
    if (machine.state === "listening" && guided) {
      guided = false;
      machine.transition("ready", "Guided turn complete");
    }
  });
}

function interruptTurn() {
  clearGuidedTimers();
  const interrupted = machine.interrupt();
  if (!interrupted) return;
  scheduleGuided(240, () => {
    guided = false;
    if (machine.state === "interrupted") machine.transition(analyser ? "listening" : "ready", "Operator control restored");
  });
}

function updateMeter(level) {
  const db = Math.round(level.db);
  $("levelDb").textContent = `${db <= -96 ? "−96" : db} dB`;
  $("levelFill").style.width = `${Math.round(level.normalized * 100)}%`;
}

function resizeCanvas() {
  const rect = canvas.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  canvasWidth = Math.max(1, rect.width);
  canvasHeight = Math.max(1, rect.height);
  canvas.width = Math.round(canvasWidth * dpr);
  canvas.height = Math.round(canvasHeight * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ensureAnimation();
}

function stateEnergy(state, time) {
  if (state === "requesting") return 0.14 + Math.sin(time * 0.003) * 0.025;
  if (state === "transcribing") return 0.17 + Math.sin(time * 0.0028) * 0.025;
  if (state === "thinking") return 0.23 + Math.sin(time * 0.0022) * 0.04;
  if (state === "speaking") return 0.35 + Math.sin(time * 0.005) * 0.09 + Math.sin(time * 0.011) * 0.035;
  if (state === "interrupted") return 0.07;
  if (state === "error") return 0.05;
  if (state === "listening" && guided) return 0.18 + Math.sin(time * 0.004) * 0.04;
  return 0.07;
}

function drawCore(time = 0) {
  animationFrame = 0;
  if (!canvasWidth || !canvasHeight) return;

  if (analyser && analyserBuffer) {
    analyser.getByteTimeDomainData(analyserBuffer);
    currentLevel = levelFromTimeDomain(analyserBuffer);
    updateMeter(currentLevel);
  } else if (!guided) {
    currentLevel = { rms: 0, peak: 0, normalized: 0, db: -96 };
  }

  const state = machine.state;
  const motionTime = reduceMotion ? 0 : time;
  const targetEnergy = analyser ? currentLevel.normalized : stateEnergy(state, motionTime);
  smoothLevel += (targetEnergy - smoothLevel) * (targetEnergy > smoothLevel ? 0.2 : 0.08);

  ctx.clearRect(0, 0, canvasWidth, canvasHeight);
  const cx = canvasWidth / 2;
  const cy = canvasHeight / 2;
  const baseRadius = Math.min(canvasWidth, canvasHeight) * 0.205;
  const palette = state === "error"
    ? ["255,107,129", "110,92,255"]
    : ["142,231,240", ["transcribing", "thinking", "speaking"].includes(state) ? "224,182,86" : "110,92,255"];

  const atmosphere = ctx.createRadialGradient(cx, cy, baseRadius * 0.2, cx, cy, baseRadius * 2.2);
  atmosphere.addColorStop(0, `rgba(${palette[0]},${0.08 + smoothLevel * 0.11})`);
  atmosphere.addColorStop(0.5, `rgba(${palette[1]},${0.04 + smoothLevel * 0.08})`);
  atmosphere.addColorStop(1, `rgba(${palette[1]},0)`);
  ctx.fillStyle = atmosphere;
  ctx.fillRect(cx - baseRadius * 2.3, cy - baseRadius * 2.3, baseRadius * 4.6, baseRadius * 4.6);

  ctx.save();
  ctx.translate(cx, cy);
  ctx.globalCompositeOperation = "screen";
  for (let layer = 0; layer < 7; layer += 1) {
    const points = 180;
    const layerOffset = (layer - 3) * 3.2;
    const energy = smoothLevel * (18 + layer * 1.8);
    ctx.beginPath();
    for (let index = 0; index <= points; index += 1) {
      const angle = (index / points) * Math.PI * 2;
      const harmonic =
        Math.sin(angle * (3 + (layer % 3)) + motionTime * (0.00035 + layer * 0.000035)) * 0.48 +
        Math.sin(angle * (7 + layer) - motionTime * 0.00022) * 0.28 +
        Math.sin(angle * 13 + layer * 0.7) * 0.12;
      const listeningShape = analyser ? currentLevel.peak * Math.sin(angle * 11 + motionTime * 0.0018) * 6 : 0;
      const radius = baseRadius + layerOffset + harmonic * energy + listeningShape;
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius * (0.96 + layer * 0.003);
      if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    const alpha = 0.1 + layer * 0.022 + smoothLevel * 0.16;
    ctx.strokeStyle = `rgba(${palette[layer % 2]},${alpha})`;
    ctx.lineWidth = layer === 3 ? 1.35 : 0.8;
    ctx.stroke();
  }

  const edge = ctx.createRadialGradient(0, 0, baseRadius * 0.18, 0, 0, baseRadius * 1.06);
  edge.addColorStop(0, "rgba(9,9,16,0.98)");
  edge.addColorStop(0.68, "rgba(15,13,26,0.92)");
  edge.addColorStop(0.9, `rgba(${palette[1]},${0.11 + smoothLevel * 0.1})`);
  edge.addColorStop(1, "rgba(9,9,16,0.2)");
  ctx.fillStyle = edge;
  ctx.beginPath();
  ctx.arc(0, 0, baseRadius * 0.88, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  if (shouldAnimateContinuously({ reduceMotion, analyserActive: Boolean(analyser) })) {
    animationFrame = requestAnimationFrame(drawCore);
  }
}

function ensureAnimation() {
  if (!animationFrame) animationFrame = requestAnimationFrame(drawCore);
}

listenButton.addEventListener("click", startListening);
guidedButton.addEventListener("click", runGuidedTurn);
interruptButton.addEventListener("click", interruptTurn);

window.addEventListener("keydown", async (event) => {
  if (event.key === "Escape") {
    interruptTurn();
    return;
  }
  if (
    event.code !== "Space" ||
    !isPttEligibleTarget(event.target) ||
    event.repeat ||
    event.metaKey ||
    event.ctrlKey ||
    event.altKey
  ) return;

  const action = pttActionForState(machine.state);
  if (action === "ignore") return;
  event.preventDefault();
  await performPttAction(action, {
    stop: async () => {
      pttLatch.reset();
      await stopListening("Space stopped local capture");
    },
    press: () => pttLatch.press(),
    start: () => startListening(),
    interrupt: () => interruptTurn(),
    scheduleStart: () => window.setTimeout(() => {
      if (machine.state === "ready") startListening();
    }, 280),
  });
});

window.addEventListener("keyup", async (event) => {
  if (event.code !== "Space" || !pttLatch.active) return;
  event.preventDefault();
  pttLatch.release();
  if (machine.state === "listening" && analyser) {
    pttLatch.consumeRelease();
    await stopListening("Push-to-talk released");
  }
});

window.addEventListener("pagehide", () => {
  pttLatch.reset();
  clearGuidedTimers();
  releaseMicrophone();
});

new ResizeObserver(resizeCanvas).observe(canvas);
resizeCanvas();
updateMeter(currentLevel);
