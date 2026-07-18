# AI Agent Cost & Reliability normalized run contract

Version: `agent-cost-reliability.run.v1`

The $495 Snapshot accepts JSONL or CSV records with exactly the fields below. Unknown fields fail closed so prompts, responses, tool payloads, arbitrary metadata, and direct identifiers cannot pass through as accidental report content.

## Limits

- One workflow label per accepted scope.
- At most 20 pseudonymous task IDs.
- At most 50 attempts.
- One object or row per attempt.
- Unique run IDs and unique task/attempt pairs.
- Complete task histories use contiguous attempt indexes `1..N`.

## Fields

| Field | Contract |
| --- | --- |
| `schema_version` | Exactly `agent-cost-reliability.run.v1`. |
| `run_id` | Unique bounded pseudonymous identifier. |
| `task_id` | Bounded pseudonymous task identifier. |
| `attempt_index` | Positive integer. |
| `task_history_status` | `complete`, `partial`, or `unknown`. |
| `outcome` | `succeeded`, `failed`, `timed_out`, `cancelled`, or `unknown`. |
| `outcome_basis` | `external_verifier`, `scorecard`, `manual_label`, `provider_status`, `process_exit`, or `unknown`. |
| `failure_category` | Null on success; otherwise an allowlisted operational category. |
| `started_at`, `ended_at` | Timezone-aware timestamps or null. |
| `duration_ms` | Nonnegative integer or null; when timestamps and duration are all present, they must agree within 1 ms. |
| `provider`, `model`, `workflow`, `role` | Bounded pseudonymous identifier strings, not free text. |
| `input_tokens`, `cached_input_tokens`, `output_tokens` | Nonnegative integers or null. |
| `model_calls`, `tool_calls` | Nonnegative integers or null. |
| `cost_amount` | Decimal string with at most six fractional places, never a JSON float. |
| `cost_status` | `complete`, `partial`, or `missing`. |
| `cost_basis` | `provider_billed`, `rate_card`, `manual`, `unknown`, or null when cost is missing. |
| `cost_currency` | `USD` or null when cost is missing. No currency conversion is performed. |
| `source_format` | Bounded versioned source-adapter identifier. |

## Privacy boundary

The contract has no field for prompts, responses, tool arguments or results, credentials, names, email addresses, customer identifiers, production URLs, or free-form metadata. Do not encode those values into pseudonymous fields. The requester is responsible for de-identifying the normalized records before private transfer.

Do not attach run records to the public GitHub scope issue. WrightOps confirms the contract and transfer boundary in writing before accepting data or requesting payment.

## Missing evidence

Missing is not zero. Use null or the documented unknown/missing status when an outcome, timestamp, usage, cost, or task history is not known. A primary metric remains unavailable when the required evidence is incomplete.

## Example JSONL row

```json
{"schema_version":"agent-cost-reliability.run.v1","run_id":"run-001","task_id":"task-001","attempt_index":1,"task_history_status":"complete","outcome":"succeeded","outcome_basis":"external_verifier","failure_category":null,"started_at":"2026-07-01T12:00:00Z","ended_at":"2026-07-01T12:00:02Z","duration_ms":2000,"provider":"provider-a","model":"model-a","workflow":"workflow-a","role":"worker","input_tokens":800,"cached_input_tokens":0,"output_tokens":100,"model_calls":1,"tool_calls":2,"cost_amount":"0.080000","cost_status":"complete","cost_basis":"provider_billed","cost_currency":"USD","source_format":"normalized-export.v1"}
```

This example is synthetic and is not a customer record or claimed business result.
