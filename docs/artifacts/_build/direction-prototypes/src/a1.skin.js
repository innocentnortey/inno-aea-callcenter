/* A1 · Work order: markup construction. Sheets with an ink top rule, label-over-value field grids,
   numbered step rails, time bars. Read by the shared engine as window.SKIN. */
(function () {
  'use strict';
  var I = {
    person: '<path d="M10 10a3.2 3.2 0 1 0 0-6.4A3.2 3.2 0 0 0 10 10Zm-5.5 6.5c.6-2.8 2.9-4.5 5.5-4.5s4.9 1.7 5.5 4.5"/>',
    send: '<path d="M3.5 10h12M11 5.5 15.5 10 11 14.5"/>',
    cal: '<rect x="3.5" y="4.5" width="13" height="12" rx="1"/><path d="M3.5 8.5h13M7 3v3M13 3v3"/>',
    clock: '<circle cx="10" cy="10" r="6.5"/><path d="M10 6.5V10l2.5 1.5"/>',
    check: '<path d="m5 10.5 3 3 7-7"/>',
    doc: '<path d="M6 3.5h5.5L15 7v9.5H6z"/><path d="M11 3.5V7h4M8 10.5h5M8 13h5"/>',
    info: '<circle cx="10" cy="10" r="6.5"/><path d="M10 9v4.5M10 6.6v.1"/>',
    pause: '<circle cx="10" cy="10" r="6.5"/><path d="M8.5 7.5v5M11.5 7.5v5"/>',
    flag: '<path d="M5.5 16.5V4M5.5 4.5h8l-1.6 3 1.6 3h-8"/>',
    phone: '<path d="M6 3.5h2.5l1 3.5-1.7 1.2a8 8 0 0 0 4 4l1.2-1.7 3.5 1v2.5a1.5 1.5 0 0 1-1.6 1.5C9 15.2 4.8 11 4.5 5.1A1.5 1.5 0 0 1 6 3.5Z"/>',
    mail: '<rect x="3.5" y="5" width="13" height="10" rx="1"/><path d="m4 5.5 6 5 6-5"/>',
    pin: '<path d="M10 17s5-4.6 5-8.5a5 5 0 1 0-10 0C5 12.4 10 17 10 17Z"/><circle cx="10" cy="8.5" r="1.8"/>',
    shield: '<path d="M10 3.5 15.5 5.5v4.2c0 3.2-2.3 5.8-5.5 6.8-3.2-1-5.5-3.6-5.5-6.8V5.5z"/><path d="m7.6 10 1.7 1.7 3.2-3.2"/>',
    warn: '<path d="M10 3.2 17.5 16.5h-15z"/><path d="M10 8.2v4M10 14.3v.1"/>',
    receipt: '<path d="M5.5 3.5h9v13l-1.5-1-1.5 1-1.5-1-1.5 1-1.5-1-1.5 1z"/><path d="M8 7.5h4M8 10.5h4"/>'
  };
  function ic(n, cls) { return '<svg class="ic ' + (cls || '') + '" viewBox="0 0 20 20" aria-hidden="true" focusable="false">' + (I[n] || I.info) + '</svg>'; }
  function warnSolid() { return '<svg class="ic-warn" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 2.6 23 21.4H1z" fill="currentColor"/><path d="M12 9v6M12 17.6v.2" stroke="var(--safety-band)" stroke-width="2.4" stroke-linecap="round"/></svg>'; }

  function field(label, value, cls) { return '<div class="fld ' + (cls || '') + '"><span class="fld-l">' + label + '</span><span class="fld-v">' + value + '</span></div>'; }
  function rail(steps) {
    return '<ol class="rail">' + steps.map(function (s, i) {
      var st = s.st || 'todo';
      return '<li class="rail-s is-' + st + '"><span class="rail-d" aria-hidden="true">' + (st === 'done' ? ic('check') : (i + 1)) + '</span>' +
        '<span class="rail-l">' + s.l + (st === 'now' ? '<span class="sr"> (current step)</span>' : st === 'done' ? '<span class="sr"> (done)</span>' : '') + '</span>' +
        (s.t ? '<time class="rail-t">' + s.t + '</time>' : '') + '</li>';
    }).join('') + '</ol>';
  }
  function sheet(title, id, body, extra) {
    return '<section class="sheet ' + (extra || '') + '"><header class="sheet-h"><h3 class="sheet-t">' + title + '</h3>' + (id ? '<span class="sheet-id">' + id + '</span>' : '') + '</header>' + body + '</section>';
  }
  function sources(keys, c) {
    return '<div class="srcs">' + keys.map(function (k) {
      var s = c.SRC[k];
      return '<details class="src"><summary>' + ic('doc') + '<span class="src-f">' + s.file + '</span><span class="src-v">' + s.ver + '</span></summary>' +
        '<div class="src-b"><q>' + s.quote + '</q>' + (s.note ? '<p>' + s.note + '</p>' : '') + '</div></details>';
    }).join('') + '</div>';
  }

  /* ---------- cards ---------- */
  function cChecks(k, S, c) {
    var st = S.cards.checks || {};
    var body = '<ol class="checks">' + c.CHECKS.map(function (t) { return '<li>' + t + '</li>'; }).join('') + '</ol>';
    var foot = st.done
      ? '<p class="sheet-done">' + ic('check') + (st.choice === 'skip' ? 'Checks skipped' : 'Tried. Still not cooling') + '</p>'
      : '<div class="sheet-f"><button type="button" class="btn btn-p" data-act="choose" data-key="checks" data-val="skip" data-fk="checks-skip">Skip the checks</button>' +
        '<button type="button" class="btn btn-q" data-act="choose" data-key="checks" data-val="tried" data-fk="checks-tried">I tried them. Still not cooling</button></div>';
    return sheet('Quick checks', 'Optional', body + foot, 'sheet-checks');
  }
  function cQuestion(card, S) {
    var st = S.cards[card.key] || {};
    var opts = [['yes', 'Yes'], ['no', 'No'], ['skip', 'Skip']];
    var foot = st.done
      ? '<p class="sheet-done">' + ic('check') + 'Answered: ' + { yes: 'Yes', no: 'No', skip: 'Skipped' }[st.choice] + '</p>'
      : '<div class="seg" role="group" aria-label="Answer">' + opts.map(function (o) {
        return '<button type="button" class="seg-b" data-act="choose" data-key="' + card.key + '" data-val="' + o[0] + '" data-fk="' + card.key + '-' + o[0] + '">' + o[1] + '</button>';
      }).join('') + '</div>';
    return '<section class="sheet sheet-q"><p class="q-n">Question ' + card.n + ' of 2 · optional</p><p class="q-t">' + card.q + '</p>' + foot + '</section>';
  }
  function cSlots(S, c) {
    var st = S.cards.slots || {};
    var day = null; c.DAYS.forEach(function (d) { if (d.key === st.day) day = d; });
    var chips = '<div class="days" role="group" aria-label="Day">' + c.DAYS.map(function (d) {
      var open = d.wins.filter(function (w) { return w[1] === 'open'; }).length;
      var sel = d.key === st.day;
      return '<button type="button" class="day ' + (sel ? 'is-sel' : '') + '" data-act="slot-day" data-val="' + d.key + '" data-fk="day-' + d.d + '" aria-pressed="' + sel + '"' + (st.done ? ' disabled' : '') + '>' +
        '<span class="day-w">' + d.dow + '</span><span class="day-d">' + d.d + '</span><span class="day-o">' + (open ? open + ' open' : 'Full') + '</span></button>';
    }).join('') + '</div>';
    var wins = '<fieldset class="wins"><legend>Arrival windows · ' + day.full + '</legend><div class="wins-g">' + day.wins.map(function (w) {
      var W = c.WIN[w[0]], taken = w[1] !== 'open', sel = st.win === w[0];
      return '<button type="button" class="win ' + (taken ? 'is-taken' : '') + (sel ? ' is-sel' : '') + '" data-act="slot-win" data-val="' + w[0] + '" data-fk="win-' + w[0] + '" aria-pressed="' + sel + '"' + (taken || st.done ? ' disabled' : '') + '>' +
        '<span class="win-t">' + W.label + '</span><span class="win-s">' + (taken ? 'Taken' : sel ? ic('check') + 'Selected' : 'Open') + '</span></button>';
    }).join('') + '</div></fieldset>';
    var fee = '<div class="fee">' + field('Standard fee', '$89 diagnostic visit', 'fld-strong') +
      '<p class="fee-n">Credited toward the repair if you approve it at the same visit. Members’ fees and member-only windows appear after the code. Windows are shown, not held.</p></div>';
    var who = '';
    var sum = st.win ? '<span class="sum-v">' + day.long + ' · ' + c.WIN[st.win].label + ' · $89 diagnostic</span>' : '<span class="sum-v is-empty">No window picked yet</span>';
    var foot = st.done
      ? '<p class="sheet-done">' + ic('check') + 'Window chosen: ' + day.long + ', ' + c.WIN[st.win].label + '</p>'
      : '<div class="sheet-sum">' + sum + '<button type="button" class="btn btn-p" data-act="slot-book" data-fk="slot-book">Continue with this window</button></div>' +
        (st.err ? '<p class="err" role="alert">' + st.err + '</p>' : '');
    return sheet('Repair visit · pick a window', 'South zone · Kyle', chips + wins + fee + who + foot, 'sheet-slots');
  }
  function timebar(w) {
    var a = 8, b = 19, l = (w.from - a) / (b - a) * 100, r = (w.to - a) / (b - a) * 100;
    var ticks = [8, 10, 12, 14, 16, 18].map(function (h) { return '<span style="left:' + ((h - a) / (b - a) * 100) + '%">' + (h > 12 ? h - 12 : h) + (h >= 12 ? ' pm' : ' am') + '</span>'; }).join('');
    return '<div class="tbar" role="img" aria-label="Arrival window ' + w.label + ' on a day from 8 am to 7 pm"><div class="tbar-track"><div class="tbar-fill" style="left:' + l + '%;width:' + (r - l) + '%"></div></div><div class="tbar-ticks" aria-hidden="true">' + ticks + '</div></div>';
  }
  function cConfirm(S) {
    var v = S.visit;
    var body = '<div class="fields">' + field('Date', v.day.long + ', 2026') + field('Arrival window', v.win.label) + field('Technician', v.tech) + field('Fee that applies', v.fee) + '</div>' +
      timebar(v.win) +
      rail([{ l: 'Booked', t: 'Fri 2:08 pm', st: 'done' }, { l: 'Technician arrives in the window', t: v.day.long, st: 'now' }, { l: 'Repair approved or declined at the visit', st: 'todo' }]) +
      '<p class="sheet-note">' + ic('info') + 'Free to change or cancel until ' + v.freeUntil + '. After that, a $49 late-cancellation fee applies. ' + v.feeNote + '</p>';
    return sheet('Repair visit', '<span class="stamp">' + ic('check') + 'Booked</span>', body, 'sheet-confirm');
  }
  function cCode(S, c) {
    var st = S.cards.code || {};
    var body;
    if (st.stage === 'locate' && !st.done) {
      body = '<form class="code-f code-loc" data-form="locate" novalidate><div class="who-g">' +
        '<label class="in"><span>Name on the account</span><input data-bind="code.name" data-fk="loc-name" value="' + c.esc(st.name || '') + '" autocomplete="name"></label>' +
        '<label class="in"><span>Phone</span><input data-bind="code.phone" data-fk="loc-phone" value="' + c.esc(st.phone || '') + '" inputmode="tel" autocomplete="tel"></label></div>' +
        '<button class="btn btn-p" data-fk="loc-send">Send the code</button></form>' + (st.err ? '<p class="err" role="alert">' + st.err + '</p>' : '') +
        '<p class="sheet-links"><span class="hint">Demo: the dataset’s test customer. The code goes to the phone on record, never to a number typed here.</span></p>';
      return sheet('Confirm it’s you', 'Before booking', body, 'sheet-code');
    }
    body = '<div class="fields fields-1">' + field('Code sent to', 'The phone on record, ending in 02') + '</div>';
    if (st.done) {
      body += '<p class="sheet-done">' + ic('shield') + 'Verified for this chat</p>';
    } else {
      body += '<form class="code-f" data-form="code" novalidate><label class="in in-code"><span>6-digit code</span>' +
        '<input id="code-input" data-fk="code-input" inputmode="numeric" autocomplete="one-time-code" maxlength="6" value="' + (st.value || '') + '"' + (st.err ? ' aria-invalid="true" aria-describedby="code-err"' : '') + '></label>' +
        '<button class="btn btn-p" data-fk="code-verify">Verify</button></form>' +
        (st.err ? '<p class="err" id="code-err" role="alert">' + st.err + '</p>' : '') +
        '<p class="sheet-links"><a href="#code" data-act="inbox" data-fk="inbox-link">Open the demo inbox</a><span class="hint">Demo: codes go to a simulated inbox, never a real phone. A code lasts 10 minutes; 3 tries.</span></p>';
    }
    return sheet('Confirm it’s you', st.done ? 'Verified' : 'Code sent', body, 'sheet-code');
  }
  function cAccount() {
    var rows = [['Diagnostic visit', '$89.00'], ['Contactor replacement', '$245.00'], ['After-hours dispatch', '$144.00']];
    var body = '<div class="fields">' + field('Issued', 'Oct 2, 2026') + field('Due', 'Nov 1, 2026') + field('Balance', '$478.00 · unpaid', 'fld-strong') + field('Paid so far', '$0.00') + '</div>' +
      '<table class="lines"><caption class="sr">Invoice lines</caption><thead><tr><th scope="col">Line</th><th scope="col">Amount</th></tr></thead><tbody>' +
      rows.map(function (r) { return '<tr><td>' + r[0] + '</td><td>' + r[1] + '</td></tr>'; }).join('') +
      '</tbody><tfoot><tr><th scope="row">Total</th><td>$478.00</td></tr></tfoot></table>';
    return sheet('Invoice', 'INV-204411', body, 'sheet-account');
  }
  function cHandoff(S, c) {
    var r = S.request, st = S.cards.follow || {};
    var body = '<p class="promise">' + c.TXT.promise + '</p>' +
      '<div class="pbar" role="img" aria-label="From now, Fri Oct 16 2:14 pm, to due, Mon Oct 19 7:00 pm"><div class="pbar-end"><span class="fld-l">Now</span><span class="fld-v">' + r.nowAt + '</span></div>' +
      '<div class="pbar-line" aria-hidden="true"><span></span></div><div class="pbar-end pbar-due"><span class="fld-l">Due</span><span class="fld-v">' + r.due + '</span></div></div>';
    if (st.done) {
      body += '<p class="sheet-done">' + ic(st.channel === 'email' ? 'mail' : 'phone') + 'Follow-up saved: ' + (st.channel === 'email' ? 'email, the address on your account' : 'phone call, the number ending in 02, ' + { mornings: 'mornings', afternoons: 'afternoons', any: 'any time' }[st.when]) + '</p>';
    } else {
      body += '<fieldset class="fu"><legend>' + c.TXT.followAsk + '</legend>' +
        '<div class="seg seg-wide" role="group" aria-label="Follow-up channel">' +
        '<button type="button" class="seg-b ' + (st.channel === 'email' ? 'is-sel' : '') + '" aria-pressed="' + (st.channel === 'email') + '" data-act="follow-ch" data-val="email" data-fk="fu-email">' + ic('mail') + '<span>Email<small>the address on your account</small></span></button>' +
        '<button type="button" class="seg-b ' + (st.channel === 'phone' ? 'is-sel' : '') + '" aria-pressed="' + (st.channel === 'phone') + '" data-act="follow-ch" data-val="phone" data-fk="fu-phone">' + ic('phone') + '<span>Phone call<small>the number ending in 02</small></span></button></div>' +
        (st.channel === 'phone' ? '<div class="seg" role="group" aria-label="Best time to call">' + [['mornings', 'Mornings'], ['afternoons', 'Afternoons'], ['any', 'Any time']].map(function (o) {
          return '<button type="button" class="seg-b ' + (st.when === o[0] ? 'is-sel' : '') + '" aria-pressed="' + (st.when === o[0]) + '" data-act="follow-when" data-val="' + o[0] + '" data-fk="fu-' + o[0] + '">' + o[1] + '</button>';
        }).join('') + '</div>' : '') +
        '</fieldset><div class="sheet-f"><button type="button" class="btn btn-p" data-act="follow-save" data-fk="fu-save">Save my choice</button></div>';
    }
    return sheet('Your request', '<span class="mono">' + r.ref + '</span>', body, 'sheet-handoff');
  }
  function cQueued(S, c) {
    var joined = S.live === 'joined';
    var body = '<p class="promise">' + c.TXT.queued + '</p>' +
      rail([{ l: 'You asked for a person', t: 'Fri 2:14 pm', st: 'done' }, { l: joined ? 'Riley (demo representative) joined' : 'A representative joins this chat', t: joined ? 'Fri 2:17 pm' : '', st: joined ? 'done' : 'now' }, { l: 'Back to the assistant, or the chat closes', st: joined ? 'now' : 'todo' }]);
    return sheet('Your request', '<span class="mono">' + S.request.ref + '</span>', body, 'sheet-queued');
  }
  function cWhere(S, c) {
    var st = S.cards.where || {};
    var body = st.done ? '<p class="sheet-done">' + ic('pin') + 'Kyle · south zone</p>'
      : '<form class="code-f" data-form="where" novalidate><label class="in"><span>ZIP code or city</span><input id="where-input" data-bind="where.value" data-fk="where-input" value="' + c.esc(st.value || '') + '" autocomplete="postal-code"' + (st.err ? ' aria-invalid="true"' : '') + '></label>' +
        '<button class="btn btn-p" data-fk="where-go">Show windows</button></form>' + (st.err ? '<p class="err" role="alert">' + st.err + '</p>' : '');
    return sheet('Visit address', 'ZIP or city', body, 'sheet-where');
  }
  function card(cd, S, c) {
    switch (cd.type) {
      case 'where': return cWhere(S, c);
      case 'checks': return cChecks(cd, S, c);
      case 'question': return cQuestion(cd, S, c);
      case 'slots': return S.cards.slots ? cSlots(S, c) : '';
      case 'confirm': return cConfirm(S, c);
      case 'code': return cCode(S, c);
      case 'account': return cAccount(S, c);
      case 'handoff': return cHandoff(S, c);
      case 'queued': return cQueued(S, c);
    }
    return '';
  }

  /* ---------- thread items ---------- */
  function item(it, S, c) {
    if (it.kind === 'event') {
      return '<div class="evt">' + ic(it.icon === 'person' ? 'person' : it.icon) + '<p>' + it.html + '</p><time>' + it.time + '</time></div>';
    }
    if (it.who === 'customer') {
      return '<div class="turn turn-c"><p class="who">You · <time>' + it.time + '</time>' + (it.viaButton ? ' · tapped' : '') + '</p><div class="cblock">' + it.html + '</div></div>';
    }
    if (it.who === 'rep') {
      return '<div class="turn turn-r"><p class="who">' + ic('person') + '<b>Riley · representative (demo)</b> · <time>' + it.time + '</time></p><div class="rblock">' + it.html + '</div></div>';
    }
    return '<div class="turn turn-a' + (it.quiet ? ' is-quiet' : '') + '"><p class="who"><span class="mk" aria-hidden="true"></span><b>Meridian assistant · automated</b> · <time>' + it.time + '</time></p>' +
      (it.html ? '<p class="say">' + it.html + '</p>' : '') + (it.card ? card(it.card, S, c) : '') + (it.after ? '<p class="say">' + it.after + '</p>' : '') +
      (it.sources ? sources(it.sources, c) : '') + '</div>';
  }

  /* ---------- safety ---------- */
  function safety(c, mode) {
    return '<section class="safety' + (mode ? ' safety-' + mode : '') + '"' + (mode ? '' : ' role="alert"') + ' aria-label="Danger: safety instruction">' +
      '<div class="sf-band">' + warnSolid() + '<p class="sf-w">DANGER</p></div>' +
      '<ol class="sf-list"><li><span class="sf-n" aria-hidden="true">1</span><p>' + c.TXT.safety1 + '</p></li><li><span class="sf-n" aria-hidden="true">2</span><p>' + c.TXT.safety2 + '</p></li></ol></section>';
  }

  /* ---------- the "what's settled" panel ---------- */
  function panel(S, c, mode) {
    var h = mode === 'strip' ? '' : '<header class="pn-h"><h2>What’s settled</h2><p>Fills in as things are confirmed.</p></header>';
    if (S.safety) return h + safety(c, 'panel');
    var hl = function (k) { return S.hl === k ? ' is-hl' : ''; };
    var v = S.visit, r = S.request;
    var visit = v
      ? '<section class="pn-b' + hl('visit') + '"><h3>' + ic('cal') + 'Your visit</h3><div class="fields">' + field('Date', v.day.long) + field('Window', v.win.label) + field('Technician', v.tech) + field('Fee', '$89 diagnostic') + '</div></section>'
      : '<section class="pn-b is-empty"><h3>' + ic('cal') + 'Your visit</h3><p>Nothing booked yet.</p></section>';
    var req;
    if (r && r.live) {
      req = '<section class="pn-b' + hl('request') + '"><h3>' + ic('receipt') + 'Your request <span class="mono">' + r.ref + '</span></h3><p>' + (S.live === 'joined' ? 'A representative has joined this chat.' : 'Waiting for a representative to join this chat. No time is promised.') + '</p></section>';
    } else if (r) {
      req = '<section class="pn-b' + hl('request') + '"><h3>' + ic('receipt') + 'Your request <span class="mono">' + r.ref + '</span></h3>' +
        '<p class="pn-promise">A representative will get back to you within 1 business day.</p><div class="fields fields-1">' + field('Due', r.due, 'fld-strong') +
        field('Follow-up', r.follow ? r.follow.channel + (r.follow.when ? ' · ' + r.follow.when : '') : 'Not chosen yet') + '</div></section>';
    } else {
      req = '<section class="pn-b is-empty"><h3>' + ic('receipt') + 'Your request</h3><p>No request open.</p></section>';
    }
    var id = '<section class="pn-b pn-line' + hl('identity') + '"><h3>' + ic('shield') + 'Identity</h3><p>' +
      (S.identity === 'verified' ? 'Verified for this chat · phone ending 02' : S.identity === 'sent' ? 'Code sent to the phone ending in 02' : 'Not checked yet. Only needed for private details.') + '</p></section>';
    var ctl = S.staffing === 'sim' ? '<section class="pn-b pn-line' + hl('control') + '"><h3>' + ic(S.live === 'joined' ? 'pause' : 'person') + 'Who is replying</h3><p>' +
      (S.live === 'joined' ? 'Riley (demo representative). The assistant is paused.' : 'The automated assistant.') + '</p></section>' : '';
    return h + ctl + visit + req + id;
  }
  function stripSummary(S, c) {
    if (S.safety) return '<span class="st-danger">' + warnSolid() + '<b>DANGER</b> · Leave the home immediately</span>';
    var bits = [];
    if (S.visit) bits.push(ic('cal') + '<span>' + S.visit.day.long + ' · ' + S.visit.win.label + '</span>');
    if (S.request) bits.push(ic('receipt') + '<span class="mono">' + S.request.ref + '</span>' + (S.request.live ? '' : '<span> · due Mon 7:00 pm</span>'));
    return '<span class="st-l">What’s settled</span>' + (bits.length ? '<span class="st-bits">' + bits.join('') + '</span>' : '<span class="st-bits st-none">Nothing yet</span>');
  }
  function staffing(S) {
    return S.staffing === 'sim' ? ic('person') + 'Simulated staff on shift (demo)' : ic('person') + 'Nobody online';
  }
  function banner(S, c) {
    if (S.staffing !== 'sim') return '';
    return '<p>' + ic('info') + c.TXT.staffBanner + '</p>' + (S.live === 'queued' ? '<button type="button" class="btn btn-q btn-s" data-act="demo-join">Demo: Riley claims the case and joins</button>' : '');
  }
  function assistantState(S) {
    return S.live === 'joined' ? ic('pause') + 'Assistant paused · Riley (demo) is replying' : 'Meridian assistant · automated';
  }

  function chatShell(c) {
    return '<div class="chat">' +
      '<header class="ch-head"><div class="brand"><p class="brand-n">Meridian Home Comfort</p><p class="brand-s" id="assistant-state"></p></div>' +
      '<button type="button" class="link-b" data-act="stub" data-msg="The demo guide (SCR-3) is not part of this direction prototype.">Demo guide</button>' +
      '<div class="demo-bar" aria-label="Demo status"><span class="chip">' + ic('cal') + 'Fri Oct 16, 2026 (demo date)</span><span class="chip" id="staffing"></span></div></header>' +
      '<div id="banner" class="banner" hidden></div>' +
      '<details id="strip" class="strip"><summary id="strip-summary"></summary><div id="strip-body" class="strip-b"></div></details>' +
      '<div class="ch-main"><div class="ch-col"><div id="pinned" class="pinned" hidden></div>' +
      '<div id="thread" class="thread" role="log" aria-label="Conversation" tabindex="0"></div>' +
      '<form class="composer" data-form="composer"><div class="cp-top"><button type="button" class="talk" id="talk" data-act="talk">' + ic('person') + 'Talk to a person</button><span id="composer-hint" class="cp-hint"></span></div>' +
      '<div class="cp-row"><label for="composer-input" class="sr">Message</label><input id="composer-input" autocomplete="off"><button class="send" aria-label="Send">' + ic('send') + '</button></div></form></div>' +
      '<aside id="panel" class="panel" aria-label="What’s settled"></aside></div></div>';
  }
  function caseShell() {
    return '<div class="console"><header class="cs-head"><div class="brand"><p class="brand-n">Meridian staff console</p><p class="brand-s">Demo staff sign-in · Riley (demo representative)</p></div>' +
      '<div class="demo-bar"><span class="chip">' + ic('cal') + 'Fri Oct 16, 2026 (demo date)</span></div></header><div id="case-root" class="case-root"></div></div>';
  }
  function inbox(c) {
    return '<dialog id="inbox" class="inbox" aria-labelledby="inbox-h"><header><h2 id="inbox-h">Demo delivery inbox</h2><p>Simulated messages. Nothing is sent to anyone. This exists only so reviewers can complete verification.</p></header>' +
      '<article class="inbox-m"><p class="fld-l">To the phone ending in 02 · Fri Oct 16, 2:07 pm</p><p>Your Meridian Home Comfort verification code is <b class="mono">482913</b>. It expires in 10 minutes.</p></article>' +
      '<div class="sheet-f"><button type="button" class="btn btn-p" data-act="inbox-use">Use this code in the chat</button><button type="button" class="btn btn-q" data-act="inbox-close">Close</button></div></dialog>';
  }

  /* ---------- staff console: queue + case ---------- */
  function tag(p, word) { return '<span class="tag tag-' + p + '">' + p + ' ' + word + '</span>'; }
  function qrow(q, CS) {
    var sel = CS.sel === q.ref;
    return '<li><button type="button" class="q-row' + (sel ? ' is-sel' : '') + '" data-act="case-select" data-val="' + q.ref + '" data-ref="' + q.ref + '" data-fk="q-' + q.ref + '"' + (sel ? ' aria-current="true"' : '') + '>' +
      '<span class="q-1">' + tag(q.p, q.pword) + '<span class="mono q-ref">' + q.ref + '</span></span>' +
      '<span class="q-due' + (q.overdue ? ' is-over' : '') + '">' + (q.overdue ? ic('clock') + '<b>Overdue</b> · ' : q.band === 'safety' ? '' : 'Due ') + q.due + '</span>' +
      '<span class="q-2">' + q.reason + '</span><span class="q-3">' + q.who + ' · ' + q.owner + (q.follow ? ' · ' + q.follow : '') + '</span></button></li>';
  }
  function caseView(CS, c) {
    var K = c.CASE;
    var safetyRows = c.QUEUE.filter(function (q) { return q.band === 'safety'; });
    var restRows = c.QUEUE.filter(function (q) { return q.band !== 'safety'; });
    var wide = window.matchMedia('(min-width: 1100px)').matches;
    var queue = '<details class="q-col"' + (wide ? ' open' : '') + '><summary class="q-sum">Queue · ' + c.QUEUE.length + ' cases</summary><div class="q-in">' +
      '<header class="col-h"><h2>Needs my action</h2><p>Safety and danger first, then by due time. Seeded demo cases.</p></header>' +
      '<section class="q-band q-band-safety"><h3>Safety and danger</h3><ul data-queue>' + safetyRows.map(function (q) { return qrow(q, CS); }).join('') + '</ul></section>' +
      '<section class="q-band"><h3>By due time</h3><ul data-queue>' + restRows.map(function (q) { return qrow(q, CS); }).join('') + '</ul></section></div></details>';

    var brief;
    if (CS.sel !== K.ref) {
      brief = '<main class="brief" id="brief"><section class="sheet brief-empty"><p>Seeded queue row. This direction prototype builds the brief only for <span class="mono">MHC-C-0007</span>.</p>' +
        '<button type="button" class="btn btn-q" data-act="case-select" data-val="MHC-C-0007" data-fk="q-MHC-C-0007">Open MHC-C-0007</button></section></main>';
    } else {
      var stIdx = CS.claimed ? 1 : 0;
      var railSteps = K.states.map(function (s, i) { return { l: s, st: i < stIdx ? 'done' : i === stIdx ? 'now' : 'todo', t: i === 0 ? 'Fri 2:14 pm' : i === 1 && CS.claimed ? 'Fri 2:20 pm' : '' }; });
      var secs = K.sections.map(function (s) {
        var items = s.items.map(function (x) {
          return '<li>' + (s.kind === 'decide' ? '<span class="dq" aria-hidden="true">?</span>' : '') + '<span class="bi-t">' + x.t + '</span>' +
            (x.src ? '<button type="button" class="src-tag" data-act="src-jump" data-val="' + x.src + '" data-fk="st-' + s.n + '-' + x.src + '">' + ic('doc') + x.tag + '</button>' : '') + '</li>';
        }).join('');
        return '<section class="bs bs-' + s.kind + '"><h3><span class="bs-n">' + s.n + '</span>' + s.h + (s.kind === 'claim' ? '<span class="nc">Not checked</span>' : '') + '</h3><ul>' + items + '</ul></section>';
      }).join('');
      var acts = '<div class="acts"><div class="acts-row">' +
        (CS.claimed ? '<span class="stamp">' + ic('check') + 'Claimed by Riley (demo)</span>' : '<button type="button" class="btn btn-p" data-act="case-claim" data-fk="act-claim">Claim</button>') +
        '<button type="button" class="btn btn-q" data-act="case-call" data-fk="act-call"' + (CS.claimed ? '' : ' disabled') + '>' + ic('phone') + 'Log a call</button>' +
        '<button type="button" class="btn btn-q" data-act="case-flag" data-fk="act-flag">' + ic('flag') + (CS.flagged ? 'Flagged' : 'Flag') + '</button>' +
        '<button type="button" class="btn btn-q" disabled>' + ic('person') + 'Join chat</button></div>' +
        '<p class="hint">' + (CS.claimed ? '' : 'Claim the case to log a call. ') + 'Join chat works only while the customer is in a live chat; nobody was online when this case was made.</p>' +
        (CS.callOpen ? '<form class="mini-f" data-form="call"><fieldset><legend>Log a call to the number ending in 02 (demo)</legend>' +
          '<label class="rd"><input type="radio" name="outcome" value="Reached the customer" data-fk="call-outcome" checked> Reached the customer</label>' +
          '<label class="rd"><input type="radio" name="outcome" value="No answer"> No answer</label></fieldset>' +
          '<p class="hint">Demo: recorded, not sent. No call is placed.</p><button class="btn btn-p btn-s">Record</button></form>' : '') +
        (CS.flagOpen ? '<form class="mini-f" data-form="flag"><label class="in"><span>What is wrong?</span><select data-fk="flag-reason"><option>The brief left something out</option><option>An answer was wrong</option><option>The escalation was not needed</option></select></label><button class="btn btn-p btn-s">Add to review list</button></form>' : '') +
        '<ol class="log">' + CS.acts.map(function (a) { return '<li><time>' + a.time + '</time><span>' + a.text + '</span></li>'; }).join('') + '</ol></div>';
      brief = '<main class="brief" id="brief"><article class="sheet case-sheet">' +
        '<header class="case-h"><div class="case-l">' + tag(K.p, K.pword) + '<span class="mono">' + K.ref + '</span><span class="case-st">' + (CS.claimed ? 'Claimed' : 'Unassigned') + '</span></div>' +
        '<h1 class="case-t">' + K.title + '</h1><p class="case-m">Created ' + K.created + ' · Due ' + K.due + ' · Owner: ' + (CS.claimed ? 'Riley (demo)' : 'nobody yet') + '</p>' + rail(railSteps) + '</header>' +
        '<section class="promise-s" aria-label="Promise and follow-up"><div class="fields">' + field('Promise shown to the customer', K.promise, 'fld-wide') + field('Due', K.due, 'fld-strong') +
        field('Follow up by', K.follow.channel) + field('Destination', K.follow.dest) + field('Best time', K.follow.when) + '</div></section>' +
        '<div class="bss">' + secs + '</div>' + acts + '</article></main>';
    }

    var tabs = '<div class="tabs" role="tablist" aria-label="Evidence">' +
      '<button type="button" role="tab" id="tab-sources" data-fk="tab-sources" aria-selected="' + (CS.tab === 'sources') + '" aria-controls="ev-panel" data-act="case-tab" data-val="sources">Sources · ' + K.sources.length + '</button>' +
      '<button type="button" role="tab" id="tab-conversation" data-fk="tab-conversation" aria-selected="' + (CS.tab === 'conversation') + '" aria-controls="ev-panel" data-act="case-tab" data-val="conversation">Conversation</button></div>';
    var ev;
    if (CS.tab === 'sources') {
      ev = K.sources.map(function (s) {
        var b = '';
        if (s.rows) {
          b = '<table class="snap"><caption class="sr">' + s.title + ': snapshot and now</caption><thead><tr><th scope="col">Field</th><th scope="col">What the AI saw<small>Fri 2:10 pm</small></th><th scope="col">Now<small>Fri 2:20 pm</small></th></tr></thead><tbody>' +
            s.rows.map(function (r) { return '<tr><th scope="row">' + r[0] + '</th><td>' + r[1] + '</td><td>' + r[2] + '</td></tr>'; }).join('') + '</tbody></table>';
        } else {
          b = '<blockquote class="quote">' + s.quote + '</blockquote>';
        }
        return '<section class="sheet src-sheet' + (CS.hl === s.id ? ' is-hl' : '') + '" id="src-' + s.id + '" tabindex="-1"><header class="sheet-h"><h3 class="sheet-t">' + s.title + '</h3></header>' +
          '<p class="src-meta"><span class="mono">' + s.file + '</span><span>' + s.ver + '</span></p>' + b +
          (s.fact ? '<p class="src-fact"><span class="fld-l">Fact</span>' + s.fact + '</p>' : '') +
          '<p class="src-ok">' + ic('check') + s.status + '</p></section>';
      }).join('');
    } else {
      ev = '<ol class="tx">' + K.transcript.map(function (t) {
        var who = t.who === 'customer' ? 'Customer' : t.who === 'event' ? 'Event' : 'Meridian assistant · automated';
        return '<li class="tx-' + t.who + '"><p class="who">' + who + ' · <time>' + t.time + '</time></p><p>' + t.text + '</p></li>';
      }).join('') + '</ol>';
    }
    var evidence = '<aside class="evidence" aria-label="Evidence"><header class="col-h"><h2>Evidence</h2><p>What the AI saw, next to what is true now.</p></header>' + tabs +
      '<div id="ev-panel" role="tabpanel" aria-labelledby="tab-' + CS.tab + '" class="ev-p">' + ev + '</div></aside>';
    return '<div class="cs-grid">' + queue + brief + evidence + '</div>';
  }

  window.SKIN = {
    code: 'A1', name: 'Work order',
    other: { file: '2026-10-20-direction-A2-route-sheet.html', short: 'Switch to A2', name: 'A2 Route sheet' },
    chatShell: chatShell, caseShell: caseShell, item: item, panel: panel, stripSummary: stripSummary,
    staffing: staffing, banner: banner, assistantState: assistantState, safety: safety, inbox: inbox, caseView: caseView
  };
})();
