import boto3
import json
import datetime
import logging


class STS(object):
    def __init__(self):
        self.app_session = None
        self.sts_client = None

    def configure(self, session):
        self.app_session = session
        self.sts_client = self.app_session.client('sts')

    def assume_role(self, role_arn, external_id):
        try:
            response = self.sts_client.assume_role(
                RoleArn=role_arn,
                ExternalId=external_id,
                RoleSessionName='assumed_role',
                DurationSeconds=3600,
                # SerialNumber='string',
                # Policy='string',
                # TokenCode='string'
            )
            return response
        except Exception as e:
            raise e

    def get_credentials(self, role_arn, external_id):
        try:
            response = self.assume_role(role_arn, external_id)
            credentials = response['Credentials']
            return credentials
        except Exception as e:
            raise e


class DynamoDB(object):
    def __init__(self):
        ec2_table = ""
        s3_table = "s3_lambda"


def get_resource_name(tags):
    for key_value in tags:
        if key_value["Key"] == "Name":
            return key_value["Value"]
    return ""


def get_workspace_name(workspace_id, workspace_client):
    response = workspace_client.describe_tags(
        ResourceId=workspace_id
    )
    if len(response["TagList"]) == 0:
        return ""


def get_workspace(session, region, account_number):
    workspace_response_list = []
    workspace_client = session.client(service_name="workspaces", region_name=region)
    workspace_response = workspace_client.describe_workspaces()
    for workspace in workspace_response["Workspaces"]:
        workspace_response_list.append({
            "ResourceId": workspace["WorkspaceId"],
            "ResourceName": workspace["ComputerName"],
            "InstanceType": "",
            "ResourceType": "Workspace",
            "AccountNumber": account_number,
            "Region": region,
            "PrivateIpAddress": workspace["IpAddress"]
        })
    while "NextToken" in workspace_response:
        workspace_response = workspace_client.describe_workspaces(NextToken=workspace_response["NextToken"])
        for workspace in workspace_response["Workspaces"]:
            workspace_response_list.append({
                "ResourceId": workspace["WorkspaceId"],
                "ResourceName": workspace["ComputerName"],
                "InstanceType": "",
                "ResourceType": "Workspace",
                "AccountNumber": account_number,
                "Region": region,
                "PrivateIpAddress": workspace["IpAddress"]
            })
    return workspace_response_list


def lookup_cloudtrail_events(session, region, event_name, event_key="EventName"):
    cloudtrail_client = session.client(service_name='cloudtrail', region_name=region)

    # date covering 30 days data
    end_date = datetime.datetime.now()
    timedelta = datetime.timedelta(days=90)
    start_date = end_date - timedelta
    events = []
    for page in cloudtrail_client.get_paginator("lookup_events").paginate(
            LookupAttributes=[
                    {
                        'AttributeKey': event_key,
                        'AttributeValue': event_name
                    }
                ],
            StartTime=start_date,
            EndTime=end_date
    ):
        for event in page['Events']:
            cloudtrail_events = json.loads(event['CloudTrailEvent'])
            events.append(cloudtrail_events)

    # date covering 30 days data
    # end_date = datetime.datetime.now()
    # timedelta = datetime.timedelta(days=30)
    # start_date = end_date - timedelta
    #
    # events = cloudtrail_client.lookup_events(
    #     LookupAttributes=[
    #         {
    #             'AttributeKey': 'EventName',
    #             'AttributeValue': event_name
    #         }
    #     ],
    #     StartTime=start_date,
    #     EndTime=end_date
    # )
    return events


def get_document_db(session, region, account_number):
    document_db_response_list = []
    document_db_client = session.client(service_name="docdb", region_name=region)
    document_db_response = document_db_client.describe_db_clusters()
    for cluster in document_db_response["DBClusters"]:
        document_db_response_list.append({
            "ResourceId": cluster["DbClusterResourceId"],
            "ResourceName": cluster["DBClusterIdentifier"],
            "InstanceType": "",
            "ResourceType": "DocumentDBCluster",
            "AccountNumber": account_number,
            "Region": region,
        })
    document_db_response = document_db_client.describe_db_instances()
    for db_instance in document_db_response["DBInstances"]:
        document_db_response_list.append({
            "ResourceId": db_instance["DbiResourceId"],
            "ResourceName": db_instance["DBInstanceIdentifier"],
            "InstanceType": db_instance["DBInstanceClass"],
            "ResourceType": "DocumentDBInstance",
            "AccountNumber": account_number,
            "Region": region
        })
    return document_db_response_list


