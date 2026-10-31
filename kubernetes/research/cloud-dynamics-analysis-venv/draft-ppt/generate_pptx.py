"""
generate_pptx.py  –  Cloud Dynamics Empirical Analysis presentation builder
Produces: Cloud_Dynamics_Empirical_Analysis.pptx  (16:9 widescreen)
"""

import os
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

# ── Palette ──────────────────────────────────────────────────────────────────
BG       = RGBColor(0xF8, 0xFA, 0xFC)   # off-white slide background
NAVY     = RGBColor(0x0F, 0x17, 0x2A)   # title / header
SLATE    = RGBColor(0x33, 0x41, 0x55)   # body text
MUTED    = RGBColor(0x47, 0x55, 0x69)   # tagline / italic
BLUE     = RGBColor(0x1F, 0x77, 0xB4)   # stateless-api accent
RED      = RGBColor(0xD6, 0x27, 0x28)   # cpu-bound accent
GREEN    = RGBColor(0x2C, 0xA0, 0x2C)   # microservices accent
WHITE    = RGBColor(0xFF, 0xFF, 0xFF)
CARD_BG  = RGBColor(0xFF, 0xFF, 0xFF)
BORDER   = RGBColor(0xE2, 0xE8, 0xF0)
GRAY_BG  = RGBColor(0xF1, 0xF5, 0xF9)

# ── Slide dimensions (16:9) ───────────────────────────────────────────────────
W = Inches(13.333)
H = Inches(7.5)

FIGURES = Path(__file__).parent / "../outputs/ali-v5/figures"

# ─────────────────────────────────────────────────────────────────────────────
# Low-level helpers
# ─────────────────────────────────────────────────────────────────────────────

def _rgb(r, g, b):
    return RGBColor(r, g, b)


def blank_slide(prs):
    """Add a truly blank slide (no placeholders)."""
    layout = prs.slide_layouts[6]   # 'Blank' layout
    return prs.slides.add_slide(layout)


def set_bg(slide, color: RGBColor):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_rect(slide, x, y, w, h, fill: RGBColor, line: RGBColor | None = None, line_w=Pt(0.75)):
    """Return a rectangle shape with optional border."""
    shape = slide.shapes.add_shape(1, x, y, w, h)   # MSO_SHAPE_TYPE.RECTANGLE = 1
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    if line:
        shape.line.color.rgb = line
        shape.line.width = line_w
    else:
        shape.line.fill.background()
    return shape


def add_textbox(slide, x, y, w, h, text, size=Pt(12), bold=False, italic=False,
                color=SLATE, align=PP_ALIGN.LEFT, wrap=True):
    """Single-run textbox helper."""
    txb = slide.shapes.add_textbox(x, y, w, h)
    tf = txb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = size
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = "Arial"
    return txb


def add_paragraph(tf, text, size=Pt(11), bold=False, italic=False,
                  color=SLATE, align=PP_ALIGN.LEFT, space_before=Pt(4), level=0):
    """Append a paragraph to an existing text frame."""
    p = tf.add_paragraph()
    p.alignment = align
    p.level = level
    p.space_before = space_before
    run = p.add_run()
    run.text = text
    run.font.size = size
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = "Arial"
    return p


def slide_header(slide, title, subtitle, slide_num, total=8):
    """Render the top header band: title left, badge right."""
    # Header band
    hdr = add_rect(slide, Inches(0), Inches(0), W, Inches(1.1), NAVY)
    # Title
    add_textbox(slide, Inches(0.35), Inches(0.12), Inches(10.5), Inches(0.85),
                title, size=Pt(22), bold=True, color=WHITE, align=PP_ALIGN.LEFT)
    # Subtitle tagline
    if subtitle:
        add_textbox(slide, Inches(0.35), Inches(0.68), Inches(10.0), Inches(0.36),
                    subtitle, size=Pt(11), italic=True, color=RGBColor(0xCB, 0xD5, 0xE1),
                    align=PP_ALIGN.LEFT)
    # Slide badge
    badge = add_rect(slide, Inches(12.3), Inches(0.22), Inches(0.82), Inches(0.55),
                     BLUE, None)
    add_textbox(slide, Inches(12.3), Inches(0.22), Inches(0.82), Inches(0.55),
                f"{slide_num}/{total}", size=Pt(11), bold=True, color=WHITE,
                align=PP_ALIGN.CENTER)


def try_add_image(slide, path, x, y, w, h):
    """Add image or a placeholder rectangle if missing."""
    p = Path(path)
    if p.exists():
        slide.shapes.add_picture(str(p), x, y, w, h)
    else:
        ph = add_rect(slide, x, y, w, h, GRAY_BG, BORDER)
        add_textbox(slide, x, y + Inches(0.4), w, Inches(0.5),
                    f"[Image not found]\n{p.name}",
                    size=Pt(9), italic=True, color=MUTED, align=PP_ALIGN.CENTER)


def set_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def card(slide, x, y, w, h, title, lines, title_color=NAVY, accent: RGBColor | None = None):
    """Draw a white card with a top accent bar, title, and bullet lines."""
    add_rect(slide, x, y, w, h, CARD_BG, BORDER)
    if accent:
        add_rect(slide, x, y, w, Inches(0.06), accent)
    add_textbox(slide, x + Inches(0.14), y + Inches(0.12), w - Inches(0.28), Inches(0.36),
                title, size=Pt(11), bold=True, color=title_color)
    txb = slide.shapes.add_textbox(x + Inches(0.14), y + Inches(0.50),
                                    w - Inches(0.28), h - Inches(0.62))
    tf = txb.text_frame
    tf.word_wrap = True
    first = True
    for line in lines:
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        p.space_before = Pt(3)
        run = p.add_run()
        run.text = line
        run.font.size = Pt(9.5)
        run.font.color.rgb = SLATE
        run.font.name = "Arial"


# ─────────────────────────────────────────────────────────────────────────────
# Slide builders
# ─────────────────────────────────────────────────────────────────────────────

