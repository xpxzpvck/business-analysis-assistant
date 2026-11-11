---
name: review-deliverable
description: Review a completed functional increment or assignment submission against requirements, checks and documentation. Exclude unrelated questions and ordinary edits still in progress.
---

# Review deliverable

Read docs/STATUS.md, relevant rows in docs/REQUIREMENTS.md and changed artifacts. For submission, use the submission checklist in docs/REQUIREMENTS.md. For NLP changes, inspect evaluation records.

Inspect git status, the tracked diff and new files. Check scope, requirement evidence, behavior risks, secrets and documentation. Run applicable checks from AGENTS.md; environment checks are not application tests.

For runtime outputs, verify:
- tasks link to existing requirements;
- each RACI activity has exactly one accountable role;
- confirmed requirements remain distinct from proposed assumptions.

At submission, require evaluation evidence for every actual component. Missing code or runs means not run, not pass.

Report actionable findings with locations, impact and required verification. Distinguish increment readiness from overall submission readiness. Fix authorized routine issues and repeat affected checks.

Update docs/STATUS.md with actual results. Record material approved decisions in the decision log in docs/ARCHITECTURE.md. Do not publish or deploy as part of this review.