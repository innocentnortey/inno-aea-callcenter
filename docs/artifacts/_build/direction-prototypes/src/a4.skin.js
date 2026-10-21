/* A4 · Account statement: markup construction. Every reply that settles something is a quiet statement
   panel, the way a utility shows a bill: a two-tone sentence headline, label-value rows split by dotted
   hairlines, facts in pale inset wells, one calm action at the foot. Read by the shared engine as window.SKIN. */
(function () {
  'use strict';
  var I = {
    person: '<circle cx="10" cy="7" r="3"/><path d="M4.5 16.5c.7-2.9 2.9-4.5 5.5-4.5s4.8 1.6 5.5 4.5"/>',
    headset: '<path d="M4 11.5V10a6 6 0 0 1 12 0v1.5"/><rect x="3.5" y="11" width="3" height="4.5" rx="1.2"/><rect x="13.5" y="11" width="3" height="4.5" rx="1.2"/><path d="M15 15.5c0 1.2-1.6 2-4 2"/>',
    send: '<path d="M4 10h11.5M11.5 6 15.5 10l-4 4"/>',
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
    copy: '<rect x="7" y="7" width="9" height="9" rx="2"/><path d="M13 7V5.5A1.5 1.5 0 0 0 11.5 4h-6A1.5 1.5 0 0 0 4 5.5v6A1.5 1.5 0 0 0 5.5 13H7"/>',
    lock: '<rect x="5" y="9" width="10" height="7.5" rx="2"/><path d="M7.5 9V7a2.5 2.5 0 0 1 5 0v2"/>',
    flag: '<path d="M5.5 16.5V4M5.5 4.5h8l-1.6 3 1.6 3h-8"/>',
    doc: '<path d="M6 3.5h5.5L15 7v9.5H6z"/><path d="M11 3.5V7h4M8 10.5h5M8 13h5"/>',
    pause: '<circle cx="10" cy="10" r="6.5"/><path d="M8.5 7.5v5M11.5 7.5v5"/>',
    question: '<circle cx="10" cy="10" r="6.5"/><path d="M8.2 8.2a1.9 1.9 0 1 1 2.6 1.8c-.5.2-.8.6-.8 1.2v.3M10 13.8v.1"/>'
  };
  function ic(n) { return '<svg class="ic" viewBox="0 0 20 20" aria-hidden="true" focusable="false">' + (I[n] || I.info) + '</svg>'; }
  function warnSolid() { return '<svg class="ic-warn" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 2.6 23 21.4H1z" fill="currentColor"/><path d="M12 9v6M12 17.6v.2" stroke="var(--safety-band)" stroke-width="2.4" stroke-linecap="round"/></svg>'; }
  /* a two-tone sentence: light lead, semibold fact */
  function tt(lead, fact, tail, tag) { tag = tag || 'h3'; return '<' + tag + ' class="tt">' + (lead ? '<span class="tt-l">' + lead + ' </span>' : '') + '<span class="tt-f">' + fact + '</span>' + (tail ? '<span class="tt-l"> ' + tail + '</span>' : '') + '</' + tag + '>'; }
  function row(label, value, icon, end) { return '<div class="r">' + (icon ? '<span class="r-i">' + ic(icon) + '</span>' : '') + '<span class="r-l">' + label + '</span><span class="r-v">' + value + (end || '') + '</span></div>'; }
  function tag(icon, word, cls) { return '<span class="tag ' + (cls || '') + '">' + ic(icon) + word + '</span>'; }
  function panel(body, cls) { return '<section class="sp ' + (cls || '') + '">' + body + '</section>'; }
  function progress(n, of, label) { return '<div class="prog"><p class="prog-t">Step ' + n + ' of ' + of + ' · ' + label + '</p><div class="prog-track" aria-hidden="true"><span style="width:' + Math.round(n / of * 100) + '%"></span></div></div>'; }
  function timeline(steps) {
    return '<ol class="tl">' + steps.map(function (s) {
      return '<li class="is-' + s.st + '"><span class="tl-d" aria-hidden="true">' + (s.st === 'done' ? ic('check') : '') + '</span><span class="tl-b"><span class="tl-l">' + s.l + (s.st === 'now' ? '<span class="sr"> (current)</span>' : s.st === 'done' ? '<span class="sr"> (done)</span>' : '') + '</span>' + (s.t ? '<time>' + s.t + '</time>' : '<span class="tl-n">Not yet</span>') + '</span></li>';
    }).join('') + '</ol>';
  }
  function sources(keys, c) {
    return '<div class="srcs">' + keys.map(function (k) {
      var s = c.SRC[k];
      return '<details class="src"><summary>' + ic('doc') + '<span>Source: ' + s.file + '</span><span class="src-v">' + s.ver + '</span></summary><div class="src-b"><q>' + s.quote + '</q>' + (s.note ? '<p>' + s.note + '</p>' : '') + '</div></details>';
    }).join('') + '</div>';
  }

  /* ---------- statement panels ---------- */
  function cChecks(S, c) {
    var st = S.cards.checks || {};
    var body = tt('These quick checks sometimes fix it.', 'They’re optional.') + '<ol class="well checks">' + c.CHECKS.map(function (t) { return '<li>' + t + '</li>'; }).join('') + '</ol>' +
      (st.done ? '<p class="done">' + tag('check', st.choice === 'skip' ? 'Checks skipped' : 'Tried, still not cooling') + '</p>'
        : '<div class="foot"><button type="button" class="btn btn-p" data-act="choose" data-key="checks" data-val="skip" data-fk="checks-skip">Skip the checks</button>' +
          '<button type="button" class="btn btn-q" data-act="choose" data-key="checks" data-val="tried" data-fk="checks-tried">I tried them. Still not cooling</button></div>');
    return panel(body);
  }
  function cQuestion(card, S) {
    var st = S.cards[card.key] || {};
    var body = '<p class="kick">Question ' + card.n + ' of 2 · optional</p>' + tt('', card.q) + (st.done ? '<p class="done">' + tag('check', 'Answered: ' + { yes: 'Yes', no: 'No', skip: 'Skipped' }[st.choice]) + '</p>'
      : '<div class="foot" role="group" aria-label="Answer">' + [['yes', 'Yes'], ['no', 'No'], ['skip', 'Skip']].map(function (o) {
        return '<button type="button" class="btn btn-q" data-act="choose" data-key="' + card.key + '" data-val="' + o[0] + '" data-fk="' + card.key + '-' + o[0] + '">' + o[1] + '</button>';
      }).join('') + '</div>');
    return panel(body, 'sp-q');
  }
  function cWhere(S, c) {
    var st = S.cards.where || {};
    var body = progress(1, 3, 'Where is the visit') + (st.done ? tt('The visit is in', 'Kyle 78640, our south zone.')
      : tt('Where is the visit?', 'A ZIP code or city is enough.') + '<form class="inl" data-form="where" novalidate><label class="in"><span>ZIP code or city</span><input id="where-input" data-bind="where.value" data-fk="where-input" value="' + c.esc(st.value || '') + '" autocomplete="postal-code"' + (st.err ? ' aria-invalid="true"' : '') + '></label>' +
        '<button class="btn btn-p" data-fk="where-go">Show windows</button></form>' + (st.err ? '<p class="err" role="alert">' + st.err + '</p>' : ''));
    return panel(body);
  }
  function dayOf(c, k) { var d = null; c.DAYS.forEach(function (x) { if (x.key === k) d = x; }); return d; }
  function cSlots(S, c) {
    var st = S.cards.slots || {};
    var day = dayOf(c, st.day);
    var days = '<div class="days" role="group" aria-label="Day">' + c.DAYS.map(function (d) {
      var open = d.wins.filter(function (w) { return w[1] === 'open'; }).length, sel = d.key === st.day;
      return '<button type="button" class="dtile' + (sel ? ' is-sel' : '') + (open ? '' : ' is-full') + '" data-act="slot-day" data-val="' + d.key + '" data-fk="day-' + d.d + '" aria-pressed="' + sel + '"' + (st.done ? ' disabled' : '') + '><span class="dt-w">' + d.dow + '</span><span class="dt-d">' + d.d + '</span><span class="dt-o">' + (open ? open + ' open' : 'Full') + '</span></button>';
    }).join('') + '</div>';
    var wins = '<fieldset class="wins"><legend>Arrival windows · ' + day.full + '</legend><div class="wins-g">' + day.wins.map(function (w) {
      var W = c.WIN[w[0]], taken = w[1] !== 'open', sel = st.win === w[0];
      return '<button type="button" class="wtile' + (taken ? ' is-taken' : '') + (sel ? ' is-sel' : '') + '" data-act="slot-win" data-day="' + day.key + '" data-val="' + w[0] + '" data-fk="win-' + w[0] + '" aria-pressed="' + sel + '"' + (taken || st.done ? ' disabled' : '') + '>' +
        '<span class="wt-t">' + W.label + '</span><span class="wt-s">' + (taken ? 'Taken' : sel ? 'Chosen' : 'Open') + '</span></button>';
    }).join('') + '</div></fieldset>';
    var rows = '<div class="rows">' + row('Diagnostic visit (standard fee)', '$89') + row('Credit', 'Applied to the repair if you approve it at the same visit') + '</div>';
    var foot = st.done ? '<p class="done">' + tag('check', 'Window chosen: ' + day.long + ', ' + c.WIN[st.win].label) + '</p>'
      : '<p class="hint">Members’ fees and member-only windows appear after the code. Windows are shown, not held.</p><div class="foot"><button type="button" class="btn btn-p" data-act="slot-book" data-fk="slot-book">Continue with this window</button></div>' + (st.err ? '<p class="err" role="alert">' + st.err + '</p>' : '');
    return panel(progress(2, 3, 'Choose a window') + tt('Choose a window', 'this week.') + days + wins + rows + foot, 'sp-slots');
  }
  function cCode(S, c) {
    var st = S.cards.code || {};
    if (st.done) return panel(tt('You’re', 'verified for this chat.') + '<div class="rows">' + row('Code sent to', 'The phone on record, ending in 02', 'phone') + '</div>', 'sp-slim');
    var body = progress(3, 3, 'Confirm it’s you');
    if (st.stage === 'locate') {
      body += tt('Before I book it,', 'I need to confirm it’s you.') + '<form class="stack" data-form="locate" novalidate><div class="two">' +
        '<label class="in"><span>Name on the account</span><input data-bind="code.name" data-fk="loc-name" value="' + c.esc(st.name || '') + '" autocomplete="name"></label>' +
        '<label class="in"><span>Phone</span><input data-bind="code.phone" data-fk="loc-phone" value="' + c.esc(st.phone || '') + '" inputmode="tel" autocomplete="tel"></label></div>' +
        '<div class="foot"><button class="btn btn-p" data-fk="loc-send">Send the code</button></div></form>' + (st.err ? '<p class="err" role="alert">' + st.err + '</p>' : '') +
        '<p class="hint">Demo: the dataset’s test customer. The code goes to the phone on record, never to a number typed here.</p>';
      return panel(body);
    }
    body += tt('A 6-digit code went to', 'the phone ending in 02.') +
      '<form class="inl" data-form="code" novalidate><label class="in in-code"><span>6-digit code</span><input id="code-input" data-fk="code-input" inputmode="numeric" autocomplete="one-time-code" maxlength="6" value="' + (st.value || '') + '"' + (st.err ? ' aria-invalid="true" aria-describedby="code-err"' : '') + '></label>' +
      '<button class="btn btn-p" data-fk="code-verify">Verify</button></form>' + (st.err ? '<p class="err" id="code-err" role="alert">' + st.err + '</p>' : '') +
      '<p class="links"><a href="#code" data-act="inbox" data-fk="inbox-link">Open the demo inbox</a></p><p class="hint">Demo: codes go to a simulated inbox, never a real phone. A code lasts 10 minutes; 3 tries.</p>';
    return panel(body);
  }
  function cConfirm(S) {
    var v = S.visit;
    var body = '<p class="kick">' + tag('check', 'Booked') + '</p>' + tt('Your visit is booked for', v.day.full.split(',')[0] + ', ' + v.win.label + '.') +
      '<div class="rows">' + row('Date', v.day.long + ', 2026', 'cal') + row('Arrival window', v.win.label, 'clock') + row('Technician', v.tech, 'person') +
      row('Fee that applies', '$89 diagnostic visit', 'receipt') + row('Address', '901 Brookside Ct, Kyle (on record)', 'pin') + '</div>' +
      '<div class="well next"><p class="next-h">What happens next</p>' + timeline([{ l: 'Technician arrives inside the window', t: v.day.long + ', ' + v.win.label, st: 'now' }, { l: 'Repair approved or declined at the visit', st: 'todo' }]) +
      '<p class="hint">Free to change or cancel until ' + v.freeUntil + '. After that, a $49 late-cancellation fee applies.</p></div>';
    return panel(body, 'sp-confirm');
  }
  function cAccount() {
    var body = tt('Invoice INV-204411 is', '$478.00, unpaid.') + '<div class="rows">' + row('Diagnostic visit', '$89.00') + row('Contactor replacement', '$245.00') + row('After-hours dispatch', '$144.00') +
      row('Total', '$478.00', '', '') + row('Issued', 'Oct 2, 2026') + row('Due', 'Nov 1, 2026') + '</div>';
    return panel(body, 'sp-account');
  }
  function refChip(ref) { return '<span class="ref"><span class="mono">' + ref + '</span><button type="button" class="ref-c" data-act="copy" data-val="' + ref + '" aria-label="Copy reference ' + ref + '">' + ic('copy') + '</button></span>'; }
  function cHandoff(S, c) {
    var r = S.request, st = S.cards.follow || {};
    var head = '<header class="sp-h"><h3 class="sp-t">Your request</h3>' + refChip(r.ref) + '</header>' +
      '<p class="tt tt-p"><span class="tt-l">No representative is online right now. </span><span class="tt-f">A representative will get back to you within 1 business day, by Monday, October 19, 7:00 pm.</span><span class="tt-l"> Your reference is MHC-C-0007.</span></p>';
    var rows = '<div class="rows">' + row('Due', 'Mon Oct 19, 7:00 pm', 'clock') + row('Status', tag('clock', 'Waiting for a representative'), 'info') + '</div>';
    var fu;
    if (st.done) {
      fu = '<div class="rows">' + row('Follow-up', st.channel === 'email' ? 'Email, the address on your account' : 'Phone call, the number ending in 02, ' + { mornings: 'mornings', afternoons: 'afternoons', any: 'any time' }[st.when], st.channel === 'email' ? 'mail' : 'phone') + '</div>' +
        '<div class="foot"><button type="button" class="link" data-act="follow-change" data-fk="fu-change">Change follow-up</button></div>';
    } else {
      var tile = function (act, val, label, sub, on, icon) {
        return '<button type="button" class="ctile' + (on ? ' is-sel' : '') + '" aria-pressed="' + on + '" data-act="' + act + '" data-val="' + val + '" data-fk="fu-' + val + '">' + (icon ? ic(icon) : '') + '<span>' + label + (sub ? '<small>' + sub + '</small>' : '') + '</span></button>';
      };
      fu = '<fieldset class="fu"><legend>' + c.TXT.followAsk + '</legend><div class="ctiles">' + tile('follow-ch', 'email', 'Email', 'the address on your account', st.channel === 'email', 'mail') +
        tile('follow-ch', 'phone', 'Phone call', 'the number ending in 02', st.channel === 'phone', 'phone') + '</div>' +
        (st.channel === 'phone' ? '<div class="ctiles ctiles-3" role="group" aria-label="Best time to call">' + [['mornings', 'Mornings'], ['afternoons', 'Afternoons'], ['any', 'Any time']].map(function (o) { return tile('follow-when', o[0], o[1], '', st.when === o[0]); }).join('') + '</div>' : '') +
        '</fieldset><div class="foot"><button type="button" class="btn btn-p" data-act="follow-save" data-fk="fu-save">Save my choice</button></div>';
    }
    return panel(head + rows + fu, 'sp-handoff');
  }
  function cQueued(S, c) {
    var joined = S.live === 'joined';
    var body = '<header class="sp-h"><h3 class="sp-t">Your request</h3>' + refChip(S.request.ref) + '</header>' + tt('A representative will join this chat', 'when available.', 'You can keep chatting with me while you wait, if you like.', 'p') +
      '<div class="rows">' + row('Status', joined ? tag('person', 'A representative has joined') : tag('clock', 'Waiting for a representative'), 'info') + '</div>';
    return panel(body, 'sp-handoff');
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

  /* ---------- the conversation ---------- */
  var NAME = { assistant: 'Meridian assistant · automated', customer: 'You', rep: 'Riley · Representative (demo)' };
  function cont(it, S) { var i = S.items.indexOf(it), p = i > 0 ? S.items[i - 1] : null; return !!(p && p.kind === 'turn' && it.kind === 'turn' && p.who === it.who); }
  function turnHTML(who, time, html, extra, isCont) {
    var cap = isCont ? '<span class="sr">' + NAME[who] + ', ' + time + ': </span>' : '<p class="cap">' + (who === 'rep' ? '<span class="disc" aria-hidden="true">R</span>' : '') + NAME[who] + ' · <time>' + time + '</time></p>';
    return '<div class="turn turn-' + who + (isCont ? ' is-cont' : '') + '">' + cap + (html ? '<div class="say">' + html + '</div>' : '') + (extra || '') + '</div>';
  }
  function item(it, S, c) {
    if (it.kind === 'event') return '<p class="hair' + (it.icon === 'person' ? ' is-join' : '') + '"><span>' + ic(it.icon === 'pause' ? 'pause' : it.icon === 'person' ? 'person' : 'info') + it.html + ' · <time>' + it.time + '</time></span></p>';
    var extra = (it.card ? card(it.card, S, c) : '') + (it.after ? '<div class="say">' + it.after + '</div>' : '') + (it.sources ? sources(it.sources, c) : '');
    var t = turnHTML(it.who, it.time, it.html, extra, cont(it, S));
    return it.quiet ? t.replace('class="turn turn-assistant', 'class="turn turn-assistant is-quiet') : t;
  }

  function safety(c, mode) {
    return '<section class="safety' + (mode ? ' safety-' + mode : '') + '"' + (mode ? '' : ' role="alert"') + ' aria-label="Danger: safety instruction">' +
      '<div class="sf-band">' + warnSolid() + '<p class="sf-w">DANGER</p></div><ol class="sf-list"><li><span class="sf-n" aria-hidden="true">1</span><p>' + c.TXT.safety1 + '</p></li>' +
      '<li><span class="sf-n" aria-hidden="true">2</span><p>' + c.TXT.safety2 + '</p></li></ol></section>';
  }

  /* ---------- what's settled (C2) ---------- */
  function settled(S, c, mode) {
    var h = mode === 'strip' ? '' : '<header class="pn-h"><h2>What’s settled</h2><p>Fills in as things are confirmed.</p></header>';
    if (S.safety) return h + safety(c, 'panel');
    var hl = function (k) { return S.hl === k ? ' is-hl' : ''; };
    var v = S.visit, r = S.request, out = h;
    if (S.staffing === 'sim') out += panel('<h3 class="sp-t">Who is replying</h3><p class="pn-p">' + (S.live === 'joined' ? 'Riley (demo representative). The assistant is paused.' : 'The automated assistant.') + '</p>', 'pn-b' + hl('control'));
    out += v ? panel('<h3 class="sp-t">Your visit</h3>' + tt('', v.day.long + ', ' + v.win.label, '', 'p') + '<div class="rows">' + row('Technician', v.tech) + row('Fee', '$89 diagnostic visit') + '</div>', 'pn-b' + hl('visit'))
      : panel('<h3 class="sp-t">Your visit</h3><p class="pn-p is-empty">Nothing booked yet.</p>', 'pn-b pn-empty');
    if (r && r.live) out += panel('<header class="sp-h"><h3 class="sp-t">Your request</h3>' + refChip(r.ref) + '</header><p class="pn-p">' + (S.live === 'joined' ? 'A representative has joined this chat.' : 'Waiting for a representative to join. No time is promised.') + '</p>', 'pn-b' + hl('request'));
    else if (r) out += panel('<header class="sp-h"><h3 class="sp-t">Your request</h3>' + refChip(r.ref) + '</header>' + tt('A representative will get back to you', 'within 1 business day.', '', 'p') +
      '<div class="rows">' + row('Due', r.due) + row('Follow-up', r.follow ? r.follow.channel + (r.follow.when ? ', ' + r.follow.when.toLowerCase() : '') : 'Not chosen yet') + '</div>', 'pn-b' + hl('request'));
    else out += panel('<h3 class="sp-t">Your request</h3><p class="pn-p is-empty">No request open.</p>', 'pn-b pn-empty');
    out += panel('<h3 class="sp-t">Identity</h3><p class="pn-p' + (S.identity ? '' : ' is-empty') + '">' + (S.identity === 'verified' ? tag('shield', 'Verified for this chat') + ' phone ending 02' : S.identity === 'sent' ? 'Code sent to the phone ending in 02' : 'Not checked yet. Needed only for private details or a booking.') + '</p>', 'pn-b' + hl('identity') + (S.identity ? '' : ' pn-empty'));
    return out;
  }
  function stripSummary(S) {
    if (S.safety) return '<span class="st-danger">' + warnSolid() + 'DANGER · Leave the home</span>';
    var latest = S.request ? S.request.ref + (S.request.live ? ' · waiting for a representative' : ' · due Mon Oct 19, 7:00 pm') : S.visit ? S.visit.day.long + ' · ' + S.visit.win.label : '';
    return '<span class="st-l">What’s settled</span><span class="st-v' + (latest ? '' : ' is-empty') + '">' + (latest || 'Nothing yet') + '</span>';
  }
  function staffing(S) { return tag('person', S.staffing === 'sim' ? 'Simulated staff on shift (demo)' : 'Nobody online'); }
  function banner(S, c) {
    if (S.staffing !== 'sim') return '';
    return '<p>' + ic('info') + c.TXT.staffBanner + '</p>' + (S.live === 'queued' ? '<button type="button" class="link" data-act="demo-join">Demo: Riley claims the case and joins</button>' : '');
  }
  function assistantState(S) { return S.live === 'joined' ? 'Riley (demo representative) is replying · assistant paused' : 'Automated assistant'; }

  function chatShell() {
    return '<div class="chat"><header class="topbar"><div class="brand"><p class="brand-n">Meridian Home Comfort</p><p class="brand-s" id="assistant-state"></p></div>' +
      '<div class="demo-bar" aria-label="Demo status"><span id="staffing"></span><button type="button" class="link" data-act="stub" data-msg="The demo guide (SCR-3) is not part of this direction prototype.">Demo guide</button></div></header>' +
      '<div id="banner" class="banner" hidden></div>' +
      '<details id="strip" class="strip"><summary id="strip-summary"></summary><div id="strip-body" class="strip-b"></div></details>' +
      '<div class="ch-main"><div class="ch-col"><div id="pinned" class="pinned" hidden></div>' +
      '<div id="thread" class="thread" role="log" aria-label="Conversation" tabindex="0"><p class="hair hair-date"><span>Fri Oct 16, 2026 (demo date)</span></p></div>' +
      '<form class="composer" data-form="composer"><div class="cp-top"><button type="button" class="talk" id="talk" data-act="talk">' + ic('headset') + 'Talk to a person</button><span id="composer-hint" class="cp-hint"></span></div>' +
      '<div class="cp-row"><label for="composer-input" class="sr">Message</label><input id="composer-input" autocomplete="off"><button class="send">Send ' + ic('send') + '</button></div></form></div>' +
      '<aside id="panel" class="panel" aria-label="What’s settled"></aside></div></div>';
  }
  function caseShell() {
    return '<div class="console"><header class="topbar"><div class="brand"><p class="brand-n">Meridian staff console</p><p class="brand-s">Demo staff sign-in · Riley (demo representative)</p></div>' +
      '<div class="demo-bar"><span class="quiet-date">Fri Oct 16, 2026 (demo date)</span></div></header><div id="case-root" class="case-root"></div></div>';
  }
  function inbox() {
    return '<dialog id="inbox" class="inbox" aria-labelledby="inbox-h">' + tt('Demo delivery inbox.', 'Simulated messages.', '', 'h2') + '<p class="hint">Nothing is sent to anyone. This exists only so reviewers can complete verification.</p>' +
      '<div class="well"><p class="cap">To the phone ending in 02 · Fri Oct 16, 2:07 pm</p><p>Your Meridian Home Comfort verification code is <b class="mono">482913</b>. It expires in 10 minutes.</p></div>' +
      '<div class="foot"><button type="button" class="btn btn-p" data-act="inbox-use">Use this code in the chat</button><button type="button" class="btn btn-q" data-act="inbox-close">Close</button></div></dialog>';
  }

  /* ---------- staff console (S2 layout, A4 construction) ---------- */
  function ptag(q) { return q.p === 'P0' ? tag('info', 'Safety', 'tag-ink') : tag('flag', q.p + ' ' + q.pword); }
  function qrow(q, CS) {
    var sel = CS.sel === q.ref;
    var due = q.overdue ? '<b class="over">' + ic('clock') + 'Overdue</b>, was due ' + q.due : q.band === 'safety' ? q.note : 'Due ' + q.due;
    return '<li><button type="button" class="qrow' + (sel ? ' is-sel' : '') + '" data-act="case-select" data-val="' + q.ref + '" data-ref="' + q.ref + '" data-fk="q-' + q.ref + '"' + (sel ? ' aria-current="true"' : '') + '>' +
      '<span class="qr-1"><span class="qr-r">' + q.reason + '</span>' + ptag(q) + '</span><span class="qr-2">' + q.who + ' · <span class="mono">' + q.ref + '</span> · ' + due + '</span>' +
      '<span class="own" aria-label="Owner: ' + q.owner + '">' + (q.owner === 'Unowned' ? '–' : 'R') + '</span></button></li>';
  }
  function caseView(CS, c) {
    var K = c.CASE;
    var wide = window.matchMedia('(min-width: 1100px)').matches;
    var first = c.QUEUE.filter(function (q) { return q.band === 'safety'; }), rest = c.QUEUE.filter(function (q) { return q.band !== 'safety'; });
    var queue = '<details class="q-col"' + (wide ? ' open' : '') + '><summary class="q-sum">Queue · ' + c.QUEUE.length + ' cases</summary><div class="q-in">' +
      tt('Needs my action.', 'Safety first, then by due time.', '', 'h2') + '<p class="hint">Seeded demo cases.</p>' +
      panel('<h3 class="sp-t">Needs attention first</h3><ul data-queue class="qlist">' + first.map(function (q) { return qrow(q, CS); }).join('') + '</ul>', 'sp-q1') +
      panel('<h3 class="sp-t">By due time</h3><ul data-queue class="qlist">' + rest.map(function (q) { return qrow(q, CS); }).join('') + '</ul>') + '</div></details>';

    var brief;
    if (CS.sel !== K.ref) {
      brief = '<main class="brief" id="brief">' + panel(tt('Seeded queue row.', 'This prototype builds the brief only for MHC-C-0007.', '', 'p') + '<div class="foot"><button type="button" class="btn btn-p" data-act="case-select" data-val="MHC-C-0007" data-fk="q-MHC-C-0007">Open MHC-C-0007</button></div>') + '</main>';
    } else {
      var tlSteps = [{ l: 'Request created', t: 'Fri Oct 16, 2:14 pm', st: 'done' }, { l: 'Claimed', t: CS.claimed ? 'Fri Oct 16, 2:20 pm' : '', st: CS.claimed ? 'done' : 'now' }, { l: 'In progress', t: '', st: CS.claimed ? 'now' : 'todo' }, { l: 'Resolved', t: '', st: 'todo' }];
      var head = panel('<p class="kick">' + ptag({ p: K.p, pword: K.pword }) + refChip(K.ref) + '</p>' + tt('Billing dispute ·', 'due Mon Oct 19, 7:00 pm', '', 'h1') +
        '<div class="well">' + timeline(tlSteps) + '</div>', 'sp-head');
      var promise = panel('<h2 class="sp-t">Promise shown to the customer</h2>' + tt('', K.promise, '', 'p') + '<div class="rows">' + row('Due', K.due, 'clock') + row('Follow up by', K.follow.channel, 'phone') +
        row('Destination', K.follow.dest, 'pin') + row('Best time', K.follow.when, 'cal') + '</div>', 'sp-promise');
      var secs = K.sections.map(function (s) {
        var items = s.items.map(function (x) {
          return '<li><span>' + x.t + '</span>' + (x.src ? '<button type="button" class="srclink" data-act="src-jump" data-val="' + x.src + '" data-fk="st-' + s.n + '-' + x.src + '">' + x.tag + '</button>' : '') + '</li>';
        }).join('');
        var list = s.kind === 'claim' ? '<div class="well claims"><p class="cap">Customer says · not checked</p><ul>' + items + '</ul></div>' : '<ul class="dl ' + (s.kind === 'decide' ? 'dl-q' : '') + '">' + items + '</ul>';
        return '<section class="bsec"><h3 class="sp-t"><span class="bs-n">' + s.n + '</span>' + s.h + '</h3>' + list + '</section>';
      }).join('');
      var acts = '<div class="foot">' + (CS.claimed ? tag('check', 'Claimed by Riley (demo)') : '<button type="button" class="btn btn-p btn-c" data-act="case-claim" data-fk="act-claim">Claim</button>') +
        '<button type="button" class="btn btn-q btn-c" data-act="case-call" data-fk="act-call"' + (CS.claimed ? '' : ' disabled') + '>' + ic('phone') + 'Log a call</button>' +
        '<button type="button" class="btn btn-q btn-c" data-act="case-flag" data-fk="act-flag">' + ic('flag') + (CS.flagged ? 'Flagged' : 'Flag') + '</button>' +
        '<button type="button" class="btn btn-q btn-c" disabled>' + ic('headset') + 'Join chat</button></div>' +
        '<p class="hint">' + (CS.claimed ? '' : 'Claim the case to log a call. ') + 'Join chat works only while the customer is in a live chat; nobody was online when this case was made.</p>' +
        (CS.callOpen ? '<form class="well mini" data-form="call"><fieldset class="fu"><legend>Log a call to the number ending in 02 (demo)</legend>' +
          '<label class="rd"><input type="radio" name="outcome" value="Reached the customer" data-fk="call-outcome" checked> Reached the customer</label>' +
          '<label class="rd"><input type="radio" name="outcome" value="No answer"> No answer</label></fieldset><p class="hint">Demo: recorded, not sent. No call is placed.</p><div class="foot"><button class="btn btn-p btn-c">Record</button></div></form>' : '') +
        (CS.flagOpen ? '<form class="well mini" data-form="flag"><label class="in"><span>What is wrong?</span><select data-fk="flag-reason"><option>The brief left something out</option><option>An answer was wrong</option><option>The escalation was not needed</option></select></label><div class="foot"><button class="btn btn-p btn-c">Add to review list</button></div></form>' : '') +
        '<div class="rows act-log">' + CS.acts.map(function (a) { return row(a.time, a.text); }).join('') + '</div>';
      brief = '<main class="brief" id="brief">' + head + promise + panel(secs, 'sp-secs') + panel('<h2 class="sp-t">Actions</h2>' + acts, 'sp-acts') + '</main>';
    }

    var tabs = '<div class="tabs" role="tablist" aria-label="Evidence">' +
      '<button type="button" role="tab" id="tab-sources" data-fk="tab-sources" aria-selected="' + (CS.tab === 'sources') + '" aria-controls="ev-panel" data-act="case-tab" data-val="sources">Sources (' + K.sources.length + ')</button>' +
      '<button type="button" role="tab" id="tab-conversation" data-fk="tab-conversation" aria-selected="' + (CS.tab === 'conversation') + '" aria-controls="ev-panel" data-act="case-tab" data-val="conversation">Conversation</button></div>';
    var ev;
    if (CS.tab === 'sources') {
      ev = K.sources.map(function (s) {
        var b = s.rows
          ? '<table class="snap"><caption class="sr">' + s.title + ': what the AI saw and now</caption><thead><tr><th scope="col">Field</th><th scope="col">What the AI saw<small>Fri 2:10 pm</small></th><th scope="col">Now<small>Fri 2:20 pm</small></th></tr></thead><tbody>' +
            s.rows.map(function (r) { return '<tr><th scope="row">' + r[0] + '</th><td>' + r[1] + '</td><td>' + r[2] + '</td></tr>'; }).join('') + '</tbody></table>'
          : '<blockquote class="well quote">' + s.quote + '</blockquote>';
        return '<section class="sp src-sp' + (CS.hl === s.id ? ' is-hl' : '') + '" id="src-' + s.id + '" tabindex="-1"><h3 class="sp-t">' + s.title + '</h3><p class="hint">' + s.file + ' · ' + s.ver + '</p>' + b +
          (s.fact ? '<div class="rows">' + row('Fact', s.fact) + '</div>' : '') + '<p class="done">' + tag('check', s.status) + '</p></section>';
      }).join('');
    } else {
      var out = '', prev = null;
      K.transcript.forEach(function (t) {
        if (t.who === 'event') { out += '<p class="hair"><span>' + ic('info') + t.text + ' · <time>' + t.time + '</time></span></p>'; prev = null; return; }
        out += turnHTML(t.who, t.time, t.text, '', prev === t.who); prev = t.who;
      });
      var notes = [{ time: 'Fri 2:14 pm', who: 'System check', text: 'The invoice’s after-hours line ($144) differs from the fee schedule ($149). For staff only; not shown to the customer.' }]
        .concat(CS.acts.slice(2).map(function (a) { return { time: a.time, who: 'Riley (demo representative)', text: a.text }; }));
      out += notes.map(function (n) { return '<div class="note"><p class="cap">' + ic('lock') + 'Internal note · ' + n.who + ' · <time>' + n.time + '</time></p><p>' + n.text + '</p></div>'; }).join('');
      ev = '<div class="sp conv">' + out + '</div>';
    }
    var evidence = '<aside class="evidence" aria-label="Evidence">' + tt('Evidence.', 'What the AI saw, next to what is true now.', '', 'h2') + tabs + '<div id="ev-panel" role="tabpanel" aria-labelledby="tab-' + CS.tab + '" class="ev-p">' + ev + '</div></aside>';
    return '<div class="cs-grid">' + queue + brief + evidence + '</div>';
  }

  window.SKIN = {
    code: 'A4', name: 'Account statement',
    chatShell: chatShell, caseShell: caseShell, item: item, panel: settled, stripSummary: stripSummary,
    staffing: staffing, banner: banner, assistantState: assistantState, safety: safety, inbox: inbox, caseView: caseView
  };
})();
