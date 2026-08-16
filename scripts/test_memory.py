"""
Two-turn memory test against the deployed AgentCore runtime.

Turn 1 tells the agent a fact ("My name is Ravi, remember it").
Turn 2 asks for that fact using the SAME actor_id but a NEW session,
which can only be answered from long-term AgentCore Memory.

Usage:
    python scripts/test_memory.py
"""
import json
import sys
import uuid
from pathlib import Path

import boto3

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import params, get_secret
from src.logging import logger


def invoke_runtime(client, runtime_arn: str, payload: dict, session_id: str) -> dict:
    response = client.invoke_agent_runtime(
        agentRuntimeArn=runtime_arn,
        runtimeSessionId=session_id,
        payload=json.dumps(payload),
    )
    body = response["response"].read()
    return json.loads(body)


def main():
    runtime_arn = get_secret("AGENT_RUNTIME_ARN")
    if not runtime_arn:
        raise RuntimeError("AGENT_RUNTIME_ARN is not set. Populate .env after `agentcore launch`.")

    client = boto3.client("bedrock-agentcore", region_name=params.aws.region)

    actor_id = f"memory-test-user-{uuid.uuid4().hex[:8]}"
    session_1 = f"{params.memory.default_session_prefix}-{uuid.uuid4().hex[:8]}"
    session_2 = f"{params.memory.default_session_prefix}-{uuid.uuid4().hex[:8]}"

    # Turn 1: plant a fact
    logger.info(f"Turn 1 (actor={actor_id}, session={session_1})")
    turn1 = invoke_runtime(
        client, runtime_arn,
        {"prompt": "My name is Ravi, remember it.", "actor_id": actor_id, "session_id": session_1},
        session_1,
    )
    logger.info(f"Turn 1 response: {turn1.get('result')}")

    # Turn 2: recall the fact in a fresh session (long-term memory only)
    logger.info(f"Turn 2 (actor={actor_id}, session={session_2})")
    turn2 = invoke_runtime(
        client, runtime_arn,
        {"prompt": "What is my name?", "actor_id": actor_id, "session_id": session_2},
        session_2,
    )
    answer = turn2.get("result", "")
    logger.info(f"Turn 2 response: {answer}")

    if "ravi" in answer.lower():
        print("✅ MEMORY TEST PASSED — agent recalled the name across sessions")
    else:
        print("❌ MEMORY TEST FAILED — name was not recalled; check CloudWatch logs")


if __name__ == "__main__":
    main()
