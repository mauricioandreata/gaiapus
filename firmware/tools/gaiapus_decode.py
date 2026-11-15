#!/usr/bin/env python3
"""Decode a Gaiapus 25-byte LoRa uplink into the MQTT JSON and the app events.

Contract: docs/protocolo-dados.md. Mirror of firmware/include/gaiapus_protocol.h.
Usable as a library by the gateway/backend team, or from the command line:

  python3 gaiapus_decode.py 01170000...00 --received-at 2026-11-14T12:30:00Z --rssi -97 --snr 6.5
  python3 gaiapus_decode.py --selftest
"""
import argparse, json, struct, sys
from datetime import datetime, timedelta, timezone

PROTOCOL_VERSION = 1
UPLINK = struct.Struct("<BIHHHhhhBHHHB")   # 25 bytes
assert UPLINK.size == 25
FLAG_BUTTON, FLAG_LOW_BATTERY, FLAG_SENSOR_ERROR, FLAG_CHARGING = 0x01, 0x02, 0x04, 0x08
TEMP_INVALID = -32768
DEPTHS_CM = (15, 40)
MM_PER_PULSE_DEFAULT = 0.2   # placeholder until mechanics defines the rain gauge bucket


class DecodeError(ValueError):
    pass


def device_id(node_id: int) -> str:
    return f"{node_id:08x}"


def parse_uplink(payload: bytes) -> dict:
    if len(payload) != UPLINK.size:
        raise DecodeError(f"expected 25 bytes, got {len(payload)}")
    f = UPLINK.unpack(payload)
    if f[0] != PROTOCOL_VERSION:
        raise DecodeError(f"unknown protocol version {f[0]}")
    keys = ("version", "node_id", "seq", "raw_15", "raw_40", "t_soil_15", "t_soil_40",
            "t_air", "rh_air", "rain_pulses", "vbat_mv", "age_min", "flags")
    return dict(zip(keys, f))


def _temp(v):
    return None if v == TEMP_INVALID else round(v / 100.0, 2)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_mqtt_json(payload: bytes, received_at: datetime, rssi=None, snr=None,
                 mm_per_pulse: float = MM_PER_PULSE_DEFAULT, gateway_id=None) -> dict:
    """Builds the JSON the gateway publishes on gaiapus/devices/{device_id}/up.
    gateway_id: 8-hex id of the gateway that heard the stake (omitted for a stake on Wi-Fi)."""
    u = parse_uplink(payload)
    observed = received_at - timedelta(minutes=u["age_min"])
    msg = {
        "device_id": device_id(u["node_id"]),
        "seq": u["seq"],
        "observed_at": _iso(observed),
        "received_at": _iso(received_at),
        "readings": [
            {"depth_cm": 15, "raw_moisture": u["raw_15"], "soil_temp_c": _temp(u["t_soil_15"])},
            {"depth_cm": 40, "raw_moisture": u["raw_40"], "soil_temp_c": _temp(u["t_soil_40"])},
        ],
        "air_temp_c": _temp(u["t_air"]),
        "air_rh_pct": u["rh_air"],
        "rain_mm": round(u["rain_pulses"] * mm_per_pulse, 2),
        "battery_mv": u["vbat_mv"],
        "rssi": rssi,
        "snr": snr,
        "flags": u["flags"],
    }
    if gateway_id is not None:
        msg["gateway_id"] = gateway_id
    return msg


def to_events(msg: dict, calibrate=None) -> list:
    """One app event per depth. `calibrate(device_id, depth_cm, raw) -> m3/m3 or None`."""
    out = []
    for r in msg["readings"]:
        ok = not (msg["flags"] & FLAG_SENSOR_ERROR) and r["soil_temp_c"] is not None and 0 < r["raw_moisture"] < 65535
        out.append({
            "event_id": f'{msg["device_id"]}-{msg["seq"]}-{r["depth_cm"]}',
            "device_id": msg["device_id"],
            "observed_at": msg["observed_at"],
            "depth_cm": r["depth_cm"],
            "raw_moisture": r["raw_moisture"],
            "moisture_m3_m3": calibrate(msg["device_id"], r["depth_cm"], r["raw_moisture"]) if calibrate else None,
            "soil_temp_c": r["soil_temp_c"],
            "battery_mv": msg["battery_mv"],
            "quality": "ok" if ok else "suspect",
        })
    return out


