"""Replay mixed SQS batches and report receipt and dead-letter evidence locally."""
import argparse
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from handler import process_batch


class SQLiteReceipts:
    def __init__(self, connection):
        self.db = connection
        self.db.execute("CREATE TABLE receipts (job_id TEXT PRIMARY KEY, units INTEGER, digest TEXT)")

    def record(self, identifier, units, digest):
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO receipts VALUES (?, ?, ?)", (identifier, units, digest))
            stored, = self.db.execute("SELECT digest FROM receipts WHERE job_id=?", (identifier,)).fetchone()
            if stored != digest:
                raise ValueError("job identifier reused with different input")

    def jobs(self):
        return [row[0] for row in self.db.execute("SELECT job_id FROM receipts ORDER BY job_id")]


def replay(scenario):
    records = scenario["records"]
    expected = scenario["expected"]
    max_receives = scenario["max_receives"]
    if type(max_receives) is not int or not 1 <= max_receives <= 10:
        raise ValueError("max_receives must be an integer from 1 through 10")
    ids = [row["messageId"] for row in records]
    if len(set(ids)) != len(ids):
        raise ValueError("scenario message IDs must be unique")
    with closing(sqlite3.connect(":memory:")) as connection:
        store = SQLiteReceipts(connection)
        pending = list(records)
        attempt_counts = {}
        for _ in range(max_receives):
            if not pending:
                break
            for row in pending:
                mid = row["messageId"]
                attempt_counts[mid] = attempt_counts.get(mid, 0) + 1
            response = process_batch({"Records": pending}, store)
            retry = {item["itemIdentifier"] for item in response["batchItemFailures"]}
            pending = [row for row in pending if row["messageId"] in retry]
        evidence = {"receipts": store.jobs(), "dead_letter": sorted(row["messageId"] for row in pending),
                    "attempt_counts": attempt_counts}
    return {"decision": "ready" if evidence == expected else "hold", **evidence}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", type=Path)
    args = parser.parse_args()
    try:
        report = replay(json.loads(args.scenario.read_text()))
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(2, f"Invalid drill: {error}\n")
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["decision"] == "ready" else 1)


if __name__ == "__main__":
    main()
