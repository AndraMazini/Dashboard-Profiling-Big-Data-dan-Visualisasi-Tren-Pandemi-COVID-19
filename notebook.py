import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 1. Load dataset dari folder data/
df = pd.read_csv('Data/WDI.csv')

# 2. Hitung jumlah baris dan kolom
print("Jumlah Baris:", len(df))
print("Jumlah Kolom:", df.shape[1])
print("\n--- Informasi Struktur Data ---")
df.info()

# 3. Hitung penggunaan memori (MB) & missing values
memory_mb = df.memory_usage(deep=True).sum() / (1024**2)
print(f"\nTotal Penggunaan Memori: {memory_mb:.2f} MB")

print("\n10 Kolom dengan Missing Values Terbanyak:")
print(df.isnull().sum().sort_values(ascending=False).head(10))

# 4. Inspeksi sampel data (5 baris awal & akhir)
print("\n--- 5 Baris Pertama ---")
print(df.head())

print("\n--- 5 Baris Terakhir ---")
print(df.tail())

# 5. Agregasi dan Visualisasi Tren Pertumbuhan
if 'date' in df.columns:
    df['Year'] = pd.to_datetime(df['date']).dt.year

if 'Year' in df.columns and 'new_cases' in df.columns:
    yearly = df.groupby('Year')['new_cases'].sum().reset_index()
    
    plt.figure(figsize=(10, 5))
    plt.plot(yearly['Year'], yearly['new_cases'], marker='o', color='b', linewidth=2)
    plt.title('Total New Cases by Year Globally')
    plt.xlabel('Year')
    plt.ylabel('Total New Cases')
    plt.grid(True)
    plt.show()

# 6. Simpan sampel 1% data ke file CSV baru
df_sample = df.sample(frac=0.01, random_state=42)
df_sample.to_csv('data/WDI_sample.csv', index=False)
print("\nProses selesai! Sampel 1% data berhasil disimpan ke 'Data/WDI_sample.csv'")