import json
import boto3
import csv
import base64
import uuid


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
                "PrivateIpAddress": instance["PrivateIpAddress"] if "PrivateIpAddress" in instance else ""
            })
    return instance_response


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


def get_bucket_location(s3_client, bucket_name):
    bucket_location_response = s3_client.get_bucket_location(
        Bucket=bucket_name
    )
    if not bucket_location_response["LocationConstraint"]:
        return "us-east-1"
    return bucket_location_response["LocationConstraint"]


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
        # role_arn = f"arn:aws:iam::715287006162:role/MontyCloud-ApplicationRole"
        # external_id = "8c833f5b-67f9-4899-826a-8b50d2aa4c41"
        # sts = STS()
        # sts.configure(boto3.Session())
        # credentials = sts.get_credentials(role_arn,
        #                                   external_id)
        regions = ["us-east-1", "us-west-2", "ap-south-1"]
        account_number = context.invoked_function_arn.split(":")[4]
        print(account_number)
        # account_number = "715287006162"

        final_response = []

        # _session = boto3.Session(
        #     aws_access_key_id=credentials['AccessKeyId'],
        #     aws_secret_access_key=credentials['SecretAccessKey'],
        #     aws_session_token=credentials['SessionToken']
        # )

        _session = boto3.Session()

        final_response = get_route_53(_session, "us-east-1", account_number)
        final_response += get_s3(_session, "us-east-1", account_number)

        for region in regions:
            final_response += get_ec2(_session, region, account_number)
            final_response += get_workspace(_session, region, account_number)
            final_response += get_document_db(_session, region, account_number)
            final_response += get_app_stream(_session, region, account_number)
            final_response += get_cloud_trail(_session, region, account_number)
            final_response += get_rds_db(_session, region, account_number)
            final_response += get_file_system(_session, region, account_number)
            final_response += get_apache_airflow(_session, region, account_number)
            final_response += get_red_shift(_session, region, account_number)

        data_file = open('/tmp/inventory_report.csv', 'w')

        # create the csv writer object
        csv_writer = csv.writer(data_file)

        count = 0

        for emp in final_response:
            if count == 0:
                # Writing headers of CSV file
                header = emp.keys()
                csv_writer.writerow(header)
                count += 1

            # Writing data of CSV file
            csv_writer.writerow(emp.values())

        data_file.close()

        a_file = open("/tmp/inventory_report.csv")

        contents = a_file.read()

        bucket_name = event["BucketName"]
        s3_key = f"Montycloud-Report/{str(uuid.uuid4())}.csv"

        data = {
            "Bucket": bucket_name,
            "Key": s3_key,
            "Body": (bytes(contents.encode('UTF-8'))),
        }
        s3_client = boto3.client("s3")
        response = s3_client.put_object(**data)
        print(f"key is {s3_key}")
        return f"Report path is {bucket_name}/{s3_key}"
    except Exception as e:
        raise e
