// Auto-playing 4-step proportional schema shrink animation for
// "Designing functions for AI isn't the same as designing them for humans"
// Exact per-function o200k_base token counts measured from mindroom-ai/mindroom:
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
        padding: 1rem 1.05rem;
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
        margin: 0 0 0.55rem;
        font-size: 0.86rem;
      }
      .td-bar-row {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: baseline;
        gap: 0.5rem;
        font-size: 0.8rem;
        margin-bottom: 0.3rem;
      }
      .td-bar-num { font-weight: 700; }
      .td-bar-num.good { color: var(--mr-success, var(--code-str, #15803d)); }
      .td-stack-track {
        display: flex;
        height: 14px;
        border-radius: 999px;
        background: var(--mr-border, var(--surface-2, #e2e8f0));
        overflow: hidden;
        margin-bottom: 0.4rem;
      }
      .td-seg {
        height: 100%;
        transition: width 0.55s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.35s ease;
      }
      .td-seg-core { background: #16a34a; }
      .td-seg-wrap { background: #3b82f6; }
      .td-seg-anyof { background: #ef4444; }
      .td-seg-meta { background: #f59e0b; }
      .td-legend {
        display: flex;
        flex-wrap: wrap;
        gap: 0.35rem 0.75rem;
        font-size: 0.73rem;
        color: var(--mr-text-muted, var(--muted, #475569));
        margin-bottom: 0.8rem;
      }
      .td-leg-item {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        transition: opacity 0.3s ease;
      }
      .td-leg-item.gone { opacity: 0.38; text-decoration: line-through; }
      .td-dot {
        width: 8px;
        height: 8px;
        border-radius: 2px;
        flex: none;
      }
      .td-wall {
        border: 1px solid var(--mr-border, var(--line, #cbd5e1));
        border-radius: 8px;
        background: var(--mr-bg, var(--bg, #ffffff));
        padding: 0.65rem 0.75rem;
        margin-bottom: 0.7rem;
      }
      .td-wall-head {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: baseline;
        gap: 0.4rem;
        font-size: 0.74rem;
        color: var(--mr-text-muted, var(--muted, #475569));
        margin-bottom: 0.48rem;
      }
      .td-wall-head strong {
        color: var(--mr-text, var(--text, #0f172a));
        font-weight: 600;
      }
      .td-rows {
        display: flex;
        flex-direction: column;
        gap: 0.42rem;
      }
      .td-row {
        display: grid;
        grid-template-columns: 9.2rem 1fr 4.3rem;
        align-items: center;
        gap: 0.5rem;
      }
      @media (max-width: 540px) {
        .td-row {
          grid-template-columns: 1fr auto;
          gap: 0.2rem 0.4rem;
        }
        .td-row-track { grid-column: 1 / -1; }
      }
      .td-row-label {
        font-size: 0.74rem;
        color: var(--mr-text-muted, var(--muted, #475569));
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .td-row-tok {
        font-size: 0.73rem;
        font-variant-numeric: tabular-nums;
        text-align: right;
        color: var(--mr-text-muted, var(--muted, #475569));
        white-space: nowrap;
      }
      .td-row-tok.good {
        color: var(--mr-success, var(--code-str, #15803d));
        font-weight: 600;
      }
      .td-row-track {
        display: flex;
        align-items: stretch;
        gap: 2px;
        height: 24px;
        width: 100%;
        background: color-mix(in srgb, var(--mr-border, var(--surface-2, #e2e8f0)) 45%, transparent);
        border-radius: 5px;
        padding: 2px;
        overflow: hidden;
      }
      .td-tile {
        display: flex;
        align-items: center;
        min-width: 4px;
        height: 100%;
        border-radius: 3px;
        overflow: hidden;
        background: rgba(59, 130, 246, 0.22);
        border: 1px solid rgba(59, 130, 246, 0.45);
        position: relative;
        transition: width 0.5s cubic-bezier(0.22, 1, 0.36, 1), background 0.3s ease, border-color 0.3s ease;
        cursor: default;
      }
      .td-tile.focus {
        border-color: var(--mr-accent, var(--accent, #2563eb));
        box-shadow: 0 0 0 1px var(--mr-accent, var(--accent, #2563eb));
      }
      .td-tile.merged {
        background: rgba(22, 163, 74, 0.24);
        border-color: rgba(22, 163, 74, 0.75);
        flex: none;
      }
      .td-merged-name {
        display: inline-flex;
        align-items: center;
        padding-left: 0.45rem;
        font-family: var(--mono, ui-monospace, SFMono-Regular, Menlo, monospace);
        font-size: 0.7rem;
        color: var(--mr-text, var(--text, #0f172a));
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .td-merged-sub {
        font-family: var(--mr-font, var(--body, system-ui, -apple-system, sans-serif));
        color: var(--mr-text-muted, var(--muted, #475569));
        margin-left: 0.35rem;
      }
      .td-tile-body {
        flex: 1 1 auto;
        min-width: 0;
        height: 100%;
      }
      .td-cap-anyof { height: 100%; flex: none; background: rgba(239, 68, 68, 0.78); }
      .td-cap-meta { height: 100%; flex: none; background: rgba(245, 158, 11, 0.82); }
      .td-zoom-head {
        font-size: 0.75rem;
        color: var(--mr-text-muted, var(--muted, #475569));
        margin-bottom: 0.28rem;
      }
      .td-zoom-head code {
        font-family: var(--mono, ui-monospace, SFMono-Regular, Menlo, monospace);
        font-size: 0.74rem;
        color: var(--mr-text, var(--text, #0f172a));
      }
      .td-code {
        margin: 0;
        padding: 0.68rem 0.82rem;
        border: 1px solid var(--mr-border, var(--line, #cbd5e1));
        border-radius: 8px;
        background: var(--mr-bg, var(--bg, #ffffff));
        color: var(--mr-text, var(--text, #0f172a));
        font-family: var(--mono, ui-monospace, SFMono-Regular, Menlo, monospace);
        font-size: 0.74rem;
        line-height: 1.46;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
      }
      .td-hl-red { background: rgba(239, 68, 68, 0.18); color: #b91c1c; border-radius: 3px; padding: 0 2px; }
      .td-hl-amber { background: rgba(245, 158, 11, 0.22); color: #92400e; border-radius: 3px; padding: 0 2px; }
      .td-hl-green { background: rgba(34, 197, 94, 0.18); color: #166534; border-radius: 3px; padding: 0 2px; }
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
  const ROW_MAX_TOK = 1871; // Largest group at Step 1 (Read issues & PRs = 1,871 tok)

  // Every single real GitHub function from df7f97a04 -> 295a31a16 with exact o200k_base tokens:
  // [name, step1Tok, step2Tok (meta desc moved), step3Tok (anyOf unwrapped)]
  const GROUPS = [
    {
      label: "Read issues/PRs",
      afterName: "github_read_issues_prs",
      afterTok: 442,
      before: [
        ["list_issues", 204, 181, 171],
        ["get_issue", 129, 106, 96],
        ["list_issue_comments", 129, 106, 96],
        ["get_pull_requests", 254, 231, 221],
        ["get_pull_request", 141, 118, 108],
        ["get_pull_request_changes", 146, 123, 113],
        ["get_pull_request_comments", 167, 144, 134],
        ["get_pull_request_with_details", 150, 127, 117],
        ["get_pull_request_count", 219, 196, 186],
        ["search_issues_and_prs", 332, 309, 299],
      ],
    },
    {
      label: "Read repos",
      afterName: "github_read_repo",
      afterTok: 364,
      before: [
        ["list_repositories", 87, 64, 54],
        ["search_repositories", 251, 228, 218],
        ["get_repository", 116, 93, 83],
        ["get_repository_with_stats", 118, 95, 85],
        ["get_repository_languages", 118, 95, 85],
        ["get_repository_stars", 120, 97, 87],
        ["list_branches", 114, 91, 81],
        ["get_file_content", 172, 149, 139],
        ["get_directory_content", 177, 154, 144],
        ["get_branch_content", 142, 119, 109],
        ["search_code", 214, 191, 181],
      ],
    },
    {
      label: "Write repos",
      afterName: "github_write_repo",
      afterTok: 301,
      before: [
        ["create_repository", 200, 177, 167],
        ["delete_repository", 124, 101, 91],
        ["create_branch", 167, 144, 134],
        ["set_default_branch", 144, 121, 111],
        ["create_file", 203, 180, 170],
        ["update_file", 227, 204, 194],
        ["delete_file", 205, 182, 172],
      ],
    },
    {
      label: "Write issues",
      afterName: "github_write_issues",
      afterTok: 244,
      before: [
        ["create_issue", 155, 132, 122],
        ["edit_issue", 170, 147, 137],
        ["comment_on_issue", 152, 129, 119],
        ["close_issue", 126, 103, 93],
        ["reopen_issue", 129, 106, 96],
        ["assign_issue", 161, 138, 128],
        ["label_issue", 158, 135, 125],
      ],
    },
    {
      label: "Write PRs",
      afterName: "github_write_pr",
      afterTok: 310,
      before: [
        ["create_pull_request", 264, 241, 231],
        ["create_pull_request_comment", 243, 220, 210],
        ["edit_pull_request_comment", 163, 140, 130],
        ["create_review_request", 216, 193, 183],
      ],
    },
  ];

  const STEPS = [
    {
      short: "1. Start",
      label: "Before: 39 separate functions, each repeating shared arguments, anyOf wrappers, and helper-arg descriptions.",
      fns: 39,
      tok: 6670,
      segs: { core: 1658, wrap: 3725, anyof: 390, meta: 897 },
      tokIdx: 1,
      showMetaCap: true,
      showAnyofCap: true,
      merged: false,
      zoomTitle: "Zoom in on one of the 39 blocks: <code>list_issues</code> (204 tok)",
      code: `{
  "name": "list_issues",
  "parameters": { "properties": {
    "repo_name": {"type": "string", "description": "(str) The full name of the repository (e.g., 'owner/repo')."},
    "state": {"type": "string", "description": "(str) 'open', 'closed', 'all'. Defaults to 'open'."},
    "page": {"type": "integer"}, "per_page": {"type": "integer"},
    "mindroom_output_path": {
      <span class="td-hl-red">"anyOf": [{"type": "string"}, {"type": "null"}]</span>,
      <span class="td-hl-amber">"default": null, "description": "Optional workspace-relative path: save the full supported output there and return a short receipt."</span>
    }
  }}
}`,
    },
    {
      short: "2. Share meta-params",
      label: "Explain mindroom_output_path once in the system prompt instead of repeating its description 39 times (-897 tok).",
      fns: 39,
      tok: 5773,
      segs: { core: 1658, wrap: 3725, anyof: 390, meta: 0 },
      tokIdx: 2,
      showMetaCap: false,
      showAnyofCap: true,
      merged: false,
      zoomTitle: "Zoom in on one of the 39 blocks: <code>list_issues</code> (181 tok)",
      code: `{
  "name": "list_issues",
  "parameters": { "properties": {
    "repo_name": {"type": "string", "description": "(str) The full name of the repository (e.g., 'owner/repo')."},
    "state": {"type": "string", "description": "(str) 'open', 'closed', 'all'. Defaults to 'open'."},
    "page": {"type": "integer"}, "per_page": {"type": "integer"},
    "mindroom_output_path": {<span class="td-hl-red">"anyOf": [{"type": "string"}, {"type": "null"}]</span>}
  }}
}`,
    },
    {
      short: "3. Unwrap anyOf",
      label: "Unwrap optional Python X | None = None unions into plain JSON types across all 39 functions (-390 tok).",
      fns: 39,
      tok: 5383,
      segs: { core: 1658, wrap: 3725, anyof: 0, meta: 0 },
      tokIdx: 3,
      showMetaCap: false,
      showAnyofCap: false,
      merged: false,
      zoomTitle: "Zoom in on one of the 39 blocks: <code>list_issues</code> (171 tok)",
      code: `{
  "name": "list_issues",
  "parameters": { "properties": {
    "repo_name": {"type": "string", "description": "(str) The full name of the repository (e.g., 'owner/repo')."},
    "state": {"type": "string", "description": "(str) 'open', 'closed', 'all'. Defaults to 'open'."},
    "page": {"type": "integer"}, "per_page": {"type": "integer"},
    "mindroom_output_path": <span class="td-hl-green">{"type": "string"}</span>
  }}
}`,
    },
    {
      short: "4. Read/write pairs",
      label: "Collapse all 39 functions into 5 read/write action= tools. Same 39 GitHub actions, 75% fewer tokens on every turn.",
      fns: 5,
      tok: 1658,
      segs: { core: 1658, wrap: 0, anyof: 0, meta: 0 },
      tokIdx: 3,
      showMetaCap: false,
      showAnyofCap: false,
      merged: true,
      zoomTitle: "Zoom in on one of the 5 merged tools: <code>github_read_issues_prs</code> (442 tok, replaces 10 functions)",
      code: `{
  "name": <span class="td-hl-green">"github_read_issues_prs"</span>,
  "parameters": { "properties": {
    "action": {"enum": ["list_issues", "get_issue", "list_issue_comments", "get_pull_requests", "get_pull_request", "..."]},
    "repo_name": {"type": "string"},
    "issue_number": {"type": "integer"}, "pr_number": {"type": "integer"},
    "state": {"type": "string"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}
  }}
}`,
    },
  ];

  function renderWall(step) {
    return GROUPS.map((g) => {
      if (step.merged) {
        const pct = ((g.afterTok / ROW_MAX_TOK) * 100).toFixed(2);
        return `
          <div class="td-row">
            <span class="td-row-label">${g.label}</span>
            <div class="td-row-track">
              <div class="td-tile merged" style="width:${pct}%" title="${g.afterName}: ${g.afterTok} tok (replaces ${g.before.length} functions)"></div>
              <span class="td-merged-name">${g.afterName}<span class="td-merged-sub">(${g.before.length} actions)</span></span>
            </div>
            <span class="td-row-tok good">${g.afterTok} tok</span>
          </div>`;
      }
      const rowTok = g.before.reduce((s, f) => s + f[step.tokIdx], 0);
      const tiles = g.before
        .map((f) => {
          const [name, t1, t2, t3] = f;
          const cur = f[step.tokIdx];
          const wPct = ((cur / ROW_MAX_TOK) * 100).toFixed(2);
          const metaPct = step.showMetaCap ? (((t1 - t2) / cur) * 100).toFixed(1) : "0";
          const anyofPct = step.showAnyofCap ? (((t2 - t3) / cur) * 100).toFixed(1) : "0";
          const focus = name === "list_issues" ? " focus" : "";
          const caps =
            (step.showAnyofCap ? `<span class="td-cap-anyof" style="width:${anyofPct}%"></span>` : "") +
            (step.showMetaCap ? `<span class="td-cap-meta" style="width:${metaPct}%"></span>` : "");
          return `<div class="td-tile${focus}" style="width:${wPct}%" title="${name}: ${cur} tok"><span class="td-tile-body"></span>${caps}</div>`;
        })
        .join("");
      return `
        <div class="td-row">
          <span class="td-row-label">${g.label} (${g.before.length})</span>
          <div class="td-row-track">${tiles}</div>
          <span class="td-row-tok">${rowTok.toLocaleString()} tok</span>
        </div>`;
    }).join("");
  }

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
          <span class="td-bar-num" data-role="num"></span>
        </div>
        <div class="td-stack-track">
          <div class="td-seg td-seg-core" data-seg="core"></div>
          <div class="td-seg td-seg-wrap" data-seg="wrap"></div>
          <div class="td-seg td-seg-anyof" data-seg="anyof"></div>
          <div class="td-seg td-seg-meta" data-seg="meta"></div>
        </div>
        <div class="td-legend" data-role="legend"></div>
        <div class="td-wall">
          <div class="td-wall-head">
            <strong data-role="wall-title"></strong>
            <span>Each block = 1 function, width proportional to tokens (same scale across all steps)</span>
          </div>
          <div class="td-rows" data-role="rows"></div>
        </div>
        <div class="td-zoom-head" data-role="zoom-head"></div>
        <pre class="td-code" data-role="code"></pre>
      </div>
    `;

    const stepsEl = el.querySelector('[data-role="steps"]');
    const toggleBtn = el.querySelector('[data-role="toggle"]');
    const replayBtn = el.querySelector('[data-role="replay"]');
    const captionEl = el.querySelector('[data-role="caption"]');
    const metaEl = el.querySelector('[data-role="meta"]');
    const numEl = el.querySelector('[data-role="num"]');
    const segEls = {
      core: el.querySelector('[data-seg="core"]'),
      wrap: el.querySelector('[data-seg="wrap"]'),
      anyof: el.querySelector('[data-seg="anyof"]'),
      meta: el.querySelector('[data-seg="meta"]'),
    };
    const legendEl = el.querySelector('[data-role="legend"]');
    const wallTitleEl = el.querySelector('[data-role="wall-title"]');
    const rowsEl = el.querySelector('[data-role="rows"]');
    const zoomHeadEl = el.querySelector('[data-role="zoom-head"]');
    const codeEl = el.querySelector('[data-role="code"]');

    const btns = STEPS.map((s, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "td-step-btn";
      b.textContent = s.short;
      b.addEventListener("click", () => {
        stop();
        render(i);
      });
      stepsEl.appendChild(b);
      return b;
    });

    function render(i) {
      idx = i;
      const s = STEPS[i];
      btns.forEach((b, j) => b.classList.toggle("active", j === i));
      captionEl.textContent = s.label;
      metaEl.textContent = `GitHub toolkit: ${s.fns} ${s.fns === 1 ? "function" : "functions"}`;
      const saved = Math.round(((BASE_TOK - s.tok) / BASE_TOK) * 100);
      numEl.textContent = saved > 0 ? `${s.tok.toLocaleString()} tokens (-${saved}%)` : `${s.tok.toLocaleString()} tokens`;
      numEl.classList.toggle("good", s.merged);

      for (const k of ["core", "wrap", "anyof", "meta"]) {
        segEls[k].style.width = `${((s.segs[k] / BASE_TOK) * 100).toFixed(2)}%`;
      }
      const items = [
        ["#16a34a", "Final 5-tool schema", 1658, false],
        ["#3b82f6", "39-fn wrappers & repeated args", 3725, s.segs.wrap === 0],
        ["#ef4444", "anyOf null wrappers", 390, s.segs.anyof === 0],
        ["#f59e0b", "Repeated helper descriptions", 897, s.segs.meta === 0],
      ];
      legendEl.innerHTML = items
        .map(
          ([col, name, tok, gone]) =>
            `<span class="td-leg-item${gone ? " gone" : ""}"><span class="td-dot" style="background:${col}"></span>${name}: ${tok.toLocaleString()} tok</span>`
        )
        .join("");

      wallTitleEl.textContent = s.merged
        ? "All 5 merged GitHub functions (same token scale)"
        : "All 39 GitHub functions grouped by target tool";
      rowsEl.innerHTML = renderWall(s);
      zoomHeadEl.innerHTML = s.zoomTitle;
      codeEl.innerHTML = s.code;
    }

    function schedule() {
      clearTimeout(timer);
      if (!playing) return;
      const delay = idx === STEPS.length - 1 ? 4500 : 3200;
      timer = setTimeout(() => {
        render((idx + 1) % STEPS.length);
        schedule();
      }, delay);
    }

    function stop() {
      playing = false;
      clearTimeout(timer);
      toggleBtn.textContent = "Play";
    }

    toggleBtn.addEventListener("click", () => {
      if (playing) {
        stop();
      } else {
        playing = true;
        toggleBtn.textContent = "Pause";
        schedule();
      }
    });

    replayBtn.addEventListener("click", () => {
      playing = true;
      toggleBtn.textContent = "Pause";
      render(0);
      schedule();
    });

    render(0);
    if (playing) schedule();
  }

  function boot() {
    document.querySelectorAll(".mr-schema-shrinker").forEach((el) => {
      if (!el.dataset.tdMounted) {
        el.dataset.tdMounted = "1";
        mountShrinker(el);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
