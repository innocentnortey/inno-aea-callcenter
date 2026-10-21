/* A2 · Route sheet: markup construction. The conversation is a route of numbered stops; facts arrive
   as perforated ticket stubs with mono labels and big tabular times; staff triage on a dark ink board.
   Read by the shared engine as window.SKIN. */
(function () {
  'use strict';
  var I = {
    person: '<circle cx="10" cy="7" r="3"/><path d="M4.5 16.5c.7-2.9 2.9-4.5 5.5-4.5s4.8 1.6 5.5 4.5"/>',
    send: '<path d="M4 10h11.5M11.5 6 15.5 10l-4 4"/>',
    clock: '<circle cx="10" cy="10" r="6.5"/><path d="M10 6.5V10l2.5 1.5"/>',
    pin: '<path d="M10 17s5-4.6 5-8.5a5 5 0 1 0-10 0C5 12.4 10 17 10 17Z"/><circle cx="10" cy="8.5" r="1.8"/>',
    check: '<path d="m5 10.5 3 3 7-7"/>',
    arrow: '<path d="M7 13 13 7M8 7h5v5"/>',
    info: '<circle cx="10" cy="10" r="6.5"/><path d="M10 9v4.5M10 6.6v.1"/>'
  };
  function ic(n) { return '<svg class="ic" viewBox="0 0 20 20" aria-hidden="true" focusable="false">' + (I[n] || I.info) + '</svg>'; }
  function warnSolid() { return '<svg class="ic-warn" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 2.6 23 21.4H1z" fill="currentColor"/><path d="M12 9v6M12 17.6v.2" stroke="var(--safety-band)" stroke-width="2.4" stroke-linecap="round"/></svg>'; }
  function lbl(t, cls) { return '<span class="lbl ' + (cls || '') + '">' + t + '</span>'; }
  function cell(l, v, cls) { return '<div class="cell ' + (cls || '') + '">' + lbl(l) + '<span class="cell-v">' + v + '</span></div>'; }
  function stub(head, main, tail, cls) {
    return '<section class="stub ' + (cls || '') + '"><div class="stub-main">' + (head ? '<header class="stub-h">' + head + '</header>' : '') + main + '</div>' +
      (tail ? '<div class="perf" aria-hidden="true"></div><div class="stub-tail">' + tail + '</div>' : '') + '</section>';
  }
  function bars() { var s = ''; for (var i = 0; i < 26; i++) s += '<i style="width:' + [1, 2, 1, 3, 1, 2][i % 6] + 'px"></i>'; return '<span class="bars" aria-hidden="true">' + s + '</span>'; }
  function stops(list, cls) {
    return '<ol class="stops ' + (cls || '') + '">' + list.map(function (s, i) {
      var st = s.st || 'todo';
      return '<li class="sp is-' + st + '"><span class="sp-d' + (s.end ? ' sp-end' : '') + '" aria-hidden="true">' + (s.end ? s.end : String(i + 1).padStart(2, '0')) + '</span><span class="sp-b"><span class="sp-l">' + s.l +
        (st === 'now' ? '<span class="sr"> (current)</span>' : st === 'done' ? '<span class="sr"> (done)</span>' : '') + '</span>' +
        '<span class="sp-c">' + { done: 'Completed', now: 'Next', todo: 'Scheduled' }[st] + '</span>' + (s.t ? '<time class="sp-t">' + s.t + '</time>' : '') + '</span></li>';
    }).join('') + '</ol>';
  }
  function key(label, attrs, cls) { return '<button type="button" class="key ' + (cls || '') + '" ' + attrs + '>' + label + '</button>'; }
  function sources(keys, c) {
    return '<div class="srcs">' + keys.map(function (k) {
      var s = c.SRC[k];
      return '<details class="src"><summary>' + lbl('SRC') + '<span class="src-f">' + s.file + '</span><span class="src-v">' + s.ver + '</span></summary>' +
        '<div class="src-b"><q>' + s.quote + '</q>' + (s.note ? '<p>' + s.note + '</p>' : '') + '</div></details>';
    }).join('') + '</div>';
  }

  /* ---------- cards ---------- */
  function cChecks(S, c) {
    var st = S.cards.checks || {};
    var main = '<ol class="chk">' + c.CHECKS.map(function (t, i) { return '<li><span class="chk-n">' + (i + 1) + '</span><span>' + t + '</span></li>'; }).join('') + '</ol>';
    var foot = st.done ? '<p class="stub-done">' + ic('check') + (st.choice === 'skip' ? 'Checks skipped' : 'Tried. Still not cooling') + '</p>'
      : '<div class="keys">' + key('Skip the checks', 'data-act="choose" data-key="checks" data-val="skip" data-fk="checks-skip"', 'key-p') +
        key('I tried them. Still not cooling', 'data-act="choose" data-key="checks" data-val="tried" data-fk="checks-tried"') + '</div>';
    return stub(lbl('Quick checks') + lbl('Optional', 'lbl-dim'), main + foot, '', 'stub-checks');
  }
  function cQuestion(card, S) {
    var st = S.cards[card.key] || {};
    var foot = st.done ? '<p class="stub-done">' + ic('check') + 'Answered: ' + { yes: 'Yes', no: 'No', skip: 'Skipped' }[st.choice] + '</p>'
      : '<div class="keys" role="group" aria-label="Answer">' + [['yes', 'Yes'], ['no', 'No'], ['skip', 'Skip']].map(function (o) {
        return key(o[1], 'data-act="choose" data-key="' + card.key + '" data-val="' + o[0] + '" data-fk="' + card.key + '-' + o[0] + '"');
      }).join('') + '</div>';
    return stub(lbl('Question ' + card.n + ' / 2') + lbl('Optional', 'lbl-dim'), '<p class="q-t">' + card.q + '</p>' + foot, '', 'stub-q');
  }
  function cSlots(S, c) {
    var st = S.cards.slots || {};
    var day = null; c.DAYS.forEach(function (d) { if (d.key === st.day) day = d; });
    var tabs = '<div class="dtabs" role="group" aria-label="Day">' + c.DAYS.map(function (d) {
      var open = d.wins.filter(function (w) { return w[1] === 'open'; }).length, sel = d.key === st.day;
      return '<button type="button" class="dtab' + (sel ? ' is-sel' : '') + '" data-act="slot-day" data-val="' + d.key + '" data-fk="day-' + d.d + '" aria-pressed="' + sel + '"' + (st.done ? ' disabled' : '') + '>' +
        '<span class="dtab-w">' + d.dow + ' ' + d.d + '</span><span class="dtab-o">' + (open ? open + ' open' : 'Full') + '</span></button>';
    }).join('') + '</div>';
    var rows = '<fieldset class="wrows"><legend>' + lbl('Arrival windows · ' + day.long) + '</legend>' + day.wins.map(function (w) {
      var W = c.WIN[w[0]], taken = w[1] !== 'open', sel = st.win === w[0];
      return '<button type="button" class="wrow' + (taken ? ' is-taken' : '') + (sel ? ' is-sel' : '') + '" data-act="slot-win" data-val="' + w[0] + '" data-fk="win-' + w[0] + '" aria-pressed="' + sel + '"' + (taken || st.done ? ' disabled' : '') + '>' +
        '<span class="wrow-t">' + W.h24 + '</span><span class="wrow-h">' + W.label + '</span><span class="wrow-s">' + (taken ? 'Taken' : sel ? 'Selected' : 'Open') + '</span></button>';
    }).join('') + '</fieldset>';
    var who = st.done ? '' : '<p class="hint">Members’ fees and member-only windows appear after the code. Windows are shown, not held.</p>';
    var act = st.done ? '<p class="stub-done">' + ic('check') + 'Window chosen: ' + day.long + ', ' + c.WIN[st.win].label + '</p>'
      : '<div class="keys">' + key('Continue with this window', 'data-act="slot-book" data-fk="slot-book"', 'key-p key-inv') + '<span class="sel-sum">' + (st.win ? day.long + ' · ' + c.WIN[st.win].label : 'No window picked yet') + '</span></div>' +
        (st.err ? '<p class="err" role="alert">' + st.err + '</p>' : '');
    var tail = '<span class="lbl">Standard fee</span><span class="big-n">$89</span><span class="tail-t">Diagnostic visit. Credited toward the repair if you approve it at the same visit.</span>';
    return stub(lbl('Repair visit') + lbl('South zone · Kyle', 'lbl-dim'), tabs + rows + who + act, tail, 'stub-board');
  }
  function cConfirm(S) {
    var v = S.visit;
    var main = '<p class="hero-t">' + v.win.h24.replace(' – ', ' → ') + '</p><p class="hero-s">' + v.day.full + ', 2026 · arrives between ' + v.win.label.replace(' – ', ' and ') + '</p>' +
      '<div class="cells">' + cell('Date', v.day.long) + cell('Technician', v.tech) + cell('Fee', '$89 diagnostic') + '</div>' +
      stops([{ l: 'Booked', t: 'Fri 14:08', st: 'done', end: 'START' }, { l: 'Technician arrives in the window', t: v.day.long, st: 'now' }, { l: 'Repair approved or declined at the visit', st: 'todo', end: 'END' }], 'stops-h') +
      '<p class="note">' + ic('info') + 'Free to change or cancel until ' + v.freeUntil + '. After that, a $49 late-cancellation fee applies. ' + v.feeNote + '</p>';
    var tail = '<span class="lbl">Keep this</span><span class="tail-big">' + v.day.dow + ' ' + v.day.d + '</span><span class="tail-t">' + v.win.h24 + '</span>' + bars();
    return stub(lbl('Repair visit · booked') + '<span class="ok">' + ic('check') + 'Booked</span>', main, tail, 'stub-ticket');
  }
  function cCode(S, c) {
    var st = S.cards.code || {};
    var main;
    if (st.stage === 'locate' && !st.done) {
      main = '<form class="code-f code-loc" data-form="locate" novalidate><div class="who-f">' +
        '<label class="in"><span>Name on the account</span><input data-bind="code.name" data-fk="loc-name" value="' + c.esc(st.name || '') + '" autocomplete="name"></label>' +
        '<label class="in"><span>Phone</span><input data-bind="code.phone" data-fk="loc-phone" value="' + c.esc(st.phone || '') + '" inputmode="tel" autocomplete="tel"></label></div>' +
        '<button class="key key-p" data-fk="loc-send">Send the code</button></form>' + (st.err ? '<p class="err" role="alert">' + st.err + '</p>' : '') +
        '<p class="hint">Demo: the dataset’s test customer. The code goes to the phone on record, never to a number typed here.</p>';
      return stub(lbl('Verify') + lbl('Before booking', 'lbl-dim'), main, '', 'stub-code');
    }
    if (st.done) main = '<p class="stub-done">' + ic('check') + 'Verified for this chat</p>';
    else main = '<p class="code-to">Code sent to the phone on record, ending in <b>02</b></p><form class="code-f" data-form="code" novalidate><label class="in in-code"><span>6-digit code</span>' +
      '<input id="code-input" data-fk="code-input" inputmode="numeric" autocomplete="one-time-code" maxlength="6" value="' + (st.value || '') + '"' + (st.err ? ' aria-invalid="true" aria-describedby="code-err"' : '') + '></label>' +
      '<button class="key key-p" data-fk="code-verify">Verify</button></form>' + (st.err ? '<p class="err" id="code-err" role="alert">' + st.err + '</p>' : '') +
      '<p class="links"><a href="#code" data-act="inbox" data-fk="inbox-link">Open the demo inbox ' + ic('arrow') + '</a></p><p class="hint">Demo: codes go to a simulated inbox, never a real phone. A code lasts 10 minutes; 3 tries.</p>';
    return stub(lbl('Verify') + lbl(st.done ? 'Done' : 'Code sent', 'lbl-dim'), main, '', 'stub-code');
  }
  function cWhere(S, c) {
    var st = S.cards.where || {};
    var main = st.done ? '<p class="stub-done stub-done-0">' + ic('pin') + 'Kyle · south zone</p>'
      : '<form class="code-f" data-form="where" novalidate><label class="in"><span>ZIP code or city</span><input id="where-input" data-bind="where.value" data-fk="where-input" value="' + c.esc(st.value || '') + '" autocomplete="postal-code"' + (st.err ? ' aria-invalid="true"' : '') + '></label>' +
        '<button class="key key-p" data-fk="where-go">Show windows</button></form>' + (st.err ? '<p class="err" role="alert">' + st.err + '</p>' : '');
    return stub(lbl('Visit address') + lbl('ZIP or city', 'lbl-dim'), main, '', 'stub-where');
  }
  function cAccount() {
    var rows = [['Diagnostic visit', '$89.00'], ['Contactor replacement', '$245.00'], ['After-hours dispatch', '$144.00']];
    var main = '<p class="hero-t hero-m">$478.00</p><p class="hero-s">Balance · unpaid · due Nov 1, 2026 · issued Oct 2, 2026</p>' +
      '<table class="lines"><caption class="sr">Invoice lines</caption><thead><tr><th scope="col">Line</th><th scope="col">Amount</th></tr></thead><tbody>' +
      rows.map(function (r) { return '<tr><td>' + r[0] + '</td><td>' + r[1] + '</td></tr>'; }).join('') + '</tbody><tfoot><tr><th scope="row">Total</th><td>$478.00</td></tr></tfoot></table>';
    return stub(lbl('Invoice') + '<span class="ref">INV-204411</span>', main, '', 'stub-account');
  }
  function cHandoff(S, c) {
    var r = S.request, st = S.cards.follow || {};
    var main = '<p class="promise">' + c.TXT.promise + '</p><div class="due">' + lbl('Due') + '<span class="due-t">' + r.due24 + '</span><span class="due-s">Asked ' + r.nowAt + '</span></div>';
    if (st.done) {
      main += '<p class="stub-done">' + ic('check') + 'Follow-up saved: ' + (st.channel === 'email' ? 'email, the address on your account' : 'phone call, the number ending in 02, ' + { mornings: 'mornings', afternoons: 'afternoons', any: 'any time' }[st.when]) + '</p>';
    } else {
      main += '<fieldset class="opts"><legend>' + c.TXT.followAsk + '</legend>' +
        [['email', 'Email', 'the address on your account'], ['phone', 'Phone call', 'the number ending in 02']].map(function (o) {
          var sel = st.channel === o[0];
          return '<button type="button" class="opt' + (sel ? ' is-sel' : '') + '" aria-pressed="' + sel + '" data-act="follow-ch" data-val="' + o[0] + '" data-fk="fu-' + o[0] + '"><span class="opt-box" aria-hidden="true"></span>' + lbl(o[1]) + '<span class="opt-d">' + o[2] + '</span></button>';
        }).join('') +
        (st.channel === 'phone' ? '<div class="keys keys-sm" role="group" aria-label="Best time to call">' + [['mornings', 'Mornings'], ['afternoons', 'Afternoons'], ['any', 'Any time']].map(function (o) {
          return key(o[1], 'aria-pressed="' + (st.when === o[0]) + '" data-act="follow-when" data-val="' + o[0] + '" data-fk="fu-' + o[0] + '"', st.when === o[0] ? 'is-sel' : '');
        }).join('') + '</div>' : '') + '</fieldset><div class="keys">' + key('Save my choice', 'data-act="follow-save" data-fk="fu-save"', 'key-p') + '</div>';
    }
    return stub(lbl('Ref') + '<span class="ref">' + r.ref + '</span>', main, '', 'stub-handoff');
  }
  function cQueued(S, c) {
    var joined = S.live === 'joined';
    var main = '<p class="promise">' + c.TXT.queued + '</p>' + stops([{ l: 'You asked for a person', t: 'Fri 14:14', st: 'done', end: 'START' },
      { l: joined ? 'Riley (demo representative) joined' : 'A representative joins this chat', t: joined ? 'Fri 14:17' : '', st: joined ? 'done' : 'now' },
      { l: 'Back to the assistant, or the chat closes', st: joined ? 'now' : 'todo', end: 'END' }]);
    return stub(lbl('Ref') + '<span class="ref">' + S.request.ref + '</span>', main, '', 'stub-handoff');
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

  /* ---------- the route (thread items) ---------- */
  function item(it, S, c) {
    if (it.kind === 'event') {
      return '<div class="stop stop-evt"><span class="disc disc-evt" aria-hidden="true"></span><header class="stop-h">' + lbl('Event') + '<time>' + it.time + '</time></header><p class="evt-t">' + it.html + '</p></div>';
    }
    if (it.who === 'customer') {
      return '<div class="stop stop-c"><span class="disc disc-c" aria-hidden="true"></span><header class="stop-h">' + lbl('You') + (it.viaButton ? lbl('Button', 'lbl-dim') : '') + '<time>' + it.time + '</time></header><p class="c-t">' + it.html + '</p></div>';
    }
    if (it.who === 'rep') {
      return '<div class="stop stop-r"><span class="disc disc-r" aria-hidden="true"></span><header class="stop-h">' + lbl('Riley · representative (demo)', 'lbl-rep') + '<time>' + it.time + '</time></header><p class="r-t">' + it.html + '</p></div>';
    }
    return '<div class="stop stop-a' + (it.quiet ? ' is-quiet' : '') + '"><span class="disc disc-a" aria-hidden="true"></span><header class="stop-h">' + lbl('Meridian assistant · automated') + '<time>' + it.time + '</time></header>' +
      (it.html ? '<p class="a-t">' + it.html + '</p>' : '') + (it.card ? card(it.card, S, c) : '') + (it.after ? '<p class="a-t">' + it.after + '</p>' : '') +
      (it.sources ? sources(it.sources, c) : '') + '</div>';
  }

  function safety(c, mode) {
    return '<section class="safety' + (mode ? ' safety-' + mode : '') + '"' + (mode ? '' : ' role="alert"') + ' aria-label="Danger: safety instruction">' +
      '<p class="sf-w">' + warnSolid() + 'DANGER</p><ol class="sf-list"><li><span class="sf-n" aria-hidden="true">1</span><p>' + c.TXT.safety1 + '</p></li>' +
      '<li><span class="sf-n" aria-hidden="true">2</span><p>' + c.TXT.safety2 + '</p></li></ol></section>';
  }

  /* ---------- manifest panel ---------- */
  function panel(S, c, mode) {
    var h = mode === 'strip' ? '' : '<header class="pn-h">' + lbl('What’s settled') + '<p>Fills in as things are confirmed.</p></header>';
    if (S.safety) return h + safety(c, 'panel');
    var hl = function (k) { return S.hl === k ? ' is-hl' : ''; };
    var v = S.visit, r = S.request, out = h;
    if (S.staffing === 'sim') out += '<div class="mrow' + hl('control') + '">' + lbl('Replying') + '<span>' + (S.live === 'joined' ? 'Riley (demo representative). Assistant paused.' : 'The automated assistant') + '</span></div>';
    out += v ? '<section class="mstub' + hl('visit') + '">' + lbl('Your visit') + '<p class="m-big">' + v.win.h24.replace(' – ', ' → ') + '</p><p class="m-sub">' + v.day.long + ' · ' + v.win.label + '</p>' +
      '<div class="cells">' + cell('Technician', v.tech) + cell('Fee', '$89 diagnostic') + '</div></section>'
      : '<section class="mstub is-empty">' + lbl('Your visit') + '<p>Nothing booked yet.</p></section>';
    if (r && r.live) out += '<section class="mstub' + hl('request') + '">' + lbl('Ref') + '<span class="ref">' + r.ref + '</span><p class="m-sub">' + (S.live === 'joined' ? 'A representative has joined this chat.' : 'Waiting for a representative to join. No time is promised.') + '</p></section>';
    else if (r) out += '<section class="mstub' + hl('request') + '">' + lbl('Ref') + '<span class="ref">' + r.ref + '</span><p class="m-sub">A representative will get back to you within 1 business day.</p>' +
      '<div class="due">' + lbl('Due') + '<span class="due-t">' + r.due24 + '</span></div>' + '<div class="cells">' + cell('Follow-up', r.follow ? r.follow.channel + (r.follow.when ? ' · ' + r.follow.when : '') : 'Not chosen yet') + '</div></section>';
    else out += '<section class="mstub is-empty">' + lbl('Your request') + '<p>No request open.</p></section>';
    out += '<div class="mrow' + hl('identity') + '">' + lbl('Identity') + '<span>' + (S.identity === 'verified' ? 'Verified for this chat · phone ending 02' : S.identity === 'sent' ? 'Code sent to the phone ending in 02' : 'Not checked. Only needed for private details.') + '</span></div>';
    return out;
  }
  function stripSummary(S) {
    if (S.safety) return '<span class="st-danger">' + warnSolid() + 'DANGER · Leave the home immediately</span>';
    var bits = [];
    if (S.visit) bits.push('<span class="st-v">' + S.visit.day.dow + ' ' + S.visit.day.d + ' · ' + S.visit.win.h24 + '</span>');
    if (S.request) bits.push('<span class="st-v">' + S.request.ref + (S.request.live ? '' : ' · due Mon 19:00') + '</span>');
    return lbl('What’s settled') + (bits.length ? bits.join('') : '<span class="st-v st-none">Nothing yet</span>');
  }
  function staffing(S) { return S.staffing === 'sim' ? 'Simulated staff on shift (demo)' : 'Nobody online'; }
  function banner(S, c) {
    if (S.staffing !== 'sim') return '';
    return lbl('Demo', 'lbl-blk') + '<p>' + c.TXT.staffBanner + '</p>' + (S.live === 'queued' ? key('Demo: Riley claims the case and joins', 'data-act="demo-join"', 'key-sm') : '');
  }
  function assistantState(S) { return S.live === 'joined' ? 'Assistant paused · Riley (demo) is replying' : 'Meridian assistant · automated'; }

  function chatShell() {
    return '<div class="chat"><header class="ch-head"><div class="brand">' + lbl('Meridian Home Comfort · chat') + '<p class="brand-n" id="assistant-state"></p></div>' +
      '<button type="button" class="link-b" data-act="stub" data-msg="The demo guide (SCR-3) is not part of this direction prototype.">Demo guide</button>' +
      '<div class="demo-bar" aria-label="Demo status"><span class="blk">Fri Oct 16, 2026 (demo date)</span><span class="blk blk-st" id="staffing"></span></div></header>' +
      '<div id="banner" class="banner" hidden></div>' +
      '<details id="strip" class="strip"><summary id="strip-summary"></summary><div id="strip-body" class="strip-b"></div></details>' +
      '<div class="ch-main"><div class="ch-col"><div id="pinned" class="pinned" hidden></div>' +
      '<div id="thread" class="thread route" role="log" aria-label="Conversation" tabindex="0"></div>' +
      '<form class="composer" data-form="composer"><button type="button" class="key key-talk" id="talk" data-act="talk">' + ic('person') + 'Talk to a person</button>' +
      '<div class="cp-row"><label for="composer-input" class="sr">Message</label><input id="composer-input" autocomplete="off"><button class="send" aria-label="Send">' + ic('send') + '</button></div>' +
      '<p id="composer-hint" class="cp-hint"></p></form></div>' +
      '<aside id="panel" class="panel" aria-label="What’s settled"></aside></div></div>';
  }
  function caseShell() {
    return '<div class="console"><header class="cs-head"><div class="brand">' + lbl('Meridian · staff console') + '<p class="brand-n">Demo staff sign-in · Riley (demo representative)</p></div>' +
      '<div class="demo-bar"><span class="blk">Fri Oct 16, 2026 (demo date)</span></div></header><div id="case-root" class="case-root"></div></div>';
  }
  function inbox() {
    return '<dialog id="inbox" class="inbox" aria-labelledby="inbox-h"><header>' + lbl('Demo delivery inbox') + '<h2 id="inbox-h">Simulated messages</h2><p>Nothing is sent to anyone. This exists only so reviewers can complete verification.</p></header>' +
      '<article class="inbox-m"><p class="lbl">To ···02 · Fri 14:07</p><p>Your Meridian Home Comfort verification code is <b class="mono">482913</b>. It expires in 10 minutes.</p></article>' +
      '<div class="keys">' + key('Use this code in the chat', 'data-act="inbox-use"', 'key-p') + key('Close', 'data-act="inbox-close"') + '</div></dialog>';
  }

  /* ---------- staff console ---------- */
  function pblk(p, w) { return '<span class="pblk pblk-' + p + '"><b>' + p + '</b>' + w + '</span>'; }
  function qrow(q, CS) {
    var sel = CS.sel === q.ref;
    return '<li><button type="button" class="qrow' + (sel ? ' is-sel' : '') + '" data-act="case-select" data-val="' + q.ref + '" data-ref="' + q.ref + '" data-fk="q-' + q.ref + '"' + (sel ? ' aria-current="true"' : '') + '>' +
      pblk(q.p, q.pword) + '<span class="qr-m"><span class="qr-ref">#' + q.ref + '</span><span class="qr-reason">' + q.reason + '</span><span class="qr-who"><span class="ini" aria-hidden="true">' + q.ini + '</span>' + q.who + ' · ' + q.owner + '</span></span>' +
      '<span class="qr-due' + (q.overdue ? ' is-over' : '') + '">' + (q.overdue ? ic('clock') + '<b>Overdue</b>' : '') + '<span>' + q.due24 + '</span>' + (q.overdue ? '<span class="sr"> (due ' + q.due + ')</span>' : '') + '</span></button></li>';
  }
  function caseView(CS, c) {
    var K = c.CASE;
    var wide = window.matchMedia('(min-width: 1100px)').matches;
    var queue = '<details class="board"' + (wide ? ' open' : '') + '><summary class="b-sum">' + lbl('Queue') + '<span>' + c.QUEUE.length + ' cases</span></summary><div class="b-in">' +
      '<header class="b-h">' + lbl('Needs my action') + '<span class="cnt">' + c.QUEUE.length + '</span></header><p class="b-hint">Safety and danger first, then by due time · seeded demo cases · <kbd>J</kbd> <kbd>K</kbd> to move, <kbd>Enter</kbd> to open</p>' +
      '<ul data-queue class="qlist">' + c.QUEUE.map(function (q) { return qrow(q, CS); }).join('') + '</ul></div></details>';

    var brief;
    if (CS.sel !== K.ref) {
      brief = '<main class="brief" id="brief"><section class="stub"><div class="stub-main"><p>Seeded queue row. This direction prototype builds the brief only for <span class="ref">MHC-C-0007</span>.</p><div class="keys">' +
        key('Open MHC-C-0007', 'data-act="case-select" data-val="MHC-C-0007" data-fk="q-MHC-C-0007"', 'key-p') + '</div></div></section></main>';
    } else {
      var stIdx = CS.claimed ? 1 : 0;
      var route = stops(K.states.map(function (s, i) { return { l: s, st: i < stIdx ? 'done' : i === stIdx ? 'now' : 'todo', t: i === 0 ? 'Fri 14:14' : i === 1 && CS.claimed ? 'Fri 14:20' : '', end: i === 0 ? 'START' : i === K.states.length - 1 ? 'END' : '' }; }), 'stops-h');
      var idx = '<nav class="sidx" aria-label="Brief sections">' + K.sections.map(function (s) { return '<a href="#stop-' + s.n + '" onclick="event.preventDefault();document.getElementById(\'stop-' + s.n + '\').scrollIntoView({block:\'start\'});document.getElementById(\'stop-' + s.n + '\').focus({preventScroll:true})">' + String(s.n).padStart(2, '0') + '<span class="sr"> ' + s.h + '</span></a>'; }).join('') + '</nav>';
      var bstops = '<ol class="bstops">' + K.sections.map(function (s) {
        var items = s.items.map(function (x) {
          return '<li><span>' + x.t + '</span>' + (x.src ? '<button type="button" class="srcb" data-act="src-jump" data-val="' + x.src + '" data-fk="st-' + s.n + '-' + x.src + '">' + lbl('Src') + x.tag + '</button>' : '') + '</li>';
        }).join('');
        return '<li class="bstop bstop-' + s.kind + '" id="stop-' + s.n + '" tabindex="-1"><span class="bs-d" aria-hidden="true">' + String(s.n).padStart(2, '0') + '</span><div class="bs-b"><h3 class="bs-h">' + s.h + '</h3>' +
          (s.kind === 'claim' ? lbl('Not checked', 'lbl-nc') : '') + '<ul>' + items + '</ul></div></li>';
      }).join('') + '</ol>';
      var acts = '<div class="acts"><div class="keys">' +
        (CS.claimed ? '<span class="ok">' + ic('check') + 'Claimed · Riley (demo)</span>' : key('Claim', 'data-act="case-claim" data-fk="act-claim"', 'key-p key-mono')) +
        key('Log a call', 'data-act="case-call" data-fk="act-call"' + (CS.claimed ? '' : ' disabled'), 'key-mono') +
        key(CS.flagged ? 'Flagged' : 'Flag', 'data-act="case-flag" data-fk="act-flag"', 'key-mono') +
        key('Join chat', 'disabled', 'key-mono') + '</div>' +
        '<p class="hint">' + (CS.claimed ? '' : 'Claim the case to log a call. ') + 'Join chat works only while the customer is in a live chat; nobody was online when this case was made.</p>' +
        (CS.callOpen ? '<form class="mini-f" data-form="call"><fieldset><legend>Log a call to ···02 (demo)</legend>' +
          '<label class="rd"><input type="radio" name="outcome" value="Reached the customer" data-fk="call-outcome" checked> Reached the customer</label>' +
          '<label class="rd"><input type="radio" name="outcome" value="No answer"> No answer</label></fieldset><p class="hint">Demo: recorded, not sent. No call is placed.</p>' +
          '<button class="key key-p key-mono">Record</button></form>' : '') +
        (CS.flagOpen ? '<form class="mini-f" data-form="flag"><label class="in"><span>What is wrong?</span><select data-fk="flag-reason"><option>The brief left something out</option><option>An answer was wrong</option><option>The escalation was not needed</option></select></label><button class="key key-p key-mono">Add to review list</button></form>' : '') +
        '<ol class="log">' + CS.acts.map(function (a) { return '<li><time>' + a.time.replace('2:14 pm', '14:14').replace('2:15 pm', '14:15').replace('2:20 pm', '14:20').replace('2:22 pm', '14:22').replace('2:23 pm', '14:23') + '</time><span>' + a.text + '</span></li>'; }).join('') + '</ol></div>';
      brief = '<main class="brief" id="brief"><header class="bh">' + lbl(K.reason + ' · ' + K.p + ' ' + K.pword) + '<span class="ref">REF ' + K.ref + '</span>' +
        '<h1 class="bh-t"><span class="bh-due">' + lbl('Due') + K.due24 + '</span><span class="bh-n">' + K.title + '</span></h1><p class="bh-m">Created Fri Oct 16, 14:14 · ' + (CS.claimed ? 'Claimed by Riley (demo)' : 'Unassigned, nobody owns it yet') + '</p></header>' +
        route +
        '<section class="pstub" aria-label="Promise and follow-up">' + lbl('Promise shown to the customer') + '<p>' + K.promise + '</p><div class="cells">' + cell('Follow up by', K.follow.channel) + cell('Destination', K.follow.dest) + cell('Best time', K.follow.when) + '</div></section>' +
        idx + bstops + acts + '</main>';
    }

    var tabs = '<div class="tabs" role="tablist" aria-label="Evidence">' +
      '<button type="button" role="tab" id="tab-sources" data-fk="tab-sources" aria-selected="' + (CS.tab === 'sources') + '" aria-controls="ev-panel" data-act="case-tab" data-val="sources">Sources <b>' + K.sources.length + '</b></button>' +
      '<button type="button" role="tab" id="tab-conversation" data-fk="tab-conversation" aria-selected="' + (CS.tab === 'conversation') + '" aria-controls="ev-panel" data-act="case-tab" data-val="conversation">Conversation</button></div>';
    var ev;
    if (CS.tab === 'sources') {
      ev = K.sources.map(function (s) {
        var body = s.rows
          ? '<table class="snap"><caption class="sr">' + s.title + ': snapshot and now</caption><thead><tr><th scope="col"><span class="sr">Field</span></th><th scope="col">' + lbl('Snapshot') + '<small>Fri 14:10</small></th><th scope="col" class="now">' + lbl('Now') + '<small>Fri 14:20</small></th></tr></thead><tbody>' +
            s.rows.map(function (r) { return '<tr><th scope="row">' + r[0] + '</th><td>' + r[1] + '</td><td class="now">' + r[2] + '</td></tr>'; }).join('') + '</tbody></table>'
          : '<blockquote class="quote">' + s.quote + '</blockquote>';
        return '<section class="stub src-stub' + (CS.hl === s.id ? ' is-hl' : '') + '" id="src-' + s.id + '" tabindex="-1"><div class="stub-main"><header class="stub-h">' + lbl('Src') + '<span class="src-title">' + s.title + '</span></header>' +
          '<p class="src-meta"><span class="mono">' + s.file + '</span> · ' + s.ver + '</p>' + body + (s.fact ? '<p class="fact">' + lbl('Fact') + '<span>' + s.fact + '</span></p>' : '') + '</div>' +
          '<div class="perf" aria-hidden="true"></div><div class="stub-tail src-tail">' + ic('check') + '<span>' + s.status + '</span></div></section>';
      }).join('');
    } else {
      ev = '<ol class="route tx">' + K.transcript.map(function (t) {
        var who = t.who === 'customer' ? 'Customer' : t.who === 'event' ? 'Event' : 'Meridian assistant · automated';
        return '<li class="stop stop-' + (t.who === 'customer' ? 'c' : t.who === 'event' ? 'evt' : 'a') + '"><span class="disc disc-' + (t.who === 'customer' ? 'c' : t.who === 'event' ? 'evt' : 'a') + '" aria-hidden="true"></span><header class="stop-h">' + lbl(who) + '<time>' + t.time + '</time></header><p>' + t.text + '</p></li>';
      }).join('') + '</ol>';
    }
    var evidence = '<aside class="evidence" aria-label="Evidence"><header class="col-h">' + lbl('Evidence') + '<p>What the AI saw, next to what is true now.</p></header>' + tabs + '<div id="ev-panel" role="tabpanel" aria-labelledby="tab-' + CS.tab + '" class="ev-p">' + ev + '</div></aside>';
    return '<div class="cs-grid">' + queue + brief + evidence + '</div>';
  }

  window.SKIN = {
    code: 'A2', name: 'Route sheet',
    other: { file: '2026-10-20-direction-A1-work-order.html', short: 'Switch to A1', name: 'A1 Work order' },
    chatShell: chatShell, caseShell: caseShell, item: item, panel: panel, stripSummary: stripSummary,
    staffing: staffing, banner: banner, assistantState: assistantState, safety: safety, inbox: inbox, caseView: caseView
  };
})();
