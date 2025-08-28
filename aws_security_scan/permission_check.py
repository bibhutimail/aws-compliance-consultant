import boto3
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError

def check_permissions(session):
    # Check Security Scan permissions (EC2, S3, IAM, etc.)
    try:
        ec2 = session.client('ec2')
        ec2.describe_instances(MaxResults=5)
    except (ClientError, NoCredentialsError, EndpointConnectionError) as e:
        print("[ERROR] Missing required EC2 permissions or credentials for security scan.")
        print(f"Details: {e}")
        return False
    try:
        s3 = session.client('s3')
        s3.list_buckets()
    except (ClientError, NoCredentialsError, EndpointConnectionError) as e:
        print("[ERROR] Missing required S3 permissions or credentials for security scan.")
        print(f"Details: {e}")
        return False
    try:
        iam = session.client('iam')
        iam.list_users(MaxItems=1)
    except (ClientError, NoCredentialsError, EndpointConnectionError) as e:
        print("[ERROR] Missing required IAM permissions or credentials for security scan.")
        print(f"Details: {e}")
        return False
    # Check Cost Explorer permissions
    try:
        ce = session.client('ce')
        ce.get_cost_and_usage(
            TimePeriod={'Start': '2023-01-01', 'End': '2023-01-02'},
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
    except (ClientError, NoCredentialsError, EndpointConnectionError) as e:
        msg = str(e)
        if 'historical data beyond' in msg or 'You haven\'t enabled historical data' in msg:
            print("[WARNING] Cost Explorer is enabled, but historical data is not available. Cost report will be limited.")
            return True
        print("[ERROR] Missing required Cost Explorer permissions or credentials.")
        print(f"Details: {e}")
        return False
    return True
