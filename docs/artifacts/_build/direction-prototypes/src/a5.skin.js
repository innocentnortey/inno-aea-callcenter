/* A5 · Service desk: markup construction. Hairline cards with a tinted header row and an emerald icon, a name line over every
   message (mint for the customer, grey for the assistant), day tabs and window tiles for booking, a square red safety card.
   Read by the shared engine as window.SKIN. */
(function () {
  'use strict';
  var I = {
    person: '<circle cx="10" cy="7" r="3"/><path d="M4.5 16.5c.7-2.9 2.9-4.5 5.5-4.5s4.8 1.6 5.5 4.5"/>',
    pin: '<path d="M10 17s5-4.6 5-8.5a5 5 0 1 0-10 0C5 12.4 10 17 10 17Z"/><circle cx="10" cy="8.5" r="1.8"/>',
    receipt: '<path d="M5.5 3.5h9v13l-1.5-1-1.5 1-1.5-1-1.5 1-1.5-1-1.5 1z"/><path d="M8 7.5h4M8 10.5h4"/>',
    info: '<circle cx="10" cy="10" r="6.5"/><path d="M10 9v4.5M10 6.6v.1"/>',
    shield: '<path d="M10 3.5 15.5 5.5v4.2c0 3.2-2.3 5.8-5.5 6.8-3.2-1-5.5-3.6-5.5-6.8V5.5z"/><path d="m7.6 10 1.7 1.7 3.2-3.2"/>',
    tool: '<path d="M12.5 4a3.5 3.5 0 0 0-3.3 4.6L4 13.8 6.2 16l5.2-5.2A3.5 3.5 0 0 0 16 7.5l-2 2-2-.5-.5-2 2-2a3.5 3.5 0 0 0-1-.5Z"/>',
    phone: '<path d="M6 3.5h2.5l1 3.5-1.7 1.2a8 8 0 0 0 4 4l1.2-1.7 3.5 1v2.5a1.5 1.5 0 0 1-1.6 1.5C9 15.2 4.8 11 4.5 5.1A1.5 1.5 0 0 1 6 3.5Z"/>',
    mail: '<rect x="3.5" y="5" width="13" height="10" rx="2"/><path d="m4 5.5 6 5 6-5"/>',
    lock: '<rect x="5" y="9" width="10" height="7.5" rx="2"/><path d="M7.5 9V7a2.5 2.5 0 0 1 5 0v2"/>',
    flag: '<path d="M5.5 16.5V4M5.5 4.5h8l-1.6 3 1.6 3h-8"/>',
    pause: '<circle cx="10" cy="10" r="6.5"/><path d="M8.5 7.5v5M11.5 7.5v5"/>',
    wait: '<path d="M6.5 3.5h7M6.5 16.5h7M7 3.5c0 3.5 6 3.5 6 6.5s-6 3-6 6.5M13 3.5c0 3.5-6 3.5-6 6.5"/>',
    question: '<circle cx="10" cy="10" r="6.5"/><path d="M8.2 8.2a1.9 1.9 0 1 1 2.6 1.8c-.5.2-.8.6-.8 1.2v.3M10 13.8v.1"/>',
    chat: '<path d="M4 5.5A1.5 1.5 0 0 1 5.5 4h9A1.5 1.5 0 0 1 16 5.5v6a1.5 1.5 0 0 1-1.5 1.5H9l-3.5 3v-3h0A1.5 1.5 0 0 1 4 11.5z"/>'
  };
  var I24 = {
    head: '<path d="M4 14v-2a8 8 0 0 1 16 0v2"/><rect x="3" y="14" width="4" height="6" rx="1.5"/><rect x="17" y="14" width="4" height="6" rx="1.5"/>',
    cal: '<rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    ticket: '<path d="M4 7h16v3a2 2 0 0 0 0 4v3H4v-3a2 2 0 0 0 0-4z"/><path d="M14 7v10" stroke-dasharray="2 2"/>',
    check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    warn: '<path d="M12 3.5L2.5 20h19z"/><path d="M12 10v4.5M12 17.2v.3"/>',
    spark: '<path d="M12 4v4M12 16v4M4 12h4M16 12h4M7 7l2 2M15 15l2 2M17 7l-2 2M9 15l-2 2"/>',
    doc: '<path d="M7 3.5h7l4 4V20.5H7z"/><path d="M14 3.5v4h4M10 12h5M10 15.5h5"/>',
    chev: '<path d="M6 9l6 6 6-6"/>',
    mk: '<path d="M5 7.5h14v9H5z"/><path d="M9 11.5h6"/>'
  };
  function ic(n) {
    if (I24[n]) return '<svg class="ic" viewBox="0 0 24 24" aria-hidden="true" focusable="false">' + I24[n] + '</svg>';
    return '<svg class="ic" viewBox="0 0 20 20" aria-hidden="true" focusable="false">' + (I[n] || I.info) + '</svg>';
  }
  function mark(cls) { return '<span class="mark ' + (cls || '') + '" aria-hidden="true">' + ic('mk') + '</span>'; }
  function warnSolid() { return '<svg class="ic-warn" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 2.6 23 21.4H1z" fill="currentColor"/><path d="M12 9v6M12 17.6v.2" stroke="var(--danger)" stroke-width="2.4" stroke-linecap="round"/></svg>'; }
  var WT = { '08:00-12:00': '8:00 am – 12:00 pm', '12:00-16:00': '12:00 pm – 4:00 pm', '13:00-17:00': '1:00 pm – 5:00 pm', '16:00-19:00': '4:00 pm – 7:00 pm' };
  function wtxt(k) { return WT[k] || k; }
  function lv(icon, label, value, cls) { return '<div class="row ' + (cls || '') + '"><span class="row-l">' + label + '</span><b class="row-v">' + value + '</b></div>'; }
  function evt(icon, text, time, cls) {
    return '<p class="evt ' + (cls || '') + '">' + (cls && /evt-in|evt-status|evt-good/.test(cls) ? ic(icon) : '') + '<span class="evt-t">' + text + '</span>' + (time ? '<time>' + time + '</time>' : '') + '</p>';
  }
  function acard(icon, title, meta, body, cls) {
    return '<section class="acard ' + (cls || '') + '"><header class="cardhead">' + ic(icon) + '<h3>' + title + '</h3><span class="cardmeta">' + meta + '</span></header><div class="cardbody">' + body + '</div></section>';
  }
  function sources(keys, c) {
    return '<div class="srcs">' + keys.map(function (k) {
      var s = c.SRC[k];
      return '<details class="src"><summary>' + ic('doc') + '<span>' + s.file + '</span><span class="src-v">' + s.ver + '</span></summary><div class="src-b"><q>' + s.quote + '</q>' + (s.note ? '<p>' + s.note + '</p>' : '') + '</div></details>';
    }).join('') + '</div>';
  }

  /* ---------- cards ---------- */
  function cChecks(S, c) {
    var st = S.cards.checks || {};
    var body = '<ol class="checks">' + c.CHECKS.map(function (t) { return '<li>' + t + '</li>'; }).join('') + '</ol>' +
      (st.done ? evt('check', st.choice === 'skip' ? 'Checks skipped' : 'Tried. Still not cooling', '', 'evt-in')
        : '<div class="acts"><button type="button" class="btn btn-p" data-act="choose" data-key="checks" data-val="skip" data-fk="checks-skip">Skip the checks</button>' +
          '<button type="button" class="btn btn-q" data-act="choose" data-key="checks" data-val="tried" data-fk="checks-tried">I tried them. Still not cooling</button></div>');
    return acard('tool', 'Quick checks', 'Optional', body);
  }
  function cQuestion(card, S) {
    var st = S.cards[card.key] || {};
    var body = '<p class="q-t">' + card.q + '</p>' + (st.done ? evt('check', 'Answered: ' + { yes: 'Yes', no: 'No', skip: 'Skipped' }[st.choice], '', 'evt-in')
      : '<div class="acts" role="group" aria-label="Answer">' + [['yes', 'Yes'], ['no', 'No'], ['skip', 'Skip']].map(function (o) {
        return '<button type="button" class="btn btn-q" data-act="choose" data-key="' + card.key + '" data-val="' + o[0] + '" data-fk="' + card.key + '-' + o[0] + '">' + o[1] + '</button>';
      }).join('') + '</div>');
    return acard('question', 'Question ' + card.n + ' of 2', 'Optional', body, 'step-q');
  }
  function cWhere(S, c) {
    var st = S.cards.where || {};
    var body = st.done ? lv('', 'Visit area', 'Kyle 78640 · our south zone')
      : '<form class="inl" data-form="where" novalidate><label class="in"><span>ZIP code or city</span><input id="where-input" data-bind="where.value" data-fk="where-input" value="' + c.esc(st.value || '') + '" autocomplete="postal-code"' + (st.err ? ' aria-invalid="true"' : '') + '></label>' +
        '<button class="btn btn-p" data-fk="where-go">Show windows</button></form>' + (st.err ? '<p class="err" role="alert">' + st.err + '</p>' : '');
    return acard('pin', 'Where is the visit?', 'Assistant step', body);
  }
  function dayByKey(c, k) { var d = null; c.DAYS.forEach(function (x) { if (x.key === k) d = x; }); return d; }
  function cSlots(S, c) {
    var st = S.cards.slots || {};
    var day = dayByKey(c, st.day) || c.DAYS[0];
    var tabs = '<div class="daytabs" role="group" aria-label="Day">' + c.DAYS.map(function (d) {
      return '<button type="button" class="daytab" aria-pressed="' + (st.day === d.key) + '" data-act="slot-day" data-val="' + d.key + '" data-fk="day-' + d.d + '"' + (st.done ? ' disabled' : '') + '><span>' + d.dow + '</span><b>' + d.d + '</b></button>';
    }).join('') + '</div>';
    var anyOpen = false;
    var wins = '<div class="wins">' + day.wins.map(function (w) {
      var key = w[0];
      if (w[1] === 'open') {
        anyOpen = true;
        var sel = st.win === key;
        return '<button type="button" class="win' + (sel ? ' is-sel' : '') + '" data-act="slot-win" data-day="' + day.key + '" data-val="' + key + '" data-fk="chip-' + day.d + '-' + key + '" aria-pressed="' + sel + '"' + (st.done ? ' disabled' : '') + '>' + (sel ? ic('check') : '') + wtxt(key) + '</button>';
      }
      return '<button type="button" class="win is-taken" disabled><s>' + wtxt(key) + '</s><i>Taken</i></button>';
    }).join('') + '</div>' + (anyOpen ? '' : '<p class="hint">Every window on this day is taken.</p>');
    var rows = '<div class="rows">' + lv('', 'Area', 'Kyle 78640 · south zone') + lv('', 'Diagnostic visit', '$89') + '</div>';
    var foot = st.done
      ? evt('check', 'Window chosen: ' + day.long + ', ' + wtxt(st.win), '', 'evt-in')
      : '<p class="hint">Windows are shown, not held. Members’ fees and member-only windows appear after the code.</p><div class="acts"><button type="button" class="btn btn-p" data-act="slot-book" data-fk="slot-book">Continue with this window</button></div>' +
        (st.err ? '<p class="err" role="alert">' + st.err + '</p>' : '');
    return acard('cal', 'Choose a window', 'this week', tabs + wins + rows + foot, 'step-slots');
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
      return acard('shield', 'Confirming it’s you', 'Before booking', body);
    }
    if (st.done) return evt('shield', 'Verified for this chat · phone ending 02', '2:08 pm', 'evt-in');
    body = lv('', 'Code sent to', 'The phone on record, ending in 02') +
      '<form class="inl" data-form="code" novalidate><label class="in in-code"><span>6-digit code</span><input id="code-input" data-fk="code-input" inputmode="numeric" autocomplete="one-time-code" maxlength="6" value="' + (st.value || '') + '"' + (st.err ? ' aria-invalid="true" aria-describedby="code-err"' : '') + '></label>' +
      '<button class="btn btn-p" data-fk="code-verify">Verify</button></form>' + (st.err ? '<p class="err" id="code-err" role="alert">' + st.err + '</p>' : '') +
      '<p class="links"><a href="#code" data-act="inbox" data-fk="inbox-link">Open the demo inbox</a> <button type="button" class="linkbtn" data-act="stub" data-msg="Demo: a new code is offered here when a code has expired, up to the per-conversation cap. The code in the demo inbox stays 482913." data-fk="resend">Send a new code</button></p>' +
      '<p class="hint">Demo: codes go to a simulated inbox, never a real phone. A code lasts 10 minutes; 3 tries.</p>';
    return acard('shield', 'Confirming it’s you', 'Code sent', body);
  }
  function cConfirm(S) {
    var v = S.visit;
    var body = '<div class="rows">' + lv('', 'Date', v.day.full + ', 2026') + lv('', 'Window', wtxt(v.winKey)) + lv('', 'Technician', v.tech) + lv('', 'Fee that applies', '$89 diagnostic visit') + '</div>' +
      '<p class="hint">' + v.feeNote + '</p><h4 class="next-h">What happens next</h4><ul class="next">' +
      '<li>' + ic('check') + 'The technician arrives any time inside your window.</li>' +
      '<li>' + ic('check') + 'Changes are free until ' + v.freeUntil + '. After that, a $49 late-cancellation fee applies.</li></ul>';
    return acard('cal', 'Your visit', '<span class="tag">' + ic('check') + 'Booked</span>', body, 'step-visit');
  }
  function cAccount() {
    var rows = [['Diagnostic visit', '$89.00'], ['Contactor replacement', '$245.00'], ['After-hours dispatch', '$144.00']];
    var body = '<div class="rows">' + lv('', 'Issued', 'Oct 2, 2026') + lv('', 'Due', 'Nov 1, 2026') + '</div>' +
      '<table class="lines"><caption class="sr">Invoice lines</caption><thead><tr><th scope="col">Line</th><th scope="col">Amount</th></tr></thead><tbody>' +
      rows.map(function (r) { return '<tr><td>' + r[0] + '</td><td>' + r[1] + '</td></tr>'; }).join('') + '</tbody><tfoot><tr><th scope="row">Total</th><td>$478.00</td></tr></tfoot></table>';
    return acard('receipt', 'Invoice INV-204411', 'Balance $478.00 · unpaid', body);
  }
  function byButton(S) {
    for (var i = S.items.length - 1; i >= 0 && i >= S.items.length - 3; i--) if (S.items[i].viaButton) return true;
    return false;
  }
  function created(r) { return '<div class="logevt">' + evt('receipt', 'Case ' + r.ref + ' created', '2:14 pm') + '</div>'; }
  function cHandoff(S, c) {
    var r = S.request, st = S.cards.follow || {};
    var reason = byButton(S) ? 'You asked for a person.' : 'Billing disputes go to a person. I can’t change or remove charges.';
    var body = '<p class="reason">' + reason + '</p><h3 class="promise">' + c.TXT.promise + '</h3><div class="rows">' + lv('', 'Due', 'Mon Oct 19, 7:00 pm') +
      lv('', 'Status', '<span class="tag">' + ic('clock') + 'Waiting for a representative</span>') + '</div>';
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
        '<div class="acts"><button type="button" class="btn btn-p" data-act="follow-save" data-fk="fu-save">Save my choice</button></div>';
    }
    return created(r) + acard('ticket', 'Your request', '<code class="mono">' + r.ref + '</code>', body, 'step-handoff');
  }
  function cQueued(S, c) {
    var joined = S.live === 'joined';
    var body = '<p class="reason">' + (byButton(S) ? 'You asked for a person.' : 'Billing disputes go to a person. I can’t change or remove charges.') + '</p>' +
      '<h3 class="promise">' + c.TXT.queued + '</h3><div class="rows">' +
      lv('', 'Status', '<span class="tag">' + (joined ? ic('person') + 'A representative has joined this chat' : ic('clock') + 'Waiting for a representative') + '</span>') + '</div>';
    return created(S.request) + acard('ticket', 'Your request', '<code class="mono">' + S.request.ref + '</code>', body, 'step-handoff');
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

  /* ---------- conversation: a name line over every message ---------- */
  var NAME = { assistant: 'Meridian assistant', customer: 'You', rep: 'Riley' };
  var SUFFIX = { assistant: ' · automated', customer: '', rep: ' · Representative (demo)' };
  function turnHTML(who, time, html, extra) {
    var lead = who === 'assistant' ? mark() : who === 'rep' ? '<span class="disc" aria-hidden="true">R</span>' : '';
    return '<div class="turn turn-' + who + '"><p class="name">' + lead + '<b>' + NAME[who] + '</b>' + SUFFIX[who] + ' · <time>' + time + '</time></p>' +
      (html ? '<div class="blk">' + html + '</div>' : '') + (extra || '') + '</div>';
  }
  function item(it, S, c) {
    if (it.kind === 'pending') return '<div class="logevt pending"><p class="evt"><span class="evt-t">' + (it.stage === 2 ? 'Still working on this…' : 'Meridian assistant is replying…') + '</span></p></div>';
    if (it.kind === 'event') return '<div class="logevt' + (it.icon === 'person' ? ' is-join' : '') + '">' + evt('info', it.html, it.time) + '</div>';
    var extra = (it.card ? card(it.card, S, c) : '') + (it.after ? '<div class="blk">' + it.after + '</div>' : '') + (it.sources ? sources(it.sources, c) : '');
    var t = turnHTML(it.who, it.time, it.html, extra);
    return it.quiet ? t.replace('class="turn turn-assistant', 'class="turn turn-assistant is-quiet') : t;
  }

  function safety(c, mode) {
    return '<section class="safety' + (mode ? ' safety-' + mode : '') + '"' + (mode ? '' : ' role="alert"') + ' aria-label="Danger: safety instruction">' +
      '<div class="sf-band">' + warnSolid() + '<p class="sf-w">DANGER</p></div>' +
      '<ol class="sf-list"><li>Leave the home immediately.</li><li>Call 911 or your gas utility from outside.</li></ol>' +
      "<p class=\"sf-p\">Don't flip any light switches, open windows near the furnace, or restart any equipment.</p></section>";
  }

  /* ---------- what's settled ---------- */
  function pnCard(icon, title, meta, body, cls) {
    return '<section class="acard pn-s' + cls + '"><header class="cardhead">' + ic(icon) + '<h3>' + title + '</h3><span class="cardmeta">' + meta + '</span></header><div class="cardbody">' + body + '</div></section>';
  }
  function panel(S, c, mode) {
    var h = mode === 'strip' ? '' : '<header class="pn-h"><h2>What’s settled</h2><p>Fills in as things are confirmed.</p></header>';
    if (S.safety) return h + safety(c, 'panel');
    var hl = function (k) { return S.hl === k ? ' is-hl' : ''; };
    var v = S.visit, r = S.request, out = h;
    if (S.staffing === 'sim') out += pnCard(S.live === 'joined' ? 'pause' : 'chat', 'Who is replying', '', '<p>' + (S.live === 'joined' ? 'Riley (demo representative). The assistant is paused.' : 'The automated assistant.') + '</p>', hl('control'));
    out += pnCard('cal', 'Your visit', '', v ? '<div class="rows">' + lv('', 'Date', v.day.long) + lv('', 'Window', wtxt(v.winKey)) + lv('', 'Technician', v.tech) + lv('', 'Fee', '$89 diagnostic visit') + '</div>' : '<p>Nothing booked yet.</p>', hl('visit') + (v ? '' : ' is-empty'));
    if (r && r.live) out += pnCard('ticket', 'Your request', '<code class="mono">' + r.ref + '</code>', '<div class="rows">' + lv('', 'Reference', r.ref) + '</div><p>' + (S.live === 'joined' ? 'A representative has joined this chat.' : 'Waiting for a representative to join. No time is promised.') + '</p>', hl('request'));
    else if (r) out += pnCard('ticket', 'Your request', '<code class="mono">' + r.ref + '</code>', '<p>A representative will get back to you within 1 business day.</p><div class="rows">' +
      lv('', 'Due', r.due) + lv('', 'Follow-up', r.follow ? r.follow.channel + (r.follow.when ? ', ' + r.follow.when.toLowerCase() : '') : 'Not chosen yet') + '</div>', hl('request'));
    else out += pnCard('ticket', 'Your request', '', '<p>No request open.</p>', ' is-empty');
    out += pnCard('shield', 'Identity', '', '<p>' + (S.identity === 'verified' ? 'Verified for this chat · phone ending 02' : S.identity === 'sent' ? 'Code sent to the phone ending in 02' : 'Not checked yet. Only needed for private details or a booking.') + '</p>', hl('identity') + (S.identity ? '' : ' is-empty'));
    return out;
  }
  function stripSummary(S) {
    if (S.safety) return ic('warn') + '<span class="st-l">Leave the home</span>';
    var bits = [];
    if (S.visit) bits.push('<span>' + ic('cal') + S.visit.day.long + ', ' + wtxt(S.visit.winKey) + '</span>');
    if (S.request) bits.push('<span>' + ic('ticket') + S.request.ref + (S.request.live ? '' : ', due Mon 7:00 pm') + '</span>');
    return '<span class="st-l">What’s settled</span><span class="st-b">' + (bits.length ? bits.join('') : '<span class="st-none">Nothing yet</span>') + '</span>';
  }
  function staffing(S) { return S.staffing === 'sim' ? 'Simulated staff on shift (demo)' : 'Nobody online'; }
  function banner(S, c) {
    if (S.staffing !== 'sim') return '';
    return '<p>' + ic('info') + c.TXT.staffBanner + '</p>' + (S.live === 'queued' ? '<button type="button" class="btn btn-q btn-s" data-act="demo-join">Demo: Riley claims the case and joins</button>' : '');
  }
  function assistantState(S) {
    var ref = S.request ? ' · Reference <code class="mono">' + S.request.ref + '</code>' : '';
    return S.live === 'joined' ? 'Riley (demo representative) is replying · assistant paused' + ref : 'Automated assistant' + ref;
  }

  function chatShell() {
    return '<div class="chat"><header class="ch-head"><div class="brand">' + mark() + '<div class="brand-t"><p class="brand-n">Meridian Home Comfort</p><p class="brand-s" id="assistant-state"></p></div></div>' +
      '<button type="button" class="link-b" data-act="stub" data-msg="The demo guide (SCR-3) is not part of this direction prototype.">Demo guide</button></header>' +
      '<div class="demo-bar" aria-label="Demo status"><span class="chip">Fri Oct 16, 2026 · demo date</span><span class="chip" id="staffing"></span></div>' +
      '<div id="banner" class="banner" hidden></div>' +
      '<details id="strip" class="strip"><summary id="strip-summary"></summary><div id="strip-body" class="strip-b"></div></details>' +
      '<div class="ch-main"><div class="ch-col"><div id="pinned" class="pinned" hidden></div>' +
      '<div id="thread" class="thread" role="log" aria-label="Conversation" tabindex="0"><p class="day-div"><span>Fri Oct 16, 2026 (demo date)</span></p></div>' +
      '<form class="composer" data-form="composer"><div class="cp-top"><button type="button" class="talk" id="talk" data-act="talk">' + ic('head') + 'Talk to a person</button><span id="composer-hint" class="cp-hint"></span></div>' +
      '<div class="cp-well"><label for="composer-input" class="sr">Message</label><input id="composer-input" autocomplete="off"><button class="send">Send</button></div></form></div>' +
      '<aside id="panel" class="panel" aria-label="What’s settled"></aside></div></div>';
  }
  function caseShell() {
    return '<div class="console"><header class="ch-head cs-head"><div class="brand"><span class="disc" aria-hidden="true">R</span><div class="brand-t"><p class="brand-n">Meridian staff console</p><p class="brand-s">Demo staff sign-in · Riley (demo representative)</p></div></div>' +
      '<div class="demo-bar-inline"><span class="chip">Fri Oct 16, 2026 · demo date</span></div></header><div id="case-root" class="case-root"></div></div>';
  }
  function inbox() {
    return '<dialog id="inbox" class="inbox" aria-labelledby="inbox-h"><h2 id="inbox-h">Demo delivery inbox</h2><p class="hint">Simulated messages. Nothing is sent to anyone. This exists only so reviewers can complete verification.</p>' +
      '<div class="inbox-m"><p class="t">To the phone ending in 02 · Fri Oct 16, 2:07 pm</p><p>Your Meridian Home Comfort verification code is <b>482913</b>. It expires in 10 minutes.</p></div>' +
      '<div class="acts"><button type="button" class="btn btn-p" data-act="inbox-use">Use this code in the chat</button><button type="button" class="btn btn-q" data-act="inbox-close">Close</button></div></dialog>';
  }

  /* ---------- staff console (S2 layout) ---------- */
  function qrow(q, CS) {
    var sel = CS.sel === q.ref;
    var tag = q.overdue ? '<span class="ptag ptag-strong">' + ic('clock') + 'Overdue</span>' : q.band === 'safety' ? '<span class="ptag">' + ic('warn') + 'Safety</span>' : '<span class="ptag">' + q.p + ' ' + q.pword + '</span>';
    var due = q.overdue ? 'was due ' + q.due : q.band === 'safety' ? q.note : 'Due ' + q.due;
    return '<li><button type="button" class="qrow' + (sel ? ' is-sel' : '') + '" data-act="case-select" data-val="' + q.ref + '" data-ref="' + q.ref + '" data-fk="q-' + q.ref + '"' + (sel ? ' aria-current="true"' : '') + '>' +
      '<span class="qr-1"><b class="qr-n">' + q.reason + '</b>' + tag + '</span><span class="qr-d">' + q.who + ' · <code class="mono">' + q.ref + '</code> · ' + due + '</span></button></li>';
  }
  function logTranscript(K, CS) {
    var out = '';
    K.transcript.forEach(function (t) {
      if (t.who === 'event') { out += '<div class="logevt">' + evt('info', t.text, t.time) + '</div>'; return; }
      out += turnHTML(t.who, t.time, t.text, '');
    });
    var notes = [{ time: 'Fri 2:14 pm', who: 'System check', text: 'The invoice’s after-hours line ($144) differs from the fee schedule ($149). For staff only; not shown to the customer.' }]
      .concat(CS.acts.slice(2).map(function (a) { return { time: a.time, who: 'Riley (demo representative)', text: a.text }; }));
    out += notes.map(function (n) { return '<div class="note"><p class="note-h">' + ic('lock') + 'Internal note · ' + n.who + '</p><p>' + n.text + '</p><time>' + n.time + '</time></div>'; }).join('');
    return '<div class="thread-mini">' + out + '</div>';
  }
  function caseView(CS, c) {
    var K = c.CASE;
    var wide = window.matchMedia('(min-width: 1100px)').matches;
    var safetyRows = c.QUEUE.filter(function (q) { return q.band === 'safety'; }), rest = c.QUEUE.filter(function (q) { return q.band !== 'safety'; });
    var queue = '<details class="q-col"' + (wide ? ' open' : '') + '><summary class="q-sum">' + ic('chat') + 'Queue · ' + c.QUEUE.length + ' cases</summary><div class="q-in">' +
      '<div class="who"><span class="disc" aria-hidden="true">R</span><div><b>Riley</b><small>Representative (demo)</small></div></div>' +
      '<h3 class="q-g">Needs attention first</h3><ul data-queue class="qlist">' + safetyRows.map(function (q) { return qrow(q, CS); }).join('') + '</ul>' +
      '<h3 class="q-g">By due time</h3><ul data-queue class="qlist">' + rest.map(function (q) { return qrow(q, CS); }).join('') + '</ul></div></details>';

    var sel = null;
    c.QUEUE.forEach(function (q) { if (q.ref === CS.sel) sel = q; });
    var claim = '';
    if (CS.sel === K.ref) {
      claim = CS.claimed ? '<span class="tag">' + ic('person') + 'Claimed by Riley (demo)</span>'
        : '<span class="split"><button type="button" class="split-m" data-act="case-claim" data-fk="act-claim">Claim</button><button type="button" class="split-c" data-act="stub" data-msg="Release and Resolve live in this menu in the product. They are not built in this prototype." aria-label="More actions">' + ic('chev') + '</button></span>';
    }
    var bar = '<div class="bar"><code class="mono">' + CS.sel + '</code><span class="titlepill">' + (CS.sel === K.ref ? 'Billing dispute · due ' + K.due : (sel ? sel.reason : '')) + '</span>' + claim + '</div>';

    var brief;
    if (CS.sel !== K.ref) {
      brief = '<main class="brief" id="brief"><h2 class="brief-h">Brief</h2><div class="acard"><div class="cardbody"><p>Seeded queue row. This direction prototype builds the brief only for MHC-C-0007.</p><div class="acts"><button type="button" class="cbtn cbtn-p" data-act="case-select" data-val="MHC-C-0007" data-fk="q-MHC-C-0007">Open MHC-C-0007</button></div></div></div></main>';
    } else {
      var secs = K.sections.map(function (s) {
        var items = s.items.map(function (x) {
          return '<li>' + (s.kind === 'decide' ? ic('question') : '') + '<span>' + x.t + (x.src ? ' <button type="button" class="srcchip" data-act="src-jump" data-val="' + x.src + '" data-fk="st-' + s.n + '-' + x.src + '">' + ic('doc') + x.tag + '</button>' : '') + '</span></li>';
        }).join('');
        var list = '<ul>' + items + '</ul>';
        if (s.kind === 'claim') list = '<div class="claims"><p class="lbl">' + ic('info') + 'Customer says · not checked</p>' + list + '</div>';
        return '<details class="bsec bsec-' + s.kind + '" open><summary><span class="bs-n">' + s.n + '</span>' + s.h + '</summary>' + list + '</details>';
      }).join('');
      var status = CS.claimed ? evt('person', 'Claimed by Riley (demo) · due Mon Oct 19, 7:00 pm', '', 'evt-status') : evt('wait', 'Unassigned, nobody owns it yet · due Mon Oct 19, 7:00 pm', '', 'evt-status');
      var draft = '<section class="draft" aria-label="Promise shown to the customer"><div class="dhead">' + ic('spark') + '<b>Promise shown to the customer</b></div><p class="big">' + K.promise + '</p>' +
        lv('', 'Due', K.due) + lv('', 'Follow up by', K.follow.channel) + lv('', 'Destination', K.follow.dest) + lv('', 'Best time', K.follow.when) + '</section>';
      var acts = '<section class="cacts" aria-label="Actions"><div class="acts">' +
        '<button type="button" class="cbtn" data-act="case-call" data-fk="act-call"' + (CS.claimed ? '' : ' disabled') + '>' + ic('phone') + 'Log a call</button>' +
        '<button type="button" class="cbtn" data-act="case-flag" data-fk="act-flag">' + ic('flag') + (CS.flagged ? 'Flagged' : 'Flag') + '</button>' +
        '<button type="button" class="cbtn" disabled>' + ic('chat') + 'Join chat</button></div>' +
        '<p class="hint">' + (CS.claimed ? '' : 'Claim the case to log a call. ') + 'Join chat works only while the customer is in a live chat; nobody was online when this case was made.</p>' +
        (CS.callOpen ? '<form class="mini" data-form="call"><fieldset class="fu"><legend>Log a call to the number ending in 02 (demo)</legend>' +
          '<label class="radio"><input type="radio" name="outcome" value="Reached the customer" data-fk="call-outcome" checked><span>Reached the customer</span></label>' +
          '<label class="radio"><input type="radio" name="outcome" value="No answer"><span>No answer</span></label></fieldset><p class="hint">Demo: recorded, not sent. No call is placed.</p><div class="acts"><button class="cbtn cbtn-p">Record</button></div></form>' : '') +
        (CS.flagOpen ? '<form class="mini" data-form="flag"><label class="in"><span>What is wrong?</span><select data-fk="flag-reason"><option>The brief left something out</option><option>An answer was wrong</option><option>The escalation was not needed</option></select></label><div class="acts"><button class="cbtn cbtn-p">Add to review list</button></div></form>' : '') +
        '<div class="activity">' + CS.acts.map(function (a) { return evt('info', a.text, a.time); }).join('') + '</div></section>';
      brief = '<main class="brief" id="brief"><h2 class="brief-h">Brief</h2>' + status + draft + secs + acts + '</main>';
    }

    var tabs = '<div class="tabrow" role="tablist" aria-label="Evidence">' +
      '<button type="button" role="tab" id="tab-sources" data-fk="tab-sources" aria-selected="' + (CS.tab === 'sources') + '" aria-controls="ev-panel" data-act="case-tab" data-val="sources">Sources (' + K.sources.length + ')</button>' +
      '<button type="button" role="tab" id="tab-conversation" data-fk="tab-conversation" aria-selected="' + (CS.tab === 'conversation') + '" aria-controls="ev-panel" data-act="case-tab" data-val="conversation">Conversation</button></div>';
    var ev = CS.tab === 'sources' ? K.sources.map(function (s) {
      var b = s.rows
        ? '<table class="snap"><caption class="sr">' + s.title + ': what the AI saw and now</caption><thead><tr><th scope="col">Field</th><th scope="col">What the AI saw<small>Fri 2:10 pm</small></th><th scope="col">Now<small>Fri 2:20 pm</small></th></tr></thead><tbody>' +
          s.rows.map(function (r) { return '<tr><th scope="row">' + r[0] + '</th><td>' + r[1] + '</td><td>' + r[2] + '</td></tr>'; }).join('') + '</tbody></table>'
        : '<blockquote class="quote">' + s.quote + '</blockquote>';
      return '<section class="acard src-card' + (CS.hl === s.id ? ' is-hl' : '') + '" id="src-' + s.id + '" tabindex="-1"><header class="cardhead">' + ic('doc') + '<h3>' + s.title + '</h3><span class="cardmeta">' + s.ver + '</span></header><div class="cardbody"><p class="src-meta">' + s.file + '</p>' + b +
        (s.fact ? '<p class="fact"><span>Fact</span>' + s.fact + '</p>' : '') + evt('check', s.status, '', 'evt-in') + '</div></section>';
    }).join('') : logTranscript(K, CS);
    var evidence = '<aside class="evidence" aria-label="Evidence"><header class="col-h"><h2>Evidence</h2><p>What the AI saw, next to what is true now.</p></header>' + tabs + '<div id="ev-panel" role="tabpanel" aria-labelledby="tab-' + CS.tab + '" class="ev-p">' + ev + '</div></aside>';
    return '<div class="cs-frame"><div class="cs-grid">' + queue + '<div class="cs-main">' + bar + '<div class="cols">' + brief + evidence + '</div></div></div></div>';
  }

  /* the embedded fonts swap in after first paint and change line wraps: once they are in, keep the thread on its latest message */
  if (document.fonts && document.fonts.load) {
    Promise.all(['A5 Display', 'A5 Sans', 'A5 Mono'].map(function (f) { return document.fonts.load('16px "' + f + '"'); })).then(function () {
      var t = document.getElementById('thread');
      if (t) t.scrollTop = t.scrollHeight;
    }, function () { /* fallback fonts: nothing to do */ });
  }

  window.SKIN = {
    code: 'A5', name: 'Service desk', pending: true,
    chatShell: chatShell, caseShell: caseShell, item: item, panel: panel, stripSummary: stripSummary,
    staffing: staffing, banner: banner, assistantState: assistantState, safety: safety, inbox: inbox, caseView: caseView
  };
})();
