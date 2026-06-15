// Starlight Voice cockpit — polls /status and renders live operator state.
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? "").replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

function renderLoop(s = {}) {
  const rows = [
    ["STT", s.stt_engine],
    ["LLM", `${s.llm_model} @ ${s.llm_fast_provider}`],
    ["TTS", s.tts_engine],
  ];
  $("loopKv").innerHTML = rows.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v)}</dd>`).join("");
}

function renderLanes(variants = []) {
  $("lanes").innerHTML = variants
    .map((v) => {
      const ok = v.key_live;
      return `<li class="lane"><span><span class="name">${esc(v.label)}</span><br><span class="engine">${esc(v.engine)}</span></span>
        <span class="pill ${ok ? "ok" : "blocked"}">${ok ? "key live" : "blocked"}</span></li>`;
    })
    .join("");
}

function renderAdapters(adapters = {}) {
  $("adapters").innerHTML = Object.entries(adapters)
    .map(([k, v]) => `<li><span>${esc(k)}</span><span class="${v ? "yes" : "no"}">${v ? "●" : "○"}</span></li>`)
    .join("");
}

function renderLedger(runs = []) {
  if (!runs.length) {
    $("ledger").innerHTML = `<li class="empty">No dispatches yet. Say "refactor the auth module" to start one.</li>`;
    return;
  }
  $("ledger").innerHTML = runs
    .slice()
    .reverse()
    .map((r) => {
      const tier = (r.tier || "?").toUpperCase();
      return `<li><span class="tier ${esc(tier)}">${esc(tier)}</span>
        <span class="st">${esc(r.status)}</span>
        <span class="task" title="${esc(r.task)}">${esc(r.task)}</span>
        <span class="st">${esc((r.target || "").split(" ")[0])}</span></li>`;
    })
    .join("");
}

async function poll() {
  try {
    const s = await (await fetch("./status", { cache: "no-store" })).json();
    renderLoop(s.settings);
    renderLanes(s.variants);
    renderAdapters(s.adapters);
    renderLedger(s.runs);
    $("budget").textContent = `≤ ${s.first_audio_budget_ms ?? "—"} ms`;
    const up = s.gateway === "running";
    const gw = $("gateway");
    gw.textContent = up ? "gateway: running" : "gateway: not running";
    gw.className = `gateway ${up ? "up" : "down"}`;
    $("liveState").className = "live ok";
    $("liveLabel").textContent = "live";
    $("err").textContent = s.error || "";
  } catch (e) {
    $("liveState").className = "live err";
    $("liveLabel").textContent = "offline";
    $("err").textContent = String(e);
  }
}

poll();
setInterval(poll, 4000);
