import os
import sys
import time
import pandas as pd
import streamlit as st

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

# -----------------------------
# Paths
# -----------------------------
SENSING_SUMMARY = os.path.join("..", "results", "sensing_summary.csv")
NETWORK_SUMMARY = os.path.join("..", "network", "results", "network_summary.csv")
MODEL_SUMMARY = os.path.join("..", "processing", "results", "model_comparison.csv")

# -----------------------------
# Helpers
# -----------------------------
def load_csv(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    return None

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

# -----------------------------
# Header
# -----------------------------
st.title("🏥 IoT Monitoring Dashboard for Medical Equipment")
st.markdown("Monitoring des équipements médicaux sur Raspberry Pi")

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("Paramètres")
refresh_data = st.sidebar.button("Rafraîchir les données")
simulate_now = st.sidebar.button("Simuler une nouvelle mesure")

# -----------------------------
# Tabs
# -----------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "Temps réel",
    "Réseau",
    "Modèles IA",
    "Énergie globale"
])

# -----------------------------
# TAB 1 - Temps réel
# -----------------------------
with tab1:
    st.subheader("Vue temps réel simulée")

    data = generate_sensor_data(
        device_id="DEV001",
        equipment_type="ventilator",
        anomaly_prob=0.2
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Vibration RMS", data["vibration_rms"])
    col2.metric("Puissance (W)", data["power_w"])
    col3.metric("Courant (A)", data["current_a"])
    col4.metric("Température (°C)", data["temperature_c"])

    st.write("### Dernière mesure")
    st.json(data)

    if data["state"] == "anomaly":
        st.error("🚨 Alerte : anomalie détectée sur l'équipement médical")
    else:
        st.success("✅ État normal")

    st.write("### État de fonctionnement")
    realtime_df = pd.DataFrame([{
        "Vibration RMS": data["vibration_rms"],
        "Vibration Peak": data["vibration_peak"],
        "Power (W)": data["power_w"],
        "Current (A)": data["current_a"],
        "Temperature (°C)": data["temperature_c"]
    }])

    st.bar_chart(realtime_df.T)

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

        st.write("### Latence moyenne")
        st.bar_chart(network_df.set_index("strategy")["avg_latency_ms"])

        st.write("### Bande passante")
        st.bar_chart(network_df.set_index("strategy")["bandwidth_bytes_sec"])

        st.write("### Consommation énergétique réseau")
        st.bar_chart(network_df.set_index("strategy")["estimated_energy_mah"])

        best_energy = network_df.loc[network_df["estimated_energy_mah"].idxmin()]
        st.info(
            f"Stratégie la plus économe : {best_energy['strategy']} "
            f"({best_energy['estimated_energy_mah']} mAh)"
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
            f"Modèle le plus économique : {best_model['model']} "
            f"({best_model['estimated_energy_mah']} mAh)"
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

    st.write("### Répartition énergétique")
    st.bar_chart(energy_df.set_index("Layer"))

    st.write("### Tableau récapitulatif")
    st.dataframe(energy_df, use_container_width=True)

    st.success(
        "✅ Rapport global généré. "
        "Le meilleur projet est celui qui équilibre précision élevée et faible consommation."
    )
