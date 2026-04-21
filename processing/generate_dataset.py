import csv
import os
import sys

sys.path.append(os.path.join("..", "sensing"))
from sensor_simulator import generate_sensor_data

OUTPUT_FILE = os.path.join("results", "medical_equipment_dataset.csv")
NUM_SAMPLES = 5000


def main():
    os.makedirs("results", exist_ok=True)

    rows = []
    for _ in range(NUM_SAMPLES):
        row = generate_sensor_data(
            device_id="DEV001",
            equipment_type="ventilator",
            anomaly_prob=0.2
        )
        rows.append(row)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Dataset généré : {OUTPUT_FILE}")
    print(f"Nombre de lignes : {len(rows)}")


if __name__ == "__main__":
    main()
