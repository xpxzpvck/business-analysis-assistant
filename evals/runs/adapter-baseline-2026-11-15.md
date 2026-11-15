# OpenRouter adapter structural baseline

Executed 2026-11-15; OPS-01 / S08. This is the first adapter baseline, with no live model or semantic evaluation.

- Code: HEAD `342c006b72f96f49476cc38a5853f91649be8be9`, dirty working tree with earlier uncommitted core/data/docs changes. Added `ba_assistant/openrouter.py` and `tests/test_openrouter.py`; uv added HTTPX 0.28.1 and locked dependencies.
- Environment: Windows, Python 3.14.7, uv 0.12.15; exact dependencies in uv.lock.
- Data: authored HTTP envelopes and exceptions in `tests/test_openrouter.py`; all requests handled by `httpx.MockTransport`. No development/held-out NLP cases were sent to a provider. Fixture model ID `example/fixed` and key `test-only-key` are dummy values, not a selected model or credential.
- Configuration: two attempts maximum, 60-second deadline per attempt by default; test deadline case uses 0.01 seconds and one attempt. Default max_tokens 4096; streaming disabled; fixed model, no provider fallback. No sampling/prompt tuning occurred.
- Commands: `uv run --frozen --no-sync pytest -q`; `uv run --frozen --no-sync ruff check .`.
- Results: 69/69 tests passed, zero failures, pytest reported 1.23 seconds. 34 adapter cases plus the unchanged 35 core/data cases. Ruff passed. The earlier core-only baseline had 35/35; the changed denominator reflects new transport coverage, not an NLP improvement.
- Coverage: valid request/schema/routing and usage; 429/500/502/503 retry; 400/401/402/403/404/422/302 non-retry; exhausted network/timeouts and HTTP failure; malformed envelopes/JSON/schema output; refusals/truncation; HTTP-200 error envelope; bounded Retry-After; overall deadline cancellation; caller cancellation; missing configuration; secret masking; no gold fields in request messages; failed provider request preserves pending Session.
- Review changes: guarded non-object `message` envelopes so malformed data yields ProviderError rather than AttributeError; removed an unused import flagged by Ruff. Regression cases cover null/string message objects.
- Privacy evidence: errors contain only category/status/attempt count; provider response text containing dummy key/private marker is absent from surfaced error text. Real secret handling was not tested with real credentials.
- Limitations: no live endpoint compatibility, provider latency, token/cost measurement or semantic score. Usage reflects only the final successful response, not failed-attempt charges. Strict-schema support varies by selected endpoint. HTTP transport cancellation cannot guarantee the remote provider stopped processing. No analyzer/generator prompt or UI integration yet. This is not a clean-checkout or deployment check.
- Review used evaluate-component and review-deliverable; no independent human code review claimed. Next: connect analyzer/generator contracts to the adapter with mocked end-to-end flows, then choose model/budget before a live development baseline.
