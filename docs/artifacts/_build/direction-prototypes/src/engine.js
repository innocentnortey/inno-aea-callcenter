/* Meridian direction-prototype engine. Shared by the direction files (A1-A3 embed an earlier copy; only A5 is current).
   It owns the scripted story, the state, routing (#step), events and the theme.
   It never writes markup for product parts: every part comes from window.SKIN. */
(function () {
  'use strict';
  var SK = window.SKIN;
  var mq = window.matchMedia('(prefers-reduced-motion: reduce)');
  function calm() { return mq.matches; }
  function $(s, r) { return (r || document).querySelector(s); }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* ---------- the eight steps ---------- */
  var STEPS = [
    { id: 'greeting', label: 'Greeting', screen: 'SCR-1' },
    { id: 'answer', label: 'Sourced answer', screen: 'SCR-1' },
    { id: 'booking', label: 'Book a repair visit', screen: 'SCR-1' },
    { id: 'code', label: 'One-time code and the bill', screen: 'SCR-1' },
    { id: 'handoff', label: 'Handoff, nobody online', screen: 'SCR-1' },
    { id: 'safety', label: 'Safety interrupt', screen: 'SCR-1' },
    { id: 'live', label: 'Live handoff (simulated staffing branch)', screen: 'SCR-1' },
    { id: 'case', label: 'Case view, staff console', screen: 'SCR-5 + SCR-6' }
  ];
  var PATHS = {
    greeting: ['greeting'],
    answer: ['greeting', 'answer'],
    booking: ['greeting', 'answer', 'booking'],
    code: ['greeting', 'answer', 'booking', 'code'],
    handoff: ['greeting', 'answer', 'booking', 'code', 'handoff'],
    safety: ['greeting', 'answer', 'booking', 'code', 'handoff', 'safety'],
    live: ['greeting', 'answer', 'booking', 'code', 'live']
  };
  var NEXT_STEP = { greeting: 'answer', answer: 'booking', booking: 'code', code: 'handoff', handoff: 'safety' };

  /* ---------- words (sources: KB files named in SRC, consolidated direction §4–§5, USER_FLOWS) ---------- */
  var TXT = {
    greet: "Hi, I'm Meridian Home Comfort's automated assistant, not a person. I can answer questions about our services, book a visit, and look up your account once you've confirmed it's you. If you'd like a person at any point, tap Talk to a person.",
    q1: 'How much is the Comfort Club, and what does it include?',
    a1: 'Comfort Club (Standard) is <b>$189 per year</b> per system, or <b>$16.99 per month</b>. It includes two seasonal tune-ups a year, priority scheduling, the $89 diagnostic fee waived on service calls, 15% off repairs, and no after-hours dispatch fee on emergency calls. Comfort Club Plus is <b>$269 per year</b> per system and adds a yearly water heater flush and inspection, a whole-home plumbing inspection, and 15% off plumbing repairs.',
    c2: 'My AC stopped cooling. Can someone come out?',
    whereAsk: 'Where is the visit? A ZIP code or city is enough.',
    pickedAsk: "Booking changes your account, so I need to confirm it's you before I write it. What name and phone number is the account under?",
    tierOk: "Thanks, you're verified for this chat. Your account isn't a Comfort Club membership, so the standard $89 diagnostic fee applies. I re-checked the window: it's still open.",
    checksIntro: "I can book a repair visit. First, these quick checks sometimes fix it. They're optional.",
    urgIntro: 'Two quick questions so we know how urgent this is. You can skip either one.',
    qa: 'Is it very hot in your home right now?',
    qb: 'Is anyone at higher risk, like an older person, a baby or someone unwell?',
    urgent: "Because someone may be in danger, please call Meridian's 24/7 emergency number now: <b>(512) 555-0199</b> (demo number). I've also logged this for our team as an emergency-priority request. No representative is online right now, so someone will review this online request within 1 business day. That is not the wait for emergency help; for that, please use the emergency line.",
    slotsIntro: '78640 is Kyle, in our south zone. Here are the open arrival windows for a repair visit. The technician arrives any time inside the window you pick.',
    slotsIntroUrgent: 'If you also want a regular visit, these are the earliest windows. This is a regular booking, not emergency service.',
    booked: "You're booked. Here are the details.",
    c4: 'Also, why is my bill $478?',
    codeAsk: "I've sent a 6-digit code to the phone number on your account, ending in 02. Please type it here.",
    already: "You're already verified in this chat, so I can show your bill. Here is invoice INV-204411, line by line.",
    lines: 'The diagnostic visit and the after-hours dispatch are fee types in our 2026 fee schedule. The contactor is the part that was replaced.',
    c5: 'The tech said it was $89 to come out. Nobody told me about an after-hours fee. I want that taken off.',
    cantChange: "I can't change or remove charges, but a person can review this with you.",
    talkAck: "Okay. I'll pass this to a person.",
    promise: 'No representative is online right now. A representative will get back to you within 1 business day, by Monday, October 19, 7:00 pm. Your reference is MHC-C-0007.',
    followAsk: "We'll follow up by email unless you'd prefer a phone call.",
    c6: 'Wait, the kitchen smells like rotten eggs.',
    safety1: 'Please leave the home immediately and call 911 or your gas utility from outside.',
    safety2: "Don't flip any light switches, open windows near the furnace, or restart any equipment.",
    quiet: "Once you're outside and safe, you can leave a number here if you'd like.",
    queued: 'A representative will join this chat when available. You can keep chatting with me while you wait, if you like.',
    staffBanner: 'Simulated staffing (demo). No Meridian employee is online.',
    joined: 'Riley (demo representative) has joined',
    paused: 'The assistant is paused while Riley is here.',
    riley: "Hi, I'm Riley. I've read your note about the after-hours fee, and I have the invoice open."
  };

  var SRC = {
    membership: { file: 'membership/comfort_club_overview.md', ver: 'eff. 2026-01-01', quote: 'Price: $189 per year per system, or $16.99 per month.', note: 'An undated older copy in archive/ says $149. It is not used.' },
    checks: { file: 'faq/troubleshooting_before_you_call.md', ver: 'Quick checks', quote: 'AC not cooling or blowing warm air: thermostat, filter, breaker, outdoor unit.' },
    fees: { file: 'pricing/2026_fee_schedule.pdf', ver: 'eff. Jan 1, 2026', quote: 'Diagnostic visit: $89 non-member; waived for Comfort Club and Plus. Late cancellation (<24h): $49.' },
    faq: { file: 'faq/customer_faq.md', ver: 'updated 2026-03-02', quote: 'Diagnostic fee: $89. Applied as credit toward the repair if you approve the repair during the same visit.' },
    invoice: { file: 'Invoice INV-204411', ver: 'scheduling record', quote: 'Issued 2026-10-02, due 2026-11-01, $478.00, balance $478.00.' }
  };

  var CHECKS = [
    'Confirm the thermostat is set to COOL and the set point is below room temperature.',
    'Check the air filter. A clogged filter is the #1 cause of weak airflow. Replace it if dirty.',
    'Check the breaker panel. Reset any tripped breaker once. If it trips again, stop and book a visit.',
    'Check the outdoor unit. If it is covered in debris or the fan is not spinning, book a visit.'
  ];

  /* Scheduling DB, zone south, service hvac_repair, Mon Oct 19 – Sat Oct 24 (slot rows 47…209). */
  var WIN = {
    '08:00-12:00': { label: '8 am – 12 pm', h24: '08:00 – 12:00', from: 8, to: 12 },
    '12:00-16:00': { label: '12 pm – 4 pm', h24: '12:00 – 16:00', from: 12, to: 16 },
    '13:00-17:00': { label: '1 pm – 5 pm', h24: '13:00 – 17:00', from: 13, to: 17 },
    '16:00-19:00': { label: '4 pm – 7 pm', h24: '16:00 – 19:00', from: 16, to: 19 }
  };
  var DAYS = [
    { key: '2026-10-19', dow: 'Mon', d: 19, long: 'Mon Oct 19', full: 'Monday, October 19', wins: [['08:00-12:00', 'taken'], ['12:00-16:00', 'taken']] },
    { key: '2026-10-20', dow: 'Tue', d: 20, long: 'Tue Oct 20', full: 'Tuesday, October 20', wins: [['08:00-12:00', 'taken'], ['13:00-17:00', 'taken']] },
    { key: '2026-10-21', dow: 'Wed', d: 21, long: 'Wed Oct 21', full: 'Wednesday, October 21', wins: [['08:00-12:00', 'open'], ['13:00-17:00', 'open']] },
    { key: '2026-10-22', dow: 'Thu', d: 22, long: 'Thu Oct 22', full: 'Thursday, October 22', wins: [['16:00-19:00', 'taken']] },
    { key: '2026-10-23', dow: 'Fri', d: 23, long: 'Fri Oct 23', full: 'Friday, October 23', wins: [['12:00-16:00', 'open']] },
    { key: '2026-10-24', dow: 'Sat', d: 24, long: 'Sat Oct 24', full: 'Saturday, October 24', wins: [['08:00-12:00', 'open']] }
  ];
  var TECH = 'Jun Park';
  var CODE = '482913';

  /* ---------- staff side (SCR-5 queue + SCR-6 case) ---------- */
  var QUEUE = [
    { ref: 'MHC-C-0008', p: 'P0', pword: 'Safety', reason: 'Gas smell reported in chat', who: 'Omar Patel', ini: 'OP', due: 'No due time: safety', due24: 'SAFETY', note: 'Instruction shown Fri 2:16 pm', owner: 'Unowned', band: 'safety' },
    { ref: 'MHC-C-0005', p: 'P3', pword: 'Standard', reason: 'Refund request', who: 'Linda Foster', ini: 'LF', due: 'Thu Oct 15, 7:00 pm', due24: 'THU 19:00', overdue: true, owner: 'Unowned' },
    { ref: 'MHC-C-0006', p: 'P3', pword: 'Standard', reason: 'Technician conduct complaint', who: 'Daniel Reyes', ini: 'DR', due: 'Mon Oct 19, 7:00 pm', due24: 'MON 19:00', owner: 'Unowned' },
    { ref: 'MHC-C-0007', p: 'P3', pword: 'Standard', reason: 'Billing dispute · INV-204411', who: 'Omar Patel', ini: 'OP', due: 'Mon Oct 19, 7:00 pm', due24: 'MON 19:00', owner: 'Unowned', follow: 'Phone · mornings' }
  ];
  var CASE = {
    ref: 'MHC-C-0007', title: 'Billing dispute: INV-204411', reason: 'Billing dispute', p: 'P3', pword: 'Standard',
    due: 'Mon Oct 19, 7:00 pm', due24: 'MON OCT 19 · 19:00', created: 'Fri Oct 16, 2:14 pm',
    promise: 'A representative will get back to you within 1 business day, by Monday, October 19, 7:00 pm.',
    follow: { channel: 'Phone, his choice (email is our default)', dest: 'The number on his record, ending 02', when: 'Mornings' },
    states: ['Unassigned', 'Claimed', 'In progress', 'Resolved'],
    sections: [
      { n: 1, h: 'Why this came to you', kind: 'fact', items: [{ t: 'The customer disputes a charge on his bill. Billing disputes go to a supervisor.', src: 'policy', tag: 'policy: escalation_and_safety.md' }] },
      { n: 2, h: 'What the customer needs', kind: 'quote', items: [{ t: '“Nobody told me about an after-hours fee. I want that taken off.”' }] },
      { n: 3, h: 'What we know for sure', kind: 'fact', items: [
        { t: 'Invoice INV-204411 is $478. Nothing is paid yet. Due Nov 1.', src: 'invoice', tag: 'invoice' },
        { t: 'The lines are: diagnostic visit $89, contactor $245, after-hours dispatch $144.', src: 'invoice', tag: 'invoice' },
        { t: 'Our fee schedule says after-hours dispatch is $149, not $144.', src: 'fees', tag: 'fee schedule, Jan 1 2026' },
        { t: 'Our FAQ says the $89 diagnostic is credited if the repair is approved at the same visit.', src: 'faq', tag: 'FAQ, Mar 2 2026' },
        { t: 'The invoice has no credit line. It does not say which visit it is for.', src: 'invoice', tag: 'invoice' }
      ] },
      { n: 4, h: 'What the customer says (not checked)', kind: 'claim', items: [{ t: 'The tech said it would be $89 to come out.' }, { t: 'Nobody told him about an after-hours fee.' }] },
      { n: 5, h: 'What the AI did', kind: 'plain', items: [{ t: 'Read the invoice and explained each line.' }, { t: 'Did not change, waive or promise anything about the bill.' }] },
      { n: 6, h: 'What we told the customer', kind: 'quote', items: [{ t: '“A representative will get back to you within 1 business day, by Monday, October 19, 7:00 pm.”' }] },
      { n: 7, h: 'What you need to decide', kind: 'decide', items: [{ t: 'Should the after-hours charge stay?' }, { t: 'Should the $89 diagnostic be credited?' }] },
      { n: 8, h: 'Who he is and how to reach him', kind: 'plain', items: [
        { t: 'Record MHC-10002, found by name and phone.' },
        { t: 'He entered the code sent to the phone on file. (Demo simulation. Not real ID proof.)' },
        { t: 'Follow up by: phone, his choice (email is our default). Number: the one on his record, ending 02. Best time: mornings.' }
      ] }
    ],
    sources: [
      { id: 'invoice', title: 'Invoice INV-204411', file: 'scheduling DB · invoices', ver: 'Snapshot read Fri Oct 16, 2:10 pm',
        rows: [['Amount', '$478.00', '$478.00'], ['Balance', '$478.00 (unpaid)', '$478.00 (unpaid)'], ['Due', 'Nov 1, 2026', 'Nov 1, 2026'], ['Diagnostic visit', '$89.00', '$89.00'], ['Contactor replacement', '$245.00', '$245.00'], ['After-hours dispatch', '$144.00', '$144.00']],
        status: 'No change since the snapshot.' },
      { id: 'fees', title: '2026 fee schedule', file: 'pricing/2026_fee_schedule.pdf', ver: 'Effective January 1, 2026. Supersedes all prior fee schedules.',
        quote: 'After-hours emergency dispatch: Non-member $149 · Comfort Club Waived · Comfort Club Plus Waived',
        fact: 'Schedule: $149. Invoice line: $144.', status: 'Snapshot and current passage match.' },
      { id: 'faq', title: 'Customer FAQ: Fees', file: 'faq/customer_faq.md', ver: 'Last updated 2026-03-02',
        quote: 'Diagnostic fee: $89. Applied as credit toward the repair if you approve the repair during the same visit.',
        fact: 'The invoice bills the $89 next to a repair, with no credit line.', status: 'Snapshot and current passage match.' },
      { id: 'policy', title: 'Escalation & safety protocol', file: 'policies/escalation_and_safety.md', ver: 'Rev 2026-01',
        quote: 'Supervisor escalation (callback within 1 business day): Billing disputes where the customer disagrees with an invoice amount.',
        status: 'Snapshot and current passage match.' }
    ],
    transcript: [
      ['assistant', '2:02 pm', 'greet'], ['customer', '2:05 pm', 'c2'], ['assistant', '2:07 pm', 'pickedAsk'], ['assistant', '2:07 pm', 'codeAsk'],
      ['event', '2:08 pm', 'Code entered. Verified for this chat.'], ['assistant', '2:08 pm', 'Booked: Wed Oct 21, 8 am – 12 pm, Jun Park, $89 diagnostic visit.'],
      ['customer', '2:10 pm', 'c4'], ['assistant', '2:10 pm', 'already'],
      ['assistant', '2:10 pm', 'Invoice INV-204411: Diagnostic visit $89.00 · Contactor replacement $245.00 · After-hours dispatch $144.00 · Total $478.00'],
      ['customer', '2:13 pm', 'c5'], ['assistant', '2:14 pm', 'cantChange'], ['assistant', '2:14 pm', 'promise'],
      ['assistant', '2:14 pm', 'followAsk'], ['customer', '2:15 pm', 'Phone call, mornings'],
      ['event', '2:15 pm', 'Follow-up preference saved: phone, mornings.']
    ]
  };
  CASE.transcript = CASE.transcript.map(function (r) { return { who: r[0], time: r[1], text: TXT[r[2]] || r[2] }; });

  /* ---------- state ---------- */
  var S, CS, gen = 0, seq = 0, waiters = {};
  function freshState() {
    return { step: 'greeting', view: 'chat', items: [], cards: {}, cardItem: {}, fast: false,
      staffing: 'none', live: null, visit: null, request: null, identity: null, safety: false,
      next: '', hl: null, busy: false, pendingLine: null };
  }
  function freshCase() {
    return { sel: 'MHC-C-0007', tab: 'sources', claimed: false, callOpen: false, flagOpen: false, flagged: null, hl: null,
      acts: [{ time: 'Fri 2:14 pm', text: 'Case created by the assistant. Unassigned.' }, { time: 'Fri 2:15 pm', text: 'Follow-up preference saved: phone, mornings.' }] };
  }
  var ctx = { TXT: TXT, SRC: SRC, CHECKS: CHECKS, DAYS: DAYS, WIN: WIN, TECH: TECH, CASE: CASE, QUEUE: QUEUE, esc: esc };

  function Stop() {}
  function pause(ms, g) {
    if (S.fast || calm()) { if (g !== gen) throw new Stop(); return Promise.resolve(); }
    return new Promise(function (r) { setTimeout(r, ms); }).then(function () { if (g !== gen) throw new Stop(); });
  }
  function turn(who, time, html, extra) {
    var t = { kind: 'turn', who: who, time: time, html: html };
    if (extra) for (var k in extra) t[k] = extra[k];
    return t;
  }
  function event(time, text, icon) { return { kind: 'event', time: time, html: text, icon: icon || 'info' }; }
  function say(item) {
    item.id = 'it' + (++seq);
    if (item.card) S.cardItem[item.card.key] = item.id;
    S.items.push(item);
    var thread = $('#thread');
    if (thread) {
      var wrap = document.createElement('div');
      wrap.innerHTML = SK.item(item, S, ctx);
      var el = wrap.firstElementChild;
      el.id = item.id;
      if (!S.fast && !calm()) el.classList.add('is-arriving');
      thread.appendChild(el);
      if (!S.fast) scrollThread();
    }
    return item;
  }
  function scrollThread() {
    var t = $('#thread');
    if (!t) return;
    t.scrollTo({ top: t.scrollHeight, behavior: calm() ? 'auto' : 'smooth' });
  }
  function refreshCard(key) {
    var id = S.cardItem[key];
    if (!id) return;
    var item = null;
    for (var i = 0; i < S.items.length; i++) if (S.items[i].id === id) item = S.items[i];
    var old = document.getElementById(id);
    if (!item || !old) return;
    var fk = document.activeElement && document.activeElement.getAttribute('data-fk');
    var wrap = document.createElement('div');
    wrap.innerHTML = SK.item(item, S, ctx);
    var el = wrap.firstElementChild;
    el.id = id;
    old.replaceWith(el);
    if (fk) { var f = el.querySelector('[data-fk="' + fk + '"]'); if (f && !f.disabled) f.focus(); }
  }

  var DEFAULTS = {
    checks: function () { return 'skip'; },
    qa: function () { return 'no'; },
    qb: function () { return 'no'; },
    where: function () { S.cards.where = { value: '78640' }; return 'ok'; },
    slots: function () { S.cards.slots = { day: '2026-10-21', win: '08:00-12:00' }; return 'pick'; },
    code: function () { S.cards.code = { stage: 'sent', name: 'Omar Patel', phone: '512-555-0102', value: CODE, attempts: 0 }; S.identity = 'sent'; return 'ok'; },
    follow: function () { S.cards.follow = { channel: 'phone', when: 'mornings' }; return 'save'; },
    join: function () { return 'join'; }
  };
  var ECHO = {
    checks: function (v) { return v === 'skip' ? 'Skip the checks' : "I tried them. It's still not cooling."; },
    qa: function (v) { return { yes: 'Yes', no: 'No', skip: 'Skip' }[v]; },
    qb: function (v) { return { yes: 'Yes', no: 'No', skip: 'Skip' }[v]; },
    where: function () { return S.cards.where.value; },
    slots: function () { var c = S.cards.slots; return dayOf(c.day).long + ', ' + WIN[c.win].label + ', please.'; },
    follow: function () { var c = S.cards.follow; return c.channel === 'email' ? 'Email is fine' : 'Phone call, ' + c.when; }
  };
  var ECHO_TIME = { checks: '2:06 pm', qa: '2:06 pm', qb: '2:06 pm', where: '2:06 pm', slots: '2:07 pm', follow: '2:15 pm' };
  function dayOf(k) { for (var i = 0; i < DAYS.length; i++) if (DAYS[i].key === k) return DAYS[i]; return null; }

  function ask(key, g) {
    var p;
    if (S.fast) p = Promise.resolve(DEFAULTS[key]());
    else { S.busy = true; updateComposer(); p = new Promise(function (r) { waiters[key] = r; }); }
    return p.then(function (v) {
      if (g !== gen) throw new Stop();
      S.busy = false;
      updateComposer();
      S.cards[key] = Object.assign(S.cards[key] || {}, { done: true, choice: v });
      refreshCard(key);
      if (ECHO[key]) say(turn('customer', ECHO_TIME[key], esc(ECHO[key](v))));
      return v;
    });
  }
  function resolve(key, v) { var w = waiters[key]; if (w) { delete waiters[key]; w(v); } }

  function firstLine(dflt) { var l = S.pendingLine; S.pendingLine = null; return l ? esc(l) : dflt; }

  /* ---------- pending-turn demo (SCREEN_SPECS SCR-1 loading): line after 0.3 s, "still working" after 10 s ---------- */
  var slowMode = false, pendingCancel = null;
  var PENDING = { line: 300, still: 10000, reply: 13000 };
  function rerender(it) {
    var old = document.getElementById(it.id);
    if (!old) return;
    var wrap = document.createElement('div');
    wrap.innerHTML = SK.item(it, S, ctx);
    var el = wrap.firstElementChild;
    el.id = it.id;
    old.replaceWith(el);
  }
  function drop(it) {
    var i = S.items.indexOf(it);
    if (i >= 0) S.items.splice(i, 1);
    var el = document.getElementById(it.id);
    if (el) el.remove();
  }
  function thinking(g) {
    if (!slowMode || S.fast || !SK.pending) return Promise.resolve();
    return new Promise(function (done) {
      var it = null, t1, t2, t3;
      function finish() {
        clearTimeout(t1); clearTimeout(t2); clearTimeout(t3);
        pendingCancel = null;
        if (it) drop(it);
        done();
      }
      pendingCancel = finish;
      t1 = setTimeout(function () { if (g !== gen) { finish(); return; } it = say({ kind: 'pending', stage: 1 }); }, PENDING.line);
      t2 = setTimeout(function () { if (g !== gen) { finish(); return; } if (it) { it.stage = 2; rerender(it); } }, PENDING.still);
      t3 = setTimeout(finish, PENDING.reply);
    }).then(function () { if (g !== gen) throw new Stop(); });
  }

  /* ---------- the story ---------- */
  var RUN = {
    greeting: function (g) {
      say(turn('assistant', '2:02 pm', TXT.greet));
      return Promise.resolve();
    },
    answer: function (g) {
      say(turn('customer', '2:03 pm', firstLine(TXT.q1)));
      return pause(450, g).then(function () { return thinking(g); }).then(function () {
        say(turn('assistant', '2:03 pm', TXT.a1, { sources: ['membership'] }));
      });
    },
    booking: function (g) {
      say(turn('customer', '2:05 pm', firstLine(TXT.c2)));
      return pause(450, g).then(function () { return thinking(g); }).then(function () {
        say(turn('assistant', '2:05 pm', TXT.checksIntro, { card: { type: 'checks', key: 'checks' }, sources: ['checks'] }));
        return ask('checks', g);
      }).then(function () { return pause(350, g); }).then(function () {
        say(turn('assistant', '2:06 pm', TXT.urgIntro, { card: { type: 'question', key: 'qa', q: TXT.qa, n: 1 } }));
        return ask('qa', g);
      }).then(function () { return pause(300, g); }).then(function () {
        say(turn('assistant', '2:06 pm', '', { card: { type: 'question', key: 'qb', q: TXT.qb, n: 2 } }));
        return ask('qb', g);
      }).then(function (b) {
        return pause(350, g).then(function () {
          if (b === 'yes') say(turn('assistant', '2:06 pm', TXT.urgent));
          S.cards.where = S.cards.where || { value: '78640' };
          say(turn('assistant', '2:06 pm', TXT.whereAsk, { card: { type: 'where', key: 'where' } }));
          return ask('where', g);
        });
      }).then(function () { return pause(400, g); }).then(function () {
        S.cards.slots = S.cards.slots || { day: '2026-10-21', win: null };
        say(turn('assistant', '2:07 pm', S.cards.qb && S.cards.qb.choice === 'yes' ? TXT.slotsIntroUrgent : TXT.slotsIntro, { card: { type: 'slots', key: 'slots' }, sources: ['fees', 'faq'] }));
        return ask('slots', g);
      }).then(function () { return pause(450, g); }).then(function () {
        S.cards.code = S.cards.code || { stage: 'locate', name: 'Omar Patel', phone: '512-555-0102', value: '', attempts: 0 };
        say(turn('assistant', '2:07 pm', TXT.pickedAsk, { card: { type: 'code', key: 'code' } }));
        return ask('code', g);
      }).then(function () { return pause(400, g); }).then(function () {
        S.identity = 'verified';
        land('identity');
        var c = S.cards.slots, d = dayOf(c.day), w = WIN[c.win];
        S.visit = { day: d, win: w, winKey: c.win, tech: TECH, fee: '$89 diagnostic visit', feeNote: 'Credited toward the repair if you approve it at the same visit.',
          freeUntil: freeUntil(d, w), bookedAt: 'Fri Oct 16, 2:08 pm' };
        say(turn('assistant', '2:08 pm', TXT.tierOk + ' ' + TXT.booked, { card: { type: 'confirm', key: 'confirm' }, sources: ['fees', 'faq'] }));
        land('visit');
      });
    },
    code: function (g) {
      say(turn('customer', '2:10 pm', firstLine(TXT.c4)));
      return pause(450, g).then(function () { return thinking(g); }).then(function () {
        say(turn('assistant', '2:10 pm', TXT.already, { card: { type: 'account', key: 'account' }, after: TXT.lines, sources: ['invoice', 'fees'] }));
      });
    },
    handoff: function (g, opt) {
      var byButton = opt && opt.trigger === 'button';
      say(turn('customer', '2:13 pm', byButton ? 'Talk to a person' : firstLine(TXT.c5), byButton ? { viaButton: true } : null));
      return pause(500, g).then(function () { return byButton ? null : thinking(g); }).then(function () {
        S.request = { ref: 'MHC-C-0007', promise: TXT.promise, nowAt: 'Fri Oct 16, 2:14 pm', due: 'Mon Oct 19, 7:00 pm', dueLong: 'Monday, October 19, 7:00 pm', due24: 'MON OCT 19 · 19:00', follow: null };
        S.cards.follow = S.cards.follow || { channel: 'email', when: 'mornings' };
        say(turn('assistant', '2:14 pm', byButton ? TXT.talkAck : TXT.cantChange, { card: { type: 'handoff', key: 'follow' } }));
        land('request');
        return ask('follow', g);
      }).then(function () { return pause(400, g); }).then(function () {
        var c = S.cards.follow;
        applyFollow();
        land('request');
        var msg = c.channel === 'email'
          ? 'Saved: a representative will follow up by email, at the address on your account. You can keep asking me other questions while this is open.'
          : 'Saved: a representative will follow up by phone, at the number ending in 02, ' + (c.when === 'any' ? 'any time' : 'in the ' + (c.when === 'mornings' ? 'morning' : 'afternoon')) + '. You can keep asking me other questions while this is open.';
        say(turn('assistant', '2:15 pm', msg));
      });
    },
    safety: function (g) {
      say(turn('customer', '2:16 pm', firstLine(TXT.c6)));
      S.safety = true;
      renderPinned();
      renderPanel();
      say(turn('assistant', '2:16 pm', TXT.quiet, { quiet: true }));
      var pin = $('#pinned');
      if (pin && !S.fast) pin.scrollIntoView({ block: 'nearest' });
      return Promise.resolve();
    },
    live: function (g, opt) {
      var byButton = opt && opt.trigger === 'button';
      say(turn('customer', '2:13 pm', byButton ? 'Talk to a person' : firstLine(TXT.c5), byButton ? { viaButton: true } : null));
      return pause(500, g).then(function () { return byButton ? null : thinking(g); }).then(function () {
        S.live = 'queued';
        S.request = { ref: 'MHC-C-0007', live: true };
        say(turn('assistant', '2:14 pm', byButton ? TXT.talkAck : TXT.cantChange, { card: { type: 'queued', key: 'join' } }));
        land('request');
        renderChrome();
        return ask('join', g);
      }).then(function () { return pause(300, g); }).then(function () {
        S.live = 'joined';
        say(event('2:17 pm', TXT.joined, 'person'));
        say(event('2:17 pm', TXT.paused, 'pause'));
        renderChrome();
        land('control');
        return pause(700, g);
      }).then(function () {
        say(turn('rep', '2:17 pm', TXT.riley));
      });
    }
  };

  function applyFollow() {
    var c = S.cards.follow;
    if (!S.request || !c) return;
    S.request.follow = c.channel === 'email' ? { channel: 'Email', dest: 'the email on your account', when: '' } : { channel: 'Phone call', dest: 'the number ending in 02', when: { mornings: 'Mornings', afternoons: 'Afternoons', any: 'Any time' }[c.when] };
  }
  function freeUntil(d, w) {
    /* FAQ: changes more than 24 hours before the window are free. */
    var prev = DAYS[DAYS.indexOf(d) - 1];
    var hh = w.from > 12 ? (w.from - 12) + ':00 pm' : w.from + ':00 ' + (w.from === 12 ? 'pm' : 'am');
    return (prev ? prev.long : 'Sun Oct 18') + ', ' + hh;
  }

  function land(block) {
    S.hl = block;
    renderPanel();
    if (!S.fast && !calm()) setTimeout(function () { if (S.hl === block) { S.hl = null; var hl = document.querySelectorAll('.is-hl'); for (var i = 0; i < hl.length; i++) hl[i].classList.remove('is-hl'); } }, 1600);
    else S.hl = null;
  }

  /* ---------- rendering ---------- */
  function renderPanel() {
    var p = $('#panel'), sb = $('#strip-body'), ss = $('#strip-summary');
    if (p) p.innerHTML = SK.panel(S, ctx);
    if (sb) sb.innerHTML = SK.panel(S, ctx, 'strip');
    if (ss) ss.innerHTML = SK.stripSummary(S, ctx);
    var strip = $('#strip');
    if (strip) strip.classList.toggle('is-safety', !!S.safety);
    var ast = $('#assistant-state'); if (ast) ast.innerHTML = SK.assistantState(S, ctx);
  }
  function renderPinned() {
    var p = $('#pinned');
    if (!p) return;
    p.innerHTML = S.safety ? SK.safety(ctx) : '';
    p.hidden = !S.safety;
    var app = $('#app'); if (app) { if (S.safety) app.setAttribute('data-safety', ''); else app.removeAttribute('data-safety'); }
  }
  function renderChrome() {
    var st = $('#staffing'); if (st) st.innerHTML = SK.staffing(S, ctx);
    var b = $('#banner'); if (b) { b.innerHTML = SK.banner(S, ctx); b.hidden = !b.innerHTML; }
    var a = $('#assistant-state'); if (a) a.innerHTML = SK.assistantState(S, ctx);
    var app = $('#app'); if (app) app.setAttribute('data-staffing', S.staffing);
    updateComposer();
  }
  function updateComposer() {
    var inp = $('#composer-input'), hint = $('#composer-hint');
    if (!inp) return;
    inp.value = S.next || '';
    inp.placeholder = S.live === 'joined' ? 'Message Riley (demo)' : 'Type a message';
    if (hint) hint.textContent = S.next ? 'Scripted demo: the next message is filled in. Press Send.' : (S.live === 'queued' ? 'Demo: play the representative from the banner above.' : S.busy ? 'Use the card above to continue.' : '');
  }

  function mountChat() {
    var app = $('#app');
    app.setAttribute('data-view', 'chat');
    app.innerHTML = SK.chatShell(ctx);
    renderChrome();
    renderPanel();
    renderPinned();
  }
  function mountCase() {
    var app = $('#app');
    app.setAttribute('data-view', 'case');
    app.innerHTML = SK.caseShell(ctx);
    renderCase();
  }
  function renderCase(focusKey) {
    var root = $('#case-root');
    if (!root) return;
    var fk = focusKey || (document.activeElement && document.activeElement.getAttribute('data-fk'));
    root.innerHTML = SK.caseView(CS, ctx);
    if (fk) { var f = root.querySelector('[data-fk="' + fk + '"]'); if (f) f.focus(); }
  }

  /* ---------- routing ---------- */
  function goTo(id) {
    if (!PATHS[id] && id !== 'case') id = 'greeting';
    gen++; var g = gen; waiters = {};
    if (pendingCancel) pendingCancel();
    S = freshState(); S.step = id;
    syncProto(id);
    if (id === 'case') { S.view = 'case'; CS = freshCase(); mountCase(); window.scrollTo(0, 0); return; }
    if (id === 'live') S.staffing = 'sim';
    mountChat();
    var path = PATHS[id], before = path.slice(0, -1);
    S.fast = true;
    var chain = Promise.resolve();
    before.forEach(function (s) { chain = chain.then(function () { return RUN[s](g); }); });
    chain.then(function () {
      if (g !== gen) throw new Stop();
      S.fast = false;
      scrollThreadNow();
      return pause(250, g);
    }).then(function () { return RUN[id](g); })
      .then(function () { if (g !== gen) return; S.next = nextLine(id); updateComposer(); })
      .catch(function (e) { if (!(e instanceof Stop)) throw e; });
  }
  function scrollThreadNow() { var t = $('#thread'); if (t) t.scrollTop = t.scrollHeight; }
  function nextLine(id) {
    var n = NEXT_STEP[id];
    if (S.safety || !n) return '';
    if (n === 'handoff' && S.request) return '';
    return { answer: TXT.q1, booking: TXT.c2, code: TXT.c4, handoff: TXT.c5, safety: TXT.c6 }[n] || '';
  }
  function setHash(id) {
    S.step = id;
    try { history.replaceState(null, '', '#' + id); } catch (e) { /* file:// may refuse; ignore */ }
    syncProto(id);
  }
  function advance(text) {
    var n = NEXT_STEP[S.step];
    if (!n || !S.next) {
      if (text) {
        say(turn('customer', 'now', esc(text)));
        say(event('now', 'Prototype: replies follow the script. Use the card above, Talk to a person, or Jump to.', 'info'));
      }
      return;
    }
    var g = gen;
    S.pendingLine = text && text !== S.next ? text : null;
    S.next = ''; updateComposer();
    setHash(n);
    RUN[n](g).then(function () { if (g !== gen) return; S.next = nextLine(n); updateComposer(); })
      .catch(function (e) { if (!(e instanceof Stop)) throw e; });
  }
  function talk() {
    if (S.view === 'case') return;
    if (S.request) { land('request'); var strip = $('#strip'); if (strip) strip.open = true; toast('Your request ' + S.request.ref + ' is open. It is in “What’s settled”.'); return; }
    gen++; var g = gen; waiters = {}; S.busy = false; S.next = '';
    if (pendingCancel) pendingCancel();
    var target = S.staffing === 'sim' ? 'live' : 'handoff';
    setHash(target);
    updateComposer();
    RUN[target](g, { trigger: 'button' }).then(function () { if (g !== gen) return; S.next = nextLine(target); updateComposer(); })
      .catch(function (e) { if (!(e instanceof Stop)) throw e; });
  }

  /* ---------- prototype bar (identical in every direction file) ---------- */
  var DIRS = [
    { code: 'A5', name: 'A5 Service desk', file: '2026-10-21-direction-A5-service-desk.html' }
  ];
  function protoBar() {
    var links = STEPS.map(function (s, i) {
      return '<li><a href="#' + s.id + '" data-step="' + s.id + '"><span class="pj-n">' + (i + 1) + '</span><span class="pj-l">' + esc(s.label) + '</span><span class="pj-s">' + s.screen + '</span></a></li>';
    }).join('');
    return '<div class="proto-bar" role="region" aria-label="Prototype controls">' +
      '<span class="pb-name"><b>' + esc(SK.code) + '</b> <span class="pb-long">' + esc(SK.name) + ' · direction prototype</span></span>' +
      '<span class="pb-tools">' +
      '<button type="button" class="pb-btn" popovertarget="jump-menu" id="jump-btn" aria-haspopup="true">Jump to</button>' +
      '<button type="button" class="pb-btn" id="slow-btn" data-act="slow" aria-pressed="false" title="Demo: hold the assistant’s next replies back so the waiting lines show.">Slow reply</button>' +
      DIRS.filter(function (d) { return d.code !== SK.code; }).map(function (d) {
        return '<a class="pb-btn switch-link" data-file="' + d.file + '" href="' + d.file + '#greeting" aria-label="Switch to ' + esc(d.name) + ' at this step">' + d.code + '</a>';
      }).join('') +
      '<button type="button" class="pb-btn" id="theme-btn" data-act="theme">Dark</button>' +
      '</span>' +
      '<nav id="jump-menu" popover aria-label="Jump to a step"><p class="pj-h">Scripted story · 8 steps</p><ol>' + links + '</ol>' +
      '<p class="pj-f">Synthetic demo data. Nothing is sent or booked.</p></nav>' +
      '</div>';
  }
  function syncProto(id) {
    var sws = document.querySelectorAll('.switch-link');
    for (var k = 0; k < sws.length; k++) sws[k].href = sws[k].getAttribute('data-file') + '#' + id;
    var as = document.querySelectorAll('#jump-menu a');
    for (var i = 0; i < as.length; i++) {
      if (as[i].getAttribute('data-step') === id) as[i].setAttribute('aria-current', 'step'); else as[i].removeAttribute('aria-current');
    }
  }

  /* ---------- theme ---------- */
  var dmq = window.matchMedia('(prefers-color-scheme: dark)');
  function effectiveTheme() { var t = document.documentElement.getAttribute('data-theme'); return t || (dmq.matches ? 'dark' : 'light'); }
  function syncThemeBtn() { var b = $('#theme-btn'); if (b) { var dark = effectiveTheme() === 'dark'; b.textContent = dark ? 'Light' : 'Dark'; b.setAttribute('aria-label', dark ? 'Switch to light theme' : 'Switch to dark theme'); } }
  function toggleTheme() {
    var next = effectiveTheme() === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('mhc-proto-theme', next); } catch (e) { /* storage may be blocked */ }
    syncThemeBtn();
  }
  try { var saved = localStorage.getItem('mhc-proto-theme'); if (saved && !document.documentElement.getAttribute('data-theme')) document.documentElement.setAttribute('data-theme', saved); } catch (e) { /* ignore */ }

  /* ---------- toast ---------- */
  var toastTimer;
  function toast(msg) {
    var t = $('#toast'); if (!t) return;
    t.textContent = msg; t.classList.add('is-on');
    clearTimeout(toastTimer); toastTimer = setTimeout(function () { t.classList.remove('is-on'); }, 3200);
  }

  /* ---------- events ---------- */
  document.addEventListener('click', function (e) {
    var a = e.target.closest('[data-act]');
    var jl = e.target.closest('#jump-menu a');
    if (jl) { var m = $('#jump-menu'); if (m && m.hidePopover) { try { m.hidePopover(); } catch (x) { /* closed */ } } }
    if (!a) return;
    var act = a.getAttribute('data-act'), key = a.getAttribute('data-key'), val = a.getAttribute('data-val');
    switch (act) {
      case 'theme': toggleTheme(); break;
      case 'slow': slowMode = !slowMode; a.setAttribute('aria-pressed', slowMode ? 'true' : 'false');
        toast(slowMode ? 'Slow reply is on. The next replies wait about 13 seconds: a replying line first, “Still working on this…” after 10 seconds.' : 'Slow reply is off.');
        if (!slowMode && pendingCancel) pendingCancel();
        break;
      case 'talk': talk(); break;
      case 'choose': if (waiters[key]) resolve(key, val); break;
      case 'slot-day': S.cards.slots.day = val; S.cards.slots.win = null; S.cards.slots.err = ''; refreshCard('slots'); break;
      case 'slot-win': if (a.getAttribute('data-day')) S.cards.slots.day = a.getAttribute('data-day'); S.cards.slots.win = val; S.cards.slots.err = ''; refreshCard('slots'); break;
      case 'slot-book':
        if (!S.cards.slots.win) { S.cards.slots.err = 'Pick an arrival window first.'; refreshCard('slots'); break; }
        resolve('slots', 'pick'); break;
      case 'inbox': e.preventDefault(); openInbox(); break;
      case 'inbox-use': S.cards.code.value = CODE; S.cards.code.err = ''; closeInbox(); refreshCard('code'); var ci = $('#code-input'); if (ci) ci.focus(); break;
      case 'inbox-close': closeInbox(); break;
      case 'follow-ch': S.cards.follow.channel = val; refreshCard('follow'); break;
      case 'follow-when': S.cards.follow.when = val; refreshCard('follow'); break;
      case 'follow-save':
        if (waiters.follow) { resolve('follow', 'save'); break; }
        if (S.cards.follow) { S.cards.follow.done = true; applyFollow(); refreshCard('follow'); land('request'); toast('Follow-up choice updated.'); }
        break;
      case 'follow-change': if (S.cards.follow) { S.cards.follow.done = false; refreshCard('follow'); } break;
      case 'demo-join': if (waiters.join) resolve('join', 'join'); break;
      case 'stub': toast(a.getAttribute('data-msg') || 'Not part of this direction prototype.'); break;
      case 'case-select': CS.sel = val; CS.callOpen = CS.flagOpen = false; renderCase('q-' + val); break;
      case 'case-tab': CS.tab = val; renderCase('tab-' + val); break;
      case 'src-jump': CS.tab = 'sources'; CS.hl = val; renderCase(); var s = document.getElementById('src-' + val); if (s) { s.scrollIntoView({ block: 'nearest', behavior: calm() ? 'auto' : 'smooth' }); s.focus({ preventScroll: true }); }
        if (!calm()) setTimeout(function () { if (CS.hl === val) { CS.hl = null; var x = document.getElementById('src-' + val); if (x) x.classList.remove('is-hl'); } }, 1800); else CS.hl = null;
        break;
      case 'case-claim': CS.claimed = true; CS.acts.push({ time: 'Fri 2:20 pm', text: 'Claimed by Riley (demo representative).' }); renderCase('act-call'); break;
      case 'case-call': CS.callOpen = !CS.callOpen; CS.flagOpen = false; renderCase(CS.callOpen ? 'call-outcome' : 'act-call'); break;
      case 'case-flag': CS.flagOpen = !CS.flagOpen; CS.callOpen = false; renderCase(CS.flagOpen ? 'flag-reason' : 'act-flag'); break;
      case 'case-join': toast('Join chat works only while the customer is in a live chat.'); break;
    }
  });
  document.addEventListener('input', function (e) {
    if (e.target.id === 'code-input' && S.cards.code) { S.cards.code.value = e.target.value.replace(/\D/g, '').slice(0, 6); }
    var bind = e.target.getAttribute && e.target.getAttribute('data-bind');
    if (bind) { var bp = bind.split('.'); if (S.cards[bp[0]]) S.cards[bp[0]][bp[1]] = e.target.value; }
  });
  document.addEventListener('submit', function (e) {
    var f = e.target, kind = f.getAttribute('data-form');
    if (!kind) return;
    e.preventDefault();
    if (kind === 'composer') { var v = ($('#composer-input').value || '').trim(); advance(v); return; }
    if (kind === 'where') {
      var wv = (S.cards.where.value || '').trim();
      if (!/^(78640|kyle)\b/i.test(wv)) { S.cards.where.err = 'This scripted demo covers Kyle (78640). Try that ZIP.'; refreshCard('where'); var wi = $('#where-input'); if (wi) wi.focus(); return; }
      S.cards.where.err = ''; resolve('where', 'ok'); return;
    }
    if (kind === 'locate') {
      var lc = S.cards.code;
      if (!(lc.name || '').trim() || !(lc.phone || '').trim()) { lc.err = 'Enter the name and phone on the account.'; refreshCard('code'); return; }
      lc.err = ''; lc.stage = 'sent'; S.identity = 'sent'; land('identity'); refreshCard('code');
      var cin = $('#code-input'); if (cin) cin.focus();
      return;
    }
    if (kind === 'code') {
      var c = S.cards.code;
      if (c.done) return;
      if (c.value === CODE) { c.err = ''; resolve('code', 'ok'); return; }
      c.attempts = (c.attempts || 0) + 1;
      c.err = c.attempts >= 3 ? 'No tries left. In the product this goes to a person, and nothing about the account is shown (FLOW-3).'
        : (c.value.length !== 6 ? 'Enter all 6 digits.' : "That code doesn't match. " + (3 - c.attempts) + (3 - c.attempts === 1 ? ' try' : ' tries') + ' left.');
      refreshCard('code');
      var ci = $('#code-input'); if (ci) ci.focus();
      return;
    }
    if (kind === 'call') {
      var out = f.querySelector('[name=outcome]:checked');
      CS.acts.push({ time: 'Fri 2:22 pm', text: 'Call logged: ' + (out ? out.value : 'No answer') + '. Demo: recorded, not sent.' });
      CS.callOpen = false; renderCase('act-call'); return;
    }
    if (kind === 'flag') {
      var r = f.querySelector('select'); CS.flagged = r ? r.value : 'Other';
      CS.acts.push({ time: 'Fri 2:23 pm', text: 'Flagged for review: ' + CS.flagged + '.' });
      CS.flagOpen = false; renderCase('act-flag'); return;
    }
  });
  document.addEventListener('keydown', function (e) {
    var appEl = $('#app');
    if (appEl && appEl.getAttribute('data-view') === 'case') {
      var row = e.target.closest && e.target.closest('[data-queue] [data-ref]');
      if (!row) return;
      var rows = Array.prototype.slice.call(document.querySelectorAll('[data-queue] [data-ref]'));
      var i = rows.indexOf(row);
      if (e.key === 'j' || e.key === 'ArrowDown') { e.preventDefault(); if (rows[i + 1]) rows[i + 1].focus(); }
      if (e.key === 'k' || e.key === 'ArrowUp') { e.preventDefault(); if (rows[i - 1]) rows[i - 1].focus(); }
    }
  });

  /* demo inbox (stub of SCR-2) */
  function openInbox() {
    var d = $('#inbox');
    if (!d) { document.body.insertAdjacentHTML('beforeend', SK.inbox(ctx)); d = $('#inbox'); }
    if (d.showModal) d.showModal(); else d.setAttribute('open', '');
  }
  function closeInbox() { var d = $('#inbox'); if (d && d.close) d.close(); }

  /* ---------- boot ---------- */
  function boot() {
    document.body.insertAdjacentHTML('afterbegin', protoBar());
    if (!$('#app')) document.body.insertAdjacentHTML('beforeend', '<div id="app"></div>');
    if (!$('#toast')) document.body.insertAdjacentHTML('beforeend', '<div id="toast" role="status" aria-live="polite"></div>');
    syncThemeBtn();
    dmq.addEventListener && dmq.addEventListener('change', syncThemeBtn);
    window.addEventListener('hashchange', function () { goTo(location.hash.slice(1)); });
    goTo(location.hash.slice(1) || 'greeting');
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
