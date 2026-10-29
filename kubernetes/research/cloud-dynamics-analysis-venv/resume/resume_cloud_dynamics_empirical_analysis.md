# Resume Analisis Cloud Dynamics (Dataset res-fix): Penjelasan Sederhana untuk Orang Awam

Dokumen ini menyajikan ringkasan hasil uji performa sistem komputasi awan (*Cloud Dynamics Empirical Analysis*) dari notebook [`cloud_dynamics_empirical_analysis.ipynb`](../notebooks/cloud_dynamics_empirical_analysis.ipynb). Seluruh penjelasan disajikan menggunakan bahasa awam dan analogi kehidupan sehari-hari agar mudah dipahami oleh siapa saja tanpa latar belakang teknis yang mendalam.

---

## 1. Analogi Dasar: Memahami "Goodput", "Throughput", dan "Beban Masuk"

Bayangkan sebuah **Restoran Cepat Saji**:

```text
[Beban Pelanggan (Offered Load)]   ===>   [Pesanan Masuk Dapur (Throughput)]   ===>   [Makanan Sukses Disajikan (Goodput)]
  (100 orang datang memesan)                (100 pesanan dicatat kasir)                 (98 porsi matang & dimakan)
                                                                                         [2 porsi gosong/dibatalkan]
```

1. **Beban Masuk (*Offered Load* / `target_rps` / `sent`):**  
   Berapa banyak pesanan yang dikirim oleh pelanggan ke kasir per detik.
2. **Kapasitas Lalu Lintas (*Throughput* / `achieved_rps`):**  
   Berapa banyak total pesanan yang diterima dan sedang ditangani oleh dapur restoran per detik (termasuk pesanan yang akhirnya gagal, gosong, atau salah masak).
3. **Pekerjaan Sukses Nyata (*Goodput* / `success`):**  
   **Ini adalah metrik terpenting!** Berapa banyak makanan yang **benar-benar matang sempurna, disajikan dengan selamat, dan dinikmati pembeli tanpa komplain**.

> **Pelajaran Penting:**  
> Dapur yang sibuk bukan berarti sukses. Jika dapur memproses 100 pesanan tapi 50 di antaranya gosong (error), maka Throughput-nya 100, tetapi **Goodput-nya hanya 50**. Goodput adalah tolak ukur kepuasan pelanggan yang sesungguhnya.

---

## 2. Mengenal 3 Karakter Aplikasi yang Diuji

Dalam pengujian ini, kita menguji 3 jenis "karyawan/dapur" dengan sifat yang berbeda:

1. **`stateless-api` (Si Kasir Cekatan):**  
   Pekerjaannya sangat ringan, seperti kasir yang hanya mengecek tiket masuk atau stempel karcis. Begitu ada orang datang, dalam hitungan milidetik langsung selesai.
2. **`microservices` (Restoran Berantai / Banyak Meja Kerja):**  
   Pekerjaannya melibatkan beberapa divisi (bagian penerima pesanan, bagian koki, bagian saus). Karena harus oper-operan antar meja, butuh waktu sedikit lebih lama, namun organisasinya rapi.
3. **`cpu-bound` (Koki Peracik Bumbu Rumit):**  
   Pekerjaannya sangat berat dan memeras otak (menghitung matematika rumit). Setiap pesanan butuh waktu mengaduk dan memasak yang lama. Koki ini punya batas tenaga maksimal yang tidak bisa dipaksa melampaui batas fisiknya.

---

## 3. Fenomena di Balik 3 Skenario Pengujian

### Skenario 1: Beban Santai & Teratur (`constant`)
Pada pengujian ini, pelanggan datang santai dengan kecepatan konstan: **25 pesanan per detik** selama 30 detik.

![Uji Beban Santai](../outputs/figures/01_constant_scenario_comparison.png)

* **Apa yang terjadi?**  
  Seluruh jenis aplikasi mampu melayani dengan sempurna. Laju Goodput persis 25 transaksi per detik.
* **Perbedaan Waktu Tunggu (Latensi):**  
  - `stateless-api` sangat cepat, pelanggan hanya menunggu sekitar **14 milidetik**.
  - `microservices` membutuhkan sekitar **29 milidetik** karena ada jeda oper-operan internal.
  - `cpu-bound` membutuhkan waktu sekitar **29 milidetik** dan menggunakan tenaga CPU 7x lebih banyak dibanding kasir cekatan.

---

### Skenario 2: Beban Jam Makan Siang yang Merangkak Naik (`ramp`)
Pelanggan datang perlahan dari sepi (10 pesanan/detik) hingga membludak ramai (**200 pesanan/detik**) selama 10 menit nonstop.

![Uji Kenaikan Beban Bertahap](../outputs/figures/02_ramp_scenario_comparison.png)

* **Fenomena Menarik pada `cpu-bound` (Si Koki Berat):**  
  Perhatikan grafik merah di atas! Saat pesanan di bawah 56 pesanan/detik, koki masih sanggup. Namun begitu pesanan menembus angka **56 pesanan/detik**, koki mencapai batas fisik tenaganya (100% CPU Limit).
* **Terjadinya Efek "Tongkat Hoki" (*Hockey-Stick Latency*):**  
  Karena pesanan terus berdatangan hingga 200 pesanan/detik sementara koki hanya bisa menyelesaikan 56 per detik, pesanan menumpuk di antrean! Waktu tunggu melonjak drastis dari **20 milidetik menjadi 4.700 milidetik (hampir 5 detik)**!
* **Ketangguhan `stateless-api` & `microservices`:**  
  Kedua aplikasi ini dengan tenang melayani hingga 200 pesanan/detik tanpa hambatan berarti (latensi di bawah 0.3 detik).

---

