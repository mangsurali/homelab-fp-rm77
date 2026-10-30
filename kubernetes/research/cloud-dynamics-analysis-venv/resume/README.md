# Kumpulan Resume Analisis Cloud Dynamics (Penjelasan untuk Orang Awam)

Direktori ini berisi dokumen ringkasan (*executive summary*) berbasis data empiris dari pengujian kinerja sistem terdistribusi di Kubernetes. Dokumen disusun khusus menggunakan bahasa populer dan analogi sehari-hari agar mudah dipahami oleh masyarakat umum, mahasiswa, maupun manajemen/stakeholder non-teknis.

---

## Daftar Dokumen Resume per Notebook

1. **[Resume Analisis Dataset Ali v3 (`resume_cloud_dynamics_empirical_analysis_ali_v3.md`)](./resume_cloud_dynamics_empirical_analysis_ali_v3.md)** *(Beban Ekstrem 800 RPS & Audit Kritis Goodput)*  
   - **Sumber Data:** `cloud-dynamics-experiments/res-ali-v3/` (21 eksperimen, 2,17 juta request)  
   - **Notebook Acuan:** [`cloud_dynamics_empirical_analysis_ali_v3.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_ali_v3.ipynb)  
   - **Grafik Terkait:** `outputs/ali-v3/figures/` (300 DPI)  
   - **Fokus Fenomena:** Menyoroti uji kapasitas ekstrem hingga 800 RPS yang mengungkap tiga tingkatan saturasi (`stateless-api` ~622 RPS, `microservices` ~340 RPS, `cpu-bound` ~69 RPS), akumulasi antrean masif 183.020 request dengan fase drain 54 menit, serta **audit kritis saintifik membedah fenomena Coordinated Omission pada load generator** yang menjelaskan mengapa Goodput success rate tetap tercatat 98.98% dengan latensi soket 4.6 detik.

2. **[Resume Analisis Dataset Ali v2 (`resume_cloud_dynamics_empirical_analysis_ali_v2.md`)](./resume_cloud_dynamics_empirical_analysis_ali_v2.md)** *(Skala Tinggi 400 RPS)*  
   - **Sumber Data:** `cloud-dynamics-experiments/res-ali-v2/` (21 eksperimen)  
   - **Notebook Acuan:** [`cloud_dynamics_empirical_analysis_ali_v2.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_ali_v2.ipynb)  
   - **Grafik Terkait:** `outputs/ali-v2/figures/` (300 DPI)  
   - **Fokus Fenomena:** Menyoroti uji kapasitas ekstrem (ramp hingga 400 RPS, burst 300 RPS), titik jenuh multi-arsitektur (`stateless-api` bebas jenuh > 400 RPS, `microservices` jenuh di ~327 RPS, `cpu-bound` jenuh di ~68 RPS), penumpukan antrean masif 28.769 request pada `cpu-bound` dengan durasi drain 555 detik (9 menit), serta analisis kritis mendalam terkait strategi `limit_req` dengan `nodelay` pada Ingress Gateway.

3. **[Resume Analisis Dataset Ali (`resume_cloud_dynamics_empirical_analysis_ali.md`)](./resume_cloud_dynamics_empirical_analysis_ali.md)**  
   - **Sumber Data:** `cloud-dynamics-experiments/res-ali/` (21 eksperimen)  
   - **Notebook Acuan:** [`cloud_dynamics_empirical_analysis_ali.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_ali.ipynb)  
   - **Grafik Terkait:** `outputs/ali/figures/` (300 DPI)  
   - **Fokus Fenomena:** Menyoroti stabilitas pengujian 21 run empiris, titik tekuk jenuh (*knee of saturation*) pada `cpu-bound` di angka ~57–64 RPS akibat pembatasan kuota CFS CPU 0.5 core, lonjakan latensi mendekati batas timeout 5 detik (4.677 ms), penumpukan antrean in-flight mencapai 11.168 request, serta durasi pengurasan (*drain phase*) pasca-burst selama 170 detik.

4. **[Resume Analisis Dataset Taufik (`resume_cloud_dynamics_empirical_analysis_taufik.md`)](./resume_cloud_dynamics_empirical_analysis_taufik.md)**  
   - **Sumber Data:** `cloud-dynamics-experiments/res-taufik/`  
   - **Notebook Acuan:** [`cloud_dynamics_empirical_analysis_taufik.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_taufik.ipynb)  
   - **Grafik Terkait:** `outputs/taufik/figures/` (300 DPI)  
   - **Fokus Fenomena:** Menyoroti perbandingan antara arsitektur modular (`microservices/frontend` vs `backend`) dan fenomena bencana antrean pada `cpu-bound` saat waktu tunggu menembus 8 detik sehingga memicu kegagalan massal (*mass timeout* hingga 55.853 request gagal).

