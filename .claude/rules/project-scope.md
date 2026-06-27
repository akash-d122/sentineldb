# Project Scope Rules

## V1A Only Until Tests Pass
Build only local proof-of-life components first:
- guardrails,
- core models,
- RCA renderer,
- simulated incident flow.

Do not implement dashboard, Jira, Slack, CloudWatch, PMM, LangGraph, SaaS, billing, auth, or multi-tenancy until the local RCA pipeline works.

## Required Behavior
Every implementation must support the product goal:
> produce a safe, evidence-backed RCA for one DB alert.

If a task does not directly support this goal, defer it.
