# Direktori Draft Presentasi Riset Cloud Dynamics

Direktori ini berisi draf materi presentasi ilmiah komprehensif 8 slide yang merangkum hasil riset pengujian empiris dinamika komputasi awan di Kubernetes berdasarkan tiga dataset acuan:
1. **Dataset Taufik** (`res-taufik`)
2. **Dataset Ali v1** (`res-ali`)
3. **Dataset Ali v5** (`res-ali-v5`)

---

## Berkas di Direktori Ini

* **[`draft_ppt_cloud_dynamics.md`](./draft_ppt_cloud_dynamics.md)**: Dokumen draf presentasi lengkap 8 slide yang memuat poin slide, diagram ASCII/tabel perbandingan, sematan gambar visualisasi 300 DPI, dan narasi lengkap pembicara (*speaker notes*) untuk setiap slide.
* **[`prompt_generate_ppt.md`](./prompt_generate_ppt.md)**: Kumpulan template *prompt* siap pakai untuk menginstruksikan Model AI / Agentic AI lain (Claude, ChatGPT, Gamma, Marp, VBA) agar mengonversi materi draf slide menjadi file presentasi (.pptx, .pdf, atau slide interaktif).

---

## Struktur 8 Slide Presentasi

1. **Slide 1: Research Context** — Konteks Riset, Latar Belakang Kubernetes, Paradoks Throughput vs. Goodput, dan Urgensi Kepuasan Pengguna Nyata.
2. **Slide 2: Experimental Environment** — Kluster Kubernetes Bare-Metal, Linux CFS cgroups, NGINX Ingress, Linkerd Service Mesh, Prometheus Telemetry, dan Generator Beban (`loadgen_v2.py`).
3. **Slide 3: Application Architecture** — Perbandingan Arsitektur `stateless-api`, `microservices` (Frontend + Backend), dan `cpu-bound` (Batas Kuota CFS 0,5 Core).
4. **Slide 4: Experimental Setup** — Protokol Pemanasan (Warm-up 30s), Active Window (600s), Cool-down (15s), Client SLA Timeout 5,0s, Replikasi 3x, dan Metodologi Closed-Loop vs. Open-Loop.
5. **Slide 5: Workload Scenario** — Tiga Pola Beban: `constant` (25 RPS Baseline), `ramp` (10-200 RPS Eskalasi Linier), dan `burst` (10 $\to$ 150 $\to$ 10 RPS Guncangan Dinamis Tiga Babak).
6. **Slide 6: Metrics dan Data Collection** — Harmonisasi 25 Kolom Data Time-Series (`combined.csv`), Formula Matematis Goodput Delivery Ratio ($\eta_d$), Success Rate ($\eta_s$), Instantaneous Fulfillment ($\eta_f$), dan In-Flight Queue ($Q(t)$).
7. **Slide 7: Experimental Results** — Perbandingan Kinerja Lintas Dataset, Plafon Kaku `cpu-bound` di ~56 RPS, Skalabilitas Linier 100% Sempurna `microservices` (0 failed dari 147.000+ request), dan Sematan Kurva Titik Jenuh.
8. **Slide 8: Observed Phenomenon** — Fenomena Kurva Tongkat Hoki (*Hockey-Stick Latency*), Bias *Coordinated Omission*, Pemulihan Cepat 20 Detik (*Self-Healing*), serta Rekomendasi Industri (*Ingress Fail-Fast Load Shedding* `limit_req ... nodelay` dan HPA Autoscaling).

---

## Panduan Penggunaan / Ekspor Presentasi
Dokumen ini disusun menggunakan format Markdown terstruktur yang siap:
1. **Dikonversi ke Slide Interaktif:** Menggunakan ekstensi [Marp for VS Code](https://marp.app/) atau [Slidev](https://sli.dev/) untuk langsung diekspor ke format PDF / PowerPoint (.pptx) / HTML.
2. **Disalin Manual:** Poin-poin presentasi dan catatan pembicara (*speaker notes*) dapat langsung disalin ke aplikasi presentasi (Microsoft PowerPoint, Google Slides, Apple Keynote).