def slide1(prs):
    sl = blank_slide(prs)
    set_bg(sl, BG)
    slide_header(sl,
        "Research Context: Urgensi Goodput dalam Sistem Cloud-Native",
        "Mengapa Throughput Tinggi Bisa Menipu — dan Mengapa Goodput adalah Kunci",
        1)

    # ── 3 cards row ──────────────────────────────────────────────────────────
    cy = Inches(1.22)
    ch = Inches(2.55)
    cw = Inches(3.95)
    gap = Inches(0.22)
    x1 = Inches(0.28)
    x2 = x1 + cw + gap
    x3 = x2 + cw + gap

    card(sl, x1, cy, cw, ch,
         "🏭  Latar Belakang Cloud-Native", [
             "• Migrasi masif monolitik → kontainer Kubernetes",
             "• Dasbor server menunjukkan CPU sibuk, tapi pengguna mengeluh:",
             "  loading lama, transaksi gagal (timeout)",
             "• Tantangan: Bagaimana mengukur 'kepuasan pengguna nyata'?",
         ], accent=NAVY)

    card(sl, x2, cy, cw, ch,
         "⚡  Paradoks: Throughput vs. Goodput", [
             "• Throughput (X): seberapa sibuk jaringan memompa paket",
             "  → tidak peduli apakah data kadaluarsa / transaksi dibatalkan",
             "• Goodput (G): transaksi produktif HTTP 200 OK",
             "  → selesai dalam batas SLA 5,0 detik",
             "• Server bisa 100% busy namun Goodput = 0%",
         ], accent=BLUE)

    card(sl, x3, cy, cw, ch,
         "❓  Tiga Pertanyaan Riset Utama", [
             "1. Di mana letak titik jenuh fisik (knee of saturation)?",
             "2. Apa yang terjadi pada antrean saat beban > kapasitas?",
             "3. Bagaimana closed-loop vs open-loop membongkar",
             "   bias Coordinated Omission?",
         ], accent=GREEN)

    # ── Flow diagram box ──────────────────────────────────────────────────────
    bx = Inches(0.28); by = Inches(3.95); bw = W - Inches(0.56); bh = Inches(1.05)
    add_rect(sl, bx, by, bw, bh, RGBColor(0xE0, 0xF2, 0xFE), BLUE, Pt(1))
    add_textbox(sl, bx + Inches(0.18), by + Inches(0.08), bw - Inches(0.36), Inches(0.3),
                "Alur Pesanan (Order Flow):",
                size=Pt(10), bold=True, color=NAVY)
    add_textbox(sl, bx + Inches(0.18), by + Inches(0.35), bw - Inches(0.36), Inches(0.62),
                "[Beban Datang (Offered Load)]  ══►  [Diproses Jaringan (Throughput)]  ══►  [Transaksi Sukses Sesuai SLA (Goodput)]\n"
                "   (Pengguna menekan tombol)              (Server sibuk bekerja)                  (Pelanggan puas, bebas error)",
                size=Pt(10), color=SLATE)

    # ── Summary box ──────────────────────────────────────────────────────────
    sx = Inches(0.28); sy = Inches(5.12); sw = W - Inches(0.56); sh = Inches(0.92)
    add_rect(sl, sx, sy, sw, sh, RGBColor(0xFF, 0xF7, 0xED), RGBColor(0xF9, 0x73, 0x16), Pt(1))
    add_textbox(sl, sx + Inches(0.18), sy + Inches(0.08), sw - Inches(0.36), Inches(0.76),
                "✦  Riset ini menguji 3 arsitektur kontainer di kluster Kubernetes bare-metal nyata — membedah antrean, "
                "mendeteksi titik jenuh, dan membongkar bias alat uji untuk data yang benar-benar mencerminkan realita produksi.",
                size=Pt(10.5), italic=True, color=RGBColor(0x7C, 0x2D, 0x12))

    set_notes(sl,
        "Selamat pagi/siang Bapak/Ibu dewan penguji dan rekan-rekan sekalian. Presentasi ini mengangkat topik krusial "
        "dalam rekayasa komputasi awan: Dinamika Performa Cloud di Bawah Beban Terkontrol. Selama bertahun-tahun, industri "
        "sering tertipu oleh metrik Throughput—menganggap bahwa selama server sibuk memproses paket data tinggi, sistem "
        "dalam keadaan baik. Namun di dunia nyata, pelanggan tidak peduli seberapa sibuk wajan dapur mengepul; pelanggan "
        "hanya peduli apakah makanannya sampai tepat waktu tanpa basi. Inilah inti dari metrik Goodput. Melalui riset ini, "
        "kami menguji tiga arsitektur aplikasi kontainer di kluster Kubernetes nyata, membedah fenomena penumpukan antrean, "
        "mendeteksi titik jenuh kapasitas, dan membongkar bias pengukuran alat uji untuk mendapatkan data yang benar-benar "
        "mencerminkan realita lapangan.")


