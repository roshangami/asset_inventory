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
        self.be_table = {
            "ec2": "ec2_lambda",
            "rds": "rds_lambda",
            "dynamodb": "dynamodb_lambda",
            "s3": "s3_lambda"
        }
        self.fe_table = {
            "ec2": "ec2_api_gateway_frontend",
            "rds": "rds_api_gateway_frontend",
            "dynamodb": "dynamodb_api_gateway_frontend",
            "s3": "s3_api_gateway_frontend"
        }
        self.client = boto3.resource('dynamodb')

    def write_data(self, data: list, d_type):
        table = self.client.Table(self.fe_table.get(d_type))
        for item in data:
            table.put_item(Item=item)
        return {
            'statusCode': 200,
            'body': json.dumps(f"Data write successful to {self.fe_table.get(d_type)}")
        }

    def get_data(self, d_type):
        table = self.client.Table(self.fe_table.get(d_type))
        data = table.scan()
        return data


def lookup_cloudtrail_events(session, region, event_name):
    cloudtrail_client = session.client(service_name='cloudtrail', region_name=region)

    # date covering 1 day data
    end_date = datetime.datetime.now()
    timedelta = datetime.timedelta(days=2)
    start_date = end_date - timedelta
    events = []
    for page in cloudtrail_client.get_paginator("lookup_events").paginate(
            LookupAttributes=[
                    {
                        'AttributeKey': 'EventName',
                        'AttributeValue': event_name
                    }
                ],
            StartTime=start_date,
            EndTime=end_date
    ):
        for event in page['Events']:
            cloudtrail_events = json.loads(event['CloudTrailEvent'])
            events.append(cloudtrail_events)
    return events


def get_resource_name(tags):
    for key_value in tags:
        if key_value["Key"] == "Name":
            return key_value["Value"]
    return ""


def update_ec2_owners(session, region, ec2_data):
    event_name = "DescribeInstances"
    updated_ec2_data = []
    ec2_events = lookup_cloudtrail_events(session, region, event_name)

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


def update_s3_database(fresh_data):
    dynamodb = DynamoDB()
    s3_table_data = dynamodb.get_data(d_type="s3")
    s3_resource_name_table = [s3["ResourceName"] for s3 in s3_table_data["Items"]]
    data_to_write = []

    for s3_fresh_data in fresh_data:
        if s3_fresh_data["ResourceName"] not in s3_resource_name_table:
            data_to_write.append(s3_fresh_data)

    if data_to_write:
        dynamodb.write_data(data_to_write, d_type="s3")

    return {
            'statusCode': 200,
            'body': json.dumps(f"Data updated successfully")
        }


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
            "CreationDate": str(s3_bucket["CreationDate"])
        })
    return s3_response_list


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

        # DynamoDB Code Below
        s3_data = get_s3(session, region, account_number)
        updated_s3_data = update_s3_owners(session, region, s3_data)
        update_s3_database(updated_s3_data)

        # DynamoDB Code Below
        # dynamo_db_data = get_dynamo_db(session, region, account_number)
        # updated_dynamo_db_data = update_dynamo_db_owners(session, region, dynamo_db_data)
        # for item in updated_dynamo_db_data:
        #     print(item)

    except Exception as e:
        print(e)


if __name__ == '__main__':
    get_inventory_report('', '')