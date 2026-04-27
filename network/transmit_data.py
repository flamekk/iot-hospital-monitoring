import time
import os
import csv
import json
import requests
import psutil
from statistics import mean
import random

import sys
sys.path.append(os.path.join("..", "sensing"))

from sensor_simulator import generate_sensor_data

SERVER_URL = "http://127.0.0.1:5000/ingest"

DEVICE_ID = "DEV001"
EQUIPMENT_TYPE = "ventilator"
COLLECTION_DURATION_SEC = 60
SAMPLING_INTERVAL_SEC = 1
ANOMALY_PROB = 0.15
BATCH_SIZE = 5

# Estimation énergétique transmission
RPI_POWER_W = 3.5
SUPPLY_VOLTAGE_V = 5.0
SEND_COST_J_PER_REQUEST = 0.05
SEND_COST_J_PER_KB = 0.01

RESULTS_FILE = os.path.join("results", "network_summary.csv")


def ensure_output_dir():
    os.makedirs("results", exist_ok=True)


def estimate_energy_wh(power_w, duration_sec):
    return power_w * (duration_sec / 3600)


def joules_to_mah(energy_j, voltage_v):
    return (energy_j / voltage_v) * (1000 / 3600)


def save_summary(summary):
    file_exists = os.path.exists(RESULTS_FILE)

    with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(summary)


def send_payload(payload):
    send_time = time.time()
    response = requests.post(SERVER_URL, json=payload)
    receive_time = time.time()

    latency_ms = (receive_time - send_time) * 1000
    payload_size_bytes = len(json.dumps(payload).encode("utf-8"))

    return response.status_code, latency_ms, payload_size_bytes


def generate_all_data():
    random.seed(42)
    data_list = []
    for _ in range(COLLECTION_DURATION_SEC // SAMPLING_INTERVAL_SEC):
        data = generate_sensor_data(
            device_id=DEVICE_ID,
            equipment_type=EQUIPMENT_TYPE,
            anomaly_prob=ANOMALY_PROB
        )
        data_list.append(data)
    return data_list


def run_strategy(strategy_name, pre_generated_data=None):
    ensure_output_dir()

    if pre_generated_data is None:
        pre_generated_data = generate_all_data()

    process = psutil.Process(os.getpid())

    latencies = []
    payload_sizes = []
    cpu_usages = []
    ram_usages = []

    total_generated = 0
    total_sent_messages = 0
    total_sent_records = 0
    anomaly_count = 0

    batch = []

    start_global = time.time()

    print(f"Début stratégie : {strategy_name}")

    for data in pre_generated_data:
        total_generated += 1

        if data["state"] == "anomaly":
            anomaly_count += 1

        time.sleep(SAMPLING_INTERVAL_SEC)

        should_send = False
        payload = None

        if strategy_name == "S1":
            payload = data
            should_send = True

        elif strategy_name == "S2":
            batch.append(data)
            if len(batch) >= BATCH_SIZE:
                payload = batch.copy()
                batch.clear()
                should_send = True

        elif strategy_name == "S3":
            if data["state"] == "anomaly":
                payload = data
                should_send = True

        if should_send and payload:
            status_code, latency_ms, payload_size_bytes = send_payload(payload)

            if status_code == 200:
                latencies.append(latency_ms)
                payload_sizes.append(payload_size_bytes)
                total_sent_messages += 1

                if isinstance(payload, list):
                    total_sent_records += len(payload)
                else:
                    total_sent_records += 1

            cpu_usages.append(psutil.cpu_percent(interval=None))
            ram_usages.append(process.memory_info().rss / (1024 * 1024))

    # envoyer le reste du batch pour S2
    if strategy_name == "S2" and batch:
        status_code, latency_ms, payload_size_bytes = send_payload(batch)

        if status_code == 200:
            latencies.append(latency_ms)
            payload_sizes.append(payload_size_bytes)
            total_sent_messages += 1
            total_sent_records += len(batch)

        cpu_usages.append(psutil.cpu_percent(interval=None))
        ram_usages.append(process.memory_info().rss / (1024 * 1024))

    end_global_actual = time.time()
    total_duration = end_global_actual - start_global

    avg_latency_ms = mean(latencies) if latencies else 0
    avg_payload_size_bytes = mean(payload_sizes) if payload_sizes else 0
    total_bytes_sent = sum(payload_sizes)

    bandwidth_bytes_sec = total_bytes_sent / total_duration if total_duration > 0 else 0

    avg_cpu = mean(cpu_usages) if cpu_usages else 0
    avg_ram = mean(ram_usages) if ram_usages else 0

    base_energy_wh = estimate_energy_wh(RPI_POWER_W, total_duration)
    base_energy_j = base_energy_wh * 3600
    tx_energy_j = (total_sent_messages * SEND_COST_J_PER_REQUEST) + ((total_bytes_sent / 1024) * SEND_COST_J_PER_KB)
    total_energy_j = base_energy_j + tx_energy_j

    estimated_wh = total_energy_j / 3600
    estimated_mah = joules_to_mah(total_energy_j, SUPPLY_VOLTAGE_V)

    summary = {
        "strategy": strategy_name,
        "sampling_interval_sec": SAMPLING_INTERVAL_SEC,
        "collection_duration_sec": round(total_duration, 2),
        "total_generated_records": total_generated,
        "anomaly_count": anomaly_count,
        "total_sent_messages": total_sent_messages,
        "total_sent_records": total_sent_records,
        "avg_latency_ms": round(avg_latency_ms, 3),
        "avg_payload_size_bytes": round(avg_payload_size_bytes, 3),
        "total_bytes_sent": total_bytes_sent,
        "bandwidth_bytes_sec": round(bandwidth_bytes_sec, 3),
        "avg_cpu_percent": round(avg_cpu, 3),
        "avg_ram_mb": round(avg_ram, 3),
        "estimated_energy_wh": round(estimated_wh, 6),
        "estimated_energy_mah": round(estimated_mah, 6)
    }

    save_summary(summary)

    print("Terminé.")
    print(summary)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python transmit_data.py S1|S2|S3")
        sys.exit(1)

    strategy = sys.argv[1]
    if strategy not in ["S1", "S2", "S3"]:
        print("Strategy must be one of: S1, S2, S3")
        sys.exit(1)

    pre_generated_data = generate_all_data()
    print(f"Données pré-générées: {len(pre_generated_data)} records")
    anomaly_in_data = sum(1 for d in pre_generated_data if d["state"] == "anomaly")
    print(f"Anomalies dans les données: {anomaly_in_data}")

    run_strategy(strategy, pre_generated_data)