def slide2(prs):
    sl = blank_slide(prs)
    set_bg(sl, BG)
    slide_header(sl,
        "Experimental Environment: Kluster Kubernetes Bare-Metal",
        "NGINX Ingress · Linkerd Service Mesh mTLS · Prometheus 1s · loadgen_v2.py Open-Loop",
        2)

    # Left column: stack details
    lx = Inches(0.28); ly = Inches(1.22); lw = Inches(7.5); lh = Inches(5.8)

    components = [
        (NAVY,  "🖥   Platform Fisik & OS",
         ["• Kubernetes Bare-Metal — Homelab RM77  (Host IP: 10.160.4.43)",
          "• Kernel Linux — isolasi sumber daya via cgroups CFS bandwidth quota"]),
        (BLUE,  "🌐  Gerbang Lalu Lintas",
         ["• NGINX Ingress Controller — domain routing via dynamic DNS sslip.io",
          "• Linkerd Service Mesh — mTLS otomatis, proxy sidecar per pod,",
          "  observabilitas latensi P50/P95/P99, pool koneksi TCP"]),
        (GREEN, "📊  Stack Telemetri & Observabilitas",
         ["• Prometheus Time-Series Engine — sampling Δt = 1,0 detik",
          "• cAdvisor & Node Exporter — CPU throttle, memori kerja, RX/TX"]),
        (RED,   "⚙   Evolusi Generator Beban",
         ["• v1 (Closed-Loop Thread-Pool): 256 worker threads — dataset Taufik & Ali v1",
          "• v2 (Open-Loop Async — loadgen_v2.py): asyncio + aiohttp, soket tak berbatas,",
          "  penegakan deadline timeout 5,0 detik sejak jadwal kedatangan — dataset Ali v5"]),
    ]

    cy = ly
    for accent, title, lines in components:
        ch = Inches(0.18 + 0.36 + len(lines) * 0.30 + 0.22)
        card(sl, lx, cy, lw, ch, title, lines, accent=accent)
        cy += ch + Inches(0.14)

    # Right column: architecture diagram
    rx = Inches(8.1); ry = Inches(1.22); rw = Inches(4.95); rh = Inches(5.8)
    add_rect(sl, rx, ry, rw, rh, CARD_BG, BORDER)
    add_textbox(sl, rx + Inches(0.15), ry + Inches(0.12), rw - Inches(0.3), Inches(0.35),
                "Arsitektur Stack Eksperimen", size=Pt(11), bold=True, color=NAVY)

    layers = [
        (BLUE,  "Client: loadgen_v2.py\n(HTTP / TCP Sockets)"),
        (NAVY,  "NGINX Ingress Controller Gateway\n(Service routing via sslip.io)"),
        (GREEN, "Linkerd Service Mesh Proxy\n(Sidecar mTLS per pod)"),
        (SLATE, "Application Pod\n(stateless-api | microservices | cpu-bound)"),
        (RGBColor(0x78, 0x71, 0x6C),
                "Prometheus + cAdvisor Telemetry\n(1-second resolution)"),
    ]
    box_h = Inches(0.72)
    box_gap = Inches(0.20)
    bx = rx + Inches(0.2)
    bw2 = rw - Inches(0.4)
    by = ry + Inches(0.58)
    for i, (clr, lbl) in enumerate(layers):
        add_rect(sl, bx, by, bw2, box_h, clr)
        add_textbox(sl, bx + Inches(0.1), by + Inches(0.08), bw2 - Inches(0.2), Inches(0.56),
                    lbl, size=Pt(9.5), bold=False, color=WHITE, align=PP_ALIGN.CENTER)
        if i < len(layers) - 1:
            # arrow
            add_textbox(sl, bx + bw2 / 2 - Inches(0.2), by + box_h, Inches(0.4), Inches(0.22),
                        "▼", size=Pt(10), color=NAVY, align=PP_ALIGN.CENTER)
        by += box_h + box_gap

    set_notes(sl,
        "Untuk memastikan data riset ini valid dan dapat direproduksi, seluruh eksperimen dijalankan di atas kluster "
        "Kubernetes bare-metal mandiri di Homelab RM77. Arsitektur jaringan kami dilengkapi NGINX Ingress Gateway sebagai "
        "pintu gerbang masuk dan Linkerd Service Mesh sebagai pengatur komunikasi antar-kontainer. Seluruh denyut sistem "
        "dipantau secara sinkron tiap 1 detik menggunakan Prometheus dan cAdvisor. Kami menggunakan dua generasi generator "
        "beban: generator v1 berbasis thread pool, dan generator v2 berbasis open-loop asinkronus yang kami bangun sendiri "
        "untuk memastikan beban ditembakkan secara independen tanpa ditahan di memori klien.")


def slide3(prs):
    sl = blank_slide(prs)
    set_bg(sl, BG)
    slide_header(sl,
        "Application Architecture: Tiga Karakteristik Aplikasi Uji",
        "Kasir Tol Cekatan · Restoran Multi-Tier · Koki Komputasi Berkuota Kaku",
        3)

    # Intro text
    add_textbox(sl, Inches(0.28), Inches(1.22), W - Inches(0.56), Inches(0.35),
                "Riset membandingkan tiga arsitektur yang mewakili spektrum beban kerja cloud-native modern:",
                size=Pt(11), color=SLATE)

    # 3 app cards
    cw = Inches(4.05); ch = Inches(2.65); cy = Inches(1.65); gap = Inches(0.26)
    xs = [Inches(0.28), Inches(0.28) + cw + gap, Inches(0.28) + (cw + gap) * 2]

    items = [
        (BLUE,  "stateless-api  —  Si Kasir Tol Otomatis",
         ["Arsitektur: Async Non-Blocking I/O Event-Loop",
          "Paradigma: Node.js / Go style",
          "CPU Usage: sangat rendah, eksekusi < 5 ms",
          "Kapasitas Teoretis: > 600 RPS",
          "Batas Kuota: uncapped (ikuti node)"]),
        (GREEN, "microservices  —  Restoran Multi-Tier",
         ["Arsitektur: Modular terdistribusi (frontend + backend)",
          "Mesh: Linkerd sidecar proxy di setiap pod",
          "Pengujian: network hop latency, serialisasi data",
          "CPU Taufik: frontend 0,54 core | backend 0,33 core",
          "Kapasitas Teoretis: ~340 RPS"]),
        (RED,   "cpu-bound  —  Koki Enkripsi Berkuota Kaku",
         ["Arsitektur: Compute-intensive (hashing & math berat)",
          "Batas Keras: cgroups limits.cpu = 500m (0,5 core CFS)",
          "Perilaku: rentan CPU throttle di atas ~56 RPS",
          "Kapasitas Teoretis: ~56 RPS (plafon kaku)",
          "Representasi: layanan pemrosesan data intensif"]),
    ]
    for (accent, title, lines), x in zip(items, xs):
        card(sl, x, cy, cw, ch, title, lines, accent=accent)

    # Comparison table
    ty = Inches(4.42); th = Inches(2.6); tx = Inches(0.28); tw = W - Inches(0.56)
    add_rect(sl, tx, ty, tw, th, CARD_BG, BORDER)

    headers = ["Parameter", "stateless-api", "microservices", "cpu-bound"]
    rows = [
        ["Karakter Beban",       "I/O-Bound (Non-blocking)", "Multi-hop Network / Mesh", "Compute-Bound (Intensive)"],
        ["Komponen Layanan",     "Single Service Pod",        "Frontend + Backend Pods",  "Single Worker Pod"],
        ["Interaksi Jaringan",   "Ingress → Pod",             "Ingress → Mesh → Service", "Ingress → Pod"],
        ["Batas Kuota CPU",      "Uncapped",                  "2 Layanan Mesh Terpisah",  "Ketat 0,5 Core (500m)"],
        ["Kapasitas Teoretis",   "> 600 RPS",                 "~340 RPS",                 "~56 RPS  ⚠"],
    ]
    col_w  = [Inches(2.2), Inches(3.3), Inches(3.3), Inches(3.3)]
    col_x  = [tx + Inches(0.05)]
    for w in col_w[:-1]:
        col_x.append(col_x[-1] + w)
    col_accents = [NAVY, BLUE, GREEN, RED]
    row_h = Inches(0.38)

    # Header row
    for i, (hdr, cx, cxa) in enumerate(zip(headers, col_x, col_accents)):
        add_rect(sl, cx, ty + Inches(0.04), col_w[i] - Inches(0.04),
                 row_h, cxa)
        add_textbox(sl, cx + Inches(0.06), ty + Inches(0.10),
                    col_w[i] - Inches(0.12), row_h - Inches(0.08),
                    hdr, size=Pt(9.5), bold=True, color=WHITE)

    for r, row in enumerate(rows):
        ry2 = ty + row_h + Inches(0.04) + r * (row_h - Inches(0.01))
        bg = GRAY_BG if r % 2 == 0 else CARD_BG
        for i, (cell, cx) in enumerate(zip(row, col_x)):
            add_rect(sl, cx, ry2, col_w[i] - Inches(0.04), row_h - Inches(0.02), bg, BORDER, Pt(0.5))
            add_textbox(sl, cx + Inches(0.06), ry2 + Inches(0.06),
                        col_w[i] - Inches(0.12), row_h - Inches(0.1),
                        cell, size=Pt(9), color=SLATE if i > 0 else NAVY, bold=(i == 0))

    set_notes(sl,
        "Untuk mendapatkan perbandingan komparatif yang bermakna, kami memilih tiga arsitektur yang mewakili beban kerja "
        "komputasi awan modern. Pertama, stateless-api, yang bekerja seperti gerbang tol otomatis: hanya memvalidasi kartu "
        "dan langsung membuka palang. Kedua, microservices, yang membagi peran antara pelayan depan (frontend) dan dapur "
        "pengolah (backend) yang saling terhubung lewat service mesh Linkerd. Ketiga, cpu-bound, yaitu pekerja komputasi "
        "berat yang kami beri batasan kuota prosesor ketat: hanya 0,5 core. Dengan menguji ketiganya secara berdampingan "
        "di bawah profil beban yang persis sama, kita dapat melihat secara transparan bagaimana perbedaan desain arsitektur "
        "memengaruhi ketahanan sistem.")


