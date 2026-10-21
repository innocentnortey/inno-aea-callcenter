import sys; sys.path.insert(0,'/Users/innocentnortey/.claude/jobs/0d72ed71/tmp')
from a5common import *
q="(()=>{const t=document.getElementById('thread');return JSON.stringify({top:t.scrollTop,ch:t.clientHeight,sh:t.scrollHeight,chat:document.querySelector('.chat').scrollTop,doc:document.scrollingElement.scrollTop})})()"
for w,h in ((390,844),(1280,800)):
    res,err=run([{'url':LIGHT+'#safety','w':w,'h':h,'wait':1500,'actions':[('check',q)]}],SH,'reduce'); print(w,res[0]['checks'],err)
