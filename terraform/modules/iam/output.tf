output "lambda_role_arn" {
  description = "ARN del rol de IAM para Lambda"
  value       = aws_iam_role.lambda_role.arn
}
