output "api_gateway_id" {
  description = "The ID of the API Gateway"
  value       = aws_api_gateway_rest_api.api_gateway.id
}

output "proxy_resource_id" {
  description = "The ID of the proxy resource"
  value       = aws_api_gateway_resource.proxy.id
}

output "api_gateway_endpoint" {
  description = "The endpoint of the API Gateway"
  value       = aws_api_gateway_rest_api.api_gateway.execution_arn
}
