# Resume Analisis Cloud Dynamics (Dataset Ali - res-ali): Penjelasan Sederhana untuk Orang Awam

Dokumen ini menyajikan ringkasan hasil uji performa sistem komputasi awan (*Cloud Dynamics Empirical Analysis*) dari notebook [`cloud_dynamics_empirical_analysis_ali.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_ali.ipynb) berbasis data pengukuran riil pada direktori `cloud-dynamics-experiments/res-ali/`.

Seluruh penjelasan disusun menggunakan bahasa populer, analogi kehidupan sehari-hari, dan grafik visual agar mudah dipahami oleh pengambil keputusan, mahasiswa, atau masyarakat umum tanpa latar belakang teknis yang mendalam.

---

## 1. Analogi Dasar: Apa itu Goodput dan Mengapa Lebih Penting dari Throughput?

Bayangkan sebuah **Dapur Restoran Cepat Saji yang Melayani Pesanan Ojek Online**:

```text
[Pesanan Masuk di Aplikasi (Offered Load)] ===> [Pesanan Diproses Dapur (Throughput)] ===> [Makanan Diterima Pembeli (Goodput)]
       (200 pesanan per detik)                          (200 pesanan diproses)                     (Hanya 57 porsi sukses!)
                                                                                                  [Pesanan menumpuk di antrean
                                                                                                   hingga nyaris batas timeout!]
```

1. **Beban yang Diminta (*Offered Load* / `target_rps`):**  
   Berapa banyak pesanan yang dikirimkan oleh ribuan pengguna aplikasi secara serentak per detik.
2. **Kapasitas Proses Lalu Lintas (*Throughput* / `achieved_rps`):**  
   Berapa banyak total pesanan yang diterima dan sedang sibuk dimasak oleh wajan dapur per detik (termasuk pesanan yang tertunda, salah saji, atau basi).
3. **Pekerjaan Sukses Produktif (*Goodput* / `success`):**  
   **Ini adalah metrik terpenting dalam industri digital!** Berapa banyak makanan yang **benar-benar matang tepat waktu, disajikan dengan selamat, dan dinikmati pembeli tanpa komplain atau pembatalan**.

> **Pelajaran Kunci:**  
> Dapur yang wajannya mengepul dan kokinya berkeringat (Throughput tinggi) belum tentu sukses memuaskan pelanggan. Jika pesanan menumpuk berjam-jam dan pelanggan membatalkan pesanan, maka jerih payah komputasi tersebut sia-sia. **Goodput adalah cerminan kepuasan pengguna riil.**

---

## 2. Mengenal 3 Karakter Aplikasi yang Diuji di Kluster Kubernetes

Riset ini menguji 3 jenis aplikasi kontainer dengan karakteristik arsitektur yang sangat berbeda di atas kluster Kubernetes Bare-Metal:

1. **`stateless-api` (Si Kasir Cekatan):**  
   Pekerjaannya sangat ringan (seperti kasir stempel tiket parkir otomatis). Memproses data secara asinkronus (*non-blocking*), hemat daya komputasi, dan langsung selesai dalam hitungan seperseribu detik.
2. **`microservices` (Restoran Berjaringan dengan Pelayan Khusus):**  
   Aplikasi modular yang membagi tugas antara penerima tamu, pengolah pesanan, dan basis data, yang saling terhubung melalui lapisan *service mesh* Linkerd. Komunikasi terkoordinasi rapi meski memiliki sedikit overhead jejaring.
3. **`cpu-bound` (Koki Peracik Bumbu Enkripsi Rumit):**  
   Mengerjakan kalkulasi komputasi matematika dan enkripsi yang sangat menguras tenaga prosesor. Koki ini dibatasi aturan ketat oleh sistem: **hanya boleh menggunakan kuota 0,5 inti CPU (500m CPU limit)**.

---

## 3. Fakta Empiris di Balik 3 Skenario Pengujian Beban

Pengujian di `res-ali` mengevaluasi sistem pada 3 skenario beban terukur:

### Skenario 1: Beban Santai & Teratur Sehari-hari (`constant`)
Pelanggan datang secara stabil dan teratur dengan kecepatan **25 pesanan per detik** selama 30 detik.

![Uji Beban Konstan Ali](../outputs/ali/figures/01_constant_scenario_comparison.png)

* **Hasil Pengamatan Nyata:**  
  - Seluruh aplikasi (`stateless-api`, `microservices`, dan `cpu-bound`) mampu menyajikan pesanan 100% sempurna dengan Goodput stabil di 25 pesanan/detik.
  - **Perbedaan Latensi (Waktu Tunggu Pelanggan):**  
    - `stateless-api`: Sangat kilat, waktu tunggu rata-rata hanya **10.7 milidetik**!
    - `microservices`: Waktu tunggu rata-rata **16.2 milidetik** (ada jeda koordinasi service mesh).
    - `cpu-bound`: Membutuhkan waktu tunggu **71.8 milidetik** (hampir 7x lebih lama dibanding kasir cekatan) karena prosesor harus mengunyah kalkulasi matematis.

---

### Skenario 2: Beban Jam Sibuk yang Merangkak Naik (`ramp`)
Beban dinaikkan perlahan seperti gelombang jam pulang kerja, dari **10 pesanan/detik merangkak naik hingga 200 pesanan/detik** selama 10 menit (600 detik).

![Uji Kenaikan Beban Bertahap Ramp Ali](../outputs/ali/figures/02_ramp_scenario_comparison.png)

* **Fenomena Kritis pada `cpu-bound` (Si Koki Berat):**  
  - Perhatikan grafik tengah di atas! Ketika pesanan masih di bawah 50 pesanan/detik, koki masih mampu melayani.
  - Namun begitu pesanan menyentuh **~57 hingga 64 pesanan/detik**, koki kehabisan nafas. Utilisasi CPU menyentuh batas limit 0.5 core ($100\%$ kuota CPU).
* **Terjadinya Efek "Tongkat Hoki" (*Hockey-Stick Latency*):**  
  - Karena pesanan terus berdatangan hingga 200 pesanan/detik sementara koki hanya sanggup memasak 56 porsi per detik, pesanan menumpuk di antrean memori.
  - Waktu tunggu pelanggan melonjak eksponensial dari **20 milidetik melesat ke 1.275 milidetik, lalu tembus ke 4.707 milidetik (hampir 5 detik)**!
* **Ketangguhan `stateless-api` dan `microservices`:**  
  - Kedua arsitektur ini dengan tenang melayani hingga 200 pesanan/detik tanpa kendala.
  - Tingkat keberhasilan (*Delivery Ratio*) mencapai **100.00%**, dengan latensi tetap stabil di bawah **120 milidetik** dan CPU di bawah 0.37 core.

---

### Skenario 3: Serbuan Kilat Diskon Dadakan (`burst`)
Sistem berjalan santai pada 10 pesanan/detik, lalu tiba-tiba **diserbu lonjakan ekstrem 150 pesanan/detik** selama 2 menit penuh (detik ke-180 hingga 300), lalu kembali sepi.

![Uji Guncangan Kilat Burst Ali](../outputs/ali/figures/03_burst_scenario_comparison.png)

* **Daya Serap Lonjakan (*Surge Capacity*):**  
  - `stateless-api` dan `microservices` menyerap lonjakan 150 pesanan/detik seketika tanpa keluhan. Waktu pemulihan (*recovery time*) mereka adalah **0 detik (langsung pulih seketika)**.
  - Sebaliknya, `cpu-bound` langsung mengalami kelumpuhan parsial:
    - Goodput yang berhasil diselesaikan **mentok di angka ~56.8 pesanan/detik**.
    - Waktu tunggu pelanggan melonjak **208 kali lipat** dari baseline 22.5 ms melonjak tajam ke **4.677,6 milidetik**!
    - Sebanyak **10 transaksi mengalami kegagalan (*timeout*)** karena waktu pemrosesan menyentuh batas toleransi sabar 5.0 detik.

---

## 4. Titik Jenuh (*Knee of Saturation*): Kapan Kapasitas Mulai Kolaps?

Bayangkan sebuah **Jalan Tol dengan 1 Gerbang Gardu Tiket**:

![Titik Jenuh Kapasitas Ali](../outputs/ali/figures/04_knee_of_saturation_curves.png)

1. **Kondisi Jalan Lancar:**  
   Selama mobil yang datang per menit lebih sedikit dari kemampuan petugas tiket melayani, seluruh mobil meluncur lancar tanpa hambatan (kurva latensi mendatar di grafik atas).
2. **Titik Tekukan Jenuh (*The Knee*):**  
   Begitu mobil yang datang melampaui kapasitas petugas loket (pada `cpu-bound` terjadi di angka **~64.5 RPS**), antrean mobil mulai mengular ke belakang.
3. **Macet Total & Penumpukan Antrean:**  
   Memaksa mengirim 100, 150, atau 200 pesanan/detik ke `cpu-bound` tidak akan menambah jumlah mobil yang keluar dari gerbang tol. Pada grafik bawah, garis Goodput mendatar (*Goodput Plateau*) di angka **54–57 RPS**. Penambahan beban hanya memperpanjang antrean dan membuang waktu tunggu pengguna.

---

## 5. Tiga Serangkai: Jurang Pemborosan Energi Komputasi (*Saturation Gap*)

Grafik berikut membedah hubungan antara **Offered Load** (garis putus-putus hitam), **Throughput** (garis oranye), dan **Goodput** (garis tebal berwarna):

![Tiga Serangkai Goodput Ali](../outputs/ali/figures/05_goodput_triad_and_fulfillment.png)

* **Jurang Penumpukan Antrean (*Saturation / Queueing Gap*):**  
  Pada grafik tengah (`cpu-bound`), area berbayang merah adalah **jurang kerugian komputasi**.
  - Garis hitam (beban yang diminta client) naik tinggi hingga 200 RPS.
  - Namun garis merah (Goodput aktual yang berhasil disajikan) tertahan di bawah 57 RPS.
  - Seluruh area di antara kedua garis tersebut mencerminkan puluhan ribu request yang tertahan di antrean sistem dan membebani server secara tidak produktif.
* **Perbandingan dengan `stateless-api` dan `microservices`:**  
  Pada kedua aplikasi lainnya, garis beban yang diminta dan garis Goodput riil berimpit sempurna dari detik awal hingga akhir (tidak ada jurang saturasi).

---

## 6. Dinamika Antrean Backpressure & Fase Pengurasan (*Drain Phase*)

Salah satu fenomena paling menarik dalam pengujian ini adalah: **Mengapa server masih sangat sibuk bekerja ketika pelanggan sudah selesai memesan?**

![Dinamika Antrean dan Pengurasan Ali](../outputs/ali/figures/06_queue_backpressure_and_drain_dynamics.png)

1. **Penumpukan Antrean Riil (*In-Flight Queue Backlog*):**  
   Selama lonjakan burst 150 RPS berlangsung (detik ke-180 hingga 300), `cpu-bound` menerima 150 request/detik tetapi hanya mampu menyelesaikan 57 request/detik. Selisih ~93 request per detik masuk ke dalam antrean memori.
   - Pada detik ke-300, akumulasi antrean mencapai puncak tertinggi: **11.168 pesanan mengantre di memori (*in-flight*)**!
2. **Fase Pengurasan (*Drain Phase*):**  
   Pada detik ke-301, lonjakan selesai dan beban client turun kembali ke 10 pesanan/detik.
   - Apakah server langsung santai? **Tidak!**
   - Server `cpu-bound` harus terus bekerja keras pada kecepatan penuh (~57 RPS) selama **170 detik (hampir 3 menit)** hanya untuk menguras tumpukan 11.000 pesanan yang tertinggal dari fase lonjakan sebelumnya!

---

## 7. Rangkuman Pemeringkatan Kinerja Goodput Antar-Arsitektur

Berdasarkan seluruh hasil pengujian empiris pada dataset Ali (`res-ali`), berikut adalah pemeringkatan ketahanan sistem:

| Peringkat | Arsitektur Aplikasi | Kapasitas Puncak Goodput | Latensi Beban Puncak | Delivery Ratio (%) | Success Rate (%) | Kesimpulan dalam Bahasa Awam |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 🥇 **1** | **`stateless-api`** | **> 200 RPS** | **22.4 ms** | **100.00%** | **100.00%** | **Juara Efisiensi:** Model I/O non-blocking sangat gesit. Mampu melayani 200 pesanan/detik dengan konsumsi CPU sangat hemat (< 0.21 core), bebas macet. |
| 🥈 **2** | **`microservices`** | **> 200 RPS** | **25.6 ms** | **100.00%** | **100.00%** | **Ketangguhan Berjaringan:** Arsitektur modular multi-hop mempertahankan rasio sukses 100% sempurna dengan overhead moderat (~0.36 core) pada service mesh. |
| 🥉 **3** | **`cpu-bound`** | **~56.8 RPS** | **4,677.6 ms** | **99.63%** | **99.63%** | **Terbatas Kuota CPU:** Mentok pada kuota CPU 0.5 core. Menghasilkan penumpukan antrean masif saat lonjakan beban dan nyaris memicu gagal massal akibat timeout. |

---

## 8. Pelajaran Berharga untuk Rekayasa Sistem di Industri

1. **Jangan Jadikan Utilisasi CPU Sebagai Satu-Satunya Pemicu Autoscaling (HPA):**  
   Pada arsitektur non-blocking seperti `stateless-api`, CPU hanya terpakai 20% padahal sistem sudah melayani 200 RPS. Sebaliknya, pada `cpu-bound`, CPU sudah 100% pada 57 RPS. Pemicu penambahan server otomatis (*autoscaler*) sebaiknya memantau **Goodput Fulfillment Ratio** atau jumlah antrean request aktif (*in-flight requests*).
2. **Sinkronisasi Waktu Toleransi (Timeout) dan Kedalaman Antrean:**  
   Batas sabar pengguna aplikasi (client timeout 5.0 detik) harus diselaraskan dengan batas antrean server. Jika server membiarkan pesanan mengantre lebih dari 5 detik, server membuang-buang listrik dan CPU untuk memproses pesanan basi yang sudah ditinggalkan pelanggannya.
