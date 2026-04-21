import pandas as pd
import matplotlib.pyplot as plt
import os

file = os.path.join("..","results","sensing_summary.csv")

df = pd.read_csv(file)

print(df)

plt.figure()
plt.bar(df["sampling_interval_sec"], df["num_samples"])
plt.xlabel("Sampling Interval (sec)")
plt.ylabel("Number of Samples")
plt.title("Sampling Frequency Impact")
plt.savefig("../results/samples_plot.png")

plt.figure()
plt.bar(df["sampling_interval_sec"], df["estimated_energy_mah"])
plt.xlabel("Sampling Interval (sec)")
plt.ylabel("Energy Consumption (mAh)")
plt.title("Energy Consumption vs Sampling Rate")
plt.savefig("../results/energy_plot.png")

plt.show()
