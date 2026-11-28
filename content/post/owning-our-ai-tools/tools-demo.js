// Auto-playing 4-step schema shrink animation for
// "Designing functions for AI isn't the same as designing them for humans"
// Real GitHub toolkit numbers from mindroom-ai/mindroom:
//   df7f97a04 (2026-11-24 PST): 39 functions, 6,670 o200k_base tokens
//   295a31a16 (2026-11-27 PST):  5 functions, 1,658 o200k_base tokens (-75.1%)
// Works standalone in Hugo (nijho.lt) and inside MindRoom review canvases.

(function initSchemaAnimation() {
  if (typeof document === "undefined") return;

  const STYLE_ID = "mr-tools-demo-styles";
  if (!document.getElementById(STYLE_ID)) {
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
      .td-card {
        margin: 1.4rem 0;
        padding: 0.95rem 1.05rem;
        border: 1px solid var(--mr-border, var(--line, #d8dee9));
        border-radius: 10px;
        background: var(--mr-surface, var(--surface, #f8fafc));
        color: var(--mr-text, var(--text, #0f172a));
        font-family: var(--mr-font, var(--body, system-ui, -apple-system, sans-serif));
        font-size: 0.9rem;
        line-height: 1.45;
      }
      .td-top {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.65rem;
      }
      .td-steps {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem;
      }
      .td-step-btn {
        appearance: none;
        border: 1px solid var(--mr-border, var(--line, #cbd5e1));
        background: var(--mr-bg, var(--bg, #ffffff));
        color: var(--mr-text-muted, var(--muted, #475569));
        border-radius: 999px;
        padding: 0.22rem 0.62rem;
        font: inherit;
        font-size: 0.78rem;
        cursor: pointer;
        transition: background 0.15s, color 0.15s, border-color 0.15s;
      }
      .td-step-btn:hover { border-color: var(--mr-accent, var(--accent, #3b82f6)); color: var(--mr-text, var(--text, #0f172a)); }
      .td-step-btn.active {
        background: var(--mr-accent, var(--accent, #3b82f6));
        color: var(--mr-accent-text, #ffffff);
        border-color: var(--mr-accent, var(--accent, #3b82f6));
        font-weight: 600;
      }
      .td-controls {
        display: inline-flex;
        gap: 0.35rem;
      }
      .td-ctrl {
        appearance: none;
        border: 1px solid var(--mr-border, var(--line, #cbd5e1));
        background: var(--mr-bg, var(--bg, #ffffff));
        color: var(--mr-text, var(--text, #1e293b));
        border-radius: 6px;
        padding: 0.22rem 0.55rem;
        font: inherit;
        font-size: 0.76rem;
        cursor: pointer;
      }
      .td-ctrl:hover { border-color: var(--mr-accent, var(--accent, #3b82f6)); }
      .td-caption {
        margin: 0 0 0.5rem;
        font-size: 0.86rem;
      }
      .td-bar-row {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: baseline;
        gap: 0.5rem;
        font-size: 0.8rem;
        margin-bottom: 0.28rem;
      }
      .td-bar-num { font-weight: 700; }
      .td-bar-num.good { color: var(--mr-success, var(--code-str, #15803d)); }
      .td-bar-track {
        position: relative;
        height: 11px;
        border-radius: 999px;
        background: var(--mr-border, var(--surface-2, #e2e8f0));
        overflow: hidden;
        margin-bottom: 0.7rem;
      }
      .td-bar-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #2563eb, #3b82f6);
        transition: width 0.55s cubic-bezier(0.22, 1, 0.36, 1), background 0.35s ease;
      }
      .td-bar-fill.done {
        background: linear-gradient(90deg, #16a34a, #22c55e);
      }
      .td-code {
        margin: 0;
        padding: 0.72rem 0.85rem;
        border: 1px solid var(--mr-border, var(--line, #cbd5e1));
        border-radius: 8px;
        background: var(--mr-bg, var(--bg, #ffffff));
        color: var(--mr-text, var(--text, #0f172a));
        font-family: var(--mono, ui-monospace, SFMono-Regular, Menlo, monospace);
        font-size: 0.76rem;
        line-height: 1.48;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        transition: opacity 0.2s ease;
      }
      .td-hl-red { background: rgba(239, 68, 68, 0.18); color: #b91c1c; border-radius: 3px; padding: 0 2px; }
      .td-hl-amber { background: rgba(245, 158, 11, 0.22); color: #92400e; border-radius: 3px; padding: 0 2px; }
      .td-hl-green { background: rgba(34, 197, 94, 0.18); color: #166534; border-radius: 3px; padding: 0 2px; }
      .td-muted { opacity: 0.55; }
      @media (prefers-color-scheme: dark) {
        :root:not([data-theme="light"]) .td-hl-red { background: rgba(239, 68, 68, 0.28); color: #fca5a5; }
        :root:not([data-theme="light"]) .td-hl-amber { background: rgba(245, 158, 11, 0.26); color: #fcd34d; }
        :root:not([data-theme="light"]) .td-hl-green { background: rgba(34, 197, 94, 0.26); color: #86efac; }
      }
      :root[data-theme="dark"] .td-hl-red { background: rgba(239, 68, 68, 0.28); color: #fca5a5; }
      :root[data-theme="dark"] .td-hl-amber { background: rgba(245, 158, 11, 0.26); color: #fcd34d; }
      :root[data-theme="dark"] .td-hl-green { background: rgba(34, 197, 94, 0.26); color: #86efac; }
    `;
    document.head.appendChild(style);
  }

  const BASE_TOK = 6670;
  const STEPS = [
    {
      short: "1. Start",
      label: "GitHub before: 39 functions, verbose anyOf optionals, and repeated helper args on every tool.",
      fns: 39,
      tok: 6670,
      done: false,
      code: `[
  {
    "name": "list_issues",
    "parameters": { "properties": {
      "repo_name": {"type": "string"},
      "state": <span class="td-hl-red">{"anyOf": [{"type": "string"}, {"type": "null"}], "default": null}</span>,
      <span class="td-hl-amber">"mindroom_output_path": {"anyOf": [{"type": "string"}, {"type": "null"}], "default": null, "description": "Optional workspace-relative path: save full supported output..."}</span>,
      <span class="td-hl-amber">"background_after": {"anyOf": [{"type": "number"}, {"type": "null"}], "description": "Seconds to wait before continuing as background job..."}</span>
    }}
  },
  <span class="td-muted">{ "name": "get_issue", ... }, { "name": "create_issue", ... }, ... (+36 more functions)</span>
]`,
    },
    {
      short: "2. Unwrap anyOf",
      label: "Unwrap Python X | None = None into plain JSON types instead of two-branch anyOf wrappers.",
      fns: 39,
      tok: 6085,
      done: false,
      code: `[
  {
    "name": "list_issues",
    "parameters": { "properties": {
      "repo_name": {"type": "string"},
      "state": <span class="td-hl-green">{"type": "string"}</span>,
      <span class="td-hl-amber">"mindroom_output_path": {"anyOf": [{"type": "string"}, {"type": "null"}], "default": null, "description": "Optional workspace-relative path: save full supported output..."}</span>,
      <span class="td-hl-amber">"background_after": {"anyOf": [{"type": "number"}, {"type": "null"}], "description": "Seconds to wait before continuing as background job..."}</span>
    }}
  },
  <span class="td-muted">{ "name": "get_issue", ... }, { "name": "create_issue", ... }, ... (+36 more functions)</span>
]`,
    },
    {
      short: "3. Share meta-params",
      label: "Explain background_after and mindroom_output_path once in the system prompt instead of 39 times.",
      fns: 39,
      tok: 5035,
      done: false,
      code: `[
  {
    "name": "list_issues",
    "parameters": { "properties": {
      "repo_name": {"type": "string"},
      "state": {"type": "string"}
    }}
  },
  {
    "name": "get_issue",
    "parameters": { "properties": { "repo_name": {"type": "string"}, "issue_number": {"type": "integer"} }}
  },
  <span class="td-muted">{ "name": "create_issue", ... }, ... (+36 more functions repeating repo_name)</span>
]`,
    },
    {
      short: "4. Read/write pairs",
      label: "Group verbs into 5 read/write action= tools. Same GitHub capabilities, 75% fewer tokens on every turn.",
      fns: 5,
      tok: 1658,
      done: true,
      code: `[
  {
    "name": <span class="td-hl-green">"github_read_issues_prs"</span>,
    "parameters": { "properties": {
      "action": {"enum": ["list_issues", "get_issue", "get_pull_requests", "get_pull_request", "..."]},
      "repo_name": {"type": "string"},
      "issue_number": {"type": "integer"}
    }}
  },
  {
    "name": <span class="td-hl-green">"github_write_issues"</span>,
    "parameters": { "properties": {
      "action": {"enum": ["create_issue", "comment_on_issue", "edit_issue", "close_issue", "..."]},
      "repo_name": {"type": "string"},
      "title": {"type": "string"}
    }}
  },
  <span class="td-muted">+ github_read_repo, github_write_pr, github_write_repo (5 functions total)</span>
]`,
    },
  ];

  function mountShrinker(el) {
    const reduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let idx = 0;
    let playing = !reduced;
    let timer = null;

    el.innerHTML = `
      <div class="td-card">
        <div class="td-top">
          <div class="td-steps" data-role="steps"></div>
          <div class="td-controls">
            <button type="button" class="td-ctrl" data-role="toggle">${playing ? "Pause" : "Play"}</button>
            <button type="button" class="td-ctrl" data-role="replay">Replay</button>
          </div>
        </div>
        <p class="td-caption" data-role="caption"></p>
        <div class="td-bar-row">
          <span data-role="meta"></span>
          <span class="td-bar-num" data-role="delta"></span>
        </div>
        <div class="td-bar-track"><div class="td-bar-fill" data-role="fill"></div></div>
        <pre class="td-code" data-role="code"></pre>
      </div>
    `;

    const stepsRow = el.querySelector('[data-role="steps"]');
    const stepBtns = STEPS.map((s, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "td-step-btn";
      b.textContent = s.short;
      b.addEventListener("click", () => {
        setPlaying(false);
        idx = i;
        render();
      });
      stepsRow.appendChild(b);
      return b;
    });

    const toggleBtn = el.querySelector('[data-role="toggle"]');
    const replayBtn = el.querySelector('[data-role="replay"]');

    function stopTimer() {
      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
    }

    function scheduleNext() {
      stopTimer();
      if (!playing) return;
      const delay = idx === STEPS.length - 1 ? 4200 : 2800;
      timer = setTimeout(() => {
        idx = (idx + 1) % STEPS.length;
        render();
        scheduleNext();
      }, delay);
    }

    function setPlaying(next) {
      playing = next;
      toggleBtn.textContent = playing ? "Pause" : "Play";
      if (playing) scheduleNext();
      else stopTimer();
    }

    toggleBtn.addEventListener("click", () => setPlaying(!playing));
    replayBtn.addEventListener("click", () => {
      idx = 0;
      render();
      setPlaying(true);
    });

    function render() {
      const s = STEPS[idx];
      const pct = Math.round(((s.tok - BASE_TOK) / BASE_TOK) * 100);
      const widthPct = Math.max(8, (s.tok / BASE_TOK) * 100);

      stepBtns.forEach((b, i) => b.classList.toggle("active", i === idx));
      el.querySelector('[data-role="caption"]').textContent = s.label;
      el.querySelector('[data-role="meta"]').textContent = `${s.fns} functions, ${s.tok.toLocaleString()} tokens/turn (${Math.round((s.tok * 40) / 1000)}k over 40 turns)`;
      const deltaEl = el.querySelector('[data-role="delta"]');
      deltaEl.textContent = pct === 0 ? "Baseline (100%)" : `${pct}% (${(BASE_TOK - s.tok).toLocaleString()} tok saved/turn)`;
      deltaEl.className = "td-bar-num" + (s.done ? " good" : "");

      const fill = el.querySelector('[data-role="fill"]');
      fill.style.width = `${widthPct}%`;
      fill.classList.toggle("done", s.done);

      el.querySelector('[data-role="code"]').innerHTML = s.code;
    }

    render();
    if (playing) scheduleNext();
  }

  function mountAll() {
    document.querySelectorAll(".mr-schema-shrinker").forEach((el) => {
      if (!el.dataset.mounted) {
        el.dataset.mounted = "1";
        mountShrinker(el);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountAll);
  } else {
    mountAll();
  }
  window.mountToolDesignDemos = mountAll;
})();