def update_rds_db_owners(session, region, rds_db_data):
    event_name = "CreateDBInstance"
    updated_rds_db_data = []
    rds_db_events = lookup_cloudtrail_events(session, region, event_name)

    for rds_dbs in rds_db_data:
        rds_dbs['CreatedBy'] = ""
        for events in rds_db_events:
            try:
                username = events['userIdentity']['userName']
                rds_db_identifier = (
                    events['requestParameters']['dBInstanceIdentifier']
                )
            except Exception as e:
                continue
            if rds_dbs['ResourceName'] == rds_db_identifier:
                rds_dbs['CreatedBy'] = username
                logging.log(msg=events)
                break
        updated_rds_db_data.append(rds_dbs)
    return updated_rds_db_data


def get_rds_db(session, region, account_number):
    rds_db_response_list = []
    rds_db_client = session.client(service_name="rds", region_name=region)
    rds_db_response = rds_db_client.describe_db_clusters()
    for cluster in rds_db_response["DBClusters"]:
        rds_db_response_list.append({
            "ResourceId": cluster["DbClusterResourceId"],
            "ResourceName": cluster["DBClusterIdentifier"],
            "InstanceType": "",
            "ResourceType": "RDSCluster",
            "AccountNumber": account_number,
            "Region": region,
        })
    document_db_response = rds_db_client.describe_db_instances()
    for db_instance in document_db_response["DBInstances"]:
        rds_db_response_list.append({
            "ResourceId": db_instance["DbiResourceId"],
            "ResourceName": db_instance["DBInstanceIdentifier"],
            "InstanceType": db_instance["DBInstanceClass"],
            "ResourceType": "RDSInstance",
            "AccountNumber": account_number,
            "Region": region
        })
    return rds_db_response_list


def get_app_stream(session, region, account_number):
    app_stream_response_list = []
    app_stream_client = session.client(service_name="appstream", region_name=region)
    fleet_response = app_stream_client.describe_fleets()
    # image_response = app_stream_client.describe_images()
    stacks_response = app_stream_client.describe_stacks()
    for fleet in fleet_response["Fleets"]:
        app_stream_response_list.append({
            "ResourceId": fleet["Arn"],
            "ResourceName": fleet["Name"],
            "InstanceType": "",
            "ResourceType": "AppStreamFleet",
            "AccountNumber": account_number,
            "Region": region,
            "PrivateIpAddress": "",
        })
    # for image in image_response["Images"]:
    #     app_stream_response_list.append({
    #         "ResourceId": image["Arn"],
    #         "ResourceName": image["Name"],
    #         "InstanceType": "",
    #         "ResourceType": "AppStreamImage",
    #         "AccountNumber": account_number,
    #         "Region": region,
    #         "PrivateIpAddress": "",
    #     })
    # while "NextToken" in image_response:
    #     image_response = app_stream_client.describe_images()
    #     for image in image_response["Images"]:
    #         app_stream_response_list.append({
    #             "ResourceId": image["Arn"],
    #             "ResourceName": image["Name"],
    #             "InstanceType": "",
    #             "ResourceType": "AppStreamImage",
    #             "AccountNumber": account_number,
    #             "Region": region,
    #             "PrivateIpAddress": "",
    #         })
    for stack in stacks_response["Stacks"]:
        app_stream_response_list.append({
            "ResourceId": stack["Arn"],
            "ResourceName": stack["Name"],
            "InstanceType": "",
            "ResourceType": "AppStreamStack",
            "AccountNumber": account_number,
            "Region": region,
            "PrivateIpAddress": "",
        })
    return app_stream_response_list


def update_ec2_owners(session, region, ec2_data):
    event_name = "DescribeInstances"
    updated_ec2_data = []
    ec2_events = lookup_cloudtrail_events(session, region, event_name)
    # ec2_events['Events'][3]['CloudTrailEvent']
    # ec2_events['Events'][3]['Username']
    # ec2_data[0]['ResourceId']

    for ec2s in ec2_data:
        ec2s['CreatedBy'] = ""
        for events in ec2_events:
            try:
                username = events['userIdentity']['userName']
                instance_id = (
                    events['requestParameters']['filterSet']['items'][0]['valueSet']['items'][0]['value']
                )
            except Exception as e:
                continue
            if ec2s['ResourceId'] == instance_id:
                ec2s['CreatedBy'] = username
                break
        updated_ec2_data.append(ec2s)
    return updated_ec2_data


