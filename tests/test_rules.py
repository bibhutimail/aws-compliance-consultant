import unittest
from aws_security_scan.rules import evaluate_all_rules

class TestRules(unittest.TestCase):
    def test_ec2_public_ip(self):
        resources = {
            'ec2_instances': [
                {'Instances': [{'InstanceId': 'i-123', 'PublicIpAddress': '1.2.3.4'}]},
                {'Instances': [{'InstanceId': 'i-456'}]}
            ]
        }
        findings = evaluate_all_rules(resources)
        self.assertTrue(any(f['resource_id'] == 'i-123' for f in findings))
        self.assertFalse(any(f['resource_id'] == 'i-456' for f in findings))

if __name__ == '__main__':
    unittest.main()
