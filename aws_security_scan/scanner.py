# Scanner module: discovers AWS resources and runs security checks
import boto3
from aws_security_scan.rules import evaluate_all_rules

class Scanner:
    def __init__(self, profile=None):
        if profile:
            self.session = boto3.Session(profile_name=profile)
        else:
            self.session = boto3.Session()
        self.account_id = self.session.client('sts').get_caller_identity()['Account']

    def run_all_checks(self):
        resources = self.discover_resources()
        findings = evaluate_all_rules(resources)
        return findings, self.account_id

    def discover_resources(self):
        # Discover resources from major AWS services
        resources = {}
        ec2 = self.session.client('ec2')
        resources['ec2_instances'] = ec2.describe_instances()['Reservations']
        resources['security_groups'] = ec2.describe_security_groups()['SecurityGroups']

        s3 = self.session.client('s3')
        resources['s3_buckets'] = s3.list_buckets()['Buckets']
        # For each bucket, get ACL and policy
        resources['s3_bucket_acls'] = {b['Name']: s3.get_bucket_acl(Bucket=b['Name']) for b in resources['s3_buckets']}
        try:
            resources['s3_bucket_policies'] = {b['Name']: s3.get_bucket_policy(Bucket=b['Name'])['Policy'] for b in resources['s3_buckets'] if s3.get_bucket_policy(Bucket=b['Name'])}
        except Exception:
            resources['s3_bucket_policies'] = {}

        iam = self.session.client('iam')
        resources['iam_users'] = iam.list_users()['Users']
        resources['iam_mfa'] = {u['UserName']: iam.list_mfa_devices(UserName=u['UserName']) for u in resources['iam_users']}
        resources['iam_access_keys'] = {u['UserName']: iam.list_access_keys(UserName=u['UserName'])['AccessKeyMetadata'] for u in resources['iam_users']}

        rds = self.session.client('rds')
        resources['rds_instances'] = rds.describe_db_instances()['DBInstances']

        lambda_client = self.session.client('lambda')
        resources['lambda_functions'] = lambda_client.list_functions()['Functions']

        vpc = self.session.client('ec2')
        resources['vpcs'] = vpc.describe_vpcs()['Vpcs']

        cloudtrail = self.session.client('cloudtrail')
        resources['cloudtrails'] = cloudtrail.describe_trails()['trailList']

        guardduty = self.session.client('guardduty')
        try:
            detectors = guardduty.list_detectors()['DetectorIds']
            resources['guardduty'] = {d: guardduty.get_detector(DetectorId=d) for d in detectors}
        except Exception:
            resources['guardduty'] = {}

        ecs = self.session.client('ecs')
        resources['ecs_clusters'] = ecs.list_clusters()['clusterArns']

        eks = self.session.client('eks')
        resources['eks_clusters'] = eks.list_clusters()['clusters']

        return resources
