"""Generate schema documentation from the running database.

Usage:
    cd backend && uv run python ../scripts/generate_schema_docs.py

Outputs docs/schema.md with markdown tables for all tables in the bb schema.
"""

import sys
from pathlib import Path
from textwrap import dedent

from sqlalchemy import create_engine, inspect, text

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.settings import get_settings


def get_engine():
    settings = get_settings()
    connstr = (
        f"mssql+pyodbc://{settings.db_user}:{settings.db_password}"
        f"@{settings.db_host}:{settings.db_port}/{settings.db_database}"
        f"?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    )
    return create_engine(connstr)


def get_tables(engine, schema="bb"):
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "select table_name from information_schema.tables "
                "where table_schema = :schema and table_type = 'BASE TABLE' "
                "order by table_name"
            ),
            {"schema": schema},
        )
        return [row[0] for row in result]


def get_columns(engine, table, schema="bb"):
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "select "
                "  c.column_name, "
                "  c.data_type, "
                "  c.character_maximum_length, "
                "  c.numeric_precision, "
                "  c.numeric_scale, "
                "  c.is_nullable, "
                "  c.column_default "
                "from information_schema.columns c "
                "where c.table_schema = :schema and c.table_name = :table "
                "order by c.ordinal_position"
            ),
            {"schema": schema, "table": table},
        )
        return result.fetchall()


def get_constraints(engine, table, schema="bb"):
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "select "
                "  tc.constraint_name, "
                "  tc.constraint_type, "
                "  kcu.column_name, "
                "  kcu2.table_name as ref_table, "
                "  kcu2.column_name as ref_column "
                "from information_schema.table_constraints tc "
                "join information_schema.key_column_usage kcu "
                "  on tc.constraint_name = kcu.constraint_name "
                "  and tc.table_schema = kcu.table_schema "
                "left join information_schema.referential_constraints rc "
                "  on tc.constraint_name = rc.constraint_name "
                "  and tc.table_schema = rc.constraint_schema "
                "left join information_schema.key_column_usage kcu2 "
                "  on rc.unique_constraint_name = kcu2.constraint_name "
                "  and rc.unique_constraint_schema = kcu2.table_schema "
                "where tc.table_schema = :schema and tc.table_name = :table "
                "order by tc.constraint_type, kcu.ordinal_position"
            ),
            {"schema": schema, "table": table},
        )
        return result.fetchall()


def format_column_type(row):
    data_type = row[1].lower()
    char_max_len = row[2]
    num_prec = row[3]
    num_scale = row[4]

    if char_max_len:
        return f"{data_type}({char_max_len})"
    if num_prec and num_scale:
        return f"{data_type}({num_prec},{num_scale})"
    if num_prec:
        return f"{data_type}({num_prec})"
    return data_type


def generate_markdown(engine, schema="bb"):
    tables = get_tables(engine, schema)
    lines = [
        f"# Database Schema Reference",
        "",
        f"Schema: `{schema}`",
        "",
    ]

    for table in tables:
        columns = get_columns(engine, table, schema)
        constraints = get_constraints(engine, table, schema)

        pk_cols = set()
        fk_cols = {}
        unique_cols = set()
        for c in constraints:
            if c[1] == "PRIMARY KEY":
                pk_cols.add(c[2])
            elif c[1] == "FOREIGN KEY":
                fk_cols[c[2]] = f"{c[3]}.{c[4]}"
            elif c[1] == "UNIQUE":
                unique_cols.add(c[2])

        lines.append(f"## {schema}.{table}")
        lines.append("")
        lines.append("| Column | Type | Nullable | Default | Constraints |")
        lines.append("|--------|------|----------|---------|-------------|")

        for col in columns:
            col_name = col[0]
            col_type = format_column_type(col)
            nullable = "YES" if col[5] == "YES" else "NO"
            default = col[6] or ""
            if default.startswith("(") and default.endswith(")"):
                default = default[1:-1]

            constraints_list = []
            if col_name in pk_cols:
                constraints_list.append("PK")
            if col_name in fk_cols:
                constraints_list.append(f"FK → {fk_cols[col_name]}")
            if col_name in unique_cols:
                constraints_list.append("UNIQUE")
            constraints_str = ", ".join(constraints_list)

            lines.append(
                f"| {col_name} | {col_type} | {nullable} | {default} | {constraints_str} |"
            )

        lines.append("")

    return "\n".join(lines)


def main():
    engine = get_engine()
    markdown = generate_markdown(engine)

    output_path = Path(__file__).parent.parent / "docs" / "schema.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown)
    print(f"Schema documentation written to {output_path}")


if __name__ == "__main__":
    main()
