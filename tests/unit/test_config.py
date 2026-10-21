"""AEA-02 frozen tests: typed Settings, role maps, secrets, Langfuse completeness (AC-12 to AC-15).

Frozen by the test-writer before the implementer starts; the implementer must not edit this file.
"""

from __future__ import annotations

import itertools
import json
import logging
import secrets
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from meridian.config import (
    ENV_NAMES,
    JEV_MODEL,
    SONNET_MODEL,
    ModelSettings,
    Settings,
    SettingsError,
    default_model_settings,
)
from meridian.domain.common import SafeError
from meridian.ports.models import Role
from meridian.privacy.redact import RedactionProfile

REPO_ROOT = Path(__file__).resolve().parents[2]

# graph-core §12: the seventeen environment names, typed here independently of ENV_NAMES.
EXPECTED_ENV_NAMES = {
    "ANTHROPIC_API_KEY",
    "OPENROUTER_API_KEY",
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_BASE_URL",
    "LANGFUSE_PROJECT_ID",
    "MERIDIAN_DEMO_USERNAME",
    "MERIDIAN_DEMO_PASSWORD",
    "MERIDIAN_SESSION_SECRET",
    "MERIDIAN_EVAL_KEY",
    "MERIDIAN_COOKIE_SECURE",
    "MERIDIAN_TRUST_PROXY_HEADERS",
    "MERIDIAN_WEB_DIST_DIR",
    "MERIDIAN_REQUIRE_FRONTEND",
    "MERIDIAN_DATA_DIR",
    "MERIDIAN_INDEX_DIR",
    "MERIDIAN_AGENT_VERSION",
}
REQUIRED_SECRETS = (
    "ANTHROPIC_API_KEY",
    "OPENROUTER_API_KEY",
    "MERIDIAN_DEMO_USERNAME",
    "MERIDIAN_DEMO_PASSWORD",
    "MERIDIAN_SESSION_SECRET",
)
LANGFUSE_NAMES = (
    "LANGFUSE_PUBLIC_KEY",
    "LANGFUSE_SECRET_KEY",
    "LANGFUSE_BASE_URL",
    "LANGFUSE_PROJECT_ID",
)


def _sentinel(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(8)}"


def _env(**overrides: str) -> dict[str, str]:
    """The five required names with run-time sentinels (never a real key); overrides add or replace names."""
    base = {name: _sentinel(name.lower()) for name in REQUIRED_SECRETS}
    base.update(overrides)
    return base


def _field_secrets(env: dict[str, str]) -> dict[str, str]:
    """The same required values keyed by Settings field name, for Settings.model_validate."""
    return {field: env[name] for field, name in ENV_NAMES.items() if name in REQUIRED_SECRETS}


def _maps() -> dict[str, dict[Any, Any]]:
    defaults = default_model_settings()
    return {
        "choice": dict(defaults.choice),
        "structured": dict(defaults.structured),
        "tools": dict(defaults.tools),
    }


def test_valid_environment_builds() -> None:
    """[invariant, AC-12] A complete environment builds with the code-default role maps and graph-core §12's names."""
    settings = Settings.from_env(
        {**_env(), "PATH": "/usr/bin", "MERIDIAN_DATA_DIR": "/tmp/x", "MERIDIAN_COOKIE_SECURE": "true"}  # noqa: S108
    )
    assert settings.data_dir == Path("/tmp/x")  # noqa: S108
    assert settings.cookie_secure is True
    assert settings.agent_version == "dev"
    assert settings.web_dist_dir == Path("apps/web/dist")
    assert settings.models == default_model_settings()

    models = settings.models
    planner_provider, planner = models.choice[Role.PLANNER]
    classifier_provider, classifier = models.choice[Role.CLASSIFIER]
    fallback_provider, fallback = models.choice[Role.PLANNER_FALLBACK]
    responder_provider, responder = models.structured[Role.RESPONDER]
    brief_provider, brief = models.structured[Role.BRIEF]
    specialist_provider, specialist = models.tools[Role.SPECIALIST]

    assert (planner_provider, classifier_provider) == ("openrouter_jev", "openrouter_jev")
    assert planner.model == JEV_MODEL
    assert classifier.model == JEV_MODEL
    for provider in (fallback_provider, responder_provider, brief_provider, specialist_provider):
        assert provider == "anthropic"
    for spec in (fallback, responder, brief, specialist):
        assert spec.model == SONNET_MODEL
    assert planner.redaction == RedactionProfile.JEV
    assert classifier.redaction == RedactionProfile.JEV
    for spec in (fallback, responder, brief, specialist):
        assert spec.redaction == RedactionProfile.SONNET
    caps = [planner.cap_s, classifier.cap_s, fallback.cap_s, responder.cap_s, brief.cap_s, specialist.cap_s]
    assert caps == [3.0, 3.0, 8.0, 12.0, 12.0, 8.0]


