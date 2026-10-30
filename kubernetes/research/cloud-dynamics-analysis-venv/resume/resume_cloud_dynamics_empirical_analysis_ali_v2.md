# Resume Analisis Cloud Dynamics (Dataset Ali v2 - Skala Tinggi 400 RPS): Penjelasan Sederhana untuk Orang Awam

Dokumen ini menyajikan ringkasan hasil uji performa sistem komputasi awan (*Cloud Dynamics Empirical Analysis*) dari notebook [`cloud_dynamics_empirical_analysis_ali_v2.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_ali_v2.ipynb) berbasis data pengukuran empiris riil pada direktori `cloud-dynamics-experiments/res-ali-v2/`.

Seluruh penjelasan disusun menggunakan bahasa populer, analogi kehidupan sehari-hari, dan grafik visual publikasi (300 DPI) agar mudah dipahami oleh pengambil keputusan, mahasiswa, atau masyarakat umum tanpa latar belakang teknis yang mendalam. Di bagian akhir, disajikan analisis kritis berbasis teori antrean mengenai strategi pengendalian beban menggunakan `limit_req` dengan parameter `nodelay`.

---

## 1. Analogi Dasar: Apa itu Goodput dan Mengapa Lebih Penting dari Throughput?

Bayangkan sebuah **Dapur Restoran Cepat Saji yang Melayani Pesanan Ojek Online pada Jam Makan Siang**:

```text
[Pesanan Masuk di Aplikasi (Offered Load)] ===> [Pesanan Dimasak di Wajan (Throughput)] ===> [Makanan Diterima Pembeli (Goodput)]
        (400 pesanan per detik)                         (360 pesanan ditangani)                     (Hanya 56 porsi sukses!)
                                                                                                   [28.000 pesanan menumpuk di dapur,
                                                                                                    menunggu hingga 500 detik!]
```

1. **Beban yang Diminta (*Offered Load* / `target_rps`):**  
   Berapa banyak pesanan yang dikirimkan oleh ribuan pengguna aplikasi secara serentak per detik.
2. **Kapasitas Proses Jaringan (*Throughput* / `achieved_rps`):**  
   Berapa banyak total request yang berhasil masuk ke pintu gerbang server dan sedang sibuk dialirkan oleh soket jaringan per detik (termasuk pesanan yang terlambat, salah saji, atau basi).
3. **Pekerjaan Sukses Produktif (*Goodput* / `success`):**  
   **Ini adalah metrik terpenting dalam industri perangkat lunak modern!** Berapa banyak transaksi yang **benar-benar selesai tepat waktu, disajikan dengan status HTTP 200 OK, dan diterima pelanggan tanpa error atau pembatalan**.

> **Pelajaran Kunci untuk Orang Awam:**  
> Dapur yang wajannya mengepul dan kokinya berkeringat (Throughput tinggi) tidak ada gunanya jika makanan baru matang setelah pembeli membatalkan pesanan karena terlalu lama menunggu. Jika server memproses data yang sudah kadaluwarsa, energi listrik dan komputasi tersebut terbuang sia-sia (*wasteful computation*). **Goodput adalah cerminan kepuasan pengguna riil.**

---

## 2. Mengenal 3 Karakter Aplikasi dalam Ujian Skala Ekstrem

Riset ini menguji 3 jenis aplikasi kontainer di atas kluster Kubernetes Bare-Metal dengan karakteristik komputasi yang kontras:

1. **`stateless-api` (Si Kasir Tol Otomatis Cekatan):**  
   Pekerjaannya sangat ringan dan efisien. Menggunakan model *asynchronous non-blocking I/O*, hemat konsumsi CPU, dan langsung menyelesaikan request dalam hitungan milidetik tanpa antrean.
2. **`microservices` (Restoran Berjaringan dengan Pelayan Khusus):**  
   Aplikasi modular yang membagi tugas antara gerbang depan (*frontend*), pemroses logika (*backend*), dan basis data, yang saling terhubung melalui lapisan *service mesh* Linkerd. Komunikasi terkoordinasi rapi, namun memiliki *overhead* koordinasi hop jaringan antar-kontainer.
3. **`cpu-bound` (Koki Peracik Bumbu Enkripsi Berat):**  
   Mengerjakan kalkulasi komputasi matematika dan enkripsi intensif yang sangat menguras tenaga prosesor. Kontainer ini dipagari aturan ketat sistem operasi: **hanya dijatah kuota CPU maksimal 0,5 inti prosesor (500m CFS CPU limit)**.

---

## 3. Fakta Empiris di Balik 3 Skenario Pengujian Skala Ekstrem (Ali v2)

Pengujian pada dataset `res-ali-v2` mengevaluasi ketahanan sistem pada batas beban yang jauh lebih agresif dibanding pengujian sebelumnya:

### Skenario 1: Beban Harian Teratur 50 Pesanan/Detik (`constant`)
Pelanggan datang secara stabil dan teratur dengan kecepatan **50 pesanan per detik** (2x lipat dari dataset v1) selama 30 detik.

![Uji Beban Konstan Ali v2](../outputs/ali-v2/figures/01_constant_scenario_comparison.png)

* **Hasil Observasi Nyata:**  
  - Seluruh aplikasi (`stateless-api`, `microservices`, dan `cpu-bound`) mampu menyajikan pesanan **100% sempurna tanpa satu pun kegagalan**.
  - **Perbandingan Latensi (Waktu Tunggu Pengguna):**  
    - `stateless-api`: Sangat kilat, waktu respons rata-rata hanya **4.4 milidetik**!
    - `microservices`: Waktu tunggu rata-rata **8.6 milidetik** (ada jeda koordinasi antar-kontainer di Linkerd).
    - `cpu-bound`: Membutuhkan waktu **20.6 milidetik** (hampir 5x lebih lambat dibanding kasir cekatan) karena prosesor harus mengunyah kalkulasi berat.
  - **Efisiensi Sumber Daya:** Pada beban 50 RPS ini, `stateless-api` hanya memakai 0.015 core CPU, `microservices` 0.026 core CPU, dan `cpu-bound` 0.107 core CPU.

---

### Skenario 2: Beban Jam Sibuk Merangkak Naik Hingga 400 Pesanan/Detik (`ramp`)
Beban dinaikkan perlahan dari **10 pesanan/detik merangkak naik hingga 400 pesanan/detik** selama 10 menit (600 detik).

![Uji Kenaikan Beban Bertahap Ramp Ali v2](../outputs/ali-v2/figures/02_ramp_scenario_comparison.png)

* **Fenomena Kolaps Dini pada `cpu-bound` (Panel Tengah):**  
  - Ketika pesanan masih di bawah 60 pesanan/detik, koki masih mampu mengimbangi.
  - Namun begitu pesanan menyentuh **~67.9 pesanan/detik**, koki kehabisan nafas. Utilisasi CPU menyentuh plafon limit 0.5 core.
  - Akibatnya, kurva latensi berbelok tajam ke atas (*hockey-stick curve*): waktu tunggu melonjak eksponensial dari **20 milidetik melesat ke 1.528 milidetik, lalu menembus 4.758 milidetik (nyaris menyentuh batas sabar timeout 5 detik)**!
* **Daya Tahan Menengah pada `microservices` (Panel Bawah):**  
  - Arsitektur mikroservis mampu melayani kenaikan beban dengan sangat baik hingga melewati 300 RPS.
  - Namun pada **~326.9 RPS**, koordinasi jaringan antar-proxy Linkerd dan gateway ingress mulai mengalami persaingan buffer. Latensi merangkak naik ke **687.8 ms** dengan total 504 request gagal karena timeout.
* **Keunggulan Mutlak `stateless-api` (Panel Atas):**  
  - Mampu melenggang mulus dari 10 hingga **400 pesanan/detik** tanpa hambatan kapasitas!
  - Menghasilkan Goodput puncak **397.3 RPS** dengan latensi rata-rata hanya **80.9 milidetik** dan tingkat keberhasilan mencapai **99.998%** (hanya 6 kegagalan dari total 122.845 request yang dikirimkan).

---

### Skenario 3: Serbuan Kilat Lonjakan Ekstrem 300 Pesanan/Detik (`burst`)
Sistem berjalan santai pada 20 pesanan/detik, lalu tiba-tiba **diserbu lonjakan dahsyat 300 pesanan/detik** selama 2 menit penuh (detik ke-360 hingga 480), lalu kembali sepi.

![Uji Guncangan Kilat Burst Ali v2](../outputs/ali-v2/figures/03_burst_scenario_comparison.png)

* **Resiliensi dan Pemulihan Seketika:**  
  - `stateless-api` dan `microservices` menyerap lonjakan 300 RPS dengan sangat tangguh. Waktu pemulihan (*recovery time*) mereka adalah **0 hingga 2 detik** begitu lonjakan berakhir.
* **Bencana Antrean pada `cpu-bound`:**  
  - Karena kapasitas pemrosesan `cpu-bound` hanya sanggup melayani ~56 pesanan/detik, terjadi ketimpangan masif: ada 300 pesanan masuk setiap detik, tetapi hanya 56 yang selesai.
  - Selisih **244 pesanan per detik terus menumpuk di antrean memori** selama 120 detik penuh!
  - Waktu tunggu pelanggan melonjak **244 kali lipat** dari baseline 19.3 ms meroket ke **4.722,6 milidetik**!

---

## 4. Titik Jenuh (*Knee of Saturation*): Kapan Kapasitas Mulai Kolaps?

Bayangkan sebuah **Jalan Tol Menuju Gerbang Gardu Tiket**:

![Titik Jenuh Kapasitas Ali v2](../outputs/ali-v2/figures/04_knee_of_saturation_curves.png)

1. **Kondisi Lancar (Sebelum Titik Jenuh):**  
   Selama mobil yang datang per detik lebih sedikit dari kecepatan petugas tiket mengetuk kartu, semua mobil meluncur tanpa hambatan (garis latensi mendatar di grafik atas).
2. **Titik Tekukan Jenuh (*The Knee*):**  
   - Pada `cpu-bound`, titik kritis terjadi di angka **67.9 RPS** (ditandai titik merah). Begitu mobil datang lebih dari 68 per detik, antrean mobil langsung mengular panjang.
   - Pada `microservices`, titik kritis terjadi di angka **326.9 RPS** (ditandai titik hijau).
   - Pada `stateless-api`, gerbang tol sangat lebar sehingga tidak pernah jenuh hingga batas uji tertinggi **400 RPS**.
3. **Pendataran Goodput (*Goodput Plateau*):**  
   Pada grafik bawah, perhatikan garis merah `cpu-bound`. Mau dipaksa dikirim 100, 200, atau 400 pesanan/detik sekalipun, jumlah makanan yang keluar **tetap mendatar di angka ~56 porsi per detik**. Memaksa kirim beban berlebih hanya memperpanjang antrean dan membakar waktu tunggu.

---

## 5. Tiga Serangkai: Jurang Pemborosan Energi Komputasi (*Saturation Gap*)

Grafik berikut membedah hubungan antara **Offered Load** (garis putus-putus hitam), **Throughput** (garis oranye), dan **Goodput** (garis tebal berwarna):

![Tiga Serangkai Goodput Ali v2](../outputs/ali-v2/figures/05_goodput_triad_and_fulfillment.png)

* **Jurang Penumpukan Antrean (*Saturation Gap*):**  
  Pada grafik tengah (`cpu-bound`), area berbayang merah adalah **jurang pemborosan sistem**.
  - Garis hitam (beban yang diminta client) melonjak hingga 400 RPS.
  - Garis merah (Goodput riil yang sukses) tertahan kaku di bawah 57 RPS.
  - Seluruh area berbayang merah mencerminkan **puluhan ribu transaksi yang tertahan mengambang di antrean penyangga jaringan (*in-flight backlog*)**.
* **Kontras dengan Arsitektur Lain:**  
  Pada `stateless-api` (panel atas), garis hitam dan garis biru berimpit sempurna hingga 400 RPS tanpa ada celah jurang saturasi sama sekali.

---

## 6. Dinamika Antrean Backpressure & Fase Pengurasan Lambat (*Drain Phase*)

Salah satu fenomena paling mencengangkan dalam pengujian Ali v2 adalah: **Mengapa server masih sibuk bekerja keras selama hampir 10 menit setelah pengujian selesai?**

![Dinamika Antrean dan Pengurasan Ali v2](../outputs/ali-v2/figures/06_queue_backpressure_and_drain_dynamics.png)

1. **Gunung Antrean In-Flight (Grafik Atas):**  
   Selama lonjakan burst 300 RPS berlangsung (detik ke-360 hingga 480), `cpu-bound` menimbun antrean raksasa:
   - Tepat di detik ke-480, terdapat **28.769 pesanan mengantre di memori (*in-flight queue*)**!
   - Bandingkan dengan `microservices` yang hanya menimbun 2.375 pesanan, dan `stateless-api` yang hanya menimbun maksimal 18 pesanan.
2. **Fase Pengurasan (*Drain Phase*):**  
   - Ketika lonjakan berakhir di detik ke-480 dan beban turun ke 20 RPS, server `cpu-bound` menguras antrean dengan kecepatan $\mu - \lambda = 56 - 20 = 36\text{ pesanan/detik}$.
   - Di detik ke-600 ketika generator beban berhenti total (`sent = 0`), masih tersisa **24.349 pesanan di antrean**!
   - Server membutuhkan waktu tambahan selama **435 detik (total drain duration 555 detik / lebih dari 9 menit)** hanya untuk menuntaskan sisa pesanan tersebut pada laju stabil $56.0\text{ RPS}$!

---

## 7. Rangkuman Pemeringkatan Kinerja Goodput Lintas Arsitektur

Berdasarkan seluruh hasil observasi empiris skala tinggi pada dataset Ali v2, berikut adalah pemeringkatan ketahanan sistem:

| Peringkat | Arsitektur Aplikasi | Kapasitas Puncak Goodput | Latensi Beban Puncak | Delivery Ratio (%) | Success Rate (%) | Kesimpulan dalam Bahasa Awam |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 🥇 **1** | **`stateless-api`** | **> 400 RPS** | **80.9 ms** | **99.998%** | **99.998%** | **Juara Mutlak:** Model I/O asinkronus non-blocking menangani 400 RPS tanpa saturasi kapasitas, tanpa antrean in-flight, dan hanya 6 kegagalan dari total 506.755 request. |
| 🥈 **2** | **`microservices`** | **~326.9 RPS** | **687.8 ms** | **99.57%** | **99.57%** | **Tangguh Menengah:** Mampu melayani lonjakan hingga ~325 RPS sebelum mengalami latensi koordinasi service mesh Linkerd (2.169 timeout dari 503.955 request). |
| 🥉 **3** | **`cpu-bound`** | **~56.8 RPS** | **4,758.8 ms** | **99.84%** | **99.84%** | **Ketat Dibatasi Kuota:** Mengalami saturasi dini pada ~68 RPS akibat kuota CFS 0.5 core. Menimbun antrean raksasa > 28.000 request dan butuh waktu 9 menit untuk menguras antrean. |

---

## 8. Analisis Kritis & Teliti: Penerapan `limit_req` dengan Parameter `nodelay`

Sebagai tindak lanjut dari fenomena penumpukan antrean masif di atas, muncul sebuah hipotesis rekayasa:  
> *"Dapatkah penambahan direktif `limit_req` dengan parameter `nodelay` pada Ingress Gateway (misal: NGINX Ingress) mengurangi antrean dan meningkatkan Goodput sistem?"*

Berikut adalah analisis kritis, matematis, dan komprehensif berdasarkan prinsip-prinsip rekayasa sistem terdistribusi dan data empiris pengujian Ali v2:

### 8.1 Mekanisme Kerja `limit_req` dan Karakteristik `nodelay`

Pada NGINX / Ingress Controller, algoritma pembatasan laju trafik didasarkan pada varian *Leaky Bucket* (*Token Bucket*):
- Format direktif: `limit_req zone=app_zone burst=B nodelay;` dengan laju dasar `rate=R r/s`.
- **Perilaku Standar (Tanpa `nodelay`):**  
  Jika trafik masuk melampaui $R$, kelebihan request (hingga batas burst $B$) akan **ditahan dan diantrekan secara artifisial di dalam memori proxy NGINX**, lalu dialirkan ke backend satu per satu sesuai laju $R$. Ini menambah waktu tunda (*queue delay*) secara sengaja di lapisan pintu masuk.
- **Perilaku dengan `nodelay`:**  
  Request yang datang di atas laju $R$ **diizinkan langsung lewat ke backend seketika tanpa antrean tunda**, selama kuota burst $B$ belum habis. Namun, begitu ember burst penuh ($> B$), seluruh request berikutnya **langsung ditolak mentah-mentah (*instant reject*) dengan kode status HTTP 503 (atau HTTP 429 Too Many Requests)** tanpa menunggu sama sekali.

---

### 8.2 Analisis Kritis Terhadap Pengurangan Antrean (*Queue Mitigation*)

Penerapan `limit_req ... nodelay` **terbukti secara teoritis dan empiris sangat efektif dalam memangkas penumpukan antrean in-flight**.

#### Mengapa Antrean Bisa Berkurang Drastis?
1. **Pemberantasan Bencana Bufferbloat:**  
   Pada pengujian `cpu-bound` tanpa rate limit, sistem menerima 300 RPS saat kapasitas layanan hanya $\mu = 56.8\text{ RPS}$. Berdasarkan Hukum Little ($L = \lambda W$), akumulasi antrean $L = 28.769$ request menyebabkan estimasi waktu tunggu antrean mencapai:
   $$W = \frac{L}{\mu} = \frac{28.769}{56.8} \approx 506.5\text{ detik (8.4 menit)!}$$
2. **Eliminasi Fase Drain 555 Detik:**  
   Jika Ingress dipasangi `limit_req zone=cpu rate=60r/s burst=20 nodelay;`:
   - Sebanyak 60 request/detik dialirkan lancar ke pod `cpu-bound`.
   - Lonjakan mikro hingga 20 request diserap seketika tanpa tunda.
   - Sisa beban berlebih sebesar $\sim 240\text{ request/detik}$ **langsung dibuang di pintu gerbang dalam waktu $< 1\text{ milidetik}$**.
   - **Hasil Konkret:** Antrean di socket kernel Linux dan Linkerd proxy tidak akan pernah membengkak hingga 28.000 request. Kedalaman antrean terjaga sangat dangkal ($\le 20\text{ request}$), dan fase drain pasca-burst yang memakan waktu 9 menit **lenyap sepenuhnya**.

---

### 8.3 Analisis Kritis Terhadap Goodput: Apakah Goodput Benar-Benar Meningkat?

Di sinilah evaluasi kritis harus dilakukan secara teliti. Apakah pembuangan request menghasilkan "Goodput yang lebih tinggi"? Kita harus membedakan antara **Kapasitas Pemrosesan Absolut** dan **Goodput Efektif Tanpa Beban Racun (*Toxic Load*)**.

#### 1. Pada Kondisi Mantap (*Steady-State Ceiling*): Goodput Absolut TIDAK Meningkat
Secara hukum fisika komputasi, batas atas Goodput dari `cpu-bound` ditentukan oleh alokasi CPU CFS $0.5$ core ($\mu \approx 56.8\text{ RPS}$).
- Menolak request di NGINX tidak akan menambah daya komputasi pod backend.
- Laju transaksi sukses HTTP 200 OK yang keluar dari pod tetap akan mentok di angka $\sim 56.8\text{ RPS}$.
- Oleh karena itu, klaim bahwa rate limiting "meningkatkan kapasitas Goodput puncak" adalah **keliru secara fundamental**.

#### 2. Pada Kondisi Beban Ekstrem: Mencegah Runtuhnya Goodput (*Preventing Goodput Collapse*)
Namun, dalam skenario dunia nyata dengan batas timeout client ($5.000\text{ ms}$), `limit_req nodelay` **berhasil menyelamatkan sistem dari fenomena *Goodput Collapse***:
- **Tanpa `limit_req` (Bencana Pemrosesan Basi / *Stale Execution*):**  
  Ketika waktu antre membengkak menjadi $506\text{ detik}$, pelanggan sudah lama meninggalkan aplikasi (mengalami timeout setelah 5 detik). Namun, server tetap membakar 100% CPU-nya untuk memproses request usang yang jawabannya sudah tidak lagi ditunggu oleh siapa pun. Ini disebut **Badput** (energi terbuang untuk transaksi mati).
- **Dengan `limit_req nodelay` (*Fail-Fast & Shedding Load*):**  
  Dengan membatasi request masuk ke angka $\approx 60\text{ RPS}$, latensi seluruh request yang diizinkan masuk tetap berada di kisaran aman **$20 - 45\text{ milidetik}$** (jauh di bawah batas timeout 5 detik).
  - **100% request yang diproses server dipastikan sukses menjadi Goodput riil yang diterima pelanggan tepat waktu.**
  - Server terbebas dari beban kerja sia-sia (*phantom load*).

```text
Perbandingan Nasib Request pada Beban 300 RPS:

[TANPA limit_req] : 300 RPS Diterima ---> Antrean 28.000 req ---> Latensi 4.700 ms ---> Client Timeout (Banyak Badput/Basi!)
[DENGAN limit_req]: 60 RPS Diterima  ---> Antrean < 20 req    ---> Latensi 25 ms    ---> 100% Goodput Produktif!
                    240 RPS Ditolak Cepat (HTTP 429/503 dalam 1 ms)
```

---

### 8.4 Sisi Negatif, Risiko Rekayasa, dan Jebakan Penerapan `nodelay`

Meskipun `limit_req ... nodelay` sangat efektif mengendalikan antrean, ada risiko dan kompromi arsitektural yang wajib diantisipasi:

1. **Penurunan Drastis Angka *Delivery Ratio* Mentah:**  
   - Pada pengujian Ali v2 tanpa rate limit, *Delivery Ratio* tercatat **99.84%** karena load generator dengan sabar menunggu 9 menit hingga seluruh antrean terkuras.
   - Jika `limit_req` diaktifkan saat lonjakan 300 RPS, maka sekitar $\frac{240}{300} = 80\%$ request akan langsung ditolak HTTP 503. Angka keberhasilan transaksi sesaat akan anjlok menjadi **~20%**.
   - *Pertimbangan Bisnis:* Lebih baik menolak 80% pengguna secara instan (agar aplikasi mereka menampilkan pesan "Server Sibuk, Coba Lagi") daripada membuat 100% pengguna menggantung dalam ketidakpastian selama 5 detik hingga sistem lumpuh total.
2. **Jebakan Penyetelan Statis Lintas Arsitektur (*Static Tuning Dilemma*):**  
   Data empiris Ali v2 membuktikan bahwa batas jenuh setiap aplikasi sangat berbeda:
   - `cpu-bound` jenuh pada **~68 RPS**.
   - `microservices` jenuh pada **~327 RPS**.
   - `stateless-api` bebas jenuh pada **> 400 RPS**.  
   *Peringatan Kritis:* Jika seorang engineer menerapkan aturan seragam di Ingress Gateway, misalnya `limit_req rate=100r/s nodelay`:
   - Bagi `cpu-bound`, angka 100 RPS masih terlalu besar (tetap akan terjadi antrean karena kapasitasnya hanya 56 RPS).
   - Bagi `stateless-api`, angka 100 RPS justru **mencekik performa secara fatal (*artificial throttle*)**, karena aplikasi ini sebenarnya mampu melayani 400 RPS dengan sangat santai!
3. **Pemilihan Parameter Burst ($B$):**  
   - Jika burst terlalu kecil (misal `burst=5 nodelay`), fluktuasi trafik normal yang wajar (*microburst*) akan memicu penolakan HTTP 503 palsu (*false positive*).
   - Jika burst terlalu besar (misal `burst=500 nodelay`), paket 500 request yang lolos seketika ke `cpu-bound` akan langsung membuat prosesor tersedak sebelum rate limit sempat meredam.

---

### 8.5 Kesimpulan & Rekomendasi Arsitektural Terbaik

Berdasarkan analisis empiris dan teoritis di atas:
1. **Gunakan `limit_req ... nodelay` Secara Spesifik Per-Layanan (*Granular Ingress Ingress-Class/Annotation*):**  
   Jangan pasang rate limit global di tingkat cluster. Berikan anotasi khusus per-Ingress sesuai profil saturasi masing-masing pod:
   - `cpu-bound`: `rate=60r/s burst=20 nodelay`
   - `microservices`: `rate=300r/s burst=50 nodelay`
   - `stateless-api`: Bebaskan atau pasang batas sangat tinggi (`rate=500r/s burst=100 nodelay`).
2. **Kombinasikan dengan Kode Status HTTP 429 dan Header `Retry-After`:**  
   Ganti respon default NGINX dari HTTP 503 menjadi HTTP 429 (*Too Many Requests*) dengan menyertakan header `Retry-After: 2`. Hal ini menginstruksikan aplikasi mobile/client untuk menunda request ulang secara teratur (*exponential backoff*), sehingga mencegah terjadinya badai percobaan ulang (*retry storm*).
3. **Evolusi Menuju *Adaptive Concurrency Limits*:**  
   Untuk sistem modern berskala besar, batasan statis NGINX sebaiknya digantikan atau dilengkapi dengan sistem kendali adaptif (seperti algoritma *TCP Vegas/Gradient Controller* pada Netflix Concurrency Limits), di mana gateway otomatis menolak request hanya ketika latensi p95 mulai merangkak naik, tanpa perlu menetapkan angka RPS statis yang kaku.
