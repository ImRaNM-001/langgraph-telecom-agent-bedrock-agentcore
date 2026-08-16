/* IAM roles and policies for the AgentCore telecom agent.

Two roles are defined:
1. Runtime execution role - assumed by the AgentCore runtime when running the agent container.
   Allows: CloudWatch logging, ECR image pulls, AgentCore Memory data-plane access, X-Ray tracing.
2. Memory execution role - assumed by the AgentCore Memory service itself.
   Allows: invoking the Bedrock embedding model used by the semantic long-term memory strategy.   */

# ---------------------------------------------------------------------------
# 1. AgentCore runtime execution role
# ---------------------------------------------------------------------------
resource "aws_iam_role" "agent_runtime_execution" {
  name = "${var.project_name}-runtime-execution-${random_string.suffix.result}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowAgentCoreRuntimeAssume"
        Effect = "Allow"
        Principal = {
          Service = "bedrock-agentcore.amazonaws.com"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = var.aws_account_id
          }
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "agent_runtime_execution" {
  name = "${var.project_name}-runtime-execution-policy"
  role = aws_iam_role.agent_runtime_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${var.aws_account_id}:log-group:/aws/bedrock-agentcore/*"
      },
      {
        Sid    = "EcrAuth"
        Effect = "Allow"
        Action = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Sid    = "EcrImagePull"
        Effect = "Allow"
        Action = [
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchCheckLayerAvailability"
        ]
        Resource = aws_ecr_repository.agent.arn
      },
      {
        Sid    = "AgentCoreMemoryAccess"
        Effect = "Allow"
        Action = [
          "bedrock-agentcore:CreateEvent",
          "bedrock-agentcore:GetEvent",
          "bedrock-agentcore:ListEvents",
          "bedrock-agentcore:DeleteEvent",
          "bedrock-agentcore:RetrieveMemoryRecords",
          "bedrock-agentcore:ListMemoryRecords",
          "bedrock-agentcore:DeleteMemoryRecord"
        ]
        Resource = "arn:aws:bedrock-agentcore:${var.aws_region}:${var.aws_account_id}:memory/*"
      },
      {
        # Optional: enable if X-Ray tracing is turned on for the runtime
        Sid    = "XRayTracing"
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets"
        ]
        Resource = "*"
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# 2. AgentCore Memory execution role (used by the semantic memory strategy)
# ---------------------------------------------------------------------------
resource "aws_iam_role" "memory_execution" {
  name = "${var.project_name}-memory-execution-${random_string.suffix.result}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowAgentCoreMemoryAssume"
        Effect = "Allow"
        Principal = {
          Service = "bedrock-agentcore.amazonaws.com"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = var.aws_account_id
          }
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "memory_execution" {
  name = "${var.project_name}-memory-execution-policy"
  role = aws_iam_role.memory_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Semantic memory strategy embeds records with a Bedrock embedding model
        Sid    = "BedrockEmbeddingModelInvoke"
        Effect = "Allow"
        Action = ["bedrock:InvokeModel"]
        Resource = "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.embedding_model_id}"
      }
    ]
  })
}
