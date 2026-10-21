import json, sys
def flow(a):
    send = ('click', 'button.send')
    w = ('wait', 250)
    acts = [send, w, send, w,
      ('click', '[data-key=checks][data-val=skip]'), w, ('click', '[data-key=qa][data-val=no]'), w, ('click', '[data-key=qb][data-val=skip]'), w,
      ('click', '[data-act=slot-book]'), w, ('check', 'document.querySelector(".err") && document.querySelector(".err").textContent'),
      ('click', '[data-act=slot-day][data-val="2026-10-23"]'), w, ('click', '[data-act=slot-win][data-val="12:00-16:00"]'), w, ('click', '[data-act=slot-book]'), ('wait', 500),
      ('check', 'document.getElementById("panel").innerText.replace(/\\s+/g," ").slice(0,200)'),
      send, ('wait', 400), 
      ('check', 'document.getElementById("code-err") && document.getElementById("code-err").textContent'),
      ('click', '[data-act=inbox]'), w, ('click', '[data-act=inbox-use]'), w, ('click', 'form[data-form=code] button'), ('wait', 500),
      ('check', 'document.getElementById("panel").innerText.includes("Verified")'),
      send, ('wait', 500), ('click', '[data-act=follow-ch][data-val=phone]'), w, ('click', '[data-act=follow-when][data-val=mornings]'), w, ('click', '[data-act=follow-save]'), ('wait', 500),
      ('check', 'document.getElementById("panel").innerText.replace(/\\s+/g," ").slice(0,400)'),
      send, ('wait', 500),
      ('check', 'JSON.stringify({hash: location.hash, pinned: !document.getElementById("pinned").hidden, panel: document.getElementById("panel").innerText.replace(/\\s+/g," "), reds: [...document.querySelectorAll("*")].filter(e => getComputedStyle(e).backgroundColor === "rgb(179, 20, 29)").map(e => e.className).slice(0,8)})'),
      ('click', '#jump-btn'), w, ('click', '#jump-menu a[data-step=case]'), ('wait', 500),
      ('check', 'JSON.stringify({hash: location.hash, view: document.getElementById("app").dataset.view, sw: document.getElementById("switch-link").getAttribute("href")})'),
      ('click', '[data-act=src-jump][data-val=fees]'), w, ('check', 'document.activeElement.id'),
      ('click', '[data-act=case-claim]'), w, ('click', '[data-act=case-call]'), w, ('click', 'form[data-form=call] button'), w,
      ('check', 'document.querySelector(".log").innerText'),
      ('click', '[data-act=case-tab][data-val=conversation]'), w, ('check', 'document.getElementById("ev-panel").innerText.slice(0,120)'),
      ('click', '[data-ref="MHC-C-0005"]'), w, ('press', 'j'), ('check', 'document.activeElement.dataset.ref'),
    ]
    return {'url': 'file://' + a + '#greeting', 'w': 1280, 'h': 800, 'shot': None, 'actions': acts}
base = '/Users/innocentnortey/Desktop/Nortorious-Technologies/inno-aea-callcenter/docs/artifacts/'
jobs = [flow(base + '2026-10-20-direction-A1-work-order.html'), flow(base + '2026-10-20-direction-A2-route-sheet.html')]
print(json.dumps({'out': '/Users/innocentnortey/.claude/jobs/0d72ed71/tmp/shots', 'jobs': jobs}))