def slide4(prs):
    sl = blank_slide(prs)
    set_bg(sl, BG)
    slide_header(sl,
        "Experimental Setup: Protokol Pengujian Terkontrol & Kontrol Metodologi",
        "Warm-up 30s · Active 600s · SLA Timeout 5,0 s · 3× Replikasi Independen",
        4)

    # Left column: protocol cards
    lx = Inches(0.28); lw = Inches(7.6); ly = Inches(1.22)

    proto = [
        (NAVY, "🔥  Fase Pemanasan (Warm-up)",
         "30 detik @ 5 RPS — Eliminasi bias cold-start & JIT compiler agar pod dan proxy Linkerd berada dalam kondisi siap tempur."),
        (BLUE, "📐  Fase Pengukuran Aktif (Active Window)",
         "Jendela pengukuran murni: 30 detik untuk skenario constant, 600 detik untuk ramp dan burst."),
        (GREEN,"❄️   Fase Pendinginan (Cool-down)",
         "15 detik pasca-uji untuk stabilisasi sistem kembali ke baseline."),
        (MUTED,"⏳  Fase Pengurasan (Drain Phase)",
         "Menunggu dan mengukur waktu penyelesaian sisa request yang masih berada di antrean soket sistem."),
    ]
    cy = ly
    for accent, title, body in proto:
        ph = Inches(1.08)
        add_rect(sl, lx, cy, lw, ph, CARD_BG, BORDER)
        add_rect(sl, lx, cy, Inches(0.08), ph, accent)
        add_textbox(sl, lx + Inches(0.18), cy + Inches(0.08), lw - Inches(0.28), Inches(0.32),
                    title, size=Pt(10.5), bold=True, color=NAVY)
        add_textbox(sl, lx + Inches(0.18), cy + Inches(0.38), lw - Inches(0.28), Inches(0.62),
                    body, size=Pt(9.5), color=SLATE)
        cy += ph + Inches(0.12)

    # SLA + replikasi boxes below
    bw = (lw - Inches(0.14)) / 2
    add_rect(sl, lx, cy, bw, Inches(0.72), RGBColor(0xFF, 0xF1, 0xF0), RED, Pt(1))
    add_textbox(sl, lx + Inches(0.12), cy + Inches(0.06), bw - Inches(0.2), Inches(0.6),
                "⏱  SLA Timeout: 5,0 detik\nRequest > 5.000 ms = GAGAL (HTTP 504)", size=Pt(9.5), color=RED, bold=False)

    add_rect(sl, lx + bw + Inches(0.14), cy, bw, Inches(0.72), RGBColor(0xF0, 0xFD, 0xF4), GREEN, Pt(1))
    add_textbox(sl, lx + bw + Inches(0.26), cy + Inches(0.06), bw - Inches(0.2), Inches(0.6),
                "🔁  3× Replikasi Independen (r1, r2, r3)\nMemastikan temuan bukan kebetulan sesaat", size=Pt(9.5), color=GREEN)

    # Right column: timeline
    rx = Inches(8.1); ry = Inches(1.22); rw = Inches(4.95); rh = Inches(5.8)
    add_rect(sl, rx, ry, rw, rh, CARD_BG, BORDER)
    add_textbox(sl, rx + Inches(0.15), ry + Inches(0.12), rw - Inches(0.3), Inches(0.35),
                "Siklus Hidup Pengujian (Timeline)", size=Pt(11), bold=True, color=NAVY)

    # Horizontal timeline
    tl_y = ry + Inches(1.1)
    tl_x = rx + Inches(0.25)
    tl_w = rw - Inches(0.5)
    tl_h = Inches(0.45)

    phases = [
        (GRAY_BG,  MUTED, "Warm-up\n30s @ 5 RPS",   0.10),
        (RGBColor(0xDB, 0xEA, 0xFE), BLUE,  "Active Measurement\n600 s",          0.58),
        (RGBColor(0xDC, 0xFC, 0xE7), GREEN, "Cool-down\n15 s",       0.14),
        (RGBColor(0xFE, 0xF3, 0xC7), RGBColor(0x92, 0x40, 0x08), "Drain\nPhase",  0.18),
    ]
    bx2 = tl_x
    for bg, tc, label, frac in phases:
        pw = tl_w * frac
        add_rect(sl, bx2, tl_y, pw - Inches(0.03), tl_h, bg, BORDER, Pt(0.5))
        add_textbox(sl, bx2 + Inches(0.04), tl_y + Inches(0.04), pw - Inches(0.1), tl_h,
                    label, size=Pt(8), color=tc, align=PP_ALIGN.CENTER)
        bx2 += pw

    # arrow under timeline
    add_textbox(sl, tl_x, tl_y + tl_h + Inches(0.04), tl_w, Inches(0.25),
                "──────────────────────────────────────────────────────────►  Waktu (s)",
                size=Pt(8), color=MUTED)

    # Evolution box
    ev_y = tl_y + Inches(1.2)
    add_rect(sl, rx + Inches(0.15), ev_y, rw - Inches(0.3), Inches(2.95), GRAY_BG, BORDER)
    add_textbox(sl, rx + Inches(0.25), ev_y + Inches(0.1), rw - Inches(0.5), Inches(0.32),
                "Evolusi Metodologi Pengujian", size=Pt(10), bold=True, color=NAVY)

    evo_items = [
        (RED,   "Taufik & Ali v1 — Closed-Loop",
                "Antrean tertahan di thread pool klien (256 threads).\nAngka sukses bisa semu → Coordinated Omission."),
        (GREEN, "Ali v5 — Open-Loop Hakiki",
                "Beban ditembakkan tepat waktu ke soket.\nDeadline timeout dihitung sejak jadwal kedatangan sesungguhnya."),
    ]
    ey = ev_y + Inches(0.48)
    for clr, ttl, body in evo_items:
        add_rect(sl, rx + Inches(0.25), ey, rw - Inches(0.5), Inches(0.05), clr)
        add_textbox(sl, rx + Inches(0.25), ey + Inches(0.08), rw - Inches(0.5), Inches(0.28),
                    ttl, size=Pt(9.5), bold=True, color=clr)
        add_textbox(sl, rx + Inches(0.25), ey + Inches(0.34), rw - Inches(0.5), Inches(0.52),
                    body, size=Pt(9), color=SLATE)
        ey += Inches(1.10)

    set_notes(sl,
        "Agar pengujian ini memenuhi kaidah saintifik yang ketat, seluruh eksperimen mengikuti protokol terkontrol yang "
        "terstandarisasi. Setiap pengujian diawali pemanasan 30 detik pada laju 5 RPS agar pod kontainer dan proxy Linkerd "
        "berada dalam kondisi siap tempur tanpa terganggu jeda cold-start. Kami menetapkan batas SLA sabar pengguna pada "
        "angka 5,0 detik: jika sebuah request membutuhkan waktu lebih dari 5 detik, request tersebut dianggap gagal. "
        "Seluruh pengujian diulang sebanyak tiga kali replikasi independen untuk memastikan konsistensi data. Khusus pada "
        "dataset Ali v5, kami menerapkan penegakan batas waktu deadline dari waktu jadwal kedatangan sesungguhnya, sehingga "
        "dinamika antrean mencerminkan realita sistem produksi.")


