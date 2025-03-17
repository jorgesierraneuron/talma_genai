output "lambda_rethrieve_qa_processor" {
  description = "Nombre de la función Lambda para traer información de neo4j"
  value       = module.lambda_rethrieve_qa_processor.function_name 
}


output "lambda_rethrieve_qa_endpoint" {
  description = "Nombre de la función Lambda para traer información de neo4j"
  value       = module.lambda_rethrieve_qa_endpoint.function_name
}


output "api_gateway_invoke_url" {
  value = aws_apigatewayv2_api.lambda_api.api_endpoint
}
