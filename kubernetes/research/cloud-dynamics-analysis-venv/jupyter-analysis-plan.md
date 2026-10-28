# Master Plan: Pembangunan Jupyter Notebook Analisis Cloud Dynamics (Per Skenario, Titik Jenuh, dan Goodput)

Dokumen ini adalah rencana kerja komprehensif (*Master Plan & Implementation Blueprint*) yang dirancang khusus untuk diinstruksikan kepada **Agent AI** (atau dieksekusi secara mandiri) untuk membangun **Jupyter Notebook Analisis Empiris** berbasis data hasil pengujian controlled workload experiments di direktori `cloud-dynamics-experiments/results/`.

---

## 1. Ringkasan Eksekutif & Tujuan Notebook

Notebook yang akan dibangun bertujuan untuk:
1. **Mengonsolidasikan dan Mengotomatisasi Ingesti Multi-Eksperimen:** Membaca seluruh direktori hasil eksperimen (`results/*/combined.csv` dan `metadata.json`) yang mencakup berbagai arsitektur aplikasi (`stateless-api`, `cpu-bound`, `microservices`) dan berbagai skenario beban (`constant`, `ramp`, `burst`, `periodic`, `variable`).
2. **Analisis Komparatif Per Skenario:** Membandingkan respons dinamis masing-masing arsitektur aplikasi terhadap setiap pola beban.
3. **Deteksi dan Analisis Titik Jenuh (*Knee of Saturation*):** Mengidentifikasi titik kritis di mana sistem mulai jenuh, latensi melonjak eksponensial, dan sumber daya menyentuh batas limit.
4. **Analisis Mendalam Terkait Goodput:** Mengevaluasi efektivitas transaksi produktif, rasio pemenuhan beban (*fulfillment ratio*), dinamika antrean *backpressure*, serta perbandingan ketahanan Goodput antar arsitektur aplikasi.
5. **Ekspor Artefak Riset:** Menghasilkan tabel ringkasan (*summary tables*) dan grafik visualisasi publikasi ilmiah (*high-res figures*) secara otomatis.

---

## 2. Struktur File & Lokasi Kerja

* **Lokasi Data Input:** `kubernetes/research/cloud-dynamics-experiments/results/` (setiap folder eksperimen memuat `combined.csv` dan `metadata.json`).
* **Virtual Environment & Dependencies:** `kubernetes/research/cloud-dynamics-analysis-venv/` (berisi Jupyter, Pandas, NumPy, SciPy, Matplotlib).
* **Target Notebook Baru:** `kubernetes/research/cloud-dynamics-analysis-venv/notebooks/cloud_dynamics_empirical_analysis.ipynb`.
* **Lokasi Ekspor Output:** `kubernetes/research/cloud-dynamics-analysis-venv/outputs/`
  * `outputs/figures/`: Seluruh visualisasi grafik (.png / .svg, 300 DPI).
  * `outputs/tables/`: Tabel metrik ringkasan (.csv).

---

## 3. Rencana Tahapan Implementasi Notebook (Step-by-Step)

```text
Tahap 1: Auto-Discovery & Data Ingestion
                   |
                   v
Tahap 2: Analisis Komparatif Per Skenario
                   |
                   v
Tahap 3: Analisis Titik Jenuh (Knee of Saturation)
                   |
                   v
Tahap 4: Analisis Mendalam Goodput & Efisiensi
                   |
                   v
Tahap 5: Sintesis, Pemeringkatan Arsitektur & Ekspor
```

---

### Tahap 1: Auto-Discovery, Ingesti Data, & Harmonisasi Multi-Eksperimen

Agent AI harus menulis kode Python yang mampu mendeteksi secara dinamis seluruh folder eksperimen tanpa hardcoding nama direktori:

1. **Pemindaian Eksperimen Dinamis:**
   * Melakukan iterasi pada direktori `RESULTS_DIR` (default: `../cloud-dynamics-experiments/results`).
   * Membaca file `metadata.json` pada setiap eksperimen untuk mengekstrak:
     * `application.name` (misal: `stateless-api`, `cpu-bound`, `microservices`).
     * `profile` (misal: `constant`, `ramp`, `burst`, `periodic`, `variable`).
     * `replicate` (nomor replikasi, misal `r1`, `r2`).
     * Parameter durasi, `warmup_seconds`, dan `cooldown_seconds`.
