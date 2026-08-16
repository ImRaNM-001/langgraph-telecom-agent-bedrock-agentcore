"""
Batch-invoke the deployed agent with questions sampled from data/lauki_qna.csv
and record the agent's answers next to the reference answers.

Usage:
    python scripts/run_dataset_eval.py [--num 10]
"""
import argparse
import csv
import json
import sys
import uuid
from pathlib import Path

import boto3

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import params, get_secret, get_csv_path
from src.logging import logger, get_root_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num", type=int, default=10, help="number of dataset questions to invoke")
    args = parser.parse_args()

    runtime_arn = get_secret("AGENT_RUNTIME_ARN")
    if not runtime_arn:
        raise RuntimeError("AGENT_RUNTIME_ARN is not set. Populate .env after `agentcore launch`.")

    client = boto3.client("bedrock-agentcore", region_name=params.aws.region)

    with open(get_csv_path(), "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))[: args.num]

    results = []
    for row in rows:
        session_id = f"{params.memory.default_session_prefix}-eval-{uuid.uuid4().hex[:8]}"
        payload = {"prompt": row["question"], "session_id": session_id}
        logger.info(f"Invoking: {row['question']}")
        response = client.invoke_agent_runtime(
            agentRuntimeArn=runtime_arn,
            runtimeSessionId=session_id,
            payload=json.dumps(payload),
        )
        answer = json.loads(response["response"].read()).get("result", "")
        results.append({
            "question": row["question"],
            "expected_answer": row["answer"],
            "agent_answer": answer,
        })

    out_path = get_root_path() / "logs" / "dataset_eval_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(results)} results to {out_path}")


if __name__ == "__main__":
    main()
