import json
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path

from drill import SQLiteReceipts, replay
from handler import StorageUnavailable, process_batch


class RecoveryTest(unittest.TestCase):
    def test_replay_retries_only_failed_records(self):
        scenario = json.loads(Path("examples/mixed-batch.json").read_text())
        self.assertEqual(replay(scenario), {"decision": "ready", **scenario["expected"]})

    def test_failed_expectation_holds(self):
        scenario = json.loads(Path("examples/mixed-batch.json").read_text())
        scenario["expected"]["receipts"] = []
        self.assertEqual(replay(scenario)["decision"], "hold")

    def test_conflicting_payload_does_not_overwrite_receipt(self):
        with closing(sqlite3.connect(":memory:")) as connection:
            store = SQLiteReceipts(connection)
            store.record("id", 1, "first")
            with self.assertRaises(ValueError):
                store.record("id", 2, "second")
            self.assertEqual(connection.execute("SELECT units FROM receipts").fetchone(), (1,))

    def test_transient_store_error_is_retried(self):
        class Unavailable:
            def record(self, *_):
                raise StorageUnavailable

        record = {"messageId": "m", "body": '{"job_id":"a","units":1}'}
        self.assertEqual(process_batch({"Records": [record]}, Unavailable()),
                         {"batchItemFailures": [{"itemIdentifier": "m"}]})
