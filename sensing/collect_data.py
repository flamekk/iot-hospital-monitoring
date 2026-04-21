import time
import csv
import os
from statistics import mean
import psutil

from sensor_simulator import generate_sensor_data

DEVICE_ID = "DEV001"
EQUIPMENT_TYPE = "ventilator"
COLLECTION_DURATION_SEC = 60
SAMPLING_INTERVAL_SEC = 5
ANOMALY_PROB = 0.15

RPI_POWER_W = 3.5
SUPPLY_VOLTAGE_V = 5.0
SENSOR_READ_COST_J = 0.02

OUTPUT_DATA = os.path.join("..", "results", "sensing_data.csv")
OUTPUT_SUMMARY = os.path.join("..", "results", "sensing_summary.csv")


def ensure_output_dir():
    os.makedirs(os.path.dirname(OUTPUT_DATA), exist_ok=True)


def save_data_to_csv(rows, output_file):
    if not rows:
        return

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def save_summary_to_csv(summary_dict, output_file):
    file_exists = os.path.exists(output_file)

    with open(output_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=summary_dict.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(summary_dict)


def estimate_energy_wh(power_w, duration_sec):
    return power_w * (duration_sec / 3600)


def joules_to_mah(energy_j, voltage_v):
    return (energy_j / voltage_v) * (1000 / 3600)


def main():
    ensure_output_dir()

    collected_rows = []
    collection_times = []
    cpu_usages = []
    ram_usages_mb = []

    process = psutil.Process(os.getpid())

    start_global = time.time()
    end_global = start_global + COLLECTION_DURATION_SEC

    print("Début de la collecte...")

    while time.time() < end_global:
        start_iter = time.time()

        data = generate_sensor_data(
            device_id=DEVICE_ID,
            equipment_type=EQUIPMENT_TYPE,
            anomaly_prob=ANOMALY_PROB
        )
        collected_rows.append(data)

        end_iter = time.time()
        collection_times.append(end_iter - start_iter)

        cpu_usages.append(psutil.cpu_percent(interval=None))
        ram_usages_mb.append(process.memory_info().rss / (1024 * 1024))

        sleep_time = SAMPLING_INTERVAL_SEC - (end_iter - start_iter)
        if sleep_time > 0:
            time.sleep(sleep_time)

    end_total = time.time()
    total_duration = end_total - start_global

    save_data_to_csv(collected_rows, OUTPUT_DATA)

    anomaly_count = sum(1 for row in collected_rows if row["state"] == "anomaly")
    normal_count = sum(1 for row in collected_rows if row["state"] == "normal")

    avg_collection_time_ms = mean(collection_times) * 1000 if collection_times else 0
    avg_cpu = mean(cpu_usages) if cpu_usages else 0
    avg_ram = mean(ram_usages_mb) if ram_usages_mb else 0

    base_energy_wh = estimate_energy_wh(RPI_POWER_W, total_duration)
    base_energy_j = base_energy_wh * 3600
    sensor_energy_j = len(collected_rows) * SENSOR_READ_COST_J
    total_energy_j = base_energy_j + sensor_energy_j

    estimated_wh = total_energy_j / 3600
    estimated_mah = joules_to_mah(total_energy_j, SUPPLY_VOLTAGE_V)

    summary = {
        "device_id": DEVICE_ID,
        "equipment_type": EQUIPMENT_TYPE,
        "sampling_interval_sec": SAMPLING_INTERVAL_SEC,
        "collection_duration_sec": round(total_duration, 2),
        "num_samples": len(collected_rows),
        "normal_samples": normal_count,
        "anomaly_samples": anomaly_count,
        "avg_collection_time_ms": round(avg_collection_time_ms, 3),
        "avg_cpu_percent": round(avg_cpu, 3),
        "avg_ram_mb": round(avg_ram, 3),
        "estimated_power_w": RPI_POWER_W,
        "sensor_read_cost_j": SENSOR_READ_COST_J,
        "estimated_energy_wh": round(estimated_wh, 6),
        "estimated_energy_mah": round(estimated_mah, 6)
    }

    save_summary_to_csv(summary, OUTPUT_SUMMARY)

    print("Collecte terminée.")
    print(f"Nombre d'échantillons : {len(collected_rows)}")
    print(f"Normal : {normal_count} | Anomalies : {anomaly_count}")
    print(f"Temps moyen par lecture : {avg_collection_time_ms:.3f} ms")
    print(f"CPU moyen : {avg_cpu:.2f} %")
    print(f"RAM moyenne : {avg_ram:.2f} MB")
    print(f"Énergie estimée : {estimated_wh:.6f} Wh")
    print(f"Consommation estimée : {estimated_mah:.6f} mAh")


if __name__ == "__main__":
    main()
