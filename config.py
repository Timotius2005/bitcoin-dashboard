"""Konfigurasi dashboard.

Dashboard ini konsumen read-only terhadap repo analisis: ia hanya membaca
JSON hasil pipeline dan tidak pernah menulis balik ke sana.
"""

from __future__ import annotations

import os

# Repo analisis yang jadi sumber data. Bisa ditimpa lewat variabel
# lingkungan BTC_PIPELINE_URL tanpa mengubah file ini.
DEFAULT_SOURCE_URL = (
    "https://raw.githubusercontent.com/Timotius2005/bitcoin-daily-pipeline"
    "/main/output/latest.json"
)

SOURCE_URL = os.environ.get("BTC_PIPELINE_URL", DEFAULT_SOURCE_URL)

# Repo analisis privat: raw.githubusercontent.com tidak menerima header
# Authorization, jadi kalau token diisi, permintaan dialihkan ke GitHub
# Contents API yang menerimanya. Token dibaca dari lingkungan saja — jangan
# pernah ditulis di file ini, karena file ini ikut masuk repo.
SOURCE_TOKEN = os.environ.get("BTC_PIPELINE_TOKEN", "")
DB_PATH = os.environ.get("BTC_DASHBOARD_DB", os.path.join("data", "history.db"))

# Data dianggap basi kalau umurnya lebih dari ini. Pipeline berjalan harian,
# jadi 36 jam memberi ruang untuk keterlambatan penjadwal GitHub Actions
# tanpa menyembunyikan kegagalan yang sebenarnya.
STALE_AFTER_HOURS = 36


def source_is_configured() -> bool:
    return "<user>" not in SOURCE_URL and "<repo>" not in SOURCE_URL
