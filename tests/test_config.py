"""
Test configuration for Task 7 Profile Setup Integration Tests
"""

import os
import tempfile
from typing import Dict, Any
from pathlib import Path

class TestConfig:
    """Centralized test configuration"""
    
    # Environment settings
    TEST_ENV = os.getenv("TEST_ENV", "test")
    CI_MODE = os.getenv("CI", "false").lower() == "true"
    
    # API endpoints
    BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:3000")
    API_URL = os.getenv("TEST_API_URL", "http://localhost:8000")
    
    # Database settings
    TEST_DB_URL = os.getenv("TEST_SUPABASE_URL", "")
    TEST_DB_KEY = os.getenv("TEST_SUPABASE_SERVICE_KEY", "")
    
    # Test data settings
    TEST_DATA_DIR = Path(__file__).parent / "test_data"
    TEMP_DIR = Path(tempfile.gettempdir()) / "wingman_tests"
    
    # Performance thresholds
    MAX_RESPONSE_TIME = float(os.getenv("TEST_MAX_RESPONSE_TIME", "2.0"))
    MAX_UPLOAD_TIME = float(os.getenv("TEST_MAX_UPLOAD_TIME", "30.0"))
    MAX_MEMORY_INCREASE_MB = int(os.getenv("TEST_MAX_MEMORY_MB", "50"))
    
    # Security settings
    ENABLE_SECURITY_TESTS = os.getenv("TEST_SECURITY", "true").lower() == "true"
    ENABLE_LOAD_TESTS = os.getenv("TEST_LOAD", "true").lower() == "true"
    
    # File upload settings
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    
    # Test timeouts
    DEFAULT_TIMEOUT = 30.0
    UPLOAD_TIMEOUT = 60.0
    DATABASE_TIMEOUT = 10.0
    
    @classmethod
    def get_test_user_data(cls) -> Dict[str, Any]:
        """Get test user data"""
        return {
            "bio": "I'm a software engineer who loves hiking and meeting new people. Looking for a confident wingman buddy to practice social skills!",
            "location": {
                "lat": 37.7749,
                "lng": -122.4194,
                "city": "San Francisco",
                "privacy_mode": "precise"
            },
            "travel_radius": 25,
            "photo_url": "https://example.com/storage/profile-photos/test-photo.jpg"
        }
    
    @classmethod
    def get_invalid_test_data(cls) -> Dict[str, Dict[str, Any]]:
        """Get invalid test data for negative testing"""
        return {
            "bio_too_short": {
                **cls.get_test_user_data(),
                "bio": "Short"
            },
            "bio_too_long": {
                **cls.get_test_user_data(),
                "bio": "x" * 401
            },
            "bio_with_pii": {
                **cls.get_test_user_data(),
                "bio": "Call me at 555-123-4567 or email test@example.com"
            },
            "invalid_lat": {
                **cls.get_test_user_data(),
                "location": {
                    "lat": 91.0,
                    "lng": -122.4194,
                    "city": "San Francisco",
                    "privacy_mode": "precise"
                }
            },
            "invalid_lng": {
                **cls.get_test_user_data(),
                "location": {
                    "lat": 37.7749,
                    "lng": 181.0,
                    "city": "San Francisco", 
                    "privacy_mode": "precise"
                }
            },
            "invalid_radius": {
                **cls.get_test_user_data(),
                "travel_radius": 51
            },
            "invalid_privacy_mode": {
                **cls.get_test_user_data(),
                "location": {
                    "lat": 37.7749,
                    "lng": -122.4194,
                    "city": "San Francisco",
                    "privacy_mode": "invalid"
                }
            }
        }
    
    @classmethod
    def setup_test_directories(cls):
        """Setup test directories"""
        cls.TEST_DATA_DIR.mkdir(exist_ok=True)
        cls.TEMP_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def cleanup_test_directories(cls):
        """Cleanup test directories"""
        import shutil
        if cls.TEMP_DIR.exists():
            shutil.rmtree(cls.TEMP_DIR, ignore_errors=True)

