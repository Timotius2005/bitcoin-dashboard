"""Tes penyimpanan histori — terutama aturan mana baris yang boleh menimpa.

Ini bagian yang paling gampang salah diam-diam: kalau aturannya keliru,
database tetap terisi dan dashboard tetap tampil, tapi angkanya berasal dari
baris yang salah.
"""

from __future__ import annotations

import pytest

import storage

# Pembeda "tidak diisi" dari "sengaja dikosongkan".
KOSONG = object()


def dokumen(
    tanggal: str = "2026-09-07",
    generated_at: str = "2026-09-08T00:05:00+00:00",
    skor: int = -4,
    backfilled: bool = False,
    dominance: float | None = 58.93,
    fng: dict | None = KOSONG,  # type: ignore[assignment]
) -> dict:
    return {
        "generated_at": generated_at,
        "data_as_of": tanggal,
        "symbol": "BTCUSDT",
        "price": {"close": 79112.01, "open": 80341.83, "high": 80443.99,
                  "low": 78680.0, "change_1d_pct": -1.53,
                  "change_7d_pct": 0.68, "change_30d_pct": 21.78},
        "indicators": {"rsi14": 62.73, "ma20": 77982.35, "ma50": 69730.69,
                       "macd_hist": -260.43, "bb_percent_b": 0.609,
                       "volume_ratio": 0.56},
        "sentiment": {
            "fear_greed": {"value": 69, "classification": "Greed"} if fng is KOSONG else fng,
            "btc_dominance_pct": dominance,
        },
        "signals": [
            {"id": "ma20_above_ma50", "category": "trend", "score": 40,
             "label": "MA20 di atas MA50", "detail": "..."},
            {"id": "macd_bearish_cross", "category": "momentum", "score": -50,
             "label": "MACD cross bearish", "detail": "..."},
        ],
        "scores": {"composite": skor, "label": "netral",
                   "by_category": {"trend": 70, "momentum": -75, "sentiment": -38}},
        "meta": {"candles_used": 200, "fetched_at": "2026-09-08T00:04:00+00:00",
                 "backfilled": backfilled},
    }


@pytest.fixture()
def conn(tmp_path):
    c = storage.connect(str(tmp_path / "uji.db"))
    yield c
    c.close()


# ── Pemipihan dokumen ────────────────────────────────────────────────────

def test_to_row_memipihkan_field_bersarang():
    row = storage.to_row(dokumen())
    assert row["date"] == "2026-09-07"
    assert row["close"] == 79112.01
    assert row["rsi14"] == 62.73
    assert row["fng_value"] == 69
    assert row["fng_class"] == "Greed"
    assert row["btc_dominance_pct"] == 58.93
    assert row["score"] == -4
    assert row["cat_trend"] == 70
    assert row["cat_momentum"] == -75
    assert row["cat_volatility"] is None  # kategori tidak aktif hari itu
    assert row["signal_count"] == 2


def test_to_row_tahan_sentimen_kosong():
    row = storage.to_row(dokumen(fng=None, dominance=None))
    assert row["fng_value"] is None
    assert row["btc_dominance_pct"] is None
    assert row["score"] == -4  # skor tetap ada


def test_to_row_menyimpan_json_utuh():
    row = storage.to_row(dokumen())
    assert '"ma20_above_ma50"' in row["signals_json"]
    assert '"data_as_of"' in row["raw_json"]


# ── Aturan penimpaan ─────────────────────────────────────────────────────

def test_dokumen_baru_masuk(conn):
    assert storage.upsert(conn, dokumen()) == "baru"
    assert storage.count(conn) == 1


def test_dokumen_sama_dilewati(conn):
    storage.upsert(conn, dokumen())
    assert storage.upsert(conn, dokumen()) == "dilewati"
    assert storage.count(conn) == 1


def test_dokumen_lebih_baru_memperbarui(conn):
    storage.upsert(conn, dokumen(skor=-4))
    hasil = storage.upsert(conn, dokumen(
        generated_at="2026-09-08T01:00:00+00:00", skor=12))
    assert hasil == "diperbarui"
    assert storage.latest(conn)["score"] == 12
    assert storage.count(conn) == 1


