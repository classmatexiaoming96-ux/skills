"""Push a markdown file to Feishu Cloud Docs via bytedcli.

Returns the doc URL and id. Raises on failure.
"""
from __future__ import annotations
import json
import subprocess
from pathlib import Path


def push(title: str, markdown_file: Path,
         folder_token: str | None = None) -> dict:
    cmd = [
        "bytedcli", "--json", "feishu", "docs", "create-doc",
        "--title", title,
        "--markdown-file", str(markdown_file),
    ]
    if folder_token:
        cmd += ["--folder-token", folder_token]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"bytedcli exited {proc.returncode}: "
                           f"{proc.stderr.strip()[-400:]}")

    # bytedcli wraps the MCP response: data.response.content[0].text is itself JSON
    out = _extract_last_json(proc.stdout)
    if out.get("status") != "success":
        raise RuntimeError(f"bytedcli error: {out.get('error')}")
    inner_text = out["data"]["response"]["content"][0]["text"]
    inner = json.loads(inner_text)
    return {"doc_id": inner["doc_id"], "doc_url": inner["doc_url"]}


def _extract_last_json(stdout: str) -> dict:
    """bytedcli sometimes prints node experimental warnings on stdout before
    the JSON payload — take the last JSON object on its own line."""
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            return json.loads(line)
    raise RuntimeError(f"no JSON found in bytedcli output: {stdout[-400:]!r}")
