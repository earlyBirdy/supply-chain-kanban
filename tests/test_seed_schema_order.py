import re
from pathlib import Path


CREATE_TABLE = re.compile(r"CREATE TABLE IF NOT EXISTS (\w+)")
REFERENCES = re.compile(r"REFERENCES (\w+)\(")


def test_seed_schema_has_no_forward_foreign_key_references() -> None:
    """Postgres db_init executes one schema file top-to-bottom.

    A table that declares a foreign key cannot reference a table that has not
    been created yet. Keep this guard close to the seed SQL so demo-agent does
    not fail at db_init after Docker has already built every image.
    """
    schema_path = Path(__file__).resolve().parents[1] / "data" / "seed_sql" / "00_schema.sql"
    created: set[str] = set()
    failures: list[str] = []

    for line_no, line in enumerate(schema_path.read_text().splitlines(), start=1):
        for ref_table in REFERENCES.findall(line):
            if ref_table not in created:
                failures.append(f"line {line_no}: references {ref_table} before CREATE TABLE")

        create_match = CREATE_TABLE.search(line)
        if create_match:
            created.add(create_match.group(1))

    assert failures == []
