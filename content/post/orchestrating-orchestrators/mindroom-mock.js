/* Mock-ups of MindRoom Chat for the post "I used to orchestrate agents. Now I orchestrate orchestrators.".
   Hand-written look-alikes with demo data, not the real app, plus a live carousel of three real agent canvases.
   Mounts on every <div class="mr-room-evolution">, <div class="mr-fold-demo">, and <div class="mr-canvas-carousel">. */
(() => {
  const SCRIPT_URL = (document.currentScript && document.currentScript.src) || location.href;
  const CSS = `
.mrm{font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;background:#1b1b1f;color:#e7e7ea;border:1px solid #34343a;border-radius:12px;padding:12px;margin:1.2em 0;text-align:left}
.mrm *{box-sizing:border-box}
.mrm button{font:inherit;color:inherit;cursor:pointer}
.mrm-steps{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}
.mrm-step{background:#26262b;border:1px solid #3a3a41;border-radius:999px;padding:3px 10px;font-size:12.5px}
.mrm-step:hover{border-color:#5b5b66}
.mrm-step.on{background:#6d5bd0;border-color:#6d5bd0;color:#fff}
.mrm-cap{color:#b9b9c2;font-size:13px;min-height:2.6em;margin:2px 2px 8px}
.mrm-room{background:#131316;border:1px solid #2c2c32;border-radius:10px;overflow:hidden}
.mrm-head{display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid #2c2c32;font-weight:600}
.mrm-head small{font-weight:400;color:#8f8f99}
.mrm-bar{display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:7px 10px;border-bottom:1px solid #2c2c32;font-size:12px}
.mrm-chip{border:1px solid #3a3a41;border-radius:7px;padding:3px 9px;background:#202025;color:#c9c9d1;transition:background .15s,border-color .15s}
.mrm-chip:hover{border-color:#646472;background:#28282f}
.mrm-chip.on{background:#3a2a16;border-color:#a96a1e;color:#f0b25d}
.mrm-chip.sort{margin-left:auto}
.mrm-list{padding:8px 10px;min-height:120px}
.mrm-empty{padding:20px 8px;text-align:center;color:#8f8f99;font-size:13px}
.mrm-t{transition:transform .45s cubic-bezier(.2,.7,.2,1),opacity .3s;margin:0 0 6px}
.mrm-t.new{opacity:0}
.mrm-row{display:flex;gap:9px;padding:6px 4px}
.mrm-av{flex:none;width:28px;height:28px;border-radius:50%;background:#7c5a3a;color:#fff;font-weight:600;font-size:12px;display:grid;place-items:center}
.mrm-meta{font-size:12px;color:#8f8f99}.mrm-meta b{color:#e7e7ea;font-weight:600;margin-right:6px}
.mrm-badge{display:inline-flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:4px;padding:3px 9px;border-radius:8px;background:#222228;border:1px solid #34343a;font-size:12.5px;color:#b9b9c2}
.mrm-badge b{color:#e7e7ea;font-weight:600}
.mrm-badge.done{background:#17301f;border-color:#2e6b42;color:#9fd3ae}
.mrm-badge.clickable{cursor:pointer}
.mrm-badge.clickable:hover{border-color:#5b5b66}
.mrm-card{border:1px solid #34343a;border-left:3px solid #55555e;border-radius:9px;background:#212126;padding:7px 10px}
.mrm-card.working{border-left-color:#e8912d}.mrm-card.needs{border-left-color:#8b7bf0}
.mrm-card.later{border-left-color:#c9a227;background:#2a2412}.mrm-card.done{border-left-color:#3c9a5c;background:#17301f}
.mrm-ctop{display:flex;justify-content:space-between;gap:8px}
.mrm-title{font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mrm-ago{flex:none;font-size:12px;color:#8f8f99}.mrm-card.working .mrm-ago{color:#e8912d}
.mrm-line{font-size:12.5px;color:#b9b9c2;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mrm-cbot{display:flex;flex-wrap:wrap;gap:5px;align-items:center;margin-top:4px;font-size:11.5px;color:#8f8f99}
.mrm-pill{border-radius:999px;padding:0 7px;background:#2e2e35;color:#c9c9d1}
.mrm-pill.tag{background:#3b2d55;color:#d2c4ff}
.mrm-dot{width:7px;height:7px;border-radius:50%;background:#e8912d;animation:mrm-pulse 1.1s infinite}
.mrm-right{margin-left:auto}
.mrm-sec{all:unset;display:flex;align-items:center;gap:6px;width:100%;cursor:pointer;font-size:12.5px;color:#b9b9c2;padding:6px 4px 5px;font-weight:600;border-radius:6px}
.mrm-sec:hover{color:#e7e7ea;background:#1c1c21}
@keyframes mrm-pulse{50%{opacity:.25}}
.mrm-nav{display:flex;gap:6px;justify-content:flex-end;margin-top:8px}
.mrm-btn{background:#26262b;border:1px solid #3a3a41;border-radius:8px;padding:4px 12px;font-size:13px}
.mrm-btn:hover:not(:disabled){border-color:#5b5b66;background:#2f2f36}
.mrm-btn:disabled{opacity:.45;cursor:default}
.mrm-note{font-size:11.5px;color:#7f7f89;margin-top:6px}
/* Fold demo */
.mrf-msg{display:flex;gap:10px;padding:10px 12px}
.mrf-msg + .mrf-msg{border-top:1px solid #222228}
.mrf-av.agent{background:#3b6ea8}
.mrf-body{min-width:0;flex:1}
.mrf-slot{margin-top:6px}
.mrf-fold{display:inline-flex;align-items:center;gap:6px;cursor:pointer;font-size:12.5px;font-weight:500;color:#b9b9c2;padding:4px 10px;border-radius:8px;background:#1e1e24;border:1px solid #32323b;transition:background .15s,border-color .15s,color .15s}
.mrf-fold:hover{background:#26262e;border-color:#4b4b58;color:#e7e7ea}
.mrf-fold .chev{display:inline-block;width:10px;text-align:center;color:#8f8f99}
.mrf-work{overflow:hidden;transition:max-height .4s ease,opacity .25s ease,margin .25s ease;margin-top:0}
.mrf-work.open{margin-top:8px;margin-bottom:10px}
.mrf-rail{border-left:2px solid #2e2e38;margin-left:5px;padding:2px 0 2px 12px;display:flex;flex-direction:column;gap:6px}
.mrf-think{background:#1a1b22;border:1px solid #2c2d3a;border-radius:8px;padding:7px 10px;font-size:12.5px;color:#a9afc2}
.mrf-think-h{font-size:11.5px;font-weight:600;color:#8f96ad;margin-bottom:3px;display:flex;align-items:center;gap:5px}
.mrf-think-b{line-height:1.45;color:#c5c9d6}
.mrf-tool{display:flex;align-items:center;gap:8px;font-size:12.5px;padding:5px 9px;border-radius:8px;background:#1c1c22;border:1px solid #2b2b34;min-width:0}
.mrf-tname{flex:none;font-weight:600;color:#c9c9d4;font-size:12px}
.mrf-tool code{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#9ea4b3;font:12px ui-monospace,SFMono-Regular,Menlo,monospace;background:transparent;padding:0;border:0}
.mrf-out{flex:none;font-size:11.5px;padding:1px 7px;border-radius:999px;background:#26262f;color:#a4a6b3}
.mrf-out.ok{background:#17301f;color:#8cd3a0}
.mrf-out.fail{background:#3a1d1f;color:#f29b9b}
.mrf-midtext{font-size:13px;line-height:1.45;color:#d6d6de;padding:2px 2px}
.mrf-answer{margin-top:8px;line-height:1.5;color:#ededf2}
.mrf-status{font-size:11.5px;color:#e8912d;margin-left:8px}.mrf-status.done{color:#6fbf87}
/* Canvas carousel */
.mrc-top{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-bottom:8px}
.mrc-tabs{display:flex;flex-wrap:wrap;gap:6px}
.mrc-actions{display:flex;align-items:center;gap:6px;margin-left:auto}
.mrc-count{font-size:12px;color:#8f8f99;min-width:2.5em;text-align:center}
.mrc-frame-wrap{background:#131316;border:1px solid #2c2c32;border-radius:10px;overflow:hidden;position:relative;color-scheme:dark}
.mrc-frame{display:block;width:100%;height:680px;border:0;background:#131316;color-scheme:dark}
.mrc-frame[hidden]{display:none}
.mrc-loading{padding:48px 16px;text-align:center;color:#8f8f99;font-size:13px}
@media (max-width:640px){.mrc-frame{height:560px}.mrm-chip.sort{margin-left:0}}
@media (prefers-reduced-motion:reduce){.mrm-t,.mrf-work{transition:none}.mrm-dot{animation:none}}
`;
  const el = (tag, cls, html) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  };
  const ensureCss = () => {
    if (!document.getElementById('mrm-css')) document.head.appendChild(Object.assign(el('style', null, CSS), { id: 'mrm-css' }));
  };

  // ---- 1. The room, in six versions -------------------------------------------------------------
  const BASE_THREADS = [
    { id: 'typo', first: 'typo in the readme, second paragraph', title: '✏️ README typo', state: 'done', ago: '5h', mins: 300, replies: 2, line: 'Fixed and merged.', tags: [], badge: '#804' },
    { id: 'docs', first: 'the plugin docs are out of date I think', title: '📚 Plugin SDK docs', state: 'done', ago: '4m', mins: 4, replies: 9, line: 'Merged. The docs match the SDK again.', tags: ['docs'], badge: '#811' },
    { id: 'rebase', first: 'remind me monday to rebase our homeserver fork', title: '🔁 Rebase the homeserver fork', state: 'later', ago: '1d', mins: 1440, replies: 4, line: 'Snoozed until Monday 9:00', tags: ['infra'], badge: '💤 Mon 9:00' },
    { id: 'rename', first: 'ok next thing, the toolkit names are confusing, see what we discussed', title: '🧰 File and coding toolkit names', state: 'needs', ago: '31m', mins: 31, replies: 57, line: 'Question: keep the old name as an alias, or rename everywhere?', tags: ['design'], badge: '#815' },
    { id: 'ios', first: 'when I go back to a room on my phone it loses my scroll position, look into that', title: '📱 Scroll position lost on Back', state: 'needs', ago: '6m', mins: 6, replies: 23, line: 'Fixed, with a test. The pull request is ready for your review.', tags: ['bug', 'ios'], badge: '#822' },
    { id: 'search', first: 'hm, search is slow again when I type two words', title: '🔎 Slow multi-word search', state: 'working', ago: '2m', mins: 2, replies: 18, line: '🔧 9 tools · profiling the query', tags: ['bug'], badge: '🌿 search-perf' },
    { id: 'ci', first: 'check CI on that PR every ten minutes and merge it when it is green', title: '✅ Merge #815 when CI passes', state: 'later', ago: '8m', mins: 8, replies: 12, line: 'Checks CI again in 6 min', tags: [], badge: '⏱ in 6 min' },
    { id: 'load', first: 'the load test from yesterday, rerun it with 500 users and fix whatever breaks', title: '🚦 Load test at 500 users', state: 'working', ago: 'now', mins: 0, replies: 41, line: '🔧 27 tools · 3 sub-agents · rerunning the 500-user profile', tags: ['perf'], badge: '🌿 load-test-500' },
  ];
  const STEPS = [
    ['First messages', 'A room like in any chat app. You see the first message of each thread, and you have to open it to know what it became.'],
    ['Titles', 'Every thread gets an AI-generated title, shown in the room.'],
    ['Resolve', 'A thread I am done with can be resolved, which marks it green.'],
    ['Sort and filter', 'Sort on latest reply or reply count, and filter out resolved or idle threads. Click Unresolved, Working, Scheduled, or the sort button below to try them.'],
    ['Cards', 'The Compact view: one card per thread, with its title, what the agent is doing, and when it last replied.'],
    ['Sections', 'The cards grouped under Needs you, Working, Later and Done. Click Group, the filters, the sort button, or any section header below.'],
  ];
  const SECTIONS = [['needs', 'Needs you'], ['working', 'Working'], ['later', 'Later'], ['done', 'Done']];
  const SORTS = [
    ['latest', 'Last reply ↓', (a, b) => a.mins - b.mins],
    ['oldest', 'Oldest first ↑', (a, b) => b.mins - a.mins],
    ['replies', 'Most replies ↓', (a, b) => b.replies - a.replies],
  ];

  const rowHtml = (t, step) => {
    const done = step >= 2 && t.state === 'done';
    const title = step >= 1 ? `<b>${t.title}</b> · ` : '';
    return `<div class="mrm-row"><div class="mrm-av">B</div><div><div class="mrm-meta"><b>Bas</b>${t.ago} ago</div>
      <div>${t.first}</div>
      <div class="mrm-badge${done ? ' done' : ''}">💬 ${title}${t.replies} replies${done ? ' · ✓ resolved' : ''}</div></div></div>`;
  };
  const cardHtml = (t) => {
    const tags = t.tags.map((x) => `<span class="mrm-pill tag">${x}</span>`).join('');
    const live = t.state === 'working' ? '<span class="mrm-dot"></span>' : '';
    const check = t.state === 'done' ? '✓ ' : '';
    return `<div class="mrm-card ${t.state}"><div class="mrm-ctop"><span class="mrm-title">${check}${t.title}</span><span class="mrm-ago">${t.ago}</span></div>
      <div class="mrm-line"><b>DevAgent:</b> ${t.line}</div>
      <div class="mrm-cbot">${live}<span class="mrm-pill">${t.badge}</span>${tags}<span class="mrm-right">💬 ${t.replies}</span></div></div>`;
  };

  function mountRoom(root) {
    ensureCss();
    root.classList.add('mrm');
    const threads = BASE_THREADS.map((t) => ({ ...t, origState: t.state }));
    let step = Math.min(STEPS.length - 1, Number(root.dataset.step) || 0);
    let hideDone = true;
    let onlyWorking = false;
    let onlyScheduled = false;
    let grouped = true;
    let sortIdx = 0;
    const secOpen = { working: true, needs: true, later: true, done: false };

    const steps = el('div', 'mrm-steps');
    const cap = el('div', 'mrm-cap');
    const room = el('div', 'mrm-room');
    const head = el('div', 'mrm-head', '# dev <small>interactive demo · click buttons to try</small>');
    const bar = el('div', 'mrm-bar');
    const list = el('div', 'mrm-list');
    room.append(head, bar, list);
    const nav = el('div', 'mrm-nav');
    const prev = el('button', 'mrm-btn', '‹ Back');
    const next = el('button', 'mrm-btn', 'Next ›');
    nav.append(prev, next);
    root.append(steps, cap, room, nav, el('div', 'mrm-note', 'A mock-up in JavaScript with demo data, not the real app. The filter, sort, group and section buttons are interactive.'));
    const nodes = new Map(threads.map((t) => [t.id, el('div', 'mrm-t')]));
    const pills = STEPS.map(([name], i) => {
      const b = el('button', 'mrm-step', `${i + 1}. ${name}`);
      b.type = 'button';
      b.onclick = () => go(i);
      steps.append(b);
      return b;
    });

    function visible() {
      let ts = threads.slice();
      if (step >= 3) {
        if (hideDone) ts = ts.filter((t) => t.state !== 'done');
        if (onlyWorking) ts = ts.filter((t) => t.state === 'working');
        if (onlyScheduled) ts = ts.filter((t) => t.state === 'later');
        ts.sort(SORTS[sortIdx][2]);
      }
      return ts;
    }

    function makeChip(label, active, onClick, extraCls = '') {
      const b = el('button', `mrm-chip${active ? ' on' : ''}${extraCls ? ' ' + extraCls : ''}`, label);
      b.type = 'button';
      b.onclick = onClick;
      return b;
    }

    function renderBar() {
      bar.style.display = step >= 3 ? '' : 'none';
      bar.replaceChildren();
      if (step < 3) return;
      if (step >= 5) {
        bar.append(
          makeChip(hideDone ? 'Unresolved' : 'All', !hideDone, () => { hideDone = !hideDone; render(); }),
          makeChip('Working', onlyWorking, () => { onlyWorking = !onlyWorking; if (onlyWorking) onlyScheduled = false; render(); }),
          makeChip('Later', onlyScheduled, () => { onlyScheduled = !onlyScheduled; if (onlyScheduled) onlyWorking = false; render(); }),
          makeChip('▤ Group', grouped, () => { grouped = !grouped; render(); }),
          makeChip(SORTS[sortIdx][1], sortIdx !== 0, () => { sortIdx = (sortIdx + 1) % SORTS.length; render(); }, 'sort'),
        );
      } else {
        bar.append(
          makeChip('Unresolved', hideDone, () => { hideDone = !hideDone; render(); }),
          makeChip('Working', onlyWorking, () => { onlyWorking = !onlyWorking; if (onlyWorking) onlyScheduled = false; render(); }),
          makeChip('Scheduled', onlyScheduled, () => { onlyScheduled = !onlyScheduled; if (onlyScheduled) onlyWorking = false; render(); }),
          makeChip(SORTS[sortIdx][1], sortIdx !== 0, () => { sortIdx = (sortIdx + 1) % SORTS.length; render(); }, 'sort'),
        );
      }
    }

    function render() {
      const before = new Map();
      nodes.forEach((n, id) => n.isConnected && before.set(id, n.getBoundingClientRect().top));
      pills.forEach((b, i) => b.classList.toggle('on', i === step));
      cap.textContent = STEPS[step][1];
      renderBar();
      list.replaceChildren();
      const add = (t) => {
        const n = nodes.get(t.id);
        n.innerHTML = step >= 4 ? cardHtml(t) : rowHtml(t, step);
        list.append(n);
      };
      const vis = visible();
      if (step < 5 || !grouped) {
        if (!vis.length) list.append(el('div', 'mrm-empty', 'No threads match this filter.'));
        else vis.forEach(add);
      } else {
        let shownAny = false;
        for (const [key, label] of SECTIONS) {
          if (hideDone && key === 'done') continue;
          const ts = vis.filter((t) => t.state === key);
          if (!ts.length && (onlyWorking || onlyScheduled)) continue;
          shownAny = true;
          const open = secOpen[key];
          const h = el('button', 'mrm-sec', `<span>${open ? '▾' : '▸'}</span><span>${label} · ${ts.length}</span>`);
          h.type = 'button';
          h.onclick = () => { secOpen[key] = !secOpen[key]; render(); };
          list.append(h);
          if (open) ts.forEach(add);
        }
        if (!shownAny) list.append(el('div', 'mrm-empty', 'No threads match this filter.'));
      }
      nodes.forEach((n, id) => {
        if (!n.isConnected) return;
        if (!before.has(id)) {
          n.classList.add('new');
          requestAnimationFrame(() => n.classList.remove('new'));
          return;
        }
        const dy = before.get(id) - n.getBoundingClientRect().top;
        if (!dy) return;
        n.style.transition = 'none';
        n.style.transform = `translateY(${dy}px)`;
        n.getBoundingClientRect();
        n.style.transition = '';
        n.style.transform = '';
      });
      prev.disabled = step === 0;
      next.textContent = step === STEPS.length - 1 ? '↺ Start over' : 'Next ›';
    }
    function go(i) {
      step = (i + STEPS.length) % STEPS.length;
      if (step === 3 || step === 4) { hideDone = true; onlyWorking = false; onlyScheduled = false; }
      if (step === 5) { hideDone = false; onlyWorking = false; onlyScheduled = false; grouped = true; secOpen.done = false; }
      render();
    }
    prev.onclick = () => go(Math.max(0, step - 1));
    next.onclick = () => go(step + 1);
    render();
  }

  // ---- 2. A reply that folds its work when it is done ---------------------------------------------
  const WORK = [
    ['think', 'The scroll position is saved when the list unmounts, but navigating back reads it before the list has its height.'],
    ['tool', 'grep', '"scrollTop" src/room', '14 matches', ''],
    ['tool', 'read_file', 'src/room/CompactList.tsx', '212 lines', ''],
    ['tool', 'run_shell_command', 'pnpm test compact-scroll', '1 failed', 'fail'],
    ['text', 'The new test reproduces it. Restoring the position after the first layout pass should fix it.'],
    ['tool', 'edit_file', 'src/room/CompactList.tsx', '+9 -3', ''],
    ['tool', 'run_shell_command', 'pnpm test compact-scroll', '42 passed', 'ok'],
  ];
  const ANSWER = 'Fixed. Going back to a room now keeps your place in the list. The saved position was read before the list had its height, so I restore it after the first layout. I added a test that fails without the fix, and the pull request is open for your review.';

  function mountFold(root) {
    ensureCss();
    root.classList.add('mrm');
    let timers = [];
    const later = (ms, fn) => timers.push(setTimeout(fn, ms));
    const room = el('div', 'mrm-room');
    const replay = el('button', 'mrm-btn', '↺ Replay');
    replay.type = 'button';
    const nav = el('div', 'mrm-nav');
    nav.append(replay);
    root.append(room, nav, el('div', 'mrm-note', 'A mock-up in JavaScript with demo data, not the real app. Click the "Worked for" row to expand or collapse the trace.'));

    function play() {
      timers.forEach(clearTimeout);
      timers = [];
      room.innerHTML = `<div class="mrm-head">📱 Scroll position lost on Back <small>thread</small></div>
        <div class="mrf-msg"><div class="mrm-av">B</div><div class="mrf-body"><div class="mrm-meta"><b>Bas</b></div>
        when I go back to a room on my phone it loses my scroll position, look into that</div></div>
        <div class="mrf-msg"><div class="mrm-av mrf-av agent">D</div><div class="mrf-body">
        <div class="mrm-meta"><b>DevAgent</b><span class="mrf-status">● working</span></div>
        <div class="mrf-slot"></div><div class="mrf-work open"><div class="mrf-rail"></div></div><div class="mrf-answer"></div></div></div>`;
      const work = room.querySelector('.mrf-work');
      const rail = room.querySelector('.mrf-rail');
      const answer = room.querySelector('.mrf-answer');
      const status = room.querySelector('.mrf-status');
      const slot = room.querySelector('.mrf-slot');
      work.style.maxHeight = 'none';
      work.style.opacity = '1';
      let t = 450;
      for (const [kind, a, b, out, tone] of WORK) {
        later(t, () => {
          if (kind === 'think') {
            rail.append(el('div', 'mrf-think', `<div class="mrf-think-h">💭 Thought for 4s</div><div class="mrf-think-b">${a}</div>`));
          } else if (kind === 'text') {
            rail.append(el('div', 'mrf-midtext', a));
          } else {
            const row = el('div', 'mrf-tool', `<span class="mrf-tname">🔧 ${a}</span><code>${b}</code><span class="mrf-out">…</span>`);
            rail.append(row);
            later(420, () => {
              const badge = row.querySelector('.mrf-out');
              badge.textContent = out;
              if (tone) badge.classList.add(tone);
            });
          }
        });
        t += kind === 'tool' ? 700 : 850;
      }
      const words = ANSWER.split(' ');
      words.forEach((w, i) => later(t + i * 42, () => { answer.textContent += (i ? ' ' : '') + w; }));
      t += words.length * 42 + 550;
      later(t, () => {
        status.textContent = '✓ done';
        status.classList.add('done');
        const fold = el('button', 'mrf-fold', '<span class="chev">▸</span><span>Worked for 2m 41s · 5 tool calls</span>');
        fold.type = 'button';
        let open = false;
        const set = (o) => {
          open = o;
          work.classList.toggle('open', open);
          work.style.maxHeight = open ? `${work.scrollHeight + 16}px` : '0px';
          work.style.opacity = open ? '1' : '0';
          fold.querySelector('.chev').textContent = open ? '▾' : '▸';
          fold.setAttribute('aria-expanded', String(open));
        };
        fold.onclick = () => set(!open);
        work.style.maxHeight = `${work.scrollHeight + 16}px`;
        slot.append(fold);
        requestAnimationFrame(() => set(false));
      });
    }
    replay.onclick = play;
    play();
  }

  // ---- 3. Interactive carousel of real agent canvases --------------------------------------------
  let canvasesPromise = null;
  function loadCanvases() {
    if (window.__MR_CANVASES__) return Promise.resolve(window.__MR_CANVASES__);
    if (!canvasesPromise) {
      const url = new URL('canvases.json', SCRIPT_URL).href;
      canvasesPromise = fetch(url).then((r) => {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      });
    }
    return canvasesPromise;
  }

  function mountCanvasCarousel(root) {
    ensureCss();
    root.classList.add('mrm');
    const top = el('div', 'mrc-top');
    const tabs = el('div', 'mrc-tabs');
    const actions = el('div', 'mrc-actions');
    const prevTop = el('button', 'mrm-btn', '‹');
    prevTop.type = 'button';
    prevTop.setAttribute('aria-label', 'Previous canvas');
    const count = el('span', 'mrc-count', '1 / 3');
    const nextTop = el('button', 'mrm-btn', '›');
    nextTop.type = 'button';
    nextTop.setAttribute('aria-label', 'Next canvas');
    const openFull = el('button', 'mrm-btn', 'Open full page ↗');
    openFull.type = 'button';
    actions.append(prevTop, count, nextTop, openFull);
    top.append(tabs, actions);

    const cap = el('div', 'mrm-cap');
    const wrap = el('div', 'mrc-frame-wrap');
    const loading = el('div', 'mrc-loading', 'Loading interactive canvases…');
    wrap.append(loading);

    const nav = el('div', 'mrm-nav');
    const prevBot = el('button', 'mrm-btn', '← Previous');
    prevBot.type = 'button';
    const nextBot = el('button', 'mrm-btn', 'Next →');
    nextBot.type = 'button';
    nav.append(prevBot, nextBot);
    const note = el('div', 'mrm-note', 'Real canvases generated by my development agent, using placeholder data. Clicking submit shows a preview toast instead of sending to an agent.');
    root.append(top, cap, wrap, nav, note);

    loadCanvases().then((slides) => {
      loading.remove();
      const frames = new Array(slides.length).fill(null);
      let idx = 0;
      const btns = slides.map((s, i) => {
        const b = el('button', 'mrm-step', s.tab);
        b.type = 'button';
        b.onclick = () => show(i);
        tabs.append(b);
        return b;
      });
      function show(i) {
        idx = (i + slides.length) % slides.length;
        btns.forEach((b, j) => b.classList.toggle('on', j === idx));
        cap.textContent = slides[idx].caption;
        count.textContent = `${idx + 1} / ${slides.length}`;
        if (!frames[idx]) {
          const fr = document.createElement('iframe');
          fr.className = 'mrc-frame';
          fr.title = slides[idx].title;
          fr.setAttribute('sandbox', 'allow-scripts');
          fr.srcdoc = slides[idx].html;
          wrap.append(fr);
          frames[idx] = fr;
        }
        frames.forEach((fr, j) => { if (fr) fr.hidden = j !== idx; });
      }
      prevTop.onclick = prevBot.onclick = () => show(idx - 1);
      nextTop.onclick = nextBot.onclick = () => show(idx + 1);
      openFull.onclick = () => {
        const blob = new Blob([slides[idx].html], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank', 'noopener');
        setTimeout(() => URL.revokeObjectURL(url), 60000);
      };
      show(0);
    }).catch((err) => {
      loading.textContent = 'Could not load interactive canvases (' + err.message + ').';
    });
  }

  function mountAll() {
    document.querySelectorAll('.mr-room-evolution:not(.mrm)').forEach(mountRoom);
    document.querySelectorAll('.mr-fold-demo:not(.mrm)').forEach(mountFold);
    document.querySelectorAll('.mr-canvas-carousel:not(.mrm)').forEach(mountCanvasCarousel);
  }
  window.mindroomMock = { mountAll };
  mountAll();
  document.addEventListener('DOMContentLoaded', mountAll);
  let tries = 0;
  const poll = setInterval(() => { mountAll(); if (++tries > 20) clearInterval(poll); }, 250);
})();
