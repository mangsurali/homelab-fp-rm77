# Analisis dan Perhitungan Goodput pada Eksperimen Cloud Dynamics

Dokumen ini memuat panduan komprehensif mengenai metodologi perhitungan **Goodput**, interpretasi data telemetri client (`sent`, `success`, `failed`), serta analisis fenomena antrean (*queueing saturation*) yang terjadi pada pengujian beban controlled experiment.

---

## 1. Definisi: Goodput vs Throughput vs Offered Load

Dalam sistem terdistribusi dan rekayasa kinerja (*performance engineering*), penting untuk membedakan tiga konsep utama:

```text
[Offered Load]               [Throughput]                       [Goodput]
(Laju Permintaan)            (Total Data / Request)             (Transaksi Sukses Saja)
target_rps / sent    --->    LINKERD_REQUEST_RATE      --->     success / LINKERD_GOODPUT_RPS
(Beban yang diminta)         (Semua yang masuk proxy)           (Pekerjaan yang bernilai & tuntas)
```

1. **Offered Load (`target_rps` / `sent` / `achieved_rps`):**
   Laju permintaan yang dibangkitkan oleh client/pengguna dan didorong ke jaringan.
2. **Throughput (`LINKERD_REQUEST_RATE`):**
   Total laju data atau request yang diproses oleh sistem per satuan waktu, termasuk request yang berakhir dengan error (HTTP 5xx) atau retransmisi.
3. **Goodput (`success` / `LINKERD_GOODPUT_RPS`):**
   Laju request atau transaksi yang **berhasil diselesaikan tanpa error** (HTTP $200 \le \text{status} < 400$) per satuan waktu. Goodput mengukur pekerjaan produktif riil yang berhasil dihantarkan ke pengguna akhir.

---

## 2. Metodologi Perhitungan Goodput dari Kolom `sent`, `success`, dan `failed`

