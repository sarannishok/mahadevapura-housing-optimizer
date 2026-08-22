"""V1 housing data-layer schema definitions.

Defines the PROPERTY and GYM field sets, which fields are raw
(source-observed facts) vs derived (computed/normalized), and the
missing-value sentinel. This is the data contract only -- no filtering,
scoring, scraping, or normalization logic lives here.

Actual V1 requirement thresholds (budget bands, hard filters, gym radius,
target localities) live in config/housing_filters_v1.yaml, not in this
module, so a future user can configure their own requirements without
editing this schema.
"""

MISSING = "unknown"

# --- PROPERTY schema --------------------------------------------------------

# Raw fields: observed/reported directly from the listing source. Never
# inferred -- if the source doesn't say, the value is MISSING ("unknown").
PROPERTY_RAW_FIELDS = [
    # IDENTITY
    "property_id",
    "source",
    "listing_url",
    # LOCATION
    "locality",  # as reported by source; may not match the canonical six
                 # target-locality spelling -- normalization is a future
                 # step, not done here.
    "society_name",
    "latitude",
    "longitude",
    # PROPERTY
    "configuration",
    "rent",
    "maintenance",
    "furnishing",           # one of FURNISHING_VALUES
    "property_age_years",
    "gated_society",        # one of GATED_SOCIETY_VALUES (tri-state, not boolean)
    "parking_type",         # one of PARKING_TYPE_VALUES
    # AVAILABILITY
    "available_from",
    "listing_date",
    "last_checked_at",
]

# Derived fields: computed from raw fields, not read directly from the
# source. The normalization logic (available_from -> availability_status)
# is not implemented yet -- this only reserves the field.
PROPERTY_DERIVED_FIELDS = [
    "availability_status",  # one of AVAILABILITY_STATUS_VALUES
]

# Full column order for a PROPERTY listings table.
PROPERTY_FIELDS = PROPERTY_RAW_FIELDS + PROPERTY_DERIVED_FIELDS

FURNISHING_VALUES = ["furnished", "semi-furnished", "unfurnished", MISSING]
GATED_SOCIETY_VALUES = ["yes", "no", MISSING]
PARKING_TYPE_VALUES = ["dedicated_closed", "dedicated_open", "shared", "none", MISSING]
AVAILABILITY_STATUS_VALUES = [
    "immediate",
    "within_7_days",
    "within_30_days",
    "over_30_days",
    MISSING,
]

# --- GYM schema (separate registry, not linked to PROPERTY yet) ------------

# All raw -- no quality-tier classification or distance-to-property field
# yet; that logic is explicitly deferred.
GYM_FIELDS = [
    "gym_id",
    "source",
    "gym_name",
    "locality",
    "latitude",
    "longitude",
    "brand_or_type_raw",  # raw string as reported, e.g. "Cult.fit",
                          # "local unbranded gym" -- not a scored tier.
    "last_checked_at",
]
