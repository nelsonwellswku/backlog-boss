---
name: write-technical-implementation
description: Write a technical implementation plan: goal, current state, files to modify, step-by-step instructions, and edge cases. Takes a feature description as input.
---

Given a feature description or requirements summary, produce a technical implementation document in `feature-artifacts/<feature-slug>/`.

## Step 1: Determine the feature name

If the feature name is clear from the prompt, use it. Otherwise, ask for one. Convert it to a slug (lowercase, hyphenated) for the folder name.

## Step 2: Create the directory

```bash
mkdir -p feature-artifacts/<feature-slug>
```

## Step 3: Write `technical-implementation.md`

Write as a handoff document for a new coding session. It must be self-contained — the new session should have everything it needs without asking questions. Include:

- **Goal**: One-sentence summary of what we're building
- **Current State**: What exists today, with file paths and line numbers for key code
- **Files to Modify/Create**: Table of all files touched, with action (modify/create)
- **Step-by-Step Instructions**: Numbered steps with full code blocks. Each step should be complete enough that a new session can execute it without guessing.
- **Architecture Decisions**: Table of key decisions made and their rationale
- **Edge Cases**: Known edge cases and how they're handled

Refer to `feature-artifacts/refresh-backlog-covers/technical-implementation.md` for style.
