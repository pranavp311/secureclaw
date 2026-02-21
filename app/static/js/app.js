/* ============ App state ============ */
let selectedTools = new Set([
    "get_weather",
    "set_alarm",
    "send_message",
    "create_reminder",
    "search_contacts",
    "play_music",
    "set_timer",
  ]),
  threshold = 0.99,
  openclawAvail = false,
  analysis = null,
  selMode = "local",
  cloudProv = "gemini",
  busy = false;

/* ============ Init ============ */
async function init() {
  const oR = await fetch("/api/openclaw-status");
  const oc = await oR.json();
  openclawAvail = oc.available;
}

/* ============ Helpers ============ */
function esc(s) {
  const d = document.createElement("div");
  d.textContent = String(s);
  return d.innerHTML;
}
function scrollBottom() {
  const m = document.querySelector("main");
  m.scrollTop = m.scrollHeight;
}
function addMsg(html) {
  const c = document.getElementById("messages");
  const w = document.createElement("div");
  w.innerHTML = html;
  c.appendChild(w.firstElementChild);
  document.getElementById("empty-state").classList.add("gone");

  if (!document.body.classList.contains("has-chats")) {
    const footer = document.querySelector("footer");
    const before = footer.getBoundingClientRect().top;
    document.body.classList.add("has-chats");
    const after = footer.getBoundingClientRect().top;
    const delta = before - after;
    footer.style.transition = "none";
    footer.style.transform = "translateY(" + delta + "px)";
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        footer.style.transition = "transform 1.0s cubic-bezier(0.22,1,0.36,1)";
        footer.style.transform = "translateY(0)";
        footer.addEventListener(
          "transitionend",
          () => {
            footer.style.transition = "";
            footer.style.transform = "";
          },
          { once: true },
        );
      });
    });
  }

  scrollBottom();
}

/* ============ Send / Analyze ============ */
async function send() {
  if (busy) return;
  const inp = document.getElementById("input");
  const msg = inp.value.trim();
  if (!msg) return;
  if (!selectedTools.size) {
    alert("Select at least one tool.");
    return;
  }
  inp.value = "";
  inp.style.height = "auto";
  busy = true;
  document.getElementById("send-btn").disabled = true;
  window.bgPulse(true);

  addMsg(
    '<div class="msg msg-user"><div class="bubble">' +
      esc(msg) +
      "</div></div>",
  );
  addMsg(
    '<div class="msg msg-sys" id="ld"><div class="bubble"><div class="dots"><span></span><span></span><span></span></div></div></div>',
  );

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: msg,
        tools: Array.from(selectedTools),
        threshold,
      }),
    });
    const data = await res.json();
    const ld = document.getElementById("ld");
    if (ld) ld.remove();
    if (data.error) {
      addMsg(
        '<div class="msg msg-sys"><div class="bubble"><div class="err-box">' +
          esc(data.error) +
          "</div></div></div>",
      );
    } else {
      analysis = data;
      analysis._msg = msg;
      selMode = data.recommendation;
      showAnalysis(data);
    }
  } catch (e) {
    const ld = document.getElementById("ld");
    if (ld) ld.remove();
    addMsg(
      '<div class="msg msg-sys"><div class="bubble"><div class="err-box">' +
        esc(e.message) +
        "</div></div></div>",
    );
  }
  busy = false;
  document.getElementById("send-btn").disabled = false;
  window.bgPulse(false);
}

/* ============ Analysis card ============ */
function showAnalysis(d) {
  const c = d.confidence,
    pct = (c * 100).toFixed(1),
    isL = d.recommendation === "local";
  const rec = isL
    ? "Confidence meets threshold. Recommended to run locally \u2014 data stays on your device."
    : "Confidence below threshold. Cloud execution recommended for higher accuracy.";

  let h = '<div class="msg msg-sys"><div class="bubble">';
  h += '<div class="a-label">Analysis</div>';
  h +=
    '<div class="conf-row"><span class="conf-num">' +
    pct +
    '</span><span class="conf-pct">% confidence</span></div>';
  h +=
    '<div class="conf-track"><div class="conf-fill" style="width:' +
    Math.max(c * 100, 1.5) +
    '%"></div></div>';
  h += '<div class="rec-box">' + rec + "</div>";

  h += '<div class="options">';
  h +=
    '<div class="opt' +
    (selMode === "local" ? " on" : "") +
    '" onclick="pick(\'local\',this)">';
  h +=
    '<div class="opt-hd"><span class="opt-title">Local</span><span class="opt-dot"></span></div>';
  h +=
    '<div class="opt-meta">' +
    d.local_time_ms.toFixed(0) +
    "ms measured<br>On-device inference</div>";
  h += '<div class="opt-tag tag-priv">Private</div></div>';

  h +=
    '<div class="opt' +
    (selMode !== "local" ? " on" : "") +
    '" onclick="pick(\'cloud\',this)">';
  h +=
    '<div class="opt-hd"><span class="opt-title">Cloud</span><span class="opt-dot"></span></div>';
  h += '<div class="opt-meta">~1\u20133s estimated<br>Higher accuracy</div>';
  h += '<div class="opt-tag tag-api">API</div>';
  h += '<div class="prov-row">';
  h +=
    '<button class="prov-btn' +
    (cloudProv === "gemini" ? " on" : "") +
    '" onclick="event.stopPropagation();setProv(\'gemini\',this)">Gemini</button>';
  h +=
    '<button class="prov-btn' +
    (cloudProv === "openclaw" ? " on" : "") +
    '"' +
    (!openclawAvail ? ' disabled title="Not detected"' : "") +
    " onclick=\"event.stopPropagation();setProv('openclaw',this)\">OpenClaw</button>";
  h += "</div></div></div>";

  h +=
    '<button class="exec-btn" onclick="execTask()">Execute ' +
    (selMode === "local" ? "locally" : "on cloud") +
    "</button>";
  h += "</div></div>";
  addMsg(h);
}

