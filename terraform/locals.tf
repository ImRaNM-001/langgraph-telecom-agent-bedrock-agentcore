/* This file defines local variables for the AgentCore telecom agent deployment using Terraform.
Locals allow us to assign a name to an expression, so we can use it multiple times without repeating it. They help improve readability and maintainability by centralizing common values and computed expressions used across the configuration.

Local variables defined here include:
- Normalized resource names (with a random suffix to avoid collisions)
- Computed tags
- Other reusable values for the AgentCore configuration       */

locals {
  # AgentCore Memory names only allow letters, digits and underscores
  memory_name = "lauki_telecom_agent_memory_${random_string.suffix.result}"
  ecr_repo_name = "${var.project_name}-${random_string.suffix.result}"

  common_tags = {
    Project     = var.project_name
    Environment = "dev"
    ManagedBy   = "terraform"
  }
}

resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}
