---
name: write-feature-spec
description: Interview the user about a feature idea until there's enough information to write a description, acceptance criteria, and dev notes. Use when the user has a feature idea and wants to refine it into a clear spec.
---

# Skill: write-feature-spec

Interview the user relentlessly about their feature idea until there is enough information to produce a clear spec. The output is raw markdown in a code block with three sections: Description, Acceptance Criteria, and Dev Notes.

## Phase 1: Understand the codebase

Before asking questions, explore the codebase to understand the current state of the area the feature touches. Look at:

- Database schema (`migrations/up/` and `docs/schema.md`)
- Backend models, handlers, and services (`backend/app/features/`)
- Frontend components and hooks (`frontend/src/`)
- Existing tests (`backend/tests/`, `frontend/src/`)

This lets you ask informed questions instead of asking the user things you could discover yourself.

## Phase 2: Interview

Ask questions one at a time. For each question, provide your recommended answer. Cover these topics in a natural order — don't follow this list rigidly, but make sure every branch gets resolved:

1. **Problem statement**: What's the user's pain point or goal?
2. **Scope**: What's in and what's out? Where are the boundaries?
3. **Security and authorization**: Who can access this? Are there permission boundaries? Does this introduce new auth requirements or change existing ones?
4. **Data model**: What needs to be stored? What relationships exist?
5. **Existing behavior**: What should stay the same? What changes?
6. **Edge cases**: What happens at the boundaries? Concurrency, missing data, existing users?
7. **Interactions**: How does this affect existing features or flows?
8. **UI**: Is there a UI component? If so, what does it look like?
9. **Rollout**: Any concerns about existing data or backward compatibility?

Skip questions that can be answered by the codebase. When a decision has dependencies on prior decisions, resolve them in order — don't ask about implementation details before scope is settled.

## Phase 3: Produce the spec

Once all branches are resolved, output the spec as raw markdown in a code block. The user should be able to copy/paste it directly into GitHub.

### Output format

````markdown
# <Feature Title>

## Description

<What the feature does and why it matters. Written for someone who doesn't know the codebase. 2-4 paragraphs.>

## Acceptance Criteria

- <Concrete, testable criterion that defines "done">
- <Each criterion should be independently verifiable>
- <Cover the happy path, edge cases, and negative cases>

## Dev Notes

- <Technical implementation details that will be helpful for the developer implementing this>
- <Schema changes, key file paths, architectural decisions, gotchas>
````

## Rules

- Ask questions one at a time, not in batches.
- Always provide a recommended answer with each question.
- If a question can be answered by reading the code, read the code instead of asking.
- Don't produce the spec until all major branches are resolved.
- Don't include a technical implementation plan — dev notes are hints, not step-by-step instructions.
- Output the spec as a raw markdown code block so it's easy to copy/paste.