def get_ec2(session, region, account_number):
    instance_response = []
    ec2_client = session.client(service_name="ec2", region_name=region)
    ec2_response = ec2_client.describe_instances()
    for reservation in ec2_response["Reservations"]:
        for instance in reservation['Instances']:
            instance_response.append({
                "ResourceId": instance["InstanceId"],
                "ResourceName": get_resource_name(instance["Tags"]),
                "InstanceType": instance["InstanceType"],
                "ResourceType": "EC2Instance",
                "AccountNumber": account_number,
                "Region": region,
                "PrivateIpAddress": instance["PrivateIpAddress"] if "PrivateIpAddress" in instance else "",
                "CreationDate": str(instance["LaunchTime"])
            })
    return instance_response


def update_dynamo_db_owners(session, region, dynamo_db_data):
    event_name = "CreateTable"
    updated_dynamo_db_data = []
    dynamo_db_events = lookup_cloudtrail_events(session, region, event_name)

    for dynamo_dbs in dynamo_db_data:
        dynamo_dbs['CreatedBy'] = ""
        for events in dynamo_db_events:
            try:
                username = events['userIdentity']['userName']
                table_name = (
                    events['requestParameters']['tableName']
                )
            except Exception as e:
                continue
            if dynamo_dbs['ResourceName'] == table_name:
                dynamo_dbs['CreatedBy'] = username
                break
        updated_dynamo_db_data.append(dynamo_dbs)
    return updated_dynamo_db_data


def get_dynamo_db(session, region, account_number):
    dynamo_db_response_list = []
    dynamo_db_client = session.client("dynamodb", region_name=region)
    dynamo_db_response = dynamo_db_client.list_tables()
    for table in dynamo_db_response['TableNames']:
        table_response = dynamo_db_client.describe_table(TableName=table)
        dynamo_db_response_list.append({
            "ResourceId": table_response['Table']['TableId'],
            "ResourceName": table,
            "InstanceType": "",
            "ResourceType": "Dynamo DB",
            "AccountNumber": account_number,
            "Region": region,
            "PrivateIpAddress": "",
            "CreationDate": str(table_response['Table']['CreationDateTime'].date())
        })
    return dynamo_db_response_list


def get_route_53(session, region, account_number):
    route_53_response_list = []
    route_53_client = session.client(service_name="route53", region_name=region)
    route_53_response = route_53_client.list_hosted_zones()
    for hosted_zone in route_53_response["HostedZones"]:
        route_53_response_list.append({
            "ResourceId": hosted_zone["Id"],
            "ResourceName": hosted_zone["Name"],
            "InstanceType": "",
            "ResourceType": "Route53HostedZone",
            "AccountNumber": account_number,
            "Region": region,
            "PrivateIpAddress": "",
        })
    return route_53_response_list


def check_s3_termination_status(session, region, s3_data):
    event_name = "DeleteBucket"
    terminate_rawdata = lookup_cloudtrail_events(session, region, event_name)
    terminated_s3s = {}
    for events in terminate_rawdata:
        try:
            terminated_s3s[f"{events['requestParameters']['bucketName']}"] = {
                "username": events['userIdentity']['userName'],
                "termination_date": events['eventTime']
            }
        except Exception as e:
            continue
    for s3 in s3_data:
        try:
            if s3["ResourceName"] in terminated_s3s.keys():
                s3["TerminatedBy"] = terminated_s3s[s3["ResourceName"]].get("username")
                s3["TerminationDate"] = terminated_s3s[s3["ResourceName"]].get("termination_date")
        except Exception as e:
            continue
    return s3_data


def get_bucket_location(s3_client, bucket_name):
    bucket_location_response = s3_client.get_bucket_location(
        Bucket=bucket_name
    )
    if not bucket_location_response["LocationConstraint"]:
        return "us-east-1"
    return bucket_location_response["LocationConstraint"]


def update_s3_owners(session, region, s3_data):
    event_name = 'CreateBucket'
    updated_s3_data = []
    s3_events = lookup_cloudtrail_events(session, region, event_name)

    for s3s in s3_data:
        s3s['CreatedBy'] = ""
        for events in s3_events:
            try:
                username = events['userIdentity']['userName']
                resource_name = events['requestParameters']['bucketName']
            except Exception as e:
                continue
            if s3s['ResourceName'] == resource_name:
                s3s['CreatedBy'] = username
                break
        updated_s3_data.append(s3s)
    return updated_s3_data


