variable "aws_region" {
  description = "AWS region in which the AgentCore runtime, memory and supporting resources are created"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID that owns the AgentCore resources"
  type        = string
}

variable "project_name" {
  description = "Name prefix used for all resources created for the telecom agent"
  type        = string
}

variable "memory_event_expiry_days" {
  description = "Number of days short-term memory events are retained in AgentCore Memory"
  type        = number
}

variable "embedding_model_id" {
  description = "Bedrock embedding model used by the AgentCore Memory semantic strategy"
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch log retention for the AgentCore runtime log group"
  type        = number
}
