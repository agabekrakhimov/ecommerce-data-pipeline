"""Data quality gate for the star-schema marts.

The warehouse is SQLite and the rest of the pipeline stays on the standard
library, so the checks are SQL files in sql/quality/ rather than a pandas or
Spark job. Each file is one check: the query returns the violating rows, and
the check passes when that result is empty.

    python3 src/quality.py

run_pipeline.py runs this after the marts are built and skips analysis when
any check fails.
"""

import glob
import os
import sqlite3
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUALITY_DIR = os.path.join(BASE, "sql", "quality")
DEFAULT_DB = os.path.join(BASE, "warehouse.sqlite")

HEADER_KEYS = ("name", "table", "category", "description")
CATEGORIES = (
    "completeness",
    "null",
    "duplicate",
    "range",
    "referential",
    "consistency",
)
CATEGORY_ORDER = CATEGORIES


def parse_check(text, origin="check"):
    """Split a quality SQL file into metadata headers plus the violation query."""
    meta = {}
    body = []
    in_header = True
    for line in text.splitlines():
        stripped = line.strip()
        if in_header and stripped == "":
            continue
        if in_header and stripped.startswith("--"):
            payload = stripped[2:].strip()
            key, sep, val = payload.partition(":")
            key = key.strip().lower()
            if sep and key in HEADER_KEYS and key not in meta:
                meta[key] = val.strip()
                continue
        in_header = False
        body.append(line)

    missing = [key for key in HEADER_KEYS if not meta.get(key)]
    if missing:
        raise ValueError("{} is missing {}".format(origin, ", ".join(missing)))

    sql = "\n".join(body).strip().rstrip(";")
    if not sql:
        raise ValueError("{} has no SQL".format(origin))
    meta["sql"] = sql
    return meta


def load_checks(directory=None):
    """Load every sql/quality/*.sql file, in filename order."""
    directory = directory or QUALITY_DIR
    paths = sorted(glob.glob(os.path.join(directory, "*.sql")))
    if not paths:
        raise FileNotFoundError("No data quality checks in {}".format(directory))

    checks = []
    for path in paths:
        with open(path) as handle:
            check = parse_check(handle.read(), origin=os.path.basename(path))
        if check["category"] not in CATEGORIES:
            raise ValueError(
                "{} has unknown category {!r}".format(path, check["category"])
            )
        check["path"] = path
        checks.append(check)
    return checks


CHECKS = load_checks()


def run_checks(conn, checks=None):
    """Run checks against an open connection.

    A check fails when its query returns any row, or when the SQL itself errors
    (a missing mart table, for example). Violation queries are counted in the
    database so a large fact table is not pulled into Python.
    """
    if checks is None:
        checks = CHECKS

    results = []
    for check in checks:
        result = {
            "name": check["name"],
            "table": check["table"],
            "category": check["category"],
            "description": check["description"],
            "violations": 0,
            "passed": False,
            "sample": [],
            "error": None,
        }
        sql = check["sql"].strip().rstrip(";")
        try:
            count_sql = "SELECT COUNT(*) FROM ({}) AS dq_violations".format(sql)
            result["violations"] = conn.execute(count_sql).fetchone()[0]
            if result["violations"]:
                sample_sql = "SELECT * FROM ({}) AS dq_violations LIMIT 5".format(sql)
                cur = conn.execute(sample_sql)
                cols = [d[0] for d in cur.description]
                result["sample"] = [dict(zip(cols, row)) for row in cur.fetchall()]
            result["passed"] = result["violations"] == 0
        except sqlite3.Error as exc:
            result["error"] = str(exc)
            result["passed"] = False
            result["violations"] = 0
        results.append(result)
    return results


def summarize(results):
    """Roll violation counts up by check and by category."""
    by_category = {}
    failed = 0
    violations = 0
    for result in results:
        bucket = by_category.setdefault(
            result["category"], {"checks": 0, "failed": 0, "violations": 0}
        )
        bucket["checks"] += 1
        count = result["violations"] or 0
        bucket["violations"] += count
        violations += count
        if not result["passed"]:
            bucket["failed"] += 1
            failed += 1
    return {
        "checks": len(results),
        "failed": failed,
        "violations": violations,
        "by_category": by_category,
    }


def format_report(results):
    lines = []
    for result in results:
        if result["error"]:
            count = "ERR"
        else:
            count = str(result["violations"])
        status = "PASS" if result["passed"] else "FAIL"
        lines.append(
            "  {:<4}  {:<13}  {:<34} {:>6}".format(
                status, result["category"], result["name"], count
            )
        )
        if result["passed"]:
            continue
        lines.append("         {}".format(result["description"]))
        if result["error"]:
            lines.append("         {}".format(result["error"]))
        for row in result["sample"]:
            lines.append("         e.g. {}".format(row))

    summary = summarize(results)
    lines.append(
        "  {} checks, {} failed, {} violations".format(
            summary["checks"], summary["failed"], summary["violations"]
        )
    )
    if summary["violations"]:
        parts = []
        seen = set()
        for category in CATEGORY_ORDER:
            bucket = summary["by_category"].get(category)
            if bucket and bucket["violations"]:
                parts.append("{} {}".format(category, bucket["violations"]))
                seen.add(category)
        for category, bucket in summary["by_category"].items():
            if category not in seen and bucket["violations"]:
                parts.append("{} {}".format(category, bucket["violations"]))
        lines.append("  violations by category: {}".format(", ".join(parts)))
    return "\n".join(lines)


def main(db_path=None):
    """Print the quality report. Return 0 when every check passes, else 1."""
    db_path = os.path.abspath(db_path or DEFAULT_DB)
    if not os.path.exists(db_path):
        print(
            "No warehouse at {}. Build the marts first (python3 run_pipeline.py).".format(
                db_path
            )
        )
        return 1

    conn = sqlite3.connect(db_path)
    try:
        results = run_checks(conn)
    finally:
        conn.close()

    print(format_report(results))
    return 1 if summarize(results)["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
