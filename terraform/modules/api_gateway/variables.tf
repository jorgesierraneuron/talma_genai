variable "api_gateway_name" {
  description = "Name of the API Gateway"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "lambda_function_name" {
  description = "Lambda function name"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

variable "integration_timeout" {
  description = "Timeout for API Gateway integration in milliseconds (default 29000)"
  type        = number
  default     = 29000
}