5. **[Resume Analisis Dataset res-fix (`resume_cloud_dynamics_empirical_analysis.md`)](./resume_cloud_dynamics_empirical_analysis.md)**  
   - **Sumber Data:** `cloud-dynamics-experiments/res-fix/`  
   - **Notebook Acuan:** [`cloud_dynamics_empirical_analysis.ipynb`](../notebooks/cloud_dynamics_empirical_analysis.ipynb)  
   - **Grafik Terkait:** `outputs/figures/` (300 DPI)  
   - **Fokus Fenomena:** Membedah kestabilan baseline, respons terhadap lonjakan beban seketika, dan perbandingan pemanfaatan kapasitas lintas kontainer.

---

## Perbandingan Cepat Karakteristik Antar Dataset

| Parameter Evaluasi | Dataset `res-ali-v3` (Beban Ekstrem 800 RPS) | Dataset `res-ali-v2` (Skala Tinggi 400 RPS) | Dataset `res-ali` (Notebook Ali v1) | Dataset `res-taufik` (Notebook Taufik) |
| :--- | :--- | :--- | :--- | :--- |
| **Beban Pengujian** | Constant: 100 RPS, Ramp: 10-800 RPS, Burst: 40 RPS | Constant: 50 RPS, Ramp: 10-400 RPS, Burst: 300 RPS | Constant: 25 RPS, Ramp: 10-200 RPS, Burst: 150 RPS | Constant: 25 RPS, Ramp: 10-200 RPS, Burst: 150 RPS |
| **Karakteristik Antrean `cpu-bound`** | Antrean menumpuk raksasa hingga **183.020 request**; durasi drain **3.267 detik (54,5 menit)**. | Antrean menumpuk ekstrem hingga **28.769 request**; latensi menyentuh **4.758 ms**; durasi drain **555 detik** (9 menit). | Antrean menumpuk hingga 11.168 request; latensi menyentuh **4.677 ms**; durasi drain **170 detik**. | Antrean meluap hingga waktu tunggu tembus **8.280 ms** (melampaui batas toleransi 5.0 detik). |
| **Tingkat Keberhasilan `cpu-bound`** | **98.98%** (karena generator menunggu tuntas 54 menit akibat Coordinated Omission). | **99.84%** (drained hingga tuntas pasca-tes). | **99.63%** (hanya 10 request gagal timeout di saat puncak burst). | **42.92%** (terjadi kegagalan massal hingga 55.853 request gagal akibat timeout panjang). |
| **Perilaku `microservices`** | Mengungkap batas jenuh di **~340.5 RPS**; antrean menumpuk 69.336 request (drain 3,6 menit). | Tangguh hingga **~326.9 RPS**; di atas itu terjadi latensi cascading (687.8 ms) dan 2.169 request gagal. | Sukses mengantar **100.00%** Goodput tanpa jenuh hingga 200 RPS. | Dipantau spesifik per sub-komponen: `frontend` (0.54c) vs `backend` (0.33c). |
| **Ketahanan `stateless-api`** | Mengungkap batas jenuh atas di **~622.3 RPS** (latensi 478 ms pada 800 RPS; drain 3,2 detik). | Sangat tangguh (**> 400 RPS**, latensi rata-rata **80.9 ms**, **99.998%** Delivery Ratio). | Sangat tangguh (> 200 RPS, latensi rata-rata < 25 ms, **100.00%** Goodput). | Sangat tangguh (> 200 RPS, latensi stabil, 99.96% sukses). |
