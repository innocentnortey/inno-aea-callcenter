import sys; sys.path.insert(0,'/Users/innocentnortey/.claude/jobs/0d72ed71/tmp')
from a5common import *
w=int(sys.argv[1])
jobs=[]
for s in 'greeting answer booking code handoff safety live case'.split():
    jobs.append({'url':LIGHT+'#'+s,'w':w,'h':844,'wait':1200,'actions':[]})
jobs.append({'url':LIGHT+'#booking','w':w,'h':844,'wait':1200,'actions':[('click','[data-key=checks][data-val=skip]'),('wait',700),('click','[data-key=qa][data-val=no]'),('wait',600),('click','[data-key=qb][data-val=skip]'),('wait',900),('click','form[data-form=where] button'),('wait',900),('click','[data-act=slot-win]'),('wait',200),('check','"sel:"+document.querySelectorAll(".win.is-sel").length')]})
jobs.append({'url':LIGHT+'#handoff','w':w,'h':844,'wait':1200,'actions':[('click','[data-act=follow-ch][data-val=phone]'),('wait',200)]})
jobs.append({'url':LIGHT+'#case','w':w,'h':844,'wait':1200,'actions':[('click','[data-act=case-tab][data-val=conversation]'),('wait',200)]})
for s in ('handoff','case','booking','safety'):
    jobs.append({'url':DARKF+'#'+s,'w':w,'h':844,'wait':1200,'actions':[]})
res,err=run(jobs,SH)
ok=True
for j,r in zip(jobs,res):
    flag = r['scrollWidth']>r['clientWidth'] or r['bad']
    ok &= not flag
    print(w, j['url'].split('/')[-1][-40:], r['scrollWidth'],r['clientWidth'], r['bad'][:3], 'FAIL' if flag else 'ok', r.get('checks') or '')
print('errors',err,'ALL OK' if ok else 'PROBLEMS')
