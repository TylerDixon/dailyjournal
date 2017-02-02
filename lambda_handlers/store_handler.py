import boto3
import json
import os
s3_client = boto3.client('s3')
s3_bucket = os.environ['S3_BUCKET']


def handler(event, context):
    s3_client.put_object(Body=json.dumps(event), Bucket=s3_bucket, Key='mykey')
    return {
        'statusCode': '200',
        'body': json.dumps(event),
        'headers': {
            'Content-Type': 'application/json',
        },
    }