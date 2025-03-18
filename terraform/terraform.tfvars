# AWS Region
aws_region = "us-east-1"

# Environment (dev, test, prod)
environment = "dev"

# IAM Role for Lambda
lambda_role_name = "lambda-execution-role"

# SQS Queue
sns_topic_name = "rethieve_qa"

# Lambda Function Names
rethrieve_qa_endpoint_name   = "rethrieve-qa-endpoint"
rethrieve_qa_processor_name  = "rethrieve-qa-processor"

# Lambda Settings
lambda_timeout = 900  # Timeout in seconds


ecr_repository_url = "911167907421.dkr.ecr.us-east-1.amazonaws.com/talmaai-docker-repo"

apigateway_name = "rethrieve_qa_api"

memory_size = 3008
