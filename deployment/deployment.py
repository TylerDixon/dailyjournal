import boto3
import botocore
import os
from .utils import archive_function
import tempfile
import shutil

def deploy_stack(config):
    access_key_id = config['aws_access_key_id'] if 'aws_access_key_id' in config else os.environ.get('AWS_ACCESS_KEY_ID')
    secret_access_key = config['aws_secret_access_key'] if 'aws_secret_access_key' in config else os.environ.get('AWS_SECRET_ACCESS_KEY')
    region = config['aws_region'] if 'aws_region' in config else os.environ.get('AWS_REGION')
    api_session = boto3.Session(aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, region_name=region)
    # account_id = boto3.client("sts").get_caller_identity()["Account"]

    # Create lambda function
    function_arn = deploy_lambda_functions(api_session.client('lambda'), config['lambda_function_prefix'])

    # Create API Gateway and necessary resources/methods
    deploy_api_gateway(api_session.client('apigateway'), function_arn)

    # # Create bucket
    # response = client.create_bucket(
    #     ACL='private' | 'public-read' | 'public-read-write' | 'authenticated-read',
    #     Bucket='string',
    #     CreateBucketConfiguration={
    #         'LocationConstraint': 'EU' | 'eu-west-1' | 'us-west-1' | 'us-west-2' | 'ap-south-1' | 'ap-southeast-1' | 'ap-southeast-2' | 'ap-northeast-1' | 'sa-east-1' | 'cn-north-1' | 'eu-central-1'
    #     },
    #     GrantFullControl='string',
    #     GrantRead='string',
    #     GrantReadACP='string',
    #     GrantWrite='string',
    #     GrantWriteACP='string'
    # )
    #
    # # Upload
    # response = client.put_object(
    #     ACL='private' | 'public-read' | 'public-read-write' | 'authenticated-read' | 'aws-exec-read' | 'bucket-owner-read' | 'bucket-owner-full-control',
    #     Body=b'bytes' | file,
    #     Bucket='string',
    #     CacheControl='string',
    #     ContentDisposition='string',
    #     ContentEncoding='string',
    #     ContentLanguage='string',
    #     ContentLength=123,
    #     ContentMD5='string',
    #     ContentType='string',
    #     Expires=datetime(2015, 1, 1),
    #     GrantFullControl='string',
    #     GrantRead='string',
    #     GrantReadACP='string',
    #     GrantWriteACP='string',
    #     Key='string',
    #     Metadata={
    #         'string': 'string'
    #     },
    #     ServerSideEncryption='AES256' | 'aws:kms',
    #     StorageClass='STANDARD' | 'REDUCED_REDUNDANCY' | 'STANDARD_IA',
    #     WebsiteRedirectLocation='string',
    #     SSECustomerAlgorithm='string',
    #     SSECustomerKey='string',
    #     SSEKMSKeyId='string',
    #     RequestPayer='requester',
    #     Tagging='string'
    # )

def deploy_lambda_functions(lambda_client, function_prefix):
    function_name = function_prefix + 'store_handler'
    temp_zip_dir = tempfile.mkdtemp()
    print temp_zip_dir
    archive = archive_function(temp_zip_dir, 'store_handler')
    try:
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime='python2.7',
            # TODO: Create role arn before creating this lambda
            Role='role_arn',
            Handler='store_handler.handler',
            Code={
                'ZipFile': archive.read()
            },
            Description='string',
            Timeout=10,
            MemorySize=128,
            Publish=True
        )
        return response['FunctionArn']
    except botocore.exceptions.ClientError as err:
        if err.response['Error']['Code'] == 'ResourceConflictException':
            print 'Function already exists under name %s, using this function' % function_name
            response = lambda_client.get_function(
                FunctionName=function_name,
            )
            return response['Configuration']['FunctionArn']
        else:
            print 'Unexpected error creating lambda function: %s' % err
    finally:
        shutil.rmtree(temp_zip_dir)

def deploy_api_gateway(api_gateway_client, function_arn, gateway_id='daily_journal_api'):
    # Create API Gateway
    create_api_response = api_gateway_client.create_rest_api(
        name=gateway_id,
        # stageName='dev',
        # stageDescription='Development environment for personal use',
        description='APIs for the daily journal application',
    )

    resources_response = api_gateway_client.get_resources(
        restApiId=create_api_response['id']
    )

    # Create resource
    entry_resource_response = api_gateway_client.create_resource(
        restApiId=create_api_response['id'],
        parentId=resources_response['items'][0]['id'],
        pathPart='entries'
    )

    # Create method for that resource
    api_gateway_client.put_method(
        restApiId=create_api_response['id'],
        resourceId=entry_resource_response['id'],
        httpMethod='POST',
        authorizationType='NONE',
        # authorizerId='string',
        apiKeyRequired=False,
        # operationName='string',
        # requestParameters={
        #     'string': True | False
        # },
        # requestModels={
        #     'string': 'string'
        # }
    )
    api_gateway_client.put_integration(
        restApiId=create_api_response['id'],
        resourceId=entry_resource_response['id'],
        httpMethod='POST',
        type='AWS',
        integrationHttpMethod='POST',
        # TODO: Use region ootion
        uri='arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/' + function_arn + '/invocations',
        # credentials='string',
        # requestParameters={
        #     'string': 'string'
        # },
        # requestTemplates={
        #     'string': 'string'
        # },
        # passthroughBehavior='string',
        # cacheNamespace='string',
        # cacheKeyParameters=[
        #     'string',
        # ],
        # contentHandling='CONVERT_TO_BINARY' | 'CONVERT_TO_TEXT'
    )
