"""Penyimpanan histori lokal (SQLite).

Satu baris per tanggal data (`data_as_of`), bukan per waktu pengambilan —
kalau cron berjalan lebih sering daripada pipeline analisis memperbarui
datanya, baris yang sama diperbarui, bukan digandakan.

Kolom-kolom penting dipipihkan jadi kolom SQL supaya bisa di-query dan
di-plot langsung; JSON aslinya tetap disimpan utuh di `raw_json` agar tidak
ada informasi yang hilang kalau nanti butuh field yang belum dipetakan.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Iterable

DEFAULT_DB = os.path.join("data", "history.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
    date                TEXT PRIMARY KEY,
    generated_at        TEXT,
    fetched_at          TEXT,
    ingested_at         TEXT NOT NULL,

    close               REAL,
    open                REAL,
    high                REAL,
    low                 REAL,
    change_1d_pct       REAL,
    change_7d_pct       REAL,
    change_30d_pct      REAL,

    rsi14               REAL,
    ma20                REAL,
    ma50                REAL,
    macd_line           REAL,
    macd_signal         REAL,
    macd_hist           REAL,
    bb_upper            REAL,
    bb_middle           REAL,
    bb_lower            REAL,
    bb_percent_b        REAL,
    volume              REAL,
    volume_ma20         REAL,
    volume_ratio        REAL,

    fng_value           INTEGER,
    fng_class           TEXT,
    btc_dominance_pct   REAL,

    score               INTEGER,
    label               TEXT,
    cat_trend           INTEGER,
    cat_momentum        INTEGER,
    cat_sentiment       INTEGER,
    cat_volatility      INTEGER,

    signal_count        INTEGER,
    backfilled          INTEGER NOT NULL DEFAULT 0,
    signals_json        TEXT,
    raw_json            TEXT
);
CREATE INDEX IF NOT EXISTS idx_snapshots_date ON snapshots(date DESC);
"""

COLUMNS = [
    "date", "generated_at", "fetched_at", "ingested_at",
    "close", "open", "high", "low",
    "change_1d_pct", "change_7d_pct", "change_30d_pct",
    "rsi14", "ma20", "ma50", "macd_line", "macd_signal", "macd_hist",
    "bb_upper", "bb_middle", "bb_lower", "bb_percent_b",
    "volume", "volume_ma20", "volume_ratio",
    "fng_value", "fng_class", "btc_dominance_pct",
    "score", "label",
    "cat_trend", "cat_momentum", "cat_sentiment", "cat_volatility",
    "signal_count", "backfilled", "signals_json", "raw_json",
]


