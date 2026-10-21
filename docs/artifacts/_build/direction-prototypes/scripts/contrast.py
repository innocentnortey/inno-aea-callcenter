import re, sys, pathlib
SRC = pathlib.Path(__file__).resolve().parent.parent / 'src'
def tokens(css, dark):
    m = re.search(r'/\*DARK-START\*/(.*?)/\*DARK-END\*/', css, re.S)
    root = re.search(r':root\s*\{(.*?)\}', css, re.S).group(1)
    t = dict(re.findall(r'--([\w-]+):\s*(#[0-9A-Fa-f]{6})', root))
    if dark: t.update(dict(re.findall(r'--([\w-]+):\s*(#[0-9A-Fa-f]{6})', m.group(1))))
    return t
def lum(h):
    c = [int(h[i:i+2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
def ratio(a, b):
    la, lb = sorted([lum(a), lum(b)], reverse=True)
    return (la + .05) / (lb + .05)
PAIRS = {
 'a1': [('ink','sheet',4.5),('ink','bg',4.5),('ink-2','sheet',4.5),('ink-2','bg',4.5),('ink-2','sheet-2',4.5),('ink','chip',4.5),('ink-2','chip',4.5),
        ('on-primary','primary',4.5),('primary','sheet',4.5),('primary','bg',4.5),('on-cust','cust',4.5),('sheet','ink',4.5),('ink','sel-bg',4.5),
        ('on-safety','safety-band',4.5),('safety-ink','safety-tint',4.5),('focus','sheet',3),('focus','bg',3),('ink-2','sheet',3)],
 'a3': [('ink','log',4.5),('ink','ground',4.5),('ink-2','log',4.5),('ink-2','ground',4.5),('ink-2','soft',4.5),('ink-2','soft-2',4.5),('ink','soft-2',4.5),
        ('on-cust','cust',4.5),('ink','rep',4.5),('on-primary','primary',4.5),('on-primary-soft','primary-soft',4.5),('on-primary-soft','log',4.5),('ink','primary-soft',4.5),
        ('on-note','note',4.5),('log','ink',4.5),('on-safety','safety-band',4.5),('safety-ink','safety-tint',4.5),('focus','log',3),('focus','ground',3),('focus','soft',3),
        ('line','log',3),('primary','log',3)],
 'a2': [('ink','paper',4.5),('ink','bg',4.5),('ink-2','paper',4.5),('ink-2','bg',4.5),('ink-2','paper-2',4.5),('paper','ink',4.5),
        ('on-board','board',4.5),('on-board-2','board',4.5),('on-board-2','board-2',4.5),('on-board','board-2',4.5),('on-board','pblk-lo',4.5),('board','on-board',4.5),
        ('on-key','key',4.5),('cobalt-ink','paper',4.5),('cobalt-ink','sel',4.5),('ink','sel',4.5),('on-cobalt','cobalt',4.5),
        ('on-safety','safety-band',4.5),('focus','paper',3),('focus','bg',3),('focus-board','board',3),('ink-2','paper',3)],
}
fails = 0
for k in ('a1', 'a2', 'a3'):
    css = (SRC / f'{k}.css').read_text()
    for dark in (False, True):
        t = tokens(css, dark)
        rows = []
        for fg, bg, need in PAIRS[k]:
            r = ratio(t[fg], t[bg]); ok = r >= need; fails += not ok
            rows.append(f'{fg}/{bg} {r:.2f}{"" if ok else " FAIL<" + str(need)}')
        print(k.upper(), 'dark' if dark else 'light', '| ' + ' | '.join(rows))
print('FAILS', fails)
