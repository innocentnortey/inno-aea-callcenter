import sys; sys.path.insert(0,'/Users/innocentnortey/.claude/jobs/0d72ed71/tmp')
from a5common import *
P = 'document.getElementById("panel").innerText.replace(/\\s+/g," ").slice(0,200)'
def flow(url, slow=False):
    w = ('wait', 900 if slow else 250); send = ('click', 'button.send')
    return {'url': url + '#greeting', 'w': 1280, 'h': 800, 'shot': None, 'actions': [
      send, ('wait', 1500 if slow else 250), send, ('wait', 1500 if slow else 250),
      ('click', '[data-key=checks][data-val=skip]'), w, ('click', '[data-key=qa][data-val=no]'), w, ('click', '[data-key=qb][data-val=skip]'), w,
      ('click', 'form[data-form=where] button'), ('wait', 400),
      ('click', '[data-act=slot-book]'), w, ('check', '"no-window error: " + (document.querySelector(".err") || {}).textContent'),
      ('eval', 'var d=document.querySelector("[data-act=slot-day][data-val=\\"2026-10-23\\"]"); if (d) d.click()'), w,
      ('click', '[data-act=slot-win][data-val="12:00-16:00"]'), w, ('check','document.querySelector(".win.is-sel").innerText'), ('click', '[data-act=slot-book]'), ('wait', 400),
      ('click', 'form[data-form=locate] button'), w,
      ('check', '"resend present: " + !!document.querySelector("[data-fk=resend]")'),
      ('click', '[data-fk=resend]'), w, ('check', '"toast: " + document.getElementById("toast").textContent'),
      ('fill', ['#code-input', '111111']), ('click', 'form[data-form=code] button'), w,
      ('check', '"wrong code: " + document.getElementById("code-err").textContent'),
      ('click', '[data-act=inbox]'), w, ('click', '[data-act=inbox-use]'), w, ('click', 'form[data-form=code] button'), ('wait', 500),
      ('check', '"booked: " + ' + P),
      send, ('wait', 1800 if slow else 500), ('check', '"#code forms open: " + document.querySelectorAll("form[data-form=code]").length + " | already line: " + document.getElementById("thread").innerText.includes("already verified")'),
      send, ('wait', 1800 if slow else 500), ('click', '[data-act=follow-ch][data-val=phone]'), w, ('click', '[data-act=follow-when][data-val=mornings]'), w, ('click', '[data-act=follow-save]'), ('wait', 500),
      ('check', '"follow: " + ' + P),
      ('eval', 'var b=document.querySelector("[data-act=follow-change]"); if (b) b.click()'), w,
      ('eval', 'var r=document.querySelector("[data-act=follow-when][data-val=afternoons]"); if (r) { r.click(); document.querySelector("[data-act=follow-save]").click(); }'), w,
      ('check', '"after change: " + ' + P),
      send, ('wait', 1800 if slow else 500),
      ('check', 'JSON.stringify({hash: location.hash, safetyAttr: document.getElementById("app").hasAttribute("data-safety"), panel: document.getElementById("panel").innerText.replace(/\\s+/g," ").slice(0,60)})'),
      ('click', '#jump-btn'), w, ('click', '#jump-menu a[data-step=case]'), ('wait', 500),
      ('check', 'JSON.stringify({view: document.getElementById("app").dataset.view, switches: document.querySelectorAll(".switch-link").length})'),
      ('click', '[data-act=src-jump][data-val=fees]'), w, ('check', '"focused " + document.activeElement.id'),
      ('click', '[data-act=case-claim]'), w, ('click', '[data-act=case-call]'), w, ('click', 'form[data-form=call] button'), w,
      ('click', '[data-act=case-tab][data-val=conversation]'), w,
      ('check', '"internal notes: " + document.querySelectorAll("#ev-panel .note").length + " | " + document.getElementById("ev-panel").innerText.replace(/\\s+/g," ").slice(-160)'),
      ('click', '[data-ref="MHC-C-0005"]'), w, ('press', 'j'), ('check', '"j moved to " + document.activeElement.dataset.ref'),
    ]}
which = sys.argv[1]
url, motion = {'light': (LIGHT,'reduce'), 'dark': (DARKF,'reduce'), 'motion': (LIGHT,'no-preference')}[which]
res, err = run([flow(url, which=='motion')], SH, motion)
print('=====', which, 'errors', err)
for c in res[0]['checks']: print(c)
