#!/usr/bin/env bash
# AgentIR v0.1 CLI Demo Walkthrough Script
set -e

echo "=================================================="
echo "      AgentIR — Autonomous CLI Demo Walkthrough"
echo "=================================================="

echo -e "\n1. Displaying AgentIR Version..."
agentir version

echo -e "\n2. Running System Environment Diagnostics (doctor)..."
agentir doctor

echo -e "\n3. Inspecting Declared Capabilities for LangGraph..."
agentir capabilities --framework langgraph

echo -e "\n4. Validating Example Manifests..."
agentir validate examples/customer_support_langgraph.yaml
agentir validate examples/research_team_agno.yaml
agentir validate examples/triage_openai_agents.yaml

echo -e "\n5. Inspecting Customer Support Manifest..."
agentir inspect examples/customer_support_langgraph.yaml

echo -e "\n6. Analyzing Compatibility Against Agno..."
agentir check examples/customer_support_langgraph.yaml --target agno || true

echo -e "\n7. Executing End-to-End Migration (LangGraph -> Agno)..."
rm -rf /tmp/demo_migrated_agno
agentir migrate tests/fixtures/langgraph/sample_graph.yaml \
  --from langgraph \
  --to agno \
  -o /tmp/demo_migrated_agno \
  --force

echo -e "\nGenerated Migration Artifacts:"
ls -l /tmp/demo_migrated_agno

echo -e "\n8. Computing Semantic Diff (Support System vs Research Team)..."
agentir diff examples/customer_support_langgraph.yaml examples/research_team_agno.yaml || true

echo -e "\n9. Verifying Integrity and Security Policies..."
agentir verify examples/customer_support_langgraph.yaml

echo -e "\n=================================================="
echo "          Demo Completed Successfully!"
echo "=================================================="
