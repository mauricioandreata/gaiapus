"""Every JSON the firmware published must equal what the gateway decoder makes from its LoRa bytes."""
import json, sys, os
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
import gaiapus_decode as gd
bad = 0
for line in open(sys.argv[1]):
    topic, js = line.split(" ", 1)
    fw = json.loads(js)
    rec = datetime.fromisoformat(fw["received_at"].replace("Z", "+00:00"))
    gw = gd.to_mqtt_json(bytes.fromhex(fw["lora_payload_hex"]), rec, rssi=fw["rssi"], snr=None)
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
