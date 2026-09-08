"""Fase D2 — dashboard Streamlit.

Jalankan: streamlit run app.py

Halaman ini hanya membaca database histori lokal. Pengambilan data adalah
tugas fetch_history.py yang dijalankan cron — memisahkan keduanya berarti
dashboard tetap bisa dibuka (dan menunjukkan data terakhir yang ada) walau
sumbernya sedang tidak bisa dihubungi.
"""

from __future__ import annotations

import streamlit as st

import charts
import components as C
import config
import storage

st.set_page_config(
    page_title="Bitcoin Harian",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_data(ttl=60)
def muat(path: str) -> list[dict]:
    """Baca seluruh histori jadi list dict biasa supaya bisa di-cache.

    TTL 60 detik: cron menulis ke database yang sama, jadi halaman ikut
    menyusul perubahannya tanpa perlu di-restart.
    """
    conn = storage.connect(path)
    try:
        return [dict(r) for r in storage.history(conn)]
    finally:
        conn.close()


def pilih_rentang() -> int:
    """Kontrol rentang. Satu-satunya filter, diletakkan di atas semua grafik
    yang dipengaruhinya — bukan di dalam kartu masing-masing grafik."""
    opsi = ["30 HARI", "90 HARI"]
    if hasattr(st, "segmented_control"):
        pilihan = st.segmented_control(
            "Rentang", options=opsi, default="90 HARI",
            label_visibility="collapsed", key="rentang",
        )
    else:  # Streamlit < 1.40
        pilihan = st.radio(
            "Rentang", opsi, index=1, horizontal=True,
            label_visibility="collapsed", key="rentang",
        )
    return 30 if pilihan == "30 HARI" else 90


def main() -> None:
    # Animasi masuk hanya diputar sekali per sesi. Streamlit menjalankan ulang
    # seluruh skrip setiap kali tombol rentang ditekan; tanpa penjaga ini
    # halaman mengulang koreografinya tiap filter dan gerakannya berubah jadi
    # gangguan, bukan penanda perubahan.
    intro = not st.session_state.get("sudah_tampil", False)
    st.session_state["sudah_tampil"] = True
    st.html(C.css(intro=intro))

    riwayat = muat(config.DB_PATH)
    if not riwayat:
        st.html(C.empty_state(config.DB_PATH))
        return

    terbaru = riwayat[-1]
    sebelum = riwayat[-2] if len(riwayat) > 1 else None
    umur = C.umur_jam(terbaru.get("generated_at"))
    basi = umur is not None and umur > config.STALE_AFTER_HOURS

    st.html(C.masthead(terbaru, umur, basi))
    if basi:
        st.html(C.stale_banner(umur, terbaru["date"]))

    # ── Hero: skor besar | blok harga ───────────────────────────────────
    kiri, kanan = st.columns([7, 5], gap="large")
    with kiri:
        st.html(C.hero(terbaru, sebelum))
    with kanan:
        st.html(C.price_header(terbaru))

    # ── Judul bagian grafik + kontrol rentang ───────────────────────────
    kol_judul, kol_kontrol = st.columns([8, 4], gap="large")
    with kol_judul:
        st.html(
            '<div style="padding-top:38px">'
            '<div class="kicker">Riwayat skor komposit</div>'
            '<div class="sect">Perjalanan skor dan harga</div></div>'
        )
    with kol_kontrol:
        st.html('<div style="padding-top:52px"></div>')
        hari = pilih_rentang()

    potongan = riwayat[-hari:] if len(riwayat) > hari else riwayat
    tanggal = [r["date"] for r in potongan]

    st.plotly_chart(
        charts.score_history(tanggal, [r["score"] for r in potongan],
                             [r["label"] or "" for r in potongan]),
        config=charts.PLOTLY_CONFIG, key="chart_skor", width="stretch",
    )

    st.html(
        f'<div class="wrap" style="padding-top:22px"><div class="kicker">'
        f'Harga penutupan · {len(potongan)} hari terakhir</div></div>'
    )
    st.plotly_chart(
        charts.price_history(tanggal, [r["close"] for r in potongan]),
        config=charts.PLOTLY_CONFIG, key="chart_harga", width="stretch",
    )

    # ── Kategori | sinyal ────────────────────────────────────────────────
    kiri, kanan = st.columns([5, 7], gap="large")
    with kiri:
        st.html(C.category_bars(terbaru))
    with kanan:
        st.html(C.signals_list(terbaru))

    st.html(C.indicator_strip(terbaru))
    st.html(C.history_table(riwayat))
    st.html(C.footer(len(riwayat)))


if __name__ == "__main__":
    main()
