.PHONY: help install test build synth deploy-merchant destroy-merchant setup-agent run-agent teardown-agent clean demo-preflight demo-provider demo-agent

help:
	@echo "Targets:"
	@echo "  install           Install all dependencies (pnpm + uv)"
	@echo "  test              Run all tests (TS + Python)"
	@echo "  build             Build TypeScript packages"
	@echo "  synth             Synth merchant CDK"
	@echo "  deploy-merchant   Deploy the merchant to AWS"
	@echo "  destroy-merchant  Destroy the merchant CloudFormation stack"
	@echo "  setup-agent       Bootstrap AgentCore resources (one-time)"
	@echo "  run-agent         Run the agent against the merchant"
	@echo "  teardown-agent    Delete AgentCore resources"
	@echo "  clean             Remove node_modules, .venv, build artifacts"
	@echo "  demo-preflight    Live-demo prep: refresh session + smoke-test"
	@echo "  demo-provider     Live-demo segment 3: the 402 / payment terms"
	@echo "  demo-agent        Live-demo segment 4: pay + settle on Arbitrum One"

install:
	pnpm install
	cd apps/agent && uv sync

test:
	pnpm test
	cd apps/agent && uv run pytest

build:
	pnpm build

synth:
	pnpm synth

deploy-merchant:
	pnpm deploy:merchant

destroy-merchant:
	pnpm destroy:merchant

setup-agent:
	cd apps/agent && uv run x402-aws-agent-setup

run-agent:
	cd apps/agent && uv run x402-aws-agent-run

teardown-agent:
	cd apps/agent && uv run x402-aws-agent-teardown

demo-preflight:
	cd apps/agent && uv run python ../../scripts/demo.py preflight

demo-provider:
	cd apps/agent && uv run python ../../scripts/demo.py provider

demo-agent:
	cd apps/agent && uv run python ../../scripts/demo.py agent

clean:
	rm -rf node_modules apps/*/node_modules packages/*/node_modules
	rm -rf apps/merchant/cdk.out apps/merchant/dist packages/*/dist
	rm -rf apps/agent/.venv apps/agent/.pytest_cache
	rm -rf apps/agent/src/x402_aws_agent/__pycache__ apps/agent/tests/__pycache__
