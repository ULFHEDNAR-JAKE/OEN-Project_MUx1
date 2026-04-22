---
name: bugfix-plan-drafting
description: 'Draft a bugfix plan from a failing behavior, error, file, symbol, or reproduction. Use when triaging bugs, scoping a fix, choosing validation steps, or turning an issue into a concrete implementation plan.'
argument-hint: 'Describe the bug, failing behavior, anchor file/symbol, or reproduction steps'
user-invocable: true
---

# Bugfix Plan Drafting

## What This Skill Produces

Produce a concrete bugfix plan that is ready to execute.

The output should include:
- The bug statement in one or two sentences
- The most concrete starting anchor available
- One falsifiable local hypothesis about the root cause
- One cheap check that could disconfirm that hypothesis
- The smallest safe change to test first
- A focused validation plan
- Risks, unknowns, and follow-up items

## When to Use

Use this skill when the user asks for any of the following:
- Draft a bugfix plan
- Triage a bug before editing code
- Turn an issue or failing behavior into implementation steps
- Decide where to start in a codebase
- Choose the right validation path for a suspected fix

Good triggers include phrases such as:
- "draft a bugfix plan"
- "how should I fix this bug"
- "where should I start"
- "triage this failure"
- "plan the fix before coding"

## Procedure

1. Restate the bug precisely.
Identify the failing behavior, expected behavior, and any reproduction details. If the report is vague, tighten it into a testable statement before planning further.

2. Find the strongest starting anchor.
Prefer a named file, symbol, endpoint, failing command, test, log line, or user-visible behavior. If none is given, propose the most direct place to inspect first.

3. Map only the controlling code path.
Stay narrow. Follow the path that computes, mutates, validates, or decides the failing behavior. Avoid broad repo surveys.

4. Form one falsifiable hypothesis.
State a local explanation for the failure that can be proven wrong. Prefer hypotheses tied to one condition, transformation, or control-flow decision.

5. Choose the cheapest discriminating check.
Pick the fastest validation that can falsify the hypothesis. Prefer, in order:
- Existing failing reproduction
- Narrow test for the touched behavior
- Focused compile, lint, or typecheck step
- Minimal logging or instrumentation when no better executable check exists

6. Propose the smallest first change.
Recommend the minimum safe edit that would test or resolve the suspected root cause. If uncertainty is high, prefer a reversible probe over a broad refactor.

7. Define the validation sequence.
List the exact checks to run immediately after the first change, then any adjacent follow-up validation needed if the first check passes.

8. Call out uncertainty explicitly.
Separate confirmed facts from assumptions. If key information is missing, name the missing detail and say how to obtain it.

## Decision Points

### If the bug report is underspecified
- Ask for the exact failure, expected behavior, and reproduction.
- If asking would block progress, plan around the best available anchor and note the missing details.

### If multiple code paths seem plausible
- Choose the path closest to the decision or mutation that directly controls the behavior.
- Prefer the path that supports the cheapest discriminating check.

### If no executable validation exists yet
- Use the narrowest available manual reproduction.
- If needed, include a small probe or logging step solely to expose the control-flow decision.

### If schema, config, or environment may be involved
- Include the exact environment assumption in the plan.
- Add a check that confirms the issue is code-level rather than setup-level.

## Quality Bar

A good bugfix plan is:
- Local: it starts from the nearest owning abstraction instead of a broad survey
- Falsifiable: it includes a concrete root-cause hypothesis that could be wrong
- Testable: it names the first focused validation step
- Minimal: it recommends the smallest safe first change
- Executable: another engineer could follow it without guessing what to do next

## Output Format

Use this structure when presenting the plan:

### Bug
Summarize the failure and expected behavior.

### Anchor
Name the first file, symbol, test, endpoint, or reproduction to inspect.

### Hypothesis
State one falsifiable local hypothesis.

### First Check
Name the cheapest check that could disconfirm the hypothesis.

### First Change
Describe the smallest safe edit or probe.

### Validation
List the focused post-edit checks in order.

### Risks and Unknowns
List assumptions, blockers, or adjacent areas to verify.

## Completion Check

The plan is complete when it:
- Names a concrete starting anchor
- Includes exactly one primary local hypothesis
- Includes at least one focused validation step
- Recommends a small first change instead of a broad rewrite
- Distinguishes assumptions from confirmed facts