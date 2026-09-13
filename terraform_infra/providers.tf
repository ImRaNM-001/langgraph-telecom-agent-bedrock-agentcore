provider "aws" {
  region = var.aws_region
  profile = "agentic-ai-bedrock-user"
}

provider "awscc" {
  region = var.aws_region
  profile = "agentic-ai-bedrock-user"
}
