provider "aws" {
  region = "us-east-1" # Change as needed
}

resource "aws_ecr_repository" "ecr_repo" {
  name = var.ecr_repo_name
}

resource "aws_dynamodb_table" "dynamodb_table" {
  name         = var.dynamodb_table_name
  billing_mode = var.dynamodb_billing_mode

  attribute {
    name = var.dynamodb_partition_key
    type = var.dynamodb_partition_key_type
  }

  hash_key = var.dynamodb_partition_key
}

resource "aws_s3_bucket" "artifacts_bucket" {
  bucket = var.artifacts_bucket_name
}

