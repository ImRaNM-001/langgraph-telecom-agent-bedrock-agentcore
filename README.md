# 🤖 Lauki Phones Telecom Agent on Amazon Bedrock AgentCore

A **LangGraph telecom FAQ agent** for Lauki Phones, deployed on **Amazon Bedrock AgentCore Runtime** with **AgentCore Memory** (short-term checkpointing + long-term semantic memory), infrastructure provisioned with **Terraform**, and observability through **CloudWatch Logs**.

The agent answers telecom questions (plans, SIM/eSIM, roaming, billing, 5G bands, porting, ...) using RAG over the **Lauki Q&A dataset** (`data/lauki_qna.csv`), and remembers user preferences across sessions.

## ✨ What this project demonstrates

- **AgentCore Runtime** — production deployment of a LangGraph agent via the `bedrock-agentcore-starter-toolkit`
- **AgentCore Memory** — `AgentCoreMemorySaver` (short-term, per session) and `AgentCoreMemoryStore` (long-term, per actor) with pre/post model middleware hooks
- **RAG toolset** — FAISS + HuggingFace embeddings (`search_faq`, `search_detailed_faq`, `reformulate_query`)
- **Terraform** — IAM execution roles, ECR repository, AgentCore Memory (semantic strategy), CloudWatch log group
- **Zero hardcoding** — all non-sensitive config in `params.yml`, all secrets in `.env`

## 📁 Project Structure

```
langgraph-telecom-agent-bedrock-agentcore/
├── README.md                     # this file
├── pyproject.toml                # uv-managed dependencies
├── params.yml                    # ALL non-sensitive configuration
├── .env                          # sensitive values only (gitignored, create from .env.example)
├── .env.example                  # key names without values
├── .gitignore
├── data/
│   └── lauki_qna.csv             # telecom FAQ dataset (74 Q&A rows)
├── src/
│   ├── __init__.py
│   ├── logging.py                # logger factory (console + logs/agent.log)
│   ├── common.py                 # read_yml() -> ConfigBox, create_directories()
│   ├── config.py                 # merges params.yml + .env; the ONLY config entry point
│   ├── data_loader.py            # load_faq_csv(): CSV -> LangChain Documents
│   ├── vector_store.py           # HuggingFace embeddings + FAISS index (lazy singleton)
│   ├── tools.py                  # search_faq, search_detailed_faq, reformulate_query
│   ├── memory.py                 # AgentCoreMemorySaver/Store + MemoryMiddleware hooks
│   ├── agent.py                  # LLM (Groq) + system prompt + create_agent(...)
│   └── main.py                   # BedrockAgentCoreApp entrypoint
├── scripts/
│   ├── test_memory.py            # two-turn cross-session memory test
│   ├── run_dataset_eval.py       # batch-invoke the agent with dataset questions
│   └── tail_logs.py              # tail the runtime's CloudWatch log group
└── terraform/
    ├── versions.tf / providers.tf
    ├── variables.tf / terraform.tfvars
    ├── locals.tf                 # name prefix + random suffix (reference style)
    ├── iam.tf                    # runtime execution role + memory execution role
    ├── ecr.tf                    # ECR repository for the agent image
    ├── memory.tf                 # AgentCore Memory (event expiry + semantic strategy)
    ├── cloudwatch.tf             # runtime log group with retention
    └── outputs.tf                # memory_id, role ARN, ECR URL, log group
```

## ⚙️ Configuration Model (no hardcoded values)

| File | Contents | Loaded by |
|---|---|---|
| `params.yml` | Non-sensitive: region (`ap-south-1`), account ID, model name, temperature, embedding model, chunk sizes, retrieval `k`, memory name/expiry, log group prefix | `src/common.py::read_yml()` → `ConfigBox` |
| `.env` | Sensitive: `GROQ_API_KEY`, `HF_API_KEY`, `AWS_PROFILE`, `MEMORY_ID`, `AGENT_RUNTIME_ARN` | `python-dotenv` in `src/config.py` |

Every module imports settings from `src/config.py` — there are **no literal values** in application code.

## 🛠️ Set-up & Pre-requisites

### System Requirements

