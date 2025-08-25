# rules.py: Maps findings to AWS best practices and CIS Benchmarks

def evaluate_all_rules(resources):
    findings = []
    # EC2 public IP check
    for reservation in resources.get('ec2_instances', []):
        for instance in reservation.get('Instances', []):
            if instance.get('PublicIpAddress'):
                findings.append({
                    'service': 'EC2',
                    'resource_id': instance['InstanceId'],
                    'finding': 'EC2 instance has a public IP address.',
                    'severity': 'Medium',
                    'recommendation': 'Remove public IP or restrict access with security groups.',
                    'cis_control': 'CIS 4.1'
                })

    # Security Groups open to 0.0.0.0/0
    for sg in resources.get('security_groups', []):
        for perm in sg.get('IpPermissions', []):
            for ip_range in perm.get('IpRanges', []):
                if ip_range.get('CidrIp') == '0.0.0.0/0':
                    findings.append({
                        'service': 'SecurityGroup',
                        'resource_id': sg['GroupId'],
                        'finding': 'Security group open to 0.0.0.0/0.',
                        'severity': 'High',
                        'recommendation': 'Restrict security group ingress rules.',
                        'cis_control': 'CIS 4.1'
                    })

    # S3 public buckets
    for bucket in resources.get('s3_buckets', []):
        acl = resources.get('s3_bucket_acls', {}).get(bucket['Name'], {})
        grants = acl.get('Grants', [])
        for grant in grants:
            grantee = grant.get('Grantee', {})
            if grantee.get('Type') == 'Group' and 'AllUsers' in grantee.get('URI', ''):
                findings.append({
                    'service': 'S3',
                    'resource_id': bucket['Name'],
                    'finding': 'S3 bucket is public.',
                    'severity': 'High',
                    'recommendation': 'Enable bucket policies or block public access.',
                    'cis_control': 'CIS 2.1.1'
                })

    # IAM users without MFA
    for user in resources.get('iam_users', []):
        mfa_devices = resources.get('iam_mfa', {}).get(user['UserName'], {}).get('MFADevices', [])
        if not mfa_devices:
            findings.append({
                'service': 'IAM',
                'resource_id': user['UserName'],
                'finding': 'User has no MFA enabled.',
                'severity': 'Medium',
                'recommendation': 'Enable MFA for all IAM users.',
                'cis_control': 'CIS 1.14'
            })

    # IAM unused access keys (older than 90 days)
    import datetime
    for user, keys in resources.get('iam_access_keys', {}).items():
        for key in keys:
            if 'CreateDate' in key:
                age = (datetime.datetime.utcnow() - key['CreateDate'].replace(tzinfo=None)).days
                if age > 90:
                    findings.append({
                        'service': 'IAM',
                        'resource_id': f"{user}:{key['AccessKeyId']}",
                        'finding': 'Access key unused for over 90 days.',
                        'severity': 'Low',
                        'recommendation': 'Rotate or remove unused access keys.',
                        'cis_control': 'CIS 1.3'
                    })

    # RDS unencrypted instances
    for db in resources.get('rds_instances', []):
        if not db.get('StorageEncrypted', False):
            findings.append({
                'service': 'RDS',
                'resource_id': db['DBInstanceIdentifier'],
                'finding': 'RDS instance is not encrypted.',
                'severity': 'Low',
                'recommendation': 'Enable encryption for RDS instances.',
                'cis_control': 'CIS 2.2.1'
            })

    # Lambda functions without least privilege (role check placeholder)
    for fn in resources.get('lambda_functions', []):
        # Placeholder: In real use, fetch and analyze role policy
        findings.append({
            'service': 'Lambda',
            'resource_id': fn['FunctionName'],
            'finding': 'Review Lambda function role for least privilege.',
            'severity': 'Low',
            'recommendation': 'Ensure Lambda function role follows least privilege.',
            'cis_control': 'CIS 1.18'
        })

    # CloudTrail logging
    if not resources.get('cloudtrails', []):
        findings.append({
            'service': 'CloudTrail',
            'resource_id': '-',
            'finding': 'No CloudTrail trails found.',
            'severity': 'High',
            'recommendation': 'Enable CloudTrail logging in all regions.',
            'cis_control': 'CIS 2.1.1'
        })

    # GuardDuty enabled
    if not resources.get('guardduty', {}):
        findings.append({
            'service': 'GuardDuty',
            'resource_id': '-',
            'finding': 'GuardDuty is not enabled.',
            'severity': 'Medium',
            'recommendation': 'Enable GuardDuty for threat detection.',
            'cis_control': 'CIS 4.2'
        })

    # ECS/EKS clusters (placeholder for compliance checks)
    for cluster in resources.get('ecs_clusters', []):
        findings.append({
            'service': 'ECS',
            'resource_id': cluster,
            'finding': 'ECS cluster discovered.',
            'severity': 'Low',
            'recommendation': 'Review ECS cluster security settings.',
            'cis_control': 'CIS 5.1'
        })
    for cluster in resources.get('eks_clusters', []):
        findings.append({
            'service': 'EKS',
            'resource_id': cluster,
            'finding': 'EKS cluster discovered.',
            'severity': 'Low',
            'recommendation': 'Review EKS cluster security settings.',
            'cis_control': 'CIS 5.1'
        })

    return findings
