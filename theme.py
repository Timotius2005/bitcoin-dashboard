"""Token desain "Voltage" — sumber kebenaran tunggal untuk warna dan font.

Nilai di sini disalin dari artboard Sistem desain, bukan dikira-kira. Kalau
desainnya berubah, ubah di sini saja — chart, komponen HTML, dan tema
Streamlit semuanya membaca dari modul ini.

Aturan peran warna yang tidak boleh dilanggar:
  CYAN     hanya untuk data bullish
  MAGENTA  hanya untuk data bearish
  VOLT     hanya untuk keadaan antarmuka (tombol aktif, denyut, crosshair)
  PURPLE   hanya untuk atmosfer (pendar, ghost aberasi)
Kalau VOLT atau PURPLE muncul sebagai warna sebuah mark data, itu bug:
pembacaan grafiknya jadi rusak karena warna kehilangan arti tunggalnya.
"""

from __future__ import annotations

# ── Permukaan ────────────────────────────────────────────────────────────
GROUND = "#121214"       # dasar halaman
PANEL = "#0C0C0E"        # panel cekung (grafik, strip indikator)
RAISED = "#17171B"       # baris hover, tooltip
TRACK = "#1B1B20"        # alur bar kategori
HAIRLINE = "#23232A"     # garis pemisah
HAIRLINE_STRONG = "#33333C"
GRID = "#1C1C22"         # gridline chart, lebih redup dari hairline
AXIS = "#4A4A56"         # sumbu nol

# ── Teks ─────────────────────────────────────────────────────────────────
INK = "#FFFFFF"
INK_2 = "#9A9AA8"
INK_3 = "#6B6B78"

# ── Data ─────────────────────────────────────────────────────────────────
CYAN = "#00F0FF"         # bullish
MAGENTA = "#FF007A"      # bearish

# ── Antarmuka & atmosfer ─────────────────────────────────────────────────
VOLT = "#CCFF00"         # keadaan antarmuka saja
PURPLE = "#BD00FF"       # atmosfer saja

# ── Font ─────────────────────────────────────────────────────────────────
FONT_SANS = "'Chakra Petch', 'Bai Jamjuree', system-ui, sans-serif"
FONT_MONO = "'JetBrains Mono', ui-monospace, Menlo, monospace"
GOOGLE_FONTS = (
    "https://fonts.googleapis.com/css2"
    "?family=Chakra+Petch:wght@300;400;500;600;700"
    "&family=JetBrains+Mono:wght@400;500;700"
    "&display=swap"
)

# ── Spesifikasi mark (dari artboard Sistem) ──────────────────────────────
LINE_WIDTH = 2
AREA_OPACITY = 0.12      # neon terlalu terang untuk blok pekat; ini batasnya
GLOW_WIDTH = 8           # garis lebar transparan di bawah garis utama
GLOW_OPACITY = 0.22
MARKER_SIZE = 9
BAR_HEIGHT = 18

# ── Ambang klasifikasi skor ──────────────────────────────────────────────
BANDS = [
    (50, 101, "bullish kuat", CYAN),
    (20, 50, "bullish", CYAN),
    (-19, 20, "netral", INK_3),
    (-49, -19, "bearish", MAGENTA),
    (-100, -49, "bearish kuat", MAGENTA),
]


def score_color(value: float | None) -> str:
    """Warna untuk sebuah nilai skor: cyan positif, magenta negatif."""
    if value is None:
        return INK_3
    if value > 0:
        return CYAN
    if value < 0:
        return MAGENTA
    return INK_3


def label_color(label: str | None) -> str:
    if not label:
        return INK_3
    if "bullish" in label:
        return CYAN
    if "bearish" in label:
        return MAGENTA
    return INK_3
