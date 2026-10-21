"""Whole-story click-through for every direction file (reduced motion)."""
import json
P = 'document.getElementById("panel").innerText.replace(/\\s+/g," ").slice(0,200)'
def flow(a):
    w = ('wait', 250); send = ('click', 'button.send')
    return {'url': 'file://' + a + '#greeting', 'w': 1280, 'h': 800, 'shot': None, 'actions': [
      send, w, send, w,
      ('click', '[data-key=checks][data-val=skip]'), w, ('click', '[data-key=qa][data-val=no]'), w, ('click', '[data-key=qb][data-val=skip]'), w,
      ('click', 'form[data-form=where] button'), ('wait', 400),
      ('click', '[data-act=slot-book]'), w, ('check', '"no-window error: " + (document.querySelector(".err") || {}).textContent'),
      ('eval', 'var d=document.querySelector("[data-act=slot-day][data-val=\\"2026-10-23\\"]"); if (d) d.click()'), w,
      ('click', '[data-act=slot-win][data-val="12:00-16:00"]'), w, ('click', '[data-act=slot-book]'), ('wait', 400),
      ('click', 'form[data-form=locate] button'), w, ('fill', ['#code-input', '111111']), ('click', 'form[data-form=code] button'), w,
      ('check', '"wrong code: " + document.getElementById("code-err").textContent'),
      ('click', '[data-act=inbox]'), w, ('click', '[data-act=inbox-use]'), w, ('click', 'form[data-form=code] button'), ('wait', 500),
      ('check', '"booked: " + ' + P),
      send, ('wait', 500), ('check', '"#code code forms open: " + document.querySelectorAll("form[data-form=code]").length + " | already line: " + document.getElementById("thread").innerText.includes("already verified")'),
      send, ('wait', 500), ('click', '[data-act=follow-ch][data-val=phone]'), w, ('click', '[data-act=follow-when][data-val=mornings]'), w, ('click', '[data-act=follow-save]'), ('wait', 500),
      ('check', '"follow: " + ' + P),
      ('eval', 'var b=document.querySelector("[data-act=follow-change]"); if (b) b.click()'), w,
      ('eval', 'var r=document.querySelector("[data-act=follow-when][data-val=afternoons]"); if (r) { r.click(); document.querySelector("[data-act=follow-save]").click(); }'), w,
      ('check', '"after change (A3 only): " + ' + P),
      send, ('wait', 500),
      ('check', 'JSON.stringify({hash: location.hash, safetyAttr: document.getElementById("app").hasAttribute("data-safety"), panel: document.getElementById("panel").innerText.replace(/\\s+/g," ").slice(0,60), redBg: [...document.querySelectorAll("body *")].filter(e => getComputedStyle(e).backgroundColor === "rgb(179, 20, 29)").map(e => e.className.baseVal === undefined ? e.className : "svg").filter((v,i,s)=>s.indexOf(v)===i)})'),
      ('click', '#jump-btn'), w, ('click', '#jump-menu a[data-step=case]'), ('wait', 500),
      ('check', 'JSON.stringify({view: document.getElementById("app").dataset.view, switches: [...document.querySelectorAll(".switch-link")].map(a => a.getAttribute("href"))})'),
      ('click', '[data-act=src-jump][data-val=fees]'), w, ('check', '"focused " + document.activeElement.id'),
      ('click', '[data-act=case-claim]'), w, ('click', '[data-act=case-call]'), w, ('click', 'form[data-form=call] button'), w,
      ('click', '[data-act=case-tab][data-val=conversation]'), w,
      ('check', '"internal notes: " + document.querySelectorAll("#ev-panel .note").length + " | " + document.getElementById("ev-panel").innerText.replace(/\\s+/g," ").slice(-160)'),
      ('click', '[data-ref="MHC-C-0005"]'), w, ('press', 'j'), ('check', '"j moved to " + document.activeElement.dataset.ref'),
    ]}
base = '/Users/innocentnortey/Desktop/Nortorious-Technologies/inno-aea-callcenter/docs/artifacts/'
files = ['2026-10-20-direction-A1-work-order.html', '2026-10-20-direction-A2-route-sheet.html', '2026-10-20-direction-A3-dispatchers-log.html']
print(json.dumps({'out': '/Users/innocentnortey/.claude/jobs/0d72ed71/tmp/shots', 'jobs': [flow(base + f) for f in files]}))
