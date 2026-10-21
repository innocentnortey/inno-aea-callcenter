import json
P = 'document.getElementById("panel").innerText.replace(/\\s+/g," ").slice(0,260)'
T = 'document.getElementById("thread").innerText.replace(/\\s+/g," ").slice(-420)'
def flow(a):
    w = ('wait', 250); send = ('click', 'button.send')
    return {'url': 'file://' + a + '#booking', 'w': 1280, 'h': 800, 'shot': None, 'actions': [
      ('click', '[data-key=checks][data-val=skip]'), w, ('click', '[data-key=qa][data-val=no]'), w, ('click', '[data-key=qb][data-val=skip]'), w,
      ('fill', ['#where-input', '78701']), ('click', 'form[data-form=where] button'), w, ('check', 'document.querySelector(".err") && document.querySelector(".err").textContent'),
      ('fill', ['#where-input', '78640']), ('click', 'form[data-form=where] button'), ('wait', 500),
      ('check', 'JSON.stringify({identityFieldsOnSlotCard: !!document.querySelector("[data-act=slot-book]").closest("section").querySelector("[data-bind]"), panel: ' + P + '})'),
      ('click', '[data-act=slot-win][data-val="08:00-12:00"]'), ('click', '[data-act=slot-book]'), ('wait', 500),
      ('click', 'form[data-form=locate] button'), w, ('check', P),
      ('fill', ['#code-input', '111111']), ('click', 'form[data-form=code] button'), w, ('check', 'document.getElementById("code-err").textContent'),
      ('click', '[data-act=inbox]'), w, ('check', 'document.querySelector("#inbox .inbox-m").innerText'), ('click', '[data-act=inbox-use]'), w, ('click', 'form[data-form=code] button'), ('wait', 600),
      ('check', T), ('check', P),
      send, ('wait', 600), ('check', 'location.hash + " | code cards: " + document.querySelectorAll("form[data-form=code]").length + " | " + ' + T),
    ]}
base = '/Users/innocentnortey/Desktop/Nortorious-Technologies/inno-aea-callcenter/docs/artifacts/'
jobs = [flow(base + f) for f in ('2026-10-20-direction-A1-work-order.html', '2026-10-20-direction-A2-route-sheet.html')]
for f in ('2026-10-20-direction-A1-work-order.html', '2026-10-20-direction-A2-route-sheet.html'):
    jobs.append({'url': 'file://' + base + f + '#code', 'w': 390, 'h': 844, 'shot': None, 'actions': [('check', 'document.querySelectorAll("form[data-form=code]").length + " code forms | " + ' + T)]})
print(json.dumps({'out': '/Users/innocentnortey/.claude/jobs/0d72ed71/tmp/shots', 'jobs': jobs}))
