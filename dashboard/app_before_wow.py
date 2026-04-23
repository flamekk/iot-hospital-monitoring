import os
import sys
import pandas as pd
import streamlit as st
import joblib

sys.path.append(os.path.join("..", "sensing"))
from sensor_simulator import generate_sensor_data

# -----------------------------
# Configuration page
# -----------------------------
st.set_page_config(
    page_title="IoT Hospital Monitoring Dashboard",
    page_icon="🏥",
    layout="wide"
)

st.markdown("""
    <style>
    .critical-box {
        background-color: #ffebee;
        border: 2px solid #d32f2f;
        padding: 1rem;
        border-radius: 12px;
        color: #b71c1c;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    .health-good {
        color: green;
        font-weight: bold;
        font-size: 20px;
    }
    .health-warning {
        color: orange;
        font-weight: bold;
        font-size: 20px;
    }
    .health-critical {
        color: red;
        font-weight: bold;
        font-size: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# Paths
# -----------------------------
SENSING_SUMMARY = os.path.join("..", "results", "sensing_summary.csv")
NETWORK_SUMMARY = os.path.join("..", "network", "results", "network_summary.csv")
MODEL_SUMMARY = os.path.join("..", "processing", "results", "model_comparison.csv")
MODELS_DIR = os.path.join("..", "processing", "models")

# -----------------------------
# Helpers
# -----------------------------
def load_csv(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

def compute_health_score(data):
    score = 100

    if data["vibration_rms"] > 2.0:
        score -= 35
    elif data["vibration_rms"] > 1.0:
        score -= 20

    if data["power_w"] > 140:
        score -= 25
    elif data["power_w"] > 110:
        score -= 12

    if data["temperature_c"] > 50:
        score -= 30
    elif data["temperature_c"] > 38:
        score -= 15

    if data["current_a"] > 0.75:
        score -= 10
    elif data["current_a"] > 0.55:
        score -= 5

    score = max(0, min(100, score))
    return score

def health_label(score):
    if score >= 90:
        return "Good", "health-good"
    elif score >= 70:
        return "Warning", "health-warning"
    else:
        return "Critical", "health-critical"

def get_global_energy():
    total = 0.0
    sensing_df = load_csv(SENSING_SUMMARY)
    network_df = load_csv(NETWORK_SUMMARY)
    model_df = load_csv(MODEL_SUMMARY)

    if sensing_df is not None and "estimated_energy_mah" in sensing_df.columns:
        total += sensing_df["estimated_energy_mah"].sum()

    if network_df is not None and "estimated_energy_mah" in network_df.columns:
        total += network_df["estimated_energy_mah"].sum()

    if model_df is not None and "estimated_energy_mah" in model_df.columns:
        total += model_df["estimated_energy_mah"].sum()

    return round(total, 4)

def predict_threshold(data):
    if (
        data["vibration_rms"] > 1.0
        or data["power_w"] > 115
        or data["temperature_c"] > 38
    ):
        return 1
    return 0

def load_model(model_name):
    if model_name == "Logistic Regression":
        model_path = os.path.join(MODELS_DIR, "logistic_regression.pkl")
        scaler_path = os.path.join(MODELS_DIR, "scaler.pkl")
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            return joblib.load(model_path), joblib.load(scaler_path)
    elif model_name == "Decision Tree":
        model_path = os.path.join(MODELS_DIR, "decision_tree.pkl")
        if os.path.exists(model_path):
            return joblib.load(model_path), None
    return None, None

def predict_with_model(model_name, data):
    features = ["vibration_rms", "vibration_peak", "power_w", "current_a", "temperature_c"]
    X = pd.DataFrame([{
        "vibration_rms": data["vibration_rms"],
        "vibration_peak": data["vibration_peak"],
        "power_w": data["power_w"],
        "current_a": data["current_a"],
        "temperature_c": data["temperature_c"]
    }])[features]

    if model_name == "Threshold":
        return predict_threshold(data)

    model, scaler = load_model(model_name)
    if model is None:
        return None

    if model_name == "Logistic Regression" and scaler is not None:
        X_scaled = scaler.transform(X)
        return int(model.predict(X_scaled)[0])

    if model_name == "Decision Tree":
        return int(model.predict(X)[0])

    return None

# -----------------------------
# Session state
# -----------------------------
if "anomaly_history" not in st.session_state:
    st.session_state.anomaly_history = []

# -----------------------------
# Header
# -----------------------------
st.title("🏥 IoT Monitoring Dashboard for Medical Equipment")
st.markdown("Monitoring intelligent des équipements médicaux sur Raspberry Pi")

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("Paramètres")

selected_strategy = st.sidebar.selectbox(
    "Choisir une stratégie réseau",
    ["S1", "S2", "S3"]
)

selected_model = st.sidebar.selectbox(
    "Choisir un modèle de prédiction",
    ["Threshold", "Logistic Regression", "Decision Tree"]
)

simulate_now = st.sidebar.button("Simuler une nouvelle mesure")
clear_history = st.sidebar.button("Vider historique anomalies")

if clear_history:
    st.session_state.anomaly_history = []

# -----------------------------
# Simulated data
# -----------------------------
data = generate_sensor_data(
    device_id="DEV001",
    equipment_type="ventilator",
    anomaly_prob=0.2
)

health_score = compute_health_score(data)
health_text, health_class = health_label(health_score)

if data["state"] == "anomaly":
    st.session_state.anomaly_history.append({
        "timestamp": data["timestamp"],
        "device_id": data["device_id"],
        "equipment_type": data["equipment_type"],
        "vibration_rms": data["vibration_rms"],
        "power_w": data["power_w"],
        "temperature_c": data["temperature_c"],
        "severity": "High" if health_score < 70 else "Medium"
    })

# -----------------------------
# Tabs
# -----------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Temps réel",
    "Réseau",
    "Modèles IA",
    "Énergie globale",
    "Prédiction"
])

# -----------------------------
# TAB 1 - Temps réel
# -----------------------------
with tab1:
    st.subheader("Vue temps réel simulée")

    if data["state"] == "anomaly":
        st.markdown(
            """
            <div class="critical-box">
            🚨 CRITICAL ALERT – Equipment Failure Risk Detected
            </div>
            """,
            unsafe_allow_html=True
        )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Vibration RMS", data["vibration_rms"])
    c2.metric("Puissance (W)", data["power_w"])
    c3.metric("Courant (A)", data["current_a"])
    c4.metric("Température (°C)", data["temperature_c"])
    c5.metric("Health Score", f"{health_score}%")

    st.markdown(
        f'<p class="{health_class}">Health Status: {health_text}</p>',
        unsafe_allow_html=True
    )

    st.write("### Dernière mesure")
    st.json(data)

    if data["state"] == "anomaly":
        st.error("🚨 Anomalie détectée sur l’équipement médical")
    else:
        st.success("✅ État normal")

    realtime_df = pd.DataFrame([{
        "Vibration RMS": data["vibration_rms"],
        "Vibration Peak": data["vibration_peak"],
        "Power (W)": data["power_w"],
        "Current (A)": data["current_a"],
        "Temperature (°C)": data["temperature_c"]
    }])
    st.write("### État de fonctionnement")
    st.bar_chart(realtime_df.T)

    st.write("### Historique des anomalies")
    if st.session_state.anomaly_history:
        hist_df = pd.DataFrame(st.session_state.anomaly_history)
        st.dataframe(hist_df, use_container_width=True)
    else:
        st.info("Aucune anomalie enregistrée pour le moment.")

    sensing_df = load_csv(SENSING_SUMMARY)
    if sensing_df is not None:
        st.write("### Résultats Sensing Layer")
        st.dataframe(sensing_df, use_container_width=True)

# -----------------------------
# TAB 2 - Réseau
# -----------------------------
with tab2:
    st.subheader("Comparaison des stratégies réseau")

    network_df = load_csv(NETWORK_SUMMARY)

    if network_df is not None:
        st.dataframe(network_df, use_container_width=True)

        st.write("### Stratégie sélectionnée")
        selected_row = network_df[network_df["strategy"] == selected_strategy]
        if not selected_row.empty:
            row = selected_row.iloc[0]
            a, b, c = st.columns(3)
            a.metric("Latence moyenne (ms)", row["avg_latency_ms"])
            b.metric("Bande passante (bytes/s)", row["bandwidth_bytes_sec"])
            c.metric("Énergie (mAh)", row["estimated_energy_mah"])

        st.write("### Latence moyenne")
        st.bar_chart(network_df.set_index("strategy")["avg_latency_ms"])

        st.write("### Bande passante")
        st.bar_chart(network_df.set_index("strategy")["bandwidth_bytes_sec"])

        st.write("### Consommation énergétique réseau")
        st.bar_chart(network_df.set_index("strategy")["estimated_energy_mah"])

        best_energy = network_df.loc[network_df["estimated_energy_mah"].idxmin()]
        st.info(
            f"Stratégie recommandée : {best_energy['strategy']} "
            f"(plus économe avec {best_energy['estimated_energy_mah']} mAh)"
        )
    else:
        st.warning("Aucun fichier réseau trouvé.")

# -----------------------------
# TAB 3 - Modèles IA
# -----------------------------
with tab3:
    st.subheader("Comparaison des modèles légers")

    model_df = load_csv(MODEL_SUMMARY)

    if model_df is not None:
        st.dataframe(model_df, use_container_width=True)

        st.write("### Accuracy")
        st.bar_chart(model_df.set_index("model")["accuracy"])

        st.write("### Temps d'inférence moyen (ms)")
        st.bar_chart(model_df.set_index("model")["avg_inference_time_ms"])

        st.write("### RAM moyenne (MB)")
        st.bar_chart(model_df.set_index("model")["avg_ram_mb"])

        st.write("### Consommation énergétique")
        st.bar_chart(model_df.set_index("model")["estimated_energy_mah"])

        best_model = model_df.loc[model_df["estimated_energy_mah"].idxmin()]
        st.info(
            f"Modèle recommandé : {best_model['model']} "
            f"(plus économique avec {best_model['estimated_energy_mah']} mAh)"
        )
    else:
        st.warning("Aucun fichier modèle trouvé.")

# -----------------------------
# TAB 4 - Énergie globale
# -----------------------------
with tab4:
    st.subheader("Rapport global de consommation")

    sensing_df = load_csv(SENSING_SUMMARY)
    network_df = load_csv(NETWORK_SUMMARY)
    model_df = load_csv(MODEL_SUMMARY)

    sensing_energy = sensing_df["estimated_energy_mah"].sum() if sensing_df is not None else 0
    network_energy = network_df["estimated_energy_mah"].sum() if network_df is not None else 0
    model_energy = model_df["estimated_energy_mah"].sum() if model_df is not None else 0

    energy_df = pd.DataFrame({
        "Layer": ["Sensing", "Network", "Processing"],
        "Energy_mAh": [sensing_energy, network_energy, model_energy]
    })

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sensing (mAh)", round(sensing_energy, 4))
    c2.metric("Network (mAh)", round(network_energy, 4))
    c3.metric("Processing (mAh)", round(model_energy, 4))
    c4.metric("Total (mAh)", get_global_energy())

    st.write("### Energy Breakdown")
    st.bar_chart(energy_df.set_index("Layer"))

    st.write("### Tableau récapitulatif")
    st.dataframe(energy_df, use_container_width=True)

# -----------------------------
# TAB 5 - Prediction
# -----------------------------
with tab5:
    st.subheader("Prédiction d’anomalie")

    st.write("### Modèle sélectionné")
    st.write(selected_model)

    pred = predict_with_model(selected_model, data)

    pred_features_df = pd.DataFrame([{
        "vibration_rms": data["vibration_rms"],
        "vibration_peak": data["vibration_peak"],
        "power_w": data["power_w"],
        "current_a": data["current_a"],
        "temperature_c": data["temperature_c"]
    }])

    st.write("### Données d’entrée")
    st.dataframe(pred_features_df, use_container_width=True)

    if pred is None:
        st.warning("Le modèle n’a pas pu être chargé.")
    else:
        if pred == 1:
            st.error("🔴 Prédiction : ANOMALIE")
        else:
            st.success("🟢 Prédiction : NORMAL")

        st.write("### Interprétation")
        if selected_model == "Threshold":
            st.info("Le modèle Threshold utilise des règles simples basées sur des seuils.")
        elif selected_model == "Logistic Regression":
            st.info("La régression logistique estime la probabilité qu’une mesure appartienne à la classe anomalie.")
        elif selected_model == "Decision Tree":
            st.info("L’arbre de décision applique une suite de règles apprises à partir des données.")
