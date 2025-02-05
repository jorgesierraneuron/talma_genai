output "repository_url" {
  description = "URL del repositorio ECR"
  value       = aws_ecr_repository.repo.repository_url
}
