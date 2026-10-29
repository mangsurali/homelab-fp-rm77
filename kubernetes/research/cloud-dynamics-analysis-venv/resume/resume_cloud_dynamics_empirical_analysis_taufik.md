# Resume Analisis Cloud Dynamics (Dataset Taufik): Penjelasan Sederhana untuk Orang Awam

Dokumen ini menyajikan ringkasan hasil uji performa sistem komputasi awan (*Cloud Dynamics Empirical Analysis*) dari notebook [`cloud_dynamics_empirical_analysis_taufik.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_taufik.ipynb) berbasis data riil pada folder `res-taufik/`. Seluruh penjelasan disajikan dengan bahasa awam dan analogi nyata agar mudah dipahami oleh pengambil keputusan, mahasiswa, atau masyarakat umum.

---

## 1. Analogi Dasar: Apa itu Goodput dan Mengapa Lebih Penting dari Throughput?

Bayangkan sebuah **Dapur Restoran Online (Ojek Makanan)**:

```text
[Pesanan Masuk di Aplikasi (Offered Load)] ===> [Pesanan Tercetak di Dapur (Throughput)] ===> [Makanan Diterima Pembeli (Goodput)]
       (200 pesanan per detik)                           (200 pesanan diproses)                      (Hanya 52 porsi sampai!)
                                                                                                    [148 pesanan dibatalkan pembeli
                                                                                                     karena lewat batas 5 detik!]
```

* **Beban Masuk (*Offered Load*):** Berapa banyak pesanan yang dibuat oleh pelanggan per detik.
* **Throughput:** Berapa banyak pesanan yang sedang digoreng atau dicoba dimasak oleh dapur.
* **Goodput (Transaksi Sukses Sejati):** Berapa banyak makanan yang **benar-benar matang tepat waktu dan sampai ke tangan pembeli dengan selamat**.

> **Fakta Kritis di Dataset Taufik:**  
> Pada pengujian dataset Taufik, kita melihat fenomena dramatis: server tampak sangat sibuk memproses ratusan pesanan (Throughput tinggi), tetapi sebagian besar pelanggan sudah keburu marah dan membatalkan pesanan karena menunggu lebih dari 5 detik! Akibatnya, pesanan yang sukses (Goodput) anjlok drastis.

---

## 2. Mengenal 3 Karakter Aplikasi yang Diuji

1. **`stateless-api` (Kasir Serba Cepat):**  
   Hanya memvalidasi data ringan. Cepat melayani, hemat daya komputasi.
2. **`microservices` (Tim Dapur Terpadu: Pelayan Depan + Koki Belakang):**  
   Terdiri dari **`frontend`** (pelayan penerima tamu di depan) dan **`backend`** (dapur pengolah di belakang). Dataset Taufik secara spesifik mencatat kinerja kedua bagian ini secara terpisah!
3. **`cpu-bound` (Koki Spesialis Rumit):**  
   Mengerjakan kalkulasi enkripsi/matematika berat. Dibatasi oleh aturan ketat: hanya boleh memakai **0,5 inti prosesor (500m CPU limit)**.

---

## 3. Fenomena di Balik 3 Skenario Pengujian

### Skenario 1: Beban Konstan Sehari-hari (`constant`)
Pelanggan datang stabil dan teratur dengan kecepatan **25 pesanan per detik**.

![Uji Beban Konstan Taufik](../outputs/taufik/figures/01_constant_scenario_comparison.png)

* **Hasil Pengamatan:**  
  - Seluruh aplikasi sukses menyajikan 25 porsi/detik tanpa ada kegagalan (100% Goodput).
  - Namun, waktu tunggu (*latensi*) sudah memperlihatkan perbedaan karakter:
    - `stateless-api`: pelanggan hanya menunggu **69.9 milidetik**.
    - `microservices`: pelanggan menunggu **325.2 milidetik** (karena pelayan depan harus koordinasi dengan dapur belakang).
    - `cpu-bound`: pelanggan harus menunggu **940.8 milidetik (hampir 1 detik)** meskipun bebannya masih tergolong ringan.

---

### Skenario 2: Beban Bertambah Perlahan Hingga Ekstrem (`ramp`)
Beban dinaikkan perlahan seperti jam sibuk, dari **10 pesanan/detik merangkak naik hingga 200 pesanan/detik** selama 10 menit.

![Uji Kenaikan Beban Ramp Taufik](../outputs/taufik/figures/02_ramp_scenario_comparison.png)

* **Tragedi Saturasi pada `cpu-bound`:**  
  - Begitu beban melampaui **52 pesanan/detik**, koki `cpu-bound` kehabisan tenaga (menyentuh limit 0.5 core).
  - Pesanan yang datang terus menumpuk di antrean. Waktu tunggu pelanggan melonjak gila-gilaan dari **0,4 detik menjadi 8,2 detik**!
* **Banjir Pembatalan (*Massive Failure*):**  
  Karena batas sabar pelanggan (*client timeout*) adalah **5.0 detik**, maka setiap pesanan yang menunggu lebih dari 5 detik otomatis gagal (*Error 504 / Timeout*).
  - Dari total ~60.000 pesanan yang dikirim, sebanyak **55.853 pesanan GAGAL**!
  - Goodput Delivery Ratio anjlok hingga tinggal **42.9%**!
* **Kemenangan `stateless-api` dan `microservices`:**  
  Kedua aplikasi ini tetap tangguh melayani hingga 200 pesanan/detik dengan tingkat keberhasilan di atas **99.8%**.

---

### Skenario 3: Serbuan Diskon Kilat Mendadak (`burst`)
Dari kondisi santai (10 pesanan/detik), tiba-tiba **diserbu 150 pesanan/detik** selama 2 menit penuh, lalu kembali ke 10 pesanan/detik.

![Uji Serbuan Kilat Burst Taufik](../outputs/taufik/figures/03_burst_scenario_comparison.png)

* **Perbedaan Ketahanan yang Mencolok:**
  - `stateless-api` dan `microservices` mampu menyerap serbuan kilat dengan sangat baik: Goodput langsung melompat melayani 148 porsi/detik, dan waktu pemulihan (*recovery time*) hanya butuh **kurang dari 1 detik**!
  - Sebaliknya, `cpu-bound` langsung **lumpuh**:
    - Waktu tunggu melonjak **115 kali lipat** hingga menyentuh **7.909 milidetik (hampir 8 detik)**!
    - Laju Goodput yang berhasil disajikan **anjlok ke hanya 12.4 pesanan/detik** (dapur macet total).
    - Terjadi **10.345 pesanan gagal** selama 2 menit lonjakan tersebut.

---

## 4. Titik Jenuh (*Knee of Saturation*): Kapan Sistem Mulai Kolaps?

![Titik Jenuh Kapasitas Taufik](../outputs/taufik/figures/04_knee_of_saturation_curves.png)

1. **Efek Tongkat Hoki (*Hockey-Stick Curve*):**  
   Perhatikan kurva merah di grafik atas. Pada awalnya kurva bergerak landai. Namun tepat di angka **~52 RPS**, kurva tiba-tiba menekuk tajam ke atas seperti ujung tongkat hoki.
2. **Goodput Plateau (Mentok):**  
   Pada grafik bawah, garis merah mendatar di angka ~52 pesanan/detik. Memaksa mengirim 100, 150, atau 200 pesanan/detik ke `cpu-bound` adalah kesia-siaan, karena kapasitas fisiknya sudah mentok.

---

## 5. Tiga Serangkai: Jurang Pemborosan Energi Komputasi

![Tiga Serangkai Goodput Taufik](../outputs/taufik/figures/05_goodput_triumvirate_and_ratios.png)

* **Jurang Kegagalan (*Queueing / Saturation Gap*):**  
  Pada grafik kiri atas, area berbayang merah adalah **kerugian nyata**. Garis oranye (pesanan yang dicoba diproses) berjalan tinggi, tetapi garis merah tebal (Goodput nyata) terpuruk di bawah. Ini membuktikan bahwa prosesor bekerja keras membuang-buang listrik untuk memproses pesanan yang pada akhirnya dibatalkan oleh pengguna.
* **Fulfillment Ratio (Kemampuan Memenuhi Permintaan):**  
  Pada grafik bawah, `microservices` mampu mempertahankan pemenuhan beban di atas **90–100%**. Sementara `cpu-bound` anjlok hingga di bawah **20%** saat beban tinggi.

---

## 6. Dinamika Antrean Backpressure: Mengapa Sistem Bisa Tenggelam?

![Dinamika Antrean Taufik](../outputs/taufik/figures/06_queue_backpressure_and_drain_dynamics.png)

### Mengapa di Dataset Taufik Terjadi Puluhan Ribu Kegagalan, Sedangkan di Pengujian Lain Tidak?
Ini adalah salah satu wawasan paling berharga dari riset ini:
1. **Di Bawah 5 Detik = Selamat:**  
   Jika antrean masih bisa diselesaikan dalam 4,9 detik, pelanggan masih sabar dan transaksi dicatat sukses.
2. **Di Atas 5 Detik = Bencana:**  
   Di dataset Taufik, antrean pesanan menumpuk begitu masif hingga waktu tunggu tembus ke angka **7 hingga 8 detik**. Begitu jarum jam melewati 5.0 detik, sistem client otomatis memutus koneksi (*timeout error*).
3. **Pelajaran untuk Industri:**  
   Tanpa sistem pembatas antrean (*rate limiting* / penolakan dini) atau penambahan server otomatis (*Autoscaling / HPA*), penumpukan antrean akan membuat server "tenggelam" dalam tumpukan pekerjaan basi.

---

## 7. Rangkuman Pemeringkatan Kinerja

| Peringkat | Aplikasi | Kapasitas Puncak Goodput | Latensi Terburuk | Tingkat Keberhasilan | Kesimpulan Bahasa Awam |
| :---: | :--- | :---: | :---: | :---: | :--- |
| 🥇 **1** | **`stateless-api`** | **> 200 RPS** | **5.85 detik** | **99.96%** | **Juara Bertahan:** Sangat efisien, hampir seluruh pesanan selamat tanpa error meski dihantam beban 200 RPS. |
| 🥈 **2** | **`microservices`** | **~190 RPS** | **6.04 detik** | **99.86%** | **Kerja Tim Hebat:** Frontend menanggung beban lebih berat (0.54 core) dibanding backend (0.33 core), namun sukses mengantar 99.86% transaksi. |
| 🥉 **3** | **`cpu-bound`** | **~52 RPS** | **8.28 detik** | **42.92%** | **Kolaps Total:** Terjebak batas prosesor 0.5 core, memicu penumpukan antrean ekstrem dan puluhan ribu pesanan gagal. |
