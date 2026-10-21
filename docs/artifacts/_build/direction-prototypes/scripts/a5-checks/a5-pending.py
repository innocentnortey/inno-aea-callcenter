import sys, time; sys.path.insert(0,'/Users/innocentnortey/.claude/jobs/0d72ed71/tmp')
from a5common import *
TH="document.getElementById('thread').innerText"
def st(): return "JSON.stringify({pend1:%s.includes('Meridian assistant is replying…'),pend2:%s.includes('Still working on this…'),reply:%s.includes('$189 per year'),talk:!document.getElementById('talk').disabled})"%(TH,TH,TH)
start=[('click','#slow-btn'),('check',"document.getElementById('slow-btn').getAttribute('aria-pressed')"),('click','#jump-btn'),('click','#jump-menu a[data-step=answer]')]
j1={'url':LIGHT+'#greeting','w':1280,'h':800,'wait':800,'actions':start+[('wait',1000),('check',st()),('wait',9800),('check',st()),('wait',3000),('check',st())]}
j2={'url':LIGHT+'#greeting','w':1280,'h':800,'wait':800,'actions':start+[('wait',1000),('check',st()),('click','#slow-btn'),('wait',600),('check',st())]}
# third: safety direct with slow on, then talk button from handoff predecessor
j3={'url':LIGHT+'#greeting','w':1280,'h':800,'wait':800,'actions':[('click','#slow-btn'),('click','#jump-btn'),('click','#jump-menu a[data-step=safety]'),('wait',1500),('check',"JSON.stringify({safetyVisible:!!document.querySelector('.safety'),pend:%s.includes('replying…')})"%TH)]}
j4={'url':LIGHT+'#code','w':1280,'h':800,'wait':1200,'actions':[('click','#slow-btn'),('click','#talk'),('wait',1500),('check',"JSON.stringify({pend:%s.includes('replying…'),hash:location.hash,card:!!document.querySelector('.step-handoff')})"%TH)]}
which=sys.argv[1]
job={'1':j1,'2':j2,'3':j3,'4':j4}[which]
t=time.time()
res,err=run([job],SH,'reduce')
print(which,res[0]['checks'],'errors',err,round(time.time()-t,1))