def encode_downlink(led: int, interval_min: int = 30) -> bytes:
    if not 0 <= led <= 3 or not 1 <= interval_min <= 255:
        raise ValueError("led 0-3, interval 1-255 min")
    return bytes([led, interval_min])


def encode_downlink_frame(node_id: int, led: int, interval_min: int = 30) -> bytes:
    """LoRa frame the gateway transmits right after an uplink: node_id (LE) + 2-byte command.
    The stake treats it as the ACK of that uplink; without it the measurement is resent later."""
    return struct.pack("<I", node_id) + encode_downlink(led, interval_min)


def _selftest():
    ex = bytes.fromhex("01170000 00D204 1248 3453 500A B509 300C 3A 0C00 EE0C 0000 00".replace(" ", ""))
    t = datetime(2026, 11, 14, 12, 30, tzinfo=timezone.utc)
    m = to_mqtt_json(ex, t, rssi=-97, snr=6.5)
    assert m["device_id"] == "00000017" and m["seq"] == 1234, m
    assert m["readings"][0] == {"depth_cm": 15, "raw_moisture": 18450, "soil_temp_c": 26.4}
    assert m["readings"][1]["soil_temp_c"] == 24.85 and m["air_temp_c"] == 31.2
    assert m["rain_mm"] == 2.4 and m["battery_mv"] == 3310 and m["observed_at"] == "2026-11-14T12:30:00Z"
    assert "gateway_id" not in m and to_mqtt_json(ex, t, gateway_id="a1b2c3d4")["gateway_id"] == "a1b2c3d4"
    resend = ex[:22] + bytes([90, 0]) + ex[24:]
    assert to_mqtt_json(resend, t)["observed_at"] == "2026-11-14T11:00:00Z"
    ev = to_events(m)
    assert [e["event_id"] for e in ev] == ["00000017-1234-15", "00000017-1234-40"] and ev[0]["quality"] == "ok"
    bad = ex[:11] + struct.pack("<h", TEMP_INVALID) + ex[13:24] + bytes([FLAG_SENSOR_ERROR])
    mb = to_mqtt_json(bad, t)
    assert mb["readings"][0]["soil_temp_c"] is None and to_events(mb)[0]["quality"] == "suspect"
    assert encode_downlink(1, 30) == b"\x01\x1e"
    assert encode_downlink_frame(0xC4000110, 2, 10).hex() == "100100c4020a"
    for p in (ex[:24], b"\x02" + ex[1:]):
        try:
            parse_uplink(p); raise AssertionError("should fail")
        except DecodeError:
            pass
    print(json.dumps(m, indent=2))
    print("RESULT: OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("hex", nargs="?", help="25-byte payload in hex (spaces allowed)")
    ap.add_argument("--received-at", help="ISO UTC time, default now")
    ap.add_argument("--rssi", type=float); ap.add_argument("--snr", type=float)
    ap.add_argument("--mm-per-pulse", type=float, default=MM_PER_PULSE_DEFAULT)
    ap.add_argument("--events", action="store_true", help="print app events instead of MQTT JSON")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest or not a.hex:
        _selftest(); sys.exit(0)
    t = datetime.fromisoformat(a.received_at.replace("Z", "+00:00")) if a.received_at else datetime.now(timezone.utc)
    msg = to_mqtt_json(bytes.fromhex(a.hex.replace(" ", "")), t, a.rssi, a.snr, a.mm_per_pulse)
    print(json.dumps(to_events(msg) if a.events else msg, indent=2))
