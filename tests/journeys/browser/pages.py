"""Devices, pages and the run object (AEA-58): contexts, screenshots (page and element, AEA-58-F1), teardown
validation (AC-7, PA-1)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from tests.api.openapi_check import load_contract
from tests.journeys.browser.network import (
    NetworkLog,
    ValidationSummary,
    teardown_failures,
    validate_exchanges,
)

if TYPE_CHECKING:
    from playwright.sync_api import Browser, BrowserContext, Locator, Page

    from tests.journeys.browser.build import ProductionBuild
    from tests.journeys.browser.record import BrowserSession
    from tests.journeys.support.run import JourneyRun


@dataclass(frozen=True)
class Device:
    name: str
    width: int
    height: int


DESKTOP = Device("chrome-desktop", 1280, 800)  # apps/web/playwright.config.ts projects
PHONE = Device("chrome-phone", 390, 844)
DEVICES: tuple[Device, ...] = (DESKTOP, PHONE)
LABEL = re.compile(r"^[a-z0-9-]{1,40}$")


@dataclass
class BrowserPage:
    device: Device
    context: BrowserContext
    page: Page
    net: NetworkLog


@dataclass
class BrowserRun:
    run: JourneyRun
    browser: Browser
    channel: str
    build: ProductionBuild
    shots_dir: Path
    session: BrowserSession
    test_name: str
    pages: list[BrowserPage] = field(default_factory=list)

    def open(self, device: Device) -> BrowserPage:
        context = self.browser.new_context(
            viewport={"width": device.width, "height": device.height},
            locale="en-US",
            timezone_id="America/Chicago",
            reduced_motion="reduce",
            base_url=self.run.base_url,
        )
        context.set_default_timeout(15_000)
        net = NetworkLog(load_contract())
        net.attach(context)
        page = context.new_page()
        made = BrowserPage(device, context, page, net)
        self.pages.append(made)
        self.session.devices.add(device.name)
        return made

    def _shot_path(self, bp: BrowserPage, label: str) -> Path:
        if not LABEL.fullmatch(label):
            raise ValueError(f"bad screenshot label: {label!r}")
        self.shots_dir.mkdir(parents=True, exist_ok=True)
        return self.shots_dir / f"{self.test_name}-{bp.device.name}-{label}.png"

    def screenshot(self, bp: BrowserPage, label: str) -> Path:
        path = self._shot_path(bp, label)
        bp.page.screenshot(path=str(path), full_page=False)
        self.session.screenshots.append(path)
        return path

    def screenshot_element(self, bp: BrowserPage, target: Locator, label: str) -> Path:
        """Only the element (AEA-58-F1 A-3): a card shown next to identity values is shot alone."""
        path = self._shot_path(bp, label)
        target.screenshot(path=str(path))
        self.session.screenshots.append(path)
        return path

    def close(self) -> None:
        contract = load_contract()
        summaries: list[ValidationSummary] = []
        for bp in self.pages:
            try:
                bp.page.wait_for_timeout(200)  # let pending requestfinished events dispatch
            except Exception:  # noqa: S110 - a closed page has nothing pending
                pass
            summary = validate_exchanges(
                bp.net.exchanges, container=self.run.container, app=self.run.app, contract=contract
            )
            summaries.append(summary)
            self.session.validated.update(summary.validated)
            self.session.unrouted.update(summary.unrouted)
            self.session.unrouted_owners.update(summary.unrouted_owners)
            self.session.unbound.update(summary.unbound)
            self.session.unbound_owners.update(summary.unbound_owners)
            self.session.sse_checked.update(summary.sse_checked)
            self.session.unfinished += summary.unfinished
        for bp in self.pages:
            try:
                bp.context.close()
            except Exception:  # noqa: S110 - a context that cannot close must not hide the validation result
                pass
        failures: list[str] = []
        for summary in summaries:
            failures.extend(teardown_failures(summary, strict=self.run.strict))
        self.session.failures += len(failures)
        if failures:
            raise AssertionError("browser API responses broke the OpenAPI:\n" + "\n".join(failures[:20]))
