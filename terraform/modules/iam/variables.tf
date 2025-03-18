variable "aws_region" {
  description = "AWS Region"
  type        = string
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "role_name" {
  description = "IAM role name for Lambda"
  type        = string
}

# ✅ SNS Topic Name (Replaced SQS)
variable "sns_topic_name" {
  description = "Name of the SNS topic that triggers Lambda"
  type        = string
  default     = "rethrieve_qa"
}

# ✅ Lambda Function Name
variable "lambda_function_name" {
  description = "The base name of the Lambda function"
  type        = string
}

# ✅ Environment (e.g., dev, prod, staging)
variable "environment" {
  description = "Deployment environment"
  type        = string
}