def slide5(prs):
    sl = blank_slide(prs)
    set_bg(sl, BG)
    slide_header(sl,
        "Workload Scenarios: Tiga Pola Beban Empiris",
        "Constant 25 RPS · Ramp 10→200 RPS · Burst 10→150→10 RPS (Tiga Babak)",
        5)

    lx = Inches(0.28); ly = Inches(1.22); lw = Inches(7.55)

    scenarios = [
        (NAVY, "1.  constant  —  Baseline Kestabilan Steady-State",
         ["• Beban: tetap 25 RPS selama 30 detik (total 750 request)",
          "• Tujuan: ukur latensi intrinsik dasar, stabilitas memori,",
          "  dan jitter index (CV = σ/μ) dalam kondisi bebas jenuh",
          "• Representasi: hari biasa tanpa lonjakan trafik"]),
        (BLUE, "2.  ramp  —  Eskalasi Linier Jam Sibuk",
         ["• Beban: naik bertahap 10 RPS → 200 RPS selama 600 detik",
          "  (ΔRPS ≈ 0,317 RPS/s)",
          "• Tujuan: petakan transisi titik jenuh (knee of saturation),",
          "  kurva latensi hockey-stick, dan divergensi Goodput",
          "• Representasi: jam sibuk pagi/sore hari secara bertahap"]),
        (RED,  "3.  burst  —  Guncangan Dinamis Tiga Babak",
         ["• Babak 1 (0–180s):   Santai @ 10 RPS",
          "• Babak 2 (180–300s): Lonjakan 15× ke 150 RPS  (120 detik)",
          "• Babak 3 (300–600s): Turun kembali ke 10 RPS  (300 detik)",
          "• Tujuan: surge capacity, overshoot latency, recovery time T_recover",
          "• Representasi: Flash Sale / event viral mendadak"]),
    ]

    cy = ly
    for accent, title, lines in scenarios:
        sh = Inches(1.70)
        card(sl, lx, cy, lw, sh, title, lines, accent=accent)
        cy += sh + Inches(0.15)

    # Right column: ASCII-style load graphs
    rx = Inches(8.05); ry = Inches(1.22); rw = Inches(5.0); rh = Inches(5.8)
    add_rect(sl, rx, ry, rw, rh, CARD_BG, BORDER)
    add_textbox(sl, rx + Inches(0.15), ry + Inches(0.12), rw - Inches(0.3), Inches(0.32),
                "Ilustrasi Pola Beban (Load Pattern)", size=Pt(10.5), bold=True, color=NAVY)

    # Constant mini-chart
    chart_configs = [
        (NAVY,  "constant",  "  RPS\n   25 |━━━━━━━━━━━━━━━━━━━━\n    0 +──────────────────► t",  Inches(1.3)),
        (BLUE,  "ramp",      "  RPS\n  200 |                   /\n   10 |──────────────────/\n    0 +──────────────────► t", Inches(1.5)),
        (RED,   "burst",     "  RPS\n  150 |     ┌───────────┐\n   10 |━━━━━┘           └━━━━\n    0 +──────────────────► t", Inches(1.5)),
    ]
    cy2 = ry + Inches(0.6)
    for clr, name, diagram, hh in chart_configs:
        add_rect(sl, rx + Inches(0.15), cy2, rw - Inches(0.3), hh, GRAY_BG, clr, Pt(1))
        add_textbox(sl, rx + Inches(0.25), cy2 + Inches(0.06), rw - Inches(0.5), Inches(0.28),
                    name, size=Pt(9.5), bold=True, color=clr)
        add_textbox(sl, rx + Inches(0.25), cy2 + Inches(0.30), rw - Inches(0.5), hh - Inches(0.36),
                    diagram, size=Pt(8.5), color=SLATE)
        cy2 += hh + Inches(0.18)

    set_notes(sl,
        "Untuk menguji kehandalan sistem dari berbagai sudut pandang operasional, kami merancang tiga skenario beban "
        "empiris. Skenario pertama adalah Constant pada 25 RPS, menguji kondisi santai sehari-hari. Skenario kedua adalah "
        "Ramp, di mana beban dinaikkan secara halus dari 10 hingga 200 RPS selama 10 menit untuk melihat di titik mana "
        "masing-masing arsitektur mulai terengah-engah dan mengalami kejenuhan. Skenario ketiga adalah Burst Dinamis tiga "
        "babak: 3 menit sepi pada 10 RPS, tiba-tiba dihantam serbuan 150 RPS selama 2 menit seperti fenomena Flash Sale "
        "e-commerce, lalu 5 menit fase sepi kembali untuk membuktikan apakah sistem sanggup pulih secara mandiri.")


