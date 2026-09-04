---
name: fetch-github-issue
description: Fetch a GitHub issue's body text and bring it into context. Use when the user wants to reference or work with a specific GitHub issue. The issue body is fetched but not acted upon automatically.
---

Fetch the body of a GitHub issue using the `gh` CLI and include it in the conversation context.

## Usage

When the user references a GitHub issue (by number, URL, or asks to pull in an issue), run:

```bash
gh issue view <issue-ref> --json title,body --jq '.title, .body'
```

Where `<issue-ref>` is the issue number or full URL the user provides.

If the user has not specified an issue, ask them for the issue number or URL before fetching.

Output the fetched title and body verbatim so they are available in context for follow-up work. Do not summarize, interpret, or act on the issue unless the user asks you to in a subsequent message.
