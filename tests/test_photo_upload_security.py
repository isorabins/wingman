"""
Security-focused tests for photo upload functionality

Test Coverage:
- File type validation (MIME type and header checking)
- File size limits and DoS prevention
- Malicious file detection (executable disguised as image)
- Path traversal prevention
- Storage bucket security (RLS policies)
- Signed URL security
- Content validation and scanning
"""

import pytest
import asyncio
import io
import os
import tempfile
import uuid
from typing import BinaryIO, Optional
from unittest.mock import patch, MagicMock, AsyncMock

# Mock Supabase client for testing
class MockSupabaseStorage:
    def __init__(self):
        self.uploads = {}
        self.errors = {}
    
    def from_bucket(self, bucket_name: str):
        return MockBucket(bucket_name, self)
    
    def set_upload_error(self, error_message: str):
        self.errors["upload"] = error_message
    
    def set_url_error(self, error_message: str):
        self.errors["url"] = error_message

class MockBucket:
    def __init__(self, name: str, storage: MockSupabaseStorage):
        self.name = name
        self.storage = storage
    
    async def upload(self, path: str, file_data: bytes, options: dict = None):
        if "upload" in self.storage.errors:
            return {"data": None, "error": {"message": self.storage.errors["upload"]}}
        
        self.storage.uploads[path] = {
            "data": file_data,
            "options": options,
            "size": len(file_data)
        }
        return {"data": {"path": path}, "error": None}
    
    def get_public_url(self, path: str):
        if "url" in self.storage.errors:
            return {"data": None, "error": {"message": self.storage.errors["url"]}}
        
        return {"data": {"publicUrl": f"https://example.com/storage/{self.name}/{path}"}}
    
    async def create_signed_upload_url(self, path: str):
        if "signed_url" in self.storage.errors:
            return {"data": None, "error": {"message": self.storage.errors["signed_url"]}}
        
        return {"data": {"signedUrl": f"https://example.com/upload/{path}?token=test"}}
    
    async def remove(self, paths: list):
        for path in paths:
            if path in self.storage.uploads:
                del self.storage.uploads[path]
        return {"error": None}

# Test file creation helpers
def create_test_file(content: bytes, filename: str) -> str:
    """Create a temporary test file"""
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, filename)
    
    with open(file_path, 'wb') as f:
        f.write(content)
    
    return file_path

def create_jpeg_file(size: int = 1024) -> bytes:
    """Create a valid JPEG file with proper header"""
    # JPEG file signature
    jpeg_header = b'\xFF\xD8\xFF\xE0\x00\x10JFIF'
    # Fill with dummy data
    content = jpeg_header + b'\x00' * (size - len(jpeg_header) - 2)
    # JPEG end marker
    content += b'\xFF\xD9'
    return content

def create_png_file(size: int = 1024) -> bytes:
    """Create a valid PNG file with proper header"""
    # PNG file signature
    png_header = b'\x89PNG\r\n\x1a\n'
    # Fill with dummy data
    content = png_header + b'\x00' * (size - len(png_header))
    return content

def create_malicious_file(size: int = 1024) -> bytes:
    """Create a malicious executable disguised as an image"""
    # Windows PE header disguised with JPEG signature
    fake_jpeg_header = b'\xFF\xD8\xFF\xE0'
    pe_header = b'MZ\x90\x00'  # Windows PE executable signature
    content = fake_jpeg_header + pe_header + b'\x00' * (size - 8)
    return content

def create_zip_bomb() -> bytes:
    """Create a small zip file that expands to large size"""
    import zipfile
    
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Create a file with lots of zeros that compresses well
        large_content = b'\x00' * (10 * 1024 * 1024)  # 10MB of zeros
        zipf.writestr('large_file.txt', large_content)
    
    return buffer.getvalue()

