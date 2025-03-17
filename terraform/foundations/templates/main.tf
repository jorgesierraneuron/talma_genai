provider "aws" {
  region = "us-east-1" # Change as needed
}

resource "aws_ecr_repository" "ecr_repo" {
  name = "${var.app_prefix}-${var.ecr_repo_name}-${var.env}"
}

resource "aws_dynamodb_table" "dynamodb_table" {
  name         = "${var.app_prefix}-${var.dynamodb_table_name}-${var.env}"
  billing_mode = var.dynamodb_billing_mode

  attribute {
    name = var.dynamodb_partition_key
    type = var.dynamodb_partition_key_type
  }

  hash_key = var.dynamodb_partition_key
}

resource "aws_s3_bucket" "artifacts_bucket" {
  bucket = "${var.app_prefix}-${var.artifacts_bucket_name}-${var.env}"
}
