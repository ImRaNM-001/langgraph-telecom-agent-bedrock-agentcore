# ECR repository that stores the container image for the telecom agent.
# The `agentcore launch` command builds and pushes the image here.

resource "aws_ecr_repository" "agent" {
  name                 = local.ecr_repo_name
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.common_tags
}