2. **Pemuatan dan Penyelarasan Dataset (`combined.csv`):**
   * Memuat data 25 kolom dari `combined.csv`.
   * Menambahkan kolom pengidentifikasi: `app_name`, `scenario_profile`, `experiment_id`.
   * Melakukan konversi tipe data numerik (`pd.to_numeric`) dengan penanganan nilai kosong (*missing values*) secara aman.
   * Menyelaraskan sumbu waktu relatif (`elapsed_s`).
3. **Kompilasi Master DataFrame:**
   * Menggabungkan seluruh eksperimen ke dalam satu DataFrame terstruktur (`df_campaign`) dan kamus data per-eksperimen untuk mempermudah analisis agregat maupun individual.

---

### Tahap 2: Analisis Komparatif Per Skenario (Scenario-by-Scenario Comparative Analysis)

Pada tahap ini, notebook menganalisis perilaku masing-masing arsitektur aplikasi terhadap 5 pola beban standar:

#### 2.1 Skenario `constant` (Baseline & Kestabilan Steady-State)
* **Tujuan:** Menguji stabilitas pada beban konstan terprediksi.
* **Analisis & Metrik:**
  * Throughput & Goodput rata-rata vs Target RPS.
  * *Jitter* dan koefisien variasi latensi ($CV = \frac{\sigma}{\mu}$).
  * Stabilitas penggunaan CPU (`CPU_USAGE`) dan memori (`MEMORY_WORKING_SET`).
* **Visualisasi:** Plot time-series (RPS, Latensi, CPU) membandingkan `stateless-api` vs `cpu-bound` vs `microservices`.

#### 2.2 Skenario `ramp` (Respons Terhadap Peningkatan Beban Gradual)
* **Tujuan:** Mengamati transisi sistem dari kondisi beban ringan menuju saturasi.
* **Analisis & Metrik:**
  * Laju pertumbuhan latensi seiring peningkatan beban ($R(t)$).
  * Deviasi antara laju kirim (`achieved_rps`) vs Goodput nyata (`LINKERD_GOODPUT_RPS`).
* **Visualisasi:** Dual-axis chart: Sumbu kiri (Target RPS vs Goodput RPS), sumbu kanan (Latensi P50, P95, P99).

#### 2.3 Skenario `burst` (Resiliensi Terhadap Lonjakan Beban Tiba-Tiba / Spike)
* **Tujuan:** Menguji elastisitas dan pemulihan sistem terhadap lonjakan beban seketika.
* **Analisis & Metrik:**
  * *Peak overshoot latency*: Seberapa tinggi lonjakan latensi saat burst terjadi.
  * *Recovery time* ($T_{\text{recover}}$): Waktu yang dibutuhkan latensi dan Goodput untuk kembali ke baseline setelah burst berakhir.
  * Terjadinya penumpukan koneksi TCP (`LINKERD_TCP_CONNECTIONS`).
* **Visualisasi:** Time-series dengan penanda visual (*shaded area*) durasi burst, menampilkan kurva respons pemulihan.

#### 2.4 Skenario `periodic` (Respons Dinamis Terhadap Gelombang Beban Berulang)
* **Tujuan:** Menguji perilaku sistem pada pola siklus berulang (sinusoidal).
* **Analisis & Metrik:**
  * *Phase lag* (pergeseran fase): Keterlambatan respons CPU/latensi terhadap gelombang trafik masuk.
  * Histeresis performa: Apakah performa saat beban turun identik dengan saat beban naik.
* **Visualisasi:** Overlay plot gelombang beban vs kurva Goodput dan kurva utilisasi CPU.

#### 2.5 Skenario `variable` (Resiliensi Terhadap Beban Stokastik / Acak)
* **Tujuan:** Menguji ketahanan terhadap fluktuasi beban yang tidak teratur (*unpredictable load*).
* **Analisis & Metrik:**
  * Distribusi probabilitas latensi (KDE / Histogram).
  * Stabilitas Goodput saat terjadi transisi anak tangga (*step changes*).
* **Visualisasi:** Violin plot / Box plot distribusi latensi antar arsitektur.

---

### Tahap 3: Analisis Titik Jenuh (*Knee of Saturation & Capacity Limits*)

