/* Mock-ups of MindRoom Chat for the post "How I develop right now".
   Hand-written look-alikes with demo data, not the real app.
   Mounts on every <div class="mr-room-evolution"> and <div class="mr-fold-demo">. */
(() => {
  const CSS = `
.mrm{font:14px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif;background:#1b1b1f;color:#e7e7ea;border:1px solid #34343a;border-radius:12px;padding:12px;margin:1.2em 0;text-align:left}
.mrm *{box-sizing:border-box}
.mrm button{font:inherit;color:inherit;cursor:pointer}
.mrm-steps{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}
.mrm-step{background:#26262b;border:1px solid #3a3a41;border-radius:999px;padding:3px 10px;font-size:12.5px}
.mrm-step.on{background:#6d5bd0;border-color:#6d5bd0;color:#fff}
.mrm-cap{color:#b9b9c2;font-size:13px;min-height:2.9em;margin:2px 2px 8px}
.mrm-room{background:#131316;border:1px solid #2c2c32;border-radius:10px;overflow:hidden}
.mrm-head{display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid #2c2c32;font-weight:600}
.mrm-head small{font-weight:400;color:#8f8f99}
.mrm-bar{display:flex;gap:6px;padding:7px 10px;border-bottom:1px solid #2c2c32;font-size:12px}
.mrm-chip{border:1px solid #3a3a41;border-radius:7px;padding:2px 8px;background:#202025;color:#c9c9d1}
.mrm-chip.on{background:#3a2a16;border-color:#a96a1e;color:#f0b25d}
.mrm-list{padding:8px 10px;min-height:120px}
.mrm-t{transition:transform .45s cubic-bezier(.2,.7,.2,1),opacity .3s;margin:0 0 6px}
.mrm-t.new{opacity:0}
.mrm-row{display:flex;gap:9px;padding:6px 4px}
.mrm-av{flex:none;width:28px;height:28px;border-radius:50%;background:#7c5a3a;color:#fff;font-weight:600;font-size:12px;display:grid;place-items:center}
.mrm-meta{font-size:12px;color:#8f8f99}.mrm-meta b{color:#e7e7ea;font-weight:600;margin-right:6px}
.mrm-badge{display:inline-flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:4px;padding:3px 9px;border-radius:8px;background:#222228;border:1px solid #34343a;font-size:12.5px;color:#b9b9c2}
.mrm-badge b{color:#e7e7ea;font-weight:600}
.mrm-badge.done{background:#17301f;border-color:#2e6b42;color:#9fd3ae}
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
.mrm-sec{all:unset;display:block;cursor:pointer;font-size:12.5px;color:#b9b9c2;padding:5px 2px 4px;font-weight:600}
@keyframes mrm-pulse{50%{opacity:.25}}
.mrm-nav{display:flex;gap:6px;justify-content:flex-end;margin-top:8px}
.mrm-btn{background:#26262b;border:1px solid #3a3a41;border-radius:8px;padding:3px 12px}
.mrm-note{font-size:11.5px;color:#7f7f89;margin-top:6px}
.mrf-msg{display:flex;gap:9px;padding:8px 6px}
.mrf-av.agent{background:#3b6ea8}
.mrf-body{min-width:0;flex:1}
.mrf-work{overflow:hidden;transition:max-height .5s ease,opacity .35s}
.mrf-think,.mrf-tool,.mrf-fold{font-size:12.5px;color:#b9b9c2;margin:3px 0;padding:3px 8px;border-radius:7px;background:#202025;border:1px solid #2f2f36}
.mrf-tool code{color:#e7e7ea;font:12px ui-monospace,SFMono-Regular,Menlo,monospace}
.mrf-tool .out{float:right;color:#8f8f99}
.mrf-fold{all:unset;display:inline-block;cursor:pointer;font-size:12.5px;color:#b9b9c2;padding:3px 9px;border-radius:7px;background:#202025;border:1px solid #2f2f36;margin:2px 0 5px}
.mrf-status{font-size:11.5px;color:#e8912d;margin-left:8px}.mrf-status.done{color:#6fbf87}
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
  const THREADS = [
    { id: 'typo', first: 'typo in the readme, second paragraph', title: '✏️ README typo', state: 'done', ago: '5h', mins: 300, replies: 2, line: 'Fixed and merged.', tags: [], badge: '#804' },
    { id: 'docs', first: 'the plugin docs are out of date I think', title: '📚 Plugin SDK docs', state: 'done', ago: '3h', mins: 180, replies: 9, line: 'Merged. The docs match the SDK again.', tags: ['docs'], badge: '#811' },
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
    ['Sort and filter', 'Sort on the latest reply and filter out the resolved threads. What is left is what I still have to look at.'],
    ['Cards', 'The Compact view: one card per thread, with its title, what the agent is doing, and when it last replied.'],
    ['Sections', 'The cards grouped under Working, Needs you, Later and Done. Click Done to open it.'],
  ];
  const SECTIONS = [['working', 'Working'], ['needs', 'Needs you'], ['later', 'Later'], ['done', 'Done']];

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
    let step = Math.min(STEPS.length - 1, Number(root.dataset.step) || 0);
    let doneOpen = false;
    const steps = el('div', 'mrm-steps');
    const cap = el('div', 'mrm-cap');
    const room = el('div', 'mrm-room');
    const head = el('div', 'mrm-head', '# dev <small>demo data</small>');
    const bar = el('div', 'mrm-bar');
    const list = el('div', 'mrm-list');
    room.append(head, bar, list);
    const nav = el('div', 'mrm-nav');
    const prev = el('button', 'mrm-btn', '‹ Back');
    const next = el('button', 'mrm-btn', 'Next ›');
    nav.append(prev, next);
    root.append(steps, cap, room, nav, el('div', 'mrm-note', 'A mock-up in JavaScript with demo data, not the real app.'));
    const nodes = new Map(THREADS.map((t) => [t.id, el('div', 'mrm-t')]));
    const pills = STEPS.map(([name], i) => {
      const b = el('button', 'mrm-step', `${i + 1}. ${name}`);
      b.onclick = () => go(i);
      steps.append(b);
      return b;
    });

    function visible() {
      let ts = THREADS.slice();
      if (step >= 3) ts = ts.slice().sort((a, b) => a.mins - b.mins);
      if (step === 3 || step === 4) ts = ts.filter((t) => t.state !== 'done');
      return ts;
    }
    function render() {
      const before = new Map();
      nodes.forEach((n, id) => n.isConnected && before.set(id, n.getBoundingClientRect().top));
      pills.forEach((b, i) => b.classList.toggle('on', i === step));
      cap.textContent = STEPS[step][1];
      bar.style.display = step >= 3 ? '' : 'none';
      bar.innerHTML = step >= 5
        ? '<span class="mrm-chip">All</span><span class="mrm-chip on">▤ Group</span>'
        : '<span class="mrm-chip on">Unresolved</span><span class="mrm-chip">Last reply ↓</span>';
      list.replaceChildren();
      const add = (t) => {
        const n = nodes.get(t.id);
        n.innerHTML = step >= 4 ? cardHtml(t) : rowHtml(t, step);
        list.append(n);
      };
      if (step < 5) visible().forEach(add);
      else {
        for (const [key, label] of SECTIONS) {
          const ts = visible().filter((t) => t.state === key);
          const open = key !== 'done' || doneOpen;
          const h = el('button', 'mrm-sec', `${open ? '▾' : '▸'} ${label} · ${ts.length}`);
          if (key === 'done') h.onclick = () => { doneOpen = !doneOpen; render(); };
          list.append(h);
          if (open) ts.forEach(add);
        }
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
    function go(i) { step = (i + STEPS.length) % STEPS.length; render(); }
    prev.onclick = () => go(Math.max(0, step - 1));
    next.onclick = () => go(step + 1);
    render();
  }

  // ---- 2. A reply that folds its work when it is done ---------------------------------------------
  const WORK = [
    ['think', 'The position is saved when the list unmounts, but Back reads it before the list has its height.'],
    ['tool', 'grep', '"scrollTop" src/room', '14 matches'],
    ['tool', 'read_file', 'src/room/CompactList.tsx', '212 lines'],
    ['tool', 'run_shell_command', 'pnpm test compact-scroll', '1 failed'],
    ['text', 'The new test reproduces it. Restoring the position after the first layout should fix it.'],
    ['tool', 'edit_file', 'src/room/CompactList.tsx', '+9 −3'],
    ['tool', 'run_shell_command', 'pnpm test compact-scroll', '42 passed'],
  ];
  const ANSWER = 'Fixed. Going back to a room now keeps your place in the list. The saved position was read before the list had its height, so I restore it after the first layout. I added a test that fails without the fix, and the pull request is open for your review.';

  function mountFold(root) {
    ensureCss();
    root.classList.add('mrm');
    let timers = [];
    const later = (ms, fn) => timers.push(setTimeout(fn, ms));
    const room = el('div', 'mrm-room');
    const replay = el('button', 'mrm-btn', '↺ Replay');
    const nav = el('div', 'mrm-nav');
    nav.append(replay);
    root.append(room, nav, el('div', 'mrm-note', 'A mock-up in JavaScript with demo data, not the real app. Click the "Worked for" row to open it.'));

    function play() {
      timers.forEach(clearTimeout);
      timers = [];
      room.innerHTML = `<div class="mrm-head">📱 Scroll position lost on Back <small>thread</small></div>
        <div class="mrf-msg"><div class="mrm-av">B</div><div class="mrf-body"><div class="mrm-meta"><b>Bas</b></div>
        when I go back to a room on my phone it loses my scroll position, look into that</div></div>
        <div class="mrf-msg"><div class="mrm-av mrf-av agent">D</div><div class="mrf-body">
        <div class="mrm-meta"><b>DevAgent</b><span class="mrf-status">● working</span></div>
        <div class="mrf-slot"></div><div class="mrf-work"></div><div class="mrf-answer"></div></div></div>`;
      const work = room.querySelector('.mrf-work');
      const answer = room.querySelector('.mrf-answer');
      const status = room.querySelector('.mrf-status');
      const slot = room.querySelector('.mrf-slot');
      let t = 500;
      for (const [kind, a, b, out] of WORK) {
        later(t, () => {
          if (kind === 'think') work.append(el('div', 'mrf-think', `💭 Thought for 4 s · ${a}`));
          else if (kind === 'text') work.append(el('div', null, a));
          else {
            const row = el('div', 'mrf-tool', `🔧 ${a} <code>${b}</code><span class="out">…</span>`);
            work.append(row);
            later(450, () => { row.querySelector('.out').textContent = out; });
          }
        });
        t += kind === 'tool' ? 750 : 900;
      }
      const words = ANSWER.split(' ');
      words.forEach((w, i) => later(t + i * 45, () => { answer.textContent += (i ? ' ' : '') + w; }));
      t += words.length * 45 + 600;
      later(t, () => {
        status.textContent = '✓ done';
        status.classList.add('done');
        const fold = el('button', 'mrf-fold', '▸ Worked for 2m 41s · 5 tool calls');
        let open = false;
        const set = (o) => {
          open = o;
          work.style.maxHeight = open ? `${work.scrollHeight}px` : '0px';
          work.style.opacity = open ? '1' : '0';
          fold.textContent = `${open ? '▾' : '▸'} Worked for 2m 41s · 5 tool calls`;
        };
        fold.onclick = () => set(!open);
        work.style.maxHeight = `${work.scrollHeight}px`;
        slot.append(fold);
        requestAnimationFrame(() => set(false));
      });
    }
    replay.onclick = play;
    play();
  }

  function mountAll() {
    document.querySelectorAll('.mr-room-evolution:not(.mrm)').forEach(mountRoom);
    document.querySelectorAll('.mr-fold-demo:not(.mrm)').forEach(mountFold);
  }
  window.mindroomMock = { mountAll };
  mountAll();
  document.addEventListener('DOMContentLoaded', mountAll);
  let tries = 0;
  const poll = setInterval(() => { mountAll(); if (++tries > 20) clearInterval(poll); }, 250);
})();
