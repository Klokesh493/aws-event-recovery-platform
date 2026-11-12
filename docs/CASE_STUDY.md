# Case study

## Problem

Retrying a whole batch because one message failed can repeat successful work. Discarding all repeats by job ID can also hide a producer bug when the ID is reused for different input.

## Implementation

A conditional write creates one receipt per job. If a duplicate arrives, a consistent read distinguishes an exact retry from a conflicting payload. The batch handler returns only failed message IDs. The drill retries those IDs until the configured receive limit and compares persisted receipts, attempts, and dead-letter IDs to expected evidence.

## Validation

Four tests passed. The fixture stored one receipt, accepted an identical retry, and sent two invalid or conflicting records to the simulated DLQ after three receives. Terraform format and validate passed with the locked AWS and archive providers.

## Limits

The local drill simulates queue delivery and redrive. Terraform validated without applying resources. AWS IAM permissions, Lambda execution, and CloudWatch delivery were outside the local test.