def slide6(prs):
    sl = blank_slide(prs)
    set_bg(sl, BG)
    slide_header(sl,
        "Metrics & Data Collection: Harmonisasi Telemetri Multi-Sumber",
        "25 Kolom Time-Series (combined.csv) · 4 Formula Matematis Goodput",
        6)

    # Left column: telemetry sources
    lx = Inches(0.28); ly = Inches(1.22); lw = Inches(5.9)

    telem = [
        (NAVY,  "📡  Sisi Klien (Traffic & User Experience)",
         ["target_rps, sent, achieved_rps",
          "success, failed",
          "mean_latency_ms, p95_latency_ms"]),
        (RED,   "🖥   Sisi Kontainer Pod (Kernel & Resource Isolation)",
         ["CPU_USAGE, CPU_THROTTLED",
          "MEMORY_WORKING_SET",
          "NETWORK_RX, NETWORK_TX, RESTARTS"]),
        (GREEN, "🔗  Sisi Service Mesh (Linkerd Proxy Metrics)",
         ["LINKERD_REQUEST_RATE",
          "LINKERD_GOODPUT_RPS, LINKERD_SUCCESS_RATE",
          "LINKERD_TCP_CONNECTIONS"]),
    ]
    cy = ly
    for accent, title, lines in telem:
        ch = Inches(0.12 + 0.36 + len(lines) * 0.32 + 0.22)
        card(sl, lx, cy, lw, ch, title, lines, accent=accent)
        cy += ch + Inches(0.14)

    # total columns badge
    add_rect(sl, lx, cy, lw, Inches(0.52), RGBColor(0xE0, 0xF2, 0xFE), BLUE, Pt(1))
    add_textbox(sl, lx + Inches(0.18), cy + Inches(0.10), lw - Inches(0.36), Inches(0.32),
                "Total: 25 kolom telemetri disinkronkan per detik  →  combined.csv",
                size=Pt(10), bold=True, color=BLUE, align=PP_ALIGN.CENTER)

    # Right column: formula cards
    rx = Inches(6.5); ry = Inches(1.22); rw = Inches(6.55)

    formulas = [
        (NAVY,  "η_d — Overall Goodput Delivery Ratio",
         "η_d = ( Σ success / Σ sent ) × 100%",
         "Efisiensi penyerapan beban menjadi transaksi produktif"),
        (BLUE,  "η_s — Goodput Success Rate",
         "η_s = ( Σ success / (Σ success + Σ failed) ) × 100%",
         "Tingkat kebersihan dari error / timeout"),
        (GREEN, "η_f(t) — Instantaneous Fulfillment Ratio",
         "η_f(t) = ( Goodput(t) / Target_RPS(t) ) × 100%",
         "Kemampuan sistem memenuhi beban sesaat per detik"),
        (RED,   "Q(t) — Akumulasi Soket Aktif / Backpressure",
         "Q(t) = max( 0, Σ_τ=0^t (sent(τ) – success(τ) – failed(τ)) )",
         "In-flight koneksi yang terjebak dalam kluster (antrean riil)"),
    ]

    cy2 = ry
    for accent, title, formula, desc in formulas:
        fh = Inches(1.30)
        add_rect(sl, rx, cy2, rw, fh, CARD_BG, BORDER)
        add_rect(sl, rx, cy2, rw, Inches(0.07), accent)
        add_textbox(sl, rx + Inches(0.15), cy2 + Inches(0.12), rw - Inches(0.3), Inches(0.28),
                    title, size=Pt(10), bold=True, color=accent)
        # formula box
        add_rect(sl, rx + Inches(0.15), cy2 + Inches(0.44), rw - Inches(0.3), Inches(0.42), GRAY_BG, BORDER, Pt(0.5))
        add_textbox(sl, rx + Inches(0.25), cy2 + Inches(0.48), rw - Inches(0.5), Inches(0.34),
                    formula, size=Pt(10.5), bold=True, color=NAVY, align=PP_ALIGN.CENTER)
        add_textbox(sl, rx + Inches(0.15), cy2 + Inches(0.90), rw - Inches(0.3), Inches(0.32),
                    desc, size=Pt(9), italic=True, color=MUTED)
        cy2 += fh + Inches(0.12)

    set_notes(sl,
        "Kekuatan analisis riset ini bertumpu pada integritas data. Setiap satu detik, pipeline kolektor kami "
        "menggabungkan 25 kolom telemetri dari tiga sudut pandang berbeda: dari sisi klien yang mengukur apa yang "
        "dirasakan pengguna, dari sisi kernel Linux cAdvisor yang mengukur utilisasi fisik prosesor dan memori, serta "
        "dari sisi proxy Linkerd yang mengukur aliran soket jaringan. Dari data tersebut, kami merumuskan empat metrik "
        "utama: Delivery Ratio, Success Rate, Instantaneous Fulfillment, serta metrik antrean in-flight Q(t) untuk "
        "menghitung berapa banyak koneksi yang sedang terjebak di dalam jaringan kluster.")


