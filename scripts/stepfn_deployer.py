import boto3
import json
from botocore.exceptions import ClientError

class StepFunctionDeployer:
    def __init__(self, region, role_arn):
        self.sfn = boto3.client('stepfunctions', region_name=region)
        self.role_arn = role_arn

    def create_or_update_sfn(self, name, definition):
        try:
            print(f"⚙️  Deploying State Machine: {name}...")
            response = self.sfn.create_state_machine(
                name=name,
                definition=json.dumps(definition),
                roleArn=self.role_arn,
                type='STANDARD'
            )
            print(f"✅ State Machine {name} created.")
            return response['stateMachineArn']
        except ClientError as e:
            if e.response['Error']['Code'] == 'StateMachineAlreadyExists':
                print(f"🔄 Updating existing State Machine: {name}...")
                # We need the ARN to update
                list_response = self.sfn.list_state_machines()
                sfn_arn = next(s for s in list_response['stateMachines'] if s['name'] == name)['stateMachineArn']
                self.sfn.update_state_machine(
                    stateMachineArn=sfn_arn,
                    definition=json.dumps(definition),
                    roleArn=self.role_arn
                )
                print(f"✅ {name} updated.")
                return sfn_arn
            raise e