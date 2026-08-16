# Plan: Lauki Telecom Agent on Amazon Bedrock AgentCore (Runtime + Memory + Terraform + CloudWatch)

## 1. Reuse analysis — can the existing codebase be used?

**Yes.** After analyzing `01_agentcore_runtime.py` and `02_agentcore_memory.py`, the existing agent codebase is directly reusable as the foundation for the telecom agent. `02_agentcore_memory.py` is the most complete base (superset of `01`), and we will refactor it into a modular structure rather than rewrite anything.

Reusable components (carried over as-is, with only hardcoded values extracted):

| Component | Source | Reuse in new project |
|---|---|---|
| `load_faq_csv(path)` CSV→`Document` loader | `00/01/02` | `src/data_loader.py` (dataset stays `lauki_qna.csv`, 74 telecom Q&A rows) |
| FAISS vector store + `HuggingFaceEmbeddings` (`sentence-transformers/all-MiniLM-L6-v2`) + `RecursiveCharacterTextSplitter` (500/0) | `01`, `02` | `src/vector_store.py` |
| 3 tools: `search_faq`, `search_detailed_faq`, `reformulate_query` | `01`, `02` | `src/tools.py` (unchanged docstrings/logic) |
| `BedrockAgentCoreApp()` + `@app.entrypoint agent_invocation(payload, context)` returning `{"result": ...}` | `01` | `src/main.py` |
| `AgentCoreMemorySaver` / `AgentCoreMemoryStore` (from `langgraph_checkpoint_aws`), `MemoryMiddleware` (pre/post model hooks, `actor_id`/`thread_id` config) | `02` | `src/memory.py` |
| System prompt (memory-aware version) | `02` | `src/prompts.py` or `params.yml` |
| Groq LLM via `init_chat_model("openai/gpt-oss-20b", model_provider="groq")` | `02` | `src/agent.py` (model name → `params.yml`) |
| Payload contract: `{"prompt", "actor_id", "thread_id"/"session_id"}` → response `{"result", "actor_id", "thread_id"}` | `02` | kept identical |
| Dependency set | `pyproject.toml` | copied into new `pyproject.toml` |

