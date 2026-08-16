# CloudWatch log group for the AgentCore runtime.
# The runtime would auto-create this group on first invocation; declaring it
# here gives us controlled retention and terraform-managed lifecycle.

resource "aws_cloudwatch_log_group" "agent_runtime" {
  name              = "/aws/bedrock-agentcore/runtimes/${var.project_name}-${random_string.suffix.result}-DEFAULT"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}
