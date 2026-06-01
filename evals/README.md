# Evals

Per the Technical Foundation, every LLM-touching feature ships a small labelled
eval set checked in here and run on every prompt change.

Planned sets (added with their modules):

- `classification/` — labelled real-style emails per category (Support / Sales /
  Billing / Spam / Other) with expected category + urgency. Target ≥ 90%
  accuracy on top categories (PRD success metric). _(Module 3)_
- `drafting/` — thread + KB fixtures with rubric-scored expected replies and
  citation checks. _(Module 5)_
- `routing/` — rule fixtures asserting the chosen assignee / CRM action. _(Module 6)_

Each set is a small dataset + a runner that reports accuracy/score so prompt and
model changes can be compared before they ship.
