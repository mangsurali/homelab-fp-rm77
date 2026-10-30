# Resume Analisis Cloud Dynamics (Dataset Ali v3 - Beban Ekstrem 800 RPS): Penjelasan Sederhana untuk Orang Awam & Audit Kritis Goodput

Dokumen ini menyajikan ringkasan komprehensif hasil uji performa sistem komputasi awan (*Cloud Dynamics Empirical Analysis*) dari notebook [`cloud_dynamics_empirical_analysis_ali_v3.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_ali_v3.ipynb) berbasis data pengukuran empiris riil pada direktori `cloud-dynamics-experiments/res-ali-v3/`.

Dokumen ini disusun dalam dua lapis penjelasan:
1. **Bahasa Populer & Analogi Kehidupan Sehari-hari:** Ditujukan agar fenomena komputasi awan mudah dipahami oleh pengambil keputusan, mahasiswa, atau masyarakat umum tanpa latar belakang teknis mendalam.
2. **Audit Kritis & Analisis Matematis:** Menjawab secara tuntas pertanyaan mendalam mengenai **mengapa Goodput Success Rate tetap tercatat tinggi (~99%) dan latensi rata-rata tercatat di bawah 5 detik, padahal antrean menumpuk hingga 54 menit**.

---

## 1. Analogi Dasar: Apa itu Goodput dan Mengapa Lebih Penting dari Throughput?

Bayangkan sebuah **Dapur Restoran Cepat Saji yang Melayani Pesanan Ojek Online pada Jam Sibuk**:

```text
[Pesanan Ditekan Pelanggan (Offered Load)] ===> [Pesanan Ditampung Kasir (Throughput)] ===> [Makanan Diterima Pelanggan (Goodput)]
        (800 pesanan per detik)                         (625 pesanan ditangani)                     (Hanya 55 porsi sukses!)
                                                                                                   [183.000 pesanan menumpuk di antrean,
                                                                                                    membutuhkan waktu 54 menit untuk tuntas!]
```

1. **Beban yang Diminta (*Offered Load* / `target_rps`):**  
   Berapa banyak pesanan yang dikirimkan oleh ribuan pengguna aplikasi secara serentak per detik.
2. **Kapasitas Proses Jaringan (*Throughput* / `achieved_rps`):**  
   Berapa banyak total pesanan yang berhasil diterima dan sedang sibuk dialirkan oleh soket jaringan per detik (termasuk pesanan yang terlambat, salah saji, atau basi).
3. **Pekerjaan Sukses Produktif (*Goodput* / `success`):**  
   **Ini adalah metrik terpenting dalam industri perangkat lunak modern!** Berapa banyak makanan yang **benar-benar matang tepat waktu, disajikan dengan status HTTP 200 OK, dan dinikmati pelanggan tanpa komplain, error, atau pembatalan**.

> **Pelajaran Kunci untuk Orang Awam:**  
> Dapur yang wajannya mengepul dan kokinya berkeringat (Throughput tinggi) tidak ada gunanya jika makanan baru matang setelah pembeli membatalkan pesanan karena terlalu lama menunggu. Jika server memproses data yang sudah kadaluwarsa, energi listrik dan komputasi tersebut terbuang sia-sia (*wasteful computation*). **Goodput adalah cerminan kepuasan pengguna riil.**

---

## 2. Mengenal 3 Karakter Aplikasi dalam Ujian Skala Ekstrem (800 RPS)

Riset ini menguji 3 jenis aplikasi kontainer di atas kluster Kubernetes Bare-Metal dengan karakteristik komputasi yang sangat kontras:

1. **`stateless-api` (Si Kasir Tol Otomatis Cekatan):**  
   Pekerjaannya sangat ringan dan efisien. Menggunakan model *asynchronous non-blocking I/O*, hemat konsumsi CPU, dan langsung menyelesaikan request dalam hitungan milidetik.
2. **`microservices` (Restoran Berjaringan dengan Pelayan Khusus):**  
   Aplikasi modular yang membagi tugas antara gerbang depan (*frontend*), pemroses logika (*backend*), dan basis data, yang saling terhubung melalui lapisan *service mesh* Linkerd. Memiliki koordinasi rapi, namun rentan mengalami hambatan pada jalur komunikasi antar-kontainer (*hop latency*).
3. **`cpu-bound` (Koki Peracik Bumbu Enkripsi Berat):**  
   Mengerjakan kalkulasi komputasi matematika dan enkripsi intensif yang sangat menguras tenaga prosesor. Kontainer ini dipagari aturan ketat sistem operasi: **hanya dijatah kuota CPU maksimal 0,5 inti prosesor (500m CFS CPU limit)**.

---

## 3. Fakta Empiris di Balik 3 Skenario Pengujian (Dataset Ali v3)

Pengujian pada dataset `res-ali-v3` menguji batas ketahanan sistem pada tingkat beban yang belum pernah diuji sebelumnya (lebih dari **2,17 juta total request** diuji):

### Skenario 1: Beban Konstan Skala Tinggi 100 Pesanan/Detik (`constant`)
Pelanggan datang secara stabil dan teratur dengan kecepatan **100 pesanan per detik** (4x lipat v1, 2x lipat v2) selama 30 detik.

![Uji Beban Konstan Ali v3](../outputs/ali-v3/figures/01_constant_scenario_comparison.png)

* **Hasil Observasi Nyata:**  
  - **`stateless-api`:** Sangat santai. Waktu tunggu rata-rata hanya **4.5 milidetik**, menggunakan hanya 0.027 core CPU, dengan Goodput sempurna di 100 RPS.
  - **`microservices`:** Tetap stabil. Waktu tunggu rata-rata **10.1 milidetik**, menggunakan 0.046 core CPU, Goodput 100% di 100 RPS.
  - **`cpu-bound` (Langsung Mengalami Kolaps):**  
    Karena kapasitas maksimalnya hanya sanggup melayani ~56 pesanan/detik, beban konstan 100 RPS **langsung membuat koki tersedak sejak detik pertama**. Waktu tunggu melonjak drastis ke **3.774,7 milidetik (hampir 4 detik)** dan CPU langsung mentok di batas limit 0.512 core.

---

### Skenario 2: Beban Jam Sibuk Ekstrem Merangkak Naik Hingga 800 Pesanan/Detik (`ramp`)
Beban dinaikkan perlahan dari **10 pesanan/detik merangkak naik hingga 800 pesanan/detik** selama 10 menit (600 detik).

![Uji Kenaikan Beban Bertahap Ramp Ali v3](../outputs/ali-v3/figures/02_ramp_scenario_comparison.png)

* **Terungkapnya 3 Kasta Kapasitas Sistem (*Three-Tier Scalability*):**  
  1. **Kasta Bawah (`cpu-bound` - Panel Tengah):** Sejak awal beban menyentuh **~69 RPS**, koki langsung kehabisan nafas. Mau beban dinaikkan ke 200, 400, atau 800 RPS sekalipun, Goodput-nya tertahan kaku di angka **~55.5 - 56.8 pesanan/detik**, dengan latensi menempel di batas sabar **4.617 milidetik**.
  2. **Kasta Menengah (`microservices` - Panel Bawah):** Mampu mendaki mulus hingga melayani 300 RPS. Namun pada **~340.5 RPS**, koordinasi jaringan Linkerd mulai mengalami persaingan buffer. Goodput mendatar di kisaran **~315 RPS** dengan latensi membengkak ke **850 milidetik**.
  3. **Kasta Tertinggi (`stateless-api` - Panel Atas):** Mampu melesat menembus 400 RPS dan 500 RPS! Pada dataset v3 ini, batas atas kasir cekatan akhirnya terungkap pada **~622.3 RPS**. Di atas angka ini, Goodput mendatar di kisaran **~540 - 601 RPS** karena prosesor menyentuh utilisasi 0.67 core, dengan latensi terkendali di **478 milidetik**.

---

### Skenario 3: Uji Stabilitas Operasional 40 Pesanan/Detik (`burst`)
Sistem diuji pada beban stabil terukur **40 pesanan per detik** selama 600 detik (kondisi di bawah titik jenuh `cpu-bound`).

![Uji Stabilitas Operasional Burst Ali v3](../outputs/ali-v3/figures/03_burst_scenario_comparison.png)

* **Hasil Observasi:**  
  - Ketiga aplikasi melayani beban 40 RPS dengan pemenuhan Goodput 100%.
  - `stateless-api` memiliki latensi dasar 5.7 ms (dengan sesekali lonjakan mikro / *jitter* hingga 243 ms).
  - `microservices` berjalan mulus pada latensi dasar 9.2 ms.
  - `cpu-bound` beroperasi pada latensi dasar 20.4 ms dengan konsumsi CPU terukur 0.33 core.

---

## 4. Titik Jenuh (*Knee of Saturation*): Kurva Tongkat Hoki & 3 Plateau Goodput

Bayangkan sebuah **Jalan Tol Menuju 3 Jenis Gardu Tol**:

![Titik Jenuh Kapasitas Ali v3](../outputs/ali-v3/figures/04_knee_of_saturation_curves.png)

1. **Kurva Tongkat Hoki (*Hockey-Stick Latency* - Grafik Atas):**  
   - `cpu-bound` menekuk paling awal di titik merah (**69.3 RPS**), di mana latensi langsung melonjak eksponensial ke ribuan milidetik.
   - `microservices` menekuk di titik hijau (**340.5 RPS**).
   - `stateless-api` menekuk paling akhir di titik biru (**622.3 RPS**).
2. **Tiga Dataran Goodput (*Goodput Plateaus* - Grafik Bawah):**  
   Grafik bawah memperlihatkan batas fisik layanan masing-masing arsitektur:
   - Garis merah (`cpu-bound`) mendatar di **~56 RPS**.
   - Garis hijau (`microservices`) mendatar di **~315 RPS**.
   - Garis biru (`stateless-api`) mendatar di **~540 - 600 RPS**.

---

## 5. Tiga Serangkai: Jurang Pemborosan Energi Komputasi (*Saturation Gap*)

Grafik berikut membedah hubungan antara **Offered Load** (garis putus-putus hitam), **Throughput** (garis oranye), dan **Goodput** (garis tebal berwarna):

![Tiga Serangkai Goodput Ali v3](../outputs/ali-v3/figures/05_goodput_triad_and_fulfillment.png)

* **Jurang Penumpukan Antrean Terbesar dalam Sejarah Pengujian:**  
  Pada grafik tengah (`cpu-bound`), area berbayang merah adalah **jurang pemborosan sistem**.
  - Beban yang diminta client (garis hitam) meroket hingga 800 RPS.
  - Goodput yang dihasilkan server (garis merah) tertahan di bawah 57 RPS.
  - Seluruh area di antara kedua garis tersebut mencerminkan **lebih dari 180.000 transaksi yang tertahan mengambang di antrean penyangga sistem**.

---

## 6. Dinamika Antrean Backpressure & Fase Pengurasan Ekstrem (*Drain Phase*)

Salah satu fenomena paling dramatis dalam pengujian Ali v3 adalah fenomena pengurasan antrean pasca-uji:

![Dinamika Antrean dan Pengurasan Ali v3](../outputs/ali-v3/figures/06_queue_backpressure_and_drain_dynamics.png)

1. **Gunung Antrean In-Flight (Grafik Atas):**  
   Selama eskalasi beban menuju 800 RPS (0 hingga 600 detik):
   - `cpu-bound` menimbun antrean raksasa: **183.020 pesanan mengantre di memori (*in-flight*)**!
   - `microservices` menimbun **69.336 pesanan**.
   - `stateless-api` hanya menimbun **1.834 pesanan**.
2. **Fase Pengurasan (*Drain Phase*):**  
   - Ketika pengujian selesai di detik ke-600 dan generator berhenti mengirim beban baru (`sent = 0`):
   - **`stateless-api`:** Menguras 1.834 pesanannya dalam tempo sangat kilat **3,2 detik** pada laju 541 RPS.
   - **`microservices`:** Menguras 69.336 pesanannya dalam waktu **217,2 detik (3,6 menit)** pada laju stabil 316.6 RPS.
   - **`cpu-bound`:** Membutuhkan waktu **3.267,7 detik (54,5 menit / hampir 1 jam)** hanya untuk menuntaskan tumpukan 183.000 pesanan tersebut pada laju stabil 55.5 RPS!

---

## 7. Rangkuman Pemeringkatan Kinerja Goodput Lintas Arsitektur

Berdasarkan seluruh hasil observasi empiris pada dataset Ali v3, berikut adalah pemeringkatan ketahanan sistem:

| Peringkat | Arsitektur Aplikasi | Kapasitas Puncak Goodput | Latensi Beban Puncak | Delivery Ratio (%) | Success Rate (%) | Kesimpulan dalam Bahasa Awam |
| :---: | :--- | :---: | :---: | :---: | :---: | :--- |
| 🥇 **1** | **`stateless-api`** | **~540 - 622 RPS** | **478.4 ms** (800 RPS) | **99.86%** | **99.86%** | **Juara Mutlak:** Mampu melayani beban hingga 622 RPS sebelum saturasi CPU event loop. Menguras 1.834 antrean hanya dalam 3,2 detik. |
| 🥈 **2** | **`microservices`** | **~315 - 340.5 RPS** | **850.1 ms** (800 RPS) | **99.46%** | **99.46%** | **Tangguh Menengah:** Menangani beban hingga ~340 RPS secara stabil sebelum saturasi hop jaringan Linkerd. Menguras 69.336 antrean dalam 3,6 menit. |
| 🥉 **3** | **`cpu-bound`** | **~55.5 - 56.8 RPS** | **4,617.1 ms** (800 RPS) | **98.98%** | **98.98%** | **Ketat Dibatasi Kuota:** Jenuh pada ~69 RPS akibat batas CFS 0.5 core. Menimbun antrean raksasa 183.000 request dan butuh waktu 54 menit untuk fase drain. |

---

## 8. Audit Kritis: Mengapa Goodput Success Rate Masih Tinggi (~99%) dan Latensi < 5 Detik Padahal Antrean Mengular 54 Menit?

Bagian ini secara khusus membedah pertanyaan kritis yang diajukan:
> *"Secara nalar, jika antrean menumpuk hingga 183.000 request dan waktu pengurasan (drain) membutuhkan 54 menit, bukankah waktu tunggu setiap request yang berada di dalam antrean seharusnya jauh melampaui batas toleransi 5 detik? Mengapa data menunjukkan latensi rata-rata masih di bawah 5 detik (4.617 ms) dan Success Rate tetap sangat tinggi (98.98%)? Ke mana hilangnya respon kegagalan tersebut?"*

Berikut adalah analisis kritis berbasis data, kode sumber pengujian, dan prinsip saintifik rekayasa sistem terdistribusi:

### 8.1 Evaluasi Kritis Terhadap Analisa Pribadi Anda: Apakah Analisa Anda Benar?

> **Jawaban Tegas:**  
> **ANALISA ANDA 100% SANGAT TEPAT DARI SUDUT PANDANG REALITA SISTEM PRODUKSI DAN PENGALAMAN PENGGUNA (*END-TO-END USER PERSPECTIVE*)!**

Secara nalar rekayasa perangkat lunak (*software engineering*):
1. Jika seorang pelanggan mengirim pesanan pada menit ke-5 pengujian, dan pesanan tersebut berada di urutan antrean ke-100.000, maka dengan kecepatan koki memasak $55.5\text{ pesanan/detik}$, pesanan tersebut secara fisik baru akan mulai dimasak pada:
   $$T_{\text{tunggu}} = \frac{100.000}{55.5} \approx 1.801\text{ detik (30 menit kemudian)!}$$
2. Jika aplikasi pelanggan (misal aplikasi mobile banking atau e-commerce) memiliki batas sabar (*timeout*) 5 detik, maka pada detik ke-5.001 pelanggan sudah pasti membatalkan pesanan atau menerima layar error (*Connection Timed Out*).
3. Maka di dunia nyata, **seluruh 183.000 request tersebut SEHARUSNYA 100% GAGAL / TIMEOUT**, dan Goodput riil seharusnya **anjlok mendekati 0% (*Goodput Collapse*)**.

Lantas, **mengapa data hasil pengujian mencatat Success Rate 98.98% dan latensi rata-rata hanya 4.6 detik?**  
Berikut adalah pembuktian akar masalahnya (*root cause*) langsung dari kode sumber sistem:

---

### 8.2 Pembedahan Fakta Kode Sumber: Fenomena *Client-Side Queueing Blindness* pada `loadgen.py`

Ketika kita membedah file generator beban [`kubernetes/research/cloud-dynamics-experiments/loadgen/loadgen.py`](file:///home/ali/kuliah/homelab-fp-rm77/kubernetes/research/cloud-dynamics-experiments/loadgen/loadgen.py), kita menemukan rahasia mekanis di balik anomali ini:

#### 1. Mekanisme Internal `ThreadPoolExecutor(max_workers=256)`
Pada baris 29 dan 89 file `loadgen.py`:
```python
p.add_argument("--workers", type=int, default=256)
...
with ThreadPoolExecutor(max_workers=a.workers) as pool:
    while True:
        ...
        futures.append(pool.submit(one_request, a.url, a.timeout))
```
- Generator beban menggunakan **kolam thread pekerja (*thread pool*) yang dibatasi hanya 256 pekerja (`workers=256`)**.
- Ketika generator mencoba menembakkan beban hingga 800 RPS, ke-256 pekerja tersebut langsung sibuk melayani 256 koneksi pertama.
- **Di mana 183.000 request sisanya berada?**  
  Request-request tersebut **TIDAK PERNAH DIKIRIMKAN KE JARINGAN KUBERNETES!** Mereka tertahan di dalam memori internal Python milik program penguji (*client-side in-memory queue* `queue.SimpleQueue`).

#### 2. Kapan Timer Latensi dan Timer Timeout Sebenarnya Dimulai?
Mari kita lihat fungsi `one_request()` pada baris 56-66 `loadgen.py`:
```python
def one_request(url, timeout):
    t0 = time.perf_counter()  # <--- TIMER BARU BERJALAN DI SINI!
    ok = False
    try:
        req = Request(url, headers={"User-Agent": "cloud-dynamics-stage3/1.0"})
        with urlopen(req, timeout=timeout) as r:  # <--- TIMEOUT SOCKET DIMULAI DI SINI!
            r.read(1)
            ok = 200 <= getattr(r, "status", 200) < 400
    except (URLError, HTTPError, TimeoutError, OSError):
        ok = False
    return ok, (time.perf_counter() - t0) * 1000.0
```
Perhatikan fakta krusial ini:
- `t0 = time.perf_counter()` **BARU DIEKSEKUSI saat salah satu dari 256 thread pekerja mengambil request tersebut dari antrean memori internal Python!**
- Parameter `timeout=5` pada `urlopen()` adalah **socket network timeout** (waktu tunggu soket TCP sejak koneksi dikirim ke jaringan hingga server merespons).
- **Waktu tunggu antrean selama puluhan menit di dalam memori Python client SAMA SEKALI TIDAK DIHITUNG ke dalam latensi**, dan **TIDAK PERNAH DIKENAI TIMEOUT 5 DETIK!**

---

### 8.3 Pembuktian Matematis: Mengapa Latensi Rata-rata Persis Berada di Angka ~4.6 Detik?

Mengapa latensi yang tercatat pada `cpu-bound` saat beban 800 RPS bernilai rata-rata **4.617 milidetik** (tepat di bawah 5.0 detik)?

Kita dapat membuktikannya menggunakan **Hukum Little (*Little's Law*)**:
$$L = \lambda \cdot W \implies W = \frac{L}{\lambda}$$
Di mana:
- $L$ adalah jumlah request simultan yang aktif di jaringan, yang dibatasi oleh ukuran thread pool client: $L = 256\text{ workers}$.
- $\lambda$ (atau kapasitas layanan $\mu$) dari pod `cpu-bound` pada kuota CPU 0.5 core: $\mu \approx 55.6\text{ req/detik}$.

Maka waktu respons soket jaringan $W$ secara matematis adalah:
$$W = \frac{256 \text{ worker}}{55.6 \text{ req/s}} = \mathbf{4.604 \text{ detik!}}$$

> **Fakta Keras Data:**  
> Angka **4.604 detik** hasil kalkulasi Hukum Little identik dengan data empiris yang tercatat di tabel `03_ramp_progression_checkpoints.csv`, yaitu **4.612 ms** pada 100 RPS dan **4.617 ms** pada 800 RPS!  
> Karena soket jaringan hanya membutuhkan waktu ~4.6 detik, maka bagi fungsi `urlopen(timeout=5)`, request tersebut **LOLOS DARI TIMEOUT (4.6 detik < 5.0 detik)**. Inilah penyebab mengapa respon kegagalan tidak pernah muncul di laporan per-detik!

---

### 8.4 Mengapa Respon Sukses Bisa Tuntas di Fase Drain (3.267 Detik)?

Pada baris 128 `loadgen.py`:
```python
# Wait for outstanding requests, but do not extend offered-load scheduling.
results = [f.result() for f in futures]
```
Ketika waktu uji 600 detik habis, generator tidak membatalkan request-request yang masih mengantre di memori. Generator dengan sabar menunggu ke-256 pekerjanya menyelesaikan seluruh 183.000 tugas yang tertinggal.
- Karena pengujian beban luar sudah berhenti ($\lambda_{\text{masuk}} = 0$), server pod tidak menerima beban baru dan dapat memproses antrean dengan tenang pada kecepatan penuh $\mu = 55.5\text{ RPS}$.
- Waktu yang dibutuhkan adalah:
  $$T_{\text{drain}} = \frac{181.400 \text{ request}}{55.5 \text{ req/s}} \approx \mathbf{3.268 \text{ detik (54.5 menit)}}.$$
- Setiap kali pekerja mengambil tugas dari antrean, pekerja membuka koneksi soket baru, menunggu 4.6 detik, menerima HTTP 200 OK, dan mencatatnya sebagai `success`.
- Ketika seluruh 181.400 request selesai di menit ke-54, baris terakhir file `combined.csv` mencatat:
  `elapsed_s = 3867.683, sent = 0, success = 181400, failed = 1620, mean_latency_ms = 4570.613`.

---

### 8.5 Kesimpulan Saintifik: Fenomena *Coordinated Omission*

Anomali yang Anda temukan secara cerdas ini adalah salah satu topik paling terkenal dalam literatur rekayasa performa sistem komputer, yang disebut oleh pakar sistem terdistribusi Gil Tene sebagai:

$$\textbf{"Coordinated Omission (Kebutaan Antrean Sisi Klien)"}$$

| Perspektif Evaluasi | Realita Pengguna Lapangan (Analisa Anda) | Hasil Rekaman Alat Uji (`loadgen.py`) |
| :--- | :--- | :--- |
| **Waktu Tunggu Total** | **~54 Menit (3.267 detik)** sejak request dijadwalkan. | **~4.6 Detik** (hanya menghitung waktu sejak thread mengirim soket). |
| **Status Transaksi** | **100% GAGAL / TIMEOUT** (pengguna sudah menutup aplikasi setelah 5 detik). | **98.98% SUKSES** (karena thread memproses tuntas hingga menit ke-54). |
| **Penyebab Utama** | Klien dunia nyata tidak mengantre secara terkoordinasi di belakang 256 worker. | Alat uji menahan request di antrean memori internal sebelum menyentuh jaringan. |

#### Rekomendasi Perbaikan Pengujian Masa Depan (*Open-Loop Testing*):
Agar hasil pengujian di laboratorium mencerminkan realita lapangan yang Anda maksudkan:
1. **Penerapan *Schedule-Time Latency Tracking*:** Latensi harus dihitung sejak `timestamp` jadwal kedatangan request ditetapkan, bukan saat fungsi `urlopen()` dipanggil.
2. **Penerapan *Drop-on-Timeout di Sisi Klien*:** Jika sebuah request telah mengantre di memori internal melebihi `a.timeout` (5 detik), request tersebut wajib langsung dibatalkan (*canceled*) dan dicatat sebagai `failed` tanpa pernah dikirimkan ke server.
3. **Penerapan *Fail-Fast Rate Limiting* (`limit_req ... nodelay`) di Ingress:** Server wajib secara aktif menolak request berlebih dengan kode HTTP 429 dalam tempo $< 1\text{ ms}$, sehingga antrean raksasa tidak pernah terbentuk di mana pun.
