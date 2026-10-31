# Draft Presentasi (8 Slide): Analisis Dinamika Cloud, Goodput, dan Titik Jenuh pada Kluster Kubernetes

Dokumen ini adalah draf materi presentasi komprehensif 8 slide yang dirancang untuk mempresentasikan hasil riset **Cloud Dynamics Empirical Analysis** berbasis sintesis tiga dataset empiris utama:
1. **Dataset Taufik** (`res-taufik` / [`resume_cloud_dynamics_empirical_analysis_taufik.md`](../resume/resume_cloud_dynamics_empirical_analysis_taufik.md))
2. **Dataset Ali v1** (`res-ali` / [`resume_cloud_dynamics_empirical_analysis_ali.md`](../resume/resume_cloud_dynamics_empirical_analysis_ali.md))
3. **Dataset Ali v5** (`res-ali-v5` / [`resume_cloud_dynamics_empirical_analysis_ali_v5.md`](../resume/resume_cloud_dynamics_empirical_analysis_ali_v5.md))

Setiap slide dilengkapi dengan:
- **Poin Presentasi (Slide Content)**
- **Visualisasi & Diagram Pendukung**
- **Catatan Pembicara / Narasi Presenter (*Speaker Notes*)** yang runtut dan mudah dipahami oleh audiens awam maupun penguji teknis.

---

## Slide 1: Research Context (Konteks Riset & Urgensi Goodput)

### Judul Slide:
**Membongkar Realita Kinerja Cloud: Mengapa Throughput Tinggi Bisa Menipu dan Mengapa Goodput adalah Kunci?**

### Konten Slide:
* **Latar Belakang Industri Cloud-Native:**
  - Migrasi masif aplikasi monolitik menuju arsitektur kontainer berbasis Kubernetes (*cloud-native microservices*).
  - Tantangan operasional: Sistem sering terlihat sibuk dan "sehat" di dasbor pemantauan, namun pengguna akhir mengeluhkan aplikasi lambat (*loading screen* lama) atau transaksi gagal (*timeout*).
* **Paradoks Throughput vs. Goodput:**
  - **Throughput ($X$):** Mengukur seberapa sibuk jaringan memompa paket data per detik, **tanpa peduli** apakah data tersebut kadaluwarsa, salah saji, atau dibatalkan pengguna.
  - **Goodput ($G$):** Mengukur transaksi produktif yang **benar-benar berhasil selesai bebas error (HTTP 200 OK) dalam batas toleransi SLA (5,0 detik)**.
* **Pertanyaan Riset Utama:**
  1. Di mana letak batas jenuh fisik (*knee of saturation*) saat beban trafik dinaikkan?
  2. Apa yang terjadi pada antrean sistem ketika beban melampaui kapasitas komputasi?
  3. Bagaimana evolusi pengujian beban dari model tertutup (*closed-loop*) ke model terbuka (*open-loop*) membongkar fenomena *Coordinated Omission*?

```text
[Beban Datang (Offered Load)] ===> [Beban Diproses Jaringan (Throughput)] ===> [Transaksi Sukses Sesuai SLA (Goodput)]
     (Pengguna Menekan Tombol)              (Server Sibuk Bekerja)                   (Pelanggan Puas Bebas Error)
```

### Catatan Pembicara (*Speaker Notes*):
> *"Selamat pagi/siang Bapak/Ibu dewan penguji dan rekan-rekan sekalian. Presentasi ini mengangkat topik krusial dalam rekayasa komputasi awan: Dinamika Performa Cloud di Bawah Beban Terkontrol. Selama bertahun-tahun, industri sering tertipu oleh metrik Throughput—menganggap bahwa selama server sibuk memproses paket data tinggi, sistem dalam keadaan baik. Namun di dunia nyata, pelanggan tidak peduli seberapa sibuk wajan dapur mengepul; pelanggan hanya peduli apakah makanannya sampai tepat waktu tanpa basi. Inilah inti dari metrik Goodput. Melalui riset ini, kami menguji tiga arsitektur aplikasi kontainer di kluster Kubernetes nyata, membedah fenomena penumpukan antrean, mendeteksi titik jenuh kapasitas, dan membongkar bias pengukuran alat uji untuk mendapatkan data yang benar-benar mencerminkan realita lapangan."*

---

## Slide 2: Experimental Environment (Lingkungan Eksperimen & Infrastruktur Kluster)

