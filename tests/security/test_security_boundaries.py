"""Security tests verifying isolation, safe parsing, and traversal prevention."""

import pytest

from agentir.analysis.verification import verify_manifest
from agentir.domain.agent import AgentSpec
from agentir.domain.exceptions import AgentIRValidationError, SecurityError
from agentir.domain.instructions import InstructionsSpec
from agentir.domain.manifest import AgentIRManifest
from agentir.domain.model import ModelSpec
from agentir.schema.serializer import (
    deserialize_manifest_from_yaml,
    load_manifest_from_file,
)


def test_malicious_python_object_tag_rejected() -> None:
    """YAML safe loader must strictly reject !!python/object tags and code execution."""
    malicious_yaml = """
name: Exploit
ir_version: "0.1.0"
agents:
  - id: evil
    name: !!python/object/apply:os.system ["echo pwned"]
    model:
      provider: openai
      model_id: gpt-4o
    instructions:
      system_prompt: Attack
"""
    with pytest.raises(AgentIRValidationError) as exc:
        deserialize_manifest_from_yaml(malicious_yaml)
    assert "Invalid YAML" in str(exc.value) or "tag" in str(exc.value).lower()


def test_oversized_payload_dos_protection() -> None:
    """Payloads exceeding 10MB must be rejected with SecurityError before parsing."""
    large_comment = "# " + ("A" * (11 * 1024 * 1024)) + "\nname: Giant\n"
    with pytest.raises(SecurityError) as exc:
        deserialize_manifest_from_yaml(large_comment)
    assert "maximum allowed size" in str(exc.value)


def test_secret_detection_blocks_bearer_and_sk_keys() -> None:
    """Manifests containing raw API keys in instructions or metadata must be flagged."""
    agent = AgentSpec(
        id="leaky",
        name="Leaky Agent",
        model=ModelSpec(provider="openai", model_id="gpt-4o"),
        instructions=InstructionsSpec(
            system_prompt=(
                "Use Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-ID to authenticate."
            )
        ),
        metadata={"api_key": "sk-proj-abc1234567890abcdef12345"},
    )
    manifest = AgentIRManifest(name="Leaky App", agents=(agent,))
    report = verify_manifest(manifest)

    assert report.is_valid is False
    assert any("secret_detection" in c.name and not c.passed for c in report.checks)


def test_missing_file_path_safe_error() -> None:
    """Non-existent file raises FileNotFoundError rather than crash."""
    with pytest.raises(FileNotFoundError):
        load_manifest_from_file("/path/that/does/not/exist/agentir.yaml")
