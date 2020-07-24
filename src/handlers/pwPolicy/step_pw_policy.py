import boto3
import json
import logging
import os
from boto_factory import BotoFactory

log = logging.getLogger()
log.setLevel(os.environ.get('LOGLEVEL'))


def set_pw_policy(account_id, pw_policy):
    """sets password policy for AWS Account account_id"""
    session = boto3.Session()
    iam = BotoFactory().get_capability(
        boto3.client, session, 'iam', account_id=account_id
    )
    response = iam.update_account_password_policy(
        **pw_policy
    )
    log.info(json.dumps(response, indent=4, default=str))
    return response


def main(event, context):
    pw_policy = {
        "MinimumPasswordLength": 16,
        "RequireSymbols": False,
        "RequireNumbers": True,
        "RequireUppercaseCharacters": True,
        "RequireLowercaseCharacters": True,
        "AllowUsersToChangePassword": True,
        "MaxPasswordAge": 90,
        "PasswordReusePrevention": 10,
        "HardExpiry": True
    }
    if not event.get('AccountId'):
        raise ValueError('AccountId missing from input event')

    result = set_pw_policy(event.get('AccountId'), pw_policy)
    log.info(json.dumps(result, indent=4, default=str))
    return {'PasswordPolicy': pw_policy}
