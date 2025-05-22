import json
import os

import boto3

# Global Variables
DOMAIN_NAME = os.environ['DOMAIN_NAME']
ROUTE53_ZONE_ID = os.environ['ROUTE53_ZONE_ID']
AWS_PRIMARY_REGION = os.environ['AWS_PRIMARY_REGION']


class IpToDNSMapper:
    """
    Class to map an EC2 instance's public IP to a Route 53 DNS record.

    Attributes:
        instance_id (str): The ID of the EC2 instance.
        _ipv4 (str): The public IPv4 address of the EC2 instance.
        _dns_str (str): The DNS name to be associated with the instance.
        _ec2_client (boto3.client): Client to interact with EC2.
        _route53_client (boto3.client): Client to interact with Route 53.
    """

    def __init__(self, instance_id) -> None:
        """
        Initializes the IpToDNSMapper object with the instance ID and AWS clients.

        Args:
            instance_id (str): The ID of the EC2 instance.
        """
        self._instance_id = instance_id
        self._ipv4 = ""
        self._dns_str = ""
        self._dns_prefix = "autodns-"

        # Initialize EC2 and Route 53 clients
        aws_session = boto3.Session(
            region_name=AWS_PRIMARY_REGION,
           
        )
        self._ec2_client = aws_session.client('ec2')
        self._route53_client = aws_session.client('route53')

    def _delete_route53_record_set(self) -> bool:
        """
        Deletes a Route 53 DNS record if it exists.

        Returns:
            bool: True if the DNS record was successfully deleted.
        """
        try:
            # Get existing Route 53 record set details
            record_desc = self._route53_client.list_resource_record_sets(
                HostedZoneId=ROUTE53_ZONE_ID,
                StartRecordName=f'{self._dns_prefix}{self._dns_str}.{DOMAIN_NAME}',
                StartRecordType='A',
                MaxItems='1'
            )['ResourceRecordSets'][0]

            # Verify if the record matches the instance DNS
            if record_desc['Name'] != f'{self._dns_prefix}{self._dns_str}.{DOMAIN_NAME}.':
                print(f"Record mismatch: {record_desc['Name']} != {self._dns_prefix}{self._dns_str}.{DOMAIN_NAME}.")
                return False

            # Delete the Route 53 record
            delete_res = self._route53_client.change_resource_record_sets(
                HostedZoneId=ROUTE53_ZONE_ID,
                ChangeBatch={
                    'Changes': [
                        {
                            'Action': 'DELETE',
                            'ResourceRecordSet': {
                                'Name': record_desc['Name'],
                                'ResourceRecords': [{'Value': record_desc['ResourceRecords'][0]['Value']}],
                                'TTL': record_desc['TTL'],
                                'Type': record_desc['Type'],
                            },
                        },
                    ],
                },
            )
            print("Deleted record set", delete_res)
            return True
        except Exception as e:
            print(f"Error deleting record: {e}")
            return False

    def _create_route53_record_set(self) -> bool:
        """
        Creates or updates a Route 53 DNS record to map the instance's IP.

        Returns:
            bool: True if DNS record creation was successful.
        """
        try:
            response = self._route53_client.change_resource_record_sets(
                HostedZoneId=ROUTE53_ZONE_ID,
                ChangeBatch={
                    'Comment': f'DNS attached to instance {self._instance_id}',
                    'Changes': [
                        {
                            'Action': 'UPSERT',
                            'ResourceRecordSet': {
                                'Name': f'{self._dns_prefix}{self._dns_str}.{DOMAIN_NAME}',
                                'ResourceRecords': [{'Value': self._ipv4}],
                                'TTL': 300,
                                'Type': 'A',
                            },
                        },
                    ],
                },
            )
            print("Created/Updated record set", response)
            return True
        except Exception as e:
            print(f"Error creating/updating record: {e}")
            return False

    def set_dns(self) -> bool:
        """
        Maps the EC2 instance's public IP to a Route 53 DNS record.
        Deletes the DNS record if the instance is terminated.
        If the instance is stopped, it sets the IP to 127.0.0.1.

        Returns:
            bool: True if DNS record creation/deletion was successful.
        """
        try:
            # Describe the EC2 instance
            ec2_described = self._ec2_client.describe_instances(InstanceIds=[self._instance_id])['Reservations'][0]['Instances'][0]
            instance_state = ec2_described['State']['Name']

            # Get DNS name from instance tags
            self._dns_str = next(
                (tag['Value'].strip().lower() for tag in ec2_described['Tags'] if tag['Key'].strip().lower() == 'dns'),
                ""
            )

            if not self._dns_str:
                print("No DNS tag found for the instance.")
                return False

            # Handle instance state
            if instance_state == 'terminated':
                return self._delete_route53_record_set()
            elif instance_state == 'running':
                self._ipv4 = ec2_described.get('PublicIpAddress', "")
            elif instance_state == 'stopped':
                self._ipv4 = '127.0.0.1'

            return self._create_route53_record_set()
        except Exception as e:
            print(f"Error in set_dns: {e}")
            return False


def lambda_handler(event, context):
    """
    AWS Lambda handler function that sets the DNS for an EC2 instance.

    Args:
        event (dict): The event data from AWS Lambda, containing instance details.
        context (dict): The runtime information from AWS Lambda.

    Returns:
        dict: Status code and message indicating function execution.
    """
    print(event)
    obj = IpToDNSMapper(event['detail']['instance-id'])
    success = obj.set_dns()

    return {
        'statusCode': 200 if success else 500,
        'body': json.dumps('Function executed' if success else 'Function failed')
    }
