import os
import logging
import boto3
import json
from boto_factory import BotoFactory

log = logging.getLogger()
log.setLevel(os.environ.get('LOGLEVEL'))


def extract_tags_dict(event):
    tags = event.get('Tags')
    tags_dict = dict()
    for tag in tags:
        tags_dict[tag.get('Key')] = tag.get('Value')
    return tags_dict


def main(event, context):
    """
    Expected input event:
    {
        "AccountName": "Account Creation Test",
        "Email": "aws+test1@test.com",
        "Tags": [
            {
            "Key": "Owner",
            "Value": "owner@test.com"
            }
        ],
        "AccountId": "123456789012",
    }
    """

    if isinstance(event, list):
        merged_event = dict()
        for e in event:
            merged_event.update(e)
        event = merged_event

    # get SES client from account with trust
    ses = BotoFactory().get_capability(
        boto3.client, boto3.Session(), 'sesv2',
        account_id=os.environ['SES_ACCOUNT'],
        rolename=os.environ['SES_ROLE'],
        region=os.environ['SES_REGION']
    )

    # read email body from HTML file
    with open('resources/email_body.html', 'r') as f:
        email_body = f.read()

    # set params for email
    params = {
        'ACCOUNT_ID': event.get('AccountId'),
        'ACCOUNT_NAME': event.get('AccountName')
    }
    # make tags addressable
    tags = extract_tags_dict(event)

    charset = 'utf-8'
    response = ses.send_email(
        FromEmailAddress=os.environ.get('FROM_EMAIL'),
        Destination={
            'ToAddresses': [
                tags.get('Owner')
            ],
            'CcAddresses': [
                event.get('Email')
            ]
        },
        ReplyToAddresses=[
            os.environ.get('REPLY_TO_EMAIL')
        ],
        # FeedbackForwardingEmailAddress=os.environ.get('REPLY_TO_EMAIL'),
        Content={
            'Simple': {
                'Subject': {
                    'Data': 'New AWS account created',
                    'Charset': charset
                },
                'Body': {
                    'Html': {
                        'Data': email_body % params,
                        'Charset': charset
                    }
                }
            }
        },
        EmailTags=[
            {
                'Name': 'Origin',
                'Value': 'accountVendingMachine'
            }
        ]
    )
    log.info(json.dumps(response, indent=4, default=str))

    return event
