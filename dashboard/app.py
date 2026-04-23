import os
import sys
import pandas as pd
import streamlit as st
import joblib
import os
import sys
import pandas as pd
import streamlit as st
import joblib
sys.path.append(os.path.join("..", "sensing"))
from sensor_simulator import generate_sensor_data
from datetime import datetime
from fpdf import FPDF

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
def generate_hospital_devices():
    devices = []
    equipment_list = [
        ("PUMP_01", "Pump", "Room A1"),
        ("VENT_01", "Ventilator", "Room A2"),
        ("MON_01", "Monitor", "Room B1"),
        ("PUMP_02", "Pump", "Room B2"),
        ("VENT_02", "Ventilator", "Room C1"),
        ("MON_02", "Monitor", "Room C2"),
    ]

    for device_id, equipment_type, room in equipment_list:
        d = generate_sensor_data(
            device_id=device_id,
            equipment_type=equipment_type,
            anomaly_prob=0.25
        )
        d["room"] = room
        d["health_score"] = compute_health_score(d)
        devices.append(d)

    return pd.DataFrame(devices)


def status_from_health(score):
    if score >= 90:
        return "🟢 Normal"
    elif score >= 70:
        return "🟠 Warning"
    return "🔴 Critical"


def priority_from_data(data):
    if data["equipment_type"].lower() == "ventilator" and data["state"] == "anomaly":
        return "High"
    elif data["state"] == "anomaly":
        return "Medium"
    return "Low"


def generate_pdf_report(output_path, total_energy, best_strategy, best_model):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    page_width = 190  # largeur sûre sur A4 avec marges

    pdf.set_font("Arial", "B", 14)
    pdf.cell(page_width, 10, "IoT Hospital Monitoring - Jury Report", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", size=11)

    # Toujours revenir à la marge gauche avant d'écrire
    pdf.set_x(10)
    pdf.multi_cell(page_width, 8, "Project summary:")
    pdf.ln(2)

    lines = [
        "Monitoring of medical equipment using Raspberry Pi",
        "Comparison of IoT transmission strategies",
        "Comparison of lightweight anomaly detection models",
        f"Best network strategy: {best_strategy}",
        f"Best AI model: {best_model}",
        f"Total estimated energy: {total_energy} mAh"
    ]

    for line in lines:
        pdf.set_x(10)
        pdf.multi_cell(page_width, 8, f"- {line}")

    pdf.ln(4)
    pdf.set_x(10)
    pdf.multi_cell(page_width, 8, "Main conclusion:")

    pdf.ln(2)
    pdf.set_x(10)
    pdf.multi_cell(
        page_width,
        8,
        "The project demonstrates that combining event-based transmission "
        "with lightweight edge intelligence improves energy efficiency "
        "while maintaining anomaly detection performance."
    )

    pdf.output(output_path)
# -----------------------------
# Session state
# -----------------------------
if "anomaly_history" not in st.session_state:
    st.session_state.anomaly_history = []
if "alert_history" not in st.session_state:
    st.session_state.alert_history = []

if "replay_data" not in st.session_state:
    st.session_state.replay_data = []

if "acknowledged_alerts" not in st.session_state:
    st.session_state.acknowledged_alerts = set()
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
hospital_df = generate_hospital_devices()

for _, row in hospital_df.iterrows():
    if row["state"] == "anomaly":
        alert_id = f"{row['device_id']}_{row['timestamp']}"
        st.session_state.alert_history.append({
            "alert_id": alert_id,
            "timestamp": row["timestamp"],
            "device_id": row["device_id"],
            "equipment_type": row["equipment_type"],
            "room": row["room"],
            "priority": priority_from_data(row),
            "health_score": row["health_score"],
            "status": "Unacknowledged"
        })

replay_rows = []
for i in range(12):
    replay_rows.append({
        "t": f"-{60 - i*5}s",
        "vibration_rms": max(0.1, data["vibration_rms"] * (0.6 + i * 0.05)),
        "power_w": max(10, data["power_w"] * (0.7 + i * 0.04)),
        "temperature_c": max(20, data["temperature_c"] * (0.75 + i * 0.03)),
    })

st.session_state.replay_data = replay_rows

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
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "Temps réel",
    "Vue Hôpital",
    "Alertes",
    "Replay Anomalie",
    "Réseau",
    "Modèles IA",
    "Simulation What-if",
    "Énergie globale",
    "Prédiction",
    "Rapport PDF"
])
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


with tab2:
    st.subheader("Vue hôpital interactive")

    display_df = hospital_df[["device_id", "equipment_type", "room", "health_score"]].copy()
    display_df["status"] = display_df["health_score"].apply(status_from_health)

    st.write("### Statut des équipements")
    st.dataframe(display_df, use_container_width=True)

    st.write("### Plan simplifié des salles")
    cols = st.columns(3)

    grouped = hospital_df.groupby("room")
    rooms = list(grouped.groups.keys())

    for i, room in enumerate(rooms):
        room_df = grouped.get_group(room)
        with cols[i % 3]:
            st.markdown(f"#### {room}")
            for _, row in room_df.iterrows():
                score = row["health_score"]
                status = status_from_health(score)
                st.markdown(
                    f"**{row['device_id']}** ({row['equipment_type']})  \n"
                    f"Status: {status}  \n"
                    f"Health Score: {score}%"
                )


