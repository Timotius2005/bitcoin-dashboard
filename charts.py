"""Grafik Plotly sesuai spesifikasi mark di artboard Sistem desain.

Yang membedakan dari chart Plotly biasa:

* Garis skor berganti warna TEPAT di sumbu nol — cyan di atas, magenta di
  bawah. Ini butuh penyisipan titik potong nol ke dalam deret sebelum
  digambar; tanpa itu warnanya akan berganti di titik data terdekat, yang
  meleset beberapa piksel dan salah secara data.
* Glow neon dibuat dari satu garis lebar transparan di bawah garis utama,
  bukan dari efek bawaan Plotly (tidak ada).
* Gridline sengaja lebih redup daripada garis pemisah biasa dan tidak
  pernah ikut menyala — kalau semuanya bercahaya, tidak ada yang menonjol.
"""

from __future__ import annotations

from datetime import datetime, timezone

import plotly.graph_objects as go

import theme as T


def _ts(tanggal: str) -> float:
    return datetime.strptime(tanggal, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()


def _dt(stamp: float) -> datetime:
    return datetime.fromtimestamp(stamp, timezone.utc)


def _sisipkan_titik_nol(xs: list[float], ys: list[float]) -> tuple[list[float], list[float]]:
    """Sisipkan titik y=0 di setiap perpotongan sumbu nol.

    Dengan titik potong yang eksplisit, memotong deret berdasarkan tanda
    menghasilkan dua garis yang bertemu persis di sumbu nol.
    """
    out_x: list[float] = []
    out_y: list[float] = []
    for i, (x, y) in enumerate(zip(xs, ys)):
        if i > 0:
            x0, y0 = xs[i - 1], ys[i - 1]
            if (y0 < 0 < y) or (y0 > 0 > y):
                bagian = -y0 / (y - y0)
                out_x.append(x0 + (x - x0) * bagian)
                out_y.append(0.0)
        out_x.append(x)
        out_y.append(y)
    return out_x, out_y


def _dasar_layout(fig: go.Figure, tinggi: int, margin: dict) -> None:
    fig.update_layout(
        height=tinggi,
        margin=margin,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        font=dict(family=T.FONT_MONO, size=11, color=T.INK_3),
        hoverlabel=dict(
            bgcolor=T.RAISED,
            bordercolor=T.HAIRLINE_STRONG,
            font=dict(family=T.FONT_MONO, size=12, color=T.INK),
        ),
        dragmode=False,
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=T.HAIRLINE,
        tickcolor=T.HAIRLINE,
        tickfont=dict(size=10, color=T.INK_3),
    )
    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        tickfont=dict(size=10, color=T.INK_3),
    )


