# Proveedor de AWS
provider "aws" {
  region = var.aws_region
}

# Repositorio ECR
module "ecr" {
  source    = "./modules/ecr"
  repo_name = var.ecr_repo_name
}


# Rol IAM para Lambda
module "iam" {
  source    = "./modules/iam"
  role_name = var.lambda_role_name
}

# Lambda Clean Files
module "lambda_rethrieve_qa" {
  source        = "./modules/lambda"
  function_name = var.rethrieve_qa_name
  iam_role_arn  = module.iam.lambda_role_arn
  image_uri     = "${module.ecr.repository_url}:rethrieve_qa_${var.environment}"
  timeout       = var.rethrieve_qa_timeout
}

# Lambda Convert JSON to Knowledgebase
module "lambda_json_to_knowledge" {
  source        = "./modules/lambda"
  function_name = var.json_to_knowledge_name
  iam_role_arn  = module.iam.lambda_role_arn
  image_uri     = "${module.ecr.repository_url}:json_to_knowledge_${var.environment}"
  timeout       = var.json_to_knowledge_timeout
  environment = {
    NEO4J_URL = var.neo4j_url
  }
}


module "api_gateway_talmagenai" {
  source = "./modules/api_gateway"

  api_gateway_name   = "gateway_talmagenai"
  aws_region         = "us-east-1"
  lambda_function_name = var.rethrieve_qa_name
  aws_account_id     = "242201272670"
}
