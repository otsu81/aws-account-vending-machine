import boto3
import json
import os
import logging

log = logging.getLogger()
log.setLevel(os.environ.get('LOGLEVEL'))


def main(event, context):
    """
    Required keys for event are "AccountId" and "Tags"
    Expected input event format:

    {
        "Tags": [
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
            "Value": "IT Organization"
            }
        ],
        "AccountId": "123456789012",
    }

    """

    if not event.get('Tags'):
        log.warning(
            f"No tags present in event: \n\
                {json.dumps(event, indent=4, default=str)}")
    else:
        org = boto3.client('organizations')
        org.tag_resource(
            ResourceId=event['AccountId'],
            Tags=event['Tags']
        )

    return {'Tagged': 'True'}