def get_s3(session, region, account_number):
    s3_response_list = []
    s3_client = session.client(service_name="s3", region_name=region)
    s3_response = s3_client.list_buckets()
    for s3_bucket in s3_response["Buckets"]:
        s3_response_list.append({
            "ResourceId": s3_bucket["Name"],
            "ResourceName": s3_bucket["Name"],
            "InstanceType": "",
            "ResourceType": "S3",
            "AccountNumber": account_number,
            "Region": get_bucket_location(s3_client, s3_bucket["Name"]),
            "PrivateIpAddress": "",
            "CreationDate": str(s3_bucket["CreationDate"]),
            "TerminatedBy": "",
            "TerminationDate": ""
        })
    return s3_response_list


def get_cloud_trail(session, region, account_number):
    cloud_trail_response_list = []
    cloud_trail_client = session.client(service_name="cloudtrail", region_name=region)
    cloud_trail_response = cloud_trail_client.list_trails()
    for trail in cloud_trail_response["Trails"]:
        cloud_trail_response_list.append({
            "ResourceId": trail["TrailARN"],
            "ResourceName": trail["Name"],
            "InstanceType": "",
            "ResourceType": "CloudTrail",
            "AccountNumber": account_number,
            "Region": region,
            "PrivateIpAddress": "",
        })
    return cloud_trail_response_list


def get_file_system(session, region, account_number):
    file_system_response_list = []
    file_system_client = session.client(service_name="fsx", region_name=region)
    file_system_response = file_system_client.describe_file_systems()
    for file_system in file_system_response["FileSystems"]:
        file_system_response_list.append({
            "ResourceId": file_system["FileSystemId"],
            "ResourceName": get_resource_name(file_system["Tags"]),
            "InstanceType": "",
            "ResourceType": "FileSystem",
            "AccountNumber": account_number,
            "Region": region,
            "PrivateIpAddress": "",
        })
    return file_system_response_list


def get_red_shift(session, region, account_number):
    red_shift_response_list = []
    red_shift_client = session.client(service_name="redshift", region_name=region)
    red_shift_response = red_shift_client.describe_clusters()
    for red_shift in red_shift_response["Clusters"]:
        red_shift_response_list.append({
            "ResourceId": red_shift["ClusterIdentifier"],
            "ResourceName": red_shift["ClusterIdentifier"],
            "InstanceType": "",
            "ResourceType": "RedShift",
            "AccountNumber": account_number,
            "Region": region,
            "PrivateIpAddress": "",
        })
    return red_shift_response_list


def get_apache_airflow(session, region, account_number):
    apache_airflow_response_list = []
    apache_airflow_client = session.client(service_name="mwaa", region_name=region)
    apache_airflow_response = apache_airflow_client.list_environments()
    for apache_airflow in apache_airflow_response["Environments"]:
        apache_airflow_response_list.append({
            "ResourceId": apache_airflow,
            "ResourceName": apache_airflow,
            "InstanceType": "",
            "ResourceType": "ApacheAirflow",
            "AccountNumber": account_number,
            "Region": region,
            "PrivateIpAddress": "",
        })
    return apache_airflow_response_list


def get_inventory_report(event, context):
    try:
        role_arn = "arn:aws:iam::390618173518:role/inventory_role"
        sts_client = boto3.client('sts')
        assume_role_obj = sts_client.assume_role(RoleArn=role_arn, RoleSessionName='TestingS3')

        credentials = assume_role_obj['Credentials']

        session = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )
        region = 'ap-south-1'
        account_number = '390618173518'

        # EC2 Code below
        # ec2_data = get_ec2(session, region, account_number)
        # updated_ec2_data = update_ec2_owners(session, region, ec2_data)
        # for items in updated_ec2_data:
        #     print(items)

        # RDS Code below
        # rds_data = get_rds_db(session, region, account_number)
        # print(rds_data)
        # updated_rds_data = update_rds_db_owners(session, region, rds_data)
        # print(updated_rds_data)

        # DynamoDB Code Below
        # dynamo_db_data = get_dynamo_db(session, region, account_number)
        # updated_dynamo_db_data = update_dynamo_db_owners(session, region, dynamo_db_data)
        # for item in updated_dynamo_db_data:
        #     print(item)

        s3_data = get_s3(session, region, account_number)
        updated_s3_data = update_s3_owners(session, region, s3_data)
        # for item in updated_s3_data:
        #     print(item)
        check_s3_termination_status(session, region, updated_s3_data)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    get_inventory_report('', '')
