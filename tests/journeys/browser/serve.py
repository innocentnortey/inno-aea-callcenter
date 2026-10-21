"""`python -m tests.journeys.browser.serve`: the same server as the browser journeys, for a hand walkthrough (AC-15)."""

from __future__ import annotations

import json
import os
import sys
import threading

from meridian.domain.common import Role
from tests.journeys.browser.build import check_production_build, dist_dir_from_env
from tests.journeys.browser.server import open_browser_journey
from tests.journeys.j1.test_aea_57 import CLASSIFIER_RAW, PLANNER_RAW, RESPONDER_TEXT
from tests.journeys.support.steps import StepCollector


def main() -> int:
    user = os.environ.get("MERIDIAN_DEMO_USERNAME")
    password = os.environ.get("MERIDIAN_DEMO_PASSWORD")
    if not user or not password:
        print(
            "set MERIDIAN_DEMO_USERNAME and MERIDIAN_DEMO_PASSWORD in your shell first "
            "(choose synthetic values; nothing is printed or invented)",
            file=sys.stderr,
        )
        return 2
    build = check_production_build(dist_dir_from_env())
    with open_browser_journey(
        collector=StepCollector(),
        strict=False,
        nodeid="serve",
        build=build,
        environ_overrides={"MERIDIAN_DEMO_USERNAME": user, "MERIDIAN_DEMO_PASSWORD": password},
    ) as run:
        run.script.add(Role.PLANNER, PLANNER_RAW)
        run.script.add(Role.CLASSIFIER, CLASSIFIER_RAW)
        run.script.add(Role.RESPONDER, json.dumps({"text": RESPONDER_TEXT}))
        print(
            f"serving {run.base_url} (production build {build.dist_dir}, scripted model; sign in with "
            "MERIDIAN_DEMO_USERNAME / MERIDIAN_DEMO_PASSWORD from your shell). Ctrl-C to stop.",
            flush=True,
        )
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
