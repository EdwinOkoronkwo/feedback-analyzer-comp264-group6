import boto3
import os

from implementations.aws.providers.analyzer import MistralAnalyzer
from implementations.local.providers.analytics import LocalAnalyticsProvider

# Specialized Local Repositories
from .repositories.user_repo import LocalUserRepository
from .repositories.summary_repo import LocalSummaryRepository
from .repositories.metadata_repo import LocalMetadataRepository

# Shared Providers & Orchestrator

from implementations.local.pipeline import LocalPipelineOrchestrator

# Agnostic Domain Logic
from chalicelib.services.user_service import UserService
from chalicelib.services.metadata_service import MetadataService
from chalicelib.services.aggregator import SummaryService
from chalicelib.services.aggregator import FeedbackAggregatorService
from chalicelib.utils.logger import FileAuditLogger

# The Logic Components you just moved to chalicelib
from chalicelib.sanitizer.feedback_sanitizer import FeedbackSanitizer
from chalicelib.ingestion.web_ingestor import WebIngestor
from chalicelib.security.simple_data_protector import SimpleDataProtector

class LocalPipelineFactory:
    @staticmethod
    def create_pipeline_and_auth():
        """
        Coordinates the assembly of the local VMware processing stack.
        """
        logger = FileAuditLogger(name="VMware-Local-Stack")
        # Local DynamoDB endpoint (usually port 8000 for VMware/Docker)
        db = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')

        # 1. Use modular builders to maintain clean code
        persistence = LocalPipelineFactory._build_persistence(db, logger)
        components = LocalPipelineFactory._build_components(logger)
        
        # 2. Assemble the Local Orchestrator (Injected dependencies)
        pipeline = LocalPipelineOrchestrator(
            persistence=persistence,
            ai_analyzer=MistralAnalyzer(logger=logger),
            sanitizer=components['sanitizer'], 
            security=components['security']    
        )
        
        # 3. Separate Auth Service
        user_repo = LocalUserRepository(db, logger)
        user_service = UserService(user_repo, logger=logger)

        return pipeline, user_service

    # --- Private Modular Builders ---

    @staticmethod
    def _build_persistence(db, logger):
        """Assembles the Local Repository layer."""
        meta_repo = LocalMetadataRepository(db, logger)
        sum_repo = LocalSummaryRepository(db, logger)
        
        return FeedbackAggregatorService(
            MetadataService(meta_repo), 
            SummaryService(sum_repo)
        )

    @staticmethod
    def _build_components(logger):
        """Assembles the logic components shared with the Cloud version."""
        return {
            "ingestor": WebIngestor(logger=logger),
            "sanitizer": FeedbackSanitizer(logger=logger),
            "security": SimpleDataProtector()
        }

    @staticmethod
    def get_analytics_layer():
        """
        Standardized getter for the analytics provider.
        Returns a tuple to match the AWSPipelineFactory signature.
        """
        # 1. Create the provider (which we just fixed to be self-sufficient)
        provider = LocalAnalyticsProvider()
        
        # 2. Return (Provider, None) to satisfy the 'analytics, _' unpacking in app.py
        return provider, None