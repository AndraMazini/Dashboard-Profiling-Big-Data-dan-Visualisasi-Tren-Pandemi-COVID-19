# Dashboard EDA Kesehatan Global (COVID-19)

Proyek ini adalah **Exploratory Data Analysis (EDA)** untuk dataset COVID-19
dunia dengan tampilan web dashboard. Dibuat sebagai **Tugas 1 Mata Kuliah Big Data**.

Data yang digunakan adalah dataset publik dari **Our World in Data (OWID)**
(`WDI.csv`, sekitar 96 MB, berisi data harian per negara).

---

## Apa Isi Proyek Ini?

1. **Memuat & menganalisis data besar (96 MB)** di dalam RAM dengan Pandas.
2. **Membuat sampel 1%** data ke `Data/WDI_sample.csv` agar mudah dibuka/diproses manual.
3. **Dashboard web** yang menampilkan:

   | Bagian | Isi |
   |---|---|
   | Kartu Ringkasan | Total baris & kolom, beban memori RAM, status file sampel |
   | Negara Terdampak | 10 negara kasus terbanyak vs 10 paling sedikit (grafik + tabel) |
   | CFR per Negara | Negara dengan rasio kematian/kasus *(Case Fatality Rate)* tertinggi |
   | Korelasi Vaksin vs Kematian | Scatter plot cakupan vaksin vs kematian per juta penduduk + nilai Pearson `r` |
   | Tren per Kontinen | Grafik multi-line kasus baru per 1 juta penduduk (agregasi bulanan) per benua |
   | Tren Global | Kasus baru per tahun secara global |
   | Missing Values | 10 kolom dengan data kosong terbanyak |

---

## Teknologi / Tools yang Digunakan

| Tool | Fungsi |
|---|---|
| **Python 3** | Bahasa pemrograman utama |
| **Pandas** | Membaca, memfilter, mengelompokkan, dan menganalisis dataset besar |
| **Matplotlib** | Membuat semua grafik pada dashboard |
| **Flask** | Framework web untuk menyajikan dashboard |
| **Bootstrap 5** (CDN) | Styling tampilan dashboard |
| **Jinja2** (bawaan Flask) | Template HTML untuk menampilkan data |

> **Catatan Big Data:** data 96 MB dimuat langsung ke RAM (uji skala Big Data).
> Grafik dibuat di server lalu dikirim ke browser sebagai gambar *base64*,
> sehingga browser tidak perlu memproses dataset besar.

---

## Struktur Folder

```
Tugas 1/
├── app.py                 # Aplikasi Flask utama (semua logika & pembuatan grafik)
├── notebook.py            # Skrip EDA sederhana (jalankan di terminal/notebook)
├── templates/
│   └── index.html         # Template dashboard (HTML + Bootstrap)
├── Data/
│   ├── WDI.csv            # Dataset full COVID-19 (~96 MB)
│   └── WDI_sample.csv     # Sampel 1% dari WDI.csv (dibuat otomatis saat app dijalankan)
└── README.md              # File ini
```

---

## Cara Menjalankan

### 1. Persiapkan lingkungan

Install Python 3 lalu install pustaka yang dibutuhkan:

```bash
pip install pandas matplotlib flask
```

### 2. Jalankan dashboard

```bash
python app.py
```

Tunggu pesan `Data berhasil dimuat!`, lalu buka browser di:

```
http://127.0.0.1:5000
```

*(Server berjalan di mode debug. Data 96 MB hanya dimuat sekali saat server pertama kali dinyalakan.)*

### 3. Alternatif: jalankan EDA sederhana di terminal

```bash
python notebook.py
```

Skrip ini mencetak struktur data, jumlah missing values, dan menyimpan sampel 1%.

---

## Memahami Data (`Data/WDI.csv`)

Dataset OWID berisi **satu baris per negara per tanggal** (format `location` + `date`).
Kolom utama dikelompokkan sebagai berikut:

| Grup | Kolom Contoh |
|---|---|
| Identitas | `iso_code`, `continent`, `location`, `date` |
| Kasus | `total_cases`, `new_cases`, `new_cases_per_million`, ... |
| Kematian | `total_deaths`, `new_deaths`, `total_deaths_per_million`, ... |
| Vaksinasi | `total_vaccinations`, `people_fully_vaccinated_per_hundred`, ... |
| Testing | `total_tests`, `positive_rate`, `tests_per_case`, ... |
| Rumah Sakit | `icu_patients`, `hosp_patients`, ... |
| Sosio-ekonomi | `population`, `gdp_per_capita`, `median_age`, `life_expectancy`, ... |
| Kebijakan | `stringency_index` |

**Catatan kelengkapan:** kolom kasus/kematian/populasi terisi hampir lengkap,
sedangkan kolom ICU/RS, testing, vaksinasi, dan *excess mortality* cukup banyak
yang kosong — perlu diperhatikan saat dianalisis.

---

## Logika Analisis di `app.py` (Singkat)

- Filter **negara asli** dengan mengecek `iso_code` (mengeluarkan agregat seperti
  "World", "Asia", "High-income countries" yang berawalan `OWID_`).
- **Negara terdampak**: ambil nilai maksimum `total_cases` & `total_deaths` per negara,
  lalu urutkan naik/turun.
- **CFR** = `total_deaths / total_cases × 100`, hanya negara dengan ≥ 100.000 kasus.
- **Korelasi vaksin vs kematian**: nilai maksimal `people_fully_vaccinated_per_hundred`
  vs `total_deaths_per_million` per negara, dihitung dengan korelasi Pearson.
- **Tren kontinen**: jumlah `new_cases_per_million` per bulan per benua
  (normalisasi per populasi agar antar-benua bisa dibandingkan).

---

## Catatan

- Server Flask ini untuk **pengembangan / tugas kuliah**, bukan untuk produksi.
- Grafik dirender ulang setiap halaman di-refresh (menggunakan data yang sudah
  dimuat di memori).
- Sampel `WDI_sample.csv` ditulis ulang setiap kali `app.py` dijalankan
  (dengan `random_state=42` agar hasilnya konsisten).