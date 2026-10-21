"""Every shared numeric limit in one place (DO-3 §4.1; merge-clashes MC-22).

The composition root (web/container.py) builds ONE frozen ``Limits``. GraphDeps.limits and ModelGateway(..., limits=...)
receive it whole (DO-4 §2, §12, §14); every other consumer receives the part it needs from the container. No other module
holds a second literal for any value here. Standard library only (DO-3 §4.1 "depends on: none").

Labels: [Decided X] a recorded decision this file only applies; proposal: a choice awaiting Innocent; [A] an assumption,
with the measurement that replaces it; [T] a target.

Not here, on purpose: the per-role model call caps (RoleSpec.cap_s in AEA-02's config.py ModelSettings defaults,
DO-4 §12); the CON-3/CON-21 stream constants STREAM_POLL_S and STREAM_HEARTBEAT_S (web.md §11, AEA-41); the stream
CapacityLimiter(4) (web.md §4, AEA-23).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TurnLimits:
    """One customer turn's time budget, and the CON-1 timing values the browser reads (api-con-mapping §0)."""

    deadline_s: int = 60  # [Decided SDQ-1] the per-turn deadline (DO-4 §2 TurnBudget; DO-3 §2.3)
    still_working_after_ms: int = 10_000  # CON-1; SCREEN_SPECS SCR-1 "Still working on this…" at about 10 s
    browser_grace_s: int = 5  # [A] DO-3 §2.3 rule 5: the browser waits deadline + 5 s; replaced by the
    #   Railway proxy-timeout check at first deploy (A12)
    max_message_chars: int = 2_000  # CON-1; the OpenAPI TextPayload maxLength

    @property
    def turn_deadline_ms(self) -> int:
        """CON-1 ``turn_deadline_ms``: the one deadline in milliseconds (60000), never typed twice."""
        return self.deadline_s * 1_000

    @property
    def browser_give_up_after_ms(self) -> int:
        """CON-1 ``browser_give_up_after_ms`` [A]: deadline plus the browser grace, in milliseconds (65000)."""
        return (self.deadline_s + self.browser_grace_s) * 1_000


@dataclass(frozen=True)
class Admission:
    """How many customer turns may run at once (DO-3 §2.3)."""

    max_in_flight: int = 30  # [Decided SDQ-9] turn 31 gets BUSY with the person key and no model call


@dataclass(frozen=True)
class Brakes:
    """Loop brakes inside one turn (R-41; agent-architecture rules 5, 15). All three are proposals."""

    tasks_per_turn: int = 3  # proposal (code-design §4.1; DO-4 §4 Plan.tasks max_length=3)
    tool_rounds: int = 2  # proposal (graph-tools C-9; the specialist runner's tool loop)
    sonnet_calls: int = (
        6  # proposal (models.md cross-topic 3; SP-1 mix B reached exactly 6 in 7 of 192 turns [M])
    )


@dataclass(frozen=True)
class IdentityLimits:
    """One-time code limits (R-15; graph-tools §5, C-9)."""

    code_ttl_s: int = 600  # [Decided R-15] 10-minute expiry
    tries: int = 3  # [Decided R-15] 3 attempts
    max_sends: int = 3  # proposal [A] at most 3 codes sent per conversation (DO-4 §14 IdentityService)


@dataclass(frozen=True)
class BookingLimits:
    """The R-41 booking cap (DO-4 §1 FailureCounters.bookings; ToolErrorCode booking_cap)."""

    max_per_conversation: int = 3  # proposal (code-design §4.1)


@dataclass(frozen=True)
class SpendLimits:
    """Our model-spend cap (models.md §6). Limits.spend, beside Limits.web."""

    daily_cap_usd: float = 30.0  # our cap, US dollars per America/Chicago day
    #   [T] system design §2 "$30/day" (Q-061; DO-7 M-26); the ONE literal


@dataclass(frozen=True)
class WebLimits:
    """Rate limits and session timing for the web shell (web.md §5; WEB-2, WEB-4, WEB-5; MC-14, MC-22).

    Each [A] is "set above 20" (PRD §5) for the 20-at-once load, and is replaced by the E-8 load re-measure at Stage 9
    (0 limited responses at 20 conversations from one IP and one login) and by abuse seen in the deploy logs.
    """

    chat_turns_per_thread_per_min: int = 20  # [A] a person types far fewer; one scripted case has ≤ ~10 turns
    chat_turns_per_session_per_min: int = (
        600  # [A] 20 closed-loop conversations at SP-1's p50 4.7 s ≈ 255/min [C], ×2
    )
    chat_turns_per_ip_per_min: int = (
        600  # [A] same arithmetic: the harness and a reviewer's office share one IP
    )
    reads_per_session_per_min: int = (
        120  # [A] apps/web polls the demo status every 10 s per open tab (POLL_MS)
    )
    reads_per_ip_per_min: int = 240  # [A]
    login_rejects_per_ip: int = 10  # [A] rejected attempts per window; while over, every attempt (even the
    login_reject_window_s: int = (
        600  #   right pair) answers 429 LOGIN_RATE_LIMITED + Retry-After (AEA-23 AC-5)
    )
    resets_per_ip: int = 10  # [A] per window; never reached by a reviewer, so not a cool-down (R-48)
    reset_window_s: int = 600
    login_session_lifetime_s: int = 43_200  # 12 h absolute, no idle timeout [Decided §7, engineering; WEB-5]
    reset_wait_s: int = 5  # [A] [Source: UI_CONTRACTS *Still open* "the 5 s reset-lock wait"] (web.md §7)


@dataclass(frozen=True)
class ContextLimits:
    """Chat window limits (graph-core §7; GRC-9, GRC-14). Replaced by the first full eval run (E-1, E-2)."""

    window_turns: int = 10  # [A] R-45 "about 10". Lines of the last 10 turn_ids, plus representative and
    #   event lines (turn_id None) since the oldest kept turn
    window_line_chars: int = 600  # [A] each ChatLine cut to 600 chars with "…"
    window_total_chars: int = 8_000  # [A] oldest lines dropped first until the window fits
    planner_lines: int = 6  # [A, SP-1] DO-4 §3: the planner's recent_chat, taken from the same window
    planner_line_chars: int = 400  # [A, SP-1]


@dataclass(frozen=True)
class Limits:
    """The one frozen set of shared limits (MC-22), built once by web/container.py."""

    turn: TurnLimits = field(default_factory=TurnLimits)
    admission: Admission = field(default_factory=Admission)
    brakes: Brakes = field(default_factory=Brakes)
    identity: IdentityLimits = field(default_factory=IdentityLimits)
    booking: BookingLimits = field(default_factory=BookingLimits)
    spend: SpendLimits = field(default_factory=SpendLimits)
    web: WebLimits = field(default_factory=WebLimits)
    context: ContextLimits = field(default_factory=ContextLimits)