Tahap ini secara matematis mengidentifikasi batas kapasitas fisik setiap arsitektur aplikasi:

1. **Pemodelan Kurva Beban vs Latensi (*Hockey-Stick Curve*):**
   * Membuat scatter plot: Sumbu X adalah **Offered Load** (`target_rps` / `achieved_rps`), sumbu Y adalah **Latensi** (`mean_latency_ms` dan `LINKERD_LATENCY_P99`).
2. **Algoritma Deteksi Titik Jenuh (*Knee Detection Algorithm*):**
   * **Kriteria 1 (Turunan Latensi):** Titik di mana laju perubahan latensi terhadap RPS ($\frac{d(\text{Latency})}{d(\text{RPS})}$) mengalami percepatan tajam (lonjakan kurva kedua $\frac{d^2(\text{Latency})}{d(\text{RPS})^2}$).
   * **Kriteria 2 (Deviasi Goodput):** Titik di mana Goodput mulai tertinggal dari Offered Load:
     $$\frac{\text{Goodput (RPS)}}{\text{Target (RPS)}} < 0.90 \quad (90\%)$$
3. **Korelasi dengan Batas Sumber Daya Sistem:**
   * Memplot `CPU_USAGE` terhadap `target_rps`.
   * Menandai titik aktivasi throttling CPU (`CPU_THROTTLED > 0`).
   * Mengonfirmasi hukum Little: Pada saat CPU menyentuh limit ($100\%$), penambahan beban tidak meningkatkan Goodput melainkan menumpuk antrean, menyebabkan latensi naik secara linear terhadap jumlah request yang mengantre.
4. **Tabel Ambang Batas Kapasitas (*Saturation Threshold Summary Table*):**
   Menghasilkan tabel ringkasan per arsitektur:
   * **RPS Maksimum Bebas Jenuh (*Saturation RPS Ceiling*).**
   * **Latensi pada Titik Jenuh.**
   * **Penyebab Utama Bottleneck** (CPU bound, I/O bound, Network bound).

---

### Tahap 4: Analisis Mendalam Terkait Goodput

Fokus utama pada bab penutup adalah membedah metrik Goodput sebagai indikator mutu kinerja utama:

1. **Perbandingan Tiga Serangkai: Offered Load vs Throughput vs Goodput:**
   * Memplot dalam satu grafik terpadu:
     * Garis 1: `target_rps` (Beban yang diminta).
     * Garis 2: `LINKERD_REQUEST_RATE` (Throughput total masuk).
     * Garis 3: `LINKERD_GOODPUT_RPS` dan `success` (Goodput produktif).
   * Menjelaskan area kesenjangan (*gap*) antara Throughput dan Goodput saat saturasi terjadi.
2. **Kompilasi Metrik Persentase Goodput:**
   Agent AI harus menghitung dan menyajikan 4 metrik persentase:
   * **Total Goodput Delivery Ratio:** $\frac{\sum \text{success}}{\sum \text{sent}} \times 100\%$ (mengukur efisiensi penyerapan beban).
   * **Goodput Success Rate:** $\frac{\sum \text{success}}{\sum \text{success} + \sum \text{failed}} \times 100\%$ atau `LINKERD_SUCCESS_RATE` (mengukur kebersihan dari HTTP 5xx).
   * **Instantaneous Offered Load Fulfillment Ratio:** $\frac{\text{Goodput (RPS)}}{\text{Target (RPS)}} \times 100\%$ pada tiap fase pengujian.
   * **Capacity Saturation Ratio:** $\frac{\text{Goodput Aktual}}{\text{Kapasitas Teoretis Maksimum}} \times 100\%$.
3. **Analisis Fenomena Antrean & Pengurasan (*Backpressure & Drain Dynamics*):**
   * Menganalisis korelasi penumpukan antrean terhadap kolom `LINKERD_TCP_CONNECTIONS`.
   * Membedah fase pengurasan (*drain phase*) di akhir tes: menunjukkan bahwa ketika `sent = 0`, server tetap menghasilkan Goodput stabil hingga ribuan request antrean tuntas diproses.
