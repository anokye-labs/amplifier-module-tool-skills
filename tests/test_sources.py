"""Tests for sources.py - cache metadata written after git clone."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from amplifier_module_tool_skills.sources import _resolve_remote_source


@pytest.mark.asyncio
async def test_write_cache_meta_after_successful_clone(tmp_path):
    """After a successful git clone, .amplifier_cache_meta.json is written."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    source = "git+https://github.com/example/my-skills@main"

    def fake_clone(cmd, **kwargs):
        """Simulate git clone by creating the destination directory."""
        result = MagicMock()
        result.returncode = 0
        result.stderr = ""
        if "clone" in cmd:
            dest = Path(cmd[-1])
            dest.mkdir(parents=True, exist_ok=True)
        return result

    mock_sha_proc = AsyncMock()
    mock_sha_proc.returncode = 0
    mock_sha_proc.communicate = AsyncMock(return_value=(b"abc1234deadbeef\n", b""))

    with patch("subprocess.run", side_effect=fake_clone):
        with patch("asyncio.create_subprocess_exec", return_value=mock_sha_proc):
            result = await _resolve_remote_source(source, cache_dir)

    assert result is not None, "Expected a resolved path"

    meta_files = list(cache_dir.glob("*/.amplifier_cache_meta.json"))
    assert len(meta_files) == 1, (
        "Expected exactly one .amplifier_cache_meta.json in the cache directory"
    )

    meta = json.loads(meta_files[0].read_text())
    assert meta["git_url"] == "https://github.com/example/my-skills"
    assert meta["ref"] == "main"
    assert meta["type"] == "skills"
    assert meta["commit"] == "abc1234deadbeef"
    assert "cached_at" in meta
