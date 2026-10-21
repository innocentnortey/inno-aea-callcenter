"""Assemble the two direction prototypes into single self-contained HTML files."""
import base64, pathlib, re, sys
T = pathlib.Path(__file__).resolve().parent.parent  # docs/artifacts/_build/direction-prototypes
SRC, FO = T / 'src', T / 'fonts-out'
OUT = T.parent.parent  # docs/artifacts

def b64(name):
    return 'data:font/woff2;base64,' + base64.b64encode((FO / name).read_bytes()).decode()

FONTS = {
  'a1': [('A1 Sans', 'a1-sans.woff2', 'normal', '400 700', 'font-stretch: 85% 100%;'),
         ('A1 Sans', 'a1-sans-italic.woff2', 'italic', '400', ''),
         ('A1 Mono', 'a1-mono-400.woff2', 'normal', '400', ''),
         ('A1 Mono', 'a1-mono-500.woff2', 'normal', '500', '')],
  'a2': [('A2 Sans', 'a2-sans-400.woff2', 'normal', '400', ''),
         ('A2 Sans', 'a2-sans-500.woff2', 'normal', '500', ''),
         ('A2 Sans', 'a2-sans-600.woff2', 'normal', '600', ''),
         ('A2 Cond', 'a2-cond-600.woff2', 'normal', '600', ''),
         ('A2 Cond', 'a2-cond-700.woff2', 'normal', '700', ''),
         ('A2 Mono', 'a2-mono.woff2', 'normal', '400 600', '')],
  'a3': [('A3 Display', 'a3-display.woff2', 'normal', '500 700', ''),
         ('A3 Sans', 'a3-sans.woff2', 'normal', '400 700', ''),
         ('A3 Sans', 'a3-sans-italic.woff2', 'italic', '400', '')],
  'a5': [('A5 Display', 'a5-display.woff2', 'normal', '400 700', 'font-stretch: 90% 100%;'),
         ('A5 Sans', 'a5-sans.woff2', 'normal', '400 700', ''),
         ('A5 Mono', 'a5-mono.woff2', 'normal', '400 600', '')],
}
META = {
  'a1': ('2026-10-20-direction-A1-work-order.html', 'Meridian · A1 Work order',
         'Direction prototype A1 Work order for the Meridian AI service agent (UX-2). Synthetic demo data.'),
  'a2': ('2026-10-20-direction-A2-route-sheet.html', 'Meridian · A2 Route sheet',
         'Direction prototype A2 Route sheet for the Meridian AI service agent (UX-2). Synthetic demo data.'),
  'a3': ('2026-10-20-direction-A3-dispatchers-log.html', "Meridian · A3 Dispatcher's log",
         "Direction prototype A3 Dispatcher's log for the Meridian AI service agent (UX-2). Synthetic demo data."),
  'a5': ('2026-10-21-direction-A5-service-desk.html', 'Meridian · A5 Service desk',
         'Direction prototype A5 Service desk for the Meridian AI service agent (UX-2). Synthetic demo data.'),
}
LICENCE = {
  'a1': 'Fonts: IBM Plex Sans and IBM Plex Mono, (c) 2017 IBM Corp., SIL Open Font License 1.1; Latin subsets.',
  'a3': 'Fonts: Bricolage Grotesque, (c) 2022 The Bricolage Grotesque Project Authors; Public Sans, (c) 2015 The Public Sans Project Authors; SIL Open Font License 1.1; Latin subsets.',
  'a5': 'Fonts: Instrument Sans, (c) 2022 The Instrument Sans Project Authors; Inter, (c) 2016 The Inter Project Authors; Geist Mono, (c) 2024 The Geist Project Authors; SIL Open Font License 1.1; Latin subsets.',
  'a2': 'Fonts: Barlow and Barlow Semi Condensed, (c) 2017 The Barlow Project Authors; JetBrains Mono, (c) 2020 The JetBrains Mono Project Authors; SIL Open Font License 1.1; Latin subsets.',
}

def css_for(k):
    css = (SRC / f'{k}.css').read_text()
    m = re.search(r'/\*DARK-START\*/(.*?)/\*DARK-END\*/', css, re.S)
    dark = m.group(1).strip()
    css = css[:m.start()] + (
        '@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { ' + dark + ' } }\n'
        ':root[data-theme="dark"] { ' + dark + ' }\n'
        ':root[data-theme="light"] { color-scheme: light; } :root[data-theme="dark"] { color-scheme: dark; }\n'
    ) + css[m.end():]
    faces = '\n'.join(
        f'@font-face {{ font-family: "{fam}"; src: url({b64(f)}) format("woff2"); font-style: {st}; font-weight: {w}; {extra} font-display: swap; }}'
        for fam, f, st, w, extra in FONTS[k])
    return faces + '\n' + (SRC / 'proto.css').read_text() + '\n' + css

def build(k, theme=None, out=None):
    fname, title, desc = META[k]
    engine = (SRC / 'engine.js').read_text()
    skin = (SRC / f'{k}.skin.js').read_text()
    th = f' data-theme="{theme}"' if theme else ''
    html = f'''<!doctype html>
<html lang="en"{th}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title.replace("'", '&#39;')}</title>
<meta name="description" content="{desc}">
<!-- {LICENCE[k]} -->
<!-- UX-2 choice aid, not product code. Scripted story; every number from the issued dataset or the consolidated direction. -->
<style>
{css_for(k)}
</style>
</head>
<body>
<noscript><p style="padding:16px">This direction prototype needs JavaScript to play its scripted story.</p></noscript>
<div id="app"></div>
<script>
{skin}
</script>
<script>
{engine}
</script>
</body>
</html>
'''
    p = pathlib.Path(out) if out else OUT / fname
    p.write_text(html)
    return p, len(html)

if __name__ == '__main__':
    ks = sys.argv[1:] or ['a5']
    for k in ks:
        p, n = build(k)
        print(p, n)
        for th in ('dark',):
            q = T / 'shots-src'
            q.mkdir(exist_ok=True)
            p2, _ = build(k, th, q / META[k][0].replace('.html', f'-{th}.html'))
            # dark copies keep the same file name stem so the switch link stays meaningful
