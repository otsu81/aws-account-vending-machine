import boto3
import os
import time
import logging
import json
from json_checker import Checker
from teams_broadcaster import TeamsBroadcaster

log = logging.getLogger()
log.setLevel(os.environ['LOGLEVEL'])


def check_input_json(event):
    expected_schema = {
        "AccountName": str,
        "Email": str,
        "RoleName": str,
        "Tags": [dict]
    }
    checker = Checker(expected_schema)
    result = checker.validate(event)
    assert result == event


def account_creation_poller(create_account_response_id, org_client):
    response = org_client.describe_create_account_status(
        CreateAccountRequestId=create_account_response_id
    )
    while response['CreateAccountStatus']['State'] == 'IN_PROGRESS':
        log.info(
            f"{create_account_response_id} still IN_PROGRESS, sleeping...")
        time.sleep(3)
        response = org_client.describe_create_account_status(
            CreateAccountRequestId=create_account_response_id
        )
    return response


def main(event, context):
    log.info(f"received event: {json.dumps(event, indent=2, default=str)}")
    """
    Must contain minimum 1 tag, but the 4 specified are recommended. Throws
    exception if AccountName, AccountEmail, Tags are not present.
    Expected event format:

    {
        "AccountName": "Account Name",
        "Email": "aws+account-name@test.com",
        "Tags" : [
            {
                "Key": "Owner",
                "Value": "owner@test.com"
            },
            {
                "Key": "CostCenter",
                "Value": "1234"
            },
            {
                "Key": "Organization",
                "Value": "Service Platform/IT"
            },
            {
                "Key": "Organization",
                "Value": "Service Platform/IT"
            },
        ]
    }
    """
    # verify input event is correct format
    # if incorrect abort and raise exception
    try:
        check_input_json(event)
    except Exception as e:
        TeamsBroadcaster().send_message(
            {
                'Failure': e,
                'Description': ''
            },
            title='Error from AccoutVendingMachine'
        )
        log.warning(e)
        raise e

    # create account
    org = boto3.client('organizations')
    response = org.create_account(
        AccountName=event['AccountName'],
        Email=event['Email'],
        RoleName=os.environ.get('DEFAULT_ORG_ADMIN_ROLE'),
        IamUserAccessToBilling=os.environ.get('IAM_USER_ACCESS_TO_BILLING')
    )
    log.info(
        f"create account response: \
            {json.dumps(response, indent=2, default=str)}")

    # wait for account to not be in progress
    create_account_response_id = response['CreateAccountStatus']['Id']
    status = account_creation_poller(create_account_response_id, org)
    log.info(
        f"create account status response: \
            {json.dumps(status, indent=2, default=str)}")

    # check succeeded or failure
    event['State'] = status['CreateAccountStatus']['State']
    if status['CreateAccountStatus']['State'] == 'SUCCEEDED':
        event['AccountId'] = status['CreateAccountStatus']['AccountId']
    elif status['CreateAccountStatus']['State'] == 'FAILED':
        event['FailureReason'] = status['CreateAccountStatus']['FailureReason']

    # send status to Teams channel
    TeamsBroadcaster().send_message(
        {
            'AccountCreation': status['CreateAccountStatus']['State'],
            'AccountDetails': event
        },
        title='AccountCreation'
    )
    log.info(f"account details: {json.dumps(event, indent=2, default=str)}")
    return event
