import sys; sys.path.insert(0,'/Users/innocentnortey/.claude/jobs/0d72ed71/tmp')
from a5common import *
rows=[('A5-chat-390-light.png',LIGHT,'handoff',390,844),('A5-chat-1280-light.png',LIGHT,'handoff',1280,800),('A5-case-1280-light.png',LIGHT,'case',1280,800),
('A5-chat-390-dark.png',DARKF,'handoff',390,844),('A5-chat-1280-dark.png',DARKF,'handoff',1280,800),('A5-case-1280-dark.png',DARKF,'case',1280,800)]
jobs=[{'url':u+'#'+h,'w':w,'h':hh,'shot':n,'wait':1200,'full':False} for n,u,h,w,hh in rows]
res,err=run(jobs,WF,'reduce'); print('errors',err)
jobs=[{'url':LIGHT+'#safety','w':390,'h':844,'shot':'safety-390.png','wait':1200},{'url':LIGHT+'#safety','w':1280,'h':800,'shot':'safety-1280.png','wait':1200},
{'url':LIGHT+'#booking','w':1280,'h':800,'shot':'book-1280.png','wait':1200,'actions':[('click','[data-key=checks][data-val=skip]'),('wait',700),('click','[data-key=qa][data-val=no]'),('wait',600),('click','[data-key=qb][data-val=skip]'),('wait',900),('click','form[data-form=where] button'),('wait',900),('click','[data-act=slot-win]'),('wait',300)]}]
res,err=run(jobs,SH,'reduce'); print('errors',err)
LOOK='file:///Users/innocentnortey/Desktop/Nortorious-Technologies/inno-aea-callcenter/docs/artifacts/2026-10-20-a5-look-sheet.html'
res,err=run([{'url':LOOK,'w':1280,'h':900,'shot':'look-1280.png','wait':1500,'full':True}],SH,'reduce'); print('errors',err)
