# AgentCore Memory for the telecom agent.
#
# - event_expiry_duration: short-term (session-scoped) conversational events,
#   used by AgentCoreMemorySaver as the LangGraph checkpointer.
# - semantic memory strategy: long-term memory, used by AgentCoreMemoryStore
#   (MemoryMiddleware pre/post hooks) to store and search user preferences
#   across sessions.
#
# The resulting memory_id must be copied into .env (MEMORY_ID) and passed to
# the runtime via `agentcore launch --env MEMORY_ID=...`.

resource "awscc_bedrockagentcore_memory" "agent_memory" {
  name                    = local.memory_name
  description             = "Short-term and long-term memory for the Lauki Phones telecom agent"
  event_expiry_duration   = var.memory_event_expiry_days
  memory_execution_role_arn = aws_iam_role.memory_execution.arn

  memory_strategies = [
    {
      semantic_memory_strategy = {
        name        = "semantic_facts"
        description = "Extracts and stores user facts and preferences for cross-session recall"
        namespaces  = ["/actors/{actorId}", "/preferences/{actorId}"]
      }
    }
  ]
}