4. **Matriks Evaluasi dan Pemeringkatan Arsitektur Aplikasi:**
   Tabel perbandingan performa Goodput antar arsitektur:

   | Arsitektur Aplikasi | Kapasitas Puncak Goodput (RPS) | Latensi pada Puncak (ms) | Success Rate (%) | Delivery Ratio (%) | Ketahanan Terhadap Beban Ekstrem |
   | :--- | :--- | :--- | :--- | :--- | :--- |
   | `stateless-api` | ... | ... | ... | ... | ... |
   | `cpu-bound` | ~56.4 RPS | ~4,543 ms | 99.96% | 99.96% | Jenuh pada CPU limit |
   | `microservices` | ... | ... | ... | ... | ... |

---

### Tahap 5: Ekspor Laporan Otomatis & Standar Kualitas

Notebook harus menyertakan fungsi ekspor di sel-sel akhir:
1. **Penyimpanan Gambar Otomatis:**
   * Setiap figur visualisasi disimpan menggunakan `plt.savefig(OUTPUTS / 'figures' / f'{filename}.png', dpi=300, bbox_inches='tight')`.
2. **Penyimpanan Tabel Ringkasan:**
   * Tabel komparasi dan ringkasan metrik diekspor ke format CSV di `outputs/tables/`.
3. **Standar Kualitas Notebook:**
   * *Self-Contained & Reproducible:* Notebook harus dapat dijalankan dari sel awal hingga akhir tanpa error (`Kernel -> Restart & Run All Cells`).
   * *Naratif Komprehensif:* Di antara setiap sel kode, wajib terdapat sel Markdown yang menjelaskan hipotesis, metodologi, dan interpretasi temuan teknis (tidak hanya menampilkan grafik kosong).

---

## 4. Prompt Siap Pakai untuk Menginstruksikan Agent AI

Berikut adalah teks instruksi (*prompt template*) yang dapat langsung Anda berikan kepada Agent AI untuk mengeksekusi rencana ini:

```markdown
Halo Agent AI, tolong buatkan sebuah Jupyter Notebook analisis empiris komprehensif pada direktori:
`kubernetes/research/cloud-dynamics-analysis-venv/notebooks/cloud_dynamics_empirical_analysis.ipynb`

Gunakan rencana kerja pada file `kubernetes/research/cloud-dynamics-analysis-venv/jupyter-analysis-plan.md` sebagai acuan utama.

Spesifikasi data dan analisis yang harus Anda bangun:
1. **Data Ingestion:**
   - Pindai direktori `../cloud-dynamics-experiments/results/` secara dinamis.
   - Baca setiap `metadata.json` dan `combined.csv` (berisi 25 kolom telemetri client, sistem kontainer, dan metrik Linkerd).
   - Bentuk master DataFrame yang menggabungkan seluruh arsitektur aplikasi (stateless-api, cpu-bound, microservices) dan skenario (constant, ramp, burst, periodic, variable).

2. **Analisis Per Skenario:**
   - Buat analisis dan visualisasi komparatif terstruktur untuk masing-masing dari 5 skenario (constant, ramp, burst, periodic, variable).
   - Tampilkan plot performa (RPS, Latensi, CPU Usage) yang membandingkan performa antar-arsitektur.

3. **Analisis Titik Jenuh (Knee of Saturation):**
   - Deteksi titik jenuh kapasitas (hockey-stick latency curve dan goodput plateau).
   - Korelasikan titik jenuh dengan metrik CPU_USAGE dan CPU_THROTTLED.
   - Sajikan tabel ambang batas kapasitas per arsitektur.

4. **Analisis Mendalam Terkait Goodput:**
   - Bandingkan Offered Load vs Throughput (LINKERD_REQUEST_RATE) vs Goodput (LINKERD_GOODPUT_RPS / success).
   - Hitung 4 persentase Goodput: Overall Goodput Delivery Ratio, Goodput Success Rate, Instantaneous Fulfillment Ratio, dan Capacity Utilization.
   - Analisis dinamika antrean backpressure, LINKERD_TCP_CONNECTIONS, dan fase drain.
   - Buat tabel pemeringkatan performa Goodput antar-arsitektur aplikasi.

5. **Ekspor & Kualitas:**
   - Ekspor grafik ke `../outputs/figures/` (300 DPI) dan tabel ke `../outputs/tables/` (.csv).
   - Sertakan narasi Markdown yang mendalam, penjelasan teknis, dan rumus matematika di setiap bagian.
   - Pastikan notebook bebas error dan dapat dieksekusi secara berurutan.
```
