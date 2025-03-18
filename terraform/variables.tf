# Región de AWS
variable "aws_region" {
  description = "Región de AWS donde se desplegará la infraestructura"
  type        = string
  default     = "us-east-1"
}

# Región de AWS
variable "aws_account_id" {
  description = "Región de AWS donde se desplegará la infraestructura"
  type        = string
  default     = "911167907421"
}

# Ambiente de despliegue (dev, test, prod)
variable "environment" {
  description = "Ambiente de despliegue"
  type        = string
  default     = "dev"
}

# Nombre del repositorio ECR
variable "ecr_repository_url" {
  description = "URL del repositorio ECR"
  type        = string
  default     = "123456789012.dkr.ecr.us-east-1.amazonaws.com/my-repo"
}

# Nombre del rol IAM para Lambda
variable "lambda_role_name" {
  description = "Nombre del rol IAM para Lambda"
  type        = string
  default     = "lambda_execution_role"
}

# Configuración de SQS
variable "sns_topic_name" {
  description = "Nombre de la cola SQS que desencadena Lambda"
  type        = string
  default     = "rethrieve_qa"
}

# Configuración de Lambda Rethrieve QA Endpoint
variable "rethrieve_qa_endpoint_name" {
  description = "Nombre de la función Lambda para rethrieve_qa_endpoint"
  type        = string
  default     = "rethrieve_qa_endpoint"
}

# Configuración de Lambda Rethrieve QA Processor
variable "rethrieve_qa_processor_name" {
  description = "Nombre de la función Lambda para rethrieve_qa_processor"
  type        = string
  default     = "rethrieve_qa_processor"
}

# Tiempo de ejecución máximo para Lambdas
variable "lambda_timeout" {
  description = "Tiempo máximo de ejecución para las funciones Lambda"
  type        = number
  default     = 60
}

variable "memory_size" {
  description = "Memoria lambda"
  type        = number
  default     = 3008
}


# Tiempo de ejecución máximo para Lambdas
variable "apigateway_name" {
  description = "Nombre del api gateway"
  type        = string
  default     = "api_rethrieve_qa"
}
