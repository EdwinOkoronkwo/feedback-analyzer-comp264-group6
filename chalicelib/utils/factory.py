import boto3
from chalicelib.analytics.athena_provider import AthenaAnalyticsProvider
from chalicelib.analytics.schema_manager import AthenaSchemaManager
from chalicelib.ingestion.web_ingestor import WebIngestor
from chalicelib.persistence.s3_repository import S3Repository
from chalicelib.persistence.user_repository import UserRepository
from chalicelib.persistence.feedback_repository import FeedbackRepository
from chalicelib.auth.user_manager import UserManager

# --- AWS Cloud Providers ---
from chalicelib.providers.aws_translator import AWSTranslateProvider
from chalicelib.providers.sentiment_analyzer import AWSComprehendProvider
from chalicelib.providers.mistral_provider import MistralAnalyzer

from chalicelib.sanitizer.feedback_sanitizer import FeedbackSanitizer
from web.config import settings
from .logger import FileAuditLogger
from .security import SimpleDataProtector
from ..pipeline import FeedbackAnalysisPipeline

class PipelineFactory:
    @staticmethod
    def create_pipeline_and_auth():
        """
        Assembles the AWS Cloud Architecture.
        Uses managed services (Translate, Comprehend, Mistral API).
        """
        # 1. Infrastructure
        logger = FileAuditLogger(name="AWS_Pipeline")
        security = SimpleDataProtector()
        db_resource = boto3.resource('dynamodb') 

        # 2. Persistence (Cloud Repos)
        user_repo = UserRepository(db_resource, logger)
        feedback_repo = FeedbackRepository(
            db_resource, 
            logger, 
            table_name=settings.DYNAMODB_TABLE
        )
        s3_repo = S3Repository(bucket_name=settings.S3_BUCKET_NAME)
        
        # 3. Ingestion & Sanitization
        ingestor = WebIngestor(logger=logger)
        sanitizer = FeedbackSanitizer(logger=logger)
        
        # 4. AWS Managed Providers (The Cloud "Engine")
        # These replace the gTTS and Ollama logic used in LocalPipelineFactory
        translator = AWSTranslateProvider(logger=logger)
        analyzer = AWSComprehendProvider(logger=logger)
        summarizer = MistralAnalyzer(logger=logger) # Uses the API, not local
        
        # 5. Logic Orchestration
        user_manager = UserManager(user_repo, logger)
        
        pipeline = FeedbackAnalysisPipeline(
            ingestor=ingestor,
            sanitizer=sanitizer,
            security=security,
            translator=translator,
            analyzer=analyzer,
            summarizer=summarizer,
            persistence=feedback_repo,
            logger=logger,
            s3_storage=s3_repo 
        )
        
        return pipeline, user_manager

    @staticmethod
    def get_analytics_layer():
        """
        Assembles Athena for Cloud Analytics.
        """
        database_name = "feedback_analytics"
        bucket = settings.S3_BUCKET_NAME
        s3_results = f"s3://{bucket}/athena-results/"
        
        provider = AthenaAnalyticsProvider(
            database=database_name, 
            s3_output=s3_results
        )
        
        # Ensure Athena is looking at the live S3 data location
        provider.update_location()
        
        manager = AthenaSchemaManager(database=database_name)
        
        return provider, manager





# import boto3
# from chalicelib.analytics.athena_provider import AthenaAnalyticsProvider
# from chalicelib.analytics.schema_manager import AthenaSchemaManager
# from chalicelib.ingestion.web_ingestor import WebIngestor
# # Import the new Repositories instead of the old Storage
# from chalicelib.persistence.s3_repository import S3Repository
# from chalicelib.persistence.user_repository import UserRepository
# from chalicelib.persistence.feedback_repository import FeedbackRepository
# from chalicelib.auth.user_manager import UserManager
# from chalicelib.providers.aws_translator import AWSTranslateProvider
# from chalicelib.providers.mistral_provider import MistralAnalyzer
# from chalicelib.providers.sentiment_analyzer import AWSComprehendProvider
# from chalicelib.sanitizer.feedback_sanitizer import FeedbackSanitizer
# from web.config import settings
# from .logger import FileAuditLogger
# from .security import SimpleDataProtector
# from ..pipeline import FeedbackAnalysisPipeline

# class PipelineFactory:
#     @staticmethod
#     def create_pipeline_and_auth():
#         """
#         Assembles the entire N-Tier architecture.
#         Satisfies Deliverable 5: Separation of Concerns & Single Responsibility.
#         """
#         # 1. Initialize Cross-Cutting Infrastructure
#         logger = FileAuditLogger(name="PipelineFactory")
#         security = SimpleDataProtector()
#         db_resource = boto3.resource('dynamodb') # Shared AWS Connection

#         # 2. Initialize Persistence Layer (Repositories)
#         # We split the concerns into User vs. Feedback
#         user_repo = UserRepository(db_resource, logger)
#         feedback_repo = FeedbackRepository(db_resource, logger, table_name=settings.DYNAMODB_TABLE)
        
#         # 3. Initialize Ingestion & Processing Layers
#         ingestor = WebIngestor(logger=logger)
#         sanitizer = FeedbackSanitizer(logger=logger)
#         translator = AWSTranslateProvider(logger=logger)
#         analyzer = AWSComprehendProvider(logger=logger)
#         summarizer = MistralAnalyzer(logger=logger)
        
#         # 4. Initialize Logic Managers (Orchestration)
#         user_manager = UserManager(user_repo, logger)
#         s3_repo = S3Repository(bucket_name=settings.S3_BUCKET_NAME)
        
#         pipeline = FeedbackAnalysisPipeline(
#             ingestor=ingestor,
#             sanitizer=sanitizer,
#             security=security,
#             translator=translator,
#             analyzer=analyzer,
#             summarizer=summarizer,
#             persistence=feedback_repo,
#             logger=logger,
#             s3_storage=s3_repo 
#         )
        
#         return pipeline, user_manager

#     @staticmethod
#     def get_analytics_layer():
#         """
#         Assembles the Analytics components for the UI.
#         Fixes the 'Total not updating' issue by repointing Athena to live-data.
#         """
#         database_name = "feedback_analytics"
#         # We need the bucket name from settings to build the path
#         bucket = settings.S3_BUCKET_NAME
#         s3_results = f"s3://{bucket}/athena-results/"
        
#         # 1. Initialize the Provider
#         provider = AthenaAnalyticsProvider(
#             database=database_name, 
#             s3_output=s3_results
#         )
        
#         # 2. PROGRAMMATIC FIX: Repoint Athena to the live-data folder
#         # This ensures the 'Total' and 'Summary' use the latest Lambda-synced files
#         provider.update_location()
        
#         # 3. The Manager for handling metadata (optional/preservation)
#         manager = AthenaSchemaManager(database=database_name)
        
#         return provider, manager