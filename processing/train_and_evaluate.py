
import os
import time
import csv
import joblib
import psutil
import pandas as pd

from statistics import mean
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

DATA_FILE = os.path.join("results", "medical_equipment_dataset.csv")
RESULTS_FILE = os.path.join("results", "model_comparison.csv")
MODELS_DIR = os.path.join("models")

SUPPLY_VOLTAGE_V = 5.0
INFERENCE_COST_J_BASE = 0.01


def joules_to_mah(energy_j, voltage_v):
    return (energy_j / voltage_v) * (1000 / 3600)


def evaluate_threshold_model(X_test, y_test):
    start = time.time()
    process = psutil.Process(os.getpid())

    preds = []
    ram_usages = []

    for _, row in X_test.iterrows():
        pred = 1 if (row["vibration_rms"] > 1.0 or row["power_w"] > 115 or row["temperature_c"] > 38) else 0
        preds.append(pred)
        ram_usages.append(process.memory_info().rss / (1024 * 1024))

    end = time.time()

    inference_time_ms = ((end - start) / len(X_test)) * 1000
    avg_ram_mb = mean(ram_usages) if ram_usages else 0

    energy_j = len(X_test) * INFERENCE_COST_J_BASE
    energy_mah = joules_to_mah(energy_j, SUPPLY_VOLTAGE_V)

    return preds, inference_time_ms, avg_ram_mb, energy_mah


def evaluate_sklearn_model(model, X_test, y_test):
    start = time.time()
    process = psutil.Process(os.getpid())

    preds = []
    ram_usages = []

    for i in range(len(X_test)):
        sample = X_test.iloc[[i]]
        pred = model.predict(sample)[0]
        preds.append(pred)
        ram_usages.append(process.memory_info().rss / (1024 * 1024))

    end = time.time()

    inference_time_ms = ((end - start) / len(X_test)) * 1000
    avg_ram_mb = mean(ram_usages) if ram_usages else 0

    energy_j = len(X_test) * (INFERENCE_COST_J_BASE * 1.2)
    energy_mah = joules_to_mah(energy_j, SUPPLY_VOLTAGE_V)

    return preds, inference_time_ms, avg_ram_mb, energy_mah


def compute_metrics(y_true, y_pred):
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1_score": f1_score(y_true, y_pred, zero_division=0),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist()
    }


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)

    df = pd.read_csv(DATA_FILE)

    df["label"] = df["state"].map({"normal": 0, "anomaly": 1})

    features = ["vibration_rms", "vibration_peak", "power_w", "current_a", "temperature_c"]
    X = df[features]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    joblib.dump(scaler, os.path.join(MODELS_DIR, "scaler.pkl"))

    results = []

    # 1) Threshold
    threshold_preds, threshold_time, threshold_ram, threshold_energy = evaluate_threshold_model(X_test, y_test)
    threshold_metrics = compute_metrics(y_test, threshold_preds)

    results.append({
        "model": "Threshold",
        "accuracy": round(threshold_metrics["accuracy"], 4),
        "precision": round(threshold_metrics["precision"], 4),
        "recall": round(threshold_metrics["recall"], 4),
        "f1_score": round(threshold_metrics["f1_score"], 4),
        "avg_inference_time_ms": round(threshold_time, 6),
        "avg_ram_mb": round(threshold_ram, 4),
        "estimated_energy_mah": round(threshold_energy, 6),
        "confusion_matrix": str(threshold_metrics["confusion_matrix"])
    })

    # 2) Logistic Regression
    logreg = LogisticRegression(max_iter=500)
    logreg.fit(X_train_scaled, y_train)
    joblib.dump(logreg, os.path.join(MODELS_DIR, "logistic_regression.pkl"))

    logreg_preds, logreg_time, logreg_ram, logreg_energy = evaluate_sklearn_model(logreg, pd.DataFrame(X_test_scaled, columns=features), y_test)
    logreg_metrics = compute_metrics(y_test, logreg_preds)

    results.append({
        "model": "LogisticRegression",
        "accuracy": round(logreg_metrics["accuracy"], 4),
        "precision": round(logreg_metrics["precision"], 4),
        "recall": round(logreg_metrics["recall"], 4),
        "f1_score": round(logreg_metrics["f1_score"], 4),
        "avg_inference_time_ms": round(logreg_time, 6),
        "avg_ram_mb": round(logreg_ram, 4),
        "estimated_energy_mah": round(logreg_energy, 6),
        "confusion_matrix": str(logreg_metrics["confusion_matrix"])
    })

    # 3) Decision Tree
    tree = DecisionTreeClassifier(max_depth=4, random_state=42)
    tree.fit(X_train, y_train)
    joblib.dump(tree, os.path.join(MODELS_DIR, "decision_tree.pkl"))

    tree_preds, tree_time, tree_ram, tree_energy = evaluate_sklearn_model(tree, X_test, y_test)
    tree_metrics = compute_metrics(y_test, tree_preds)

    results.append({
        "model": "DecisionTree",
        "accuracy": round(tree_metrics["accuracy"], 4),
        "precision": round(tree_metrics["precision"], 4),
        "recall": round(tree_metrics["recall"], 4),
        "f1_score": round(tree_metrics["f1_score"], 4),
        "avg_inference_time_ms": round(tree_time, 6),
        "avg_ram_mb": round(tree_ram, 4),
        "estimated_energy_mah": round(tree_energy, 6),
        "confusion_matrix": str(tree_metrics["confusion_matrix"])
    })

    with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print("Évaluation terminée.")
    for r in results:
        print(r)


if __name__ == "__main__":
    main()
