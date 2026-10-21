import sys; sys.path.insert(0,'/Users/innocentnortey/.claude/jobs/0d72ed71/tmp')
from a5common import *
jobs=[{'url':LIGHT+'#'+s,'w':w,'h':h,'shot':f'sm-{s}-{w}.png','wait':1200,'actions':[('check','document.querySelectorAll(".switch-link").length')]} for s,w,h in [('booking',390,844),('handoff',1280,800),('case',1280,800),('safety',390,844)]]
res,err=run(jobs,SH)
print(json.dumps(res,indent=0)[:1500]); print('ERR',err)
