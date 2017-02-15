import boto3
import json
import os
import time
import uuid
s3_client = boto3.client('s3')
s3_bucket = os.environ['S3_BUCKET']


def handler(event, context):
    key = time.strftime('%Y-%m-%d') + '-' + str(uuid.uuid4())
    s3_client.put_object(Body=json.dumps(event), Bucket=s3_bucket, Key='entries/' + key)
    return {
        'statusCode': '200',
        'body': json.dumps(event),
        'headers': {
            'Content-Type': 'application/json',
        },
    }