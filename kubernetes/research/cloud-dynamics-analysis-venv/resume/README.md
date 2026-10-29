# Kumpulan Resume Analisis Cloud Dynamics (Penjelasan untuk Orang Awam)

Direktori ini berisi dokumen ringkasan (*executive summary*) berbasis data empiris dari pengujian kinerja sistem terdistribusi di Kubernetes. Dokumen disusun khusus menggunakan bahasa populer dan analogi sehari-hari agar mudah dipahami oleh masyarakat umum, mahasiswa, maupun manajemen/stakeholder non-teknis.

---

## Daftar Dokumen Resume per Notebook

1. **[Resume Analisis Dataset Ali (`resume_cloud_dynamics_empirical_analysis_ali.md`)](./resume_cloud_dynamics_empirical_analysis_ali.md)**  
   - **Sumber Data:** `cloud-dynamics-experiments/res-ali/` (21 eksperimen)  
   - **Notebook Acuan:** [`cloud_dynamics_empirical_analysis_ali.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_ali.ipynb)  
   - **Grafik Terkait:** `outputs/ali/figures/` (300 DPI)  
   - **Fokus Fenomena:** Menyoroti stabilitas pengujian 21 run empiris, titik tekuk jenuh (*knee of saturation*) pada `cpu-bound` di angka ~57–64 RPS akibat pembatasan kuota CFS CPU 0.5 core, lonjakan latensi mendekati batas timeout 5 detik (4.677 ms), penumpukan antrean in-flight mencapai 11.168 request, serta durasi pengurasan (*drain phase*) pasca-burst selama 170 detik.

2. **[Resume Analisis Dataset Taufik (`resume_cloud_dynamics_empirical_analysis_taufik.md`)](./resume_cloud_dynamics_empirical_analysis_taufik.md)**  
   - **Sumber Data:** `cloud-dynamics-experiments/res-taufik/`  
   - **Notebook Acuan:** [`cloud_dynamics_empirical_analysis_taufik.ipynb`](../notebooks/cloud_dynamics_empirical_analysis_taufik.ipynb)  
   - **Grafik Terkait:** `outputs/taufik/figures/` (300 DPI)  
   - **Fokus Fenomena:** Menyoroti perbandingan antara arsitektur modular (`microservices/frontend` vs `backend`) dan fenomena bencana antrean pada `cpu-bound` saat waktu tunggu menembus 8 detik sehingga memicu kegagalan massal (*mass timeout* hingga 55.853 request gagal).

3. **[Resume Analisis Dataset res-fix (`resume_cloud_dynamics_empirical_analysis.md`)](./resume_cloud_dynamics_empirical_analysis.md)**  
   - **Sumber Data:** `cloud-dynamics-experiments/res-fix/`  
   - **Notebook Acuan:** [`cloud_dynamics_empirical_analysis.ipynb`](../notebooks/cloud_dynamics_empirical_analysis.ipynb)  
   - **Grafik Terkait:** `outputs/figures/` (300 DPI)  
   - **Fokus Fenomena:** Membedah kestabilan baseline, respons terhadap lonjakan beban seketika, dan perbandingan pemanfaatan kapasitas lintas kontainer.

---

## Perbandingan Cepat Karakteristik Antar Dataset

| Parameter Evaluasi | Dataset `res-ali` (Notebook Ali) | Dataset `res-taufik` (Notebook Taufik) |
| :--- | :--- | :--- |
| **Karakteristik Antrean `cpu-bound`** | Antrean menumpuk hingga 11.168 request; latensi menyentuh **4.677 ms** (tepat di bawah batas timeout 5 detik). | Antrean meluap hingga waktu tunggu tembus **8.280 ms** (melampaui batas toleransi 5.0 detik). |
| **Tingkat Keberhasilan `cpu-bound`** | **99.63%** (hanya 10 request gagal timeout di saat puncak burst). | **42.92%** (terjadi kegagalan massal hingga 55.853 request gagal akibat timeout panjang). |
| **Perilaku `microservices`** | Diuji secara menyeluruh melalui service mesh Linkerd; sukses mengantar **100.00%** Goodput. | Dipantau spesifik per sub-komponen: `frontend` (0.54c) vs `backend` (0.33c). |
| **Ketahanan `stateless-api`** | Sangat tangguh (> 200 RPS, latensi rata-rata < 25 ms, **100.00%** Goodput). | Sangat tangguh (> 200 RPS, latensi stabil, 99.96% sukses). |