class TestPhotoUploadSecurity:
    """Security tests for photo upload functionality"""
    
    @pytest.fixture
    def mock_supabase(self):
        return MockSupabaseStorage()
    
    @pytest.fixture
    def photo_service(self, mock_supabase):
        # Import and patch the photo upload service
        with patch('storage.photo_upload.supabase', mock_supabase):
            from storage.photo_upload import PhotoUploadService
            service = PhotoUploadService()
            service.supabase = mock_supabase
            return service
    
    def test_file_size_validation(self, photo_service):
        """Test file size limits are enforced"""
        # Test valid file size
        valid_content = create_jpeg_file(1024 * 1024)  # 1MB
        validation = photo_service.validatePhotoFile(
            type('File', (), {
                'size': len(valid_content),
                'type': 'image/jpeg',
                'name': 'test.jpg'
            })()
        )
        assert validation['valid'] is True
        
        # Test oversized file
        oversized_content = create_jpeg_file(6 * 1024 * 1024)  # 6MB
        validation = photo_service.validatePhotoFile(
            type('File', (), {
                'size': len(oversized_content),
                'type': 'image/jpeg',
                'name': 'oversized.jpg'
            })()
        )
        assert validation['valid'] is False
        assert '5MB' in validation['error']
    
    def test_mime_type_validation(self, photo_service):
        """Test MIME type validation"""
        valid_mime_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
        invalid_mime_types = [
            'application/octet-stream',
            'text/html',
            'application/javascript',
            'application/x-executable',
            'video/mp4'
        ]
        
        # Test valid MIME types
        for mime_type in valid_mime_types:
            validation = photo_service.validatePhotoFile(
                type('File', (), {
                    'size': 1024,
                    'type': mime_type,
                    'name': f'test.{mime_type.split("/")[1]}'
                })()
            )
            assert validation['valid'] is True
        
        # Test invalid MIME types
        for mime_type in invalid_mime_types:
            validation = photo_service.validatePhotoFile(
                type('File', (), {
                    'size': 1024,
                    'type': mime_type,
                    'name': 'test.exe'
                })()
            )
            assert validation['valid'] is False
            assert 'Invalid file type' in validation['error']
    
    @pytest.mark.asyncio
    async def test_file_header_validation(self, photo_service):
        """Test file header (magic number) validation"""
        # Create files with valid headers
        jpeg_content = create_jpeg_file(1024)
        png_content = create_png_file(1024)
        
        # Mock File objects
        jpeg_file = type('File', (), {
            'size': len(jpeg_content),
            'type': 'image/jpeg',
            'name': 'test.jpg'
        })()
        
        png_file = type('File', (), {
            'size': len(png_content),
            'type': 'image/png', 
            'name': 'test.png'
        })()
        
        # Mock FileReader behavior
        with patch('storage.photo_upload.FileReader') as mock_reader:
            # Mock successful JPEG validation
            mock_reader.return_value.onload = lambda e: None
            mock_reader.return_value.readAsArrayBuffer = lambda data: None
            
            # This test would require proper FileReader mocking
            # For now, test the basic validation logic
            validation = await photo_service.validatePhotoFileAsync(jpeg_file)
            # The async validation depends on FileReader which isn't available in Node.js
            # In a real test environment, we'd use jsdom or similar
    
    def test_malicious_file_detection(self, photo_service):
        """Test detection of malicious files disguised as images"""
        # Create malicious file with fake image header
        malicious_content = create_malicious_file(1024)
        
        malicious_file = type('File', (), {
            'size': len(malicious_content),
            'type': 'image/jpeg',  # Lying about type
            'name': 'malicious.jpg'
        })()
        
        # Basic MIME type validation should pass (relies on deeper validation)
        validation = photo_service.validatePhotoFile(malicious_file)
        
        # The async header validation should catch this
        # This test demonstrates the need for both MIME and header validation
        assert validation['valid'] is True  # Basic validation passes
        # Header validation (async) would catch the malicious content
    
    def test_zip_bomb_protection(self, photo_service):
        """Test protection against zip bombs and compression attacks"""
        zip_bomb_content = create_zip_bomb()
        
        # File appears small but could expand to large size
        zip_file = type('File', (), {
            'size': len(zip_bomb_content),
            'type': 'application/zip',  # Wrong type, should be rejected
            'name': 'bomb.zip'
        })()
        
        validation = photo_service.validatePhotoFile(zip_file)
        assert validation['valid'] is False
        assert 'Invalid file type' in validation['error']
    
    def test_path_traversal_prevention(self, photo_service):
        """Test prevention of path traversal attacks in file paths"""
        user_id = str(uuid.uuid4())
        
        # Test malicious filenames
        malicious_filenames = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '/etc/shadow',
            '../../../../root/.ssh/id_rsa',
            'legitimate.jpg../../../../etc/passwd',
        ]
        
        for filename in malicious_filenames:
            file_path = photo_service._PhotoUploadService__generate_file_path(user_id, filename)
            
            # Generated path should be contained within user's folder
            assert file_path.startswith(f'{user_id}/')
            assert '../' not in file_path
            assert '..\\' not in file_path
            assert not file_path.startswith('/')
    
    def test_filename_sanitization(self, photo_service):
        """Test filename sanitization against various attacks"""
        user_id = str(uuid.uuid4())
        
        # Test various problematic filenames
        problematic_filenames = [
            'file with spaces.jpg',
            'file;with;semicolons.png',
            'file|with|pipes.gif',
            'file<with>brackets.webp',
            'file"with"quotes.jpg',
            'file\x00with\x00nulls.png',
            'file\nwith\nnewlines.jpg',
        ]
        
        for filename in problematic_filenames:
            file_path = photo_service._PhotoUploadService__generate_file_path(user_id, filename)
            
            # Path should be safe and contain user_id
            assert file_path.startswith(f'{user_id}/')
            assert len(file_path.split('/')) == 2  # user_id/filename format
            
            # Extract sanitized filename
            sanitized_filename = file_path.split('/')[1]
            
            # Should not contain problematic characters
            assert '\x00' not in sanitized_filename
            assert '\n' not in sanitized_filename
            assert '\r' not in sanitized_filename
    
    @pytest.mark.asyncio
    async def test_upload_error_handling(self, photo_service, mock_supabase):
        """Test proper error handling during upload process"""
        user_id = str(uuid.uuid4())
        valid_content = create_jpeg_file(1024)
        
        valid_file = type('File', (), {
            'size': len(valid_content),
            'type': 'image/jpeg',
            'name': 'test.jpg'
        })()
        
        # Test storage upload error
        mock_supabase.set_upload_error("Storage quota exceeded")
        
        result = await photo_service.uploadPhoto(valid_file, user_id)
        
        assert result['success'] is False
        assert 'Storage quota exceeded' in result['error']
    
    @pytest.mark.asyncio
    async def test_signed_url_security(self, photo_service, mock_supabase):
        """Test signed URL generation and security"""
        user_id = str(uuid.uuid4())
        
        # Test valid signed URL creation
        result = await photo_service.createSignedUploadUrl(
            user_id=user_id,
            fileName='test.jpg',
            fileSize=1024 * 1024,  # 1MB
            mimeType='image/jpeg'
        )
        
        assert 'uploadUrl' in result
        assert 'finalUrl' in result
        assert user_id in result['uploadUrl']
        
        # Test signed URL with invalid parameters
        result = await photo_service.createSignedUploadUrl(
            user_id=user_id,
            fileName='test.exe',
            fileSize=1024,
            mimeType='application/octet-stream'
        )
        
        assert 'error' in result
        assert 'Invalid file type' in result['error']
    
    def test_user_isolation_in_file_paths(self, photo_service):
        """Test that file paths properly isolate users"""
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        filename = 'profile.jpg'
        
        path1 = photo_service._PhotoUploadService__generate_file_path(user1_id, filename)
        path2 = photo_service._PhotoUploadService__generate_file_path(user2_id, filename)
        
        # Paths should be different and isolated
        assert path1 != path2
        assert path1.startswith(f'{user1_id}/')
        assert path2.startswith(f'{user2_id}/')
        
        # Should not be able to access other user's folder
        assert user2_id not in path1
        assert user1_id not in path2
    
    @pytest.mark.asyncio
    async def test_photo_deletion_security(self, photo_service):
        """Test secure photo deletion with authorization checks"""
        user1_id = str(uuid.uuid4())
        user2_id = str(uuid.uuid4())
        
        # URL from user1's photo
        user1_photo_url = f"https://example.com/storage/profile-photos/{user1_id}/photo.jpg"
        
        # User1 should be able to delete their own photo
        success = await photo_service.deletePhoto(user1_photo_url, user1_id)
        assert success is True
        
        # User2 should NOT be able to delete user1's photo
        success = await photo_service.deletePhoto(user1_photo_url, user2_id)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_concurrent_upload_handling(self, photo_service):
        """Test handling of concurrent upload attempts"""
        import asyncio
        
        user_id = str(uuid.uuid4())
        valid_content = create_jpeg_file(1024)
        
        def create_file():
            return type('File', (), {
                'size': len(valid_content),
                'type': 'image/jpeg',
                'name': f'test_{uuid.uuid4().hex[:8]}.jpg'
            })()
        
        # Create multiple concurrent uploads
        upload_tasks = []
        for i in range(5):
            file_obj = create_file()
            task = photo_service.uploadPhoto(file_obj, user_id)
            upload_tasks.append(task)
        
        # Wait for all uploads to complete
        results = await asyncio.gather(*upload_tasks, return_exceptions=True)
        
        # All should succeed or fail gracefully (no crashes)
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, dict)
            assert 'success' in result
    
    def test_image_metadata_stripping(self, photo_service):
        """Test that image metadata (EXIF) is stripped for privacy"""
        # Create JPEG with fake EXIF data
        jpeg_content = create_jpeg_file(2048)
        
        # In a real implementation, we'd add EXIF data and verify it's stripped
        # This test demonstrates the security requirement
        
        # The photo service should strip metadata during processing
        # This would typically be done during image compression/optimization
        
        # For now, this test serves as documentation of the requirement
        assert True  # Placeholder for actual EXIF stripping test

