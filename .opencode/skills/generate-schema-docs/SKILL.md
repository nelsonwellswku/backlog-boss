---
name: generate-schema-docs
description: Regenerate docs/schema.md from the running SQL Server database. Run this after schema migrations.
---

Run this after any schema migration to refresh the static schema reference used by agents for database-related tasks.

## Prerequisites

- Docker running (`docker compose up`)
- `backend/.env` with valid DB credentials

## Invocation

```bash
cd backend && uv run python ../scripts/generate_schema_docs.py
```

Output: `docs/schema.md`
