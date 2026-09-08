"""Fase D1 — ambil hasil analisis dan simpan ke histori lokal.

Tiga cara pakai:

  python fetch_history.py                      # ambil latest.json dari URL repo analisis
  python fetch_history.py --from-file X.json   # dari file lokal (untuk uji coba)
  python fetch_history.py --from-dir output/history   # ingest arsip sekaligus

Ini yang dijalankan crontab lokal. Keluar dengan kode 1 kalau gagal, supaya
kegagalannya terlihat di log cron dan bukan diam-diam.
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import os
import sys
from typing import Any

import requests

import config
import storage

log = logging.getLogger("fetch_history")

TIMEOUT = 30


RAW_PREFIX = "https://raw.githubusercontent.com/"


def api_url_from_raw(url: str) -> str | None:
    """Ubah URL raw.githubusercontent jadi URL GitHub Contents API.

    raw.githubusercontent.com mengabaikan header Authorization, jadi repo
    privat harus diambil lewat Contents API yang menerimanya:

      https://raw.githubusercontent.com/OWNER/REPO/REF/a/b.json
      -> https://api.github.com/repos/OWNER/REPO/contents/a/b.json?ref=REF

    Return None kalau URL-nya bukan URL raw GitHub.
    """
    if not url.startswith(RAW_PREFIX):
        return None
    bagian = url[len(RAW_PREFIX):].split("/")
    if len(bagian) < 4:
        return None
    owner, repo, ref = bagian[0], bagian[1], bagian[2]
    path = "/".join(bagian[3:])
    return f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}"


def load_from_url(url: str, token: str = "") -> dict[str, Any]:
    headers = {"User-Agent": "bitcoin-dashboard/1.0"}
    if token:
        api = api_url_from_raw(url)
        if api is not None:
            url = api
            # Accept raw: minta isi berkasnya langsung, bukan pembungkus JSON
            # berisi base64 yang jadi bawaan Contents API.
            headers["Accept"] = "application/vnd.github.raw"
        headers["Authorization"] = f"Bearer {token}"
        log.info("GET %s (dengan token)", url)
    else:
        log.info("GET %s", url)

    resp = requests.get(url, timeout=TIMEOUT, headers=headers)
    if resp.status_code == 404 and not token:
        raise RuntimeError(
            "404 — kalau repo analisisnya privat, set BTC_PIPELINE_TOKEN "
            "dengan personal access token yang punya akses baca repo itu."
        )
    resp.raise_for_status()
    return resp.json()


def load_from_file(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def validate(payload: dict[str, Any], sumber: str) -> None:
    """Tolak dokumen yang tidak berbentuk hasil pipeline.

    Lebih baik gagal keras di sini daripada menyimpan baris setengah kosong
    yang baru ketahuan salah waktu dashboard menampilkannya.
    """
    if not isinstance(payload, dict):
        raise ValueError(f"{sumber}: bukan objek JSON")
    for field in ("data_as_of", "scores", "price"):
        if field not in payload:
            raise ValueError(f"{sumber}: field '{field}' tidak ada")
    if payload["scores"].get("composite") is None:
        raise ValueError(f"{sumber}: skor komposit kosong")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ambil hasil analisis ke histori lokal.")
    parser.add_argument("--url", default=None, help="URL latest.json (default dari config)")
    parser.add_argument("--from-file", default=None, help="baca satu file JSON lokal")
    parser.add_argument("--from-dir", default=None, help="ingest semua *.json dalam folder")
    parser.add_argument("--db", default=config.DB_PATH)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    dokumen: list[tuple[str, dict[str, Any]]] = []
    try:
        if args.from_dir:
            berkas = sorted(glob.glob(os.path.join(args.from_dir, "*.json")))
            if not berkas:
                log.error("Tidak ada file JSON di %s", args.from_dir)
                return 1
            log.info("Ingest %d file dari %s", len(berkas), args.from_dir)
            for path in berkas:
                dokumen.append((os.path.basename(path), load_from_file(path)))
        elif args.from_file:
            dokumen.append((args.from_file, load_from_file(args.from_file)))
        else:
            url = args.url or config.SOURCE_URL
            if not config.source_is_configured() and args.url is None:
                log.error(
                    "URL sumber belum diatur. Set BTC_PIPELINE_URL atau ubah "
                    "DEFAULT_SOURCE_URL di config.py."
                )
                return 1
            dokumen.append((url, load_from_url(url, config.SOURCE_TOKEN)))
    except Exception as exc:  # noqa: BLE001
        log.error("Gagal membaca sumber: %s", exc)
        return 1

    sah: list[dict[str, Any]] = []
    for sumber, payload in dokumen:
        try:
            validate(payload, sumber)
        except ValueError as exc:
            log.error("Dokumen ditolak — %s", exc)
            if len(dokumen) == 1:
                return 1
            continue
        sah.append(payload)

    if not sah:
        log.error("Tidak ada dokumen yang lolos validasi")
        return 1

    conn = storage.connect(args.db)
    hitung = storage.upsert_many(conn, sah)
    total = storage.count(conn)

    log.info(
        "%d baru | %d diperbarui | %d dilewati | total %d baris di %s",
        hitung["baru"], hitung["diperbarui"], hitung["dilewati"], total, args.db,
    )
    terbaru = storage.latest(conn)
    if terbaru is not None:
        log.info(
            "Terbaru: %s | tutup %s | skor %+d (%s)",
            terbaru["date"], terbaru["close"], terbaru["score"], terbaru["label"],
        )
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
