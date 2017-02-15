import boto3
import botocore
import os
import random
from .utils import archive_function
import json
import uuid
import tempfile
import shutil
import subprocess
from multiprocessing import Pool
import inquirer


def get_config(config_location):
    """Attempt to open config at location, and offer to write any necessary default properties to that config."""
    default_config = {
        'deployment_name': 'dj-deployment',
        'lambda_function_prefix': 'dj_',
        'entries_bucket_name': 'dj-2017-' + str(random.randrange(2**24)),
        'api_gateway_identifier': 'dj_2017'
    }

    try:
        raw_config = open(config_location, 'r+')
        try:
            config = json.load(raw_config)
            # Offer to fill in any necessary config keys with defaults
            if not all (k in config for k in default_config.keys()):
                should_create_config_question = inquirer.Confirm('write_remaining_properties',
                              message='The supplied config doesn\'t have all of the necessary properties. Can I write the rest of them?'.format(config_location)
                              )
                answers = inquirer.prompt([should_create_config_question])
                if not answers['write_remaining_properties']:
                    print 'Please create a configuration file with all necessary properties. Check the docs for more info!'
                    return None
                else:
                    for key in default_config:
                        try:
                            config[key] = config[key]
                        except KeyError:
                            config[key] = default_config[key]
                    try:
                        raw_config.seek(0)
                        raw_config.write(json.dumps(config))
                        raw_config.truncate()
                    except IOError as write_config_err:
                        print 'Failed to write config due to {}. Aborting'.format(write_config_err)
                        return None
        except ValueError as parse_error:
            print 'The supplied config at {} isn\'t valid JSON, failed with error: {}'.format(config_location,
                                                                                              parse_error)
            print 'Please supply a valid config.'
            return None

        finally:
            raw_config.close()

    # If we fail to find the config file, offer to create one using the default
    except IOError:
        should_create_config_question = inquirer.Confirm('create_default',
                      message='Do you want me to create a default configuration for you at {}?'.format(config_location)
                      )
        answers = inquirer.prompt([should_create_config_question])
        if not answers['create_default']:
            print 'Please create a configuration file and call this with `python dailyjournal.py --config=path/to/config`'
            return None
        else:
            config = default_config
            try:
                config_file = open(config_location, 'w')
                config_file.write(json.dumps(config))
                config_file.close()
            except IOError as write_default_config_error:
                print 'Failed to write default config at {} due to {}'.format(config_location, write_default_config_error)


    try:
        config['access_key_id'] = config['aws_access_key_id']
    except KeyError:
        config['access_key_id'] = os.environ.get('AWS_ACCESS_KEY_ID')
    if config['access_key_id'] == None:
        print 'No access key id found in config/environment variable, will be defaulting to what you find here: http://boto3.readthedocs.io/en/latest/guide/configuration.html#configuring-credentials'

    try:
        config['secret_access_key'] = config['aws_secret_access_key']
    except KeyError:
        config['secret_access_key'] = os.environ.get('AWS_SECRET_ACCESS_KEY')
    if config['secret_access_key'] == None:
        print 'No secret access key found in config/environment variable, will be defaulting to what you find here: http://boto3.readthedocs.io/en/latest/guide/configuration.html#configuring-credentials'


    try:
        config['region'] = config['aws_region']
    except KeyError:
        config['region'] = os.environ.get('AWS_REGION')
    if config['region'] == None:
        print 'No region found in config/environment variable, will be defaulting to what you find here: http://boto3.readthedocs.io/en/latest/guide/configuration.html#configuring-credentials'

    return config

def deploy_stack(config, debug_npm):
    api_session = boto3.Session(aws_access_key_id=config['access_key_id'], aws_secret_access_key=config['secret_access_key'],
                                region_name=config['region'])

    region = api_session.region_name

    # Create a temporary bucket for uploading zipped lambda functions for deployment
    entries_bucket_name = config['entries_bucket_name']
    s3 = boto3.resource('s3')
    deployment_bucket = s3.Bucket('dj-deployment' + str(uuid.uuid4()))
    print 'Creating bucket'
    deployment_bucket.create()
    # Surround operations with a try, so buckets can always be cleaned up after the fact.
    try:
        print 'Uploading functions'
        upload_lambda_functions(deployment_bucket, 'store_handler')
        stack_name = config['deployment_name'] or 'daily-journal-deployment'
        try:
            notification_email = config['notification_email']
        except KeyError:
            notification_email = None
        try:
            notification_sms = config['notification_sms']
        except KeyError:
            notification_sms = None

        try:
            lambda_function_prefix = config['lambda_function_prefix']
        except KeyError:
            lambda_function_prefix = 'daily_journal_'
        cloudformation_client = api_session.client('cloudformation')
        deploy_cloud_formation(api_gateway_identifier=config['api_gateway_identifier'],
                               stack_name=stack_name,
                               cloudformation_client=cloudformation_client,
                               deployment_bucket_name=deployment_bucket.name,
                               entries_bucket_name=entries_bucket_name,
                               region=region,
                               notification_email=notification_email,
                               notification_sms=notification_sms,
                               lambda_prefix=lambda_function_prefix)
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

    apigateway_client = api_session.client('apigateway')
    upload_journal_views(apigateway_client=apigateway_client,
                         entries_bucket=s3.Bucket(entries_bucket_name),
                         api_gateway_identifier=config['api_gateway_identifier'],
                         region=region,
                         debug_view_build=debug_npm)