def slide7(prs):
    sl = blank_slide(prs)
    set_bg(sl, BG)
    slide_header(sl,
        "Experimental Results: Plafon Kaku CPU-Bound vs. Ketangguhan Microservices",
        "Tabel Lintas Dataset (Taufik · Ali v1 · Ali v5) · Kurva Titik Jenuh Hockey-Stick",
        7)

    # Comparison table (left, full-width then image right)
    tx = Inches(0.28); ty = Inches(1.22); tw = Inches(7.8)

    headers = ["Arsitektur", "Goodput Peak", "Latency Baseline", "Latency Puncak", "Delivery Ratio (200 RPS)", "Perilaku Burst 150 RPS"]
    col_w   = [Inches(1.40), Inches(1.12), Inches(1.18), Inches(1.18), Inches(1.48), Inches(1.44)]
    col_x   = [tx]
    for w in col_w[:-1]:
        col_x.append(col_x[-1] + w)
    col_accent = [NAVY, BLUE, GREEN, RED, BLUE, GREEN]

    rows = [
        ["stateless-api", "> 200 RPS", "4,0–10,7 ms", "4,2–22,4 ms", "98,4%–100%",   "100% sukses; Latency < 5 ms; Recovery 0s"],
        ["microservices", "> 200 RPS", "8,1–16,2 ms", "8,8–25,6 ms", "100,00% ✓",    "100% sukses; Latency 8,2 ms; Recovery 0s"],
        ["cpu-bound",     "~52–57 RPS","18,9–71,8 ms","4700–8280 ms","42,9%–48,9% ✗", "Lumpuh; Latency 5.000 ms; Pulih ~20 detik"],
    ]
    row_accents = [BLUE, GREEN, RED]
    row_h = Inches(0.40)
    hdr_h = Inches(0.40)

    # header
    for i, (hdr, cx) in enumerate(zip(headers, col_x)):
        add_rect(sl, cx, ty, col_w[i] - Inches(0.02), hdr_h, NAVY)
        add_textbox(sl, cx + Inches(0.04), ty + Inches(0.07),
                    col_w[i] - Inches(0.1), hdr_h - Inches(0.1),
                    hdr, size=Pt(8.5), bold=True, color=WHITE)

    for r, (row, ra) in enumerate(zip(rows, row_accents)):
        ry2 = ty + hdr_h + r * row_h
        for i, (cell, cx) in enumerate(zip(row, col_x)):
            bg = RGBColor(0xFF, 0xFF, 0xFF) if r % 2 == 0 else GRAY_BG
            add_rect(sl, cx, ry2, col_w[i] - Inches(0.02), row_h - Inches(0.01), bg, BORDER, Pt(0.5))
            fc = ra if i == 0 else SLATE
            add_textbox(sl, cx + Inches(0.04), ry2 + Inches(0.06),
                        col_w[i] - Inches(0.1), row_h - Inches(0.1),
                        cell, size=Pt(8.5), bold=(i == 0), color=fc)

    # 3 key findings
    fy = ty + hdr_h + len(rows) * row_h + Inches(0.18)
    findings = [
        (RED,   "⚠  cpu-bound: Plafon Kaku ~56 RPS",
                "Dibatasi keras oleh kuota CFS 0,5 core. Pada 200 RPS, ~51% request pasti timeout."),
        (GREEN, "✓  microservices: 100,00% Sempurna",
                "Ali v5: 62.999 request — 0 kegagalan. Rata-rata latensi hanya 8,8 ms."),
        (BLUE,  "⚡  stateless-api: Tercepat & Terhemat",
                "Latensi sub-5 ms konsisten, konsumsi daya paling rendah dari ketiga arsitektur."),
    ]
    fw = (tw - Inches(0.2)) / 3
    fx = tx
    for clr, title, body in findings:
        add_rect(sl, fx, fy, fw, Inches(0.98), CARD_BG, clr, Pt(1.2))
        add_rect(sl, fx, fy, fw, Inches(0.06), clr)
        add_textbox(sl, fx + Inches(0.1), fy + Inches(0.1), fw - Inches(0.2), Inches(0.3),
                    title, size=Pt(9.5), bold=True, color=clr)
        add_textbox(sl, fx + Inches(0.1), fy + Inches(0.38), fw - Inches(0.2), Inches(0.55),
                    body, size=Pt(9), color=SLATE)
        fx += fw + Inches(0.1)

    # Right: visualization image
    img_x = Inches(8.2); img_y = Inches(1.22); img_w = Inches(4.85); img_h = Inches(5.8)
    try_add_image(sl, FIGURES / "04_knee_of_saturation_curves.png",
                  img_x, img_y, img_w, img_h)
    add_textbox(sl, img_x, img_y + img_h + Inches(0.04), img_w, Inches(0.25),
                "Gambar: Kurva Titik Jenuh (Knee of Saturation) — Ali v5",
                size=Pt(8), italic=True, color=MUTED, align=PP_ALIGN.CENTER)

    set_notes(sl,
        "Mari kita cermati tabel dan grafik hasil eksperimen di slide ini. Grafik ini menunjukkan fakta yang sangat "
        "konsisten di ketiga dataset. Perhatikan garis merah pada grafik titik jenuh: kurva latensi cpu-bound bergerak "
        "landai hingga angka 56 RPS, namun begitu melewati 64 RPS, kurva menekuk tajam ke atas menyerupai tongkat hoki "
        "dan membentur garis batas toleransi 5 detik. Sebaliknya, microservices membuktikan performa gemilang dengan "
        "meraih 100% Success Rate sempurna dari total 147.000 request tanpa ada satu pun yang gagal, dengan latensi "
        "rata-rata hanya 8,8 milidetik. Sementara itu, cpu-bound konsisten terjepit di angka 56 RPS, membuktikan bahwa "
        "batas prosesor 0,5 core menjadi tembok pembatas kaku yang tidak bisa ditawar.")