def test_each_value_is_read_from_its_graph_core_name() -> None:
    """[invariant, AC-12] Every secret field is read from the environment name graph-core §12 gives it."""
    env = _env()
    settings = Settings.from_env(env)
    assert settings.anthropic_api_key.get_secret_value() == env["ANTHROPIC_API_KEY"]
    assert settings.openrouter_api_key.get_secret_value() == env["OPENROUTER_API_KEY"]
    assert settings.demo_username.get_secret_value() == env["MERIDIAN_DEMO_USERNAME"]
    assert settings.demo_password.get_secret_value() == env["MERIDIAN_DEMO_PASSWORD"]
    assert settings.session_secret.get_secret_value() == env["MERIDIAN_SESSION_SECRET"]
    assert set(ENV_NAMES.values()) == EXPECTED_ENV_NAMES


def test_env_example_matches_settings() -> None:
    """[invariant, AC-12] .env.example lists exactly Settings' environment names, each with no value."""
    names: list[str] = []
    for raw in (REPO_ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, separator, value = line.partition("=")
        assert separator == "=", f"not a NAME= line: {line[:40]}"
        assert value == "", f"{name} has a value in .env.example"
        names.append(name)
    print(sorted(names))
    assert len(names) == len(set(names)), "duplicate name"
    assert set(names) == set(ENV_NAMES.values())
    assert set(names) == EXPECTED_ENV_NAMES
    assert len(names) == 17


@pytest.mark.parametrize(
    ("map_name", "role"),
    [("structured", Role.RESPONDER), ("structured", Role.BRIEF), ("tools", Role.SPECIALIST)],
    ids=["responder", "brief", "specialist"],
)
def test_jev_in_structured_or_tool_role_rejected(map_name: str, role: Role) -> None:
    """[failure/refusal, AC-13] Jev configured for responder, brief or specialist fails, naming the field and the rule."""
    maps = _maps()
    _, spec = maps[map_name][role]
    maps[map_name][role] = ("openrouter_jev", spec)

    with pytest.raises(ValidationError):
        ModelSettings.model_validate(maps)

    env = _env()
    with pytest.raises(ValidationError) as caught:
        Settings.model_validate({**_field_secrets(env), "models": maps})
    exc = caught.value
    problems = SafeError.from_validation_error(exc)
    assert any(map_name in p.field.split(".") and p.code == "literal_error" for p in problems), [
        (p.field, p.code) for p in problems
    ]
    for value in env.values():
        assert value not in str(exc)


@pytest.mark.parametrize(
    ("case", "expected_code"),
    [
        ("responder_in_choice", "literal_error"),
        ("planner_in_structured", "literal_error"),
        ("planner_in_tools", "literal_error"),
        ("missing_brief", "missing_role"),
    ],
)
def test_role_in_wrong_map_rejected(case: str, expected_code: str) -> None:
    """[failure/refusal, AC-13] A role placed in the wrong map, or a missing role, fails validation."""
    maps = _maps()
    if case == "responder_in_choice":
        maps["choice"][Role.RESPONDER] = maps["structured"][Role.RESPONDER]
    elif case == "planner_in_structured":
        maps["structured"][Role.PLANNER] = ("anthropic", maps["choice"][Role.PLANNER][1])
    elif case == "planner_in_tools":
        maps["tools"][Role.PLANNER] = ("anthropic", maps["choice"][Role.PLANNER][1])
    else:
        del maps["structured"][Role.BRIEF]
    with pytest.raises(ValidationError) as caught:
        ModelSettings.model_validate(maps)
    problems = SafeError.from_validation_error(caught.value)
    assert any(p.code == expected_code for p in problems), [(p.field, p.code) for p in problems]
    if expected_code == "missing_role":
        assert any("brief" in p.constraint for p in problems), [p.constraint for p in problems]


@pytest.mark.parametrize("name", REQUIRED_SECRETS)
@pytest.mark.parametrize("blank", [False, True], ids=["absent", "blank"])
def test_missing_required_secret_named(name: str, blank: bool) -> None:
    """[failure/refusal, AC-13] A missing or blank required secret stops start-up, naming the variable."""
    env = _env()
    if blank:
        env[name] = "  "
    else:
        del env[name]
    with pytest.raises(SettingsError) as caught:
        Settings.from_env(env)
    exc = caught.value
    assert name in str(exc)
    assert any(p.field == name and p.code == "missing" for p in exc.problems), [
        (p.field, p.code) for p in exc.problems
    ]
    for other_name, value in env.items():
        if other_name != name:
            assert value not in str(exc)


def test_secret_values_absent_from_repr_errors_and_logs(caplog: pytest.LogCaptureFixture) -> None:
    """[negative, AC-14] No secret value appears in repr, str, the dump, the role map, any error report or any log."""
    secret_env = {
        "ANTHROPIC_API_KEY": _sentinel("anthropic"),
        "OPENROUTER_API_KEY": _sentinel("openrouter"),
        "LANGFUSE_PUBLIC_KEY": _sentinel("lf-public"),
        "LANGFUSE_SECRET_KEY": _sentinel("lf-secret"),
        "MERIDIAN_DEMO_USERNAME": _sentinel("demo-user"),
        "MERIDIAN_DEMO_PASSWORD": _sentinel("demo-pass"),
        "MERIDIAN_SESSION_SECRET": _sentinel("session"),
        "MERIDIAN_EVAL_KEY": _sentinel("eval"),
    }
    env = {**secret_env, "LANGFUSE_BASE_URL": "https://langfuse.invalid", "LANGFUSE_PROJECT_ID": "proj-1"}
    sentinels = list(secret_env.values())

    settings = Settings.from_env(env)
    for sentinel in sentinels:
        assert sentinel not in repr(settings)
        assert sentinel not in str(settings)
        assert sentinel not in settings.model_dump_json()
        assert sentinel not in json.dumps(settings.role_model_map())

    bad_value = _sentinel("not-a-bool")
    logger = logging.getLogger("tests.unit.test_config")
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(SettingsError) as caught:
            try:
                Settings.from_env({**env, "MERIDIAN_COOKIE_SECURE": bad_value})
            except SettingsError:
                logger.warning("settings %r", settings)
                logger.exception("start-up failed")
                raise
        exc = caught.value
    for sentinel in [*sentinels, bad_value]:
        assert sentinel not in str(exc)
        assert sentinel not in repr(exc)
        assert sentinel not in caplog.text
    assert exc.__cause__ is None


@pytest.mark.parametrize(
    "flags",
    list(itertools.product([True, False], repeat=4)),
    ids=lambda flags: "".join("1" if f else "0" for f in flags),
)
def test_langfuse_complete_needs_all_four(flags: tuple[bool, bool, bool, bool]) -> None:
    """[invariant, AC-15] langfuse_complete() is true only when all four values are set; absent keys stay valid."""
    env = _env()
    for name, present in zip(LANGFUSE_NAMES, flags, strict=True):
        if present:
            env[name] = _sentinel(name.lower())
    settings = Settings.from_env(env)
    assert settings.langfuse_complete() is all(flags)
