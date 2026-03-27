import boto3
# Ensure naming matches the class in local_orchestrator.py
from chalicelib.local.local_orchestrator import LocalPipelineOrchestrator
from chalicelib.providers.mistral_provider import MistralAnalyzer
from chalicelib.utils.logger import FileAuditLogger
# Import your actual Mistral provider


from chalicelib.local.local_analytics_provider import LocalAnalyticsProvider
from chalicelib.persistence.repositories import (
    UserRepository, 
    MetadataRepository, 
    SummaryRepository
)
from chalicelib.local.local_services import (
    UserService,
    MetadataService,
    SummaryService,
    FeedbackAggregatorService
)

class LocalPipelineFactory:
    @staticmethod
    def create_local_stack():
        # 1. Logger & Database Connection
        audit_logger = FileAuditLogger(name="VMware-Local-Stack")
        
        db_resource = boto3.resource(
            'dynamodb', 
            endpoint_url='http://localhost:8000',
            region_name='us-east-1',
            aws_access_key_id='local',
            aws_secret_access_key='local'
        )
        
        # 2. Instantiate Repositories
        user_repo = UserRepository(db_resource, logger=audit_logger)
        meta_repo = MetadataRepository(db_resource, logger=audit_logger)
        sum_repo = SummaryRepository(db_resource, logger=audit_logger)
        
        # 3. Instantiate AI Analyzer (Mistral)
        mistral_provider = MistralAnalyzer(logger=audit_logger)
        
        # 4. Instantiate Dedicated Services
        # Passing logger to UserService so it can log registrations/logins
        user_service = UserService(user_repo, logger=audit_logger)
        meta_service = MetadataService(meta_repo)
        sum_service = SummaryService(sum_repo)
        
        # 5. Instantiate Aggregator (The 4th Service / The Bridge)
        aggregator_service = FeedbackAggregatorService(
            meta_service=meta_service,
            summary_service=sum_service
        )
        
        # 6. Inject everything into the Orchestrator
        pipeline = LocalPipelineOrchestrator(
            persistence=aggregator_service,
            ai_analyzer=mistral_provider
        )
        
        return pipeline, user_service

    @staticmethod
    def get_local_analytics():
        return LocalAnalyticsProvider()