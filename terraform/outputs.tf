# Salidas del Repositorio ECR
output "ecr_repository_url" {
  description = "URL del repositorio ECR"
  value       = module.ecr.repository_url
}



# Salidas de las funciones Lambda
output "lambda_rethrieve_qa" {
  description = "Nombre de la función Lambda para traer información de neo4j"
  value       = module.lambda_rethrieve_qa.lambda_function_name
}

output "lambda_json_to_knowledge" {
  description = "Nombre de la función Lambda para crear el Knowledgebase"
  value       = module.lambda_json_to_knowledge.lambda_function_name
}

output "api_gateway_talmagenai" {
  description = "ID de api gateway"
  value       = module.api_gateway_talmagenai.api_gateway_id
}