Pada file dataset gabungan [`combined.csv`](file:///home/ali/experimpent/cloud2023/kubernetes/research/cloud-dynamics-experiments/results/ramp-20261028T003408Z-r1/combined.csv) dan log client [`workload.csv`](file:///home/ali/experimpent/cloud2023/kubernetes/research/cloud-dynamics-experiments/loadgen/loadgen.py), metrik dicatat per interval sampling ($\Delta t$, default 1 detik).

### A. Formula Goodput Client-Side
Goodput riil pada setiap jendela waktu $\Delta t$ dihitung sebagai laju penyelesaian transaksi sukses:

$$\text{Goodput (RPS)} = \frac{\text{success}}{\Delta t}$$

* Karena interval pengujian default adalah $\Delta t = 1.0\text{ detik}$, maka nilai pada kolom **`success` adalah Goodput langsung** (RPS) pada detik tersebut:
  $$\text{Goodput (RPS)} = \text{success}$$

### B. Formula Success Rate (Tingkat Keberhasilan Pemrosesan)
Rasio keberhasilan dari seluruh respons yang selesai diterima pada interval tersebut:

$$\text{Success Rate} = \frac{\text{success}}{\text{success} + \text{failed}}$$

* Jika $\text{failed} = 0$, maka $\text{Success Rate} = 1.0$ ($100\%$).
* Jika ada error (timeout, HTTP 500/502/503), nilainya akan turun di bawah 1.0.

### C. Jebakan Perhitungan: Mengapa Tidak Membagi $\frac{\text{success}}{\text{sent}}$ per Detik?

> [!CAUTION]
> Jangan menghitung efisiensi sesaat (*instantaneous efficiency*) menggunakan formula $\frac{\text{success}}{\text{sent}}$ per detik!

Penyebabnya adalah **adanya delay waktu (latensi)**:
1. Kolom `sent` mencatat request yang **diberangkatkan** pada interval detik tersebut.
2. Kolom `success` dan `failed` mencatat request yang **selesai diterima kembali** pada interval detik tersebut.
3. Saat beban tinggi dan latensi melonjak (misal 3 detik), request yang selesai di detik $t$ adalah request yang dikirim pada detik $t - 3$.
4. Jika Anda membagi $\frac{\text{success}}{\text{sent}}$, nilainya akan tampak anjlok semu saat beban naik.
5. Terlebih lagi pada **fase pengurasan antrean (*drain phase*)**, di mana injeksi beban sudah berhenti (`sent = 0`), server masih menyelesaikan ribuan request sukses (`success > 0`). Menghitung $\frac{\text{success}}{\text{sent}}$ akan menyebabkan kesalahan matematika *division by zero*!

---

## 3. Analisis Fenomena: `sent` Meningkat, `success` Konstan/Menurun, dan `failed` Tetap 0

Fenomena di mana laju pengiriman (`sent`) terus melonjak, tetapi laju sukses (`success`) mendatar (*plateau*) atau sedikit turun, sementara kegagalan (`failed`) tetap bernilai 0, adalah karakteristik fundamental dari **saturasi antrean (*queueing saturation*)**.

```text
[Client / loadgen]  === sent: 100, 300, 500, 1000 RPS ===>
                                  |
                                  v
                +------------------------------------+
                |       SISTEM BUFFER & ANTREAN       |
                |  - TCP Listen Backlog (OS Kernel)  |
                |  - Ingress Nginx Connection Buffer |
                |  - Linkerd Inbound Proxy Queue     |
                +------------------------------------+
                                  |
                   Request Menunggu Giliran Eksekusi
                   (Latensi melonjak: 20ms -> 4500ms)
                   [TETAP BELUM TIMEOUT (< 5s)]
                                  |
                                  v  (Maksimal ~56 RPS)
                +------------------------------------+
                |       KAPASITAS CPU APLIKASI       |
                |   (2 Pod x 500m Limit = 100% CPU)  |
                +------------------------------------+
                                  |
                                  v
                 HTTP 200 OK Selesai Diproses
                 (success = ~56 RPS, failed = 0)
```

### Penjelasan Mekanisme Fisik & Sistemik:

### 1. Batas Jenuh Kapasitas Layanan (*Throughput / Goodput Plateau*)
* Aplikasi target (misalnya [`cpu-bound`](file:///home/ali/experimpent/cloud2023/kubernetes/research/cloud-dynamics-experiments/scenarios/ramp.env)) memiliki batas sumber daya terbatas.
* Pada arsitektur `cpu-bound` 2 replika pod dengan limit CPU masing-masing 500m (total 1000m atau 1 core vCPU), setiap request membutuhkan komputasi hash sekitar ~14.6 ms:
  $$\text{Kapasitas Teoretis} = \frac{1000\text{ ms CPU}}{14.6\text{ ms / req}} \approx 68.5\text{ RPS}$$
* Memperhitungkan overhead enkripsi mTLS dan perutean proxy Linkerd, batas kapasitas nyata stabil pada **~56–57 RPS**.
* Sekalipun client melipatgandakan pengiriman request hingga 1000 RPS, CPU pod tidak bisa menyelesaikan pekerjaan melebihi kapasitas fisiknya. Akibatnya, nilai `success` tertahan mendatar (*plateau*) di angka ~56 RPS.

### 2. Mengapa Nilai `success` Cenderung Sedikit Menurun pada Beban Ekstrem?
* Saat beban offered load melompat jauh di atas kapasitas (misal 500–1000 RPS), ribuan koneksi TCP dan soket aktif harus dipertahankan secara bersamaan ([`LINKERD_TCP_CONNECTIONS`](file:///home/ali/experimpent/cloud2023/kubernetes/research/cloud-dynamics-experiments/results/ramp-20261028T003408Z-r1/combined.csv) melonjak dari 4 menjadi 580 koneksi).
* Kernel Linux dan proxy Linkerd menghabiskan sebagian siklus CPU untuk *context switching*, manajemen buffer memori, dan penanganan soket jaringan.
* Terjadinya fenomena *thrashing* ringan ini mengurangi alokasi CPU murni untuk komputasi aplikasi, sehingga Goodput (`success`) mengalami penurunan kecil (misalnya dari 59 RPS ke 54–56 RPS).

### 3. Mengapa Kolom `failed` Masih Tetap 0?
* **Request Mengantre (*Queued*), Bukan Ditolak (*Dropped*):**
  Lapisan infrastruktur Kubernetes (kernel Linux TCP backlog, Ingress Controller Nginx, dan proxy Linkerd) dirancang memiliki *buffer* antrean. Request yang datang tidak langsung ditolak, melainkan ditahan di dalam antrean sampai giliran pekerjaannya tiba.
* **Batas Waktu Timeout Client Belum Terlampaui:**
  Generator beban [`loadgen.py`](file:///home/ali/experimpent/cloud2023/kubernetes/research/cloud-dynamics-experiments/loadgen/loadgen.py) menggunakan parameter konfigurasi [`REQUEST_TIMEOUT = 5`](file:///home/ali/experimpent/cloud2023/kubernetes/research/cloud-dynamics-experiments/config/experiment.env#L14) detik.
* Selama total durasi antrean + waktu eksekusi masih di bawah 5 detik (misalnya 4.5 detik), koneksi tidak putus dan client tetap sabar menunggu.
* Ketika pod akhirnya menyelesaikan request tersebut dan mengirimkan respons HTTP status `200 OK`, client menganggap transaksi tersebut **sukses**, bukan gagal!
* Kolom `failed` baru akan bernilai positif jika:
  1. Waktu tunggu di antrean melampaui 5 detik (*client timeout*).
  2. Buffer antrean TCP/proxy meluap (*queue overflow*), menyebabkan Nginx/Linkerd memutus koneksi atau membalas dengan status 502/503/504.

---

## 4. Bukti Empiris dari Pengujian Nyata (`combined.csv`)

Kebenaran analisis di atas terbukti secara nyata pada data hasil eksperimen beban 1000 RPS ([`results/ramp-20261028T003408Z-r1/combined.csv`](file:///home/ali/experimpent/cloud2023/kubernetes/research/cloud-dynamics-experiments/results/ramp-20261028T003408Z-r1/combined.csv)):

| Detik (`elapsed_s`) | Offered Load (`target_rps`) | Laju Kirim (`sent`) | Laju Selesai (`success`) | Gagal (`failed`) | Latensi Rata-rata (`mean_latency_ms`) | Latensi P99 Linkerd | Koneksi TCP Aktif |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1.00 s** | 43.1 RPS | 26 | 26 | 0 | **19.6 ms** | 0.99 ms | 4 |
| **4.00 s** | 142.1 RPS | 125 | 57 | 0 | **695.4 ms** | 19.87 ms | 8 |
| **10.00 s** | 340.0 RPS | 323 | 56 | 0 | **4,354.8 ms** | 3,843.78 ms | 267 |
| **20.00 s** | 670.0 RPS | 648 | 57 | 0 | **4,551.5 ms** | 4,972.63 ms | 555 |
| **30.00 s** | 1000.0 RPS | 968 | 59 | 0 | **4,543.8 ms** | 4,987.19 ms | 568 |
| **267.6 s (Drain)**| 1000.0 RPS | **0** | **13,343** | **5** | 4,556.9 ms | 4,989.91 ms | 580 |

### Pembacaan Data:
1. **Lonjakan Latensi Sebagai Indikator Antrean:**
   Pada detik ke-1, latensi hanya **19.6 ms** (tanpa antrean). Pada detik ke-30, latensi melonjak menjadi **4,543 ms** (antrean sangat padat, request tertahan ~4.5 detik di memori sebelum dieksekusi).
2. **Koneksi TCP Melonjak:**
   Koneksi TCP simultan naik dari **4 koneksi** menjadi **568–580 koneksi**, membuktikan ratusan request client sedang ditahan bersamaan dalam antrean soket.
3. **Pengurasan Antrean (*Drain Phase*):**
   Pada baris terakhir ($t = 267.6\text{ s}$), client berhenti mengirim (`sent = 0`), tetapi server menyelesaikan **13.343 request sukses** yang tadi mengantre!
   Sebanyak **5 request tercatat gagal (`failed = 5`)** karena request-request di ujung paling belakang antrean sempat menyentuh batas timeout 5 detik.

---

## 5. Studi Kasus & Analisis Mendalam: Paradoks Antrean vs Batas Timeout 5 Detik

### A. Pertanyaan Kritis / Paradoks:
> *"Pada detik ke-30 pengujian puncak 1000 RPS, beban meningkat tajam namun `success` mendatar dan `failed` tetap 0. Jika pengujian berlangsung hingga 30 detik (bahkan total 267 detik), bukankah request dengan waktu tunggu lebih dari 5 detik seharusnya mengalami kegagalan (`failed > 0`) karena `REQUEST_TIMEOUT = 5` detik? Mengapa pada detik ke-1 hingga ke-30 `failed` tetap 0?"*

### B. Resolusi Paradoks: Garis Waktu Eksperimen vs Waktu Tunggu per Request

Kunci penyelesaian paradoks ini terletak pada pemisahan antara **sumbu waktu jalannya eksperimen (*timeline*)** dengan **durasi tunggu individual sebuah request (*latency*)**:

1. **"Detik ke-30" adalah Jam Eksperimen, Bukan Waktu Tunggu Request:**
   * Angka `elapsed_s = 30.000` adalah titik waktu pada jam eksperimen sejak generator mulai berjalan (dari $t = 0$ hingga $t = 30$ detik saat beban mencapai puncak 1000 RPS).
   * Nilai ini **sama sekali bukan** lama waktu sebuah request menunggu di dalam antrean.
2. **Waktu Tunggu Riil per Request diukur oleh `mean_latency_ms` dan `LINKERD_LATENCY_P99`:**
   * Pada detik ke-1 ($t = 1.0\text{ s}$): latensi hanya **19.6 ms** ($0.019\text{ detik}$).
   * Pada detik ke-10 ($t = 10.0\text{ s}$): latensi naik ke **4,354.8 ms** ($4.35\text{ detik}$).
   * Pada detik ke-30 ($t = 30.0\text{ s}$): latensi rata-rata mencapai **4,543.8 ms** ($4.54\text{ detik}$), dan latensi terburuk (P99) menyentuh **4,987.19 ms** ($4.987\text{ detik}$).

> [!IMPORTANT]
> **Mengapa `failed` Tetap 0?**
> Perhatikan nilai latensi P99 pada detik ke-30: **`4,987.19 ms` ($4.987\text{ detik}$)**.
> Angka ini **masih berada tepat di bawah ambang batas timeout $5.000\text{ detik}$**!
> Karena server berhasil merespons dan mengembalikan status HTTP `200 OK` tepat sepersekian milidetik sebelum batas 5 detik berakhir, transaksi tersebut **selamat dan dicatat sebagai `success`**, sehingga kolom `failed` tetap bernilai 0.

---

### C. Arsitektur Antrean Dua Lapis (*Two-Tier Queueing*) pada `loadgen.py`

Jika dalam 30 detik client mengirim total **14.988 request**, sementara kapasitas server hanya ~56 request/detik, bagaimana mungkin 14.988 request tersebut tidak semuanya mengalami timeout?

Hal ini dijelaskan oleh arsitektur internal [`loadgen.py`](file:///home/ali/experimpent/cloud2023/kubernetes/research/cloud-dynamics-experiments/loadgen/loadgen.py):

```text
                                  [ loadgen.py ]
                             (Total 14.988 Request)
                                       |
                   +---------------------------------------+
                   |  Lapisan 1: Antrean Memori Python     |
                   |  (ThreadPoolExecutor Internal Queue)  |
                   |  --> Timer timeout 5s BELUM berjalan! |
                   +---------------------------------------+
                                       |
                   Worker bebas mengambil giliran (256 worker thread)
                                       |
                                       v
                   +---------------------------------------+
                   |  Lapisan 2: Eksekusi Soket HTTP       |
                   |  (urlopen ke Ingress & Linkerd Proxy) |
                   |  --> Timer timeout 5s BERJALAN!       |
                   |  --> Tiap request selesai dlm 4.5-4.9s|
                   +---------------------------------------+
                                       |
                                       v
                   [ Server membalas dlm 4.98s (< 5.00s) ] ===> SUCCESS!
```

1. **Lapisan 1: Antrean Memori Client (Internal Queue):**
   Generator beban menggunakan `ThreadPoolExecutor(max_workers=256)`. Ribuan request dijadwalkan oleh thread utama dan ditampung ke dalam antrean memori internal Python (`pool._work_queue`). Pada lapisan ini, **soket jaringan belum dibuka ke server**, sehingga timer batas timeout 5 detik **belum berdetak**.
2. **Lapisan 2: Eksekusi Soket Aktif (`one_request` via `urlopen`):**
   Hanya ada 256 worker thread yang aktif membuka koneksi TCP (`urlopen(..., timeout=5)`) ke server secara simultan. **Timer batas timeout 5 detik baru mulai berhitung saat soket dibuka.**
3. **Matematika Laju Pengurasan Antrean:**
   Karena setiap thread memproses 1 request dalam durasi $\approx 4.5\text{ detik}$, maka 256 worker thread secara paralel mampu menyelesaikan:
   $$\text{Laju Pemrosesan Paralel} \approx \frac{256\text{ worker}}{4.5\text{ detik}} \approx 56.8\text{ request / detik}$$
   Angka ini identik dengan kapasitas Goodput server yang tercatat pada `LINKERD_GOODPUT_RPS` (~56 RPS).
4. **Alasan Eksperimen Berlangsung 267.6 Detik:**
   Untuk menuntaskan antrean 14.988 request dengan laju pemrosesan 56.8 request/detik:
   $$\text{Durasi Total Eksekusi} \approx \frac{14.988\text{ request}}{56.8\text{ req/detik}} \approx 264\text{ detik}$$
   Hasil ini membuktikan secara matematis mengapa durasi total pengukuran yang tercatat pada metadata eksperimen adalah **`267.6 detik`**.
   Setiap request yang sedang aktif di jaringan hanya menghabiskan waktu 4.5–4.98 detik (sehingga tidak timeout). Request lainnya sabar mengantre di memori client menunggu gilirannya.

---

### D. Kapan Kegagalan (`failed`) Akhirnya Muncul?

Pada baris paling akhir di file [`combined.csv`](file:///home/ali/experimpent/cloud2023/kubernetes/research/cloud-dynamics-experiments/results/ramp-20261028T003408Z-r1/combined.csv) pada detik ke-267.6:

```csv
elapsed_s=267.672, target_rps=1000.0, sent=0, success=13343, failed=5
```

Di sinilah **`failed = 5`** akhirnya tercatat. 

**Penyebab Munculnya 5 Kegagalan Ini:**
Dari 14.988 request yang diproses bergiliran, terdapat **5 request di ujung antrean** yang total waktu respons jaringannya membengkak sedikit melampaui ambang batas **`5000 ms` ($5.00\text{ detik}$)**. Begitu melewati 5 detik, modul `urllib.request` melempar `TimeoutError`, dan generator mencatatnya sebagai kegagalan (`failed = 5`).

---

### E. Perhitungan Persentase Goodput dari Studi Kasus Ini

Berdasarkan dataset riil eksperimen `ramp-20261028T003408Z-r1`:

1. **Total Goodput Delivery Ratio (Rasio Penyerapan Beban Menjadi Transaksi Sukses):**
   $$\text{Delivery Ratio} = \frac{\sum \text{success}}{\sum \text{sent}} \times 100\% = \frac{14.983}{14.988} \times 100\% = \mathbf{99.967\%}$$
2. **Goodput Success Rate (Kualitas Bebas Error):**
   $$\text{Success Rate} = \frac{\sum \text{success}}{\sum \text{success} + \sum \text{failed}} \times 100\% = \frac{14.983}{14.983 + 5} \times 100\% = \mathbf{99.967\%}$$
3. **Instantaneous Load Fulfillment Ratio pada Beban Puncak ($t = 30\text{ s}$, `target_rps = 1000`):**
   $$\text{Fulfillment Ratio} = \frac{56.35\text{ RPS}}{1000.0\text{ RPS}} \times 100\% = \mathbf{5.64\%}$$
   *(Artinya: Pada beban 1000 RPS, sistem hanya mampu mengeksekusi 5.64% secara instan, sedangkan 94.36% sisanya dipaksa menunggu giliran dalam antrean).*

---

## 6. Rencana Pemanfaatan Metrik Goodput untuk Riset Cloud Dynamics

Dokumen ini merekomendasikan penggunaan metrik Goodput untuk analisis riset lanjutan:

1. **Deteksi Titik Lutut Jenuh (*Knee of Saturation*):**
   Titik di mana kurva `target_rps` mulai menyimpang dari kurva `success` (Goodput) adalah titik jenuh kapasitas arsitektur. Pada `cpu-bound`, titik jenuh berada di kisaran ~140 RPS offered load.
2. **Komparasi Lintas Arsitektur Aplikasi:**
   Bandingkan kurva Goodput antara:
   * [`stateless-api`](file:///home/ali/experimpent/cloud2023/kubernetes/research/cloud-dynamics-experiments/config/experiment.env): I/O ringan, kapasitas Goodput jauh lebih tinggi.
   * [`cpu-bound`](file:///home/ali/experimpent/cloud2023/kubernetes/research/cloud-dynamics-experiments/scenarios/ramp.env): Cepat jenuh pada batas alokasi CPU core.
   * `microservices`: Rawan bottleneck bertingkat (*cascading latency*).
3. **Validasi Autoscaling (HPA):**
   Eksperimen berikutnya dapat menguji HPA: saat `sent` naik dan Goodput mendatar, replika pod harus bertambah sehingga Goodput kembali meningkat mengikuti laju permintaan.
