import boto3
import botocore
import os
from .utils import archive_function
import json
import uuid
import tempfile
import shutil


def deploy_stack(config):
    access_key_id = config['aws_access_key_id'] if 'aws_access_key_id' in config else os.environ.get(
        'AWS_ACCESS_KEY_ID')
    secret_access_key = config['aws_secret_access_key'] if 'aws_secret_access_key' in config else os.environ.get(
        'AWS_SECRET_ACCESS_KEY')
    region = config['aws_region'] if 'aws_region' in config else os.environ.get('AWS_REGION')
    api_session = boto3.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key,
                                region_name=region)
    cloudformation_client = api_session.client('cloudformation')
    s3 = boto3.resource('s3')
    deployment_bucket = s3.Bucket('dj-deployment' + str(uuid.uuid4()))
    print 'Creating bucket'
    deployment_bucket.create()
    # Surround operations with a try, so buckets can always be cleaned up after the fact.
    try:
        print 'Uploading functions'
        upload_lambda_functions(deployment_bucket, 'store_handler')
        stack_name = config['deployment_name'] or 'daily-journal-deployment'
        deploy_cloud_formation(config['api_gateway_identifier'], stack_name, cloudformation_client, deployment_bucket.name)
        apigateway_client = api_session.client('apigateway')

        upload_journal_views(apigateway_client, config['api_gateway_identifier'], region)
    finally:
        print 'Deleting s3 objects'
        deployment_bucket.delete_objects(Delete={
            'Objects': [
                {
                    'Key': 'store_handler.zip'
                }
            ]
        })
        print 'Deleting s3 bucket'
        deployment_bucket.delete()


def upload_lambda_functions(bucket, function_name):
    """Given a bucket and a function name, uploads a zipped up lambda handler function to s3 for deployment"""
    temp_zip_dir = tempfile.mkdtemp()
    print temp_zip_dir
    archive_loc = archive_function(temp_zip_dir, function_name)
    bucket.upload_file(archive_loc, function_name + '.zip')
    shutil.rmtree(temp_zip_dir)

def deploy_cloud_formation(api_gateway_identifier, stack_name, cloudformation_client, deployment_bucket_name):
    should_update = True
    stack_waiter = 'stack_update_complete'
    try:
        cloudformation_client.describe_stacks(StackName=stack_name)
    except botocore.exceptions.ClientError:
        should_update = False
        stack_waiter = 'stack_create_complete'

    print 'Loading configuration'
    with open(os.path.join(os.getcwd(), os.path.dirname(__file__), 'cloud_formation.json')) as f:
        cloud_formation_settings = json.load(f)
        cloud_formation_settings['Resources']['StoreLambda']['Properties']['Code']['S3Bucket'] = deployment_bucket_name
        cloud_formation_settings['Resources']['DjRestApi']['Properties']['Name'] = api_gateway_identifier

        if should_update:
            print 'Updating stack'
            cloudformation_client.update_stack(StackName=stack_name,
                                               Capabilities=['CAPABILITY_NAMED_IAM'],
                                               TemplateBody=json.dumps(cloud_formation_settings))
        else:
            print 'Creating stack'
            cloudformation_client.create_stack(StackName=stack_name,
                                               Capabilities=['CAPABILITY_NAMED_IAM'],
                                               TemplateBody=json.dumps(cloud_formation_settings))
    waiter = cloudformation_client.get_waiter(stack_waiter)
    print 'Waiting for stack {0} to be {1}..'.format(stack_name, 'update' if should_update else 'create')
    try:
        waiter.wait(StackName=stack_name)
    except botocore.exceptions.ClientError as err:
        print 'Failed to deploy stack {}'.format(stack_name)
        print err
    print 'Stack request complete!'
    print 'Retrieving '

def upload_journal_views(apigateway_client, api_gateway_identifier, region):
    all_apis = apigateway_client.get_rest_apis(
        limit=500
    )

    for api in all_apis['items']:
        if api['name'] == api_gateway_identifier:
            deployed_api_url = 'https://{0}.execute-api.{1}.amazonaws.com/{2}/'.format(api.id, region, 'dev')
            # TODO: Update built view index with

    raise RuntimeError('Failed to find an API Gateway matching the name {}. Unable to upload views.'.format(api_gateway_identifier))