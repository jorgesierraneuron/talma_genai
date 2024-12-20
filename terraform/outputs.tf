# Salidas del Repositorio ECR
output "ecr_repository_url" {
  description = "URL del repositorio ECR"
  value       = module.ecr.repository_url
}

# Salidas de la cola SQS
output "sqs_queue_url" {
  description = "URL de la cola SQS"
  value       = module.sqs.queue_url
}

output "sqs_queue_arn" {
  description = "ARN de la cola SQS"
  value       = module.sqs.queue_arn
}

# Salidas de las funciones Lambda
output "lambda_clean_files_name" {
  description = "Nombre de la función Lambda para clean-files"
  value       = module.lambda_clean_files.lambda_function_name
}

output "lambda_convert_json_name" {
  description = "Nombre de la función Lambda para convertir JSON"
  value       = module.lambda_convert_json.lambda_function_name
}
