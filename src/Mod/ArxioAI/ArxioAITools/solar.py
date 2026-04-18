# SPDX-License-Identifier: LGPL-2.1-or-later
"""Solar / orientation analysis — no API required.

Implements the NOAA Solar Position Algorithm (simplified) to compute
sun elevation/azimuth for a given latitude/longitude/date/time, then
evaluates each wall of the active document to report its orientation
and whether it is facing the sun at the chosen moment. Useful to
orient living rooms, terraces, shading and PV panels.
"""

import datetime
import math

import FreeCAD


# ---------------------------------------------------------------------------
# Sun position (NOAA SPA, low-precision, ~1° accuracy — enough for
# massing decisions in early design phases)
# ---------------------------------------------------------------------------
def sun_position(lat_deg, lon_deg, when_utc):
    """Return (azimuth_deg, elevation_deg) for an observer at
    (lat, lon) at UTC datetime `when_utc`.

    Azimuth is measured clockwise from North (0° = N, 90° = E, 180° = S).
    """
    # Julian day
    y = when_utc.year
    m = when_utc.month
    d = when_utc.day + (
        when_utc.hour + when_utc.minute / 60.0 + when_utc.second / 3600.0
    ) / 24.0
    if m <= 2:
        y -= 1
        m += 12
    a = int(y / 100)
    b = 2 - a + int(a / 4)
    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5

    n = jd - 2451545.0  # days since J2000.0
    # Mean longitude of the sun
    L = (280.460 + 0.9856474 * n) % 360
    # Mean anomaly
    g = math.radians((357.528 + 0.9856003 * n) % 360)
    # Ecliptic longitude
    lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    # Obliquity of the ecliptic
    eps = math.radians(23.439 - 0.0000004 * n)
    # Right ascension and declination
    ra = math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam))
    dec = math.asin(math.sin(eps) * math.sin(lam))
    # Greenwich Mean Sidereal Time (hours)
    gmst = (18.697374558 + 24.06570982441908 * n) % 24
    # Local sidereal time
    lst = math.radians((gmst * 15 + lon_deg) % 360)
    # Hour angle
    h = lst - ra

    lat = math.radians(lat_deg)
    # Elevation
    sin_alt = math.sin(lat) * math.sin(dec) + math.cos(lat) * math.cos(dec) * math.cos(h)
    alt = math.asin(max(-1.0, min(1.0, sin_alt)))
    # Azimuth (from North, clockwise)
    y_az = -math.sin(h)
    x_az = math.tan(dec) * math.cos(lat) - math.sin(lat) * math.cos(h)
    az = (math.degrees(math.atan2(y_az, x_az)) + 360) % 360

    return az, math.degrees(alt)


# ---------------------------------------------------------------------------
# Wall orientation analysis
# ---------------------------------------------------------------------------
def _is_wall(obj):
    proxy = getattr(getattr(obj, "Proxy", None), "__class__", type(None)).__name__
    return "Wall" in proxy or getattr(obj, "IfcType", "") == "Wall"


def _wall_outward_normal(wall):
    """Best-effort horizontal outward normal for a wall (unit vector)."""
    base = getattr(wall, "Base", None)
    if base is None or not getattr(base, "Shape", None):
        return None
    edges = base.Shape.Edges
    if not edges:
        return None
    edge = edges[0]
    p1 = edge.Vertexes[0].Point
    p2 = edge.Vertexes[-1].Point
    dir_along = FreeCAD.Vector(p2.x - p1.x, p2.y - p1.y, 0.0)
    if dir_along.Length < 1e-6:
        return None
    dir_along.normalize()
    # Perpendicular in XY, rotated +90°: this gives ONE of the two
    # possible normals. For the MVP we report both in the summary.
    return FreeCAD.Vector(-dir_along.y, dir_along.x, 0.0)


def _cardinal(az_deg):
    # 8-point compass
    dirs = [
        ("N", 0),
        ("NE", 45),
        ("E", 90),
        ("SE", 135),
        ("S", 180),
        ("SO", 225),
        ("O", 270),
        ("NO", 315),
    ]
    # Closest cardinal
    best = min(dirs, key=lambda p: min(abs(az_deg - p[1]), 360 - abs(az_deg - p[1])))
    return best[0]


