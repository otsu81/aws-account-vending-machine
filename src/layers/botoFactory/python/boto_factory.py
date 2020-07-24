import os


class BotoFactory:
    """Returns anything boto3 is capable of returning but in a slightly more
    accessible way in any account available to an AWS organization.

    Example usage:
    BotoFactory().get_capability(boto3.client, boto3.Session(
        profile_name='default', 'ec2', '123456789012',
        'OrganizationsAdmin', region='us-east-1'))

    Parameters:
        boto3_capability (function):The boto3 capability to be returned, e.g.
            client or resource
        session (boto3.Session):The session to be used to generate the
            capability, very useful for using specific profile defined in CLI
        service_name (boto3.service): Any AWS service available in boto3,
            e.g. EC2, IAM, SQS...
        account_id (str): The AWS account ID where the capability from which
            credentials should be valid
        rolename (str): The target role to be asssumed, must have trust to
            session account ID
        region (str): (Optional) The region where the capability should be
            made from
    """
    def get_capability(self, boto3_capability, session, service_name,
                       account_id='', rolename='', region=''):
        sts = session.client('sts')
        if region == '':
            region = session.region_name
        if account_id == '':
            account_id = sts.get_caller_identity().get('AccountId')
        if rolename == '':
            rolename = os.getenv('DEFAULT_ORG_ADMIN_ROLE')

        response = sts.assume_role(
            RoleArn=f"arn:aws:iam::{account_id}:role/{rolename}",
            RoleSessionName='OrganizationsAccount',
            DurationSeconds=900
        )
        return boto3_capability(
            service_name,
            region_name=region,
            aws_access_key_id=response['Credentials']['AccessKeyId'],
            aws_secret_access_key=response['Credentials']['SecretAccessKey'],
            aws_session_token=response['Credentials']['SessionToken']
        )