**Hardcoded values found that must be extracted (requirement #4/#5/#6):**
- `REGION = "ap-southeast-2"` in `02_agentcore_memory.py:30` → **`params.yml`, changed to `ap-south-1`**
- `MEMORY_ID = "lauki_agent_memory-Yrm3JrG0Vz"` in `02_agentcore_memory.py:31` → **`.env`** (resource identifier, produced by Terraform)
- Model name, temperature, embedding model, chunk size/overlap, retrieval `k`, CSV path, log group → **`params.yml`**
- `GROQ_API_KEY`, `HF_API_KEY`, AWS credentials → **`.env`**

## 2. Folder structure (requirement #4 — modular, no hardcoding)

```
langgraph-telecom-agent-bedrock-agentcore/
├── README.md                     # rewritten end-to-end (reuses root README sections)
├── pyproject.toml                # uv-managed; deps copied from root pyproject.toml
├── params.yml                    # ALL non-sensitive config (style of root params.yml)
├── .env                          # sensitive values only (gitignored)
├── .env.example                  # key names without values
├── .gitignore                    # .env, .venv, __pycache__, .bedrock_agentcore*, terraform state
├── data/
│   └── lauki_qna.csv             # telecom FAQ dataset (copied from root)
├── src/
│   ├── __init__.py
│   ├── logging.py                # log_message() ported from root data_loader.py
│   ├── common.py                 # read_yml() (ConfigBox style, from root common.py) + get_root_path()
│   ├── config.py                 # loads params.yml + .env into one ConfigBox settings object
│   ├── data_loader.py            # load_faq_csv()
│   ├── vector_store.py           # embeddings + FAISS index build
│   ├── tools.py                  # search_faq, search_detailed_faq, reformulate_query
│   ├── memory.py                 # AgentCoreMemorySaver/Store init + MemoryMiddleware
│   ├── agent.py                  # LLM init + system prompt + create_agent(...)
│   └── main.py                   # BedrockAgentCoreApp entrypoint (agentcore configure -e src/main.py)
├── scripts/
│   ├── test_memory.py            # two-turn invocation proving memory works (same actor/thread)
│   ├── run_dataset_eval.py       # batch-invoke agent with questions from data/lauki_qna.csv
│   └── tail_logs.py              # boto3 CloudWatch Logs tail of the runtime log group
├── terraform/
│   ├── versions.tf               # style of terraform-reference (aws ~> 5.95.0 + awscc for AgentCore resources)
│   ├── providers.tf
│   ├── variables.tf
│   ├── terraform.tfvars          # aws_region = "ap-south-1", account 315183407444
│   ├── locals.tf                 # name prefix + random_string suffix (their style)
│   ├── iam.tf                    # AgentCore runtime execution role + memory/log policies
│   ├── ecr.tf                    # ECR repo for the agent container
│   ├── memory.tf                 # AgentCore Memory resource (short-term event retention + semantic strategy)
│   ├── cloudwatch.tf             # log group (optional; runtime auto-creates one)
│   └── outputs.tf                # memory_id, execution_role_arn, ecr_repo_url, log_group_name
└── .claude/plans/                # this plan
```

## 3. Configuration files (requirements #5 and #6)

**`params.yml`** (non-sensitive, style mirrors root `params.yml` + loaded via `read_yml()`/`ConfigBox` like root `common.py`):

```yaml
aws:
  region: ap-south-1
  account_id: "<YOUR_AWS_ACCOUNT_ID>"

agent:
  name: lauki-telecom-agent
  model: openai/gpt-oss-20b
  model_provider: groq
  temperature: 0

knowledge_base:
  csv_path: data/lauki_qna.csv
  embedding_model: sentence-transformers/all-MiniLM-L6-v2
  chunk_size: 500
  chunk_overlap: 0
  search_k: 3
  detailed_search_k: 5

memory:
  memory_name: lauki_telecom_agent_memory
  event_expiry_days: 30
  default_actor_id: default-user
  default_session_prefix: session

observability:
  log_group_prefix: /aws/bedrock-agentcore/runtimes
  log_level: INFO
```

**`.env`** (sensitive only — created locally, never committed; `.env.example` lists the keys):

```env
GROQ_API_KEY=<your_groq_api_key>
HF_API_KEY=<your_huggingface_api_key>
AWS_PROFILE=<optional>
MEMORY_ID=<populated after terraform apply>
AGENT_RUNTIME_ARN=<populated after agentcore launch>
```

`src/config.py` is the single place that merges `params.yml` (via `read_yml` + `ConfigBox`) and `.env` (via `python-dotenv`); every other module imports settings from it — no literal values anywhere else.

## 4. Terraform infrastructure (requirement #3 — their scripting style)

Follow `terraform-reference` conventions exactly: separate `.tf` file per concern, descriptive `description` fields on variables/outputs, `random_string.suffix` in `locals.tf`, values centralized in `terraform.tfvars` with inline `# source:` comments. **Keep `315183407444` and `ap-south-1` unchanged.**

Resources:
- **`versions.tf` / `providers.tf`** — copy version-pin style from reference (`aws ~> 5.95.0`); add `awscc` provider for `awscc_bedrockagentcore_memory` (AgentCore memory is not in the aws 5.x provider), plus `random` provider.
- **`iam.tf`** — AgentCore runtime execution role: trust `bedrock-agentcore.amazonaws.com`; policies for CloudWatch Logs, ECR image pull, memory `CreateEvent`/`RetrieveMemoryRecords`/`ListEvents`, X-Ray (optional).
- **`ecr.tf`** — ECR repository `lauki-telecom-agent` (immutable tags, scan on push).
- **`memory.tf`** — `awscc_bedrockagentcore_memory` named `lauki_telecom_agent_memory`, event expiry 30 days, with a semantic long-term memory strategy (so `AgentCoreMemoryStore.search()` in `MemoryMiddleware` works as in `02_agentcore_memory.py`).
- **`outputs.tf`** — `memory_id`, `execution_role_arn`, `ecr_repository_url`, `log_group_name` → copied into `.env` / used by `agentcore configure`.

## 5. Deployment, memory, testing, observability (requirement #2) --> SKIP THIS ONE for now

1. `uv sync` inside the project folder (deps from root `pyproject.toml`: `bedrock-agentcore`, `bedrock-agentcore-starter-toolkit`, `langgraph-checkpoint-aws`, `faiss-cpu`, `langchain-*`, `sentence-transformers`, plus `python-dotenv`, `pyyaml`, `ensure`, `python-box`).
2. `terraform -chdir=terraform init && apply` → capture `memory_id` + `execution_role_arn` into `.env`.
3. Local smoke test: `python src/main.py` and invoke the entrypoint locally with a sample prompt.
4. `agentcore configure -e src/main.py --region ap-south-1 --execution-role <tf output> --ecr <tf output>` (generates `.bedrock_agentcore.yaml`).
5. `agentcore launch --env GROQ_API_KEY=... --env MEMORY_ID=...` (CodeBuild-based deploy; no local Docker needed).
6. **Functional test**: `agentcore invoke '{"prompt": "Explain roaming activation", "actor_id": "user-1", "session_id": "s-1"}'`.
7. **Memory test** (`scripts/test_memory.py`): turn 1 — `"My name is Ravi, remember it"`; turn 2 with the **same** `actor_id` + new `session_id` — `"What is my name?"`; assert the answer uses stored memory (validates both short-term checkpointer and long-term store).
8. **Dataset test** (`scripts/run_dataset_eval.py`): batch-invoke a sample of questions from `data/lauki_qna.csv` and record answers vs expected.
9. **CloudWatch verification** (`scripts/tail_logs.py` + console): tail `/aws/bedrock-agentcore/runtimes/<runtime-id>-DEFAULT` to confirm the `print` statements in the entrypoint (payload, retrieved memories, result) appear; screenshot/log excerpt goes into README.

## 6. README.md (requirement #7)

Rewrite `langgraph-telecom-agent-bedrock-agentcore/README.md`, reusing these sections from the root `README.md` verbatim/adapted:
- **Set-up & Pre-requisites** (Python 3.13, uv, AWS credentials — region updated to `ap-south-1`, GROQ/HF API keys)
- **Installation** (`uv sync`, `.env` creation — key list updated)
- **Troubleshooting** (Python version, missing keys, FAISS install, AWS credentials — kept as-is)
- **Additional Resources** links + Codebasics copyright footer

New/updated sections documenting what was done and how:
- Project structure tree (above)
- Configuration model (`params.yml` vs `.env`, how `src/config.py` merges them)
- Terraform provisioning steps + outputs
- Deploy steps (`agentcore configure/launch/invoke`) for the modular `src/main.py`
- Memory test walkthrough and CloudWatch log verification steps

## 7. Execution order

1. Scaffold folder + copy `lauki_qna.csv`, `pyproject.toml`, `.gitignore`
2. Port `common.py` / `data_loader.py` utilities → `src/logging.py`, `src/common.py`, `src/config.py`; write `params.yml`, `.env.example`
3. Refactor `02_agentcore_memory.py` → `src/` modules (all literals replaced by config lookups)
4. Write Terraform configs (style-matched to reference, ap-south-1 / 315183407444)
5. `uv sync`, terraform apply, `.env` filled, local smoke test   --> SKIP THIS ONE for now
6. `agentcore configure` + `launch`; functional + memory + dataset tests; CloudWatch log check --> SKIP THIS ONE for now
7. Write README end-to-end
