# Free router replacement — 2026-11-15

- Scope: user explicitly requested replacing fixed Ling with free models, without additional controls. Requirements BA-04–07, SYS-01 and OPS-01; scenarios S01, S06–08.
- Baseline: inclusionai/ling-3.2-flash:free. Candidate: openrouter/free, which selects a compatible free model per request. No deterministic underlying model identity is claimed.
- Prompts unchanged (analyzer_v2, generator_v2, schema_repair_v1); token cap 4096, analysis deadline 60s, generation deadline 180s, default one attempt per action, zero-price provider filters and strict local validators retained. No tools, plugins or paid fallback added.
- Existing in-memory Ling sessions are migrated on rerun, preserving credentials/settings, dialogue, review state and records; migration makes no HTTP request. New configuration accepts only the approved free-router ID.
- Actual checks: 136 tests passed in 10.51s; Ruff and environment checker PASS. Request test asserts literal openrouter/free and unchanged zero-price filters; migration regression checks state preservation and no request. The first full run had one obsolete assertion requiring the :free suffix; updated it to the explicit router ID and reran successfully.
- Structural evidence uses mocked HTTP, not NLP scores. Live routing compatibility, latency, actual selected models and semantic quality comparison NOT RUN. No API credentials or private traces captured. Free-model availability and schema adherence remain unproven for this application.
- Next experiment: run the existing confirmed development dialogue through generation; compare schema validity, requirement coverage, unsupported claims and RACI validity against the fixed-model baseline when available. Do not use held-out data for tuning.
- Source: [OpenRouter free-router documentation](https://github.com/OpenRouterTeam/docs/blob/main/guides/routing/routers/free-router.mdx), checked 2026-11-15.
