output "lambda_function_name" {
  description = "Nombre de la función Lambda"
  value       = aws_lambda_function.lambda_function.function_name
}
