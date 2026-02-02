---
title: Docker Containers
tags: [docker, devops, containers]
---

# Docker Containers

Understanding containerization with Docker.

## What is Docker?

Docker is a platform for developing, shipping, and running applications in containers. Containers allow developers to package an application with all its dependencies into a standardized unit.

## Key Concepts

### Images

A Docker image is a read-only template with instructions for creating a Docker container. Images are built from a Dockerfile and can be shared via Docker Hub.

### Containers

A container is a runnable instance of an image. You can create, start, stop, move, or delete a container using the Docker API or CLI.

### Volumes

Volumes are the preferred mechanism for persisting data generated and used by Docker containers. They are completely managed by Docker.

## Common Commands

```bash
# Pull an image
docker pull nginx

# Run a container
docker run -d -p 80:80 nginx

# List containers
docker ps

# Stop a container
docker stop container_id
```

## Docker Compose

Docker Compose is a tool for defining and running multi-container Docker applications. With Compose, you use a YAML file to configure your application's services.

See also [[Kubernetes]] for container orchestration at scale.

#infrastructure #cloud
