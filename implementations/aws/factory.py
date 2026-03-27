import os
import boto3
from chalicelib.sanitizer.feedback_sanitizer import FeedbackSanitizer
from chalicelib.security.simple_data_protector import SimpleDataProtector
from implementations.aws.pipeline import FeedbackAnalysisPipeline
# Ensure settings is used or removed if not needed
from web.config import settings

# --- Specialized AWS Implementation Imports ---
from .repositories.user_repo import AWSUserRepository
from .repositories.summary_repo import AWSSummaryRepository
from .repositories.metadata_repo import AWSMetadataRepository
from .providers.translate import AWSTranslateProvider
from .providers.sentiment import AWSComprehendProvider
from .providers.analyzer import MistralAnalyzer
# Fixed: Importing AthenaAnalyticsProvider to use in the getter
from .providers.analytics import AthenaAnalyticsProvider 

# --- Agnostic Domain Logic ---
from chalicelib.services.user_service import UserService
from chalicelib.services.metadata_service import MetadataService
from chalicelib.services.aggregator import FeedbackAggregatorService, SummaryService
from chalicelib.utils.logger import FileAuditLogger
from chalicelib.ingestion.web_ingestor import WebIngestor

# --- GLOBAL CONFIG FROM .ENV ---
# We pull the region once here so all methods can see it
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

class AWSPipelineFactory:
    @staticmethod
    def create_pipeline_and_auth():
        logger = FileAuditLogger(name="AWS_Pipeline")
        
        # Use the AWS_REGION variable here
        db = boto3.resource('dynamodb', region_name=AWS_REGION)
        bucket = os.getenv("S3_BUCKET_NAME")

        persistence = AWSPipelineFactory._build_persistence(db, logger)
        providers = AWSPipelineFactory._build_providers(logger)
        components = AWSPipelineFactory._build_components(logger)

        pipeline = FeedbackAnalysisPipeline(
            ingestor=components['ingestor'],
            sanitizer=components['sanitizer'],
            security=components['security'],
            translator=providers['translator'],
            analyzer=providers['analyzer'],
            persistence=persistence, 
            logger=logger,
            # Creating a mock object for S3 configuration
            s3_storage=type('S3', (object,), {'bucket_name': bucket}),
            summarizer=providers['summarizer']
        )
        
        user_repo = AWSUserRepository(db, logger)
        user_service = UserService(user_repo, logger=logger)

        return pipeline, user_service

    @staticmethod
    def _build_persistence(db, logger):
        meta_repo = AWSMetadataRepository(db, logger)
        sum_repo = AWSSummaryRepository(db, logger)
        meta_service = MetadataService(meta_repo)
        sum_service = SummaryService(sum_repo)
        return FeedbackAggregatorService(meta_service, sum_service)

    @staticmethod
    def _build_providers(logger):
        return {
            "translator": AWSTranslateProvider(logger=logger),
            "analyzer": AWSComprehendProvider(logger=logger),
            "summarizer": MistralAnalyzer(logger=logger)
        }

    @staticmethod
    def _build_components(logger):
        return {
            "ingestor": WebIngestor(logger=logger),
            "sanitizer": FeedbackSanitizer(logger=logger),
            "security": SimpleDataProtector() 
        }

    @staticmethod
    def get_analytics_layer():
        """
        Returns (Provider, Workgroup) using your .env AWS_REGION.
        """
        workgroup = os.getenv("ATHENA_WORKGROUP", "primary")
        
        # Fixed: Using AthenaAnalyticsProvider (the name from your import)
        # Fixed: Using AWS_REGION instead of the undefined REGION
        provider = AthenaAnalyticsProvider(region=AWS_REGION, workgroup=workgroup)
        
        return provider, workgroup