### Skenario 3: Guncangan Diskon Kilat Tiba-Tiba (`burst`)
Sistem berjalan santai pada 10 pesanan/detik, tiba-tiba **diserbu lonjakan 150 pesanan/detik** selama 2 menit, lalu kembali sepi.

![Uji Guncangan Kilat](../outputs/figures/03_burst_scenario_comparison.png)

* **Fenomena Guncangan (*Overshoot*):**  
  - Begitu diserbu 150 pesanan, `stateless-api` dan `microservices` menyerap lonjakan tersebut seketika dan langsung menyajikan 150 Goodput per detik.
  - Sebaliknya, `cpu-bound` langsung kewalahan! Waktu tunggu melonjak **66 kali lipat** hingga menyentuh **5.051 milidetik**.
* **Waktu Pemulihan (*Recovery Time*):**  
  Setelah serbuan berhenti, `stateless-api` dan `microservices` pulih ke kondisi normal dalam sekejap (**kurang dari 1 detik**). Sementara `cpu-bound` butuh waktu **275 detik (lebih dari 4,5 menit)** hanya untuk membereskan sisa antrean yang menumpuk!

---

## 4. Mengapa Terjadi Titik Jenuh (*Knee of Saturation*)?

Bayangkan jalan tol dengan 1 gerbang tol:

![Titik Jenuh Kapasitas](../outputs/figures/04_knee_of_saturation_curves.png)

1. **Jalan Lancar:** Selama kendaraan yang masuk lebih sedikit dari kecepatan mesin tiket gerbang tol, semua mobil meluncur tanpa hambatan (garis mendatar).
2. **Titik Jenuh (*Knee*):** Begitu mobil yang datang melampaui kecepatan mesin tiket, antrean mulai mengular.
3. **Macet Total:** Menambah mobil ke jalan tol tidak akan membuat mobil keluar lebih cepat dari gerbang tol. Mobil hanya akan diam mengantre dan waktu tempuh melonjak eksponensial.
4. **Data Riil:** Pada `cpu-bound`, titik jenuh terjadi di angka **~56 RPS**. Di atas angka ini, Goodput tidak bisa bertambah lagi (mendatar) dan latensi meledak.

---

## 5. Tiga Serangkai: Perbedaan Nyata Antara Beban Masuk, Throughput, dan Goodput

Grafik di bawah ini memperlihatkan celah (*gap*) kerugian saat sistem mengalami saturasi:

![Tiga Serangkai Goodput](../outputs/figures/05_goodput_triumvirate_and_ratios.png)

* **Area Abu-Abu (Celah Antrean/Saturasi):**  
  Pada grafik kiri atas (`cpu-bound`), ada jarak lebar antara garis putus-putus (beban yang diminta) dengan garis merah (Goodput riil). Celah ini adalah pesanan yang terpaksa mengantre lama di memori server.
* **Persentase Pemenuhan Beban (*Fulfillment Ratio*):**  
  Pada `stateless-api` dan `microservices`, sistem mampu memenuhi **100%** permintaan pelanggan sepanjang waktu. Pada `cpu-bound`, kemampuannya anjlok hingga tinggal **25%** saat beban puncak.

---

## 6. Dinamika Antrean Backpressure dan Fenomena Cuci Piring di Akhir (*The Drain Phase*)

![Dinamika Antrean dan Drain](../outputs/figures/06_queue_backpressure_and_drain_dynamics.png)

### Mengapa Pesanan Tidak Langsung Ditolak? (Paradoks Batas Waktu 5 Detik)
Banyak orang heran: *"Jika pesanan datang 150 tapi kemampuan hanya 56, mengapa pelanggan tidak langsung mendapat pesan Error?"*

Jawabannya adalah **Sistem Antrean Bertingkat**:
1. Pelanggan menggunakan aplikasi dengan batas sabar (timeout) **5.0 detik**.
2. Komputer server tidak langsung menolak pesanan, melainkan menampungnya di dalam antrean memori jaringan (*socket buffer*).
3. Karena server berhasil memasak dan membalas pesanan dalam waktu **4,5 hingga 4,9 detik** (tepat sebelum batas 5 detik habis), pesanan tersebut **tetap dianggap sukses (Goodput)**!

### Fenomena Fase Pengurasan (*Drain Phase*):
Ketika jam tes berakhir dan pelanggan sudah berhenti memesan (`sent = 0`), server **tidak langsung menganggur**. Server terus bekerja keras dengan kecepatan stabil 56 pesanan/detik selama bermenit-menit hingga ribuan pesanan yang mengantre tadi tuntas terselesaikan (seperti koki yang mencuci piring dan menyelesaikan sisa bon pesanan setelah restoran tutup).

---

## 7. Kesimpulan & Peringkat Ketahanan

| Peringkat | Aplikasi | Kapasitas Maksimal | Waktu Tunggu Beban Puncak | Tingkat Keberhasilan | Kesimpulan Bahasa Awam |
| :---: | :--- | :---: | :---: | :---: | :--- |
| 🥇 **1** | **`stateless-api`** | **> 200 RPS** | **0.09 detik** | **100.00%** | **Sangat Tangguh & Gesit:** Tidak ada tanda-tanda lelah pada beban tinggi, sangat hemat energi komputer. |
| 🥈 **2** | **`microservices`** | **~180 RPS** | **0.31 detik** | **100.00%** | **Tangguh & Terorganisir:** Sedikit lebih lambat karena koordinasi antar layanan, tapi pesanan tidak pernah gagal. |
| 🥉 **3** | **`cpu-bound`** | **~56 RPS** | **4.73 detik** | **99.56%** | **Cepat Lelah:** Tenaga prosesor habis di 56 pesanan/detik, menyebabkan antrean panjang mengular. |
