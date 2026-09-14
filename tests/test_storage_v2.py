"""Tes kolom scoring v2 dan migrasi database yang dibuat versi lama."""

from __future__ import annotations

import json
import sqlite3

import storage


def dokumen_v2() -> dict:
    return {
        "generated_at": "2026-09-14T00:40:00+00:00",
        "data_as_of": "2026-09-13",
        "price": {"close": 76842.01},
        "indicators": {
            "rsi14": 55.0, "adx14": 16.8, "plus_di": 21.0, "minus_di": 18.5,
            "atr_pct": 2.345, "atr_pct_percentile": 7.5, "obv_above_sma20": False,
        },
        "sentiment": {"fear_greed": {"value": 57, "classification": "Greed"}},
        "signals": [
            {"id": "adx_tren_lemah", "category": "trend", "kind": "info", "score": 0,
             "label": "Tren lemah, sinyal tren diredam", "detail": "..."},
            {"id": "ma20_above_ma50", "category": "trend", "kind": "score", "score": 40,
             "label": "MA20 di atas MA50", "detail": "..."},
        ],
        "scores": {
            "composite": 11, "label": "netral", "by_category": {"trend": 35},
            "adjustments": [{"category": "trend", "factor": 0.5, "before": 70,
                             "after": 35, "reason": "ADX(14) 16.8 di bawah 20"}],
        },
        "meta": {"scoring_version": 2, "backfilled": False},
    }


def test_to_row_memetakan_kolom_v2():
    row = storage.to_row(dokumen_v2())
    assert row["adx14"] == 16.8
    assert row["atr_pct"] == 2.345
    assert row["atr_pct_percentile"] == 7.5
    assert row["obv_above_sma20"] == 0
    assert row["scoring_version"] == 2
    assert json.loads(row["adjustments_json"])[0]["after"] == 35


def test_dokumen_v1_tetap_bisa_disimpan():
    doc = dokumen_v2()
    doc["indicators"] = {"rsi14": 55.0}
    doc["scores"].pop("adjustments")
    doc["meta"] = {}
    row = storage.to_row(doc)
    assert row["adx14"] is None
    assert row["obv_above_sma20"] is None
    assert row["scoring_version"] == 1
    assert json.loads(row["adjustments_json"]) == []


def test_database_lama_dimigrasikan_tanpa_kehilangan_data(tmp_path):
    path = str(tmp_path / "lama.db")
    lama = sqlite3.connect(path)
    lama.execute(
        "CREATE TABLE snapshots (date TEXT PRIMARY KEY, generated_at TEXT, "
        "ingested_at TEXT NOT NULL, score INTEGER, backfilled INTEGER NOT NULL DEFAULT 0)"
    )
    lama.execute(
        "INSERT INTO snapshots (date, generated_at, ingested_at, score) "
        "VALUES ('2026-09-01', '2026-09-02T00:00:00+00:00', 'x', 5)"
    )
    lama.commit()
    lama.close()

    conn = storage.connect(path)
    kolom = {r[1] for r in conn.execute("PRAGMA table_info(snapshots)")}
    assert set(storage.COLUMNS) <= kolom
    assert conn.execute(
        "SELECT score FROM snapshots WHERE date = '2026-09-01'").fetchone()["score"] == 5

    assert storage.upsert(conn, dokumen_v2()) == "baru"
    assert storage.latest(conn)["adx14"] == 16.8
    conn.close()
