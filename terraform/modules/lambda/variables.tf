variable "function_name" {
  description = "Nombre de la función Lambda"
  type        = string
}

variable "iam_role_arn" {
  description = "ARN del rol de IAM asociado con la función Lambda"
  type        = string
}

variable "image_uri" {
  description = "URI de la imagen en ECR"
  type        = string
}

variable "timeout" {
  description = "Tiempo máximo de ejecución para la función Lambda"
  type        = number
  default     = 120
}

variable "environment" {
  description = "Variables de entorno para la función Lambda"
  type        = map(string)
  default     = {}
}

variable "sqs_arn" {
  description = "ARN de la cola SQS para activar Lambda"
  type        = string
  default     = null
}

variable "sqs_batch_size" {
  description = "Tamaño del lote para procesar mensajes de SQS"
  type        = number
  default     = 10
}
