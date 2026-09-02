---
name: write-pr-description
description: Generate a GitHub pull request description by diffing the current branch against origin/main. Use when the user wants to create or update a PR description for their current branch.
---

# Skill: write-pr-description

Generate a GitHub pull request description by analyzing the diff between the current branch and `origin/main`.

## Steps

1. Fetch the latest remote refs:
   ```bash
   git fetch origin
   ```

2. Get the branch name:
   ```bash
   git branch --show-current
   ```

3. Get the diff stat (summary of changes):
   ```bash
   git diff origin/main...HEAD --stat
   ```

4. Get the full diff:
   ```bash
   git diff origin/main...HEAD
   ```

5. Get the commit log for the branch:
   ```bash
   git log origin/main...HEAD --oneline
   ```

6. Analyze the diff and commits, then generate a PR description.

## Output Format

Output the PR description as raw markdown in a code block so it can be copied/pasted directly into GitHub. Use this structure:

````markdown
## Summary

<1-2 sentence overview of what this PR does and why.>

## Changes

- <Bullet list of meaningful changes, grouped by area of concern. Focus on *what* changed and *why*, not implementation details.>

## Testing

<How to verify the changes work. Include specific steps or commands if applicable.>

## Notes

<Any caveats, follow-up work, or context reviewers should know. Omit this section if not needed.>
````

## Rules

- Focus on the *why*, not just the *what*. Explain the motivation behind changes when it's not obvious.
- Group related changes together rather than listing every file.
- Skip trivial changes (formatting, whitespace, import ordering) unless they are the entire diff.
- Keep the summary under 2 sentences.
- If the diff is very large or complex, call out the most important areas for reviewers to focus on.
- Do not fabricate testing steps — only include instructions if the diff reveals clear verification paths (e.g. new endpoints, CLI flags, UI changes).
