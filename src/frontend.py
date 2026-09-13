"""Streamlit UI for invoking the telecom agent without exposing infrastructure."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import boto3
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import get_secret, params


def _runtime_arn() -> str:
    """Return the configured cloud runtime ARN, if this deployment uses one."""
    return get_secret("AGENT_RUNTIME_ARN").strip()


def _runs_in_ecs() -> bool:
    """Detect the Fargate task environment without exposing it in the UI."""
    execution_environment = os.getenv("AWS_EXECUTION_ENV", "")
    return bool(
        os.getenv("ECS_CONTAINER_METADATA_URI_V4")
        or execution_environment.startswith("AWS_ECS")
    )


def _read_runtime_response(response: dict[str, Any]) -> dict[str, Any]:
    """Decode the JSON response returned by InvokeAgentRuntime."""
    body = response.get("response")
    if body is None:
        raise RuntimeError("The agent runtime returned no response body.")

    if hasattr(body, "read"):
        raw_body = body.read()
    elif isinstance(body, (bytes, bytearray, str)):
        raw_body = body
    else:
        raise RuntimeError("The agent runtime returned an unsupported response body.")

    if isinstance(raw_body, bytes):
        raw_body = raw_body.decode("utf-8")
    decoded = json.loads(raw_body)
    if not isinstance(decoded, dict):
        raise RuntimeError("The agent runtime returned an invalid response.")
    return decoded


def _invoke_cloud(payload: dict[str, str], runtime_arn: str) -> dict[str, Any]:
    """Invoke AgentCore using the server's AWS credential provider chain."""
    client = boto3.client("bedrock-agentcore", region_name=params.aws.region)
    response = client.invoke_agent_runtime(
        agentRuntimeArn=runtime_arn,
        runtimeSessionId=payload["session_id"],
        contentType="application/json",
        accept="application/json",
        payload=json.dumps(payload).encode("utf-8"),
        qualifier="DEFAULT",
    )
    return _read_runtime_response(response)


def _invoke_local(payload: dict[str, str]) -> dict[str, Any]:
    """Use the existing memory-aware entrypoint in the Streamlit process."""
    from src.main import agent_invocation

    result = agent_invocation(payload, context=None)
    if not isinstance(result, dict):
        raise RuntimeError("The local agent returned an invalid response.")
    return result


def _invoke(payload: dict[str, str]) -> dict[str, Any]:
    """Use local logic unless running in the configured ECS deployment."""
    runtime_arn = _runtime_arn()
    if runtime_arn and _runs_in_ecs():
        return _invoke_cloud(payload, runtime_arn)
    return _invoke_local(payload)


def _history() -> list[dict[str, str]]:
    """Keep display-only request history for the current browser session."""
    return st.session_state.setdefault("request_history", [])


def _sync_identity_to_url() -> None:
    """Persist the selected identity across a browser refresh."""
    st.query_params["actor_id"] = st.session_state["actor_id"]
    st.query_params["session_id"] = st.session_state["session_id"]


def _load_identity_from_url() -> None:
    """Restore identity values before Streamlit creates their widgets."""
    if "actor_id" not in st.session_state:
        st.session_state["actor_id"] = st.query_params.get("actor_id", "")
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = st.query_params.get("session_id", "")


def _submit_request(status_placeholder: Any) -> None:
    """Submit current widget values and clear only the sent message."""
    actor_id = st.session_state["actor_id"].strip()
    session_id = st.session_state["session_id"].strip()
    prompt = st.session_state["message"].strip()

    if not actor_id or not session_id or not prompt:
        st.session_state["request_error"] = (
            "Enter an actor ID, session ID, and message before sending."
        )
        return

    payload = {
        "prompt": prompt,
        "actor_id": actor_id,
        "session_id": session_id,
    }
    try:
        with status_placeholder.status("Thinking...", expanded=False):
            result = _invoke(payload)
        answer = result.get("result")
        returned_actor = result.get("actor_id")
        thread_id = result.get("thread_id")
        if not all(
            isinstance(value, str) for value in (answer, returned_actor, thread_id)
        ):
            raise RuntimeError("The agent returned an incomplete response.")
    except Exception as exp:
        # st.session_state["request_error"] = (
        #     "Unable to complete the request. Please try again."
        # )
        print(f"INVOKE_AGENT_RUNTIME_ERROR: {exp}", flush=True)
        st.session_state["request_error"] = f"Request failed: {exp}"
        return

    _history().insert(
        0,
        {
            "prompt": prompt,
            "result": answer,
            "actor_id": returned_actor,
            "thread_id": thread_id,
        },
    )
    st.session_state["clear_message_on_rerun"] = True
    st.session_state.pop("request_error", None)


def _render_history(container: Any) -> None:
    history = _history()
    with container:
        st.subheader("Conversation")
        if not history:
            st.caption("Responses will appear here.")
            return

        for item in history:
            with st.chat_message("user"):
                st.write(item["prompt"])
            with st.chat_message("assistant"):
                st.write(item["result"])
                st.caption(
                    f"Actor: {item['actor_id']}  |  Session: {item['thread_id']}"
                )


def main() -> None:
    st.set_page_config(
        page_title="Telecom Assistant Agent", page_icon="💬", layout="wide"
    )
    st.title("Telecom Assistant Agent")
    st.caption("Enter an actor, session, and question to continue a conversation.")
    with st.expander("Memory testing guidance"):
        st.write(
            "For conversation context, reuse the same actor and session. "
            "For cross-session recall, keep the actor and change the session. "
            "For isolation, use a different actor."
        )

    _load_identity_from_url()
    if st.session_state.pop("clear_message_on_rerun", False):
        st.session_state["message"] = ""
    input_column, response_column = st.columns([2, 3], gap="large")

    with input_column:
        st.text_input("Actor ID", key="actor_id", on_change=_sync_identity_to_url)
        st.text_input("Session ID", key="session_id", on_change=_sync_identity_to_url)
        st.text_area("Message", key="message")
        status_placeholder = st.empty()
        if st.button("Send", type="primary"):
            _submit_request(status_placeholder)
            if st.session_state.get("clear_message_on_rerun"):
                st.rerun()
        if request_error := st.session_state.get("request_error"):
            st.error(request_error)

    with response_column:
        _render_history(st.container(height=600))


if __name__ == "__main__":
    main()
