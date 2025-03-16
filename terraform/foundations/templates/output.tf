output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.ecr_repo.repository_url
}

output "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  value       = aws_dynamodb_table.dynamodb_table.arn
}