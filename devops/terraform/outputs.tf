output "project_name" {
  value = var.project_name
}

output "environment" {
  value = var.environment
}

output "container_name" {
  value = docker_container.knowledge_backend.name
}
