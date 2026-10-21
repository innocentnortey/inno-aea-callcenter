"""AEA-50: registers the `deploy` marker and skips docker tests unless `-m deploy` selects them (frozen).

Later CAP tickets extend this file by appending hooks; none replaces it (AEA-50 plan section 8, R-6).
"""

from __future__ import annotations

import pytest

from tests.deploy.support import cleanup_session, configure_deploy_marker, skip_deploy_unless_selected


def pytest_configure(config: pytest.Config) -> None:
    configure_deploy_marker(config)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    skip_deploy_unless_selected(config, items)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    cleanup_session()