# Test data generators
class TestDataGenerator:
    """Generate test data for various scenarios"""
    
    @staticmethod
    def create_jpeg_bytes(size: int = 1024) -> bytes:
        """Create a valid JPEG file as bytes"""
        # JPEG file signature
        jpeg_header = b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00'
        # Fill with dummy data
        content = jpeg_header + b'\x00' * (size - len(jpeg_header) - 2)
        # JPEG end marker
        content += b'\xFF\xD9'
        return content
    
    @staticmethod
    def create_png_bytes(size: int = 1024) -> bytes:
        """Create a valid PNG file as bytes"""
        # PNG file signature
        png_header = b'\x89PNG\r\n\x1a\n'
        # IHDR chunk (basic header)
        ihdr = b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
        # Fill remaining space
        remaining = size - len(png_header) - len(ihdr) - 12  # 12 for IEND chunk
        idat = b'\x00\x00\x00\x00IDAT' + b'\x00' * max(0, remaining - 6) + b'\x00\x00\x00\x00'
        # PNG end chunk
        iend = b'\x00\x00\x00\x00IEND\xaeB`\x82'
        
        return png_header + ihdr + idat + iend
    
    @staticmethod
    def create_malicious_bytes(size: int = 1024) -> bytes:
        """Create malicious file disguised as image"""
        # Start with JPEG header
        fake_header = b'\xFF\xD8\xFF\xE0'
        # Add executable signature
        pe_header = b'MZ\x90\x00'  # Windows PE
        # Fill rest with random data
        content = fake_header + pe_header + b'\x00' * (size - 8)
        return content
    
    @staticmethod
    def create_oversized_bytes() -> bytes:
        """Create file exceeding size limits"""
        return TestDataGenerator.create_jpeg_bytes(6 * 1024 * 1024)  # 6MB
    
    @staticmethod
    def create_test_files(test_dir: Path) -> Dict[str, Path]:
        """Create various test files in given directory"""
        files = {}
        
        # Valid files
        files['valid_jpeg'] = test_dir / "valid.jpg"
        files['valid_jpeg'].write_bytes(TestDataGenerator.create_jpeg_bytes(1024 * 1024))
        
        files['valid_png'] = test_dir / "valid.png"
        files['valid_png'].write_bytes(TestDataGenerator.create_png_bytes(512 * 1024))
        
        # Invalid files
        files['oversized'] = test_dir / "oversized.jpg"
        files['oversized'].write_bytes(TestDataGenerator.create_oversized_bytes())
        
        files['malicious'] = test_dir / "malicious.jpg"
        files['malicious'].write_bytes(TestDataGenerator.create_malicious_bytes(1024))
        
        # Text file disguised as image
        files['fake_image'] = test_dir / "fake.jpg"
        files['fake_image'].write_text("This is not an image file")
        
        return files

# Performance monitoring utilities
class PerformanceMonitor:
    """Monitor test performance metrics"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.memory_start = None
        self.memory_end = None
    
    def start(self):
        """Start monitoring"""
        import time
        import psutil
        import os
        
        self.start_time = time.time()
        process = psutil.Process(os.getpid())
        self.memory_start = process.memory_info().rss
    
    def stop(self):
        """Stop monitoring and return metrics"""
        import time
        import psutil
        import os
        
        self.end_time = time.time()
        process = psutil.Process(os.getpid())
        self.memory_end = process.memory_info().rss
        
        return {
            'execution_time': self.end_time - self.start_time,
            'memory_used_mb': (self.memory_end - self.memory_start) / (1024 * 1024),
            'memory_start_mb': self.memory_start / (1024 * 1024),
            'memory_end_mb': self.memory_end / (1024 * 1024)
        }

# Test result validation utilities
class TestValidator:
    """Validate test results and assertions"""
    
    @staticmethod
    def validate_api_response(response_data: Dict[str, Any], expected_fields: list) -> bool:
        """Validate API response contains expected fields"""
        return all(field in response_data for field in expected_fields)
    
    @staticmethod
    def validate_performance_metrics(metrics: Dict[str, float], thresholds: Dict[str, float]) -> Dict[str, bool]:
        """Validate performance metrics against thresholds"""
        results = {}
        for metric, value in metrics.items():
            threshold = thresholds.get(metric, float('inf'))
            results[metric] = value <= threshold
        return results
    
    @staticmethod
    def validate_security_headers(headers: Dict[str, str]) -> Dict[str, bool]:
        """Validate security headers in HTTP response"""
        security_checks = {
            'has_cors_headers': 'access-control-allow-origin' in headers,
            'has_content_type': 'content-type' in headers,
            'no_server_info': 'server' not in headers or 'nginx' not in headers.get('server', '').lower()
        }
        return security_checks

# Export configuration
test_config = TestConfig()
test_data_generator = TestDataGenerator()
performance_monitor = PerformanceMonitor()
test_validator = TestValidator()
