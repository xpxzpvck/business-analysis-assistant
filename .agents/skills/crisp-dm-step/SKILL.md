---
name: crisp-dm-step
description: Plan or review a CRISP-DM phase for this NLP project, producing phase artifacts and evidence-based exit criteria. Use for phase planning or reassessment, not routine code edits or generic CRISP-DM explanations.
---

# CRISP-DM step

Read docs/STATUS.md, the relevant requirements in docs/REQUIREMENTS.md, and the phase table in docs/WORKFLOW.md from the repository root. Read architecture or eval material only for the selected phase.

Identify the requested phase and whether the task is planning or review. If not specified, infer from recorded state and clearly label the choice; do not mark subsequent phases complete.

Produce:
- phase goal and requirement IDs;
- available inputs and evidence, distinguishing missing material;
- smallest next artifact and steps to produce it;
- concrete exit criteria and checks;
- open decisions and proposed next phase.

During review, map each exit criterion to actual evidence. A written plan is not proof of execution. For Data understanding, require research into existing datasets before synthetic generation. Keep unresolved product choices proposed. Update STATUS only when work was actually performed; record material approved decisions in DECISIONS.

Output a compact phase note using the fields above. If implementation is requested and already authorized, continue the agreed task; this skill itself does not authorize scope or architecture changes.
