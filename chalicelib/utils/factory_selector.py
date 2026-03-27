import os
from implementations.aws.factory import AWSPipelineFactory
from implementations.local.factory import LocalPipelineFactory

class FactorySelector:
    @staticmethod
    def get_factory():
        # Looks for an environment variable; defaults to LOCAL for safety
        mode = os.getenv("ENV_MODE", "LOCAL").upper()
        
        if mode == "AWS":
            return AWSPipelineFactory, "☁️ AWS Cloud Mode"
        else:
            return LocalPipelineFactory, "💻 VMware Local Mode"