with tab3:
    st.subheader("Alertes intelligentes et priorisées")

    if st.session_state.alert_history:
        alerts_df = pd.DataFrame(st.session_state.alert_history).drop_duplicates(subset=["alert_id"])
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        alerts_df["priority_rank"] = alerts_df["priority"].map(priority_order)
        alerts_df = alerts_df.sort_values(by=["priority_rank", "timestamp"])

        st.dataframe(
            alerts_df[["timestamp", "device_id", "equipment_type", "room", "priority", "health_score", "status"]],
            use_container_width=True
        )

        st.write("### Accusé de réception")
        selected_alert = st.selectbox(
            "Choisir une alerte à accuser réception",
            alerts_df["alert_id"].tolist()
        )

        if st.button("Accuser réception"):
            st.session_state.acknowledged_alerts.add(selected_alert)
            for alert in st.session_state.alert_history:
                if alert["alert_id"] == selected_alert:
                    alert["status"] = "Acknowledged"
            st.success("Alerte marquée comme traitée.")
    else:
        st.success("Aucune alerte active.")


with tab4:
    st.subheader("Timeline avant / après anomalie")

    replay_df = pd.DataFrame(st.session_state.replay_data)

    if not replay_df.empty:
        st.write("### Évolution des signaux avant la détection")
        st.line_chart(replay_df.set_index("t")[["vibration_rms", "power_w", "temperature_c"]])

        st.write("### Données du replay")
        st.dataframe(replay_df, use_container_width=True)
    else:
        st.info("Aucune séquence de replay disponible.")


with tab5:
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


with tab6:
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


with tab7:
    st.subheader("Mode simulation What-if")

    strategy_sim = st.selectbox("Stratégie simulée", ["S1", "S2", "S3"], key="whatif_strategy")
    sampling_sim = st.slider("Fréquence d’échantillonnage (secondes)", 1, 10, 2)
    model_sim = st.selectbox("Modèle simulé", ["Threshold", "Logistic Regression", "Decision Tree"], key="whatif_model")

    if strategy_sim == "S1":
        latency = 10 + sampling_sim * 0.2
        energy = 12.0 + (1 / sampling_sim)
        bandwidth = 220 + (10 / sampling_sim)
    elif strategy_sim == "S2":
        latency = 13 + sampling_sim * 0.5
        energy = 11.6 + (0.5 / sampling_sim)
        bandwidth = 180 + (6 / sampling_sim)
    else:
        latency = 11.5 + sampling_sim * 0.3
        energy = 11.3 + (0.2 / sampling_sim)
        bandwidth = 45 + (2 / sampling_sim)

    if model_sim == "Threshold":
        inference = 0.15
        accuracy = 1.0
    elif model_sim == "Logistic Regression":
        inference = 3.32
        accuracy = 1.0
    else:
        inference = 3.17
        accuracy = 1.0

    a, b, c, d = st.columns(4)
    a.metric("Latence estimée (ms)", round(latency, 2))
    b.metric("Énergie estimée (mAh)", round(energy, 2))
    c.metric("Bande passante estimée", round(bandwidth, 2))
    d.metric("Accuracy estimée", round(accuracy, 2))

    st.write("### Temps d'inférence estimé")
    st.metric("Inference (ms)", inference)

    st.info(
        f"Configuration simulée : {strategy_sim} + {model_sim} avec fréquence {sampling_sim}s"
    )


with tab8:
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


with tab9:
    st.subheader("Prédiction d’anomalie")

    mode = st.radio("Mode de prédiction", ["Temps réel", "Batch (10 mesures)"])

    st.write("### Modèle sélectionné")
    st.write(selected_model)

    if mode == "Temps réel":
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

    else:
        batch_data = []

        for i in range(10):
            d = generate_sensor_data(
                device_id=f"DEV_BATCH_{i+1}",
                equipment_type="ventilator",
                anomaly_prob=0.3
            )

            pred = predict_with_model(selected_model, d)

            batch_data.append({
                "device_id": d["device_id"],
                "vibration_rms": d["vibration_rms"],
                "vibration_peak": d["vibration_peak"],
                "power_w": d["power_w"],
                "current_a": d["current_a"],
                "temperature_c": d["temperature_c"],
                "prediction": "ANOMALIE" if pred == 1 else "NORMAL"
            })

        df_batch = pd.DataFrame(batch_data)

        st.write("### Prédictions multiples")
        st.dataframe(df_batch, use_container_width=True)

        st.write("### Répartition des prédictions")
        pred_counts = df_batch["prediction"].value_counts()
        st.bar_chart(pred_counts)

        st.write("### Interprétation")
        st.info(
            "Le mode Batch permet d’évaluer le comportement du modèle sur plusieurs mesures simulées "
            "afin d’observer la répartition entre états normaux et anomalies."
        )
with tab10:
    st.subheader("Rapport automatique PDF")

    network_df = load_csv(NETWORK_SUMMARY)
    model_df = load_csv(MODEL_SUMMARY)

    best_strategy = "N/A"
    best_model = "N/A"

    if network_df is not None:
        best_strategy = network_df.loc[network_df["estimated_energy_mah"].idxmin(), "strategy"]

    if model_df is not None:
        best_model = model_df.loc[model_df["estimated_energy_mah"].idxmin(), "model"]

    total_energy = get_global_energy()

    st.write("### Résumé automatique")
    st.write(f"**Stratégie gagnante :** {best_strategy}")
    st.write(f"**Modèle gagnant :** {best_model}")
    st.write(f"**Énergie totale estimée :** {total_energy} mAh")

    pdf_path = os.path.join(".", "jury_report.pdf")

    if st.button("Générer le rapport PDF"):
        generate_pdf_report(pdf_path, total_energy, best_strategy, best_model)
        st.success("PDF généré avec succès.")

    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            st.download_button(
                label="Télécharger le rapport PDF",
                data=f,
                file_name="jury_report.pdf",
                mime="application/pdf"
            )
