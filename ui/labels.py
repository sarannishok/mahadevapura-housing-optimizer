"""User-facing terminology for the "Find Areas" prototype.

Single source of truth for how internal field names are shown to a user.
In particular: P90 is never displayed -- it is always shown as
"Slower-traffic travel time". Keep the underlying scoring/data fields as
they are; only the display strings live here.
"""

FIELD_LABELS = {
    "locality": "Area",
    "distance_km": "Distance from office",
    "typical_travel_time": "typical",
    "slower_traffic_travel_time": "slower traffic",
    "reliable_until": "Reliable until",
    "commute_score": "Commute score",
}

PAGE_TITLE = "Commute Intelligence"
FIND_AREAS_BUTTON = "Find Areas"
OFFICE_LABEL = "Office location"
DISTANCE_LABEL = "Preferred travel distance"
TRAVEL_MODE_LABEL = "Travel mode"
NO_RESULTS_MESSAGE = "No commute data available for this office yet."

SECTION_HEADING_TEMPLATE = "Areas around {office}"
SUBHEADING_TEMPLATE = "Your preferred distance: {distance} km · {mode}"

WITHIN_RANGE_BADGE = "Within your preferred range"
BEYOND_RANGE_BADGE = "Beyond your preferred range"

SUMMARY_WITHIN_TEMPLATE = "{count} areas are within your preferred {distance} km range"
SUMMARY_BEYOND_TEMPLATE = "{count} additional areas shown for comparison"

# "How we estimate your commute" explainer, shown above the results.
HOW_IT_WORKS_TITLE = "How we estimate your commute"
HOW_IT_WORKS_BODY = (
    "Each area is represented by a few residential reference points selected "
    "near residential clusters. We use these points to estimate the commute "
    "from that area to your office."
)
HOW_IT_WORKS_NOTE = "These are reference points, not individual properties or exact addresses."

REFERENCE_POINTS_HEADING = "Residential reference points"
ANCHOR_WITHIN_BADGE = "🟢 Within your preferred range"
ANCHOR_BEYOND_BADGE = "⚪ Beyond your preferred range"
