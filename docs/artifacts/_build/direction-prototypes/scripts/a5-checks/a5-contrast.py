import re
css=open('/Users/innocentnortey/Desktop/Nortorious-Technologies/inno-aea-callcenter/docs/artifacts/_build/direction-prototypes/src/a5.css').read()
root=re.search(r':root\s*\{(.*?)\}',css,re.S).group(1)
dk=re.search(r'/\*DARK-START\*/(.*?)/\*DARK-END\*/',css,re.S).group(1)
def toks(t): return dict((k,v.upper()) for k,v in re.findall(r'--([a-z0-9-]+):\s*(#[0-9A-Fa-f]{6})',t))
L=toks(root); D=dict(L); D.update(toks(dk))
def lum(h):
    f=lambda c:c/12.92 if c<=.03928 else ((c+.055)/1.055)**2.4
    r,g,b=(int(h[i:i+2],16)/255 for i in (1,3,5)); return .2126*f(r)+.7152*f(g)+.0722*f(b)
def ratio(a,b):
    x,y=sorted((lum(a),lum(b)),reverse=True); return (x+.05)/(y+.05)
text="ink/ground ink/panel ink/rail ink/well ink/mint ink/mint-edge ink/selected ink2/ground ink2/panel ink2/rail ink2/well ink2/mint ink2/selected primary/panel primary/well primary/rail primary/mint on-primary/primary on-charcoal/charcoal on-person/person on-danger/danger".split()
ui="primary/panel primary/mint danger/panel charcoal/panel line/panel line/well focus/panel focus/well focus/mint focus/ground".split()
fails=0
for name,T in (('light',L),('dark',D)):
    out=[]
    for pairs,min_ in ((text,4.5),(ui,3.0)):
        for p in pairs:
            a,b=p.split('/'); r=ratio(T[a],T[b]); ok=r>=min_
            if not ok: fails+=1
            out.append(f"{p}={r:.2f}{'' if ok else ' FAIL(<%s)'%min_}")
    print(name,' '.join(out))
print('FAILS',fails)
