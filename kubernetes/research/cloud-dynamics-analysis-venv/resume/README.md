# Kumpulan Resume Analisis Cloud Dynamics (Penjelasan untuk Orang Awam)

Direktori ini berisi dokumen ringkasan (*executive summary*) berbasis data empiris dari pengujian kinerja sistem terdistribusi di Kubernetes. Dokumen disusun khusus menggunakan bahasa populer dan analogi sehari-hari agar mudah dipahami oleh masyarakat umum, mahasiswa, maupun manajemen/stakeholder non-teknis.

---

## Daftar Dokumen Resume per Notebook

1. **[Resume Analisis Dataset Ali v5 (`resume_cloud_dynamics_empirical_analysis_ali_v5.md`)](./resume_cloud_dynamics_empirical_analysis_ali_v5.md)** *(Skalabilitas Moderat 200 RPS & Guncangan Dinamis 150 RPS Open-Loop)*  
   - **Sumber Data:** `cloud-dynamics-experiments/res-ali-v5/` (21 eksperimen)  
   - **Notebook Acuan:** [`cloud_dynamics_empirical_analysis_ali_v5.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_ali_v5.ipynb)  
   - **Grafik Terkait:** `outputs/ali-v5/figures/` (300 DPI)  
   - **Fokus Fenomena:** Meneliti rentang beban operasional moderat dengan generator terbuka `loadgen_v2.py`. Membuktikan keunggulan absolut `microservices` (100% sukses sempurna di seluruh 147.000+ request tanpa 1 pun error, latensi 8 ms), latensi intrinsik dasar bebas jenuh pada 25 RPS (stateless 4,0 ms, microservices 8,1 ms, cpu-bound 18,9 ms), serta **uji ketahanan guncangan dinamis tiga fase (10 $\to$ 150 $\to$ 10 RPS)** yang membuktikan kemampuan pemulihan cepat (*fast self-healing recovery*) pada `cpu-bound` dalam tempo 20 detik setelah lonjakan mereda.

2. **[Resume Analisis Dataset Ali v4 (`resume_cloud_dynamics_empirical_analysis_ali_v4.md`)](./resume_cloud_dynamics_empirical_analysis_ali_v4.md)** *(Beban Ekstrem 800 RPS Open-Loop & Pembongkaran Realita Kegagalan)*  
   - **Sumber Data:** `cloud-dynamics-experiments/res-ali-v4/` (21 eksperimen)  
   - **Notebook Acuan:** [`cloud_dynamics_empirical_analysis_ali_v4.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_ali_v4.ipynb)  
   - **Grafik Terkait:** `outputs/ali-v4/figures/` (300 DPI)  
   - **Fokus Fenomena:** Terobosan metodologi pengujian menggunakan model *open-loop* non-blocking (`loadgen_v2.py`) yang **mengeliminasi Coordinated Omission total**. Pengujian ini mengungkap kegagalan nyata (*real timeout failures*): `cpu-bound` menolak 213.308 request (87,8% gagal) karena kuota 0,5 core dengan batas waktu deadline 5,0 detik, `microservices` gagal 97.337 request di atas 348 RPS, penumpukan soket in-flight stabil di 450–620 koneksi, dan **fase drain tuntas bersih dalam $\le 5$ detik** (tanpa antrean siluman 54 menit).

3. **[Resume Analisis Dataset Ali v3 (`resume_cloud_dynamics_empirical_analysis_ali_v3.md`)](./resume_cloud_dynamics_empirical_analysis_ali_v3.md)** *(Beban Ekstrem 800 RPS Closed-Loop & Audit Kritis Coordinated Omission)*  
   - **Sumber Data:** `cloud-dynamics-experiments/res-ali-v3/` (21 eksperimen, 2,17 juta request)  
   - **Notebook Acuan:** [`cloud_dynamics_empirical_analysis_ali_v3.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_ali_v3.ipynb)  
   - **Grafik Terkait:** `outputs/ali-v3/figures/` (300 DPI)  
   - **Fokus Fenomena:** Menyoroti uji kapasitas ekstrem hingga 800 RPS yang mengungkap tiga tingkatan saturasi (`stateless-api` ~622 RPS, `microservices` ~340 RPS, `cpu-bound` ~69 RPS), akumulasi antrean masif 183.020 request dengan fase drain 54 menit, serta **audit kritis saintifik membedah fenomena Coordinated Omission pada load generator v1** yang menjelaskan mengapa Goodput success rate tetap tercatat 98.98% dengan latensi soket 4.6 detik.

4. **[Resume Analisis Dataset Ali v2 (`resume_cloud_dynamics_empirical_analysis_ali_v2.md`)](./resume_cloud_dynamics_empirical_analysis_ali_v2.md)** *(Skala Tinggi 400 RPS)*  
   - **Sumber Data:** `cloud-dynamics-experiments/res-ali-v2/` (21 eksperimen)  
   - **Notebook Acuan:** [`cloud_dynamics_empirical_analysis_ali_v2.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_ali_v2.ipynb)  
   - **Grafik Terkait:** `outputs/ali-v2/figures/` (300 DPI)  
   - **Fokus Fenomena:** Menyoroti uji kapasitas ekstrem (ramp hingga 400 RPS, burst 300 RPS), titik jenuh multi-arsitektur (`stateless-api` bebas jenuh > 400 RPS, `microservices` jenuh di ~327 RPS, `cpu-bound` jenuh di ~68 RPS), penumpukan antrean masif 28.769 request pada `cpu-bound` dengan durasi drain 555 detik (9 menit), serta analisis kritis mendalam terkait strategi `limit_req` dengan `nodelay` pada Ingress Gateway.

