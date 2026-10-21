import sys; sys.path.insert(0,'/Users/innocentnortey/.claude/jobs/0d72ed71/tmp')
from a5common import *
CHK = r"""(() => {
 const dark = document.documentElement.getAttribute('data-theme') === 'dark';
 const red = dark ? 'rgb(200, 49, 47)' : 'rgb(180, 35, 24)';
 const props = ['color','backgroundColor','borderTopColor','borderBottomColor','borderLeftColor','borderRightColor','fill','stroke'];
 const bad = [...document.querySelectorAll('body *')].filter(e => !e.closest('.safety') && props.some(p => getComputedStyle(e)[p] === red)).map(e => e.tagName + '.' + (e.className.baseVal === undefined ? e.className : 'svg'));
 const txt = document.getElementById('app').innerText;
 const chat = document.getElementById('app').dataset.view === 'chat';
 const cust = document.querySelector('.turn-customer .blk');
 const t = document.getElementById('talk');
 const small = chat ? [...document.querySelectorAll('.chat button, .chat [data-act], .chat input:not([type=radio])')].filter(e => !e.closest('.proto-bar') && e.getBoundingClientRect().width && e.getBoundingClientRect().height < 43.5 && !e.classList.contains('pb-btn')).map(e => (e.id||e.className||e.tagName) + ':' + Math.round(e.getBoundingClientRect().height)) : [];
 return JSON.stringify({hash: location.hash, B_red_outside_safety: bad.slice(0,6), C_cust: cust ? getComputedStyle(cust).backgroundColor : null,
  D_labels: [...document.querySelectorAll('#thread .turn, .thread-mini .turn')].every(x => x.querySelector('.name')),
  E_banned: /confidence|\d\s?%(?! off)|thought for|queue position|estimated wait|wait time/i.test(txt),
  F_talk: chat ? (!!t && !t.disabled && t.getBoundingClientRect().height >= 44) : 'n/a',
  G_24h: /\b\d{1,2}:\d{2}(?!\s?[ap]m)/i.test(txt), H_small: small.slice(0,8), switches: document.querySelectorAll('.switch-link').length});
})()"""
FONT = "Promise.all(['A5 Display','A5 Sans','A5 Mono'].map(f => document.fonts.load('16px \"' + f + '\"').then(r => r.length > 0))).then(JSON.stringify)"
for name, url in (('light', LIGHT), ('dark', DARKF)):
    jobs=[]
    for s in 'greeting answer booking code handoff safety live case'.split():
        acts=[('check',CHK)]
        if s=='live': acts=[('click','[data-act=demo-join]'),('wait',2500),('check',"document.getElementById('thread').innerText.includes('Riley (demo representative) has joined')"),('check',CHK)]
        if s=='safety': acts+=[('check',"""JSON.stringify({band:getComputedStyle(document.querySelector('.safety .sf-band')).backgroundColor, txt:document.querySelector('.safety').innerText, last:document.getElementById('thread').lastElementChild.innerText, sq:getComputedStyle(document.querySelector('.safety')).borderRadius})""")]
        if s=='greeting': acts+=[('check',FONT)]
        jobs.append({'url':url+'#'+s,'w':1280,'h':800,'shot':None,'wait':1500,'actions':acts})
    res,err=run(jobs,SH,'reduce')
    print('=====',name,'errors',err)
    for r in res:
        for c in r['checks']: print(c)
