"""Preprocessing pipeline for skill body content.

Handles string substitution and shell command execution in order:
1. String substitution ($ARGUMENTS, positional $N, ${SKILL_DIR})
2. Shell preprocessing (!`command` patterns)
"""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

# Matches !`command` patterns for shell execution
_SHELL_PATTERN = re.compile(r"!`([^`]+)`")


def _substitute_variables(
    body: str,
    skill_dir: Path,
    arguments: str | None,
) -> str:
    """Replace variable placeholders in body text.

    Replacements performed:
    - ${SKILL_DIR}  → absolute skill directory path
    - $ARGUMENTS    → full argument string (empty string if None)
    - $0, $1, $2, … → individual positional args (empty string if beyond args)

    Args:
        body: Raw skill body text.
        skill_dir: Path to the skill directory.
        arguments: Full argument string passed by the user, or None.

    Returns:
        Body with all variable placeholders substituted.
    """
    # Resolve $ARGUMENTS early (before positional so "$ARGUMENTS" isn't split)
    args_str = arguments if arguments is not None else ""
    positional = args_str.split() if args_str else []

    # 1. ${SKILL_DIR}
    body = body.replace("${SKILL_DIR}", str(skill_dir))

    # 2. $ARGUMENTS
    body = body.replace("$ARGUMENTS", args_str)

    # 3. Positional $N — replace from highest index down to avoid $1 matching inside $10
    def _replace_positional(match: re.Match[str]) -> str:
        idx = int(match.group(1))
        return positional[idx] if idx < len(positional) else ""

    body = re.sub(r"\$(\d+)", _replace_positional, body)

    return body


async def _execute_shell_commands(body: str, skill_dir: Path) -> str:
    """Find !`command` patterns and replace them with command stdout.

    Commands execute with skill_dir as the working directory.
    On success, the pattern is replaced with trimmed stdout.
    On failure or timeout (30 s), an inline error message is injected.

    Args:
        body: Body text after variable substitution.
        skill_dir: Path to the skill directory (used as cwd).

    Returns:
        Body with all !`command` patterns replaced.
    """
    matches = list(_SHELL_PATTERN.finditer(body))
    if not matches:
        return body

    # Process matches in reverse order to preserve string offsets
    for match in reversed(matches):
        command = match.group(1)
        replacement = await _run_shell_command(command, skill_dir)
        body = body[: match.start()] + replacement + body[match.end() :]

    return body


async def _run_shell_command(command: str, cwd: Path) -> str:
    """Execute a single shell command and return its output.

    Args:
        command: Shell command string to execute.
        cwd: Working directory for the command.

    Returns:
        Stripped stdout on success, or an inline error string on failure/timeout.
    """
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=30.0
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            logger.warning(f"Shell command timed out: {command!r}")
            return f"[preprocessing error: command timed out: {command}]"

        if proc.returncode != 0:
            stderr_text = stderr_bytes.decode(errors="replace").strip()
            logger.warning(
                f"Shell command failed (exit {proc.returncode}): {command!r} — {stderr_text}"
            )
            return f"[preprocessing error: command failed (exit {proc.returncode}): {command}]"

        return stdout_bytes.decode(errors="replace").strip()

    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Shell command error: {command!r} — {exc}")
        return f"[preprocessing error: {exc}]"


async def preprocess(
    body: str,
    *,
    skill_dir: Path,
    arguments: str | None,
    execute_shell: bool = True,
) -> str:
    """Preprocess skill body content through the full pipeline.

    Pipeline order:
    1. String substitution (${SKILL_DIR}, $ARGUMENTS, $N positional)
    2. Shell command execution (!`command` patterns) — only when execute_shell=True

    Args:
        body: Raw skill body text.
        skill_dir: Path to the skill directory.
        arguments: Full argument string from the user, or None.
        execute_shell: If False, skip shell command execution (!`command` patterns).
            Default is True. Set to False for inline skills to prevent untrusted
            shell execution.

    Returns:
        Preprocessed body text ready for delivery.
    """
    body = _substitute_variables(body, skill_dir, arguments)
    if execute_shell:
        body = await _execute_shell_commands(body, skill_dir)
    return body
