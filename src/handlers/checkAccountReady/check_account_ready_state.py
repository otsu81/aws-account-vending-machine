import os
import boto3
import logging
from boto_factory import BotoFactory


log = logging.getLogger()
log.setLevel(os.environ.get('LOGLEVEL'))


def main(event, context):
    sts = BotoFactory().get_capability(
        boto3.client, boto3.Session(), 'sts',
        account_id=event['AccountId'],
        rolename=event['RoleName']
    )
    log.info(sts.get_caller_identity())

    event['AccountReady'] = 'True'

    return event
