# Skills and verification

## What this repository demonstrates

SQS partial batch response, DynamoDB conditional receipts, Terraform validation, and dead-letter recovery.

## Reproduce the result

Run `make verify`, then `python3 drill.py examples/mixed-batch.json`. Expect one receipt and two simulated dead-letter records after three receives.

Run `make verify` locally. Ruff and Bandit medium/high checks passed for the checked Python code.

## Scope

The queue drill uses SQLite. Infrastructure coverage is Terraform configuration validation.

[drill.py](../drill.py) · [handler.py](../handler.py) · [Architecture](../docs/ARCHITECTURE.md) · [Case study](../docs/CASE_STUDY.md) · [Runbook](../docs/RUNBOOK.md)

[GitHub Actions CI template](github-actions/ci.yml)