function pick(mode, el) {
  if (el.closest(".options.locked")) return;
  selMode = mode;
  const p = el.closest(".options");
  p.querySelectorAll(".opt").forEach((o) => o.classList.remove("on"));
  el.classList.add("on");
  const btn = el.closest(".bubble").querySelector(".exec-btn");
  if (btn)
    btn.textContent = "Execute " + (mode === "local" ? "locally" : "on cloud");
}

function setProv(p, btn) {
  if (btn.closest(".options.locked")) return;
  if (p === "openclaw" && !openclawAvail) return;
  cloudProv = p;
  btn.parentElement
    .querySelectorAll(".prov-btn")
    .forEach((b) => b.classList.remove("on"));
  btn.classList.add("on");
  const card = btn.closest(".opt");
  if (card) pick("cloud", card);
}

function lockOptions() {
  document
    .querySelectorAll(".options")
    .forEach((o) => o.classList.add("locked"));
}

/* ============ Execute ============ */
async function execTask() {
  if (busy || !analysis) return;
  busy = true;
  window.bgPulse(true);
  lockOptions();
  const mode = selMode === "local" ? "local" : cloudProv,
    msg = analysis._msg;
  document.querySelectorAll(".exec-btn").forEach((b) => {
    b.disabled = true;
    b.textContent = "Executing\u2026";
  });

  addMsg(
    '<div class="msg msg-sys" id="eld"><div class="bubble"><div class="dots"><span></span><span></span><span></span></div></div></div>',
  );

  const body = { message: msg, tools: Array.from(selectedTools), mode };
  if (mode === "local" && analysis) {
    body.cached_result = {
      function_calls: analysis.function_calls,
      total_time_ms: analysis.local_time_ms,
      confidence: analysis.confidence,
    };
  }

  try {
    const res = await fetch("/api/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const r = await res.json();
    const eld = document.getElementById("eld");
    if (eld) eld.remove();
    showResult(r, msg);
  } catch (e) {
    const eld = document.getElementById("eld");
    if (eld) eld.remove();
    showResult({ error: e.message, total_time_ms: 0 }, msg);
  }
  busy = false;
  analysis = null;
  window.bgPulse(false);
  document.querySelectorAll(".exec-btn").forEach((b) => {
    b.disabled = false;
    b.textContent = "Execute";
  });
}

/* ============ Result card ============ */
function showResult(r, msg) {
  const src = r.source || "unknown",
    isL = src.includes("on-device");
  let h = '<div class="msg msg-sys"><div class="bubble">';
  h += '<div class="r-label">Result</div>';
  h += '<div class="r-meta"><span class="r-src">' + esc(src) + "</span>";
  if (r.total_time_ms) h += "<span>" + r.total_time_ms.toFixed(0) + "ms</span>";
  if (r.confidence !== undefined)
    h += "<span>" + (r.confidence * 100).toFixed(1) + "% conf</span>";
  h += "<span>" + (isL ? "Private" : "Cloud") + "</span></div>";
  if (r.error) {
    h +=
      '<div class="fn-card"><div class="fn-name fail">' +
      esc(msg) +
      " unsuccessful</div>" +
      '<div class="err-box">' +
      esc(r.error) +
      "</div></div>";
  } else if (r.function_calls && r.function_calls.length) {
    for (const fn of r.function_calls) {
      h +=
        '<div class="fn-card"><div class="fn-name">' +
        esc(msg) +
        " successful!</div>";
      for (const [k, v] of Object.entries(fn.arguments || {})) {
        h +=
          '<div><span class="fn-k">' +
          esc(k) +
          ': </span><span class="fn-v">' +
          esc(JSON.stringify(v)) +
          "</span></div>";
      }
      h += "</div>";
    }
  } else {
    h += '<div class="no-calls">No function calls generated.</div>';
  }
  h += "</div></div>";
  addMsg(h);
}

/* ============ Input auto-grow ============ */
const inp = document.getElementById("input");
inp.addEventListener("input", () => {
  inp.style.height = "auto";
  inp.style.height = Math.min(inp.scrollHeight, 120) + "px";
});
inp.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

init();
