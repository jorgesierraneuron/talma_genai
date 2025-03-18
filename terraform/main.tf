# AWS Provider
provider "aws" {
  region = var.aws_region
}

# IAM Role for Lambda
module "iam" {
  source         = "./modules/iam"
  role_name      = var.lambda_role_name
  aws_account_id = var.aws_account_id
  aws_region     = var.aws_region
  environment    = var.environment
  lambda_function_name = var.rethrieve_qa_endpoint_name
}

# ✅ SNS Topic instead of SQS
resource "aws_sns_topic" "lambda_sns" {
  name = var.sns_topic_name
}

# Lambda Function: Rethrieve QA Endpoint
module "lambda_rethrieve_qa_endpoint" {
  source        = "./modules/lambda"
  function_name = var.rethrieve_qa_endpoint_name
  role_arn      = module.iam.lambda_role_arn
  image_uri     = "${var.ecr_repository_url}-${var.environment}:rethrieve_qa_endpoint_${var.environment}"
  timeout       = var.lambda_timeout
  memory_size   = var.memory_size
}

# Lambda Function: Rethrieve QA Processor
module "lambda_rethrieve_qa_processor" {
  source        = "./modules/lambda"
  function_name = var.rethrieve_qa_processor_name
  role_arn      = module.iam.lambda_role_arn
  image_uri     = "${var.ecr_repository_url}-${var.environment}:rethrieve_qa_processor_${var.environment}"
  timeout       = var.lambda_timeout
  memory_size   = var.memory_size
}

# ✅ SNS Subscription for Lambda
resource "aws_sns_topic_subscription" "lambda_subscription" {
  topic_arn = aws_sns_topic.lambda_sns.arn
  protocol  = "lambda"
  endpoint  = module.lambda_rethrieve_qa_processor.lambda_function_arn
  depends_on = [aws_lambda_permission.sns_lambda]
}

# ✅ Lambda Permission for SNS
resource "aws_lambda_permission" "sns_lambda" {
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_rethrieve_qa_processor.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.lambda_sns.arn
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

