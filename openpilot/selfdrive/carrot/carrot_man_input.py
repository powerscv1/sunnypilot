from __future__ import annotations

from typing import Any
import time


CARROT_MAN_STALE_SECONDS = 1.5


def get_carrot_man(sm: Any):
  """Return a valid CarrotMan message, or None when the stream is absent."""
  if "carrotMan" not in sm or not sm.valid.get("carrotMan", False):
    return None
  msg = sm["carrotMan"]
  # Do not reuse navigation commands after the producer has disappeared.
  rcv_times = getattr(sm, "rcv_time", {})
  rcv_time = rcv_times.get("carrotMan", 0.0) if hasattr(rcv_times, "get") else 0.0
  if rcv_time and time.monotonic() - rcv_time > CARROT_MAN_STALE_SECONDS:
    return None
  return msg if 0 < msg.desiredSpeed <= 250 else None