def test_dokumen_lebih_lama_tidak_menimpa(conn):
    storage.upsert(conn, dokumen(generated_at="2026-09-08T05:00:00+00:00", skor=12))
    hasil = storage.upsert(conn, dokumen(
        generated_at="2026-09-08T01:00:00+00:00", skor=-99))
    assert hasil == "dilewati"
    assert storage.latest(conn)["score"] == 12


def test_baris_harian_menimpa_backfill_walau_timestampnya_lebih_tua(conn):
    # Backfill dihitung ulang belakangan, jadi generated_at-nya justru lebih
    # baru. Baris harian asli tetap harus menang karena datanya lebih lengkap.
    storage.upsert(conn, dokumen(
        generated_at="2026-09-20T00:00:00+00:00", backfilled=True,
        dominance=None, skor=-6))
    hasil = storage.upsert(conn, dokumen(
        generated_at="2026-09-08T00:05:00+00:00", backfilled=False,
        dominance=58.93, skor=-4))
    assert hasil == "diperbarui"
    baris = storage.latest(conn)
    assert baris["score"] == -4
    assert baris["backfilled"] == 0
    assert baris["btc_dominance_pct"] == 58.93


def test_backfill_tidak_menimpa_baris_harian(conn):
    storage.upsert(conn, dokumen(backfilled=False, dominance=58.93))
    hasil = storage.upsert(conn, dokumen(
        generated_at="2026-09-20T00:00:00+00:00", backfilled=True, dominance=None))
    assert hasil == "dilewati"
    assert storage.latest(conn)["btc_dominance_pct"] == 58.93


def test_tanggal_berbeda_jadi_baris_berbeda(conn):
    storage.upsert(conn, dokumen(tanggal="2026-09-06"))
    storage.upsert(conn, dokumen(tanggal="2026-09-07"))
    assert storage.count(conn) == 2
    assert storage.latest(conn)["date"] == "2026-09-07"


# ── Pembacaan ────────────────────────────────────────────────────────────

def test_history_urut_kronologis(conn):
    for hari in ("2026-09-05", "2026-09-07", "2026-09-06"):
        storage.upsert(conn, dokumen(tanggal=hari))
    tanggal = [r["date"] for r in storage.history(conn)]
    assert tanggal == ["2026-09-05", "2026-09-06", "2026-09-07"]


def test_history_batas_hari_mengambil_yang_terbaru(conn):
    for hari in ("2026-09-04", "2026-09-05", "2026-09-06", "2026-09-07"):
        storage.upsert(conn, dokumen(tanggal=hari))
    tanggal = [r["date"] for r in storage.history(conn, days=2)]
    assert tanggal == ["2026-09-06", "2026-09-07"]


def test_database_kosong_aman_dibaca(conn):
    assert storage.latest(conn) is None
    assert storage.history(conn) == []
    assert storage.count(conn) == 0


def test_upsert_many_menghitung_hasil(conn):
    hasil = storage.upsert_many(conn, [
        dokumen(tanggal="2026-09-06"),
        dokumen(tanggal="2026-09-07"),
        dokumen(tanggal="2026-09-07"),  # duplikat
    ])
    assert hasil == {"baru": 2, "diperbarui": 0, "dilewati": 1}


# ── Akses repo privat ────────────────────────────────────────────────────

def test_konversi_url_raw_ke_contents_api():
    import fetch_history as fh
    hasil = fh.api_url_from_raw(
        "https://raw.githubusercontent.com/budi/btc-pipeline/main/output/latest.json")
    assert hasil == (
        "https://api.github.com/repos/budi/btc-pipeline/contents/"
        "output/latest.json?ref=main")


def test_konversi_url_dengan_path_bersarang():
    import fetch_history as fh
    hasil = fh.api_url_from_raw(
        "https://raw.githubusercontent.com/budi/btc/main/output/history/2026-09-07.json")
    assert hasil.endswith("contents/output/history/2026-09-07.json?ref=main")


def test_url_bukan_github_tidak_dikonversi():
    import fetch_history as fh
    assert fh.api_url_from_raw("https://example.com/latest.json") is None
    assert fh.api_url_from_raw("https://raw.githubusercontent.com/terlalu/pendek") is None
