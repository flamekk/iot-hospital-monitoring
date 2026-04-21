import pandas as pd
import matplotlib.pyplot as plt
import os

file = os.path.join("results", "network_summary.csv")
df = pd.read_csv(file)

print(df)

plt.figure()
plt.bar(df["strategy"], df["avg_latency_ms"])
plt.xlabel("Stratégie")
plt.ylabel("Latence moyenne (ms)")
plt.title("Comparaison de la latence")
plt.savefig(os.path.join("results", "latency_plot.png"))

plt.figure()
plt.bar(df["strategy"], df["bandwidth_bytes_sec"])
plt.xlabel("Stratégie")
plt.ylabel("Bande passante (bytes/s)")
plt.title("Comparaison de la bande passante")
plt.savefig(os.path.join("results", "bandwidth_plot.png"))

plt.figure()
plt.bar(df["strategy"], df["estimated_energy_mah"])
plt.xlabel("Stratégie")
plt.ylabel("Consommation estimée (mAh)")
plt.title("Comparaison énergétique des stratégies")
plt.savefig(os.path.join("results", "network_energy_plot.png"))

plt.show()