def analyse(doc, lat, lon, when_utc):
    """Compute sun position + per-wall orientation/exposure.

    Returns a dict consumable by the UI layer.
    """
    az_sun, alt_sun = sun_position(lat, lon, when_utc)
    walls = [o for o in doc.Objects if _is_wall(o)]

    wall_rows = []
    for w in walls:
        n = _wall_outward_normal(w)
        if n is None:
            continue
        # Normal azimuth (from North, CW)
        az_n = (math.degrees(math.atan2(n.x, n.y))) % 360
        # Also the opposite face
        az_n2 = (az_n + 180) % 360
        best_az = az_n if _alignment(az_n, az_sun) >= _alignment(az_n2, az_sun) else az_n2
        exposure_deg = 180 - min(
            abs(best_az - az_sun), 360 - abs(best_az - az_sun)
        )
        exposed = alt_sun > 0 and exposure_deg > 90  # sun "in front of" the wall
        wall_rows.append(
            {
                "label": w.Label,
                "facing_az_deg": round(best_az, 1),
                "facing_cardinal": _cardinal(best_az),
                "exposure_score_deg": round(exposure_deg, 1),
                "sunlit": exposed,
            }
        )

    return {
        "latitude": lat,
        "longitude": lon,
        "when_utc": when_utc.isoformat(),
        "sun_azimuth_deg": round(az_sun, 1),
        "sun_elevation_deg": round(alt_sun, 1),
        "sun_cardinal": _cardinal(az_sun),
        "walls": wall_rows,
    }


def _alignment(face_az, sun_az):
    """Score 0..180: 180 = wall fully facing sun."""
    delta = abs(face_az - sun_az)
    if delta > 180:
        delta = 360 - delta
    return 180 - delta


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
def open_dialog(doc):
    """Qt dialog to collect parameters and display the analysis."""
    try:
        from PySide import QtCore, QtWidgets
    except ImportError:  # pragma: no cover
        return None

    dlg = QtWidgets.QDialog()
    dlg.setWindowTitle("Arxio AI — Analyse solaire")
    dlg.resize(620, 540)
    layout = QtWidgets.QVBoxLayout(dlg)

    form = QtWidgets.QFormLayout()
    lat = QtWidgets.QDoubleSpinBox()
    lat.setRange(-90.0, 90.0)
    lat.setDecimals(4)
    lat.setValue(6.1725)  # Lomé by default
    lon = QtWidgets.QDoubleSpinBox()
    lon.setRange(-180.0, 180.0)
    lon.setDecimals(4)
    lon.setValue(1.2314)
    date = QtWidgets.QDateEdit(QtCore.QDate.currentDate())
    date.setCalendarPopup(True)
    time = QtWidgets.QTimeEdit(QtCore.QTime(12, 0))
    form.addRow("Latitude (°)", lat)
    form.addRow("Longitude (°)", lon)
    form.addRow("Date (locale)", date)
    form.addRow("Heure (locale)", time)
    layout.addLayout(form)

    run_btn = QtWidgets.QPushButton("Analyser")
    layout.addWidget(run_btn)

    out = QtWidgets.QTextBrowser()
    layout.addWidget(out, stretch=1)

    def _run():
        local = datetime.datetime(
            date.date().year(),
            date.date().month(),
            date.date().day(),
            time.time().hour(),
            time.time().minute(),
        )
        # Naive: treat local as UTC+0; for production, honour system tz.
        report = analyse(doc, lat.value(), lon.value(), local)
        out.setMarkdown(_format_report(report))

    run_btn.clicked.connect(_run)

    close = QtWidgets.QPushButton("Fermer")
    close.clicked.connect(dlg.accept)
    layout.addWidget(close)

    _run()
    dlg.exec_()
    return dlg


def _format_report(r):
    lines = [
        f"### Soleil — {r['when_utc']}",
        "",
        f"- Position : **{r['sun_cardinal']}** — azimut {r['sun_azimuth_deg']}°, "
        f"élévation {r['sun_elevation_deg']}°",
        f"- Lieu : lat {r['latitude']}°, lon {r['longitude']}°",
        "",
        "### Murs du projet",
        "",
        "| Mur | Orientation | Score d'exposition | Ensoleillé ? |",
        "|---|---|---|---|",
    ]
    if not r["walls"]:
        lines.append("| — | aucun mur Arch détecté | — | — |")
    else:
        for w in r["walls"]:
            sun = "☀" if w["sunlit"] else "—"
            lines.append(
                f"| {w['label']} | {w['facing_cardinal']} ({w['facing_az_deg']}°) | "
                f"{w['exposure_score_deg']}° | {sun} |"
            )
    lines.append("")
    lines.append(
        "*Astuce :* pour le climat tropical, limiter les grandes baies à l'**Ouest**, "
        "privilégier **Nord** et **Sud** ; en climat tempéré, maximiser le **Sud**."
    )
    return "\n".join(lines)
