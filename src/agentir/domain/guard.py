"""Guard and safety check domain models."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GuardSpec:
    """Safety guardrail or validation rule applied at input, output, or tool boundaries."""

    name: str
    stage: str  # "input", "output", "tool"
    rule_type: str  # "schema_validation", "regex_pattern", "pii_filter", "custom_callable"
    pattern_or_rule: str
    action_on_failure: str = "abort"  # "abort", "retry", "sanitize", "fallback"
    fallback_target: str | None = None
    description: str = ""
