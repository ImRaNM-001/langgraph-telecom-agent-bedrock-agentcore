output "memory_id" {
  description = "AgentCore Memory ID — copy into .env as MEMORY_ID"
  value       = awscc_bedrockagentcore_memory.agent_memory.memory_id
}

output "memory_arn" {
  description = "ARN of the AgentCore Memory resource"
  value       = awscc_bedrockagentcore_memory.agent_memory.arn
}

output "execution_role_arn" {
  description = "IAM execution role ARN for the AgentCore runtime — pass to `agentcore configure --execution-role`"
  value       = aws_iam_role.agent_runtime_execution.arn
}

output "ecr_repository_url" {
  description = "ECR repository URL for the agent container image — pass to `agentcore configure --ecr`"
  value       = aws_ecr_repository.agent.repository_url
}

output "log_group_name" {
  description = "CloudWatch log group where the agent runtime writes invocation logs"
  value       = aws_cloudwatch_log_group.agent_runtime.name
}

output "region" {
  description = "AWS region in which the resources are created"
  value       = var.aws_region
}
