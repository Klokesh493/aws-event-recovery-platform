# Operator runbook

## Reproduce

```sh
make verify
python3 drill.py examples/mixed-batch.json
terraform -chdir=infra init -backend=false
terraform -chdir=infra validate
```

## Triage and recovery

When the DLQ alarm fires, compare failed IDs with producer validation and receipt state. A reused job ID with changed content needs a producer fix. Correct the producer or message before authorizing replay. Compare receipt count before and after to detect duplicate processing.

## Evidence boundaries

The local drill simulates queue delivery and redrive. Terraform validated without applying resources. AWS IAM permissions, Lambda execution, and CloudWatch delivery were outside the local test.
