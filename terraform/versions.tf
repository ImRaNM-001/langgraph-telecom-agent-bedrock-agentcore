terraform {
  required_version = ">= 1.12.0"

  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.7.2"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.95.0"       # Kept consistent with terraform-reference style
    }
    awscc = {
      source  = "hashicorp/awscc"
      version = "~> 1.50.0"       # Required: AgentCore Memory is not available in the aws 5.x provider
    }
  }
}
