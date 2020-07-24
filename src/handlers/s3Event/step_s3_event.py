import json
import boto3
import os
import logging
from teams_broadcaster import TeamsBroadcaster

log = logging.getLogger()
log.setLevel(os.environ['LOGLEVEL'])


def parse_s3_json_obj(s3_metadata):
    """
    example of expected format:
    {
        "s3SchemaVersion": "1.0",
        "configurationId": "xxxxxxxxxxxx",
        "bucket": {
            "name": "testbucket",
            "ownerIdentity": {
                "principalId": "xxxxxxxxxxx"
            },
            "arn": "arn:aws:s3:::testbucket"
        },
        "object": {
            "key": "test.json",
            "size": 20,
            "eTag": "xxxxxxxxx",
            "sequencer": "xxxxxxxxxxxxxx"
    }
    """

    s3 = boto3.resource('s3')
    obj = s3.Object(
        os.environ.get('S3_BUCKET'), s3_metadata['object']['key'])
    raw = obj.get()['Body'].read()
    body = json.loads(raw.decode('utf-8'))
    log.info(body)
    return body


def invoke_steps_create_account(account_info):
    sfn = boto3.client('stepfunctions')
    response = sfn.start_execution(
        stateMachineArn=os.environ['STEPFUNCTION_ARN'],
        input=json.dumps(account_info, default=str)
    )
    log.info(json.dumps(response, indent=4, default=str))
    return response


def main(event, context):
    body = dict()
    for e in event['Records']:
        if e.get('s3'):
            body = parse_s3_json_obj(e['s3'])

    TeamsBroadcaster().send_message(body, title='S3Event')

    invoke_steps_create_account(body)
    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response
