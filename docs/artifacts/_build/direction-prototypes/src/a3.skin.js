/* A3 · Dispatcher's log: markup construction. The conversation is a calm log: turns grouped by speaker
   under a name line, soft 16px blocks, event lines with icons and times, the assistant's working steps as
   step cards, appointments as label-value rows with icons. Read by the shared engine as window.SKIN. */
(function () {
  'use strict';
  var I = {
    person: '<circle cx="10" cy="7" r="3"/><path d="M4.5 16.5c.7-2.9 2.9-4.5 5.5-4.5s4.8 1.6 5.5 4.5"/>',
    send: '<path d="M10 15.5v-11M5.5 9 10 4.5 14.5 9"/>',
    cal: '<rect x="3.5" y="4.5" width="13" height="12" rx="2.5"/><path d="M3.5 8.5h13M7 3v3M13 3v3"/>',
    clock: '<circle cx="10" cy="10" r="6.5"/><path d="M10 6.5V10l2.5 1.5"/>',
    pin: '<path d="M10 17s5-4.6 5-8.5a5 5 0 1 0-10 0C5 12.4 10 17 10 17Z"/><circle cx="10" cy="8.5" r="1.8"/>',
    receipt: '<path d="M5.5 3.5h9v13l-1.5-1-1.5 1-1.5-1-1.5 1-1.5-1-1.5 1z"/><path d="M8 7.5h4M8 10.5h4"/>',
    check: '<path d="m5 10.5 3 3 7-7"/>',
    info: '<circle cx="10" cy="10" r="6.5"/><path d="M10 9v4.5M10 6.6v.1"/>',
    shield: '<path d="M10 3.5 15.5 5.5v4.2c0 3.2-2.3 5.8-5.5 6.8-3.2-1-5.5-3.6-5.5-6.8V5.5z"/><path d="m7.6 10 1.7 1.7 3.2-3.2"/>',
    tool: '<path d="M12.5 4a3.5 3.5 0 0 0-3.3 4.6L4 13.8 6.2 16l5.2-5.2A3.5 3.5 0 0 0 16 7.5l-2 2-2-.5-.5-2 2-2a3.5 3.5 0 0 0-1-.5Z"/>',
    phone: '<path d="M6 3.5h2.5l1 3.5-1.7 1.2a8 8 0 0 0 4 4l1.2-1.7 3.5 1v2.5a1.5 1.5 0 0 1-1.6 1.5C9 15.2 4.8 11 4.5 5.1A1.5 1.5 0 0 1 6 3.5Z"/>',
    mail: '<rect x="3.5" y="5" width="13" height="10" rx="2"/><path d="m4 5.5 6 5 6-5"/>',
    lock: '<rect x="5" y="9" width="10" height="7.5" rx="2"/><path d="M7.5 9V7a2.5 2.5 0 0 1 5 0v2"/>',
    flag: '<path d="M5.5 16.5V4M5.5 4.5h8l-1.6 3 1.6 3h-8"/>',
    doc: '<path d="M6 3.5h5.5L15 7v9.5H6z"/><path d="M11 3.5V7h4M8 10.5h5M8 13h5"/>',
    pause: '<circle cx="10" cy="10" r="6.5"/><path d="M8.5 7.5v5M11.5 7.5v5"/>',
    wait: '<path d="M6.5 3.5h7M6.5 16.5h7M7 3.5c0 3.5 6 3.5 6 6.5s-6 3-6 6.5M13 3.5c0 3.5-6 3.5-6 6.5"/>',
    hand: '<path d="M7 10V5.5a1.3 1.3 0 0 1 2.6 0V9M9.6 9V4.3a1.3 1.3 0 0 1 2.6 0V9M12.2 9V5.5a1.3 1.3 0 0 1 2.6 0v5.5a5.5 5.5 0 0 1-9.6 3.7L3.6 12a1.3 1.3 0 0 1 2-1.7L7 11.6"/>',
    question: '<circle cx="10" cy="10" r="6.5"/><path d="M8.2 8.2a1.9 1.9 0 1 1 2.6 1.8c-.5.2-.8.6-.8 1.2v.3M10 13.8v.1"/>',
    chat: '<path d="M4 5.5A1.5 1.5 0 0 1 5.5 4h9A1.5 1.5 0 0 1 16 5.5v6a1.5 1.5 0 0 1-1.5 1.5H9l-3.5 3v-3h0A1.5 1.5 0 0 1 4 11.5z"/>'
  };
  function ic(n) { return '<svg class="ic" viewBox="0 0 20 20" aria-hidden="true" focusable="false">' + (I[n] || I.info) + '</svg>'; }
  function warnSolid() { return '<svg class="ic-warn" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 2.6 23 21.4H1z" fill="currentColor"/><path d="M12 9v6M12 17.6v.2" stroke="var(--safety-band)" stroke-width="2.4" stroke-linecap="round"/></svg>'; }
  function lv(icon, label, value, cls) { return '<div class="lv ' + (cls || '') + '"><span class="lv-i">' + ic(icon) + '</span><span class="lv-t"><span class="lv-l">' + label + '</span><span class="lv-v">' + value + '</span></span></div>'; }
  function evt(icon, text, time, cls) { return '<p class="evt ' + (cls || '') + '"><span class="evt-i">' + ic(icon) + '</span><span class="evt-t">' + text + '</span>' + (time ? '<time>' + time + '</time>' : '') + '</p>'; }
  function step(icon, title, kicker, body, cls) {
    return '<section class="step ' + (cls || '') + '"><header class="step-h"><span class="step-i">' + ic(icon) + '</span><span class="step-tt"><span class="step-k">' + kicker + '</span><h3 class="step-t">' + title + '</h3></span></header><div class="step-b">' + body + '</div></section>';
  }
  function sources(keys, c) {
    return '<div class="srcs">' + keys.map(function (k) {
      var s = c.SRC[k];
      return '<details class="src"><summary>' + ic('doc') + '<span>' + s.file + '</span><span class="src-v">' + s.ver + '</span></summary><div class="src-b"><q>' + s.quote + '</q>' + (s.note ? '<p>' + s.note + '</p>' : '') + '</div></details>';
    }).join('') + '</div>';
  }

  /* ---------- step cards and rows ---------- */
  function cChecks(S, c) {
    var st = S.cards.checks || {};
    var body = '<ol class="checks">' + c.CHECKS.map(function (t) { return '<li>' + t + '</li>'; }).join('') + '</ol>' +
      (st.done ? evt('check', st.choice === 'skip' ? 'Checks skipped' : 'Tried. Still not cooling', '', 'evt-in')
        : '<div class="acts"><button type="button" class="btn btn-p" data-act="choose" data-key="checks" data-val="skip" data-fk="checks-skip">Skip the checks</button>' +
          '<button type="button" class="btn btn-q" data-act="choose" data-key="checks" data-val="tried" data-fk="checks-tried">I tried them. Still not cooling</button></div>');
    return step('tool', 'Quick checks', 'Optional', body);
  }
  function cQuestion(card, S) {
    var st = S.cards[card.key] || {};
    var body = '<p class="q-t">' + card.q + '</p>' + (st.done ? evt('check', 'Answered: ' + { yes: 'Yes', no: 'No', skip: 'Skipped' }[st.choice], '', 'evt-in')
      : '<div class="acts" role="group" aria-label="Answer">' + [['yes', 'Yes'], ['no', 'No'], ['skip', 'Skip']].map(function (o) {
        return '<button type="button" class="btn btn-q" data-act="choose" data-key="' + card.key + '" data-val="' + o[0] + '" data-fk="' + card.key + '-' + o[0] + '">' + o[1] + '</button>';
      }).join('') + '</div>');
    return step('question', 'Question ' + card.n + ' of 2', 'Optional', body, 'step-q');
  }
  function cWhere(S, c) {
    var st = S.cards.where || {};
    var body = st.done ? lv('pin', 'Visit area', 'Kyle 78640 · our south zone')
      : '<form class="inl" data-form="where" novalidate><label class="in"><span>ZIP code or city</span><input id="where-input" data-bind="where.value" data-fk="where-input" value="' + c.esc(st.value || '') + '" autocomplete="postal-code"' + (st.err ? ' aria-invalid="true"' : '') + '></label>' +
        '<button class="btn btn-p" data-fk="where-go">Show windows</button></form>' + (st.err ? '<p class="err" role="alert">' + st.err + '</p>' : '');
    return step('pin', 'Where is the visit?', 'Assistant step', body);
  }
  function cSlots(S, c) {
    var st = S.cards.slots || {};
    var head = '<div class="lvs">' + lv('tool', 'Service', 'Repair visit · AC not cooling') + lv('pin', 'Area', 'Kyle 78640 · south zone') +
      lv('receipt', 'Standard fee', '$89 diagnostic visit · credited toward the repair if you approve it at the same visit') + '</div>';
    var days = '<div class="week"><p class="week-h">This week · Oct 19 – 24 · arrival windows</p>' + c.DAYS.map(function (d) {
      var chips = d.wins.filter(function (w) { return w[1] === 'open'; }).map(function (w) {
        var W = c.WIN[w[0]], sel = st.day === d.key && st.win === w[0];
        return '<button type="button" class="tchip' + (sel ? ' is-sel' : '') + '" data-act="slot-win" data-day="' + d.key + '" data-val="' + w[0] + '" data-fk="chip-' + d.d + '-' + w[0] + '" aria-pressed="' + sel + '"' + (st.done ? ' disabled' : '') + '>' +
          (sel ? ic('check') : '') + W.label + '</button>';
      }).join('');
      return '<div class="dayrow"><span class="dr-d">' + d.dow + ', Oct ' + d.d + '</span><span class="dr-c">' + (chips || '<span class="dr-full">Full, no open windows</span>') + '</span></div>';
    }).join('') + '</div>';
    var foot = st.done
      ? evt('check', 'Window chosen: ' + (function () { var d = null; c.DAYS.forEach(function (x) { if (x.key === st.day) d = x; }); return d.long + ', ' + c.WIN[st.win].label; })(), '', 'evt-in')
      : '<p class="hint">Members’ fees and member-only windows appear after the code. Windows are shown, not held.</p><div class="acts"><button type="button" class="btn btn-p" data-act="slot-book" data-fk="slot-book">Continue with this window</button></div>' +
        (st.err ? '<p class="err" role="alert">' + st.err + '</p>' : '');
    return step('cal', 'Repair visit', 'Open arrival windows', head + days + foot, 'step-slots');
  }
  function cCode(S, c) {
    var st = S.cards.code || {};
    var body;
    if (st.stage === 'locate' && !st.done) {
      body = '<form class="stack" data-form="locate" novalidate><div class="two">' +
        '<label class="in"><span>Name on the account</span><input data-bind="code.name" data-fk="loc-name" value="' + c.esc(st.name || '') + '" autocomplete="name"></label>' +
        '<label class="in"><span>Phone</span><input data-bind="code.phone" data-fk="loc-phone" value="' + c.esc(st.phone || '') + '" inputmode="tel" autocomplete="tel"></label></div>' +
        '<div class="acts"><button class="btn btn-p" data-fk="loc-send">Send the code</button></div></form>' + (st.err ? '<p class="err" role="alert">' + st.err + '</p>' : '') +
        '<p class="hint">Demo: the dataset’s test customer. The code goes to the phone on record, never to a number typed here.</p>';
      return step('shield', 'Confirming it’s you', 'Before booking', body);
    }
    if (st.done) return evt('shield', 'Verified for this chat · phone ending 02', '2:08 pm', 'evt-log');
    body = lv('phone', 'Code sent to', 'The phone on record, ending in 02') +
      '<form class="inl" data-form="code" novalidate><label class="in in-code"><span>6-digit code</span><input id="code-input" data-fk="code-input" inputmode="numeric" autocomplete="one-time-code" maxlength="6" value="' + (st.value || '') + '"' + (st.err ? ' aria-invalid="true" aria-describedby="code-err"' : '') + '></label>' +
      '<button class="btn btn-p" data-fk="code-verify">Verify</button></form>' + (st.err ? '<p class="err" id="code-err" role="alert">' + st.err + '</p>' : '') +
      '<p class="links"><a href="#code" data-act="inbox" data-fk="inbox-link">Open the demo inbox</a></p><p class="hint">Demo: codes go to a simulated inbox, never a real phone. A code lasts 10 minutes; 3 tries.</p>';
    return step('shield', 'Confirming it’s you', 'Code sent', body);
  }
  function cConfirm(S) {
    var v = S.visit;
    return evt('check', 'Booked · ' + v.day.long + ', ' + v.win.label, '2:08 pm', 'evt-log evt-good') +
      '<div class="rows">' + lv('cal', 'Date', v.day.full + ', 2026') + lv('clock', 'Arrival window', v.win.label + ' · the technician arrives any time inside it') +
      lv('person', 'Technician', v.tech) + lv('receipt', 'Fee', '$89 diagnostic visit · ' + v.feeNote.charAt(0).toLowerCase() + v.feeNote.slice(1)) +
      lv('info', 'Changes', 'Free until ' + v.freeUntil + '. After that, a $49 late-cancellation fee applies.') + '</div>';
  }
  function cAccount() {
    var rows = [['Diagnostic visit', '$89.00'], ['Contactor replacement', '$245.00'], ['After-hours dispatch', '$144.00']];
    return '<div class="rows">' + lv('receipt', 'Invoice', 'INV-204411 · issued Oct 2, 2026') + lv('cal', 'Due', 'Nov 1, 2026') + lv('info', 'Balance', '$478.00 · unpaid') +
      '<table class="lines"><caption class="sr">Invoice lines</caption><thead><tr><th scope="col">Line</th><th scope="col">Amount</th></tr></thead><tbody>' +
      rows.map(function (r) { return '<tr><td>' + r[0] + '</td><td>' + r[1] + '</td></tr>'; }).join('') + '</tbody><tfoot><tr><th scope="row">Total</th><td>$478.00</td></tr></tfoot></table></div>';
  }
  function byButton(S) {
    for (var i = S.items.length - 1; i >= 0 && i >= S.items.length - 3; i--) if (S.items[i].viaButton) return true;
    return false;
  }
  function cHandoff(S, c) {
    var r = S.request, st = S.cards.follow || {};
    var reason = byButton(S) ? 'You asked for a person.' : 'Billing disputes go to a person. I can’t change or remove charges.';
    var body = '<p class="reason">' + reason + '</p><p class="promise">' + c.TXT.promise + '</p><div class="lvs">' + lv('clock', 'Due', 'Mon Oct 19, 7:00 pm') + lv('receipt', 'Reference', r.ref) + '</div>';
    if (st.done) {
      body += '<div class="saved">' + ic(st.channel === 'email' ? 'mail' : 'phone') + '<p>' + (st.channel === 'email' ? 'We’ll follow up by email, at the address on your account.'
        : 'We’ll follow up by phone, at the number ending in 02, ' + { mornings: 'in the morning', afternoons: 'in the afternoon', any: 'at any time' }[st.when] + '.') + '</p>' +
        '<button type="button" class="btn btn-q btn-s" data-act="follow-change" data-fk="fu-change">Change</button></div>';
    } else {
      var radio = function (name, val, label, sub, on, act) {
        return '<label class="radio"><input type="radio" name="' + name + '" value="' + val + '" data-act="' + act + '" data-val="' + val + '" data-fk="fu-' + val + '"' + (on ? ' checked' : '') + '><span>' + label + (sub ? '<small>' + sub + '</small>' : '') + '</span></label>';
      };
      body += '<fieldset class="fu"><legend>' + c.TXT.followAsk + '</legend>' +
        radio('fu-ch', 'email', 'Email', 'the address on your account', st.channel === 'email', 'follow-ch') +
        radio('fu-ch', 'phone', 'Phone call', 'the number ending in 02', st.channel === 'phone', 'follow-ch') + '</fieldset>' +
        (st.channel === 'phone' ? '<fieldset class="fu"><legend>Best time to call</legend>' + [['mornings', 'Mornings'], ['afternoons', 'Afternoons'], ['any', 'Any time']].map(function (o) {
          return radio('fu-when', o[0], o[1], '', st.when === o[0], 'follow-when');
        }).join('') + '</fieldset>' : '') +
        '<div class="acts"><button type="button" class="btn btn-p pulse" data-act="follow-save" data-fk="fu-save">Confirm</button></div>';
    }
    return evt('receipt', 'Case ' + r.ref + ' created', '2:14 pm', 'evt-log') + step('hand', 'Passing this to a person', 'Assistant step', body, 'step-handoff');
  }
  function cQueued(S, c) {
    var joined = S.live === 'joined';
    var body = '<p class="reason">' + (byButton(S) ? 'You asked for a person.' : 'Billing disputes go to a person. I can’t change or remove charges.') + '</p>' +
      '<p class="promise">' + c.TXT.queued + '</p><div class="lvs">' + lv('receipt', 'Reference', S.request.ref) + '</div>' +
      (joined ? evt('person', 'A representative has joined this chat', '2:17 pm', 'evt-in') : evt('wait', 'Waiting for a representative · no time is promised', '', 'evt-in'));
    return evt('receipt', 'Case ' + S.request.ref + ' created', '2:14 pm', 'evt-log') + step('hand', 'Passing this to a person', 'Assistant step', body, 'step-handoff');
  }
  function card(cd, S, c) {
    switch (cd.type) {
      case 'checks': return cChecks(S, c);
      case 'question': return cQuestion(cd, S, c);
      case 'where': return cWhere(S, c);
      case 'slots': return S.cards.slots ? cSlots(S, c) : '';
      case 'confirm': return cConfirm(S, c);
      case 'code': return cCode(S, c);
      case 'account': return cAccount(S, c);
      case 'handoff': return cHandoff(S, c);
      case 'queued': return cQueued(S, c);
    }
    return '';
  }

  /* ---------- the log ---------- */
  var NAME = { assistant: 'Meridian assistant · automated', customer: 'You', rep: 'Riley · Representative (demo)' };
  function cont(it, S) {
    var i = S.items.indexOf(it), p = i > 0 ? S.items[i - 1] : null;
    return !!(p && p.kind === 'turn' && it.kind === 'turn' && p.who === it.who);
  }
  function turnHTML(who, time, html, extra, isCont) {
    var name = isCont ? '<span class="sr">' + NAME[who] + ': </span>' : '<p class="name">' + (who === 'assistant' ? '<span class="name-mk" aria-hidden="true">' + ic('chat') + '</span>' : who === 'rep' ? '<span class="name-mk name-rep" aria-hidden="true">' + ic('person') + '</span>' : '') + NAME[who] + '</p>';
    return '<div class="turn turn-' + who + (isCont ? ' is-cont' : '') + '">' + name + (html ? '<div class="blk">' + html + '</div>' : '') + (extra || '') + '<time class="t">' + time + '</time></div>';
  }
  function item(it, S, c) {
    if (it.kind === 'event') return '<div class="logevt' + (it.icon === 'person' ? ' is-join' : '') + '">' + evt(it.icon === 'pause' ? 'pause' : it.icon === 'person' ? 'person' : 'info', it.html, it.time) + '</div>';
    var extra = (it.card ? card(it.card, S, c) : '') + (it.after ? '<div class="blk">' + it.after + '</div>' : '') + (it.sources ? sources(it.sources, c) : '');
    var t = turnHTML(it.who, it.time, it.html, extra, cont(it, S));
    return it.quiet ? t.replace('class="turn turn-assistant', 'class="turn turn-assistant is-quiet') : t;
  }

  function safety(c, mode) {
    return '<section class="safety' + (mode ? ' safety-' + mode : '') + '"' + (mode ? '' : ' role="alert"') + ' aria-label="Danger: safety instruction">' +
      '<div class="sf-band">' + warnSolid() + '<p class="sf-w">DANGER</p></div><ol class="sf-list"><li><span class="sf-n" aria-hidden="true">1</span><p>' + c.TXT.safety1 + '</p></li>' +
      '<li><span class="sf-n" aria-hidden="true">2</span><p>' + c.TXT.safety2 + '</p></li></ol></section>';
  }

  /* ---------- what's settled ---------- */
  function panel(S, c, mode) {
    var h = mode === 'strip' ? '' : '<header class="pn-h"><h2>What’s settled</h2><p>Fills in as things are confirmed.</p></header>';
    if (S.safety) return h + safety(c, 'panel');
    var hl = function (k) { return S.hl === k ? ' is-hl' : ''; };
    var v = S.visit, r = S.request, out = h;
    if (S.staffing === 'sim') out += '<section class="pn-s' + hl('control') + '"><h3>' + ic(S.live === 'joined' ? 'pause' : 'chat') + 'Who is replying</h3><p>' + (S.live === 'joined' ? 'Riley (demo representative). The assistant is paused.' : 'The automated assistant.') + '</p></section>';
    out += '<section class="pn-s' + hl('visit') + (v ? '' : ' is-empty') + '"><h3>' + ic('cal') + 'Your visit</h3>' + (v ? '<div class="lvs">' + lv('clock', v.day.long, v.win.label) + lv('person', 'Technician', v.tech) + lv('receipt', 'Fee', '$89 diagnostic visit') + '</div>' : '<p>Nothing booked yet.</p>') + '</section>';
    if (r && r.live) out += '<section class="pn-s' + hl('request') + '"><h3>' + ic('receipt') + 'Your request</h3><div class="lvs">' + lv('receipt', 'Reference', r.ref) + '</div><p>' + (S.live === 'joined' ? 'A representative has joined this chat.' : 'Waiting for a representative to join. No time is promised.') + '</p></section>';
    else if (r) out += '<section class="pn-s' + hl('request') + '"><h3>' + ic('receipt') + 'Your request</h3><p>A representative will get back to you within 1 business day.</p><div class="lvs">' +
      lv('clock', 'Due', r.due) + lv('receipt', 'Reference', r.ref) + lv(r.follow && r.follow.channel === 'Email' ? 'mail' : 'phone', 'Follow-up', r.follow ? r.follow.channel + (r.follow.when ? ', ' + r.follow.when.toLowerCase() : '') : 'Not chosen yet') + '</div></section>';
    else out += '<section class="pn-s is-empty"><h3>' + ic('receipt') + 'Your request</h3><p>No request open.</p></section>';
    out += '<section class="pn-s' + hl('identity') + (S.identity ? '' : ' is-empty') + '"><h3>' + ic('shield') + 'Identity</h3><p>' + (S.identity === 'verified' ? 'Verified for this chat · phone ending 02' : S.identity === 'sent' ? 'Code sent to the phone ending in 02' : 'Not checked yet. Only needed for private details or a booking.') + '</p></section>';
    return out;
  }
  function stripSummary(S) {
    if (S.safety) return '<span class="st-danger">' + warnSolid() + 'DANGER · Leave the home</span>';
    var bits = [];
    if (S.visit) bits.push(ic('cal') + '<span>' + S.visit.day.long + ', ' + S.visit.win.label + '</span>');
    if (S.request) bits.push(ic('receipt') + '<span>' + S.request.ref + (S.request.live ? '' : ', due Mon 7:00 pm') + '</span>');
    return '<span class="st-l">What’s settled</span><span class="st-b">' + (bits.length ? bits.join('') : '<span class="st-none">Nothing yet</span>') + '</span>';
  }
  function staffing(S) { return ic('person') + (S.staffing === 'sim' ? 'Simulated staff on shift (demo)' : 'Nobody online'); }
  function banner(S, c) {
    if (S.staffing !== 'sim') return '';
    return '<p>' + ic('info') + c.TXT.staffBanner + '</p>' + (S.live === 'queued' ? '<button type="button" class="btn btn-q btn-s" data-act="demo-join">Demo: Riley claims the case and joins</button>' : '');
  }
  function assistantState(S) {
    var ref = S.request ? ' · Reference <b>' + S.request.ref + '</b>' : '';
    return S.live === 'joined' ? 'Riley (demo representative) is replying · assistant paused' + ref : 'Automated assistant' + ref;
  }

  function chatShell() {
    return '<div class="chat"><header class="ch-head"><div class="brand"><p class="brand-n">Meridian Home Comfort</p><p class="brand-s" id="assistant-state"></p></div>' +
      '<button type="button" class="link-b" data-act="stub" data-msg="The demo guide (SCR-3) is not part of this direction prototype.">Demo guide</button>' +
      '<div class="demo-bar" aria-label="Demo status"><span class="chip">' + ic('cal') + 'Fri Oct 16, 2026 (demo date)</span><span class="chip" id="staffing"></span></div></header>' +
      '<div id="banner" class="banner" hidden></div>' +
      '<details id="strip" class="strip"><summary id="strip-summary"></summary><div id="strip-body" class="strip-b"></div></details>' +
      '<div class="ch-main"><div class="ch-col"><div id="pinned" class="pinned" hidden></div>' +
      '<div id="thread" class="thread" role="log" aria-label="Conversation" tabindex="0"><p class="day-div"><span>Today · Fri Oct 16, 2026 (demo date)</span></p></div>' +
      '<form class="composer" data-form="composer"><div class="cp-top"><button type="button" class="talk" id="talk" data-act="talk">' + ic('person') + 'Talk to a person</button><span id="composer-hint" class="cp-hint"></span></div>' +
      '<div class="cp-row"><label for="composer-input" class="sr">Message</label><input id="composer-input" autocomplete="off"><button class="send" aria-label="Send">' + ic('send') + '</button></div></form></div>' +
      '<aside id="panel" class="panel" aria-label="What’s settled"></aside></div></div>';
  }
  function caseShell() {
    return '<div class="console"><header class="ch-head cs-head"><div class="brand"><p class="brand-n">Meridian staff console</p><p class="brand-s">Demo staff sign-in · Riley (demo representative)</p></div>' +
      '<div class="demo-bar"><span class="chip">' + ic('cal') + 'Fri Oct 16, 2026 (demo date)</span></div></header><div id="case-root" class="case-root"></div></div>';
  }
  function inbox() {
    return '<dialog id="inbox" class="inbox" aria-labelledby="inbox-h"><h2 id="inbox-h">Demo delivery inbox</h2><p class="hint">Simulated messages. Nothing is sent to anyone. This exists only so reviewers can complete verification.</p>' +
      '<div class="inbox-m"><p class="t">To the phone ending in 02 · Fri Oct 16, 2:07 pm</p><p>Your Meridian Home Comfort verification code is <b>482913</b>. It expires in 10 minutes.</p></div>' +
      '<div class="acts"><button type="button" class="btn btn-p" data-act="inbox-use">Use this code in the chat</button><button type="button" class="btn btn-q" data-act="inbox-close">Close</button></div></dialog>';
  }

  /* ---------- staff console (S2 layout, A3 construction) ---------- */
  function ptag(p, w) { return '<span class="ptag ptag-' + p + '">' + p + ' ' + w + '</span>'; }
  function preview(q, c) {
    if (q.ref === 'MHC-C-0007') return '“' + c.TXT.c5 + '”';
    if (q.ref === 'MHC-C-0008') return '“' + c.TXT.c6 + '”';
    return 'Seeded demo row. No conversation in this prototype.';
  }
  function qrow(q, CS, c) {
    var sel = CS.sel === q.ref;
    var due = q.overdue ? ic('clock') + '<span><b>Overdue</b>, was due ' + q.due + '</span>' : q.band === 'safety' ? ic('info') + '<span>' + q.note + '</span>' : ic('clock') + '<span>Due ' + q.due + '</span>';
    return '<li><button type="button" class="qrow' + (sel ? ' is-sel' : '') + '" data-act="case-select" data-val="' + q.ref + '" data-ref="' + q.ref + '" data-fk="q-' + q.ref + '"' + (sel ? ' aria-current="true"' : '') + '>' +
      '<span class="qr-1"><span class="qr-n">' + q.who + '</span>' + ptag(q.p, q.pword) + '</span><span class="qr-r">' + q.reason + ' · ' + q.ref + '</span>' +
      '<span class="qr-d' + (q.overdue ? ' is-over' : '') + '">' + due + '</span><span class="qr-p">' + preview(q, c) + '</span></button></li>';
  }
  function logTranscript(K, CS) {
    var out = '', prev = null;
    K.transcript.forEach(function (t) {
      if (t.who === 'event') { out += '<div class="logevt">' + evt('info', t.text, t.time) + '</div>'; prev = null; return; }
      var isCont = prev === t.who; prev = t.who;
      out += turnHTML(t.who, t.time, t.text, '', isCont);
    });
    var notes = [{ time: 'Fri 2:14 pm', who: 'System check', text: 'The invoice’s after-hours line ($144) differs from the fee schedule ($149). For staff only; not shown to the customer.' }]
      .concat(CS.acts.slice(2).map(function (a) { return { time: a.time, who: 'Riley (demo representative)', text: a.text }; }));
    out += notes.map(function (n) { return '<div class="note"><p class="note-h">' + ic('lock') + 'Internal note · ' + n.who + '</p><p>' + n.text + '</p><time class="t">' + n.time + '</time></div>'; }).join('');
    return '<div class="thread thread-mini">' + out + '</div>';
  }
  function caseView(CS, c) {
    var K = c.CASE;
    var wide = window.matchMedia('(min-width: 1100px)').matches;
    var safetyRows = c.QUEUE.filter(function (q) { return q.band === 'safety'; }), rest = c.QUEUE.filter(function (q) { return q.band !== 'safety'; });
    var queue = '<details class="q-col"' + (wide ? ' open' : '') + '><summary class="q-sum">' + ic('chat') + 'Queue · ' + c.QUEUE.length + ' cases</summary><div class="q-in">' +
      '<header class="col-h"><h2>Needs my action</h2><p>Safety and danger first, then by due time. Seeded demo cases.</p></header>' +
      '<h3 class="q-g">Safety and danger</h3><ul data-queue class="qlist">' + safetyRows.map(function (q) { return qrow(q, CS, c); }).join('') + '</ul>' +
      '<h3 class="q-g">By due time</h3><ul data-queue class="qlist">' + rest.map(function (q) { return qrow(q, CS, c); }).join('') + '</ul></div></details>';

    var brief;
    if (CS.sel !== K.ref) {
      brief = '<main class="brief" id="brief"><div class="card"><p>Seeded queue row. This direction prototype builds the brief only for MHC-C-0007.</p><div class="acts"><button type="button" class="cbtn cbtn-p" data-act="case-select" data-val="MHC-C-0007" data-fk="q-MHC-C-0007">Open MHC-C-0007</button></div></div></main>';
    } else {
      var secs = K.sections.map(function (s) {
        var items = s.items.map(function (x) {
          return '<li>' + (s.kind === 'decide' ? ic('question') : '') + '<span>' + x.t + (x.src ? ' <button type="button" class="srcchip" data-act="src-jump" data-val="' + x.src + '" data-fk="st-' + s.n + '-' + x.src + '">' + ic('doc') + x.tag + '</button>' : '') + '</span></li>';
        }).join('');
        return '<details class="bsec bsec-' + s.kind + '" open><summary><span class="bs-n">' + s.n + '</span>' + s.h + '</summary>' +
          (s.kind === 'claim' ? '<p class="nc">' + ic('info') + 'In the customer’s words. Not checked.</p>' : '') + '<ul>' + items + '</ul></details>';
      }).join('');
      var status = CS.claimed ? evt('person', 'Claimed by Riley (demo) · due Mon Oct 19, 7:00 pm', '', 'evt-status') : evt('wait', 'Unassigned, nobody owns it yet · due Mon Oct 19, 7:00 pm', '', 'evt-status');
      var acts = '<section class="cacts" aria-label="Actions"><div class="acts">' +
        (CS.claimed ? '' : '<button type="button" class="cbtn cbtn-p" data-act="case-claim" data-fk="act-claim">Claim</button>') +
        '<button type="button" class="cbtn" data-act="case-call" data-fk="act-call"' + (CS.claimed ? '' : ' disabled') + '>' + ic('phone') + 'Log a call</button>' +
        '<button type="button" class="cbtn" data-act="case-flag" data-fk="act-flag">' + ic('flag') + (CS.flagged ? 'Flagged' : 'Flag') + '</button>' +
        '<button type="button" class="cbtn" disabled>' + ic('chat') + 'Join chat</button></div>' +
        '<p class="hint">' + (CS.claimed ? '' : 'Claim the case to log a call. ') + 'Join chat works only while the customer is in a live chat; nobody was online when this case was made.</p>' +
        (CS.callOpen ? '<form class="mini" data-form="call"><fieldset class="fu"><legend>Log a call to the number ending in 02 (demo)</legend>' +
          '<label class="radio"><input type="radio" name="outcome" value="Reached the customer" data-fk="call-outcome" checked><span>Reached the customer</span></label>' +
          '<label class="radio"><input type="radio" name="outcome" value="No answer"><span>No answer</span></label></fieldset><p class="hint">Demo: recorded, not sent. No call is placed.</p><div class="acts"><button class="cbtn cbtn-p">Record</button></div></form>' : '') +
        (CS.flagOpen ? '<form class="mini" data-form="flag"><label class="in"><span>What is wrong?</span><select data-fk="flag-reason"><option>The brief left something out</option><option>An answer was wrong</option><option>The escalation was not needed</option></select></label><div class="acts"><button class="cbtn cbtn-p">Add to review list</button></div></form>' : '') +
        '<div class="activity">' + CS.acts.map(function (a) { return evt('info', a.text, a.time); }).join('') + '</div></section>';
      brief = '<main class="brief" id="brief"><article class="card case-card"><header class="case-h"><p class="case-l">' + ptag(K.p, K.pword) + '<span>' + K.ref + '</span></p><h1 class="case-t">' + K.title + '</h1>' + status + '</header>' +
        '<section class="promise-b" aria-label="Promise and follow-up"><div class="lvs">' + lv('chat', 'Promise shown to the customer', K.promise) + lv('clock', 'Due', K.due) +
        lv('phone', 'Follow up by', K.follow.channel) + lv('pin', 'Destination', K.follow.dest) + lv('cal', 'Best time', K.follow.when) + '</div></section>' +
        '<div class="bsecs">' + secs + '</div>' + acts + '</article></main>';
    }

    var tabs = '<div class="tabs" role="tablist" aria-label="Evidence">' +
      '<button type="button" role="tab" id="tab-sources" data-fk="tab-sources" aria-selected="' + (CS.tab === 'sources') + '" aria-controls="ev-panel" data-act="case-tab" data-val="sources">Sources (' + K.sources.length + ')</button>' +
      '<button type="button" role="tab" id="tab-conversation" data-fk="tab-conversation" aria-selected="' + (CS.tab === 'conversation') + '" aria-controls="ev-panel" data-act="case-tab" data-val="conversation">Conversation</button></div>';
    var ev = CS.tab === 'sources' ? K.sources.map(function (s) {
      var b = s.rows
        ? '<table class="snap"><caption class="sr">' + s.title + ': what the AI saw and now</caption><thead><tr><th scope="col">Field</th><th scope="col">What the AI saw<small>Fri 2:10 pm</small></th><th scope="col">Now<small>Fri 2:20 pm</small></th></tr></thead><tbody>' +
          s.rows.map(function (r) { return '<tr><th scope="row">' + r[0] + '</th><td>' + r[1] + '</td><td>' + r[2] + '</td></tr>'; }).join('') + '</tbody></table>'
        : '<blockquote class="quote">' + s.quote + '</blockquote>';
      return '<section class="card src-card' + (CS.hl === s.id ? ' is-hl' : '') + '" id="src-' + s.id + '" tabindex="-1"><h3>' + ic('doc') + s.title + '</h3><p class="src-meta">' + s.file + ' · ' + s.ver + '</p>' + b +
        (s.fact ? '<p class="fact"><span>Fact</span>' + s.fact + '</p>' : '') + evt('check', s.status, '', 'evt-in') + '</section>';
    }).join('') : logTranscript(K, CS);
    var evidence = '<aside class="evidence" aria-label="Evidence"><header class="col-h"><h2>Evidence</h2><p>What the AI saw, next to what is true now.</p></header>' + tabs + '<div id="ev-panel" role="tabpanel" aria-labelledby="tab-' + CS.tab + '" class="ev-p">' + ev + '</div></aside>';
    return '<div class="cs-grid">' + queue + brief + evidence + '</div>';
  }

  window.SKIN = {
    code: 'A3', name: 'Dispatcher’s log',
    chatShell: chatShell, caseShell: caseShell, item: item, panel: panel, stripSummary: stripSummary,
    staffing: staffing, banner: banner, assistantState: assistantState, safety: safety, inbox: inbox, caseView: caseView
  };
})();