### Judul Slide:
**Infrastruktur Eksperimen: Kluster Kubernetes Bare-Metal dengan Service Mesh & Telemetri Presisi**

### Konten Slide:
* **Platform Fisik & Sistem Operasi:**
  - Kluster Kubernetes Bare-Metal (Homelab Riset RM77, Host IP: `10.160.4.43`).
  - Kernel Linux dengan regulasi isolasi sumber daya cgroups (Completely Fair Scheduler / CFS bandwidth quota).
* **Gerbang Lalu Lintas & Komunikasi Layanan:**
  - **Ingress Gateway:** NGINX Ingress Controller (Domain routing berbasis dynamic DNS `sslip.io`).
  - **Service Mesh:** **Linkerd** (mTLS terenkripsi otomatis, proxy sidecar per pod, observabilitas latensi P50/P95/P99, dan pool koneksi TCP).
* **Stack Telemetri & Observabilitas:**
  - **Prometheus Time-Series Engine:** Pengambilan metrik sistem terpadu setiap interval $\Delta t = 1,0\text{ detik}$.
  - **cAdvisor & Node Exporter:** Telemetri utilisasi CPU, throttling kuota CFS, memori kerja, dan aliran jaringan RX/TX.
* **Evolusi Generator Beban (*Workload Generator*):**
  - **Generator v1 (Closed-Loop Thread-Pool):** Menggunakan 256 worker threads (digunakan pada dataset awal Taufik dan Ali v1).
  - **Generator v2 (Open-Loop Asinkronus murni - [`loadgen_v2.py`](file:///home/ali/kuliah/homelab-fp-rm77/kubernetes/research/cloud-dynamics-experiments/loadgen/loadgen_v2.py)):** Berbasis `asyncio` & `aiohttp`, koneksi soket tanpa batas antrean klien, dengan penegakan *deadline timeout* ketat 5,0 detik (digunakan pada Ali v5).

```text
[Client Load Generator (loadgen_v2.py)]
                 │  (HTTP / TCP Sockets)
                 ▼
[NGINX Ingress Controller Gateway]
                 │  (Service Routing via sslip.io)
                 ▼
[Linkerd Service Mesh Proxy (Sidecar mTLS)]
                 │
       ┌─────────┴─────────┐
       ▼                   ▼
[Application Pod]  [Prometheus / cAdvisor Telemetry (1s)]
```

### Catatan Pembicara (*Speaker Notes*):
> *"Untuk memastikan data riset ini valid dan dapat direproduksi, seluruh eksperimen dijalankan di atas kluster Kubernetes bare-metal mandiri di Homelab RM77. Arsitektur jaringan kami dilengkapi NGINX Ingress Gateway sebagai pintu gerbang masuk dan Linkerd Service Mesh sebagai pengatur komunikasi antar-kontainer. Seluruh denyut sistem—mulai dari penggunaan CPU, pembatasan throttling kuota Linux, jejak memori, hingga koneksi TCP—dipantau secara sinkron tiap 1 detik menggunakan Prometheus dan cAdvisor. Lebih jauh lagi, kami menggunakan dua generasi generator beban: generator v1 berbasis thread pool, dan generator v2 berbasis open-loop asinkronus yang kami bangun sendiri untuk memastikan beban ditembakkan secara independen tanpa ditahan di memori klien."*

---

## Slide 3: Application Architecture (Arsitektur Tiga Aplikasi Uji)

### Judul Slide:
**Tiga Karakter Aplikasi: Dari Kasir Cekatan Hingga Koki Komputasi Berkuota Kaku**

### Konten Slide:
Riset ini membandingkan respons dinamis dari tiga karakteristik arsitektur aplikasi kontainer yang sangat kontras:

1. **`stateless-api` (Si Kasir Tol Otomatis Cekatan):**
   - **Arsitektur:** *Asynchronous Non-Blocking I/O Event-Loop* (Node.js/Go paradigm).
   - **Karakteristik:** Menangani request I/O ringan, pemakaian CPU sangat rendah, eksekusi instan dalam milidetik ($< 5\text{ ms}$).
2. **`microservices` (Restoran Berjaringan Multi-Tier):**
   - **Arsitektur:** Modular terdistribusi, memisahkan gerbang penerima tamu (**`frontend`**) dan unit pengolah logika (**`backend`**).
   - **Karakteristik:** Dilengkapi proxy sidecar Linkerd di setiap pod. Menguji dampak *network hop latency*, serialisasi data, dan koordinasi antar-layanan. Pada dataset Taufik, konsumsi CPU dipantau terpisah (`frontend` 0,54 core vs `backend` 0,33 core).
3. **`cpu-bound` (Koki Spesialis Enkripsi Berat Berkuota Terbatas):**
   - **Arsitektur:** Compute-intensive workload (perhitungan matematika berat & hashing enkripsi).
   - **Karakteristik:** Dibatasi aturan ketat oleh cgroups Linux: **`limits.cpu = 500m` (0,5 inti CPU)**. Merupakan representasi layanan pemrosesan data intensif yang rentan tercekik (*CPU throttled*).

| Parameter Arsitektur | `stateless-api` | `microservices` | `cpu-bound` |
| :--- | :---: | :---: | :---: |
| **Karakter Beban** | I/O-Bound (Non-blocking) | Multi-hop Network / Mesh | Compute-Bound (Intensive) |
| **Komponen Layanan** | Single Service Pod | Frontend + Backend Pods | Single Worker Pod |
| **Interaksi Jaringan** | Direct Ingress $\to$ Pod | Ingress $\to$ Mesh $\to$ Inter-service | Direct Ingress $\to$ Pod |
| **Batas Kuota CPU** | Mengikuti Node / Uncapped | 2 Layanan Mesh Terpisah | **Ketat 0,5 Core (500m CFS)** |
| **Kapasitas Teoretis** | Sangat Tinggi ($> 600\text{ RPS}$) | Menengah ($\sim 340\text{ RPS}$) | Terbatas Kaku ($\sim 56\text{ RPS}$) |

### Catatan Pembicara (*Speaker Notes*):
> *"Untuk mendapatkan perbandingan komparatif yang bermakna, kami memilih tiga arsitektur yang mewakili beban kerja komputasi awan modern. Pertama, stateless-api, yang bekerja seperti gerbang tol otomatis: hanya memvalidasi kartu dan langsung membuka palang. Kedua, microservices, yang membagi peran antara pelayan depan (frontend) dan dapur pengolah (backend) yang saling terhubung lewat service mesh Linkerd. Ketiga, cpu-bound, yaitu pekerja komputasi berat yang kami beri batasan kuota prosesor ketat: hanya 0,5 core atau setengah inti CPU. Dengan menguji ketiganya secara berdampingan di bawah profil beban yang persis sama, kita dapat melihat secara transparan bagaimana perbedaan desain arsitektur memengaruhi ketahanan sistem."*

---

## Slide 4: Experimental Setup (Pengaturan Eksperimen & Kontrol Metodologi)

### Judul Slide:
**Protokol Eksperimen Terkontrol: Pengujian Berulang, SLA 5 Detik, dan Siklus Hidup Uji**

### Konten Slide:
* **Protokol Siklus Pengujian Terstandarisasi:**
  - **Fase Pemanasan (*Warm-up*):** 30 detik pada beban rendah 5 RPS untuk mengeliminasi bias *cold start* / JIT compiler.
  - **Fase Pengukuran Aktif (*Active Window*):** Jendela pengukuran murni (30 detik untuk *constant*, 600 detik untuk *ramp* dan *burst*).
  - **Fase Pendinginan (*Cool-down*):** 15 detik pasca-uji untuk stabilisasi sistem.
  - **Fase Pengurasan (*Drain Phase*):** Menunggu dan mengukur waktu penyelesaian sisa request yang masih berada di antrean soket sistem.
* **Batas Toleransi Sabar Pengguna (*Client Timeout SLA*):**
  - Ditetapkan tegas pada angka **5,0 detik ($5.000\text{ ms}$)**.
  - Transaksi yang membutuhkan waktu $> 5,0\text{ detik}$ dianggap gagal total oleh pengguna (*HTTP 504 / Connection Timeout*).
* **Reproduksibilitas Statistik:**
  - Setiap skenario dijalankan sebanyak **3 replikasi independen ($r1, r2, r3$)** untuk memastikan temuan bukan kebetulan sesaat.
* **Evolusi Metodologi Pengujian Antar Dataset:**
  - **Taufik & Ali v1:** Model closed-loop (antrean tertahan di thread pool klien).
  - **Ali v5:** Model open-loop hakiki (beban ditembakkan tepat waktu ke soket jaringan, deadline timeout dihitung sejak jadwal kedatangan).

```text
[0s] ──(Warm-up: 30s @ 5 RPS)──► [30s] ──(Active Measurement: 600s)──► [630s] ──(Cool-down: 15s)──► [Drain Window]
```

### Catatan Pembicara (*Speaker Notes*):
> *"Agar pengujian ini memenuhi kaidah saintifik yang ketat, seluruh eksperimen mengikuti protokol terkontrol yang terstandarisasi. Setiap pengujian diawali pemanasan 30 detik pada laju 5 RPS agar pod kontainer dan proxy Linkerd berada dalam kondisi siap tempur tanpa terganggu jeda cold-start. Kami menetapkan batas SLA sabar pengguna pada angka 5,0 detik: jika sebuah request membutuhkan waktu lebih dari 5 detik, request tersebut dianggap gagal. Seluruh pengujian diulang sebanyak tiga kali replikasi independen untuk memastikan konsistensi data. Khusus pada dataset Ali v5, kami menerapkan penegakan batas waktu deadline dari waktu jadwal kedatangan sesungguhnya, sehingga dinamika antrean mencerminkan realita sistem produksi."*

---

## Slide 5: Workload Scenario (Tiga Skenario Pola Beban Empiris)

### Judul Slide:
**Tiga Skenario Uji: Beban Konstan Sehari-hari, Kenaikan Bertahap, dan Guncangan Lonjakan Dadakan**

### Konten Slide:
Riset ini mengevaluasi sistem terhadap tiga pola lalu lintas realistis:

1. **`constant` (Baseline Kestabilan Steady-State):**
   - **Pola Beban:** Beban tetap teratur (25 RPS) selama 30 detik (total 750 request).
   - **Tujuan Evaluasi:** Mengukur latensi intrinsik dasar, stabilitas pemakaian memori, dan indeks dispersi jitter ($CV = \sigma / \mu$) dalam kondisi bebas jenuh.
2. **`ramp` (Eskalasi Linier Jam Sibuk):**
   - **Pola Beban:** Beban merangkak naik bertahap dari **10 RPS ke 200 RPS** selama 600 detik ($\Delta \text{RPS} \approx 0,317\text{ RPS/s}$).
   - **Tujuan Evaluasi:** Memetakan transisi titik jenuh (*knee of saturation*), kurva latensi *hockey-stick*, dan divergensi Goodput saat beban mulai melampaui kapasitas.
3. **`burst` (Guncangan Dinamis Tiga Babak):**
   - **Babak 1 (0–180s):** Kondisi tenang santai pada 10 RPS.
   - **Babak 2 (180–300s):** Lonjakan ekstrem seketika 15x lipat ke **150 RPS** selama 120 detik (2 menit).
   - **Babak 3 (300–600s):** Beban turun kembali ke 10 RPS selama 300 detik (5 menit).
   - **Tujuan Evaluasi:** Mengukur daya serap lonjakan (*surge capacity*), lonjakan latensi puncak (*overshoot latency*), dan waktu pemulihan mandiri (*recovery time* $T_{\text{recover}}$).

```text
  RPS ^                                   RPS ^           [150 RPS Spike]
  200 |              /                    150 |           ┌─────────────┐
      |             /                         |           │ (120 detik) │
      |            /                          |           │             │
   25 | ──────────                            | ──────────┘             └──────────
   10 |                                    10 |  (180s)                   (300s)
      +──────────────> Waktu (s)              +───────────────────────────────────> Waktu (s)
       [Constant]   [Ramp]                                  [Burst]
```

### Catatan Pembicara (*Speaker Notes*):
> *"Untuk menguji kehandalan sistem dari berbagai sudut pandang operasional, kami merancang tiga skenario beban empiris. Skenario pertama adalah Constant pada 25 RPS, menguji kondisi santai sehari-hari untuk mengukur latensi dasar sistem ketika tidak ada antrean. Skenario kedua adalah Ramp, di mana beban dinaikkan secara halus dari 10 hingga 200 RPS selama 10 menit untuk melihat di titik mana masing-masing arsitektur mulai terengah-engah dan mengalami kejenuhan. Skenario ketiga adalah Burst Dinamis tiga babak: 3 menit sepi pada 10 RPS, tiba-tiba dihantam serbuan 150 RPS selama 2 menit (seperti fenomena Flash Sale e-commerce), lalu 5 menit fase sepi kembali untuk membuktikan apakah sistem sanggup pulih secara mandiri atau justru mati suri selamanya."*

---

## Slide 6: Metrics dan Data Collection (Telemetri Terpadu & Rumus Matematis)

### Judul Slide:
**Harmonisasi Telemetri Multi-Sumber: 25 Kolom Data dan Formula Matematis Goodput**

### Konten Slide:
* **Sinkronisasi 25 Kolom Data Per Detik (`combined.csv`):**
  - **Sisi Klien (Traffic & User Experience):** `target_rps`, `sent`, `achieved_rps`, `success`, `failed`, `mean_latency_ms`, `p95_latency_ms`.
  - **Sisi Kontainer Pod (Kernel & Resource Isolation):** `CPU_USAGE`, `CPU_THROTTLED`, `MEMORY_WORKING_SET`, `NETWORK_RX`, `NETWORK_TX`, `RESTARTS`.
  - **Sisi Service Mesh (Linkerd Mesh Proxy):** `LINKERD_REQUEST_RATE`, `LINKERD_GOODPUT_RPS`, `LINKERD_SUCCESS_RATE`, `LINKERD_TCP_CONNECTIONS`.
* **Empat Formula Metrik Evaluasi Goodput:**
  1. **Overall Goodput Delivery Ratio ($\eta_d$):**
     $$\eta_d = \frac{\sum \text{success}}{\sum \text{sent}} \times 100\% \quad \text{(Efisiensi penyerapan beban menjadi transaksi produktif)}$$
  2. **Goodput Success Rate ($\eta_s$):**
     $$\eta_s = \frac{\sum \text{success}}{\sum \text{success} + \sum \text{failed}} \times 100\% \quad \text{(Tingkat kebersihan dari error / timeout)}$$
  3. **Instantaneous Fulfillment Ratio ($\eta_f(t)$):**
     $$\eta_f(t) = \frac{\text{Goodput}(t)}{\text{Target RPS}(t)} \times 100\% \quad \text{(Kemampuan sistem memenuhi beban sesaat)}$$
  4. **Akumulasi Soket Aktif / Backpressure ($Q(t)$):**
     $$Q(t) = \max\left(0, \sum_{\tau=0}^t (\text{sent}(\tau) - \text{success}(\tau) - \text{failed}(\tau))\right)$$

### Catatan Pembicara (*Speaker Notes*):
> *"Kekuatan analisis riset ini bertumpu pada integritas data. Setiap satu detik, pipeline kolektor kami menggabungkan 25 kolom telemetri dari tiga sudut pandang berbeda: dari sisi klien yang mengukur apa yang dirasakan pengguna, dari sisi kernel Linux cAdvisor yang mengukur utilisasi fisik prosesor dan memori, serta dari sisi proxy Linkerd yang mengukur aliran soket jaringan. Dari data tersebut, kami merumuskan empat metrik utama: Delivery Ratio untuk mengukur berapa persen pesanan yang berhasil sampai, Success Rate untuk mengukur kebersihan transaksi dari error 500 atau timeout, Instantaneous Fulfillment untuk mengukur kesiapan sistem merespons beban di setiap detik, serta metrik antrean in-flight Q(t) untuk menghitung berapa banyak koneksi yang sedang terjebak di dalam jaringan kluster."*

---

## Slide 7: Experimental Results (Hasil Eksperimen & Perbandingan Lintas Dataset)

### Judul Slide:
**Hasil Pengujian Empiris: Plafon Kaku CPU-Bound vs. Ketangguhan Sempurna Microservices**

### Konten Slide:
* **Tabel Perbandingan Kinerja Utama Lintas Dataset (Taufik, Ali v1, Ali v5):**

| Arsitektur Aplikasi | Kapasitas Puncak Goodput | Latensi Baseline (25 RPS) | Latensi Puncak (Ramp) | Delivery Ratio (Ramp 200 RPS) | Perilaku Lonjakan Burst (150 RPS) |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`stateless-api`** | **$> 200\text{ RPS}$** | **$4,0 - 10,7\text{ ms}$** | **$4,2 - 22,4\text{ ms}$** | **$98,4\% - 100\%$** | **Sempurna 100% Sukses;** Latensi $< 5\text{ ms}$; Recovery 0 detik. |
| **`microservices`** | **$> 200\text{ RPS}$** | **$8,1 - 16,2\text{ ms}$** | **$8,8 - 25,6\text{ ms}$** | **$100,00\%$** (0 failed di Ali v5) | **Sempurna 100% Sukses;** Latensi $8,2\text{ ms}$; Recovery 0 detik. |
| **`cpu-bound`** | **$\sim 52 - 57\text{ RPS}$** | **$18,9 - 71,8\text{ ms}$** | **$4.700 - 8.280\text{ ms}$** | **$42,9\% - 48,9\%$** (Gagal masif) | **Lumpuh Parsial;** Latensi mentok 5.000 ms; Pulih dalam 20 detik. |

* **Visualisasi Inti Hasil Eksperimen:**
  - **Kurva Titik Jenuh (*Hockey-Stick & Goodput Plateau*):**

![Titik Jenuh Kapasitas Ali v5](../outputs/ali-v5/figures/04_knee_of_saturation_curves.png)

* **Tiga Fakta Keras Temuan Eksperimen:**
  1. **Plafon Kapasitas `cpu-bound` Konsisten di $\sim 56\text{ RPS}$:** Dibatasi kaku oleh kuota CFS 0,5 core. Pada beban 200 RPS, separuh beban ($\sim 51\%$) pasti gagal timeout.
  2. **Keunggulan Absolut `microservices` pada Skala 200 RPS:** Pada Ali v5, melayani seluruh **62.999 request dengan 100,00% sukses** tanpa 1 pun transaksi gagal (latensi rata-rata hanya 8,8 ms).
  3. **Kecepatan Tertinggi `stateless-api`:** Konsisten tercepat dengan latensi sub-5 ms dan konsumsi daya paling hemat.

### Catatan Pembicara (*Speaker Notes*):
> *"Mari kita cermati tabel dan grafik hasil eksperimen di slide ini. Grafik ini menunjukkan fakta yang sangat konsisten di ketiga dataset. Perhatikan garis merah pada grafik titik jenuh: kurva latensi cpu-bound bergerak landai hingga angka 56 RPS, namun begitu melewati 64 RPS, kurva menekuk tajam ke atas menyerupai tongkat hoki dan membentur garis merah putus-putus, yaitu batas toleransi batas waktu 5 detik. Sebaliknya, perhatikan garis hijau untuk microservices dan garis biru untuk stateless-api: keduanya berimpit sempurna dengan garis putus-putus hitam ideal. Khusus pada dataset Ali v5, microservices membuktikan performa gemilang dengan meraih 100% Success Rate sempurna dari total 147.000 request tanpa ada satu pun yang gagal, dengan latensi rata-rata hanya 8,8 milidetik. Sementara itu, cpu-bound konsisten terjepit di angka 56 RPS, membuktikan bahwa batas prosesor 0,5 core menjadi tembok pembatas kaku yang tidak bisa ditawar."*

---

## Slide 8: Observed Phenomenon (Fenomena Kritis, Teori, dan Rekomendasi Industri)

### Judul Slide:
**Fenomena Kritis Sistem Terdistribusi & Rekomendasi Rekayasa untuk Industri**

### Konten Slide:
* **Empat Fenomena Sistemik yang Terungkap:**
  1. **Kurva Tongkat Hoki (*Hockey-Stick Latency*) & Hukum Little:**  
     Ketika laju kedatangan $\lambda$ mendekati kapasitas layanan $\mu$, utilisasi $\rho \to 1,0$. Berdasarkan teori antrean $M/M/1$, waktu tunggu $W = \frac{1}{\mu(1-\rho)}$ melonjak vertikal. Penambahan beban di atas 56 RPS hanya memperpanjang antrean sia-sia (*wasteful computation*).
  2. **Bias Pengujian: Coordinated Omission vs. Realitas Open-Loop:**  
     Pengujian closed-loop lama (Taufik/Ali v1) menyamarkan antrean di memori klien (menghasilkan angka sukses semu), sedangkan pengujian open-loop (Ali v5) membongkar kegagalan timeout riil dan mengendalikan akumulasi antrean soket aktif.
  3. **Resiliensi Lonjakan & Pemulihan Cepat (*Self-Healing*):**  
     Pada uji burst 150 RPS, `cpu-bound` membuktikan kemampuan menormalkan antrean dan kembali ke latensi normal ($18,7\text{ ms}$) dalam tempo **$\sim 20\text{ detik}$** tanpa restart pod (*zero restart*).

![Triad Kinerja Goodput Ali v5](../outputs/ali-v5/figures/05_goodput_triad_and_fulfillment.png)

* **Tiga Rekomendasi Rekayasa untuk Sistem Produksi Cloud:**
  - **Penerapan *Fail-Fast Load Shedding* di Ingress (`limit_req ... nodelay`):** Lebih baik menolak request berlebih dalam waktu $< 1\text{ ms}$ (HTTP 429) daripada membiarkan pengguna menunggu 5 detik lalu gagal.
  - **Autoscaling Proaktif (HPA) Berbasis Titik Jenuh:** Pod komputasi berat wajib dipasangi *Horizontal Pod Autoscaler* yang memicu replikasi sebelum beban mencapai ambang jenuh 56 RPS.
  - **Keyakinan Menggunakan Service Mesh:** Mengikis mitos bahwa service mesh memperlambat sistem; Linkerd terbukti sangat tangguh pada beban kerja produksi moderat ($\le 200\text{ RPS}$).

### Catatan Pembicara (*Speaker Notes*):
> *"Sebagai penutup, riset ini memberikan pelajaran rekayasa yang sangat fundamental bagi industri perangkat lunak modern. Pertama, kita membuktikan secara matematis dan empiris bahwa membiarkan sistem berjalan di atas titik jenuh tanpa perlindungan adalah pemborosan fatal: server bekerja keras menghabiskan listrik dan CPU untuk memproses pesanan yang pada akhirnya dibatalkan oleh pengguna karena timeout. Kedua, kami membuktikan pentingnya pengujian beban open-loop untuk menghindari ilusi Coordinated Omission. Rekomendasi konkret kami untuk para praktisi industri: pasanglah mekanisme Fail-Fast Load Shedding di gerbang Ingress NGINX menggunakan limit_req nodelay agar kelebihan beban ditolak seketika dalam 1 milidetik, pasang Autoscaler otomatis pada aplikasi komputasi sebelum menyentuh batas jenuh 56 RPS, dan jangan ragu mengadopsi Service Mesh Linkerd karena terbukti tangguh mengawal ratusan ribu transaksi dengan kebersihan 100 persen. Terima kasih, kami siap menerima pertanyaan dan masukan dari dewan penguji."*

---

## Verifikasi Tautan Berkas Terkait
* Direktori Draft PPT: [`kubernetes/research/cloud-dynamics-analysis-venv/draft-ppt/`](file:///home/ali/kuliah/homelab-fp-rm77/kubernetes/research/cloud-dynamics-analysis-venv/draft-ppt/)
* Berkas Resume Taufik: [`resume_cloud_dynamics_empirical_analysis_taufik.md`](file:///home/ali/kuliah/homelab-fp-rm77/kubernetes/research/cloud-dynamics-analysis-venv/resume/resume_cloud_dynamics_empirical_analysis_taufik.md)
* Berkas Resume Ali v1: [`resume_cloud_dynamics_empirical_analysis_ali.md`](file:///home/ali/kuliah/homelab-fp-rm77/kubernetes/research/cloud-dynamics-analysis-venv/resume/resume_cloud_dynamics_empirical_analysis_ali.md)
* Berkas Resume Ali v5: [`resume_cloud_dynamics_empirical_analysis_ali_v5.md`](file:///home/ali/kuliah/homelab-fp-rm77/kubernetes/research/cloud-dynamics-analysis-venv/resume/resume_cloud_dynamics_empirical_analysis_ali_v5.md)
* Direktori Gambar Visualisasi:
  - [`outputs/ali-v5/figures/`](file:///home/ali/kuliah/homelab-fp-rm77/kubernetes/research/cloud-dynamics-analysis-venv/outputs/ali-v5/figures/)
  - [`outputs/ali/figures/`](file:///home/ali/kuliah/homelab-fp-rm77/kubernetes/research/cloud-dynamics-analysis-venv/outputs/ali/figures/)
  - [`outputs/taufik/figures/`](file:///home/ali/kuliah/homelab-fp-rm77/kubernetes/research/cloud-dynamics-analysis-venv/outputs/taufik/figures/)
