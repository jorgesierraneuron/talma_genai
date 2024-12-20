variable "queue_name" {
  description = "Nombre de la cola SQS"
  type        = string
}

variable "visibility_timeout" {
  description = "Tiempo de visibilidad para los mensajes (en segundos)"
  type        = number
  default     = 30
}

variable "message_retention_seconds" {
  description = "Duración máxima que los mensajes permanecen en la cola (en segundos)"
  type        = number
  default     = 345600
}

variable "delay_seconds" {
  description = "Retraso inicial para mensajes (en segundos)"
  type        = number
  default     = 0
}
