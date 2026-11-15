"""Every JSON the firmware published must equal what the Python decoder makes from the same LoRa bytes.

usage: cross_check.py published.txt [hex.txt]
The bytes come from "lora_payload_hex" (bench, stake Wi-Fi) or, for the gateway, whose JSON
has no hex, from hex.txt (one payload per published uplink, same order)."""
import json, sys, os
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import gaiapus_decode as gd
bad = 0
hexes = iter(open(sys.argv[2]).read().split()) if len(sys.argv) > 2 else None
for line in open(sys.argv[1]):
    topic, js = line.split(" ", 1)
    if not topic.endswith("/up"):
        continue                                   # gateway status, etc.
    fw = json.loads(js)
    rec = datetime.fromisoformat(fw["received_at"].replace("Z", "+00:00"))
    raw = bytes.fromhex(fw["lora_payload_hex"] if hexes is None else next(hexes))
    gw = gd.to_mqtt_json(raw, rec, rssi=fw["rssi"], snr=fw["snr"], gateway_id=fw.get("gateway_id"))
    assert set(fw) - {"lora_payload_hex"} == set(gw), f"field sets differ: {sorted(set(fw) ^ set(gw))}"
    assert topic == f'gaiapus/devices/{fw["device_id"]}/up', topic
    for k in gw:
        a, b = fw[k], gw[k]
        if k == "observed_at":
            dt = abs((datetime.fromisoformat(a[:-1]) - datetime.fromisoformat(b[:-1])).total_seconds())
            ok = dt < 60
        else:
            ok = a == b
        if not ok:
            bad += 1; print(f"MISMATCH seq {fw['seq']} {k}: firmware {a} / decoder {b}")
    ev = gd.to_events(gw)
    print(f"seq {fw['seq']}: flags={fw['flags']} rain_mm={fw['rain_mm']} t15={fw['readings'][0]['soil_temp_c']} "
          f"t_air={fw['air_temp_c']} observed={fw['observed_at']} received={fw['received_at']} quality={[e['quality'] for e in ev]}")
print("RESULT:", "OK" if bad == 0 else f"FAIL ({bad})")
sys.exit(bad != 0)
