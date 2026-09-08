# Bitcoin Dashboard

Lapisan visualisasi untuk [pipeline analisis Bitcoin](../Pipeline_project). Mengambil
`output/latest.json` dari repo analisis, menyimpannya sebagai histori lokal, dan
menampilkannya sebagai dashboard.

```
[Cron lokal]  fetch_history.py  →  data/history.db (SQLite)
                                          ↓
              app.py (Streamlit)  →  http://localhost:8501
```

Dashboard ini **konsumen read-only**: tidak pernah menulis balik ke repo analisis.
Pengambilan data dan penampilan sengaja dipisah, jadi halaman tetap bisa dibuka dan
menunjukkan data terakhir yang ada walau sumbernya sedang tidak bisa dihubungi.

## Status per fase

| Fase | Isi | Status |
|---|---|---|
| D0 | Setup repo, venv, cron lokal | Kode siap; penjadwalan perlu didaftarkan (lihat bawah) |
| D1 | `fetch_history.py` + SQLite, dengan aturan dedup | Selesai, 14 tes lolos |
| D2 | `app.py` — dashboard sesuai desain "Voltage" | Selesai |
| D3 | Akses tanpa start manual | Belum — pilihan ada di bawah |

## Menjalankan

```bash
python -m venv .venv
.venv/Scripts/activate            # Windows; Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

# Isi histori awal dari arsip repo analisis (90 hari)
python fetch_history.py --from-dir ../Pipeline_project/output/history

streamlit run app.py              # buka http://localhost:8501
pytest -q                         # 14 tes
```

Kalau database masih kosong, dashboard menampilkan halaman petunjuk berisi perintah
di atas, bukan halaman rusak atau grafik kosong.

## Mengarahkan ke repo analisis

Setelah repo analisis di-push ke GitHub:

```bash
export BTC_PIPELINE_URL="https://raw.githubusercontent.com/Timotius2005/bitcoin-daily-pipeline/main/output/latest.json"
python fetch_history.py
```

Atau ubah `DEFAULT_SOURCE_URL` di [config.py](config.py). Selama URL-nya masih berisi
placeholder `<user>/<repo>`, `fetch_history.py` menolak jalan dengan pesan yang jelas
alih-alih gagal dengan 404 yang membingungkan.

**Kalau suatu saat repo analisisnya dijadikan privat**, tambahkan token:

```bash
export BTC_PIPELINE_TOKEN="ghp_xxx"    # PAT dengan akses baca repo analisis
```

`raw.githubusercontent.com` mengabaikan header `Authorization`, jadi begitu token
diisi, permintaan otomatis dialihkan ke GitHub Contents API yang menerimanya. Token
hanya dibaca dari variabel lingkungan — jangan pernah ditulis di `config.py`, karena
file itu ikut masuk repo.

## Menjadwalkan pengambilan data

Jadwalkan **setelah** cron GitHub Actions di repo analisis (07:00 WIB). Jeda satu jam
memberi ruang untuk keterlambatan penjadwal Actions yang normalnya 5–30 menit.

**Linux/macOS (crontab):**

```cron
0 8 * * * cd /path/ke/bitcoin-dashboard && .venv/bin/python fetch_history.py >> data/cron.log 2>&1
```

**Windows (Task Scheduler):**

```powershell
$aksi = New-ScheduledTaskAction -Execute "C:\path\ke\bitcoin-dashboard\.venv\Scripts\python.exe" `
        -Argument "fetch_history.py" -WorkingDirectory "C:\path\ke\bitcoin-dashboard"