def upload_lambda_functions(bucket, function_name):
    """Given a bucket and a function name, uploads a zipped up lambda handler function to s3 for deployment"""
    temp_zip_dir = tempfile.mkdtemp()
    archive_loc = archive_function(temp_zip_dir, function_name)
    bucket.upload_file(archive_loc, function_name + '.zip')
    shutil.rmtree(temp_zip_dir)


def deploy_cloud_formation(api_gateway_identifier, stack_name, cloudformation_client, deployment_bucket_name,
                           entries_bucket_name, region, notification_email, notification_sms, lambda_prefix):
    """Deploy the cloudformation stack (create a new one if it doesn't exist, update the old one if it does)"""
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
        cf_resources = cloud_formation_settings['Resources']
        cf_resources['StoreLambda']['Properties']['Code']['S3Bucket'] = deployment_bucket_name
        cf_resources['StoreLambda']['Properties']['FunctionName'] = lambda_prefix + 'store_handler'
        cf_resources['DjRestApi']['Properties']['Name'] = api_gateway_identifier
        cf_resources['EntryBuckets']['Properties']['BucketName'] = entries_bucket_name
        # TODO: Allow custom message from configuration
        cf_resources['NotificationRule']['Properties']['Targets'][0][
            'Input'] = '"Don\'t forget today\'s entry! http://{}.s3-website-{}.amazonaws.com/"'.format(
            entries_bucket_name, region)
        if notification_email:
            cf_resources['ReminderSNS']['Properties']['Subscription'].append(
                {'Endpoint': notification_email, 'Protocol': 'email'})
        if notification_sms:
            cf_resources['ReminderSNS']['Properties']['Subscription'].append(
                {'Endpoint': notification_sms, 'Protocol': 'sms'})

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

def upload_journal_views(apigateway_client, entries_bucket, api_gateway_identifier, region, debug_view_build):
    all_apis = apigateway_client.get_rest_apis(
        limit=500
    )

    # Retrieve the API Gateway ID to generate the deployment URL
    for api in all_apis['items']:
        if api['name'] == api_gateway_identifier:
            deployed_api_url = 'https://{0}.execute-api.{1}.amazonaws.com/{2}/entries'.format(api['id'], region, 'dev')
            build_journal_views(debug_view_build, deployed_api_url)
            files_to_upload = []
            base_path = 'journal/build'
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    files_to_upload.append({'bucket': entries_bucket.name, 'file_path': file_path,
                                            'key': os.path.relpath(file_path, base_path)})
            print 'Uploading journal views'
            upload_pool = Pool(10)
            results = upload_pool.map(upload_file, files_to_upload)
            if results.count(True) > 0:
                print 'Failed to upload all files, deleting uploaded views.'
                entries_bucket.delete_objects({
                    'Objects': map(lambda key: {'Key': key}, filter(lambda key: key != True, results))
                })
            else:
                print 'Uploaded journal views!'
            return
    return RuntimeError(
        'Failed to find an API Gateway matching the name {}. Unable to upload views.'.format(api_gateway_identifier))


def upload_file(settings):
    client = boto3.client('s3')
    try:
        content_type = 'text/html' if os.path.splitext(settings['key'])[1] == '.html' else 'application/octet-stream'
        client.upload_file(settings['file_path'], settings['bucket'], settings['key'],
                           ExtraArgs={'ContentType': content_type})
    except botocore.exceptions.ClientError as upload_err:
        print 'Failed to upload file {} to bucket {} under key {} because of {}'.format(settings['bucket'],
                                                                                        settings['file_path'],
                                                                                        settings['key'], upload_err)
        return True
    return settings['key']


def build_journal_views(debug, gateway_url):
    """Install view dependencies, and build them with the appropriate gateway invocation URL environment variable"""
    cwd = os.path.join(os.getcwd(), 'journal')

    stdout = subprocess.PIPE
    if debug:
        stdout = None
    print 'Installing journal view dependencies'
    install_cmd = subprocess.Popen('npm i', stdout=stdout, stderr=stdout, shell=True, cwd=cwd)
    # if debug:
    out, err = install_cmd.communicate()
    if install_cmd.returncode != 0:
        print 'Failed to npm run build in journal directory because of: {}'.format(err)
        print out
        return False

    # Set up the `REACT_APP_GATEWAY_URL` environment variable to be read by the react app
    build_env = os.environ.copy()
    build_env['REACT_APP_GATEWAY_URL'] = gateway_url
    print 'Building journal views'
    build_cmd = subprocess.Popen('npm run build', stdout=stdout, stderr=stdout, shell=True, cwd=cwd, env=build_env)
    # if debug:
    out, err = build_cmd.communicate()
    if build_cmd.returncode != 0:
        print 'Failed to npm install in journal directory because of: {}'.format(err)
        print out
        return False

    return True
