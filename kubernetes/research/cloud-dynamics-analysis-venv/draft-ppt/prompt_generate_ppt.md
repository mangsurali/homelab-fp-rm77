# Master Prompt: Panduan Prompt Lengkap untuk Menghasilkan File Presentasi (PPTX / Marp / HTML) Menggunakan Model AI Lain

File ini memuat kumpulan template *prompt* siap pakai (*ready-to-use prompts*) yang dirancang khusus untuk diinstruksikan kepada berbagai jenis **Model AI / Agentic AI** (seperti Claude 3.7 Sonnet / ChatGPT GPT-4o / Gemini 1.5 Pro / DeepSeek / Gamma.app / Cursor / Copilot) guna mengubah konten draf presentasi pada [`draft_ppt_cloud_dynamics.md`](./draft_ppt_cloud_dynamics.md) menjadi file slide presentasi visual profesional (.pptx, .pdf, atau slide interaktif).

---

## Daftar Isi Pilihan Prompt
1. **[Prompt 1: Agentic AI / Python Developer (Generate File `.pptx` Nyata dengan `python-pptx`)](#pilihan-1-prompt-untuk-agentic-ai--python-pptx-menghasilkan-file-pptx-asli)**  
   *(Paling Direkomendasikan: Menghasilkan file PowerPoint `.pptx` asli dengan layout 16:9, warna profesional, tabel terformat, dan gambar 300 DPI tertanam otomatis).*
2. **[Prompt 2: Marp Markdown Presentation Generator (Export PDF / HTML / PPTX)](#pilihan-2-prompt-untuk-marp-markdown-presentation-engine)**  
   *(Sangat Cepat: Menghasilkan berkas Markdown Marp dengan styling CSS canggih).*
3. **[Prompt 3: AI Presentation Web Tools (Gamma.app / SlidesGPT / Beautiful.ai)](#pilihan-3-prompt-untuk-tools-ai-generatif-gammaapp--slidesgpt--beautifulai)**  
   *(Desain Otomatis: Diformat khusus untuk AI presentation builder berbasis web).*
4. **[Prompt 4: VBA Macro Generator (One-Click PowerPoint Generator di Microsoft Office)](#pilihan-4-prompt-generator-vba-macro-powerpoint)**  
   *(Tanpa Python: Menghasilkan kode Visual Basic for Applications untuk dieksekusi langsung di PowerPoint).*

---

## Pilihan 1: Prompt untuk Agentic AI / `python-pptx` (Menghasilkan File `.pptx` Asli)

> **Instruksi Penggunaan:**  
> Salin seluruh teks di dalam kotak blok di bawah ini dan berikan kepada Agentic AI (seperti Claude Code, ChatGPT Advanced Data Analysis, Cursor, Antigravity, atau script runner Python).

```markdown
Anda adalah seorang Desainer Presentasi Ilmiah dan Rekayasawan Perangkat Lunak Python tingkat tinggi.
Tugas Anda adalah membuat skrip Python lengkap (`generate_pptx.py`) yang memanfaatkan pustaka `python-pptx` untuk menghasilkan file presentasi PowerPoint profesional bernama `Cloud_Dynamics_Empirical_Analysis.pptx`.

Gunakan data dan konten dari file `draft_ppt_cloud_dynamics.md` yang berada di direktori saat ini.

### 1. Spesifikasi Teknis & Desain Visual:
1. **Aspek Rasio:** 16:9 Widescreen (Width: 13.333 inci, Height: 7.5 inci).
2. **Palet Warna Profesional (Cloud Infrastructure Theme):**
   - Background Utama: Off-white / Light Slate `#F8FAFC`
   - Dark Navy (Teks Judul & Header): `#0F172A`
   - Slate Gray (Teks Body & Penjelasan): `#334155`
   - Stateless-API Color (Biru I/O): `#1F77B4`
   - CPU-bound Alert Color (Merah Throttled / Saturation): `#D62728`
   - Microservices Color (Hijau Mesh / Tangguh): `#2CA02C`
   - Card Background / Container: `#FFFFFF` dengan outline halus `#E2E8F0`
3. **Tipografi & Hierarki:**
   - Font Family: Arial / Helvetica / Segoe UI (Universal)
   - Judul Slide: 24-28 pt (Bold, Navy `#0F172A`)
   - Subjudul / Tagline Inti: 13-14 pt (Italic / Semi-bold `#475569`)
   - Body Bullet Points: 11-13 pt
   - Label Tabel & Caption: 9-11 pt
4. **Layout Komposisi (Two-Column & Card Layout):**
   - Header atas: Judul Slide + Badge Nomor Slide.
   - Kolom Kiri (~55-60% lebar): Poin-poin analisis terstruktur, kartu metrik, atau tabel perbandingan.
   - Kolom Kanan (~40-45% lebar): Gambar grafik visualisasi empiris 300 DPI dengan bingkai rapi.
   - Kolom Catatan Pembicara: Masukkan seluruh narasi presenter (*Speaker Notes*) ke dalam properti `slide.notes_slide.notes_text_frame.text` di setiap slide!

### 2. Struktur 8 Slide yang Harus Dibangun:

- **Slide 1: Research Context (Urgensi Goodput)**
  - Konten: Latar belakang Kubernetes di industri, paradoks Throughput vs Goodput, diagram alur pesanan dari Offered Load $\to$ Throughput $\to$ Goodput, dan ringkasan evolusi pengujian.
  - Layout: 3 kartu penjelasan berdampingan + 1 kotak kesimpulan di bawah.

- **Slide 2: Experimental Environment (Kluster Kubernetes Bare-Metal)**
  - Konten: Arsitektur kluster Bare-Metal Homelab RM77, NGINX Ingress, Linkerd Service Mesh mTLS, Linux CFS quota limits, stack Prometheus 1s, dan evolusi generator terbuka `loadgen_v2.py`.
  - Layout: Diagram arsitektur tumpukan teknologi (Ingress $\to$ Mesh $\to$ Pod $\to$ Telemetry).

- **Slide 3: Application Architecture (Tiga Karakteristik Aplikasi)**
  - Konten: Membandingkan `stateless-api` (I/O non-blocking), `microservices` (modular frontend vs backend di Linkerd mesh), dan `cpu-bound` (komputasi intensif dengan kuota 0.5 core CFS).
  - Elemen Khusus: Buat tabel perbandingan visual 3 kolom dengan warna aksen masing-masing arsitektur.

- **Slide 4: Experimental Setup (Pengaturan Terkontrol & Kontrol Metodologi)**
  - Konten: Siklus pengujian terstandarisasi (Warm-up 30s @ 5 RPS $\to$ Active 600s $\to$ Cool-down 15s $\to$ Drain phase), batas toleransi sabar pengguna (SLA Timeout 5,0 detik), 3x replikasi independen, dan perbedaan closed-loop vs open-loop.
  - Elemen Khusus: Garis waktu horizontal (*timeline*) siklus hidup pengujian.

- **Slide 5: Workload Scenario (Tiga Pola Beban Empiris)**
  - Konten: Membedah 3 skenario: `constant` (25 RPS baseline santai), `ramp` (10-200 RPS eskalasi linier), dan `burst` (10 $\to$ 150 $\to$ 10 RPS guncangan dinamis tiga babak).
  - Elemen Khusus: Grafik mini / ilustrasi pola beban step-up dan pulse burst.

- **Slide 6: Metrics & Data Collection (Harmonisasi Telemetri Multi-Sumber)**
  - Konten: Integrasi 25 kolom telemetri time-series (`combined.csv`), rumus matematis Overall Goodput Delivery Ratio ($\eta_d$), Goodput Success Rate ($\eta_s$), Instantaneous Fulfillment ($\eta_f$), dan In-Flight Sockets ($Q(t)$).
  - Elemen Khusus: Kotak rumus matematika dengan latar belakang kartu abu-abu bersih.

- **Slide 7: Experimental Results (Hasil Eksperimen & Perbandingan Kinerja)**
  - Konten: Tabel perbandingan metrik utama lintas dataset (Taufik vs Ali v1 vs Ali v5). Menampilkan plafon kaku `cpu-bound` di ~56 RPS dan pencapaian 100% sempurna `microservices` (0 failed dari 147.000+ request).
  - Gambar Visualisasi: Masukkan gambar:
    `../outputs/ali-v5/figures/04_knee_of_saturation_curves.png`
    (Atau jika file tidak ditemukan, gunakan fallback yang tersedia atau buat placeholder shape).

- **Slide 8: Observed Phenomenon (Fenomena Kritis & Rekomendasi Industri)**
  - Konten: Penjelasan Hockey-Stick latency curve sesuai hukum Little & antrean M/M/1, bias Coordinated Omission, kemampuan pemulihan mandiri 20 detik (*self-healing*), serta 3 rekomendasi industri: Ingress Load Shedding `limit_req ... nodelay`, Autoscaling HPA, dan adopsi Service Mesh.
  - Gambar Visualisasi: Masukkan gambar:
    `../outputs/ali-v5/figures/05_goodput_triad_and_fulfillment.png`

### 3. Instruksi Eksekusi Kode Python:
- Tulis kode Python yang modular, tangani jika gambar tidak ditemukan dengan try-except / path checking.
- Gunakan modul `pptx.util` (`Inches`, `Pt`, `RGBColor`) dan `pptx.enum.text.PP_ALIGN`.
- Jalankan skrip tersebut untuk menghasilkan file `Cloud_Dynamics_Empirical_Analysis.pptx`.
- Pastikan tidak ada teks yang saling tumpang tindih (*overlapping*) dan margin slide terjaga rapi.
```

---

## Pilihan 2: Prompt untuk Marp Markdown Presentation Engine

> **Instruksi Penggunaan:**  
> Salin prompt di bawah ini ke model AI untuk menghasilkan satu file tunggal Markdown Marp (`slides.marp.md`). File tersebut dapat langsung dibuka di VS Code (dengan ekstensi Marp) atau dikompilasi via terminal menjadi PPTX/PDF menggunakan perintah:  
> `marp --pptx slides.marp.md` atau `marp --pdf slides.marp.md`.

```markdown
Anda adalah seorang perancang slide presentasi berbasis Marp (Markdown Presentation Ecosystem).
Tolong buatkan berkas presentasi Markdown Marp lengkap (`slides.marp.md`) dengan 8 slide ilmiah berdasarkan konten file `draft_ppt_cloud_dynamics.md`.

### Persyaratan Konfigurasi Marp:
1. Header YAML Frontmatter wajib menyertakan:
   ```yaml
   ---
   marp: true
   theme: default
   paginate: true
   size: 16:9
   header: "Riset Cloud Dynamics: Analisis Titik Jenuh, Goodput, dan Ketahanan Kubernetes"
   footer: "Homelab RM77 | Ali & Tim Riset Komputasi Awan"
   style: |
     section {
       background-color: #f8fafc;
       font-family: 'Segoe UI', 'DejaVu Sans', Arial, sans-serif;
       color: #1e293b;
       padding: 40px;
     }
     h1 {
       color: #0f172a;
       font-size: 26pt;
     }
     h2 {
       color: #1e40af;
       font-size: 20pt;
     }
     .highlight-blue { color: #1f77b4; font-weight: bold; }
     .highlight-red { color: #d62728; font-weight: bold; }
     .highlight-green { color: #2ca02c; font-weight: bold; }
     .card {
       background: #ffffff;
       border: 1px solid #e2e8f0;
       border-radius: 8px;
       padding: 12px;
       box-shadow: 0 2px 4px rgba(0,0,0,0.05);
     }
     .columns {
       display: grid;
       grid-template-columns: 1fr 1fr;
       gap: 20px;
     }
     table {
       font-size: 11pt;
     }
   ---
   ```
2. Setiap slide dipisahkan dengan tanda `---`.
3. Terapkan layout dua kolom (`<div class="columns">`) untuk slide yang menyandingkan teks analisis dan gambar visualisasi.
4. Sematkan gambar relatif:
   - Slide 7: `![w:520](../outputs/ali-v5/figures/04_knee_of_saturation_curves.png)`
   - Slide 8: `![w:520](../outputs/ali-v5/figures/05_goodput_triad_and_fulfillment.png)`
5. Masukkan catatan pembicara di setiap slide menggunakan sintesis komentar HTML:
   ```html
   <!-- _footer: "..." -->
   <!--
   Catatan Pembicara:
   [Tuliskan narasi presenter lengkap di sini]
   -->
   ```
6. Susun tepat 8 slide sesuai struktur topik:
   - Slide 1: Research Context
   - Slide 2: Experimental Environment
   - Slide 3: Application Architecture
   - Slide 4: Experimental Setup
   - Slide 5: Workload Scenario
   - Slide 6: Metrics & Data Collection
   - Slide 7: Experimental Results
   - Slide 8: Observed Phenomenon
```

---

## Pilihan 3: Prompt untuk Tools AI Generatif (Gamma.app / SlidesGPT / Beautiful.ai)

> **Instruksi Penggunaan:**  
> Salin teks di bawah ini langsung ke kotak input AI Presentation Creator (seperti **Gamma.app**, **SlidesGPT**, **Tome**, atau **ChatBA**) untuk menghasilkan slide presentasi otomatis dengan grafis modern.

```markdown
Buatkan presentasi profesional 8 slide dengan rasio 16:9 bertema "Analisis Kinerja Cloud Dynamics pada Kubernetes: Membedah Titik Jenuh, Goodput, dan Ketahanan Sistem".

Tone & Style:
- Gaya: Academic, Technical, Minimalist Modern.
- Palet Warna: Navy Slate, Tech Blue, Alert Red, Emerald Green.
- Format Konten: Judul padat, ringkasan kartu 3 poin, tabel ringkas, dan callout rekomendasi.

Outline Slide:
Slide 1: Research Context — Paradoks Throughput vs Goodput. Mengapa server yang sibuk memproses Throughput tinggi belum tentu memuaskan pelanggan, dan mengapa Goodput (transaksi bebas error dalam batas waktu 5 detik) adalah tolok ukur kepuasan nyata pengguna di Kubernetes.
Slide 2: Experimental Environment — Kluster Kubernetes Bare-Metal Homelab RM77. Menggunakan NGINX Ingress Controller, Linkerd Service Mesh mTLS, regulasi isolasi prosesor Linux CFS cgroups, telemetri Prometheus tiap 1 detik, serta generator beban open-loop asinkronus loadgen_v2.py.
Slide 3: Application Architecture — Tiga Pola Beban Kerja Kontainer. Membandingkan stateless-api (I/O asinkronus ultra cepat), microservices (multi-tier frontend & backend di dalam service mesh Linkerd), dan cpu-bound (pekerja enkripsi berat berkuota ketat 0,5 inti CPU).
Slide 4: Experimental Setup — Protokol Pengujian Terkontrol. Siklus hidup pengujian berulang (Pemanasan 30 detik pada 5 RPS, Pengukuran aktif 600 detik, Pendinginan 15 detik), Client SLA Timeout 5,0 detik, serta 3 replikasi independen untuk menjamin reproduksibilitas.
Slide 5: Workload Scenario — Tiga Skenario Beban Industri. Uji kestabilan dasar Constant (25 RPS), uji eskalasi jam sibuk Ramp (10 hingga 200 RPS), dan uji guncangan lonjakan dinamis Burst tiga babak (10 RPS tenang -> 150 RPS lonjakan 2 menit -> 10 RPS pemulihan).
Slide 6: Metrics & Data Collection — Formula Metrik Kinerja Goodput. Integrasi 25 kolom data telemetri, Overall Goodput Delivery Ratio, Goodput Success Rate, Instantaneous Fulfillment Ratio, dan Dinamika Antrean In-Flight Soket Sistem Q(t).
Slide 7: Experimental Results — Hasil Pengujian Empiris Lintas Dataset. Pembuktian plafon kaku cpu-bound pada ~56 RPS akibat kuota prosesor, dan rekor sempurna microservices meraih 100% Success Rate dari 147.000+ request tanpa satu pun transaksi gagal pada skala operasional 200 RPS.
Slide 8: Observed Phenomenon & Industrial Takeaways — Fenomena Kritis & Rekomendasi Industri. Kurva latensi tongkat hoki (Hockey-Stick), pembongkaran ilusi Coordinated Omission, pemulihan cepat mandiri (self-healing) dalam 20 detik, serta rekomendasi penerapan Ingress Load Shedding (limit_req ... nodelay) dan HPA Autoscaling.
```

---

## Pilihan 4: Prompt Generator VBA Macro PowerPoint

> **Instruksi Penggunaan:**  
> Jika Anda atau pengguna ingin menghasilkan file presentasi langsung di dalam Microsoft PowerPoint tanpa perlu menginstal Python atau Node.js, salin prompt ini ke model AI untuk menghasilkan kode Macro VBA (`Sub CreateCloudDynamicsSlides()`).

```markdown
Anda adalah seorang programmer Microsoft Office Visual Basic for Applications (VBA) tingkat lanjut.
Buatkan modul kode VBA lengkap yang dapat disalin ke PowerPoint (Alt + F11 -> Insert Module -> Run) untuk secara otomatis membuat file presentasi 8 slide 16:9 berdasarkan file `draft_ppt_cloud_dynamics.md`.

Spesifikasi Kode VBA:
1. Buat presentasi baru dengan rasio 16:9 (`SlideWidth = 960`, `SlideHeight = 540`).
2. Tentukan konstanta warna:
   - `NAVY = RGB(15, 23, 42)`
   - `SLATE = RGB(51, 65, 85)`
   - `BG_LIGHT = RGB(248, 250, 252)`
   - `ACCENT_BLUE = RGB(31, 119, 180)`
   - `ALERT_RED = RGB(214, 39, 40)`
   - `SUCCESS_GREEN = RGB(44, 160, 44)`
   - `WHITE = RGB(255, 255, 255)`
3. Di setiap slide:
   - Tambahkan shape container / kartu modern berlatar belakang putih dengan border tipis abu-abu.
   - Tambahkan Judul Slide (Font: Arial Bold, 24pt, warna NAVY).
   - Tambahkan Text Box konten poin-poin dengan font ukuran 12-14pt.
   - Tambahkan Catatan Pembicara (*Speaker Notes*) ke dalam `slide.NotesPage.Shapes.Placeholders(2).TextFrame.TextRange.Text`.
4. Pada Slide 7 dan Slide 8, sisipkan gambar grafik visualisasi menggunakan perintah:
   `slide.Shapes.AddPicture(FileName:="...", LinkToFile:=msoFalse, SaveWithDocument:=msoTrue, Left:=520, Top:=120, Width:=400, Height:=300)`
   Sertakan error handling (`On Error Resume Next`) jika file gambar berada di direktori relatif yang berbeda.
5. Susun tepat 8 slide sesuai dengan materi pada `draft_ppt_cloud_dynamics.md`.
```

---

## Ringkasan Lokasi Asset Gambar untuk Disematkan

Saat menjalankan skrip atau prompt di atas, berikut adalah path absolut dan relatif file gambar visualisasi 300 DPI yang siap disematkan:

| Slide | Nama Gambar | Path Relatif (dari folder `draft-ppt/`) | Path Absolut di Sistem |
| :---: | :--- | :--- | :--- |
| **Slide 5** | Pola Beban Ramp | `../outputs/ali-v5/figures/02_ramp_scenario_comparison.png` | `/home/ali/kuliah/homelab-fp-rm77/kubernetes/research/cloud-dynamics-analysis-venv/outputs/ali-v5/figures/02_ramp_scenario_comparison.png` |
| **Slide 5** | Pola Beban Burst | `../outputs/ali-v5/figures/03_burst_scenario_comparison.png` | `/home/ali/kuliah/homelab-fp-rm77/kubernetes/research/cloud-dynamics-analysis-venv/outputs/ali-v5/figures/03_burst_scenario_comparison.png` |
| **Slide 7** | Titik Jenuh (*Knee Curves*) | `../outputs/ali-v5/figures/04_knee_of_saturation_curves.png` | `/home/ali/kuliah/homelab-fp-rm77/kubernetes/research/cloud-dynamics-analysis-venv/outputs/ali-v5/figures/04_knee_of_saturation_curves.png` |
| **Slide 8** | Triad Goodput & Drop Gap | `../outputs/ali-v5/figures/05_goodput_triad_and_fulfillment.png` | `/home/ali/kuliah/homelab-fp-rm77/kubernetes/research/cloud-dynamics-analysis-venv/outputs/ali-v5/figures/05_goodput_triad_and_fulfillment.png` |
| **Slide 8** | Antrean Soket & Drain | `../outputs/ali-v5/figures/06_queue_backpressure_and_drain_dynamics.png` | `/home/ali/kuliah/homelab-fp-rm77/kubernetes/research/cloud-dynamics-analysis-venv/outputs/ali-v5/figures/06_queue_backpressure_and_drain_dynamics.png` |
