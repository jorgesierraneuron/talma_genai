# AWS Provider
provider "aws" {
  region = var.aws_region
}

# IAM Role for Lambda
module "iam" {
  source    = "./modules/iam"
  role_name =  var.lambda_role_name
  aws_account_id = var.aws_account_id
  aws_region = var.aws_region
}

# SQS Queue
resource "aws_sqs_queue" "lambda_sqs" {
  name                       = var.sqs_queue_name
  delay_seconds              = 0
  message_retention_seconds  = 86400  
  visibility_timeout_seconds = 5400   
  max_message_size           = 262144
  receive_wait_time_seconds  = 5
}

# Lambda Function: Rethrieve QA Endpoint
module "lambda_rethrieve_qa_endpoint" {
  source        = "./modules/lambda"
  function_name = var.rethrieve_qa_endpoint_name
  role_arn  = module.iam.lambda_role_arn
  image_uri     = "${var.ecr_repository_url}-${var.environment}:rethrieve_qa_endpoint_${var.environment}"
  timeout       = var.lambda_timeout
  memory_size = var.memory_size
}

# Lambda Function: Rethrieve QA Processor
module "lambda_rethrieve_qa_processor" {
  source        = "./modules/lambda"
  function_name = var.rethrieve_qa_processor_name
  role_arn  = module.iam.lambda_role_arn
  image_uri     = "${var.ecr_repository_url}-${var.environment}:rethrieve_qa_processor_${var.environment}"
  timeout       = var.lambda_timeout
  memory_size = var.memory_size
}

# Lambda SQS Event Source Mapping 
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.lambda_sqs.arn
  function_name    = module.lambda_rethrieve_qa_processor.function_name
  batch_size       = 1  # Ensures one Lambda execution per message
  enabled          = true
}

# API Gateway (HTTP API)
resource "aws_apigatewayv2_api" "lambda_api" {
  name          = "${var.apigateway_name}-${var.environment}"
  protocol_type = "HTTP"
}

# API Gateway Integration with Lambda
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.lambda_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = module.lambda_rethrieve_qa_endpoint.invoke_arn
}

# API Gateway Route (Proxy)
resource "aws_apigatewayv2_route" "proxy" {
  api_id    = aws_apigatewayv2_api.lambda_api.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# API Gateway Deployment
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.lambda_api.id
  name        = "$default"
  auto_deploy = true
}

# Lambda Permission for API Gateway
resource "aws_lambda_permission" "apigw_lambda" {
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_rethrieve_qa_endpoint.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.lambda_api.execution_arn}/*/*"
}

