import boto3
import json
import logging
import os

log = logging.getLogger()
log.setLevel(os.environ.get('LOGLEVEL'))


def map_all_children_ou(org_client, parent_ou):
    ou_dict = dict()
    pgnt = org_client.get_paginator('list_organizational_units_for_parent')
    itr = pgnt.paginate(
        ParentId=parent_ou
    )
    for i in itr:
        for ou in i['OrganizationalUnits']:
            ou_dict[ou['Name']] = ou['Id']

    if len(ou_dict):
        for k in ou_dict.copy().keys():
            ou_dict.update(map_all_children_ou(org_client, ou_dict[k]))
    return ou_dict


def extract_tags_dict(event):
    tags = event.get('Tags')
    tags_dict = dict()
    for tag in tags:
        tags_dict[tag.get('Key')] = tag.get('Value')
    return tags_dict


def main(event, context):
    org = boto3.client('organizations')

    # get root OU
    roots = org.list_roots()
    root_ou = roots['Roots'][0]['Id']

    # map all OUs in the organization
    ous = map_all_children_ou(org, root_ou)
    ous['Root'] = root_ou

    # get the tags from the account creation event
    tags = extract_tags_dict(event)

    # move account from root to target OU
    # if target OU doesn't exist, warn
    target_ou = ous.get(tags.get('Organization'))
    if not target_ou:
        log.warning(
            f"No OU for {tags.get('Organization')}, setting root as OU")
        event['OU'] = root_ou
    else:
        org.move_account(
            AccountId=event['AccountId'],
            SourceParentId=root_ou,
            DestinationParentId=target_ou
        )
        event['OU'] = target_ou

    log.info(json.dumps(event, indent=4, default=str))
    return {'OU': target_ou}