def score_history(
    tanggal: list[str],
    skor: list[float],
    label: list[str] | None = None,
    tampilkan_pita: bool = True,
) -> go.Figure:
    """Garis riwayat skor komposit dengan area divergen dan pita klasifikasi."""
    xs = [_ts(d) for d in tanggal]
    ys = [float(v) for v in skor]
    gx, gy = _sisipkan_titik_nol(xs, ys)
    gdt = [_dt(x) for x in gx]

    atas = [v if v >= 0 else 0.0 for v in gy]
    bawah = [v if v <= 0 else 0.0 for v in gy]
    garis_cyan = [v if v >= 0 else None for v in gy]
    garis_magenta = [v if v <= 0 else None for v in gy]

    fig = go.Figure()

    # Area: neon dijaga tipis (12%) — terlalu terang untuk blok pekat.
    fig.add_trace(go.Scatter(
        x=gdt, y=atas, mode="lines", fill="tozeroy",
        line=dict(width=0), fillcolor=_rgba(T.CYAN, T.AREA_OPACITY),
        hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=gdt, y=bawah, mode="lines", fill="tozeroy",
        line=dict(width=0), fillcolor=_rgba(T.MAGENTA, T.AREA_OPACITY),
        hoverinfo="skip",
    ))

    # Glow: garis lebar transparan di bawah garis utama.
    fig.add_trace(go.Scatter(
        x=gdt, y=garis_cyan, mode="lines", connectgaps=False,
        line=dict(color=_rgba(T.CYAN, T.GLOW_OPACITY), width=T.GLOW_WIDTH, shape="linear"),
        hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=gdt, y=garis_magenta, mode="lines", connectgaps=False,
        line=dict(color=_rgba(T.MAGENTA, T.GLOW_OPACITY), width=T.GLOW_WIDTH),
        hoverinfo="skip",
    ))

    # Garis utama, dipecah tepat di sumbu nol.
    fig.add_trace(go.Scatter(
        x=gdt, y=garis_cyan, mode="lines", connectgaps=False,
        line=dict(color=T.CYAN, width=T.LINE_WIDTH), hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=gdt, y=garis_magenta, mode="lines", connectgaps=False,
        line=dict(color=T.MAGENTA, width=T.LINE_WIDTH), hoverinfo="skip",
    ))

    # Titik akhir dan puncak tertinggi — satu-satunya titik yang dilabeli.
    puncak = max(range(len(ys)), key=lambda i: ys[i])
    fig.add_trace(go.Scatter(
        x=[_dt(xs[puncak])], y=[ys[puncak]], mode="markers",
        marker=dict(size=T.MARKER_SIZE, color=T.score_color(ys[puncak]),
                    line=dict(width=2, color=T.PANEL)),
        hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=[_dt(xs[-1])], y=[ys[-1]], mode="markers",
        marker=dict(size=T.MARKER_SIZE + 1, color=T.score_color(ys[-1]),
                    line=dict(width=2, color=T.PANEL)),
        hoverinfo="skip",
    ))

    # Satu trace tak terlihat memegang seluruh hover, supaya tooltip-nya
    # satu baris rapi dan bukan tumpukan enam trace.
    teks = label if label is not None else ["" for _ in ys]
    fig.add_trace(go.Scatter(
        x=[_dt(x) for x in xs], y=ys, mode="markers",
        marker=dict(size=1, color="rgba(0,0,0,0)"),
        customdata=teks,
        hovertemplate="<b>%{x|%d %b %Y}</b><br>skor %{y:+.0f} · %{customdata}<extra></extra>",
    ))

    lo = min(-40.0, min(ys) - 8)
    hi = max(70.0, max(ys) + 8)

    bentuk = [dict(
        type="line", xref="paper", x0=0, x1=1, yref="y", y0=0, y1=0,
        line=dict(color=T.AXIS, width=1),
    )]
    anotasi = []
    if tampilkan_pita:
        for batas in (50, 20, -20):
            if lo < batas < hi:
                bentuk.append(dict(
                    type="line", xref="paper", x0=0, x1=1, yref="y",
                    y0=batas, y1=batas, line=dict(color=T.GRID, width=1),
                ))
        for bawah_pita, atas_pita, nama, warna in T.BANDS:
            tengah = (max(bawah_pita, lo) + min(atas_pita, hi)) / 2
            if lo < tengah < hi:
                anotasi.append(dict(
                    xref="paper", x=1.015, xanchor="left",
                    yref="y", y=tengah, yanchor="middle",
                    text=nama.upper(), showarrow=False,
                    font=dict(family=T.FONT_MONO, size=9, color=warna),
                    opacity=0.85 if nama != "netral" else 1.0,
                ))

    _dasar_layout(fig, 300, dict(l=56, r=170, t=16, b=28))
    fig.update_layout(
        shapes=bentuk, annotations=anotasi, hovermode="x",
        xaxis=dict(showspikes=True, spikecolor=T.VOLT, spikethickness=1,
                   spikedash="solid", spikemode="across", spikesnap="cursor"),
    )
    fig.update_yaxes(range=[lo, hi], tickvals=[-40, -20, 0, 20, 50, 70])
    return fig


def price_history(tanggal: list[str], tutup: list[float]) -> go.Figure:
    """Garis harga penutupan — satu deret, jadi satu warna dan tanpa legenda."""
    xs = [_dt(_ts(d)) for d in tanggal]
    ys = [float(v) for v in tutup]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines", fill="tozeroy",
        line=dict(width=0), fillcolor=_rgba(T.CYAN, 0.07), hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines",
        line=dict(color=_rgba(T.CYAN, T.GLOW_OPACITY), width=T.GLOW_WIDTH),
        hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="lines", line=dict(color=T.CYAN, width=T.LINE_WIDTH),
        hovertemplate="<b>%{x|%d %b %Y}</b><br>US$%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[xs[-1]], y=[ys[-1]], mode="markers",
        marker=dict(size=T.MARKER_SIZE, color=T.CYAN, line=dict(width=2, color=T.GROUND)),
        hoverinfo="skip",
    ))

    rentang = max(ys) - min(ys) or 1
    _dasar_layout(fig, 150, dict(l=56, r=56, t=10, b=24))
    fig.update_layout(
        hovermode="x",
        xaxis=dict(showspikes=True, spikecolor=T.VOLT, spikethickness=1,
                   spikedash="solid", spikemode="across", spikesnap="cursor"),
    )
    fig.update_yaxes(
        range=[min(ys) - rentang * 0.12, max(ys) + rentang * 0.12],
        showticklabels=False,
    )
    return fig


def _rgba(hex_warna: str, alpha: float) -> str:
    h = hex_warna.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


PLOTLY_CONFIG = {
    "displayModeBar": False,
    "scrollZoom": False,
    "staticPlot": False,
    "doubleClick": False,
}