5. **[Resume Analisis Dataset Ali (`resume_cloud_dynamics_empirical_analysis_ali.md`)](./resume_cloud_dynamics_empirical_analysis_ali.md)**  
   - **Sumber Data:** `cloud-dynamics-experiments/res-ali/` (21 eksperimen)  
   - **Notebook Acuan:** [`cloud_dynamics_empirical_analysis_ali.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_ali.ipynb)  
   - **Grafik Terkait:** `outputs/ali/figures/` (300 DPI)  
   - **Fokus Fenomena:** Menyoroti stabilitas pengujian 21 run empiris, titik tekuk jenuh (*knee of saturation*) pada `cpu-bound` di angka ~57–64 RPS akibat pembatasan kuota CFS CPU 0.5 core, lonjakan latensi mendekati batas timeout 5 detik (4.677 ms), penumpukan antrean in-flight mencapai 11.168 request, serta durasi pengurasan (*drain phase*) pasca-burst selama 170 detik.

6. **[Resume Analisis Dataset Taufik (`resume_cloud_dynamics_empirical_analysis_taufik.md`)](./resume_cloud_dynamics_empirical_analysis_taufik.md)**  
   - **Sumber Data:** `cloud-dynamics-experiments/res-taufik/`  
   - **Notebook Acuan:** [`cloud_dynamics_empirical_analysis_taufik.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_taufik.ipynb)  
   - **Grafik Terkait:** `outputs/taufik/figures/` (300 DPI)  
   - **Fokus Fenomena:** Menyoroti perbandingan antara arsitektur modular (`microservices/frontend` vs `backend`) dan fenomena bencana antrean pada `cpu-bound` saat waktu tunggu menembus 8 detik sehingga memicu kegagalan massal (*mass timeout* hingga 55.853 request gagal).

7. **[Resume Analisis Dataset res-fix (`resume_cloud_dynamics_empirical_analysis.md`)](./resume_cloud_dynamics_empirical_analysis.md)**  
   - **Sumber Data:** `cloud-dynamics-experiments/res-fix/`  
   - **Notebook Acuan:** [`cloud_dynamics_empirical_analysis.ipynb`](../notebooks/cloud_dynamics_empirical_analysis.ipynb)  
   - **Grafik Terkait:** `outputs/figures/` (300 DPI)  
   - **Fokus Fenomena:** Membedah kestabilan baseline, respons terhadap lonjakan beban seketika, dan perbandingan pemanfaatan kapasitas lintas kontainer.

---

## Perbandingan Cepat Karakteristik Antar Dataset

| Parameter Evaluasi | Dataset `res-ali-v5` (Moderat 200 RPS & Shock 150 RPS) | Dataset `res-ali-v4` (Open-Loop 800 RPS) | Dataset `res-ali-v3` (Closed-Loop 800 RPS) | Dataset `res-ali-v2` (Closed-Loop 400 RPS) |
| :--- | :--- | :--- | :--- | :--- |
| **Model Generator** | `loadgen_v2.py` (Open-Loop, Strict Deadline Timeout 5s) | `loadgen_v2.py` (Open-Loop, Strict Deadline Timeout 5s) | `loadgen.py` (Closed-Loop 256 Threads, Coordinated Omission) | `loadgen.py` (Closed-Loop 256 Threads) |
| **Beban Pengujian** | Constant: 25 RPS, Ramp: 10-200 RPS, Burst: 10-150-10 RPS | Constant: 100 RPS, Ramp: 10-800 RPS, Burst: 40 RPS | Constant: 100 RPS, Ramp: 10-800 RPS, Burst: 40 RPS | Constant: 50 RPS, Ramp: 10-400 RPS, Burst: 300 RPS |
| **Tingkat Sukses `cpu-bound`** | **48,91%** pada Ramp 200 RPS; **100%** pada Constant 25 RPS. | **12,22%** pada Ramp 800 RPS; **46,8%** pada Constant 100 RPS (213k gagal). | **98,98%** semu (karena antrean ditahan di RAM klien hingga 54 menit). | **99,84%** semu (drained pasca-tes 9 menit). |
| **Dinamika Antrean & Drain** | Soket in-flight stabil $\le 285$; drain tuntas **5 detik**; pemulihan burst **20 detik**. | Soket in-flight stabil di 450–620; drain tuntas **$\le 5$ detik**. | Antrean menumpuk di memori hingga **183.020 req**; drain **54,5 menit**. | Antrean menumpuk **28.769 req**; drain **9 menit**. |
| **Perilaku `microservices`** | **100,00% Sempurna (0 failed)** di seluruh 147.000+ request; latensi 8 ms. | Menolak 97.337 request di atas 348 RPS (**59,81%** Delivery Ratio). | Mengungkap batas jenuh di **~340.5 RPS**; antrean 69.336 req (drain 3,6 menit). | Tangguh hingga **~326.9 RPS**; di atas itu latensi membengkak ke 687 ms. |
| **Ketahanan `stateless-api`** | Sangat prima (**98,44% – 100%** sukses, latensi rata-rata $\sim 4\text{ ms}$). | Sangat tangguh (**91,93%** Delivery Ratio pada eskalasi 800 RPS). | Mengungkap batas jenuh di **~622.3 RPS** (latensi 478 ms pada 800 RPS). | Sangat tangguh (> 400 RPS, latensi rata-rata 80.9 ms, 99.998% sukses). |
