import os
import pandas as pd
import matplotlib.pyplot as plt

file = os.path.join("results", "model_comparison.csv")
df = pd.read_csv(file)

print(df)

plt.figure()
plt.bar(df["model"], df["accuracy"])
plt.xlabel("Modèle")
plt.ylabel("Accuracy")
plt.title("Comparaison de la précision")
plt.savefig(os.path.join("results", "accuracy_plot.png"))

plt.figure()
plt.bar(df["model"], df["avg_inference_time_ms"])
plt.xlabel("Modèle")
plt.ylabel("Temps moyen d'inférence (ms)")
plt.title("Comparaison du temps d'inférence")
plt.savefig(os.path.join("results", "inference_time_plot.png"))

plt.figure()
plt.bar(df["model"], df["avg_ram_mb"])
plt.xlabel("Modèle")
plt.ylabel("RAM moyenne (MB)")
plt.title("Comparaison de l'utilisation mémoire")
plt.savefig(os.path.join("results", "ram_plot.png"))

plt.figure()
plt.bar(df["model"], df["estimated_energy_mah"])
plt.xlabel("Modèle")
plt.ylabel("Consommation estimée (mAh)")
plt.title("Comparaison énergétique des modèles")
plt.savefig(os.path.join("results", "processing_energy_plot.png"))

plt.show()
