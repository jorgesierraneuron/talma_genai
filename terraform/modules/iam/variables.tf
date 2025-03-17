variable "aws_region" {
  description = "Region AWS"
  type        = string
}

variable "aws_account_id" {
  description = "Region AWS"
  type        = string
}

variable "role_name" {
  description = "Nombre del rol de IAM para Lambda"
  type        = string
}

variable "sqs_queue_name" {
  description = "Nombre de la cola SQS que desencadena Lambda"
  type        = string
  default     = "rethrieve_qa_sqs"
}