# Resume Analisis Cloud Dynamics (Dataset Ali v5 - Skalabilitas Moderat 200 RPS & Guncangan Dinamis 150 RPS): Dari Kestabilan Santai Hingga Pembuktian Pemulihan Cepat

Dokumen ini menyajikan ringkasan komprehensif hasil uji performa sistem komputasi awan (*Cloud Dynamics Empirical Analysis*) dari notebook [`cloud_dynamics_empirical_analysis_ali_v5.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_ali_v5.ipynb) berbasis data pengukuran empiris riil pada direktori `cloud-dynamics-experiments/res-ali-v5/`.

Dokumen ini disusun dalam dua lapis penjelasan:
1. **Bahasa Populer & Analogi Kehidupan Sehari-hari:** Ditujukan agar fenomena komputasi awan mudah dipahami oleh pengambil keputusan, mahasiswa, atau masyarakat umum tanpa latar belakang teknis mendalam.
2. **Audit Kritis & Analisis Matematis:** Menjelaskan secara tuntas perilaku sistem pada rentang beban moderat (10–200 RPS), pembuktian skalabilitas linier 100% pada arsitektur *microservices*, serta dinamika pemulihan kilat (*fast recovery*) pasca-guncangan beban seketika 150 RPS (*dynamic burst*).

---

## 1. Analogi Dasar: Jam Kerja Restoran, Peningkatan Teratur, dan Serbuan Kilat (*Flash Sale*)

Setelah pada pengujian sebelumnya (Dataset v3 dan v4) sistem sengaja "dihantam hingga hancur" dengan beban ekstrem 800 pesanan per detik, **Dataset Ali v5** dirancang untuk mengamati perilaku sistem pada **kondisi operasional bisnis yang lebih realistis**:

```text
[Fase 1: Jam Santai (25 RPS)]        [Fase 2: Jam Sibuk Teratur (10-200 RPS)]      [Fase 3: Serbuan Flash Sale (10 -> 150 -> 10 RPS)]
  - Semua koki rileks                  - Pelanggan bertambah bertahap                 - 3 menit awal: santai (10 orang/s)
  - Makanan selesai < 20 milidetik     - Kasir & restoran jaringan melesat 100%       - 2 menit lonjakan: 150 orang/s menyerbu serentak!
  - 100% pesanan sukses bebas error    - Koki komputasi tersedak di 64 orang/s        - 5 menit pemulihan: apakah restoran bisa pulih normal?
```

1. **Beban Santai Steady-State (`constant` 25 RPS):**  
   Mengukur performa dasar ketika server sama sekali tidak stres, sebagai tolok ukur kecepatan intrinsik sistem.
2. **Eskalasi Teratur (`ramp` 10 ke 200 RPS):**  
   Melihat apakah sistem bertumbuh secara linier seimbang (skalabilitas 1:1) saat pelanggan bertambah pelan-pelan.
3. **Guncangan Dinamis Tiga Babak (`burst` 10 $\to$ 150 $\to$ 10 RPS):**  
   Menguji elastisitas dan ketahanan pemulihan (*resilience & recovery time*): ketika dibanting dari sepi ke sangat ramai lalu sepi kembali, apakah server akan macet selamanya (*deadlock*) atau sanggup pulih secara mandiri (*self-healing*)?

---

## 2. Mengenal 3 Karakter Aplikasi dalam Ujian Dinamis v5

1. **`stateless-api` (Si Kasir Tol Otomatis):**  
   Pekerjaannya sangat ringan (membaca dan meneruskan data I/O). Hemat CPU, latensi super rendah, dan tidak mudah terpengaruh oleh lonjakan trafik.
2. **`microservices` (Bintang Utama Dataset v5 - Restoran Berjaringan Tangguh):**  
   Memiliki banyak pelayan dan stasiun kerja yang dikoordinasikan oleh lapisan *service mesh* Linkerd. **Pada rentang beban $\le 200\text{ RPS}$, arsitektur ini menunjukkan performa terbaik dan terbersih tanpa satu pun kesalahan.**
3. **`cpu-bound` (Koki Peracik Resep Rahasia Berkuota Terbatas):**  
   Melakukan komputasi matematika dan enkripsi intensif. Dijatah kuota ketat oleh sistem operasi Kubernetes: **maksimal hanya 0,5 inti CPU (CFS quota 500m)**, yang setara dengan kapasitas fisik sekitar $\sim 56\text{ pesanan/detik}$.

---

## 3. Fakta Empiris di Balik 3 Skenario Pengujian (Dataset Ali v5)

Dataset `res-ali-v5` mencakup 21 eksperimen empiris riil yang dijalankan menggunakan generator beban terbuka [`loadgen_v2.py`](file:///home/ali/kuliah/homelab-fp-rm77/kubernetes/research/cloud-dynamics-experiments/loadgen/loadgen_v2.py):

### 3.1 Skenario `constant`: Kestabilan Santai Bebas Jenuh (25 Pesanan/Detik)
Beban dijalankan stabil pada **25 pesanan per detik** selama 30 detik (total 750 request per run).

![Uji Beban Konstan Ali v5](../outputs/ali-v5/figures/01_constant_scenario_comparison.png)

* **Hasil Observasi Nyata:**
  - Karena beban 25 RPS berada jauh di bawah kapasitas batas terendah (`cpu-bound` ~56 RPS), **ketiga arsitektur mencapai 100% Success Rate sempurna (0 transaksi gagal)**!
  - **Kecepatan Asli Masing-masing Sistem (*Intrinsic Baseline Latency*):**
    - **`stateless-api`:** Waktu tunggu hanya **4,00 milidetik** (P95: 4,85 ms), menggunakan hanya 0,02 core CPU. Sangat kilat!
    - **`microservices`:** Waktu tunggu hanya **8,09 milidetik** (P95: 10,59 ms), menggunakan 0,03 core CPU. Membuktikan bahwa koordinasi antar-layanan Linkerd hanya menambah latensi $\sim 4\text{ milidetik}$.
    - **`cpu-bound`:** Waktu tunggu **18,92 milidetik** (P95: 20,73 ms), menggunakan 0,13 core CPU. Mengerjakan komputasi berat tanpa hambatan antrean.

---

### 3.2 Skenario `ramp`: Skalabilitas Linier Halus 10 ke 200 Pesanan/Detik
Beban dinaikkan perlahan dari **10 hingga 200 pesanan per detik** selama 10 menit (600 detik). Generator menembakkan 62.999 request per eksperimen.

![Uji Eskalasi Ramp Ali v5](../outputs/ali-v5/figures/02_ramp_scenario_comparison.png)

* **Pencapaian Menakjubkan pada Skala 200 RPS:**
  1. **Kesempurnaan Mutlak `microservices` (Panel Bawah):**  
     Menyelesaikan seluruh **62.999 request dengan 100,00% Success Rate (0 failed)** di seluruh 3 replikasi pengujian!  
     - Waktu tunggu rata-rata stabil di angka **8,82 – 8,92 milidetik**.  
     - Konsumsi CPU bertumbuh linier mulus dari 0,03 hingga 0,40 core.  
     - Ini membuktikan bahwa kapasitas batas `microservices` berada jauh di atas 200 RPS (kapasitas jenuhnya ada di ~348 RPS).
  2. **Efisiensi Tinggi `stateless-api` (Panel Atas):**  
     Replikasi r2 dan r3 mencatat **100,00% sukses** dengan latensi rata-rata hanya **4,15 – 4,69 ms**. Pada r1 sempat terjadi gangguan jaringan sesaat di $\sim 142\text{ RPS}$ (menghasilkan 2.940 kegagalan timeout sebelum pulih total). Rata-rata tingkat keberhasilan tetap sangat tinggi (**98,44%**).
  3. **Pemisahan Titik Jenuh Presisi pada `cpu-bound` (Panel Tengah):**  
     - Hingga beban menyentuh **~56 RPS**, sistem berjalan normal 100%.
     - Di atas **64,0 RPS**, koki komputasi mulai tersedak kuota CPU 0,5 core. Goodput mendatar di plafon **~56,8 pesanan/detik**, waktu tunggu melonjak menabrak batas atas 5.000 ms, dan permintaan gagal mulai terbentuk secara konsisten.
     - Dari 62.999 request, **30.816 request berhasil (48,91%)** dan **32.183 request gagal timeout (51,09%)**.

---

### 3.3 Skenario `burst`: Guncangan Dinamis Tiga Babak (10 $\to$ 150 $\to$ 10 Pesanan/Detik)
Skenario ini mensimulasikan kejadian nyata di mana aplikasi tiba-tiba diserbu trafik gila-gilaan (*Flash Sale*):

![Uji Guncangan Dinamis Burst Ali v5](../outputs/ali-v5/figures/03_burst_scenario_comparison.png)

* **Tiga Babak Perjalanan Sistem:**
  1. **Babak 1 - Kondisi Tenang (Detik 0 s.d. 180):**  
     Beban hanya 10 RPS. Ketiga arsitektur santai dengan latensi $< 20\text{ ms}$.
  2. **Babak 2 - Hantaman Lonjakan 150 RPS (Detik 180 s.d. 300 / Berlangsung 2 Menit):**  
     Trafik melonjak mendadak 15 kali lipat!  
     - **`stateless-api` & `microservices`:** Menyerap lonjakan 150 RPS secara instan tanpa berkedip! **100% Success Rate (0 failed)**, latensi rata-rata tetap di bawah 10 ms (4,18 ms pada stateless dan 8,26 ms pada microservices).
     - **`cpu-bound`:** Karena kapasitas fisiknya hanya ~56 RPS, diserbu 150 RPS membuatnya langsung kebanjiran. Selama 2 menit lonjakan, sistem hanya mampu memproses ~56 RPS dan **membuang $\sim 94\text{ request/detik}$ menjadi kegagalan timeout (total 11.000+ request gagal per run)**. CPU mentok di 0,55 core dan latensi menempel di plafon 5.000 ms.
  3. **Babak 3 - Pemulihan Cepat (*Self-Healing Recovery*) (Detik 300 s.d. 600):**  
     Beban diturunkan kembali ke 10 RPS.  
     - **Keajaiban Pemulihan:** Hanya dalam waktu **$\sim 20\text{ detik}$** (pada detik ke-320), seluruh antrean sisa pada `cpu-bound` berhasil dibersihkan, dan waktu tunggu **kembali normal ke 18,7 milidetik**!
     - Ini membuktikan bahwa sistem tidak mengalami *hang* atau kebocoran memori, melainkan sanggup menormalkan diri dengan cepat setelah guncangan mereda.

---

## 4. Titik Jenuh (*Knee of Saturation*): Pembuktian Skalabilitas Linier

![Titik Jenuh Kapasitas Ali v5](../outputs/ali-v5/figures/04_knee_of_saturation_curves.png)

Grafik di atas menunjukkan evaluasi titik jenuh pada rentang 10 s.d. 200 RPS:
1. **Kurva Tongkat Hoki Latensi (Grafik Atas):**  
   - Garis hijau (`microservices`) dan garis biru (`stateless-api`) tetap mendatar di bawah 15 ms hingga ujung 200 RPS. Keduanya **Bebas Jenuh** pada skala pengujian ini.
   - Garis merah (`cpu-bound`) menekuk tajam ke atas (*hockey-stick*) tepat di titik **64,0 RPS**, melesat dari 19 ms ke batas atas garis merah putus-putus (*Timeout Ceiling 5.000 ms*).
2. **Plateau Goodput (Grafik Bawah):**  
   - `stateless-api` dan `microservices` berimpit sempurna dengan garis putus-putus hitam (*Ideal 1:1 Offered Load*).
   - `cpu-bound` memisahkan diri di atas 56 RPS dan mendatar kaku (*Goodput Plateau*) di **~56,8 RPS**.

---

## 5. Kesenjangan Kegagalan Nyata (*Triad Goodput & Drop Gap*)

![Triad Kinerja Goodput Ali v5](../outputs/ali-v5/figures/05_goodput_triad_and_fulfillment.png)

Pada grafik triad di atas:
- Untuk `stateless-api` dan `microservices`, ketiga garis (Offered, Throughput, Goodput) bersatu, menunjukkan **efisiensi penyerapan beban 100%**.
- Untuk `cpu-bound`, area arsir merah (*Failure / Timeout Drop Gap*) terbuka lebar begitu beban melewati 56 RPS. Area merah ini secara akurat memperlihatkan jumlah transaksi yang dibatalkan oleh batas waktu deadline 5,0 detik.

---

## 6. Dinamika Soket Jaringan & Pengendalian Antrean In-Flight

![Dinamika Antrean Soket Ali v5](../outputs/ali-v5/figures/06_queue_backpressure_and_drain_dynamics.png)

Grafik dinamika soket memperlihatkan bagaimana kluster Kubernetes mengelola koneksi TCP aktif:
1. **`microservices` Bebas Beban:** Akumulasi soket aktif in-flight maksimum **hanya 5 koneksi**, membuktikan transaksi diselesaikan seketika tanpa ada yang tertahan di antrean.
2. **`cpu-bound` Tertahan Stabil:** Akumulasi soket aktif tertahan di angka **~285 koneksi**. Buffer jaringan tidak pernah meledak karena request yang lebih tua dari 5,0 detik langsung digugurkan secara berkala.
3. **Pengurasan Akhir Kilat:** Begitu pengujian ramp 600 detik selesai, seluruh sisa antrean soket tuntas dalam waktu **tepat 5,0 detik** (antrean bersih 0).

---

## 7. Matriks Pemeringkatan Kinerja Goodput Lintas Arsitektur (Ali v5)

| Peringkat | Arsitektur Aplikasi | Batas Kapasitas Puncak | Latensi pada Beban Puncak | Tingkat Keberhasilan Riil | Karakteristik Ketahanan |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **1** | **`stateless-api`** | **> 200 RPS** (Absolut ~630 RPS) | 4,15 – 4,69 ms (pada 200 RPS) | **98,44%** | **Sangat Unggul & Efisien:** Latensi terendah secara konsisten (~4 ms). Menyerap lonjakan 150 RPS secara instan tanpa kegagalan (100% sukses) dan konsumsi CPU sangat hemat (0,18 core). |
| **2** | **`microservices`** | **> 200 RPS** (Absolut ~348 RPS) | 8,82 – 8,92 ms (pada 200 RPS) | **100,00%** | **Sangat Tangguh & Bersih:** 100% Success Rate sempurna di seluruh 7 eksperimen tanpa satu pun transaksi gagal. Mampu menyerap lonjakan 150 RPS dengan latensi hanya 8,26 ms, membuktikan kehandalan mesh Linkerd pada beban moderat. |
| **3** | **`cpu-bound`** | **~56,8 RPS** (Batas Kuota CFS) | 5.001 ms (*Timeout Ceiling* pada > 64 RPS) | **66,45%** | **Tergantung Kuota CPU:** Beroperasi sempurna pada 25 RPS steady (100% sukses), namun jenuh pada 64 RPS akibat kuota 0,5 core. Mengalami kegagalan timeout saat dibebani 150–200 RPS, tetapi pulih kilat dalam 20 detik pasca-guncangan. |

---

## 8. Pelajaran Rekayasa untuk Bisnis & Produksi

1. **Keunggulan Arsitektur Microservices pada Beban Nyata:**  
   Banyak orang mengira *microservices* lambat karena memiliki banyak lompatan jaringan (*network hops*). Namun Dataset Ali v5 membuktikan bahwa pada beban moderat ($\le 200\text{ RPS}$), *microservices* yang dilengkapi Linkerd service mesh berjalan sangat mulus (latensi 8 ms) dan memiliki kebersihan transaksi 100% tanpa satu pun kegagalan.
2. **Kesiapan Menghadapi Flash Sale (*Burst Resilience*):**  
   Pengujian dinamis 10 $\to$ 150 $\to$ 10 RPS menunjukkan bahwa sistem yang sehat harus memiliki kemampuan pemulihan cepat (*fast recovery*). Walaupun aplikasi komputasi sempat tersedak selama 2 menit masa lonjakan, ia mampu menormalkan diri dalam tempo 20 detik tanpa memerlukan *restart* kontainer (*pod restart = 0*).
3. **Pentingnya Autoscaling (HPA) untuk Komputasi Berat:**  
   Karena satu kontainer `cpu-bound` berkuota 0,5 core hanya mampu melayani ~56 RPS, layanan yang memiliki fitur enkripsi atau pengolahan data berat **wajib memasang *Horizontal Pod Autoscaler* (HPA)** agar jumlah replika pod otomatis bertambah dari 1 menjadi 3 atau 4 pod saat mendeteksi trafik mendekati 150 RPS.
