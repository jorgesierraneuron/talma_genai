# Región de AWS
variable "aws_region" {
  description = "Región de AWS donde se desplegará la infraestructura"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Ambiente de despliegue"
  type        = string
  default     = "dev"
}


# Nombre del repositorio ECR
variable "ecr_repo_name" {
  description = "Nombre del repositorio ECR"
  type        = string
  default     = "lambda-container-repo"
}


# Nombre del rol IAM para Lambda
variable "lambda_role_name" {
  description = "Nombre del rol IAM para Lambda"
  type        = string
  default     = "lambda_execution_role"
}

# Configuración de Lambda Clean Files
variable "rethrieve_qa_name" {
  description = "Nombre de la función Lambda para rethrieve_qa"
  type        = string
  default     = "rethrieve_qa"
}

variable "rethrieve_qa_timeout" {
  description = "Tiempo máximo de ejecución para clean-files Lambda"
  type        = number
  default     = 120
}

# Configuración de Lambda Convert JSON
variable "json_to_knowledge_name" {
  description = "Nombre de la función Lambda para convertir JSON"
  type        = string
  default     = "json_to_knowledge"
}

variable "json_to_knowledge_timeout" {
  description = "Tiempo máximo de ejecución para convert-json Lambda"
  type        = number
  default     = 180
}

# URL de la base de datos Neo4j
variable "neo4j_url" {
  description = "URL de la base de datos Neo4j"
  type        = string
  default     = "your-neo4j-database-url"
}
