import os
import boto3
import json

# Environment variables
DOMAIN_NAME = os.environ.get('DOMAIN_NAME')  # e.g., himanshutest.in
ROUTE53_ZONE_ID = os.environ.get('ROUTE53_ZONE_ID')  # your hosted zone ID

class IpToDNSMapper:
    """
    Class to map an EC2 instance's public IP to a Route 53 DNS record
    """

    def __init__(self, instance_id) -> None:
        self._instance_id = instance_id
        self._ipv4 = ""
        self._dns_str = ""

        # Use default boto3 clients with IAM role permissions
        self._ec2_client = boto3.client('ec2')
        self._route53_client = boto3.client('route53')

    def _delete_route53_record_set(self) -> bool:
        try:
            record_desc = self._route53_client.list_resource_record_sets(
                HostedZoneId=ROUTE53_ZONE_ID,
                StartRecordName=f'{self._dns_str}.{DOMAIN_NAME}',
                StartRecordType='A',
                MaxItems='1'
            )['ResourceRecordSets'][0]

            if record_desc['Name'] != f'{self._dns_str}.{DOMAIN_NAME}.':
                print(f"Record mismatch: {record_desc['Name']} != {self._dns_str}.{DOMAIN_NAME}.")
                return False

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
        try:
            response = self._route53_client.change_resource_record_sets(
                HostedZoneId=ROUTE53_ZONE_ID,
                ChangeBatch={
                    'Comment': f'DNS attached to instance {self._instance_id}',
                    'Changes': [
                        {
                            'Action': 'UPSERT',
                            'ResourceRecordSet': {
                                'Name': f'{self._dns_str}.{DOMAIN_NAME}',
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
        try:
            ec2_described = self._ec2_client.describe_instances(InstanceIds=[self._instance_id])['Reservations'][0]['Instances'][0]
            instance_state = ec2_described['State']['Name']

            self._dns_str = next(
                (tag['Value'].strip().lower() for tag in ec2_described.get('Tags', []) if tag['Key'].strip().lower() == 'dns'),
                ""
            )

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
    print(event)
    obj = IpToDNSMapper(event['detail']['instance-id'])
    success = obj.set_dns()
    return {
        'statusCode': 200 if success else 500,
        'body': json.dumps('Function executed' if success else 'Function failed')
    }
