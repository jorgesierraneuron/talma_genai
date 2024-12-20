# Proveedor de AWS
provider "aws" {
  region = var.aws_region
}

# Repositorio ECR
module "ecr" {
  source    = "./modules/ecr"
  repo_name = var.ecr_repo_name
}

# Cola SQS
module "sqs" {
  source       = "./modules/sqs"
  queue_name   = var.sqs_queue_name
}

# Rol IAM para Lambda
module "iam" {
  source    = "./modules/iam"
  role_name = var.lambda_role_name
}

# Lambda Clean Files
module "lambda_clean_files" {
  source        = "./modules/lambda"
  function_name = var.clean_files_function_name
  iam_role_arn  = module.iam.lambda_role_arn
  image_uri     = "${module.ecr.repository_url}:clean-files"
  timeout       = var.clean_files_timeout
  environment = {
    SQS_QUEUE_URL = module.sqs.queue_url
  }
}

# Lambda Convert JSON to Knowledgebase
module "lambda_convert_json" {
  source        = "./modules/lambda"
  function_name = var.convert_json_function_name
  iam_role_arn  = module.iam.lambda_role_arn
  image_uri     = "${module.ecr.repository_url}:convert-json"
  timeout       = var.convert_json_timeout
  environment = {
    NEO4J_URL = var.neo4j_url
  }
  sqs_arn        = module.sqs.queue_arn
  sqs_batch_size = var.convert_json_sqs_batch_size
}
