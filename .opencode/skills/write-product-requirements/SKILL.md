---
name: write-product-requirements
description: Create a product requirements document from a feature description or design discussion. Outputs product-requirements.md — business requirements and acceptance criteria, no technical details.
---

Given a feature description or requirements summary, produce a product requirements document in `feature-artifacts/<feature-slug>/`.

## Step 1: Determine the feature name

If the feature name is clear from the prompt, use it. Otherwise, ask for one. Convert it to a slug (lowercase, hyphenated) for the folder name.

## Step 2: Create the directory

```bash
mkdir -p feature-artifacts/<feature-slug>
```

## Step 3: Write `product-requirements.md`

Write from the perspective of a product manager. Include:
- **Description**: What the feature does and why it matters to users
- **Acceptance Criteria**: Concrete, testable criteria that define "done"

Do NOT include:
- Technical architecture
- Implementation details
- File paths or code
- API endpoints

Refer to `feature-artifacts/refresh-backlog-covers/product-requirements.md` for style.
