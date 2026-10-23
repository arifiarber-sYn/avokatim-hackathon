"""Best-effort GPU lease via the fleet arbiter (openclaw-knowledge D-083, Faza 5).

The Whisper STT model is an interactive GPU tenant (~1.6 GB VRAM while resident). We
register it with the fleet arbiter (`~/scripts/gpu_arbiter.py`) as `interactive`
(highest priority) for the LIFETIME of the resident CUDA model — acquire when the CUDA
model loads, release when the idle loop unloads it. This keeps the cost off the
per-transcription hot path while still letting co-tenants (ACE-Step music, KMed batch)
see that a high-priority tenant holds the GPU.

Advisory & best-effort: any failure (arbiter missing, subprocess error) is swallowed;
STT never depends on this layer.
"""
from __future__ import annotations

import os
import subprocess

_ARBITER = os.path.expanduser("~/scripts/gpu_arbiter.py")
_TENANT = "avokatim-stt"


def acquire(need_mb: int = 2000) -> None:
    """Register STT as the GPU holder (interactive). Non-blocking (timeout 0)."""
    if not os.path.exists(_ARBITER):
        return
    try:
        subprocess.run(
            ["python3", _ARBITER, "acquire", "--tenant", _TENANT,
             "--priority", "interactive", "--need-mb", str(need_mb), "--timeout", "0"],
            capture_output=True, timeout=15,
        )
    except Exception:  # pragma: no cover - advisory only
        pass


def release() -> None:
    if not os.path.exists(_ARBITER):
        return
    try:
        subprocess.run(["python3", _ARBITER, "release", "--tenant", _TENANT],
                       capture_output=True, timeout=15)
    except Exception:  # pragma: no cover - advisory only
        pass
