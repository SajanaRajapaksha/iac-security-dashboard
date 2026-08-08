import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.datetime_utils import format_timestamp, calculate_duration
from services.s3_service import S3Service

class TestDashboardLogic(unittest.TestCase):

    def test_datetime_formatter(self):
        start = "2026-08-08T15:50:01.449208+00:00"
        end = "2026-08-08T16:00:47.619605+00:00"
        
        start_fmt = format_timestamp(start, "Asia/Colombo")
        self.assertEqual(start_fmt, "08 Aug 2026 21:20:01")
        
        duration = calculate_duration(start, end)
        self.assertEqual(duration, "10m 46s")
        
    def test_missing_timestamps(self):
        self.assertEqual(format_timestamp("NOT_AVAILABLE"), "N/A")
        self.assertEqual(calculate_duration("NOT_AVAILABLE", "NOT_AVAILABLE"), "N/A")
        self.assertEqual(calculate_duration(None, None), "N/A")
        
    def test_finding_key_generation(self):
        f = {
            "finding_record_key": "ebc1b3d704cc9e20",
            "finding_id": "CKV_AWS_24",
            "scanner": "CHECKOV"
        }
        
        # Test fallback works for finding_key manually if finding_record_key is not there
        s3 = S3Service("bucket", "us-east-1", "profile")
        fallback_key = s3.generate_finding_key({"finding_id": "CKV_AWS_24", "scanner": "CHECKOV"})
        self.assertIsNotNone(fallback_key)
        self.assertNotEqual(fallback_key, "ebc1b3d704cc9e20")
        
if __name__ == '__main__':
    unittest.main()