$pemicu = New-ScheduledTaskTrigger -Daily -At 8:00AM
Register-ScheduledTask -TaskName "BTC Dashboard Fetch" -Action $aksi -Trigger $pemicu
```

`fetch_history.py` keluar dengan kode 1 kalau gagal, jadi kegagalannya terlihat di log
cron dan tidak lewat diam-diam.

## Struktur

```
config.py            URL sumber, path DB, ambang basi
storage.py           Skema SQLite + aturan baris mana yang boleh menimpa
fetch_history.py     Fase D1 — ambil dari URL / file / folder arsip
theme.py             Token desain "Voltage" (warna, font, spesifikasi mark)
charts.py            Grafik Plotly sesuai spesifikasi mark
components.py        Blok HTML kustom + stylesheet global
app.py               Fase D2 — halaman Streamlit
tests/               Tes penyimpanan dan aturan dedup
data/history.db      Histori lokal (gitignored)
```

## Keputusan yang perlu diketahui

**Satu baris per tanggal data, bukan per waktu pengambilan.** Kalau cron jalan lebih
sering daripada pipeline memperbarui datanya, baris yang sama diperbarui, bukan
digandakan.

**Baris harian selalu menang atas baris backfill.** Baris backfill dihitung ulang
belakangan, jadi `generated_at`-nya justru lebih baru untuk tanggal yang sama. Tanpa
pengecualian eksplisit, backfill akan mengunci baris asli yang datanya lebih lengkap
(baris backfill tidak punya dominansi BTC — CoinGecko tidak menyediakan historinya
gratis). Ini diuji di `tests/test_storage.py`.

**Arsip harian di repo analisis adalah pengaman.** `latest.json` hanya menyimpan
snapshot terakhir; kalau mesin ini mati tiga hari, tiga hari itu hilang permanen tanpa
`output/history/`. Itu sebabnya arsip dijadikan bagian inti pipeline, bukan opsional.

**Data basi ditandai, bukan disembunyikan.** Kalau `generated_at` lebih tua dari 36 jam,
masthead berubah merah dan muncul spanduk peringatan di atas halaman — supaya angka
kemarin tidak terbaca sebagai kondisi hari ini.

**Tampilan tidak menyimpulkan apa pun.** Kalimat pembuka disusun ulang dari skor dan
kategori yang sudah ada di JSON. Semua kesimpulan analisis dihitung di repo analisis.

## Catatan implementasi tampilan

Streamlit tidak bisa menghasilkan tampilan ini dengan komponen bawaannya, jadi:

- Sebagian besar halaman adalah HTML kustom lewat **`st.html`**, bukan
  `st.markdown(unsafe_allow_html=True)`. `st.markdown` memproses string sebagai Markdown
  lebih dulu, sehingga baris ber-indentasi berubah jadi blok kode dan stylesheet-nya
  bocor jadi teks di halaman.
- Grafik pakai Plotly yang di-theme manual, bukan `st.line_chart`.
- **Wadah `stPlotlyChart` tidak boleh diberi padding CSS.** Plotly menghitung lebar SVG
  dari wadahnya; padding membuat SVG melampaui kotak tampil dan sisi kanannya terpotong
  diam-diam. Jarak tepi diatur lewat `margin` di figure.
- Warna divergen tidak bisa dibuat dengan satu trace: garis dipecah tepat di sumbu nol
  dengan menyisipkan titik potong interpolasi, lalu digambar sebagai dua trace.

## Lapisan animasi

Satu koreografi masuk sekitar 2,5 detik, lalu tiga gerak yang terus berjalan:
glitch angka hero, aliran gradien masthead, dan denyut penanda kesegaran data.

| Elemen | Gerak |
|---|---|
| Garis masthead | melebar dari kiri |
| Angka hero | ghost aberasi cyan/ungu datang terpisah lalu mengunci jadi satu |
| Alur skor | dua sisi tumbuh keluar dari sumbu nol, penanda jatuh belakangan |
| Grafik | tersingkap kiri→kanan dengan garis pemindai volt di tepi singkapan |
| Bar kategori | tumbuh dari sumbu nol, lalu satu kilatan lewat sekali |
| Baris sinyal & tabel | naik bertahap, berselang 60–70 ms |

Yang berulang tanpa henti:

| Elemen | Gerak | Periode |
|---|---|---|
| Angka hero | ghost RGB pecah dan tersayat, lalu mengunci lagi | letupan ~0,4 dtk tiap 5,5 dtk |
| Garis masthead | gradien cyan→ungu→magenta→volt mengalir ke kanan | 7 dtk per siklus |
| Titik kesegaran data | denyut volt | 2,4 dtk |

**Glitch hero sengaja meletup singkat, bukan bergetar terus.** Angka itu informasi
terpenting di halaman; getaran terus-menerus membuatnya tidak terbaca. Delapan puluh
empat persen dari siklusnya diam total — hanya lapisan ghost yang pecah saat letupan,
lapisan putihnya nyaris tidak bergeser.

Gradien masthead ditulis dua siklus penuh dan ditutup warna awalnya, dengan
`background-size: 200%`. Bergeser satu lebar wadah berarti tepat satu siklus, jadi
pengulangannya mulus tanpa kedutan di titik sambung.

Loop tak berujung **tetap berjalan setelah rerun** — yang dilepas saat filter ditekan
cuma bagian animasi masuknya.

**Animasi masuk hanya diputar sekali per sesi.** Streamlit menjalankan ulang seluruh
skrip setiap kali tombol rentang ditekan; tanpa penjaga `st.session_state`, halaman
akan mengulang koreografinya tiap kali difilter dan gerak berubah jadi gangguan.
Yang tetap dijalankan saat rerun cuma sapuan grafik, dipercepat jadi 0,85 detik —
karena datanya memang baru berubah, jadi gerakannya menyampaikan informasi.

Plotly tidak punya animasi masuk, jadi efek "garis menggambar dirinya sendiri" dibuat
dengan menyingkap wadah grafik lewat `clip-path`. Singkapannya berhenti di
`inset(0 -50px 0 0)`, bukan `0` — dengan `0`, label pita di gutter kanan ikut
terpotong permanen setelah animasi selesai.

Semua gerak, termasuk loop tak berujung, mati otomatis untuk yang menyalakan
`prefers-reduced-motion` di sistemnya.

**Batas yang diketahui:** di bawah ~1000 px masthead membungkus dan tanggal edisi
bertabrakan dengan penanda kesegaran. Dashboard ini dirancang untuk lebar desktop;
di 1280 px ke atas tata letaknya rapi.

## Fase D3 — akses tanpa start manual

Belum dikerjakan. Dua pilihan, tergantung dari mana mau diakses:

- **Tetap lokal sebagai service** — `systemd` (Linux) atau Task Scheduler "at startup"
  (Windows) menjalankan `streamlit run app.py` di latar. Diakses dari perangkat manapun
  di jaringan rumah lewat `http://<ip-mesin>:8501`.
- **Streamlit Community Cloud dengan repo privat** — bisa diakses dari luar rumah tanpa
  mesin menyala. Perlu diperiksa dulu batasan app privat di paket gratis saat ini, dan
  `data/history.db` yang di-gitignore berarti perlu strategi lain untuk datanya di sana.

## Catatan

Analisis rule-based otomatis untuk keperluan belajar dan portfolio. Bukan saran keuangan.
