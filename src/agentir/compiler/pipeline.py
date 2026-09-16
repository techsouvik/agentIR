"""AgentIR Migration Compiler and pipeline coordinator."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agentir.adapters.registry import get_adapter
from agentir.capabilities.analyzer import analyze_compatibility
from agentir.capabilities.status import CompatibilityReport, SemanticLossRisk
from agentir.domain.exceptions import CompatibilityError
from agentir.domain.manifest import AgentIRManifest
from agentir.schema.canonical import compute_canonical_hash


@dataclass(frozen=True, slots=True)
class MigrationPlan:
    """Evaluated execution plan for a framework migration."""

    target_framework: str
    compatibility: CompatibilityReport
    can_proceed: bool
    warnings: tuple[str, ...] = field(default_factory=tuple)
    blocked_reasons: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class MigrationResult:
    """Outcome of an AgentIR compilation and export operation."""

    success: bool
    target_framework: str
    output_directory: Path
    generated_files: tuple[Path, ...]
    plan: MigrationPlan
    report_path: Path | None = None
    report_json_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "target_framework": self.target_framework,
            "output_directory": str(self.output_directory),
            "generated_files": [str(p) for p in self.generated_files],
            "score": round(self.plan.compatibility.score, 1),
            "can_proceed": self.plan.can_proceed,
            "warnings": list(self.plan.warnings),
            "blocked_reasons": list(self.plan.blocked_reasons),
            "report_path": str(self.report_path) if self.report_path else None,
            "report_json_path": str(self.report_json_path) if self.report_json_path else None,
        }


def plan_migration(
    manifest: AgentIRManifest,
    target_framework: str,
    force: bool = False,
) -> MigrationPlan:
    """Plan a migration by analyzing target compatibility and invariants."""
    manifest.validate_invariants()
    compatibility = analyze_compatibility(manifest, target_framework)

    warnings: list[str] = []
    blocked_reasons: list[str] = []

    for item in compatibility.emulated:
        warnings.append(
            f"Capability '{item.capability_id}' will be emulated in {target_framework}: "
            f"{item.emulation_strategy}"
        )

    for item in compatibility.adapter:
        warnings.append(
            f"Capability '{item.capability_id}' requires adapter shim: "
            f"{item.required_adapter_shim or item.description}"
        )

    for item in compatibility.unsupported:
        msg = (
            f"Target framework does not support capability '{item.capability_id}': "
            f"{item.description}"
        )
        if item.semantic_loss_risk in (SemanticLossRisk.HIGH, SemanticLossRisk.CRITICAL):
            blocked_reasons.append(msg)
        else:
            warnings.append(msg)

    can_proceed = len(blocked_reasons) == 0 or force

    return MigrationPlan(
        target_framework=target_framework,
        compatibility=compatibility,
        can_proceed=can_proceed,
        warnings=tuple(warnings),
        blocked_reasons=tuple(blocked_reasons),
    )


def compile_migration(
    manifest: AgentIRManifest,
    target_framework: str,
    output_directory: Path | str,
    force: bool = False,
    generate_report: bool = True,
) -> MigrationResult:
    """Compile an AgentIR manifest to the target framework and emit artifacts.

    Raises:
        CompatibilityError: If compatibility check fails and force is False.
    """
    out_dir = Path(output_directory).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    plan = plan_migration(manifest, target_framework, force=force)

    if not plan.can_proceed:
        msg = (
            f"Cannot migrate manifest '{manifest.name}' to '{target_framework}' due to "
            f"{len(plan.blocked_reasons)} blocking incompatibility issue(s). "
            f"Use force=True to compile anyway with degraded semantics."
        )
        raise CompatibilityError(
            msg,
            {
                "target": target_framework,
                "blocked_reasons": list(plan.blocked_reasons),
                "warnings": list(plan.warnings),
            },
        )

    adapter = get_adapter(target_framework)
    generated_files = list(adapter.export_manifest(manifest, out_dir))

    report_path: Path | None = None
    report_json_path: Path | None = None

    if generate_report:
        report_md, report_data = _generate_migration_report(manifest, plan, generated_files)

        report_path = out_dir / "MIGRATION_REPORT.md"
        report_path.write_text(report_md, encoding="utf-8")
        generated_files.append(report_path)

        report_json_path = out_dir / "migration_report.json"
        report_json_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
        generated_files.append(report_json_path)

    return MigrationResult(
        success=True,
        target_framework=target_framework,
        output_directory=out_dir,
        generated_files=tuple(generated_files),
        plan=plan,
        report_path=report_path,
        report_json_path=report_json_path,
    )


def _generate_migration_report(
    manifest: AgentIRManifest,
    plan: MigrationPlan,
    generated_files: list[Path],
) -> tuple[str, dict[str, Any]]:
    """Generate Markdown and JSON migration audit reports."""
    canonical_hash = compute_canonical_hash(manifest)
    comp = plan.compatibility

    report_lines: list[str] = [
        f"# AgentIR Migration Audit Report — {manifest.name}",
        "",
        f"- **Source System**: {manifest.name} (`{manifest.ir_version}`)",
        f"- **Canonical Hash**: `{canonical_hash}`",
        f"- **Target Framework**: `{plan.target_framework}`",
        f"- **Compatibility Score**: **{comp.score:.1f}%**",
        f"- **Migration Status**: {'SUCCESS' if plan.can_proceed else 'BLOCKED'}",
        "",
        "## 1. Capabilities Summary",
        "",
        f"- **Total Required Capabilities**: {len(comp.required_capabilities)}",
        f"- **Native**: {len(comp.native)}",
        f"- **Adapter Bridged**: {len(comp.adapter)}",
        f"- **Emulated**: {len(comp.emulated)}",
        f"- **Unsupported**: {len(comp.unsupported)}",
        "",
        "### Native Matches",
    ]

    for n in comp.native:
        report_lines.append(f"- `✓` **{n.capability_id}**: Natively supported.")

    if comp.adapter:
        report_lines.append("\n### Adapter-Bridged Capabilities")
        for a in comp.adapter:
            report_lines.append(f"- `⚙` **{a.capability_id}**: {a.description}")

    if comp.emulated:
        report_lines.append("\n### Emulated Capabilities (Semantic Risk Warning)")
        for e in comp.emulated:
            risk = e.semantic_loss_risk.value.upper()
            report_lines.append(
                f"- `⚠` **{e.capability_id}** (Risk: {risk}): {e.emulation_strategy}"
            )

    if comp.unsupported:
        report_lines.append("\n### Unsupported Capabilities")
        for u in comp.unsupported:
            risk = u.semantic_loss_risk.value.upper()
            report_lines.append(
                f"- `✗` **{u.capability_id}** (Risk: {risk}): {u.description}"
            )

    report_lines.extend(
        [
            "",
            "## 2. Generated Artifacts",
            "",
        ]
    )
    for f in generated_files:
        report_lines.append(f"- `{f.name}`")

    report_lines.extend(
        [
            "",
            "## 3. Recommended Manual Actions",
            "",
        ]
    )
    if comp.required_actions:
        for action in comp.required_actions:
            report_lines.append(f"1. {action}")
    else:
        report_lines.append("No manual migration actions required. Code is ready to run.")

    report_data = {
        "manifest_name": manifest.name,
        "canonical_hash": canonical_hash,
        "target_framework": plan.target_framework,
        "score": comp.score,
        "is_compatible": plan.can_proceed,
        "compatibility": comp.to_dict(),
        "generated_files": [f.name for f in generated_files],
    }

    return "\n".join(report_lines) + "\n", report_data
