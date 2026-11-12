"""Process standard SQS batches with idempotent DynamoDB receipts."""
import hashlib
import json
import os


def request(record):
    data = json.loads(record["body"])
    identifier = data["job_id"]
    units = data["units"]
    if (not isinstance(identifier, str) or not 1 <= len(identifier) <= 128
            or type(units) is not int or not 1 <= units <= 10_000):
        raise ValueError("invalid job")
    digest = hashlib.sha256(str(units).encode()).hexdigest()
    return identifier, units, digest


def process_batch(event, store):
    failures = []
    for record in event["Records"]:
        try:
            identifier, units, digest = request(record)
            store.record(identifier, units, digest)
        except (ValueError, KeyError, TypeError, StorageUnavailable):
            failures.append({"itemIdentifier": record["messageId"]})
    return {"batchItemFailures": failures}


class StorageUnavailable(Exception):
    """The receipt store could not finish this item."""


class DynamoReceipts:
    def __init__(self, client, table):
        self.client = client
        self.table = table

    def record(self, identifier, units, digest):
        from botocore.exceptions import BotoCoreError, ClientError

        try:
            self.client.put_item(
                TableName=self.table,
                Item={"job_id": {"S": identifier}, "units": {"N": str(units)}, "digest": {"S": digest}},
                ConditionExpression="attribute_not_exists(job_id)",
            )
        except ClientError as error:
            if error.response["Error"]["Code"] != "ConditionalCheckFailedException":
                raise StorageUnavailable from error
            try:
                stored = self.client.get_item(
                    TableName=self.table, Key={"job_id": {"S": identifier}}, ConsistentRead=True
                )
            except (BotoCoreError, ClientError) as read_error:
                raise StorageUnavailable from read_error
            if stored.get("Item", {}).get("digest", {}).get("S") != digest:
                raise ValueError("job identifier reused with different input") from error
        except BotoCoreError as error:
            raise StorageUnavailable from error


def lambda_handler(event, context):
    import boto3

    return process_batch(event, DynamoReceipts(boto3.client("dynamodb"), os.environ["RECEIPT_TABLE"]))