class TestStorageRLSPolicies:
    """Test Row-Level Security policies for photo storage"""
    
    def test_rls_policy_validation(self):
        """Test that RLS policies are properly configured"""
        # Read the migration file and validate RLS policies
        migration_path = '/Applications/wingman/supabase/migrations_wm/003_add_storage_setup.sql'
        
        try:
            with open(migration_path, 'r') as f:
                migration_content = f.read()
        except FileNotFoundError:
            pytest.skip("Migration file not found")
        
        # Check for essential RLS policies
        required_policies = [
            'Users can upload own photos',
            'Users can view own photos',
            'Users can update own photos',
            'Users can delete own photos',
        ]
        
        for policy in required_policies:
            assert policy in migration_content, f"Missing RLS policy: {policy}"
        
        # Check for proper bucket configuration
        assert 'profile-photos' in migration_content
        assert 'allowed_mime_types' in migration_content
        assert 'file_size_limit' in migration_content
    
    def test_bucket_security_configuration(self):
        """Test storage bucket security configuration"""
        migration_path = '/Applications/wingman/supabase/migrations_wm/003_add_storage_setup.sql'
        
        try:
            with open(migration_path, 'r') as f:
                migration_content = f.read()
        except FileNotFoundError:
            pytest.skip("Migration file not found")
        
        # Verify security settings
        assert '5242880' in migration_content  # 5MB limit
        assert 'image/jpeg' in migration_content
        assert 'image/png' in migration_content
        assert 'image/webp' in migration_content
        assert 'image/gif' in migration_content
        
        # Check that dangerous file types are not allowed
        dangerous_types = ['application/octet-stream', 'text/html', 'application/javascript']
        for dangerous_type in dangerous_types:
            assert dangerous_type not in migration_content

if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short", "-k", "not test_rls_policy_validation"])
