"""Blok HTML kustom sesuai desain "Voltage".

Komponen bawaan Streamlit tidak bisa dibentuk seperti desainnya — sudut
menyudut, aberasi kromatik, bar divergen dari sumbu tengah — jadi bagian
yang butuh kendali penuh ditulis sebagai HTML dan disuntikkan. Yang tetap
memakai komponen Streamlit hanya grafik (Plotly) dan kontrol rentang.

Semua warna diambil dari theme.py, tidak ada hex yang ditulis langsung di
sini, supaya perubahan desain cukup dilakukan di satu tempat.
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone

import theme as T

# ── Format angka gaya Indonesia ──────────────────────────────────────────

BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
         "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
BULAN_PANJANG = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli",
                 "Agustus", "September", "Oktober", "November", "Desember"]
NAMA_KATEGORI = {"trend": "Tren", "momentum": "Momentum", "sentiment": "Sentimen",
                 "volatility": "Volatilitas & volume"}


def rb(nilai: float | None, kosong: str = "—") -> str:
    """Ribuan dengan titik: 79112 -> 79.112"""
    if nilai is None:
        return kosong
    return f"{round(nilai):,}".replace(",", ".")


def des(nilai: float | None, digit: int = 2, kosong: str = "—") -> str:
    """Desimal dengan koma: 62.73 -> 62,73"""
    if nilai is None:
        return kosong
    return f"{nilai:,.{digit}f}".replace(",", "~").replace(".", ",").replace("~", ".")


def persen(nilai: float | None, kosong: str = "—") -> str:
    if nilai is None:
        return kosong
    return ("+" if nilai > 0 else "−" if nilai < 0 else "") + des(abs(nilai), 2) + "%"


def skor(nilai: int | None, kosong: str = "—") -> str:
    if nilai is None:
        return kosong
    return ("+" if nilai > 0 else "−" if nilai < 0 else "") + str(abs(nilai))


def tanggal_pendek(iso: str) -> str:
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.day:02d} {BULAN[d.month - 1]}"


def tanggal_panjang(iso: str) -> str:
    d = datetime.strptime(iso, "%Y-%m-%d")
    return f"{d.day:02d} {BULAN_PANJANG[d.month - 1]} {d.year}"


def umur_jam(generated_at: str | None) -> float | None:
    if not generated_at:
        return None
    try:
        saat = datetime.fromisoformat(generated_at)
    except ValueError:
        return None
    if saat.tzinfo is None:
        saat = saat.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - saat).total_seconds() / 3600


def _e(teks: object) -> str:
    """Escape — isi JSON berasal dari file luar, jangan pernah dipercaya mentah."""
    return html.escape(str(teks), quote=True)


# Dipakai saat skrip dijalankan ulang: animasi masuk dimatikan, tapi sapuan
# grafik dibiarkan (lebih cepat) karena datanya memang baru berubah.
INTRO_OFF = '''
  .rise, .barL, .barR, .drop, .bloom,
  .bar-fill::after { animation: none !important; }
  /* Loop tak berujung tetap jalan setelah rerun; yang dilepas cuma bagian
     animasi masuknya, supaya gerak berulang tidak ikut mati saat difilter. */
  .gL { animation: glitchLoopL 5.5s linear 0s infinite !important; }
  .gR { animation: glitchLoopR 5.5s linear 0s infinite !important; }
  .gM { animation: glitchLoopM 5.5s linear 0s infinite !important; }
  .rule { animation: flowRule 7s linear 0s infinite !important; }
  [data-testid="stPlotlyChart"],
  [data-testid="stPlotlyChart"]::after { animation-duration: 0.85s !important;
                                         animation-delay: 0s !important; }
'''


# ── Stylesheet global ────────────────────────────────────────────────────

def css(intro: bool = True) -> str:
    """Stylesheet global.

    `intro` mematikan animasi masuk saat skrip dijalankan ulang (misal
    waktu tombol rentang ditekan). Tanpa ini seluruh halaman akan
    memutar ulang koreografinya setiap kali difilter — gerak jadi
    kebisingan, bukan penanda bahwa ada yang berubah.
    """
    matikan_intro = "" if intro else INTRO_OFF
    return f"""
