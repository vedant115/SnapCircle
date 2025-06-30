import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AWSConfig:
    """AWS S3 configuration and client management."""
    
    def __init__(self):
        self.access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.bucket_name = os.getenv("S3_BUCKET_NAME")
        self.bucket_url = os.getenv("S3_BUCKET_URL")
        self.use_s3_storage = os.getenv("USE_S3_STORAGE", "false").lower() == "true"
        
        # Validate required configuration
        if self.use_s3_storage:
            self._validate_config()
        
        self._s3_client = None
    
    def _validate_config(self):
        """Validate that all required AWS configuration is present."""
        required_vars = [
            ("AWS_ACCESS_KEY_ID", self.access_key_id),
            ("AWS_SECRET_ACCESS_KEY", self.secret_access_key),
            ("S3_BUCKET_NAME", self.bucket_name),
            ("S3_BUCKET_URL", self.bucket_url)
        ]
        
        missing_vars = [var_name for var_name, var_value in required_vars if not var_value]
        
        if missing_vars:
            raise ValueError(
                f"Missing required AWS configuration variables: {', '.join(missing_vars)}. "
                f"Please set these in your .env file or set USE_S3_STORAGE=false to use local storage."
            )
    
    @property
    def s3_client(self):
        """Get or create S3 client."""
        if not self.use_s3_storage:
            raise ValueError("S3 storage is disabled. Set USE_S3_STORAGE=true to enable.")
        
        if self._s3_client is None:
            try:
                self._s3_client = boto3.client(
                    's3',
                    aws_access_key_id=self.access_key_id,
                    aws_secret_access_key=self.secret_access_key,
                    region_name=self.region
                )
                # Test the connection
                self._s3_client.head_bucket(Bucket=self.bucket_name)
            except NoCredentialsError:
                raise ValueError("AWS credentials not found. Please check your AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    raise ValueError(f"S3 bucket '{self.bucket_name}' not found.")
                elif error_code == '403':
                    raise ValueError(f"Access denied to S3 bucket '{self.bucket_name}'. Please check your AWS credentials and bucket permissions.")
                else:
                    raise ValueError(f"Error connecting to S3: {e}")
        
        return self._s3_client
    
    def test_connection(self):
        """Test the S3 connection and return status."""
        if not self.use_s3_storage:
            return {"status": "disabled", "message": "S3 storage is disabled"}
        
        try:
            # Test connection by listing objects (limit to 1)
            self.s3_client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=1)
            return {"status": "success", "message": "S3 connection successful"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Global instance
aws_config = AWSConfig()
