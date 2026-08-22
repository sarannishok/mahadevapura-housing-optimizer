# Housing Data Acquisition Strategy — Research & Design Document

Status: research only. No listings have been collected, scraped, or stored.
No automated requests were made to any listing platform's search or
property pages — only to public policy files (`robots.txt`) and public
Terms of Use / Terms & Conditions pages, which is standard due-diligence
reading, not data collection.

## 1. Purpose & scope

This document evaluates candidate sources for the property-listing data
that will eventually populate the `PROPERTY` schema defined in
`src/housing_schema.py`. The current project is a **personal prototype**
for one user's own Bangalore apartment search. Section 5 explicitly flags
everything that would need to be re-evaluated if this ever became a
general consumer product serving other users.

Nothing here authorizes or performs any data collection. This is
input to a future, separately-approved decision about *how* (or whether)
to acquire listing data from each source.

## 2. Methodology

Each source was evaluated using only its **public policy files** —
`robots.txt` (fetched directly) and its published Terms of Use / Terms &
Conditions page (fetched where accessible). No login was used, no listing
or search page was requested, and no listing content was retrieved.

Every claim below is labeled:
- **[FACT — source: <what was fetched>]** — directly observed in the
  platform's own `robots.txt` or Terms page, quoted or paraphrased with
  the section noted where possible.
- **[FACT — third-party report]** — a claim from a secondary source (e.g.
  a scraping-vendor's blog), not verified against the platform's own
  documentation. Flagged as such because it is not primary evidence.
- **[INFERENCE]** — my own judgment where the primary source was silent,
  inaccessible, or ambiguous.
- **UNKNOWN/UNCLEAR** — used explicitly whenever available information was
  insufficient to reach a conclusion, rather than assuming permission.

Where a platform's Terms page could not be retrieved at all (several
blocked the automated fetch tool outright — itself a relevant finding,
noted per source), that is stated plainly rather than papered over.

## 3. Source-by-source evaluation

### Housing.com

1. **Official access method/API/feed**: UNKNOWN/UNCLEAR. No public
   developer API or data-feed program was found via search. [INFERENCE —
   absence of search results is not proof no such program exists; a
   private/partner-only program cannot be ruled out.]

2. **Restrictions on automated access**: **[FACT — source: housing.com's
   own `robots.txt`, fetched directly]** it explicitly disallows crawling
   of, among others: `/*/*/search*`, `/rent/search-*`,
   `/paying-guests/search-*`, `/rent/recommendations/*`,
   `/rent/shortlist*`, `/developer/*`. The rental search-result paths —
   exactly what a listings collector would need — are explicitly
   disallowed for all crawlers (`User-Agent: *`).
   The Terms of Use text itself could **not** be retrieved: two direct
   fetch attempts (`housing.com/terms`, `housing.com/tnc`) both returned
   HTTP 406 to the automated fetch tool. **[FACT — the fetch tool itself
   was blocked/rejected]**; I could not read or quote the actual legal
   terms.

