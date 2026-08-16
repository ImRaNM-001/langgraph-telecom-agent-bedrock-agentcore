"""
Tail the CloudWatch log group of the deployed AgentCore runtime to verify
agent invocations end-to-end (payload received, memories retrieved, result).

Usage:
    python scripts/tail_logs.py [--minutes 15]
"""
import argparse
import sys
import time
from pathlib import Path

import boto3

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import params


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=int, default=15, help="how far back to fetch logs")
    args = parser.parse_args()

    logs = boto3.client("logs", region_name=params.aws.region)
    prefix = params.observability.log_group_prefix

    # Discover the runtime log group: <prefix>/<runtime-id>-DEFAULT
    groups = logs.describe_log_groups(logGroupNamePrefix=prefix).get("logGroups", [])
    if not groups:
        print(f"No log groups found under prefix '{prefix}'. Has the agent been invoked yet?")
        return

    for group in groups:
        group_name = group["logGroupName"]
        print(f"\n===== {group_name} =====")
        start_ms = int((time.time() - args.minutes * 60) * 1000)
        events = logs.filter_log_events(logGroupName=group_name, startTime=start_ms).get("events", [])
        for event in events:
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event["timestamp"] / 1000))
            print(f"{ts}  {event['message'].rstrip()}")
        if not events:
            print("(no events in the requested window)")


if __name__ == "__main__":
    main()
