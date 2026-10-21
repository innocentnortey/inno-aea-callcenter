"""The one typed `Settings`, the role maps and their start-up validation (AEA-02; graph-core section 12, DO-4 12).

Built once by the container's caller from the environment; never a module-level singleton and never touches the
database. Every secret is a `SecretStr`. A start-up refusal names variables, codes and rules, never a value.
No numeric limit lives here (those are `policy/limits.py`).
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal

from pydantic import Field, SecretStr, ValidationError, model_validator
from pydantic_core import PydanticCustomError

from meridian.domain.common import MeridianModel, SafeError
from meridian.ports.models import ChoiceRole, Role, StructuredRole, ToolRole
from meridian.privacy.redact import RedactionProfile

JEV_MODEL = "typesafe/jev-1.13"  # models.md section 2 JEV_PRICES key
SONNET_MODEL = "claude-sonnet-5-5"  # models.md section 2 ANTHROPIC_PRICES key


class RoleSpec(MeridianModel):
    """DO-4 section 12."""

    model: str
    effort: Literal["low", "medium", "high"] | None
    cap_s: float
    max_tokens: int
    redaction: RedactionProfile


class ModelSettings(MeridianModel):
    """DO-4 section 12. Jev is legal only in the choice map."""

    choice: dict[ChoiceRole, tuple[Literal["openrouter_jev", "anthropic"], RoleSpec]]
    structured: dict[StructuredRole, tuple[Literal["anthropic"], RoleSpec]]
    tools: dict[ToolRole, tuple[Literal["anthropic"], RoleSpec]]

    @model_validator(mode="after")
    def _every_role_once(self) -> ModelSettings:
        expected: tuple[tuple[set[Role], set[Role]], ...] = (
            ({Role.PLANNER, Role.CLASSIFIER, Role.PLANNER_FALLBACK}, set(self.choice)),
            ({Role.RESPONDER, Role.BRIEF}, set(self.structured)),
            ({Role.SPECIALIST}, set(self.tools)),
        )
        missing = {role for wanted, present in expected for role in wanted - present}
        if missing:
            raise PydanticCustomError(
                "missing_role",
                "every role needs one entry in its own map; missing: {missing}",
                {"missing": ", ".join(sorted(role.value for role in missing))},
            )
        return self


def default_model_settings() -> ModelSettings:
    """The code defaults (DO-1 section 8.1 caps; SP-1 option B for effort and max tokens)."""
    return ModelSettings(
        choice={
            Role.PLANNER: (
                "openrouter_jev",
                RoleSpec(
                    model=JEV_MODEL,
                    effort=None,
                    cap_s=3.0,  # proposal (DO-1 section 8.1)
                    max_tokens=1500,
                    redaction=RedactionProfile.JEV,
                ),
            ),
            Role.CLASSIFIER: (
                "openrouter_jev",
                RoleSpec(
                    model=JEV_MODEL,
                    effort=None,
                    cap_s=3.0,  # proposal (DO-1 section 8.1)
                    max_tokens=800,
                    redaction=RedactionProfile.JEV,
                ),
            ),
            Role.PLANNER_FALLBACK: (
                "anthropic",
                RoleSpec(
                    model=SONNET_MODEL,
                    effort="low",
                    cap_s=8.0,  # [A] plan decision D-10
                    max_tokens=1500,
                    redaction=RedactionProfile.SONNET,
                ),
            ),
        },
        structured={
            Role.RESPONDER: (
                "anthropic",
                RoleSpec(
                    model=SONNET_MODEL,
                    effort="low",
                    cap_s=12.0,  # proposal (DO-1 section 8.1)
                    max_tokens=1500,
                    redaction=RedactionProfile.SONNET,
                ),
            ),
            Role.BRIEF: (
                "anthropic",
                RoleSpec(
                    model=SONNET_MODEL,
                    effort="low",
                    cap_s=12.0,  # proposal (DO-1 section 8.1)
                    max_tokens=1200,
                    redaction=RedactionProfile.SONNET,
                ),
            ),
        },
        tools={
            Role.SPECIALIST: (
                "anthropic",
                RoleSpec(
                    model=SONNET_MODEL,
                    effort="medium",
                    cap_s=8.0,  # proposal (DO-1 section 8.1)
                    max_tokens=3000,
                    redaction=RedactionProfile.SONNET,
                ),
            ),
        },
    )


ENV_NAMES: Mapping[str, str] = MappingProxyType(
    {
        "anthropic_api_key": "ANTHROPIC_API_KEY",
        "openrouter_api_key": "OPENROUTER_API_KEY",
        "langfuse_public_key": "LANGFUSE_PUBLIC_KEY",
        "langfuse_secret_key": "LANGFUSE_SECRET_KEY",
        "langfuse_base_url": "LANGFUSE_BASE_URL",
        "langfuse_project_id": "LANGFUSE_PROJECT_ID",
        "demo_username": "MERIDIAN_DEMO_USERNAME",
        "demo_password": "MERIDIAN_DEMO_PASSWORD",
        "session_secret": "MERIDIAN_SESSION_SECRET",
        "eval_key": "MERIDIAN_EVAL_KEY",
        "cookie_secure": "MERIDIAN_COOKIE_SECURE",
        "trust_proxy_headers": "MERIDIAN_TRUST_PROXY_HEADERS",
        "web_dist_dir": "MERIDIAN_WEB_DIST_DIR",
        "require_frontend": "MERIDIAN_REQUIRE_FRONTEND",
        "data_dir": "MERIDIAN_DATA_DIR",
        "index_dir": "MERIDIAN_INDEX_DIR",
        "agent_version": "MERIDIAN_AGENT_VERSION",
    }
)  # 17 names; `models` and `issued_db_path` have none


class SettingsError(ValueError):
    """Start-up refusal. Names variables, codes and rules; never a value."""

    def __init__(self, problems: tuple[SafeError, ...]) -> None:
        self.problems = problems
        super().__init__(
            "invalid settings: " + "; ".join(f"{p.field}: {p.code} ({p.constraint})" for p in problems)
        )


def _nonblank(secret: SecretStr | None) -> bool:
    return secret is not None and bool(secret.get_secret_value().strip())


class Settings(MeridianModel):
    """graph-core section 12, exactly these fields."""

    anthropic_api_key: SecretStr
    openrouter_api_key: SecretStr
    models: ModelSettings = Field(default_factory=default_model_settings)
    langfuse_public_key: SecretStr | None = None
    langfuse_secret_key: SecretStr | None = None
    langfuse_base_url: str | None = None
    langfuse_project_id: str | None = None
    demo_username: SecretStr
    demo_password: SecretStr
    session_secret: SecretStr
    eval_key: SecretStr | None = None
    cookie_secure: bool = False
    trust_proxy_headers: bool = False
    web_dist_dir: Path = Path("apps/web/dist")
    require_frontend: bool = False
    data_dir: Path = Path("var")
    index_dir: Path = Path("var/index")
    issued_db_path: Path = Path("docs/data/issued/meridian_dataset/scheduling_db/meridian_scheduling.sqlite")
    agent_version: str = "dev"

    @classmethod
    def from_env(cls, environ: Mapping[str, str]) -> Settings:
        """Build from a mapping the caller passes once (never reads os.environ itself).

        Only the 17 names are read; a blank value counts as unset. A failure raises `SettingsError`, which names
        the variable and the rule and drops the pydantic exception (whose errors hold inputs) from the chain.
        """
        data = {
            field_name: environ[env_name]
            for field_name, env_name in ENV_NAMES.items()
            if env_name in environ and environ[env_name].strip()
        }
        try:
            return cls.model_validate(data)
        except ValidationError as exc:
            problems = tuple(
                SafeError(
                    field=ENV_NAMES.get(problem.field.split(".")[0], problem.field),
                    code=problem.code,
                    constraint=problem.constraint,
                )
                for problem in SafeError.from_validation_error(exc)
            )
            raise SettingsError(problems) from None

    def role_model_map(self) -> Mapping[str, Any]:
        """Plain JSON-safe role settings for `compute_agent_version`; no secrets (data.md section 7)."""
        entries: dict[str, Any] = {}
        pairs = (*self.models.choice.items(), *self.models.structured.items(), *self.models.tools.items())
        for role, (provider, spec) in pairs:
            entries[role.value] = {
                "provider": provider,
                "model": spec.model,
                "effort": spec.effort,
                "cap_s": spec.cap_s,
                "max_tokens": spec.max_tokens,
                "redaction": spec.redaction.value,
            }
        return {key: entries[key] for key in sorted(entries)}

    def langfuse_complete(self) -> bool:
        """True only when all four LANGFUSE_* values are set and non-blank."""
        return (
            _nonblank(self.langfuse_public_key)
            and _nonblank(self.langfuse_secret_key)
            and bool(self.langfuse_base_url and self.langfuse_base_url.strip())
            and bool(self.langfuse_project_id and self.langfuse_project_id.strip())
        )