3. **Permitted / unclear / requires permission**: UNCLEAR on the legal
   text (couldn't access it), but the `robots.txt` disallow list directly
   covers the pages this project would need, and the site's edge
   infrastructure rejected non-browser requests even for the terms page.
   [INFERENCE, from the two confirmed facts above] this reads as **not
   intended for automated access** to rental listings.

4. **Fields matching our schema**: Not assessed — doing so would require
   viewing actual listing pages, which this research step deliberately
   did not do. [INFERENCE, general knowledge of Indian rental portals,
   unverified] listing pages typically show rent, configuration,
   locality, society name, and furnishing status.

5. **Freshness/availability determinability**: UNKNOWN/UNCLEAR — not
   assessed for the same reason as (4).

6. **Storing normalized facts — permitted/unclear**: UNCLEAR — could not
   verify against the actual Terms text.

7. **Linking back to the original listing**: Not assessed.

8. **Recommended acquisition method**: **Manual only**, if used at all — a
   human (you) browsing the site directly and personally noting relevant
   fields for a small number of candidate listings you are personally
   considering is a fundamentally different activity from automated
   collection, and isn't blocked by anything found here. **Do not automate.**

### NoBroker

1. **Official access method/API/feed**: UNKNOWN/UNCLEAR. No public
   developer API or partner feed found via search.

2. **Restrictions on automated access**: **[FACT — source:
   `nobroker.in/robots.txt`, fetched directly]** disallows crawling of
   `/property/listing/` explicitly, plus all of `/api/v1/` through
   `/api/v5/`, `/falcon/*`, and various admin/auth paths.

   **[FACT — source: `nobroker.in/terms-and-condition`, fetched and quoted
   directly]**, Section 15 ("Content on the Site") prohibits the user
   from:
   > "(vii) license, sublicense, sell, resell, transfer, assign,
   > distribute or otherwise commercially exploit or make available to
   > any third party the Service or any content contained in or made
   > available through the Service in any way"

   > "(ix) create internet 'links' to the Site or 'frame' or 'mirror' any
   > Content on any other server or wireless or internet-based device"

   > "(x) reverse engineer or access the Service in order to (a) build a
   > product competitive with the Service, (b) build a product using
   > ideas, features, functions or graphics similar to those of the
   > Service, or (c) copy any ideas, features, functions or graphics
   > contained in the Service"

   Section 17(v) further states:
   > "The User further accepts and agrees that NoBroker shall have
   > Intellectual Property Rights on all information and data provided or
   > shared by the User on the Site."

3. **Permitted / unclear / requires permission**: **Not permitted** for
   automated collection, reproduction, or redistribution — this is the
   most explicit and direct prohibition found among all four sources.
   [FACT-based conclusion] Clause (x) is particularly relevant: it
   prohibits building "a product competitive with the Service" using
   ideas/features from it — worth remembering if this project's scope
   ever grows into something NoBroker-adjacent.

4. **Fields matching our schema**: [INFERENCE, unverified] typical fields
   likely include rent, deposit, configuration, furnishing, locality,
   society name — probably a good schema match in principle, but
   irrelevant given (3).

5. **Freshness/availability determinability**: [INFERENCE, unverified]
   listings typically show a relative "posted X days ago" indicator.

6. **Storing normalized facts — permitted/unclear**: **Not permitted** —
   Section 15(vii)'s "content contained in or made available through the
   Service" is broad, and Section 17(v)'s IP claim over "all information
   and data" on the site plausibly extends to normalized/derived records
   built from that content, not just verbatim copies.

7. **Linking back to the original listing**: Technically possible (URLs
   are public), but moot given (3).

8. **Recommended acquisition method**: **Do not automate against NoBroker
   in any form**, including for personal use — the explicit
   no-commercial-exploitation and no-competitive-product clauses, plus
   the IP claim, make this the clearest RED of the four. Manual,
   individual browsing for your own reference is the only use this
   research supports.

### MagicBricks

1. **Official access method/API/feed**: UNKNOWN/UNCLEAR. No public
   developer API or feed found via search.

2. **Restrictions on automated access**: **[FACT — source:
   `magicbricks.com/robots.txt`, fetched directly]** disallows
   `/property/*`, `/propertyDetails/map-of-*`, `/propertyDetails/viewProject`,
   and several other property-related paths. It also explicitly blocks a
   named list of known bots (`Wotbox`, `SEOkicks-Robot`, `oBot`,
   `IstellaBot`, `YoudaoBot`, `SeznamBot`, `yacybot`), while explicitly
   *allowing* named AI crawlers (`OAI-SearchBot`, `PerplexityBot`,
   `Applebot-Extended`) — indicating a deliberate, selective bot policy
   rather than a blanket ban, but one that still disallows the
   property-listing paths this project would need.

   The Terms & Conditions page could **not** be retrieved — the fetch
   tool was unable to connect at all. **[FACT — the fetch tool itself
   failed against magicbricks.com]**, I could not read the actual legal
   text. **[FACT — third-party report, not verified firsthand]**: a
   scraping-vendor site (ProxyEmpire) states MagicBricks sits behind
   Akamai bot protection that returns an "Access Denied" page to any
   non-browser request, including plain HTTP clients and datacenter
   proxies — consistent with what I observed, but I'm citing this as a
   third-party claim, not something I verified myself.

3. **Permitted / unclear / requires permission**: UNCLEAR on the legal
   text (inaccessible), but the `robots.txt` disallow on property paths
   plus the inability to even reach the terms page [INFERENCE] point
   toward **not intended for automated access**.

4. **Fields matching our schema**: Not assessed.

5. **Freshness/availability determinability**: Not assessed.

6. **Storing normalized facts — permitted/unclear**: UNCLEAR — terms
   unreachable.

7. **Linking back to the original listing**: Not assessed.

8. **Recommended acquisition method**: **Manual only, if at all.** Given
   the inaccessible terms and the property-path disallow, any future use
   beyond manual personal browsing would require someone to actually read
   the Terms & Conditions in a normal browser first, and likely to
   contact MagicBricks directly about a data licensing arrangement before
   automating anything.

### 99acres

1. **Official access method/API/feed**: UNKNOWN/UNCLEAR. No public
   developer API or feed found via search.

2. **Restrictions on automated access**: **[FACT — directly observed]**
   even a plain `robots.txt` request to `99acres.com` returned an HTTP
   403 "Access Denied" page from an Akamai edge node (error reference
   `18.171cc517...` shown in the response body) — the site's edge
   infrastructure rejected the request before it reached any
   policy-serving logic. The Terms of Use page returned HTTP 403 to the
   fetch tool as well. This is the strongest technical barrier found
   among the four sources: 99acres blocks non-browser automated requests
   at the network edge, even for retrieving its own public policy
   documents.

3. **Permitted / unclear / requires permission**: Legal terms UNKNOWN
   (never retrieved), but [INFERENCE] the aggressive edge-level blocking
   is a strong practical barrier independent of whatever the written
   terms say.

4.–7. Not assessed — no information could be retrieved.

8. **Recommended acquisition method**: **Do not attempt automation in any
   form.** If used at all, manual personal browsing only, exactly as with
   the others.

### Other candidates considered (not deeply researched)

- **OLX / local classifieds, direct broker outreach, or
  word-of-mouth/society-office listings**: plausible manual-only
  channels for a personal search, not researched in depth here given time
  constraints. Flagged as a candidate for future research if the four
  primary platforms remain unusable.
- **Government/public open data**: no known official open dataset of
  Bangalore rental listings was found or searched for exhaustively. Not
  pursued further in this pass.

## 4. Ranking summary

| Source | Rating | Reason |
|---|---|---|
| Housing.com | 🔴 RED | `robots.txt` explicitly disallows rental search pages; ToS text unreachable (406 on two attempts) — technical evidence points against automated access; legal text UNCLEAR. |
| NoBroker | 🔴 RED | Explicit ToS prohibition on commercial exploitation, mirroring, and building a competitive product; explicit IP claim over site data (Section 15, 17(v)) — the clearest case. |
| MagicBricks | 🔴 RED | `robots.txt` disallows property paths; ToS page unreachable by automated tooling; third-party reports (unverified firsthand) describe aggressive bot-blocking. |
| 99acres | 🔴 RED | Strongest technical barrier — even `robots.txt` itself returns HTTP 403 from edge infrastructure; ToS unreachable; nothing could be verified. |

**No source cleared GREEN or YELLOW for automated access.** This is the
honest finding, not a gap in the research: every one of the four major
platforms either explicitly prohibits the relevant automated use (NoBroker)
or presents a technical/legal picture too unclear or actively blocked to
proceed on (the other three). The practical path for V1 — and the one
this research supports — is **manual, human-entered data** into the
`PROPERTY` schema already defined, not automated collection from any of
these four sources.

## 5. Commercialization flags

Everything below is specific to *if this project ever becomes a general
consumer product* used by people other than you:

- **NoBroker's clauses would be directly triggered by commercialization**:
  "commercially exploit," "make available to any third party," and "build
  a product competitive with the Service" are squarely aimed at exactly
  what a multi-user consumer product would do. A commercial pivot without
  an explicit licensing/partnership agreement from NoBroker would be a
  clear contract violation, not a gray area.
- **Personal use and multi-user redistribution are legally different
  postures, even where the terms are silent or unclear** (Housing.com,
  MagicBricks, 99acres). A single person manually noting facts about
  listings they're personally considering is a different activity from a
  product that systematically collects and redistributes listing data to
  other users — the latter is exactly the kind of use these platforms'
  terms (where readable) and technical bot-blocking are designed to
  prevent.
- **Any commercial version would need one of**: (a) explicit written
  data-licensing or partnership agreements with each platform used, (b)
  a switch to genuinely independent data sources (paid data providers,
  direct society/broker relationships, user-submitted listings), or (c)
  formal legal review before relying on any of these four platforms at
  scale.
- **This document's RED ratings are not a legal opinion** — they reflect
  what could and couldn't be verified from public policy pages in this
  research pass. Before any commercial use, get an actual legal review
  rather than relying on this document.

## 6. Open questions / recommended next steps

- Housing.com's and MagicBricks' actual Terms of Use/Conditions text was
  never read (both blocked automated retrieval) — if either platform is
  ever considered for anything beyond manual personal browsing, someone
  needs to actually read those terms in a normal browser first.
- No source's official-API question was fully closed — "no public API
  found via search" is not the same as "confirmed no API exists." Worth a
  direct email to each platform's support/partnerships contact if
  automated access is ever genuinely needed.
- The "other candidates" list (OLX, direct broker outreach, open data)
  was not researched in this pass and would need its own evaluation round
  if the four primary platforms remain unusable.
- Recommended immediate next step: proceed with **manual entry** of
  candidate listings into the existing `PROPERTY` schema
  (`src/housing_schema.py`), sourced from whatever platforms you
  personally browse as a human user — not from any automated process.
