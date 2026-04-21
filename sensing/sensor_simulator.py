import random
from datetime import datetime


def generate_sensor_data(device_id="DEV001", equipment_type="ventilator", anomaly_prob=0.15):
    is_anomaly = random.random() < anomaly_prob

    if not is_anomaly:
        return {
            "timestamp": datetime.now().isoformat(),
            "device_id": device_id,
            "equipment_type": equipment_type,
            "vibration_rms": round(random.uniform(0.2, 0.8), 3),
            "vibration_peak": round(random.uniform(0.5, 1.2), 3),
            "power_w": round(random.uniform(80, 110), 2),
            "current_a": round(random.uniform(0.35, 0.50), 3),
            "temperature_c": round(random.uniform(28, 36), 2),
            "state": "normal"
        }
    else:
        return {
            "timestamp": datetime.now().isoformat(),
            "device_id": device_id,
            "equipment_type": equipment_type,
            "vibration_rms": round(random.uniform(1.2, 3.0), 3),
            "vibration_peak": round(random.uniform(2.0, 5.0), 3),
            "power_w": round(random.uniform(120, 180), 2),
            "current_a": round(random.uniform(0.55, 0.90), 3),
            "temperature_c": round(random.uniform(40, 65), 2),
            "state": "anomaly"
        }