- **Python**: 3.13 or newer (see [python.org/downloads](https://www.python.org/downloads/) to install)
- **Operating System**: Windows, macOS, or Linux
- **uv**: Ultra-fast Python package installer and resolver
- **Terraform**: 1.12.0 or newer

Check your Python version:
```bash
python --version
```

Install uv:
```bash
pip install uv
```
Or follow the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)

### AWS Account & Credentials

- An **AWS account** with access to Amazon Bedrock AgentCore
- **AWS credentials** configured (see [AWS CLI Configuration](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html))
- Region set to `ap-south-1` (account `<YOUR_AWS_ACCOUNT_ID>` per `terraform/terraform.tfvars` and `params.yml`)

### API Keys

- **GROQ API Key**: Required for accessing the Groq LLM service
  - Sign up at [console.groq.com](https://console.groq.com)
  - Create an API key in your account settings
- **Hugging Face API Key**: Used for downloading the `sentence-transformers/all-MiniLM-L6-v2` embedding model

## 📦 Installation

### Step 1: Enter the Project

```bash
cd langgraph-telecom-agent-bedrock-agentcore
```

### Step 2: Install Dependencies

```bash
uv sync
```

This installs all dependencies specified in `pyproject.toml`.

### Step 3: Configure Environment Variables

```bash
cp .env.example .env
```

Fill in your keys:

```env
GROQ_API_KEY=your_groq_api_key_here
HF_API_KEY=your_huggingface_api_key_here
AWS_PROFILE=optional_profile_name
MEMORY_ID=          # filled in after terraform apply (step below)
AGENT_RUNTIME_ARN=  # filled in after agentcore launch
```

## 🏗️ Provision Infrastructure with Terraform

All infrastructure lives in `terraform/` and follows the reference style: one `.tf` file per concern, values centralized in `terraform.tfvars`, and a `random_string` suffix in `locals.tf` to keep resource names unique.

```bash
terraform -chdir=terraform init
terraform -chdir=terraform plan
terraform -chdir=terraform apply
```

Resources created in **`ap-south-1`** (account **`<YOUR_AWS_ACCOUNT_ID>`**):

| Resource | Purpose |
|---|---|
| IAM role `...-runtime-execution-...` | Assumed by the AgentCore runtime: CloudWatch Logs, ECR pull, Memory data-plane, X-Ray |
| IAM role `...-memory-execution-...` | Assumed by AgentCore Memory to invoke the Titan embedding model for the semantic strategy |
| ECR repository | Stores the agent container image built by `agentcore launch` |
| AgentCore Memory | 30-day event expiry (short-term) + semantic strategy (long-term user preferences) |
| CloudWatch log group | `/aws/bedrock-agentcore/runtimes/<name>-DEFAULT` with 14-day retention |

Copy the outputs into `.env` (and keep them for the deploy step):

```bash
terraform -chdir=terraform output memory_id           # -> MEMORY_ID in .env
terraform -chdir=terraform output execution_role_arn  # -> used by agentcore configure
terraform -chdir=terraform output ecr_repository_url  # -> used by agentcore configure
```

## 🚀 Deploy the Agent on AgentCore Runtime

### Step 1: Local smoke test (optional but recommended)

```bash
uv run python -m src.main
```

In another terminal, invoke the local server:

```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain roaming activation", "actor_id": "local-user", "session_id": "local-1"}'
```

### Step 2: Configure

```bash
agentcore configure -e src/main.py \
  --region ap-south-1 \
  --execution-role <execution_role_arn from terraform> \
  --ecr <ecr_repository_url from terraform>
```

This generates `.bedrock_agentcore.yaml` with the agent configuration.

### Step 3: Launch

```bash
agentcore launch --env GROQ_API_KEY=your_groq_api_key_here --env MEMORY_ID=<memory_id from terraform>
```

CodeBuild builds and pushes the image to ECR and creates the runtime — no local Docker required.

### Step 4: Invoke

```bash
agentcore invoke '{"prompt": "Explain roaming activation", "actor_id": "user-1", "session_id": "s-1"}'
```

Record the runtime ARN in `.env` as `AGENT_RUNTIME_ARN` (the scripts below use it).

**Payload contract** (unchanged from the course examples):

- Request: `{"prompt": str, "actor_id"?: str, "session_id"?: str}`
- Response: `{"result": str, "actor_id": str, "thread_id": str}`

## 🧠 Verify Memory (short-term + long-term)

`scripts/test_memory.py` proves cross-session long-term memory:

1. **Turn 1** (actor `A`, session `S1`): `"My name is Ravi, remember it."`
2. **Turn 2** (actor `A`, **new** session `S2`): `"What is my name?"`

Only long-term AgentCore Memory can answer turn 2:

```bash
uv run python scripts/test_memory.py
# ✅ MEMORY TEST PASSED — agent recalled the name across sessions
```

## 📊 Verify with the Dataset

Batch-invoke the agent with questions from `data/lauki_qna.csv` and compare against reference answers:

```bash
uv run python scripts/run_dataset_eval.py --num 10
# results written to logs/dataset_eval_results.json
```

## 🔍 Observe in CloudWatch Logs

Every entrypoint invocation prints the received payload, retrieved memories, and the result. These land in `/aws/bedrock-agentcore/runtimes/<runtime-id>-DEFAULT`:

```bash
uv run python scripts/tail_logs.py --minutes 15
```

Or in the console: **CloudWatch → Log groups → /aws/bedrock-agentcore/runtimes/** — confirm the `Received payload`, `Retrieved memories`, and `Result` lines for each invocation.

## ⚙️ Troubleshooting

### Issue: Python version error
**Solution**: Ensure you have Python 3.13 or newer installed:
```bash
python --version
```

### Issue: Missing `GROQ_API_KEY`
**Solution**: Verify your `.env` file contains the key and is in the project root:
```bash
cat .env
```

### Issue: FAISS installation fails
**Solution**: Install the CPU version explicitly:
```bash
uv pip install --upgrade faiss-cpu
```

### Issue: AWS credentials not found
**Solution**: Configure AWS credentials using AWS CLI:
```bash
aws configure
```

### Issue: `MEMORY_ID is not set` when running scripts
**Solution**: Run `terraform -chdir=terraform output memory_id` and copy the value into `.env`.

### Issue: terraform `awscc_bedrockagentcore_memory` fails
**Solution**: Verify the `hashicorp/awscc` provider installed correctly (`terraform -chdir=terraform init` again) and that AgentCore is available in `ap-south-1` for your account.

## 📚 Additional Resources

- [Amazon bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/?trk=33dad69a-efe5-4eb8-b3eb-bfdc0cf9a3c0&sc_channel=el)
- [Amazon Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-get-started-toolkit.html/?trk=33dad69a-efe5-4eb8-b3eb-bfdc0cf9a3c0&sc_channel=el)
- [Amazon Bedrock Agentcore Samples](https://github.com/awslabs/amazon-bedrock-agentcore-samples)

---
Copyright©️ Codebasics Inc. All rights reserved.
