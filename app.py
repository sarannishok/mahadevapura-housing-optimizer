"""V1 "Find Areas" prototype UI.

Reads only the existing, already-computed commute-analysis datasets
(via ui/data_access.py). Makes no Google Routes API calls, uses no
Supabase, and does not touch the housing-filters module. See
ui/options.py for the V1-only dropdown values (Mahadevapura / 5 km /
Car) -- the registry there is written so a future office, distance, or
travel mode is an addition, not a rewrite.

All 6 analyzed localities are always shown, and EVERY representative
anchor ("residential reference point") of each locality is shown --
never collapsed to one. The selected distance is a preference/status
indicator (within vs. beyond range), applied independently at the
locality level (which section a locality is grouped under) and at the
individual reference-point level (its own badge). See
ui/data_access.annotate_range_status.

Run: streamlit run app.py
"""

import html
import textwrap
from datetime import datetime

import streamlit as st

from ui.data_access import annotate_range_status, get_localities
from ui.labels import (
    ANCHOR_BEYOND_BADGE,
    ANCHOR_WITHIN_BADGE,
    BEYOND_RANGE_BADGE,
    DISTANCE_LABEL,
    FIELD_LABELS,
    FIND_AREAS_BUTTON,
    HOW_IT_WORKS_BODY,
    HOW_IT_WORKS_NOTE,
    HOW_IT_WORKS_TITLE,
    NO_RESULTS_MESSAGE,
    OFFICE_LABEL,
    PAGE_TITLE,
    REFERENCE_POINTS_HEADING,
    SECTION_HEADING_TEMPLATE,
    SUBHEADING_TEMPLATE,
    SUMMARY_BEYOND_TEMPLATE,
    SUMMARY_WITHIN_TEMPLATE,
    TRAVEL_MODE_LABEL,
)
from ui.options import V1_DISTANCES_KM, V1_OFFICES, V1_TRAVEL_MODES

# NOTE: every HTML fragment below is passed through st.markdown(unsafe_allow_html=True).
# Markdown treats any line starting with 4+ spaces of indentation as a
# preformatted code block, which would print these tags as literal text
# instead of rendering them. textwrap.dedent().strip() strips that
# indentation so the HTML actually renders as HTML.
PAGE_STYLE = textwrap.dedent("""
    <style>
    .how-it-works {
        border: 1px solid rgba(128,128,128,0.25); border-radius: 8px;
        padding: 14px 18px; margin: 6px 0 18px 0; background: rgba(128,128,128,0.06);
    }
    .how-it-works .title { font-weight: 700; margin-bottom: 6px; }
    .how-it-works .body { font-size: 0.9rem; margin-bottom: 4px; }
    .how-it-works .note { font-size: 0.82rem; color: rgba(128,128,128,0.9); font-style: italic; }

    .group-divider-label {
        font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em;
        color: rgba(128,128,128,0.9); margin: 22px 0 10px 0;
        border-bottom: 1px solid rgba(128,128,128,0.15); padding-bottom: 6px;
    }

    .locality-card {
        padding: 14px 0 16px 0; border-bottom: 1px solid rgba(128,128,128,0.15);
    }
    .locality-card.beyond-range { opacity: 0.65; }
    .locality-header { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }
    .locality-name { font-size: 1.15rem; font-weight: 700; }
    .locality-score-badge {
        font-size: 0.8rem; font-weight: 600; padding: 2px 10px; border-radius: 10px;
        background: rgba(128,128,128,0.15); white-space: nowrap;
    }
    .locality-subline { font-size: 0.82rem; color: rgba(128,128,128,0.85); margin-top: 2px; }

    .reference-points-heading {
        font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em;
        color: rgba(128,128,128,0.75); margin: 12px 0 6px 0;
    }
    .anchor-row {
        padding: 6px 0 6px 14px; margin-bottom: 2px; border-left: 2px solid rgba(128,128,128,0.2);
    }
    .anchor-name { font-weight: 600; font-size: 0.92rem; }
    .anchor-metrics { font-size: 0.85rem; color: rgba(128,128,128,0.9); margin-top: 1px; }
    .anchor-badge { font-size: 0.78rem; margin-top: 3px; }
    .anchor-badge.within { color: #1e7d1e; }
    .anchor-badge.beyond { color: rgba(100,100,100,1); }
    </style>
""").strip()


def format_minutes(value):
    return f"{round(value)} min"


