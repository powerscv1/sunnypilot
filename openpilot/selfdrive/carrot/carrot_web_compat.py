"""Dependency-free CarrotMan HTTP bridge for SunnyPilot."""
from __future__ import annotations

import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

INT_FIELDS = {"activeCarrot", "nRoadLimitSpeed", "xSpdType", "xSpdLimit", "xSpdDist", "xSpdCountDown", "xTurnInfo", "xDistToTurn", "xTurnCountDown", "vTurnSpeed", "desiredSpeed", "carrotCmdIndex", "trafficState", "nGoPosDist", "nGoPosTime", "leftSec", "vehicleNaviSpeed"}
TEXT_FIELDS = {"remote", "atcType", "szPosRoadName", "szTBTMainText", "desiredSource", "carrotCmd", "carrotArg", "szSdiDescr", "naviPaths"}
FLOAT_FIELDS = {"xPosLat", "xPosLon", "xPosAngle", "xPosSpeed"}
BOOL_FIELDS = {"vehicleNaviActive", "vehicleNaviSectionActive", "vehicleNaviAvailable"}
ALL_FIELDS = INT_FIELDS | TEXT_FIELDS | FLOAT_FIELDS | BOOL_FIELDS


def validated_payload(payload: Any) -> dict[str, Any]:
  if not isinstance(payload, dict):
    raise ValueError("JSON object required")
  result: dict[str, Any] = {}
  for key, value in payload.items():
    if key not in ALL_FIELDS:
      continue
    if key in INT_FIELDS:
      value = int(value)
      if not -(2**31) <= value < 2**31:
        raise ValueError(f"invalid value for {key}")
    elif key in FLOAT_FIELDS:
      value = float(value)
    elif key in BOOL_FIELDS:
      if not isinstance(value, bool):
        raise ValueError(f"invalid value for {key}")
    elif not isinstance(value, str) or len(value) > 512:
      raise ValueError(f"invalid value for {key}")
    result[key] = value
  return result


class CarrotWebBridge:
  def __init__(self):
    import openpilot.cereal.messaging as messaging
    self.messaging = messaging
    self.pm = messaging.PubMaster(["carrotMan"])
    self.state: dict[str, Any] = {}
    self.last_navi_version = ""
    self.lock = threading.Lock()

  def update(self, payload: dict[str, Any]) -> dict[str, Any]:
    with self.lock:
      self.state.update(validated_payload(payload))
      msg = self.messaging.new_message("carrotMan")
      for key, value in self.state.items():
        setattr(msg.carrotMan, key, value)
      self.pm.send("carrotMan", msg)
      return dict(self.state)


def make_handler(bridge: CarrotWebBridge):
  class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: dict[str, Any]) -> None:
      data = json.dumps(body, ensure_ascii=False).encode()
      self.send_response(status)
      self.send_header("Content-Type", "application/json")
      self.send_header("Content-Length", str(len(data)))
      self.end_headers()
      self.wfile.write(data)

    def do_GET(self) -> None:
      if self.path in ("/health", "/api/health"):
        self._send(200, {"ok": True, "service": "carrotMan", "lastTmapVersion": bridge.last_navi_version})
      elif self.path in ("/api/carrot", "/api/carrot/state"):
        with bridge.lock:
          self._send(200, dict(bridge.state))
      else:
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
      if self.path.startswith("/api/navi/"):
        try:
          size = int(self.headers.get("Content-Length", "0"))
          if size > 64 * 1024:
            raise ValueError("request too large")
          payload = json.loads(self.rfile.read(size))
          if not isinstance(payload, dict):
            raise ValueError("JSON object required")
          version = self.path.removeprefix("/api/navi/").split("/", 1)[0]
          bridge.last_navi_version = version
          source = payload.get("carrotMan", payload)
          if isinstance(source, dict):
            update = {key: value for key, value in source.items() if key in ALL_FIELDS}
            self._send(200, {"ok": True, "tmap_version": version, "state": bridge.update(update)})
            return
          raise ValueError("JSON object required")
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
          self._send(400, {"ok": False, "error": str(exc)})
          return
      if self.path not in ("/api/carrot", "/api/carrot/state"):
        self._send(404, {"error": "not found"})
        return
      try:
        size = int(self.headers.get("Content-Length", "0"))
        if size > 64 * 1024:
          raise ValueError("request too large")
        self._send(200, bridge.update(json.loads(self.rfile.read(size))))
      except (ValueError, TypeError, json.JSONDecodeError) as exc:
        self._send(400, {"error": str(exc)})

    def log_message(self, _format: str, *_args: Any) -> None:
      return
  return Handler


def main() -> None:
  parser = argparse.ArgumentParser(description="SunnyPilot CarrotMan web bridge")
  parser.add_argument("--host", default="0.0.0.0")
  parser.add_argument("--port", type=int, default=7706)
  args = parser.parse_args()
  server = ThreadingHTTPServer((args.host, args.port), make_handler(CarrotWebBridge()))
  server.serve_forever()


if __name__ == "__main__":
  main()
