"""Visual theme and small HTML helpers for the travel planner dashboard.

Everything here is presentation only: no planning logic lives in this file.
"""

import html

import streamlit as st

PALETTE = {
    "green": "#0f5c4d",
    "green_soft": "#e4f1ec",
    "yellow": "#ffd966",
    "purple": "#5b1d4f",
    "blue": "#b8c0ff",
    "ink": "#17211e",
    "muted": "#6b7773",
    "bg": "#f7f5ef",
    "card": "#ffffff",
}

MODE_ICONS = {"Car": "🚗", "Taxi": "🚕", "Train": "🚆", "Flight": "✈️"}

CSS = f"""
<style>
.stApp {{ background: {PALETTE['bg']}; }}
.block-container {{ padding-top: 1.5rem; max-width: 1280px; }}
section[data-testid="stSidebar"] {{ background: #fff; border-right: 1px solid #ece8dd; }}

.hero {{
    background: linear-gradient(135deg, #0f5c4d 0%, #1b7f6a 55%, #3aa088 100%);
    color: #fff; border-radius: 22px; padding: 28px 32px; margin-bottom: 18px;
}}
.hero h1 {{ margin: 0 0 6px 0; font-size: 2rem; color: #fff; }}
.hero p {{ margin: 0; opacity: .88; }}

.card {{
    background: {PALETTE['card']}; border-radius: 20px; padding: 18px 20px;
    box-shadow: 0 1px 3px rgba(20,40,35,.06); margin-bottom: 16px;
}}
.card h3 {{ margin: 0 0 12px 0; font-size: 1.05rem; color: {PALETTE['ink']}; }}
.card.yellow {{ background: {PALETTE['yellow']}; }}
.card.soft-green {{ background: {PALETTE['green_soft']}; border: 1px solid #cfe5dc; }}
.card.purple {{ background: {PALETTE['purple']}; color: #fff; }}
.card.purple h3 {{ color: #fff; }}
.card.blue {{ background: {PALETTE['blue']}; }}

.pill {{
    display: inline-block; background: {PALETTE['green_soft']}; color: {PALETTE['green']};
    border-radius: 999px; padding: 4px 12px; font-size: .85rem; font-weight: 600; margin-right: 6px;
}}

.stat-strip {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }}
.stat {{ background: #fff; border-radius: 16px; padding: 14px 16px; }}
.stat .v {{ font-size: 1.35rem; font-weight: 700; color: {PALETTE['ink']}; }}
.stat .l {{ font-size: .8rem; color: {PALETTE['muted']}; }}

.timeline {{ position: relative; margin-left: 6px; }}
.stop {{ display: flex; gap: 12px; align-items: flex-start; padding-bottom: 10px; }}
.badge {{
    background: {PALETTE['green']}; color: #fff; border-radius: 999px;
    min-width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: .8rem;
}}
.stop .name {{ font-weight: 700; color: {PALETTE['ink']}; }}
.stop .sub {{ font-size: .82rem; color: {PALETTE['muted']}; }}
.leg {{
    margin: 0 0 10px 42px; display: inline-block; background: #f1efe7;
    border-radius: 10px; padding: 4px 10px; font-size: .8rem; color: {PALETTE['ink']};
}}

.donut {{
    width: 170px; height: 170px; border-radius: 50%; margin: 6px auto 12px auto;
    display: flex; align-items: center; justify-content: center;
}}
.donut .hole {{
    width: 105px; height: 105px; background: #fff; border-radius: 50%;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
}}
.donut .hole b {{ font-size: 1.25rem; color: {PALETTE['ink']}; }}
.donut .hole span {{ font-size: .75rem; color: {PALETTE['muted']}; }}
.legend-row {{ display: flex; justify-content: space-between; font-size: .88rem; padding: 3px 0; }}
.dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 8px; }}

.day {{ border-bottom: 1px solid #eee9dc; padding: 10px 0; }}
.day:last-child {{ border-bottom: none; }}
.day-tag {{
    background: #e9e4d3; border-radius: 8px; padding: 2px 9px; font-size: .78rem;
    font-weight: 600; margin-right: 8px;
}}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def _e(value):
    return html.escape(str(value))


def short_name(full_name):
    """Nominatim returns long display names; keep only the first part."""
    return str(full_name).split(",")[0].strip()


def hero(title, subtitle):
    st.markdown(
        f'<div class="hero"><h1>{_e(title)}</h1><p>{_e(subtitle)}</p></div>',
        unsafe_allow_html=True,
    )


def pills(items):
    body = "".join(f'<span class="pill">{_e(item)}</span>' for item in items)
    st.markdown(body, unsafe_allow_html=True)


def stat_strip(stats):
    """stats: list of (value, label)."""
    cells = "".join(
        f'<div class="stat"><div class="v">{_e(v)}</div><div class="l">{_e(l)}</div></div>'
        for v, l in stats
    )
    st.markdown(f'<div class="stat-strip">{cells}</div>', unsafe_allow_html=True)


def route_timeline(locations, legs):
    """Vertical list of stops with the transport leg between each pair."""
    parts = ['<div class="card"><h3>Route summary</h3><div class="timeline">']
    for index, place in enumerate(locations):
        label = "Start" if index == 0 else f"Stop {index}"
        parts.append(
            f'<div class="stop"><div class="badge">{index + 1}</div>'
            f'<div><div class="name">{_e(short_name(place["name"]))}</div>'
            f'<div class="sub">{label}</div></div></div>'
        )
        if index < len(legs):
            leg = legs[index]
            icon = MODE_ICONS.get(leg["mode"], "🧭")
            hours = float(leg["hours"])
            whole, minutes = int(hours), int(round((hours - int(hours)) * 60))
            parts.append(
                f'<div class="leg">{icon} {_e(leg["mode"])} · {whole}h {minutes:02d}m · '
                f'{float(leg.get("distance_km", 0)):,.0f} km</div>'
            )
    parts.append("</div></div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def budget_donut(breakdown, budget):
    """breakdown: dict of category -> amount. Pure CSS conic-gradient donut."""
    colors = ["#0f5c4d", "#ffd966", "#b8c0ff", "#e07a5f"]
    total = sum(breakdown.values()) or 1
    stops, start = [], 0.0
    for color, amount in zip(colors, breakdown.values()):
        end = start + amount / total * 100
        stops.append(f"{color} {start:.1f}% {end:.1f}%")
        start = end
    used_pct = min(999, round(sum(breakdown.values()) / budget * 100)) if budget else 0

    legend = "".join(
        f'<div class="legend-row"><span><span class="dot" style="background:{c}"></span>{_e(k)}</span>'
        f'<b>₹{v:,.0f}</b></div>'
        for c, (k, v) in zip(colors, breakdown.items())
    )
    st.markdown(
        f'<div class="card"><h3>Budget</h3>'
        f'<div class="donut" style="background: conic-gradient({", ".join(stops)})">'
        f'<div class="hole"><b>{used_pct}%</b><span>of budget used</span></div></div>'
        f'{legend}</div>',
        unsafe_allow_html=True,
    )


def day_cards(locations, days, legs):
    """Spread the stops across the trip days as a simple day-by-day outline."""
    stops = [short_name(p["name"]) for p in locations]
    parts = ['<div class="card"><h3>Days &amp; activity</h3>']
    for day in range(1, days + 1):
        if day == 1:
            text = f"Depart {stops[0]}" + (f" for {stops[1]}" if len(stops) > 1 else "")
        elif day == days:
            text = f"Final day in {stops[-1]} and return"
        else:
            idx = min(len(stops) - 1, max(1, round(day * (len(stops) - 1) / days)))
            text = f"Explore {stops[idx]}"
        parts.append(f'<div class="day"><span class="day-tag">Day {day}</span>{_e(text)}</div>')
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)