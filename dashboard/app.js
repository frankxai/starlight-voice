const option = document.querySelector("#option");
const rating = document.querySelector("#rating");
const ratingOut = document.querySelector("#ratingOut");
const notes = document.querySelector("#notes");
const status = document.querySelector("#status");
const form = document.querySelector("#ratingForm");
const briefingText = document.querySelector("#briefingText");
const voiceSelect = document.querySelector("#voiceSelect");
const coolFactor = document.querySelector("#coolFactor");
const coolOut = document.querySelector("#coolOut");
const speechStatus = document.querySelector("#speechStatus");
const speakBriefing = document.querySelector("#speakBriefing");

const briefings = {
  arcanea:
    "Hello sir. This is the update about Arcanea Business. The priority is simple: tighten the offer, verify the revenue path, and use Starlight Voice as the executive operator that keeps the system moving while you build.",
  sis:
    "Hello sir. This is the update about the Starlight Intelligence Systems. The substrate is online, the voice cockpit is now testable, and the next move is a hybrid architecture with beautiful speech, safe browser execution, and Codex-grade engineering control.",
  ops:
    "Hello sir. Builder operations are ready. I recommend a five step run: check machine readiness, open the dashboard, speak the briefing, test one workflow, then save the rating that decides the next implementation lane.",
};

const workflowBriefings = {
  "arcanea-business":
    "Arcanea Business Update selected. The operator should gather business state, surface blockers, summarize momentum, and end with the next highest leverage action.",
  "sis-ops":
    "Starlight Intelligence Check selected. The operator should inspect repositories, memory, agents, install state, and return a precise build report.",
  "browser-builder":
    "Browser Builder Run selected. The operator should open the target, observe the page, perform approved actions, verify output, and log evidence.",
  "voice-lab":
    "Voice Provider Bakeoff selected. The operator should compare ElevenLabs, OpenAI Realtime, and open source lanes by beauty, latency, control, privacy, and cost.",
};

let voices = [];

function pickPreferredVoice() {
  const preferred = voices.find((voice) => /natural|premium|online|aria|jenny|guy|brian|sonia/i.test(voice.name));
  return preferred || voices[0] || null;
}

function loadVoices() {
  if (!("speechSynthesis" in window)) {
    speechStatus.textContent = "Browser speech synthesis is not available in this browser.";
    return;
  }

  voices = window.speechSynthesis.getVoices();
  voiceSelect.innerHTML = '<option value="">System default</option>';
  voices.forEach((voice, index) => {
    const optionNode = document.createElement("option");
    optionNode.value = String(index);
    optionNode.textContent = `${voice.name} (${voice.lang})`;
    voiceSelect.append(optionNode);
  });

  const preferred = pickPreferredVoice();
  if (preferred) {
    voiceSelect.value = String(voices.indexOf(preferred));
  }
}

function speak(text) {
  if (!("speechSynthesis" in window)) {
    speechStatus.textContent = "Browser speech synthesis is not available in this browser.";
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  const selectedVoice = voices[Number(voiceSelect.value)];
  if (selectedVoice) utterance.voice = selectedVoice;
  const cool = Number(coolFactor.value);
  utterance.rate = Math.max(0.82, Math.min(1.05, 0.94 + (cool - 7) * 0.015));
  utterance.pitch = Math.max(0.76, Math.min(1.1, 0.9 + (cool - 7) * 0.018));
  utterance.volume = 1;
  utterance.onstart = () => {
    speechStatus.textContent = "Speaking briefing...";
  };
  utterance.onend = () => {
    speechStatus.textContent = "Briefing complete.";
  };
  utterance.onerror = () => {
    speechStatus.textContent = "Speech failed in this browser. Try Edge or Chrome.";
  };
  window.speechSynthesis.speak(utterance);
}

document.querySelectorAll("[data-choice]").forEach((button) => {
  button.addEventListener("click", () => {
    option.value = button.dataset.choice;
    document.querySelector(".panel").scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

rating.addEventListener("input", () => {
  ratingOut.textContent = rating.value;
});

coolFactor.addEventListener("input", () => {
  coolOut.textContent = coolFactor.value;
});

document.querySelectorAll("[data-briefing]").forEach((button) => {
  button.addEventListener("click", () => {
    briefingText.textContent = briefings[button.dataset.briefing];
  });
});

document.querySelectorAll("[data-run-workflow]").forEach((button) => {
  button.addEventListener("click", () => {
    briefingText.textContent = workflowBriefings[button.dataset.runWorkflow];
    speak(briefingText.textContent);
  });
});

speakBriefing.addEventListener("click", () => {
  speak(briefingText.textContent);
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  status.textContent = "Saving...";
  const payload = {
    option: option.value,
    rating: Number(rating.value),
    notes: notes.value.trim(),
    briefing: briefingText.textContent.trim(),
    cool_factor: Number(coolFactor.value),
    selected_voice: voiceSelect.selectedOptions[0]?.textContent || "System default",
    user_agent: navigator.userAgent,
  };

  try {
    const response = await fetch("/ratings", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json();
    if (!body.ok) throw new Error("Save failed");
    localStorage.setItem("starlight-voice-last-rating", JSON.stringify(payload));
    status.textContent = `Saved to ${body.path}`;
  } catch (error) {
    localStorage.setItem("starlight-voice-last-rating", JSON.stringify(payload));
    status.textContent = "Saved in browser only. Start dashboard server to write JSONL.";
  }
});

loadVoices();
if ("speechSynthesis" in window) {
  window.speechSynthesis.onvoiceschanged = loadVoices;
}
