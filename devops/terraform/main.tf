terraform {
  required_version = ">= 1.5.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_container" "knowledge_backend" {
  name  = "terraform-knowledge-backend"
  image = "nginx:alpine"

  ports {
    internal = 80
    external = 8082
  }
}
