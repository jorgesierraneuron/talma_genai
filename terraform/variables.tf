# Región de AWS
variable "aws_region" {
  description = "Región de AWS donde se desplegará la infraestructura"
  type        = string
  default     = "us-east-1"
}

# Nombre del repositorio ECR
variable "ecr_repo_name" {
  description = "Nombre del repositorio ECR"
  type        = string
  default     = "lambda-container-repo"
}

# Nombre de la cola SQS
variable "sqs_queue_name" {
  description = "Nombre de la cola SQS"
  type        = string
  default     = "lambda-trigger-queue"
}

# Nombre del rol IAM para Lambda
variable "lambda_role_name" {
  description = "Nombre del rol IAM para Lambda"
  type        = string
  default     = "lambda_execution_role"
}

# Configuración de Lambda Clean Files
variable "clean_files_function_name" {
  description = "Nombre de la función Lambda para clean-files"
  type        = string
  default     = "clean_files_lambda"
}

variable "clean_files_timeout" {
  description = "Tiempo máximo de ejecución para clean-files Lambda"
  type        = number
  default     = 120
}

# Configuración de Lambda Convert JSON
variable "convert_json_function_name" {
  description = "Nombre de la función Lambda para convertir JSON"
  type        = string
  default     = "convert_json_lambda"
}

variable "convert_json_timeout" {
  description = "Tiempo máximo de ejecución para convert-json Lambda"
  type        = number
  default     = 180
}

variable "convert_json_sqs_batch_size" {
  description = "Tamaño del lote de mensajes para la función convert-json Lambda"
  type        = number
  default     = 5
}

# URL de la base de datos Neo4j
variable "neo4j_url" {
  description = "URL de la base de datos Neo4j"
  type        = string
  default     = "your-neo4j-database-url"
}
