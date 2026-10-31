# Resume Analisis Cloud Dynamics (Dataset Ali v4 - Beban Ekstrem 800 RPS Open-Loop): Mengapa Angka Kegagalan Meledak dan Bagaimana Uji Terbuka Mengungkap Realita Sebenarnya

Dokumen ini menyajikan ringkasan komprehensif hasil uji performa sistem komputasi awan (*Cloud Dynamics Empirical Analysis*) dari notebook [`cloud_dynamics_empirical_analysis_ali_v4.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_ali_v4.ipynb) berbasis data pengukuran empiris riil pada direktori `cloud-dynamics-experiments/res-ali-v4/`.

Dokumen ini disusun dalam dua lapis penjelasan:
1. **Bahasa Populer & Analogi Kehidupan Sehari-hari:** Ditujukan agar fenomena komputasi awan mudah dipahami oleh pengambil keputusan, mahasiswa, atau masyarakat umum tanpa latar belakang teknis mendalam.
2. **Audit Kritis & Analisis Matematis:** Menjelaskan secara tuntas mengapa tingkat kegagalan (*failed requests*) meledak drastis (hingga 87,8% pada aplikasi komputasi berat), mengapa fenomena antrean 54 menit lenyap total, dan bagaimana generator beban terbuka (*open-loop generator*) mengungkap perilaku sistem dunia nyata.

---

## 1. Kilas Balik Paradigma: Dari "Antrean Tersembunyi" Menuju "Realita Terbuka"

Pada pengujian sebelumnya (Dataset v1, v2, dan v3), alat penguji beban (*load generator v1*) bekerja seperti **kantor pendaftaran tertutup**:
- Klien hanya memiliki 256 petugas pengirim (*workers*).
- Jika server di dalam kluster mulai lambat, ribuan permintaan baru tidak ditembakkan ke jaringan, melainkan **disimpan diam-diam di ruang tunggu memori internal laptop penguji** (Python queue).
- Akibatnya, server tampak "baik-baik saja" dengan tingkat keberhasilan (Success Rate) palsu sebesar **98,98%**, padahal di belakang layar ada 183.000 permintaan yang tertahan dan membutuhkan waktu **54 menit** hanya untuk diselesaikan setelah pengujian usai! Fenomena ini dalam ilmu rekayasa komputer disebut **Coordinated Omission** (kebutaan antrean akibat penahanan beban di sisi klien).

### Revolusi Generator Terbuka pada Dataset Ali v4 (`loadgen_v2.py`)
Pada Dataset Ali v4, generator dimutakhirkan menjadi arsitektur **Open-Loop Asinkronus murni** ([`loadgen_v2.py`](file:///home/ali/kuliah/homelab-fp-rm77/kubernetes/research/cloud-dynamics-experiments/loadgen/loadgen_v2.py)):
1. **Tidak Ada Antrean di Klien:** Setiap permintaan yang dijadwalkan langsung ditembakkan seketika itu juga ke gerbang jaringan Kubernetes (Ingress NGINX & kernel socket buffer).
2. **Batas Waktu Ketat dari Jadwal Kedatangan (*Strict Deadline Timeout 5.0 Detik*):** Jika sebuah permintaan belum mendapatkan jawaban lengkap dalam waktu **5,0 detik sejak jadwal permintaan diluncurkan**, transaksi tersebut **langsung dinyatakan GAGAL (TIMEOUT)**. Tidak ada lagi penantian sabar berjam-jam!
3. **Hasilnya:** Seluruh kelemahan dan batas fisik server terbongkar secara telanjang dan jujur.

---

## 2. Analogi Sederhana: Gerbang Konser Musik Tanpa Ruang Tunggu Tertutup

Bayangkan sebuah **Pintu Masuk Stadion Konser Musik Megah yang Dijejali 800 Penonton per Detik**:

```text
[800 Penonton Datang per Detik (Offered Load)]
                      ||
                      \/
[Gerbang Jaringan Ingress NGINX & Buffer Soket Kubernetes]
                      ||
       +--------------+--------------+
       |                             |
[Loket Masuk Cepat]         [Pemeriksaan Sidik Jari Rumit]
 (`stateless-api`)                  (`cpu-bound`)
       |                             |
(Kapasitas 630 orang/s)      (Kapasitas HANYA 56 orang/s)
[223.385 Lolos Masuk]        [29.691 Lolos Masuk]
[19.613 Tiket Batal/Timeout] [213.308 Penonton Ditolak/Timeout!]
(Tingkat Sukses: 91,9%)      (Tingkat Sukses HANCUR: 12,2%!)
```

1. **Beban Datang (*Offered Load*):** 800 penonton merangsek ke pintu masuk setiap detik.
2. **Throughput Jaringan:** Berapa banyak koneksi soket yang diterima oleh penjaga gerbang depan.
3. **Goodput (Transaksi Sukses Nyata):** Berapa banyak penonton yang **berhasil masuk ke dalam stadion dalam waktu kurang dari 5 detik dengan tiket valid (HTTP 200 OK)**.
4. **Kegagalan (*Failed Requests*):** Penonton yang waktu antrenya melebihi 5 detik langsung pulang dengan kecewa (aplikasi menampilkan layar error / timeout).

---

## 3. Mengenal 3 Karakter Aplikasi dalam Ujian Terbuka 800 RPS

1. **`stateless-api` (Si Pintu Putar Otomatis Cekatan):**  
   Hanya membaca kartu secara nirkabel (I/O asinkronus non-blocking). Sangat cepat, hemat tenaga CPU, dan mampu memproses ratusan orang per detik secara serentak.
2. **`microservices` (Pemeriksaan Berantai Multi-Petugas):**  
   Penonton harus melewati loket depan (*frontend*), loket validasi tiket, dan loket bagasi (*backend*), yang semuanya dihubungkan oleh jalur khusus *service mesh* Linkerd. Koordinasi sangat rapi, tetapi memiliki batas kelancaran di jalur lorong penghubung.
3. **`cpu-bound` (Petugas Pemeriksa Dokumen Rumit yang Tangannya Diikat):**  
   Harus memverifikasi enkripsi sidik jari matematika yang sangat berat. Masalahnya, sistem operasi Kubernetes memberikan aturan kaku: **ia hanya boleh menggunakan tenaga maksimal setengah orang / 0,5 inti CPU (kuota CFS 500m)**.

---

## 4. Fakta Empiris di Balik 3 Skenario Pengujian (Dataset Ali v4)

Dataset `res-ali-v4` menguji 21 eksperimen empiris riil dengan generator open-loop:

### 4.1 Skenario `constant`: Beban Konstan 100 Pesanan/Detik
Beban langsung dipatok stabil pada **100 pesanan per detik** selama 30 detik (total 3.000 request).

![Uji Beban Konstan Ali v4](../outputs/ali-v4/figures/01_constant_scenario_comparison.png)

* **Hasil Observasi Nyata:**
  - **`microservices` (Juara Bertahan di 100 RPS):** Berhasil melayani **3.000 dari 3.000 pesanan (100% Success Rate, 0 failed)**! Waktu tunggu rata-rata hanya **8,2 milidetik** dengan CPU sangat hemat (0,11 core).
  - **`stateless-api` (Sangat Stabil):** Melayani **2.824 pesanan sukses** dan 176 gagal akibat lonjakan inisiasi buffer soket di detik pertama (94,1% sukses), dengan latensi 148 ms.
  - **`cpu-bound` (Langsung Kolaps Sejak Awal):**  
    Karena kapasitas layanannya hanya mampu melayani ~56 pesanan/detik, dipaksa melayani 100 pesanan/detik membuat antrean soket langsung meluap. Waktu tunggu menabrak batas atas 5.000 ms. Hasilnya: **1.596 pesanan (53,2%) GAGAL TOTAL karena timeout**, hanya 1.404 pesanan yang berhasil diselesaikan!

---

### 4.2 Skenario `ramp`: Eskalasi Beban Bertahap 10 ke 800 Pesanan/Detik
Beban dinaikkan perlahan dari **10 pesanan/detik merangkak naik hingga 800 pesanan/detik** selama 10 menit (600 detik). Generator menembakkan total ~242.998 request per eksperimen secara tepat waktu.

![Uji Eskalasi Ramp Ali v4](../outputs/ali-v4/figures/02_ramp_scenario_comparison.png)

* **Terungkapnya Realita Kegagalan pada Model Terbuka:**
  1. **Keruntuhan Total `cpu-bound` (Panel Tengah):**  
     Sejak detik ke-54 (saat beban baru menyentuh **~81 RPS**), server mulai membuang request yang kedaluwarsa. Mau beban dinaikkan hingga 800 RPS, Goodput-nya tertahan kaku di plafon **~56,8 pesanan/detik**.  
     - Dari 242.998 request yang dikirimkan, **213.308 request (87,8%) DINYATAKAN GAGAL (TIMEOUT)!**  
     - Hanya **29.691 request (12,22%)** yang berhasil diselamatkan. Latensi P95 menempel kaku di garis batas sabar 5.001 ms.
  2. **Daya Tahan Menengah `microservices` (Panel Bawah):**  
     Mampu melayani beban linier tanpa error hingga **~348 RPS**. Di atas angka tersebut, antrean di proxy Linkerd mulai padat. Hasil akhir: **145.662 sukses (59,94%)** dan **97.337 request gagal**.
  3. **Keunggulan Mutlak `stateless-api` (Panel Atas):**  
     Mampu melayani beban linier mulus hingga **~630 RPS**. Baru di atas 630 RPS prosesor menyentuh utilisasi 0,76 core dan menghasilkan sedikit kegagalan di puncak 800 RPS. Hasil akhir: **223.385 sukses (91,93%)** dan hanya 19.613 gagal!

---

### 4.3 Skenario `burst`: Uji Stabilitas Operasional 40 Pesanan/Detik
Sistem diuji pada beban stabil terukur **40 pesanan per detik** selama 600 detik (total 24.000 request per run).

![Uji Stabilitas Burst Ali v4](../outputs/ali-v4/figures/03_burst_scenario_comparison.png)

* **Hasil Observasi:**  
  - Karena 40 RPS berada di bawah batas kapasitas terendah (`cpu-bound` ~56 RPS), **ketiga arsitektur mencapai 100% Success Rate sempurna (0 failed dari total 72.000 request di 3 replikasi)**!
  - `stateless-api`: Waktu tunggu rata-rata **3,9 ms**, CPU 0,05 core.
  - `microservices`: Waktu tunggu rata-rata **8,2 ms**, CPU 0,09 core.
  - `cpu-bound`: Waktu tunggu rata-rata **38,6 ms**, CPU 0,49 core.
  - **Kesimpulan Saintifik:** Pada kondisi di mana beban tidak melampaui kapasitas fisik kontainer, generator open-loop bekerja dengan kestabilan absolut tanpa menghasilkan error semu.

---

## 5. Titik Jenuh (*Knee of Saturation*): Hukum Antrean & Plafon Batas Waktu

![Titik Jenuh Kapasitas Ali v4](../outputs/ali-v4/figures/04_knee_of_saturation_curves.png)

Grafik di atas memperlihatkan perbandingan kurva latensi (*Hockey-Stick*) dan kurva Goodput:
1. **Kurva Latensi Hockey-Stick (Grafik Atas):**  
   - Pada pengujian tertutup lama (v3), kurva latensi tertahan di 4,6 detik akibat keterbatasan 256 worker.
   - Pada pengujian terbuka v4, kurva latensi `cpu-bound` melesat vertikal dan **membentur plafon garis merah putus-putus (*Timeout Ceiling 5.000 ms*)**.
2. **Plafon Goodput Tiga Kasta (Grafik Bawah):**  
   - `cpu-bound`: Menekuk paling dini pada **64,0 RPS**, Goodput mendatar di **~56,8 RPS**.
   - `microservices`: Menekuk pada **348,4 RPS**, Goodput mendatar di **~320 RPS**.
   - `stateless-api`: Menekuk pada **630,2 RPS**, Goodput mendatar di **~580 RPS**.

---

## 6. Kesenjangan Kegagalan Nyata (*Triad Goodput & Real Failure Gap*)

![Triad Kinerja Goodput Ali v4](../outputs/ali-v4/figures/05_goodput_triad_and_fulfillment.png)

Pada grafik triad di atas:
- **Garis Putus-putus Hitam:** Beban yang diminta pengguna (*Offered Load*).
- **Garis Oranye:** Laju request yang ditembakkan ke jaringan (*Throughput Dispatched*).
- **Garis Tebal Berwarna:** Transaksi yang benar-benar berhasil selesai (*Goodput*).
- **Area Arsir Merah (*Failure / Timeout Drop Gap*):** Kesenjangan antara beban yang ditembakkan dan beban yang berhasil diproses.

Pada `cpu-bound`, area merah melebar secara masif seiring peningkatan beban. Setiap request di area merah ini adalah pengguna aplikasi yang mengalami *loading screen* selama 5 detik lalu mendapatkan pesan "Koneksi Terputus / Server Sibuk".

---

## 7. Dinamika Soket Jaringan & Lenyapnya "Antrean Siluman 54 Menit"

Salah satu penemuan paling memuaskan pada Dataset Ali v4 adalah pembuktian perilaku antrean soket di dunia nyata:

![Dinamika Antrean Soket Ali v4](../outputs/ali-v4/figures/06_queue_backpressure_and_drain_dynamics.png)

1. **Antrean Soket In-Flight Dibatasi Secara Alami:**  
   - Pada dataset v3, antrean menumpuk hingga 183.000 request karena generator terus menampung request di memori.
   - Pada dataset v4, akumulasi soket aktif in-flight di jaringan **tertahan stabil di kisaran 450 – 620 koneksi aktif**.
   - Mengapa tidak meledak ke ratusan ribu? Karena **setiap request yang telah menunggu 5,0 detik langsung dibatalkan (dibuang) oleh klien**, sehingga slot soket dibebaskan kembali secara dinamis! Angka ini sinkron dengan metrik Linkerd (`LINKERD_TCP_CONNECTIONS` puncak 616 hingga 904 koneksi).
2. **Fase Pengurasan (*Drain Phase*) Kilat:**  
   - Ketika pengujian 600 detik selesai dan pengiriman berhenti (`sent = 0`), server hanya membutuhkan waktu tambahan **1 hingga 5 detik** untuk membersihkan seluruh sisa antrean soket menjadi 0!
   - **Tidak ada lagi fase pengurasan semu selama 54 menit seperti pada dataset v3!**

---

## 8. Matriks Pemeringkatan Kinerja Goodput Lintas Arsitektur (Ali v4)

| Peringkat | Arsitektur Aplikasi | Batas Kapasitas Puncak | Latensi pada Beban Puncak | Tingkat Keberhasilan Riil | Karakteristik Ketahanan |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **1** | **`stateless-api`** | **~630 RPS** | 429,6 ms (pada 630 RPS) | **91,89%** | **Sangat Unggul:** Mampu melayani beban linier hingga 630 RPS dengan serapan Goodput sangat tinggi (223.385 transaksi sukses). Antrean drain bersih dalam 1 detik. |
| **2** | **`microservices`** | **~348 RPS** | 816,9 ms (pada 348 RPS) | **59,81%** | **Tangguh Menengah:** Sangat stabil pada beban moderat (100% sukses pada 100 RPS steady). Mulai jenuh pada ~348 RPS akibat overhead hop proxy Linkerd. |
| **3** | **`cpu-bound`** | **~56,8 RPS** | 5.001 ms (*Timeout Ceiling*) | **12,50%** | **Sangat Rentan:** Tercekik ketat oleh kuota CPU 0,5 core. Mengalami 213.308 kegagalan timeout pada ramp 800 RPS dan 53,2% kegagalan pada 100 RPS steady. Antrean bersih dalam 5 detik. |

---

## 9. Pelajaran Rekayasa untuk Bisnis & Produksi

1. **Validasi Model Pengujian Terbuka (Open-Loop):**  
   Pengujian performa sistem cloud wajib menggunakan generator open-loop dengan batas waktu ketat sejak jadwal kedatangan. Pengujian closed-loop/thread-pool memberikan "rasa aman palsu" dengan success rate 99% semu.
2. **Pentingnya Mekanisme *Fail-Fast & Load Shedding* di Pintu Gerbang (Ingress):**  
   Pada `cpu-bound`, membiarkan 213.000 penonton menunggu selama 5 detik sebelum membatalkannya adalah pemborosan sumber daya server yang sangat besar. Dengan menerapkan `limit_req ... nodelay` di Ingress NGINX, server dapat **menolak kelebihan beban seketika dalam tempo $< 1\text{ ms}$ (HTTP 429)**, sehingga pelanggan tidak digantung dan server tidak tersedak.
3. **Penyetelan Kuota CPU Kubernetes:**  
   Batas kuota 500m ($0,5$ core) mutlak tidak memadai untuk beban produksi komputasi di atas 50 RPS. Diperlukan penambahan alokasi vCPU minimal 2–4 core atau penerapan *Horizontal Pod Autoscaler* (HPA) otomatis.
