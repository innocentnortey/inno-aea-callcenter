"""Headless inspection: screenshots + horizontal-overflow and console checks.
Launches its own Chrome with a temp profile under the job tmp dir. Never attaches to a running browser."""
import json, sys, tempfile, pathlib
from playwright.sync_api import sync_playwright
T = pathlib.Path('/Users/innocentnortey/.claude/jobs/0d72ed71/tmp')
ART = pathlib.Path('/Users/innocentnortey/Desktop/Nortorious-Technologies/inno-aea-callcenter/docs/artifacts')
WF = pathlib.Path('/Users/innocentnortey/Desktop/Nortorious-Technologies/inno-aea-callcenter/docs/ux/02-concepts/wireframes')
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
FILES = {'A1': '2026-10-20-direction-A1-work-order.html', 'A2': '2026-10-20-direction-A2-route-sheet.html'}

OVERFLOW_JS = """() => {
  const vw = document.documentElement.clientWidth;
  const bad = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width && (r.right > vw + 1 || r.left < -1)) {
      const cs = getComputedStyle(el);
      if (cs.position === 'fixed' && el.id === 'jump-menu') continue;
      bad.push((el.id ? '#' + el.id : el.tagName.toLowerCase() + '.' + [...el.classList].join('.')) + ' ' + Math.round(r.left) + '..' + Math.round(r.right));
    }
  }
  return {innerWidth: innerWidth, clientWidth: vw, scrollWidth: document.documentElement.scrollWidth, bodyScroll: document.body.scrollWidth, bad: bad.slice(0, 12)};
}"""

def run(jobs, outdir, spec_motion='reduce'):
    outdir.mkdir(parents=True, exist_ok=True)
    prof = tempfile.mkdtemp(prefix='chrome-prof-', dir=str(T))
    results = []
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(prof, executable_path=CHROME, headless=True,
              reduced_motion=spec_motion, viewport={'width': 1280, 'height': 800}, args=['--no-first-run', '--no-default-browser-check'])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        errors = []
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: errors.append(str(e)))
        for j in jobs:
            page.set_viewport_size({'width': j['w'], 'height': j['h']})
            page.goto('about:blank')
            page.goto(j['url'])
            page.wait_for_timeout(j.get('wait', 900))
            for act in j.get('actions', []):
                kind, arg = act
                if kind == 'click': page.click(arg)
                elif kind == 'eval': page.evaluate(arg)
                elif kind == 'wait': page.wait_for_timeout(arg)
                elif kind == 'fill': page.fill(arg[0], arg[1])
                elif kind == 'check': j.setdefault('checks', []).append(page.evaluate(arg))
                elif kind == 'press': page.keyboard.press(arg)
            page.wait_for_timeout(300)
            m = page.evaluate(OVERFLOW_JS)
            if j.get('shot'):
                page.screenshot(path=str(outdir / j['shot']), full_page=j.get('full', False))
            results.append({'name': j.get('shot') or j['url'], 'w': j['w'], 'checks': j.get('checks'), **m})
        ctx.close()
    return results, errors

if __name__ == '__main__':
    spec = json.loads(sys.argv[1])
    res, errs = run(spec['jobs'], pathlib.Path(spec['out']), spec.get('motion', 'reduce'))
    print(json.dumps({'results': res, 'errors': errs}, indent=1))
