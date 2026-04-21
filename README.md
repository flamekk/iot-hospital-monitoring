# 🏥 IoT Hospital Monitoring System

## 📌 Overview
This project presents a complete **IoT-based system for monitoring medical equipment** in a hospital environment.  
The objective is to detect abnormal behavior in devices such as ventilators, pumps, and monitoring systems in order to prevent failures and improve reliability.

The system is implemented on a **Raspberry Pi** and follows a **4-layer IoT architecture**, integrating data collection, transmission, intelligent processing, and visualization.

---

## 🎯 Objectives
- Monitor the physical state of medical equipment
- Detect anomalies in real-time
- Optimize energy consumption in IoT systems
- Compare multiple data transmission strategies
- Implement lightweight AI models on an edge device
- Provide a real-time monitoring dashboard

---

## 🏗️ System Architecture


Sensors → Raspberry Pi → Network → AI Models → Dashboard


The system is organized into four main layers:

---

## 🔹 Sensing Layer
This layer is responsible for data collection.

Implemented features:
- Simulation of IoMT data (no physical sensors required)
- Parameters:
  - Vibration (RMS & Peak)
  - Electrical Power (W)
  - Current (A)
  - Temperature (°C)
- Real-time data generation
- CPU, RAM, and execution time monitoring
- Energy consumption estimation

Experiments:
- Tested multiple sampling intervals (1s, 2s, 5s)
- Measured impact on:
  - Number of samples
  - Energy consumption

---

## 🔹 Network Layer
This layer manages data transmission between the edge device and server.

Implemented strategies:
- **S1 (Real-time transmission)** → send every data point
- **S2 (Batch transmission)** → send grouped data
- **S3 (Event-based transmission)** → send only anomalies

Measured metrics:
- Latency (ms)
- Bandwidth (bytes/sec)
- Number of messages
- Energy consumption (mAh)

Key findings:
- S1 → lowest latency, highest energy usage
- S2 → balanced solution
- S3 → best energy efficiency

---

## 🔹 Data Processing Layer
This layer performs anomaly detection directly on the Raspberry Pi (Edge AI).

Implemented models:
- Threshold-based model (rule-based)
- Logistic Regression
- Decision Tree

Dataset:
- Generated synthetic dataset (~5000 samples)
- Balanced normal/anomaly classes

Evaluated metrics:
- Accuracy
- Precision / Recall / F1-score
- Inference time (ms)
- RAM usage (MB)
- Energy consumption (mAh)

Key findings:
- All models achieved high accuracy (simulated data)
- Threshold model is:
  - Fastest
  - Most energy-efficient
- ML models provide more flexibility for real-world scenarios

---

## 🔹 Application Layer
A **Streamlit dashboard** was developed to visualize system behavior.

Features:
- Real-time simulated monitoring
- Automatic anomaly alerts 🚨
- Network strategies comparison
- AI models comparison
- Global energy consumption report
- Interactive data visualization

---

## 🧪 Technologies Used
- Python 3
- Raspberry Pi
- Pandas
- Scikit-learn
- Flask (IoT server)
- Streamlit (dashboard)
- Matplotlib

---

## 📊 Results Summary

### Network Optimization
- **S3 (event-based)** minimizes bandwidth and energy usage
- **S1** provides real-time monitoring but higher cost

### AI Performance
- All models reached high accuracy
- **Threshold model** is optimal for edge devices

### Energy Optimization
- Best configurations:
  - **Low energy → S3 + Threshold**
  - **Balanced → S2 + Logistic Regression**
  - **Real-time critical systems → S1**

---

## ⚡ Edge AI & IoT

This project demonstrates:
- Edge Computing using Raspberry Pi
- Local data processing (no cloud dependency)
- Lightweight Machine Learning (TinyML-inspired)
- Energy-aware IoT system design

---

## 📁 Project Structure


iot_hospital_monitoring/
├── sensing/ # Data simulation & collection
├── network/ # Transmission strategies
├── processing/ # ML models & evaluation
├── dashboard/ # Streamlit application
├── results/ # CSV & graphs
├── models/ # Trained models
└── README.md


---

## 🚀 How to Run


git clone https://github.com/flamekk/iot-hospital-monitoring.git
cd iot-hospital-monitoring

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cd dashboard
streamlit run app.py
👩‍💻 Authors
Hiba Zbari
Aya Fadel
Najoua Mouaddab

Engineering Students – Big Data & Artificial Intelligence

📌 Notes
Dataset is fully simulated
Focus on IoT energy optimization and edge intelligence
Inspired by IoMT (Internet of Medical Things) and Edge AI concepts

---
⭐ Contribution

Feel free to fork this project or suggest improvements!
---
