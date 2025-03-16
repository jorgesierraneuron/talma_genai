variable "env" {
  description = "Environment name (e.g., dev, prod)"
  type        = string
}

variable "ecr_repo_name" {
  description = "Name of the ECR repository"
  type        = string
}

variable "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  type        = string
}

variable "dynamodb_billing_mode" {
  description = "Billing mode for DynamoDB (PROVISIONED or PAY_PER_REQUEST)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "dynamodb_partition_key" {
  description = "Partition key for DynamoDB"
  type        = string
}

variable "dynamodb_partition_key_type" {
  description = "Partition key type (S, N, or B)"
  type        = string
}

variable "artifacts_bucket_name" {
  description = "S3 bucket name for Terraform state storage"
  type        = string
}