<link rel="stylesheet" href="{T.GOOGLE_FONTS}">
<style>
  :root {{
    --ground: {T.GROUND}; --panel: {T.PANEL}; --raised: {T.RAISED};
    --track: {T.TRACK}; --hair: {T.HAIRLINE}; --hair-strong: {T.HAIRLINE_STRONG};
    --grid: {T.GRID}; --axis: {T.AXIS};
    --ink: {T.INK}; --ink2: {T.INK_2}; --ink3: {T.INK_3};
    --cyan: {T.CYAN}; --magenta: {T.MAGENTA}; --volt: {T.VOLT}; --purple: {T.PURPLE};
  }}

  /* Buang chrome bawaan Streamlit supaya halaman jadi kanvas kosong. */
  [data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
  [data-testid="stDecoration"], [data-testid="stStatusWidget"] {{ display: none !important; }}
  [data-testid="stAppViewContainer"], .stApp {{ background: var(--ground) !important; }}
  [data-testid="stMainBlockContainer"], .block-container {{
    padding: 0 !important; max-width: 100% !important;
  }}
  [data-testid="stVerticalBlock"] {{ gap: 0 !important; }}
  [data-testid="stElementContainer"] {{ margin: 0 !important; }}

  html, body, .stApp {{
    background: var(--ground);
    color: var(--ink);
    font-family: {T.FONT_SANS};
    -webkit-font-smoothing: antialiased;
  }}
  a {{ color: var(--cyan); text-decoration: none; }}
  a:hover {{ color: var(--volt); }}

  .wrap {{ padding: 0 48px; }}
  /* Kolom dan grafik Streamlit tidak ikut .wrap, jadi diberi padding halaman
     di sini. Panel full-bleed tetap membentang penuh dan memakai .wrap di dalam. */
  [data-testid="stHorizontalBlock"] {{ padding: 0 48px !important; }}
  [data-testid="stPlotlyChart"] {{ padding: 0 !important; overflow: visible !important; }}
  .js-plotly-plot .plotly .modebar {{ display: none !important; }}
  .kicker {{
    font-family: {T.FONT_MONO}; font-size: 10.5px; font-weight: 500;
    letter-spacing: 0.24em; text-transform: uppercase; color: var(--ink3);
  }}
  .num {{ font-family: {T.FONT_MONO}; font-variant-numeric: tabular-nums; }}
  .head {{ font-weight: 600; letter-spacing: 0.01em; text-transform: uppercase; }}
  .sect {{ font-size: 22px; font-weight: 600; text-transform: uppercase;
           margin-top: 9px; line-height: 1; }}
  .panel {{ background: var(--panel); border-top: 1px solid var(--hair);
            border-bottom: 1px solid var(--hair); }}

  /* ── Gerak: satu reveal berurutan saat halaman dibuka ── */
  @keyframes riseIn  {{ from {{ opacity: 0; transform: translateY(16px); }} to {{ opacity: 1; transform: none; }} }}
  @keyframes ruleIn  {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
  @keyframes growL   {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
  @keyframes dropIn  {{ from {{ opacity: 0; transform: translateY(-10px); }} to {{ opacity: 1; transform: none; }} }}
  @keyframes bloomIn {{ from {{ opacity: 0; transform: scale(0.82); }} to {{ opacity: 1; transform: scale(1); }} }}
  @keyframes beat    {{ 0%, 100% {{ opacity: 1; box-shadow: 0 0 8px 1px rgba(204,255,0,0.7); }}
                        50% {{ opacity: 0.35; box-shadow: none; }} }}
  .rise  {{ animation: riseIn 0.75s cubic-bezier(0.2,0.75,0.2,1) both; }}
  .rule  {{ transform-origin: left center;
            animation: ruleIn 1.1s cubic-bezier(0.25,0.8,0.25,1) both,
                       flowRule 7s linear 1.1s infinite; }}
  .barL  {{ transform-origin: left center;  animation: growL 0.9s cubic-bezier(0.2,0.8,0.2,1) both; }}
  .barR  {{ transform-origin: right center; animation: growL 0.9s cubic-bezier(0.2,0.8,0.2,1) both; }}
  .drop  {{ animation: dropIn 0.7s cubic-bezier(0.2,0.8,0.2,1) both; }}
  .bloom {{ animation: bloomIn 1.7s cubic-bezier(0.2,0.7,0.2,1) 0.15s both; }}
  .live  {{ animation: beat 2.4s ease-in-out infinite; }}

  /* ── Grafik: tersingkap dari kiri ke kanan, meniru garis yang menggambar
        dirinya sendiri. Plotly tidak punya animasi masuk sendiri.
        Berhenti di inset kanan -50px, bukan 0, supaya label pita di gutter
        kanan tidak ikut terpotong saat animasinya selesai. ── */
  @keyframes wipeIn {{ from {{ clip-path: inset(0 100% 0 0); }}
                       to   {{ clip-path: inset(0 -50px 0 0); }} }}
  @keyframes scanEdge {{ 0%   {{ left: 0; opacity: 0; }}
                         12%  {{ opacity: 1; }}
                         88%  {{ opacity: 1; }}
                         100% {{ left: 100%; opacity: 0; }} }}
  [data-testid="stPlotlyChart"] {{
    position: relative;
    animation: wipeIn 1.9s cubic-bezier(0.35, 0, 0.15, 1) 0.35s both;
  }}
  [data-testid="stPlotlyChart"]::after {{
    content: ""; position: absolute; top: 8%; bottom: 14%; width: 2px;
    background: var(--volt); box-shadow: 0 0 14px 2px rgba(204, 255, 0, 0.75);
    pointer-events: none;
    animation: scanEdge 1.9s cubic-bezier(0.35, 0, 0.15, 1) 0.35s both;
  }}

  /* ── Angka hero: ghost aberasi datang terpisah lalu mengunci ── */
  @keyframes ghostL {{ 0%  {{ transform: translate(-16px, 5px); opacity: 0; }}
                       45% {{ opacity: 0.75; }}
                       72% {{ transform: translate(3px, -2px); }}
                       100%{{ transform: translate(0, 0); opacity: 0.55; }} }}
  @keyframes ghostR {{ 0%  {{ transform: translate(16px, -5px); opacity: 0; }}
                       45% {{ opacity: 0.7; }}
                       72% {{ transform: translate(-3px, 2px); }}
                       100%{{ transform: translate(0, 0); opacity: 0.5; }} }}
  .gL {{ animation: ghostL 1.25s cubic-bezier(0.2, 0.8, 0.2, 1) 0.2s both,
                    glitchLoopL 5.5s linear 1.6s infinite; }}
  .gR {{ animation: ghostR 1.25s cubic-bezier(0.2, 0.8, 0.2, 1) 0.2s both,
                    glitchLoopR 5.5s linear 1.6s infinite; }}
  .gM {{ animation: glitchLoopM 5.5s linear 1.6s infinite; }}

  /* ── Glitch berulang pada angka hero ───────────────────────────────
        Sebagian besar siklus diam. Letupannya cuma ~0,4 detik tiap 5,5
        detik: angka ini informasi terpenting di halaman, dan getaran
        terus-menerus membuatnya tidak terbaca. Ghost RGB-nya yang pecah
        dan tersayat, lapisan putihnya nyaris tidak bergerak. ── */
  @keyframes glitchLoopL {{
    0%, 84%, 100% {{ transform: translate(0, 0); clip-path: inset(0 0 0 0); opacity: 0.55; }}
    85%  {{ transform: translate(-9px, 1px);  clip-path: inset(10% 0 58% 0); opacity: 0.95; }}
    87%  {{ transform: translate(6px, -2px);  clip-path: inset(60% 0 6% 0);  opacity: 0.9; }}
    89%  {{ transform: translate(-5px, 1px);  clip-path: inset(34% 0 40% 0); opacity: 0.9; }}
    91%  {{ transform: translate(3px, 0);     clip-path: inset(0 0 72% 0);   opacity: 0.8; }}
    93%  {{ transform: translate(0, 0);       clip-path: inset(0 0 0 0);     opacity: 0.55; }}
  }}
  @keyframes glitchLoopR {{
    0%, 84%, 100% {{ transform: translate(0, 0); clip-path: inset(0 0 0 0); opacity: 0.5; }}
    85%  {{ transform: translate(9px, -1px);  clip-path: inset(56% 0 12% 0); opacity: 0.9; }}
    87%  {{ transform: translate(-6px, 2px);  clip-path: inset(8% 0 62% 0);  opacity: 0.95; }}
    89%  {{ transform: translate(5px, -1px);  clip-path: inset(38% 0 36% 0); opacity: 0.85; }}
    91%  {{ transform: translate(-3px, 0);    clip-path: inset(70% 0 0 0);   opacity: 0.8; }}
    93%  {{ transform: translate(0, 0);       clip-path: inset(0 0 0 0);     opacity: 0.5; }}
  }}
  @keyframes glitchLoopM {{
    0%, 84%, 100% {{ transform: translate(0, 0); }}
    86%  {{ transform: translate(2px, -1px); }}
    88%  {{ transform: translate(-2px, 1px); }}
    90%  {{ transform: translate(1px, 0); }}
    92%  {{ transform: translate(0, 0); }}
  }}

  /* ── Garis masthead: gradien mengalir terus.
        Urutan warnanya ditulis dua siklus penuh dan ditutup warna awal,
        dengan background-size 200% — bergeser satu lebar wadah berarti
        tepat satu siklus, jadi pengulangannya tidak berkedut. ── */
  @keyframes flowRule {{ from {{ background-position: 0% 50%; }}
                         to   {{ background-position: 100% 50%; }} }}
  .flow-rule {{
    background-image: linear-gradient(90deg,
      {T.CYAN}, {T.PURPLE}, {T.MAGENTA}, {T.VOLT},
      {T.CYAN}, {T.PURPLE}, {T.MAGENTA}, {T.VOLT}, {T.CYAN}) !important;
    background-size: 200% 100%;
  }}

  /* ── Bar kategori: satu kilatan lewat setelah bar selesai tumbuh ── */
  @keyframes sweep {{ from {{ transform: translateX(-130%); }}
                      to   {{ transform: translateX(130%); }} }}
  .bar-fill {{ position: relative; overflow: hidden; }}
  .bar-fill::after {{
    content: ""; position: absolute; inset: 0; pointer-events: none;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.5), transparent);
    animation: sweep 1.05s ease-out 1.45s both;
  }}

  /* ── Sel indikator: mengangkat sedikit dan menyala saat disorot ── */
  .ind {{ transition: transform 0.2s ease, opacity 0.2s ease; }}
  .ind:hover {{ transform: translateY(-3px); }}
  .ind:hover .ind-val {{ text-shadow: 0 0 16px currentColor; }}
  .ind-val {{ transition: text-shadow 0.25s ease; }}

  /* ── Baris yang bisa disorot ── */
  .sig-row {{ transition: background-color 0.2s ease, box-shadow 0.2s ease; }}
  .sig-row:hover {{ background-color: var(--raised); box-shadow: inset 2px 0 0 var(--volt); }}
  .sig-row:hover .sig-detail {{ color: var(--ink2); }}
  .sig-detail {{ transition: color 0.2s ease; }}
  .tbl-row {{ transition: background-color 0.18s ease; }}
  .tbl-row:hover {{ background-color: var(--raised); }}

  /* ── Kontrol rentang Streamlit, diwarnai ulang jadi volt ── */
  [data-testid="stSegmentedControl"] button {{
    background: transparent !important; border: 1px solid var(--hair-strong) !important;
    border-radius: 0 !important; color: var(--ink3) !important;
    font-family: {T.FONT_MONO} !important; font-size: 11px !important;
    letter-spacing: 0.12em !important;
  }}
  [data-testid="stSegmentedControl"] button[aria-checked="true"],
  [data-testid="stSegmentedControl"] button[aria-selected="true"] {{
    background: var(--volt) !important; color: var(--ground) !important;
    border-color: var(--volt) !important;
  }}

  /* ── Tekstur: scanline CRT + butiran film ── */
  .fx {{
    position: fixed; inset: 0; pointer-events: none; z-index: 9999;
  }}
  .fx-scan {{
    opacity: 0.35;
    background: repeating-linear-gradient(180deg,
      rgba(255,255,255,0.028) 0px, rgba(255,255,255,0.028) 1px,
      rgba(0,0,0,0) 1px, rgba(0,0,0,0) 3px);
  }}

  {matikan_intro}

  @media (prefers-reduced-motion: reduce) {{
    *, *::before, *::after {{ animation: none !important; transition: none !important; }}
  }}
</style>
<div class="fx fx-scan"></div>
"""


# ── Blok halaman ─────────────────────────────────────────────────────────

def masthead(baris, umur: float | None, basi: bool) -> str:
    tanda = (
        f'<div class="num" style="background:{T.MAGENTA};color:{T.INK};font-size:11.5px;'
        f'font-weight:700;letter-spacing:0.1em;padding:7px 16px;'
        f'clip-path:polygon(9px 0,100% 0,calc(100% - 9px) 100%,0 100%)">DATA BASI</div>'
        if basi else
        f'<div class="num" style="background:{T.VOLT};color:{T.GROUND};font-size:11.5px;'
        f'font-weight:700;letter-spacing:0.1em;padding:7px 16px;'
        f'clip-path:polygon(9px 0,100% 0,calc(100% - 9px) 100%,0 100%)">'
        f'EDISI {_e(tanggal_panjang(baris["date"]).upper())}</div>'
    )
    umur_teks = "baru saja" if umur is None else f"{des(umur, 1)} jam lalu"
    warna_denyut = T.MAGENTA if basi else T.VOLT

    return f"""
<div class="wrap rise" style="display:flex;align-items:center;justify-content:space-between;
     padding-top:28px;padding-bottom:18px">
  <div style="display:flex;align-items:center;gap:20px">
    <div class="head" style="font-size:38px;font-weight:700;letter-spacing:0.02em;line-height:1">BITCOIN HARIAN</div>
    <div style="width:1px;height:26px;background:{T.HAIRLINE_STRONG}"></div>
    <div class="kicker" style="letter-spacing:0.3em">Rule-based</div>
  </div>
  <div style="display:flex;align-items:center;gap:22px">
    <div style="display:flex;align-items:center;gap:9px">
      <div class="live" style="width:6px;height:6px;background:{warna_denyut}"></div>
      <div class="num" style="font-size:11.5px;color:{T.INK_2}">Dianalisis {_e(umur_teks)}</div>
    </div>
    {tanda}
  </div>
</div>
<div class="wrap"><div class="rule flow-rule" style="height:2px"></div></div>
"""


def narasi(baris, sebelum) -> str:
    """Kalimat pembuka yang disusun dari angka, bukan dikarang.

    Sengaja hanya menyatakan ulang apa yang ada di data — pipeline yang
    menentukan kesimpulan, tampilan ini cuma menceritakannya.
    """
    kategori = {
        "Tren": baris["cat_trend"], "Momentum": baris["cat_momentum"],
        "Sentimen": baris["cat_sentiment"], "Volatilitas": baris["cat_volatility"],
    }
    aktif = {k: v for k, v in kategori.items() if v is not None}
    kalimat: list[str] = []

    if sebelum is not None and sebelum["score"] is not None:
        delta = baris["score"] - sebelum["score"]
        warna = T.label_color(sebelum["label"])
        kalimat.append(
            f'Kemarin <span style="color:{warna};font-weight:500">'
            f'{_e(sebelum["label"])} {skor(sebelum["score"])}</span>'
            + (f", bergerak {skor(delta)} poin." if delta else ", tidak bergerak.")
        )

    if aktif:
        positif = {k: v for k, v in aktif.items() if v > 0}
        negatif = {k: v for k, v in aktif.items() if v < 0}
        if positif and negatif:
            atas = max(positif, key=lambda k: positif[k])
            bawah = min(negatif, key=lambda k: negatif[k])
            kalimat.append(
                f"{atas} ({skor(aktif[atas])}) dan {bawah.lower()} ({skor(aktif[bawah])}) "
                f"saling bertentangan, jadi skornya tertahan di "
                f"<span style=\"color:{T.label_color(baris['label'])}\">{_e(baris['label'])}</span>."
            )
        else:
            arah = "searah naik" if positif else "searah turun"
            kalimat.append(
                f"Semua kategori aktif {arah} — tidak ada sinyal yang berlawanan hari ini."
            )

    tidak_aktif = [k for k, v in kategori.items() if v is None]
    if tidak_aktif:
        kalimat.append(
            f"{', '.join(tidak_aktif)} tidak menyumbang skor; bobotnya dinormalisasi ulang."
        )

    return " ".join(kalimat)


def hero(baris, sebelum) -> str:
    nilai = baris["score"]
    warna = T.score_color(nilai)
    posisi = max(0.0, min(100.0, (nilai + 100) / 2))

    delta_blok = ""
    if sebelum is not None and sebelum["score"] is not None:
        delta = nilai - sebelum["score"]
        if delta != 0:
            naik = delta > 0
            warna_delta = T.CYAN if naik else T.MAGENTA
            panah = ("M5.5 11V1M5.5 1L1.5 5M5.5 1L9.5 5" if naik
                     else "M5.5 1V11M5.5 11L1.5 7M5.5 11L9.5 7")
            delta_blok = f"""
            <div style="display:flex;align-items:center;gap:8px;margin-top:14px">
              <svg width="11" height="12" viewBox="0 0 11 12" fill="none">
                <path d="{panah}" stroke="{warna_delta}" stroke-width="1.7"
                      stroke-linecap="round" stroke-linejoin="round"></path>
              </svg>
              <div class="num" style="font-size:13px;color:{warna_delta}">
                {abs(delta)} poin dari kemarin</div>
            </div>"""

    return f"""
<div style="position:relative">
  <div class="bloom" style="position:absolute;left:-80px;top:-60px;width:940px;height:560px;
       pointer-events:none;background:radial-gradient(ellipse at 30% 42%,
       {_rgba(warna, 0.20)},{_rgba(T.PURPLE, 0.09)} 40%,{_rgba(T.PURPLE, 0)} 68%)"></div>

  <div style="position:relative;padding-top:40px">
    <div class="kicker rise" style="animation-delay:0.16s">Skor komposit hari ini</div>
    <div style="display:flex;align-items:baseline;gap:28px;margin-top:16px">
      <div class="rise" style="position:relative;animation-delay:0.2s">
        <div aria-hidden="true" class="gL" style="position:absolute;left:-3px;top:2px;font-size:132px;
             font-weight:700;line-height:0.82;letter-spacing:-0.035em;color:{T.CYAN};opacity:0.55">{skor(nilai)}</div>
        <div aria-hidden="true" class="gR" style="position:absolute;left:3px;top:-2px;font-size:132px;
             font-weight:700;line-height:0.82;letter-spacing:-0.035em;color:{T.PURPLE};opacity:0.5">{skor(nilai)}</div>
        <div class="gM" style="position:relative;font-size:132px;font-weight:700;line-height:0.82;
             letter-spacing:-0.035em;color:{T.INK};text-shadow:0 0 34px {_rgba(warna, 0.6)}">{skor(nilai)}</div>
      </div>
      <div class="rise" style="animation-delay:0.28s">
        <div class="head" style="font-size:32px;font-weight:600;line-height:1;color:{warna};
             text-shadow:0 0 18px {_rgba(warna, 0.45)}">{_e(baris["label"] or "").upper()}</div>
        {delta_blok}
        <div class="num" style="font-size:11px;color:{T.INK_3};margin-top:8px">skala &minus;100 … +100</div>
      </div>
    </div>

    <div class="rise" style="margin-top:36px;max-width:600px;animation-delay:0.36s">
      <div style="position:relative;height:12px;background:{T.TRACK}">
        <div class="barR" style="position:absolute;left:0;top:0;width:30%;height:100%;
             background:linear-gradient(90deg,{T.MAGENTA},{_rgba(T.MAGENTA, 0.25)});animation-delay:0.5s"></div>
        <div class="barL" style="position:absolute;left:70%;top:0;width:30%;height:100%;
             background:linear-gradient(90deg,{_rgba(T.CYAN, 0.25)},{T.CYAN});animation-delay:0.5s"></div>
        <div style="position:absolute;left:50%;top:-6px;width:1px;height:24px;background:{T.AXIS}"></div>
        <div class="drop" style="position:absolute;left:{posisi:.1f}%;top:-8px;width:3px;height:28px;
             background:{T.INK};box-shadow:0 0 12px 2px {_rgba(warna, 0.9)};animation-delay:0.95s"></div>
      </div>
      <div style="display:flex;justify-content:space-between;margin-top:10px">
        <div class="num" style="font-size:10px;color:{T.INK_3}">&minus;100</div>
        <div class="num" style="font-size:10px;color:{T.INK_3}">&minus;50</div>
        <div class="num" style="font-size:10px;color:{T.INK_2}">0</div>
        <div class="num" style="font-size:10px;color:{T.INK_3}">+50</div>
        <div class="num" style="font-size:10px;color:{T.INK_3}">+100</div>
      </div>
    </div>

    <div class="rise" style="font-size:18px;font-weight:300;line-height:1.55;color:{T.INK_2};
         margin-top:30px;max-width:620px;text-wrap:pretty;animation-delay:0.44s">
      {narasi(baris, sebelum)}
    </div>
  </div>
</div>
"""


def price_header(baris) -> str:
    def kolom(judul: str, nilai: float | None) -> str:
        warna = T.CYAN if (nilai or 0) > 0 else T.MAGENTA if (nilai or 0) < 0 else T.INK_3
        return f"""
        <div>
          <div class="kicker" style="font-size:9.5px;letter-spacing:0.18em">{judul}</div>
          <div class="num" style="font-size:19px;font-weight:500;color:{warna};margin-top:7px">{persen(nilai)}</div>
        </div>"""

    return f"""
<div class="rise" style="border-left:1px solid {T.HAIRLINE};padding-left:32px;padding-top:40px;
     animation-delay:0.3s">
  <div class="kicker">Harga penutupan · {_e(baris["date"])}</div>
  <div class="num" style="font-size:46px;font-weight:700;letter-spacing:-0.03em;
       margin-top:16px;line-height:1">US${rb(baris["close"])}</div>
  <div style="display:flex;gap:40px;margin-top:26px">
    {kolom("1 hari", baris["change_1d_pct"])}
    {kolom("7 hari", baris["change_7d_pct"])}
    {kolom("30 hari", baris["change_30d_pct"])}
  </div>
</div>
"""


def _catatan_penyesuaian(adj: dict | None) -> str:
    """Catatan di bawah bar kalau skor kategorinya diubah aturan antar-indikator.

    Tanpa ini, bar tren yang diredam ADX terlihat seperti skor tren yang
    memang lemah - padahal sinyal trennya kuat dan cuma dianggap kurang andal.
    """
    if not adj:
        return ""
    return (f'<div class="num" style="font-size:10px;color:{T.INK_3};margin-top:7px">'
            f'diredam ×{des(adj.get("factor"), 1)} dari {skor(adj.get("before"))} · '
            f'{_e(adj.get("reason", ""))}</div>')


def category_bars(baris) -> str:
    definisi = [
        ("trend", "Tren", baris["cat_trend"], 0.35),
        ("momentum", "Momentum", baris["cat_momentum"], 0.25),
        ("sentiment", "Sentimen", baris["cat_sentiment"], 0.25),
        ("volatility", "Volatilitas &amp; volume", baris["cat_volatility"], 0.15),
    ]
    try:
        penyesuaian = {a["category"]: a
                       for a in json.loads(baris.get("adjustments_json") or "[]")}
    except (json.JSONDecodeError, TypeError, KeyError):
        penyesuaian = {}
    potong_kanan = "polygon(0 0,100% 0,calc(100% - 6px) 100%,0 100%)"
    potong_kiri = "polygon(6px 0,100% 0,100% 100%,0 100%)"

    blok = []
    for i, (kunci, nama, nilai, bobot) in enumerate(definisi):
        if nilai is None:
            blok.append(f"""
            <div style="opacity:0.45">
              <div style="display:flex;justify-content:space-between;align-items:baseline">
                <div style="font-size:14px;color:{T.INK_2}">{nama}
                  <span class="num" style="color:{T.INK_3};font-size:10.5px">bobot {des(bobot, 2)}</span></div>
                <div class="num" style="font-size:12.5px;color:{T.INK_3}">tidak aktif</div>
              </div>
              <div style="position:relative;height:{T.BAR_HEIGHT}px;margin-top:9px;background:{T.TRACK}">
                <div style="position:absolute;left:50%;top:0;bottom:0;width:1px;background:{T.AXIS}"></div>
              </div>
            </div>""")
            continue

        warna = T.score_color(nilai)
        lebar = abs(nilai) / 2  # -100..100 dipetakan ke 50% ke kiri/kanan
        if nilai >= 0:
            isi = (f'<div class="barL bar-fill" style="position:absolute;left:50%;top:0;'
                   f'height:{T.BAR_HEIGHT}px;width:{lebar:.1f}%;background:{warna};'
                   f'box-shadow:0 0 14px {_rgba(warna, 0.45)};clip-path:{potong_kanan};'
                   f'animation-delay:{0.7 + i * 0.09:.2f}s"></div>')
        else:
            isi = (f'<div class="barR bar-fill" style="position:absolute;right:50%;top:0;'
                   f'height:{T.BAR_HEIGHT}px;width:{lebar:.1f}%;background:{warna};'
                   f'box-shadow:0 0 14px {_rgba(warna, 0.45)};clip-path:{potong_kiri};'
                   f'animation-delay:{0.7 + i * 0.09:.2f}s"></div>')

        blok.append(f"""
        <div>
          <div style="display:flex;justify-content:space-between;align-items:baseline">
            <div style="font-size:14px;font-weight:500">{nama}
              <span class="num" style="color:{T.INK_3};font-size:10.5px;font-weight:400">bobot {des(bobot, 2)}</span></div>
            <div class="num" style="font-size:15px;font-weight:500;color:{warna}">{skor(nilai)}</div>
          </div>
          <div style="position:relative;height:{T.BAR_HEIGHT}px;margin-top:9px;background:{T.TRACK}">
            <div style="position:absolute;left:50%;top:0;bottom:0;width:1px;background:{T.AXIS}"></div>
            {isi}
          </div>
          {_catatan_penyesuaian(penyesuaian.get(kunci))}
        </div>""")

    return f"""
<div style="padding-top:32px;padding-bottom:8px">
  <div class="kicker">Skor per kategori</div>
  <div class="sect">Dari mana angkanya datang</div>
  <div style="display:flex;flex-direction:column;gap:20px;margin-top:26px">{"".join(blok)}</div>
</div>
"""


def signals_list(baris) -> str:
    try:
        sinyal = json.loads(baris["signals_json"] or "[]")
    except (json.JSONDecodeError, TypeError):
        sinyal = []

    if not sinyal:
        isi = (f'<div class="num" style="font-size:12.5px;color:{T.INK_3};padding:18px 0">'
               f'Tidak ada sinyal yang menyala hari ini.</div>')
    else:
        baris_html = []
        for i, s in enumerate(sinyal):
            nilai = s.get("score", 0)
            info = s.get("kind") == "info"
            warna = T.INK_3 if info else T.score_color(nilai)
            nilai_teks = "INFO" if info else skor(nilai)
            terakhir = i == len(sinyal) - 1
            garis = "" if terakhir else f"border-bottom:1px solid {T.GRID};"
            baris_html.append(f"""
            <div class="sig-row rise" style="display:flex;gap:20px;padding:14px 16px 14px 14px;
                 margin-left:-14px;{garis}align-items:baseline;animation-delay:{0.5 + i * 0.07:.2f}s">
              <div class="num" style="width:48px;flex-shrink:0;font-size:15px;font-weight:500;
                   color:{warna};text-align:right">{nilai_teks}</div>
              <div>
                <div style="font-size:14.5px;font-weight:500">{_e(s.get("label", ""))}</div>
                <div class="num sig-detail" style="font-size:11px;color:{T.INK_3};
                     margin-top:6px">{_e(s.get("detail", ""))}</div>
              </div>
              <div class="kicker" style="margin-left:auto;font-size:9.5px;flex-shrink:0">
                {_e(NAMA_KATEGORI.get(s.get("category", ""), s.get("category", "")))}</div>
            </div>""")
        isi = "".join(baris_html)

    return f"""
<div style="border-left:1px solid {T.HAIRLINE};padding-left:32px;padding-top:32px;padding-bottom:8px">
  <div class="kicker">Sinyal terdeteksi · {sum(1 for x in sinyal if x.get('kind') != 'info')} aktif</div>
  <div class="sect">Aturan yang menyala hari ini</div>
  <div style="display:flex;flex-direction:column;margin-top:22px">{isi}</div>
</div>
"""


def indicator_strip(baris) -> str:
    def meter(nilai: float | None, tanda: tuple[float, float], warna: str) -> str:
        if nilai is None:
            return ""
        posisi = max(0.0, min(100.0, nilai))
        return f"""
        <div style="position:relative;height:4px;background:{T.TRACK};margin-top:14px">
          <div style="position:absolute;left:{tanda[0]}%;top:-3px;width:1px;height:10px;background:{T.HAIRLINE_STRONG}"></div>
          <div style="position:absolute;left:{tanda[1]}%;top:-3px;width:1px;height:10px;background:{T.HAIRLINE_STRONG}"></div>
          <div class="drop" style="position:absolute;left:{posisi:.1f}%;top:-4px;width:2px;height:12px;
               background:{warna};box-shadow:0 0 8px {_rgba(warna, 0.8)};animation-delay:1.1s"></div>
        </div>"""

    def sel(judul: str, nilai: str, warna: str = T.INK) -> str:
        return f"""
        <div class="ind">
          <div class="kicker" style="font-size:9.5px;letter-spacing:0.16em">{judul}</div>
          <div class="num ind-val" style="font-size:19px;font-weight:500;margin-top:9px;color:{warna}">{nilai}</div>
        </div>"""

    rsi = baris["rsi14"]
    fng = baris["fng_value"]
    warna_rsi = T.MAGENTA if (rsi or 0) > 55 else T.CYAN
    warna_fng = T.MAGENTA if (fng or 50) > 50 else T.CYAN
    macd = baris["macd_hist"]

    return f"""
<div class="panel">
  <div class="wrap" style="padding-top:26px;padding-bottom:30px">
    <div class="kicker" style="margin-bottom:22px">Indikator mentah · {_e(tanggal_panjang(baris["date"]))}</div>
    <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:32px">

      <div class="ind">
        <div class="kicker" style="font-size:9.5px;letter-spacing:0.16em">RSI (14)</div>
        <div class="num ind-val" style="font-size:27px;font-weight:500;margin-top:9px;color:{warna_rsi}">{des(rsi, 1)}</div>
        {meter(rsi, (30, 70), warna_rsi)}
        <div class="num" style="font-size:9.5px;color:{T.INK_3};margin-top:11px">oversold 30 · overbought 70</div>
      </div>

      <div class="ind">
        <div class="kicker" style="font-size:9.5px;letter-spacing:0.16em">Fear &amp; Greed</div>
        <div style="display:flex;align-items:baseline;gap:10px;margin-top:9px">
          <div class="num ind-val" style="font-size:27px;font-weight:500;color:{warna_fng}">{fng if fng is not None else "—"}</div>
          <div style="font-size:13px;font-weight:500;color:{warna_fng}">{_e((baris["fng_class"] or "").upper())}</div>
        </div>
        {meter(fng, (25, 75), warna_fng)}
        <div class="num" style="font-size:9.5px;color:{T.INK_3};margin-top:11px">dibaca contrarian</div>
      </div>

      <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px">
        {sel("MA20", rb(baris["ma20"]))}
        {sel("MA50", rb(baris["ma50"]))}
        {sel("MACD hist", rb(macd), T.score_color(macd))}
        {sel("%B Bollinger", des(baris["bb_percent_b"], 2))}
      </div>

      <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px">
        {sel("Volume", des(baris["volume_ratio"], 2) + "×")}
        {sel("Dominansi BTC", des(baris["btc_dominance_pct"], 2) + "%" if baris["btc_dominance_pct"] is not None else "—")}
        {sel("ADX (14)", des(baris.get("adx14"), 1))}
        {sel("ATR harian", des(baris.get("atr_pct"), 2) + "%" if baris.get("atr_pct") is not None else "—")}
      </div>
    </div>
  </div>
</div>
"""


def history_table(baris_list, jumlah: int = 7) -> str:
    kolom = "116px 116px 96px 78px 130px 90px 110px 100px"
    terbaru = list(reversed(baris_list))[:jumlah]

    kepala = f"""
    <div class="kicker" style="display:grid;grid-template-columns:{kolom};
         padding:0 14px 12px 14px;margin-left:-14px;border-bottom:1px solid {T.HAIRLINE_STRONG};font-size:9.5px">
      <div>Tanggal</div><div style="text-align:right">Tutup</div>
      <div style="text-align:right">&Delta; 1 hari</div><div style="text-align:right">Skor</div>
      <div style="padding-left:24px">Label</div><div style="text-align:right">Tren</div>
      <div style="text-align:right">Momentum</div><div style="text-align:right">Sentimen</div>
    </div>"""

    baris_html = []
    for i, r in enumerate(terbaru):
        pertama = i == 0
        terakhir = i == len(terbaru) - 1
        sorot = (f"background:{T.RAISED};box-shadow:inset 2px 0 0 {T.VOLT};" if pertama else "")
        garis = "" if terakhir else f"border-bottom:1px solid {T.GRID};"

        def angka(nilai, kosong="—"):
            return (f'<div class="num" style="text-align:right;color:{T.score_color(nilai)}">'
                    f'{skor(nilai, kosong)}</div>')

        baris_html.append(f"""
        <div class="tbl-row rise" style="display:grid;grid-template-columns:{kolom};
             padding:13px 14px;margin-left:-14px;{garis}{sorot}font-size:12.5px;
             animation-delay:{0.6 + i * 0.06:.2f}s">
          <div class="num" style="color:{T.INK if pertama else T.INK_2}">{_e(tanggal_pendek(r["date"]))}</div>
          <div class="num" style="text-align:right;color:{T.INK}">{rb(r["close"])}</div>
          <div class="num" style="text-align:right;color:{T.score_color(r["change_1d_pct"])}">{persen(r["change_1d_pct"])}</div>
          {angka(r["score"])}
          <div style="padding-left:24px;color:{T.INK_2};font-size:13px">{_e(r["label"] or "—")}</div>
          {angka(r["cat_trend"])}{angka(r["cat_momentum"])}{angka(r["cat_sentiment"])}
        </div>""")

    return f"""
<div class="wrap" style="padding-top:32px;padding-bottom:12px">
  <div class="kicker">Tujuh hari terakhir</div>
  <div class="sect">Setiap angka di atas, per hari</div>
  <div style="margin-top:22px">{kepala}{"".join(baris_html)}</div>
</div>
"""


def footer(jumlah_baris: int, versi: int | None = None) -> str:
    return f"""
<div class="wrap" style="display:flex;justify-content:space-between;align-items:center;
     padding-top:26px;padding-bottom:36px">
  <div class="num" style="font-size:10.5px;color:{T.INK_3}">
    BINANCE · COINGECKO · ALTERNATIVE.ME · SCORING v{versi or 1} · {jumlah_baris} HARI TERSIMPAN</div>
  <div class="num" style="font-size:10.5px;color:{T.INK_3}">BUKAN SARAN KEUANGAN</div>
</div>
"""


def empty_state(db_path: str) -> str:
    return f"""
<div class="wrap" style="padding-top:80px;padding-bottom:80px;max-width:760px">
  <div class="head" style="font-size:32px;font-weight:700;letter-spacing:0.02em">BELUM ADA DATA</div>
  <div style="font-size:16px;font-weight:300;line-height:1.6;color:{T.INK_2};margin-top:18px">
    Database <span class="num" style="color:{T.INK}">{_e(db_path)}</span> masih kosong.
    Isi dulu dengan salah satu perintah berikut, lalu muat ulang halaman ini.
  </div>
  <div class="num" style="background:{T.PANEL};border:1px solid {T.HAIRLINE_STRONG};
       padding:20px 22px;margin-top:24px;font-size:12.5px;line-height:2;color:{T.INK_2}">
    <span style="color:{T.VOLT}">$</span> python fetch_history.py --from-dir ../Pipeline_project/output/history<br>
    <span style="color:{T.INK_3}">&nbsp;&nbsp;isi histori awal dari arsip repo analisis</span><br><br>
    <span style="color:{T.VOLT}">$</span> python fetch_history.py<br>
    <span style="color:{T.INK_3}">&nbsp;&nbsp;ambil hasil terbaru dari URL repo analisis</span>
  </div>
</div>
"""


def stale_banner(umur: float | None, tanggal: str) -> str:
    teks = "umurnya tidak diketahui" if umur is None else f"dianalisis {des(umur, 1)} jam lalu"
    return f"""
<div class="wrap" style="padding-top:16px">
  <div style="border:1px solid {T.MAGENTA};background:{_rgba(T.MAGENTA, 0.08)};
       padding:14px 18px;display:flex;align-items:center;gap:14px">
    <div style="width:8px;height:8px;background:{T.MAGENTA};flex-shrink:0"></div>
    <div style="font-size:13.5px;color:{T.INK}">
      Data terakhir dari <span class="num">{_e(tanggal)}</span> — {teks}.
      Yang tampil di bawah bukan kondisi hari ini. Cek apakah cron pipeline analisis masih jalan.
    </div>
  </div>
</div>
"""


def _rgba(hex_warna: str, alpha: float) -> str:
    h = hex_warna.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"
