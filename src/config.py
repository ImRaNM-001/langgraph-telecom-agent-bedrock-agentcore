import os
from pathlib import Path

from dotenv import load_dotenv

from src.common import read_yml
from src.logging import get_root_path

# Load sensitive values from .env (local dev). In the AgentCore runtime container
# these are injected via `agentcore launch --env KEY=VALUE` instead.
_ = load_dotenv(get_root_path() / ".env")

# All non-sensitive configuration lives in params.yml
params = read_yml(get_root_path() / "params.yml")

# Make sure boto3-based clients (AgentCore Memory, CloudWatch) default to the
# configured region unless the environment already pins one.
os.environ.setdefault("AWS_REGION", params.aws.region)
os.environ.setdefault("AWS_DEFAULT_REGION", params.aws.region)


def get_secret(name: str, default: str = "") -> str:
    """Read a sensitive value (API keys, resource identifiers) from the environment."""
    return os.getenv(name, default)


def get_csv_path() -> Path:
    """Absolute path to the FAQ dataset, resolved from params.knowledge_base.csv_path."""
    csv_path = Path(params.knowledge_base.csv_path)
    if not csv_path.is_absolute():
        csv_path = get_root_path() / csv_path
    return csv_path