def format_distance(value_km):
    return f"{value_km:.1f} km"


def format_time_ampm(departure_time_hhmm):
    parsed = datetime.strptime(departure_time_hhmm, "%H:%M")
    return parsed.strftime("%I:%M %p").lstrip("0")


def format_commute_score(value):
    return f"{round(value)} / 100"


def render_how_it_works():
    box_html = textwrap.dedent(f"""
        <div class="how-it-works">
            <div class="title">{HOW_IT_WORKS_TITLE}</div>
            <div class="body">{HOW_IT_WORKS_BODY}</div>
            <div class="note">{HOW_IT_WORKS_NOTE}</div>
        </div>
    """).strip()
    st.markdown(box_html, unsafe_allow_html=True)


def _anchor_row_html(anchor):
    name = html.escape(anchor["representative_pocket"])
    badge_class = "within" if anchor["within_range"] else "beyond"
    badge_text = ANCHOR_WITHIN_BADGE if anchor["within_range"] else ANCHOR_BEYOND_BADGE
    metrics = (
        f"{format_distance(anchor['distance_km'])} · "
        f"{format_minutes(anchor['median_travel_minutes'])} {FIELD_LABELS['typical_travel_time']} · "
        f"{format_minutes(anchor['p90_travel_minutes'])} {FIELD_LABELS['slower_traffic_travel_time']}"
    )
    return textwrap.dedent(f"""
        <div class="anchor-row">
            <div class="anchor-name">• {name}</div>
            <div class="anchor-metrics">{metrics}</div>
            <div class="anchor-badge {badge_class}">{badge_text}</div>
        </div>
    """).strip()


def _locality_card_html(locality, group_class):
    name = html.escape(locality["locality"])
    anchors_html = "\n".join(_anchor_row_html(a) for a in locality["anchors"])
    return textwrap.dedent(f"""
        <div class="locality-card {group_class}">
            <div class="locality-header">
                <span class="locality-name">{name}</span>
                <span class="locality-score-badge">{FIELD_LABELS['commute_score']}: {format_commute_score(locality['commute_score'])}</span>
            </div>
            <div class="locality-subline">{FIELD_LABELS['reliable_until']} {format_time_ampm(locality['latest_fully_reliable_departure'])}</div>
            <div class="reference-points-heading">{REFERENCE_POINTS_HEADING}</div>
    """).strip() + "\n" + anchors_html + "\n</div>"


def render_results(results, distance_km):
    if not results:
        st.info(NO_RESULTS_MESSAGE)
        return

    within_range = sorted(
        (r for r in results if r["within_range"]),
        key=lambda r: r["commute_score"],
        reverse=True,
    )
    beyond_range = sorted(
        (r for r in results if not r["within_range"]),
        key=lambda r: r["commute_score"],
        reverse=True,
    )

    st.markdown(f"**{SUMMARY_WITHIN_TEMPLATE.format(count=len(within_range), distance=distance_km)}**")
    if beyond_range:
        st.caption(SUMMARY_BEYOND_TEMPLATE.format(count=len(beyond_range)))

    st.markdown(PAGE_STYLE, unsafe_allow_html=True)

    cards_html = "\n".join(_locality_card_html(loc, "") for loc in within_range)
    if beyond_range:
        cards_html += f'\n<div class="group-divider-label">{BEYOND_RANGE_BADGE}</div>\n'
        cards_html += "\n".join(
            _locality_card_html(loc, "beyond-range") for loc in beyond_range
        )

    st.markdown(cards_html, unsafe_allow_html=True)


def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="wide")
    st.title(PAGE_TITLE)

    office = st.selectbox(OFFICE_LABEL, options=list(V1_OFFICES.keys()))
    distance_km = st.selectbox(DISTANCE_LABEL, options=V1_DISTANCES_KM, format_func=lambda km: f"{km} km")
    travel_mode = st.selectbox(TRAVEL_MODE_LABEL, options=V1_TRAVEL_MODES)

    if st.button(FIND_AREAS_BUTTON, type="primary"):
        st.markdown(f"### {SECTION_HEADING_TEMPLATE.format(office=office)}")
        st.markdown(SUBHEADING_TEMPLATE.format(distance=distance_km, mode=travel_mode))

        render_how_it_works()

        localities = get_localities(office)
        results = annotate_range_status(localities, distance_km)
        render_results(results, distance_km)


if __name__ == "__main__":
    main()