def slide8(prs):
    sl = blank_slide(prs)
    set_bg(sl, BG)
    slide_header(sl,
        "Observed Phenomenon: Fenomena Kritis & Rekomendasi Rekayasa Industri",
        "Hockey-Stick Latency · Coordinated Omission · Self-Healing 20s · 3 Rekomendasi Produksi",
        8)

    # Left column: phenomena + recommendations
    lx = Inches(0.28); ly = Inches(1.22); lw = Inches(7.55)

    phenomena = [
        (RED,   "📈  1. Kurva Hockey-Stick & Hukum Little (M/M/1)",
         ["Saat λ → μ, utilisasi ρ → 1,0.  Waktu tunggu W = 1 / (μ·(1−ρ)) melonjak vertikal.",
          "Penambahan beban di atas 56 RPS hanya memperpanjang antrean sia-sia (wasteful computation)."]),
        (NAVY,  "🎭  2. Bias Pengujian: Coordinated Omission",
         ["Closed-loop (Taufik/Ali v1): antrean tertahan di memori klien → angka sukses semu.",
          "Open-loop (Ali v5): membongkar kegagalan timeout riil dan antrean soket aktif yang sesungguhnya."]),
        (GREEN, "🔄  3. Resiliensi Lonjakan & Self-Healing ~20 Detik",
         ["Burst 150 RPS: cpu-bound mampu menormalkan antrean dan kembali ke latensi normal (18,7 ms)",
          "dalam tempo ~20 detik tanpa restart pod (zero restart) — mekanisme pemulihan mandiri."]),
    ]

    cy = ly
    for accent, title, lines in phenomena:
        ph = Inches(0.14 + 0.36 + len(lines) * 0.36 + 0.16)
        card(sl, lx, cy, lw, ph, title, lines, accent=accent)
        cy += ph + Inches(0.13)

    # Recommendations
    add_textbox(sl, lx, cy, lw, Inches(0.32),
                "💡  Tiga Rekomendasi Rekayasa untuk Sistem Produksi Cloud:",
                size=Pt(10.5), bold=True, color=NAVY)
    cy += Inches(0.36)

    recs = [
        (RED,   "Fail-Fast Load Shedding (Ingress)",
                "limit_req ... nodelay: tolak request berlebih < 1 ms (HTTP 429)\ndaripada pengguna menunggu 5 detik lalu timeout."),
        (BLUE,  "Autoscaling Proaktif (HPA)",
                "Pasang Horizontal Pod Autoscaler yang memicu replikasi\nsebelum beban menyentuh ambang jenuh 56 RPS."),
        (GREEN, "Adopsi Service Mesh (Linkerd)",
                "Kikis mitos 'mesh memperlambat': Linkerd terbukti tangguh\npada 100% dari 147.000+ request di 200 RPS."),
    ]
    rw2 = (lw - Inches(0.2)) / 3
    rx3 = lx
    rh3 = Inches(1.15)
    for clr, title, body in recs:
        add_rect(sl, rx3, cy, rw2, rh3, CARD_BG, clr, Pt(1.2))
        add_rect(sl, rx3, cy, rw2, Inches(0.07), clr)
        add_textbox(sl, rx3 + Inches(0.1), cy + Inches(0.12), rw2 - Inches(0.2), Inches(0.3),
                    title, size=Pt(9.5), bold=True, color=clr)
        add_textbox(sl, rx3 + Inches(0.1), cy + Inches(0.42), rw2 - Inches(0.2), Inches(0.68),
                    body, size=Pt(9), color=SLATE)
        rx3 += rw2 + Inches(0.1)

    # Right: visualization image
    img_x = Inches(8.05); img_y = Inches(1.22); img_w = Inches(5.0); img_h = Inches(5.8)
    try_add_image(sl, FIGURES / "05_goodput_triad_and_fulfillment.png",
                  img_x, img_y, img_w, img_h)
    add_textbox(sl, img_x, img_y + img_h + Inches(0.04), img_w, Inches(0.25),
                "Gambar: Goodput Triad & Fulfillment Ratio — Ali v5",
                size=Pt(8), italic=True, color=MUTED, align=PP_ALIGN.CENTER)

    set_notes(sl,
        "Sebagai penutup, riset ini memberikan pelajaran rekayasa yang sangat fundamental bagi industri perangkat lunak "
        "modern. Pertama, kita membuktikan secara matematis dan empiris bahwa membiarkan sistem berjalan di atas titik "
        "jenuh tanpa perlindungan adalah pemborosan fatal: server bekerja keras menghabiskan listrik dan CPU untuk "
        "memproses pesanan yang pada akhirnya dibatalkan oleh pengguna karena timeout. Kedua, kami membuktikan pentingnya "
        "pengujian beban open-loop untuk menghindari ilusi Coordinated Omission. Rekomendasi konkret kami: pasanglah "
        "mekanisme Fail-Fast Load Shedding di gerbang Ingress NGINX menggunakan limit_req nodelay agar kelebihan beban "
        "ditolak seketika dalam 1 milidetik, pasang Autoscaler otomatis pada aplikasi komputasi sebelum menyentuh batas "
        "jenuh 56 RPS, dan jangan ragu mengadopsi Service Mesh Linkerd karena terbukti tangguh mengawal ratusan ribu "
        "transaksi dengan kebersihan 100 persen. Terima kasih, kami siap menerima pertanyaan dan masukan dari dewan penguji.")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def build():
    prs = Presentation()
    prs.slide_width  = W
    prs.slide_height = H

    for fn in (slide1, slide2, slide3, slide4, slide5, slide6, slide7, slide8):
        fn(prs)

    out = Path(__file__).parent / "Cloud_Dynamics_Empirical_Analysis.pptx"
    prs.save(str(out))
    print(f"✅  Saved: {out}")


if __name__ == "__main__":
    build()