def connect(path: str = DEFAULT_DB) -> sqlite3.Connection:
    """Buka (dan kalau perlu buat) database beserta skemanya."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def to_row(payload: dict[str, Any]) -> dict[str, Any]:
    """Ratakan satu dokumen latest.json jadi satu baris database."""
    price = payload.get("price") or {}
    ind = payload.get("indicators") or {}
    sent = payload.get("sentiment") or {}
    fng = sent.get("fear_greed") or {}
    scores = payload.get("scores") or {}
    cats = scores.get("by_category") or {}
    meta = payload.get("meta") or {}
    signals = payload.get("signals") or []

    return {
        "date": payload["data_as_of"],
        "generated_at": payload.get("generated_at"),
        "fetched_at": meta.get("fetched_at"),
        "ingested_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),

        "close": price.get("close"),
        "open": price.get("open"),
        "high": price.get("high"),
        "low": price.get("low"),
        "change_1d_pct": price.get("change_1d_pct"),
        "change_7d_pct": price.get("change_7d_pct"),
        "change_30d_pct": price.get("change_30d_pct"),

        "rsi14": ind.get("rsi14"),
        "ma20": ind.get("ma20"),
        "ma50": ind.get("ma50"),
        "macd_line": ind.get("macd_line"),
        "macd_signal": ind.get("macd_signal"),
        "macd_hist": ind.get("macd_hist"),
        "bb_upper": ind.get("bb_upper"),
        "bb_middle": ind.get("bb_middle"),
        "bb_lower": ind.get("bb_lower"),
        "bb_percent_b": ind.get("bb_percent_b"),
        "volume": ind.get("volume"),
        "volume_ma20": ind.get("volume_ma20"),
        "volume_ratio": ind.get("volume_ratio"),

        "fng_value": fng.get("value"),
        "fng_class": fng.get("classification"),
        "btc_dominance_pct": sent.get("btc_dominance_pct"),

        "score": scores.get("composite"),
        "label": scores.get("label"),
        "cat_trend": cats.get("trend"),
        "cat_momentum": cats.get("momentum"),
        "cat_sentiment": cats.get("sentiment"),
        "cat_volatility": cats.get("volatility"),

        "signal_count": len(signals),
        "backfilled": 1 if meta.get("backfilled") else 0,
        "signals_json": json.dumps(signals, ensure_ascii=False),
        "raw_json": json.dumps(payload, ensure_ascii=False),
    }


def upsert(conn: sqlite3.Connection, payload: dict[str, Any]) -> str:
    """Simpan satu dokumen. Return 'baru', 'diperbarui', atau 'dilewati'.

    Baris harian menang atas baris backfill untuk tanggal yang sama: baris
    backfill tidak punya dominansi BTC dan dihitung ulang belakangan, jadi
    hasil pipeline aslinya lebih otoritatif.
    """
    row = to_row(payload)
    lama = conn.execute(
        "SELECT generated_at, backfilled FROM snapshots WHERE date = ?", (row["date"],)
    ).fetchone()

    if lama is not None:
        naik_kualitas = row["backfilled"] == 0 and lama["backfilled"] == 1
        turun_kualitas = row["backfilled"] == 1 and lama["backfilled"] == 0
        sama_atau_lebih_tua = (
            lama["generated_at"] is not None
            and row["generated_at"] is not None
            and row["generated_at"] <= lama["generated_at"]
        )
        # Perbandingan timestamp hanya berlaku antar baris sejenis. Baris
        # backfill dihitung ulang belakangan, jadi generated_at-nya justru
        # lebih baru daripada baris harian asli untuk tanggal yang sama —
        # tanpa pengecualian ini, backfill akan mengunci baris aslinya.
        if not naik_kualitas and (turun_kualitas or sama_atau_lebih_tua):
            return "dilewati"

    kolom = ", ".join(COLUMNS)
    tanda = ", ".join("?" for _ in COLUMNS)
    update = ", ".join(f"{c} = excluded.{c}" for c in COLUMNS if c != "date")
    conn.execute(
        f"INSERT INTO snapshots ({kolom}) VALUES ({tanda}) "
        f"ON CONFLICT(date) DO UPDATE SET {update}",
        [row[c] for c in COLUMNS],
    )
    conn.commit()
    return "diperbarui" if lama is not None else "baru"


def upsert_many(conn: sqlite3.Connection, payloads: Iterable[dict[str, Any]]) -> dict[str, int]:
    hitung = {"baru": 0, "diperbarui": 0, "dilewati": 0}
    for payload in payloads:
        hitung[upsert(conn, payload)] += 1
    return hitung


def latest(conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM snapshots ORDER BY date DESC LIMIT 1"
    ).fetchone()


def history(conn: sqlite3.Connection, days: int | None = None) -> list[sqlite3.Row]:
    """Baris terbaru lebih dulu dibalik jadi urut kronologis untuk plotting."""
    sql = "SELECT * FROM snapshots ORDER BY date DESC"
    params: tuple = ()
    if days is not None:
        sql += " LIMIT ?"
        params = (days,)
    rows = conn.execute(sql, params).fetchall()
    return list(reversed(rows))


def count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) AS n FROM snapshots").fetchone()["n"]
