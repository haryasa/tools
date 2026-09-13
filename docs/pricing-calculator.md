# Guesthouse Pricing Calculator — PRD

## 1. Goal

A single-file HTML tool, `tools/pricing-calculator.html`, for a guesthouse or
similar property with **one or more unit types**. All units of a type share one
rate; types share one set of pricing rules and differ only in their base rate,
their floor, and optionally their length-of-stay discounts. It lets the owner:

1. **Quote** a direct booking: price breakdown, negotiation range, PBJT, guest total.
2. **View a price calendar**: nightly rate, minimum stay, and OTA rate for a date range.
3. **Edit the pricing rules** without touching code, and share them as a link.

All amounts are IDR, whole rupiah. Everything ships in one phase; §9 lists what
is deliberately left out.

---

## 2. Definitions

| Term | Meaning |
| --- | --- |
| Unit type | A group of units priced identically, e.g. "Standard" or "Family". Every quote and calendar rate is for one type |
| Night of D | The stay from date D to D+1. A stay's nights are check-in … checkout − 1. |
| Nights | checkout − check-in, in days |
| Lead time | check-in − booking date, in days |
| Extension | A stay that starts on the checkout date of the same guest's current stay |
| `round(x)` | Nearest whole rupiah, halves up |
| `round_inc(x)` | Nearest multiple of `rounding_increment`, halves up |
| `ceil_inc(x)` | Next multiple of `rounding_increment` at or above x |

---

## 3. Configuration

Defaults, which are also the format used by the settings link:

```json
{
  "version": 1,
  "unit_types": [
    { "name": "Standard", "base_nightly_rate": 500000, "floor_nightly_rate": 350000 }
  ],
  "floor_pct_of_rate": 65,
  "rounding_increment": 10000,
  "tax_pct": 10,
  "preparation_days": 1,
  "ota_host_fee_pct": 15.5,
  "ota_tax_base": "gross",

  "weekend": { "nights": ["fri", "sat"], "multiplier": 1.10 },

  "seasons": [
    { "name": "Low",    "multiplier": 0.90, "min_stay": 2 },
    { "name": "Normal", "multiplier": 1.00, "min_stay": 2 },
    { "name": "High",   "multiplier": 1.20, "min_stay": 3 },
    { "name": "Peak",   "multiplier": 1.30, "min_stay": 3 }
  ],
  "month_seasons": ["High", "Low", "Low", "Normal", "Normal", "High",
                    "Peak", "Peak", "High", "Normal", "Low", "High"],

  "special_dates": [
    { "name": "Christmas & New Year", "start": "2026-12-20", "end": "2027-01-05",
      "multiplier": 1.40, "min_stay": 5 }
  ],

  "los_tiers": [
    { "min_nights": 7,  "discount_pct": 10 },
    { "min_nights": 14, "discount_pct": 20 },
    { "min_nights": 28, "discount_pct": 30 }
  ],

  "last_minute": {
    "enabled": false,
    "tiers": [
      { "max_lead_days": 1,  "discount_pct": 15 },
      { "max_lead_days": 7,  "discount_pct": 10 },
      { "max_lead_days": 14, "discount_pct": 5 }
    ]
  },

  "negotiation": { "ask_buffer_pct": 5, "max_discount_pct": 5 }
}
```

Rules:

- **Unit types**: at least one, with unique names. Each sets its own
  `base_nightly_rate` and `floor_nightly_rate`. A type may also carry its own
  `los_tiers`, which **replaces** the top-level ladder for that type entirely —
  tiers are not merged. A type without one uses the top-level `los_tiers`. That
  ladder is the type's **LOS ladder** everywhere below. Everything else in the
  config is shared by all types. For example:

  ```json
  { "name": "Family", "base_nightly_rate": 750000, "floor_nightly_rate": 500000,
    "los_tiers": [
      { "min_nights": 7,  "discount_pct": 5 },
      { "min_nights": 14, "discount_pct": 15 },
      { "min_nights": 28, "discount_pct": 25 }
    ] }
  ```

- **Seasons**: each month maps to one named season.
- **Special dates** belong to a specific year. `start` and `end` are the first
  and last nights included. `min_stay` is optional; if it's missing, the
  season's value is used. Special dates must not overlap.
- **LOS tier**: the tier in the type's LOS ladder with the highest
  `min_nights` ≤ nights; no match → 0%.
- **Last-minute tier**: the tier with the smallest `max_lead_days` ≥ lead time;
  no match → 0%.
- **LOS and last-minute do not stack**, and nothing else compounds. They
  resolve by fixed priority, not by depth: a stay that reaches any LOS tier
  takes it, and last-minute applies only to a stay that doesn't (§4.2). This is
  Airbnb's order, adopted so a direct quote and the same stay on the channel
  take the same discount (§5.2).
- **`last_minute.enabled` defaults to `false`.** A lead-time ladder discounts
  every late booking, including the ones that would have come anyway; the
  practice it imitates is gap-filling a date that is genuinely at risk. Turn it
  on when the calendar is soft, off when it isn't.
- **`ota_tax_base`**: what PBJT is charged on for an OTA booking, where the
  guest never paid it on top and it comes out of the payout instead (§4.1).
  `"gross"` if you owe it on the guest's full payment, `"payout"` if your
  bapenda lets you compute it on what the channel pays you after commission.
  The rate is always `tax_pct`; this only picks the base. There is no setting
  that skips the tax: a smaller base is still taxed.

### 3.1 Why the tiers step instead of tapering

An earlier draft required each tier to be shallow enough that a longer stay
always costs more than a shorter one. Holding that line caps the deepest tier at
roughly 16%, which is well below what the market offers for a month, and it
produced a 21-night tier so tight that the 21st night came out free in five of
seven possible start-days.

Threshold discounts are **rate fences**, not a smooth curve, and the market
treats them that way. Airbnb's own defaults — 10% weekly, 20% monthly — cliff by
the same 10 points at the monthly line that these tiers do, just at one fewer
threshold. So the tiers here step on purpose. Under the defaults (the
`Standard` type), in Normal season with a Monday check-in:

| Nights | Tier | Net |
| ---: | ---: | ---: |
| 13 | 10% | 6,030,000 |
| 14 | 20% | 5,760,000 |
| 27 | 20% | 11,120,000 |
| 28 | 30% | 10,080,000 |

Crossing 14 costs 270,000; crossing 28 costs 1,040,000. The tool **warns** when
a quote sits just below a threshold (§4.5) so the owner sees the exposure and
decides, rather than silently pricing against it.

Depth is bounded by what a longer stay actually saves. Holding
revenue-per-calendar-night constant with `preparation_days = 1`, and taking a
3-night stay as the reference, the turnover-justified discount is 14.3% at 7
nights, 19.6% at 14, 22.3% at 28, with a 25% asymptote. The 28-night tier sits
above that because a property with several units can carry a long stay in one
unit while the rest stay open to short bookings — the extra depth buys occupancy
certainty, not turnover savings. The floor (§4.2) is what stops it going
further. A type with only one or two units has far less of that slack, which is
the case for giving it a shallower ladder of its own (§3).

---

## 4. Pricing rules

### 4.1 Nightly rate

```text
night_rate(T, D) = round_inc(T.base_nightly_rate × M × W)

T = the unit type being priced
M = special date multiplier if D is in a special date, else D's season multiplier
W = weekend.multiplier if D's weekday is in weekend.nights, else 1

min_stay(D) = special date min_stay if set, else D's season min_stay
ota_rate(T, D) = ceil_inc(night_rate(T, D) / K)

K = 1 − (ota_host_fee_pct + tax_pct)/100             if ota_tax_base = "gross"
K = (1 − ota_host_fee_pct/100) × (1 − tax_pct/100)   if ota_tax_base = "payout"
```

Only the base rate depends on the type; `M`, `W` and the minimum stay are the
same for every type. A special date replaces the season. The weekend multiplier still applies on top.
The calendar shows these exact rates, and quotes sum them, so the calendar and
quotes always agree.

The OTA rate is the price that leaves the same money in hand as a direct
booking, so it grosses up for **both** deductions a channel booking carries: the
commission, and the PBJT still owed on a stay where the guest never saw a tax
line (§5.2). At the defaults (`"gross"`) K is 0.745, not 0.845 — a High weekday
night worth 600,000 direct needs 810,000 on the channel, not 710,000. Under
`"payout"` the tax falls on the 84.5% left after commission, so K is
0.845 × 0.90 = 0.7605 and the same night needs 790,000. Ignoring the tax
altogether would price it at 710,000 and leave about 540,000 in hand. It rounds
**up**, so neither deduction eats into the direct-booking equivalent.

### 4.2 Stay price

| # | Step | Formula | Notes |
| --- | --- | --- | --- |
| 1 | Gross | `p = Σ night_rate(T, D)` over the stay's nights | |
| 2 | Discount | `d = los_pct > 0 ? los_pct : lm_pct`, `p = round(p × (1 − d/100))` | `los_pct` comes from T's LOS ladder. `lm_pct` is 0 if last-minute is disabled or this is an extension. LOS takes priority even when last-minute is deeper (§3). An extension counts **only its own nights** for the LOS tier, not the stay so far |
| 3 | Round | `p = round_inc(p)` | |
| 4 | Floor | `net = max(p, stay_floor)` | see below |
| 5 | PBJT | `tax = round(net × tax_pct/100)` | |
| 6 | Guest total | `net + tax` | |

**An extension earns no discount of its own.** The flag changes two things and
no price directly: last-minute is suppressed (a guest already in the room is not
a late booking worth buying), and the preparation day is not counted twice
(§4.4). The length tier on the extension's own nights is the whole of what a
returning guest gets. So an extension never prices below the same nights booked
outright, and splitting a long stay into extensions never beats booking it
whole — 14 + 14 as an extension takes 20% twice, against 30% for 28 nights in
one booking.

```text
stay_floor = ceil_inc( Σ max(T.floor_nightly_rate,
                             round_inc(night_rate(T, D) × floor_pct_of_rate/100)) )
```

The floor has two halves and takes whichever is higher per night. The **absolute**
half (the type's `floor_nightly_rate`) is the never-below-this line and binds in
Low season. The **relative** half (`floor_pct_of_rate`, shared) keeps protection
proportional in High and Peak, where a flat rupiah floor would sit far below any
rate worth defending. For the default `Standard` type:

| | Rate | Floor |
| --- | ---: | ---: |
| Low weekday | 450,000 | 350,000 |
| Normal weekday | 500,000 | 350,000 |
| High weekday | 600,000 | 390,000 |
| Peak weekday | 650,000 | 420,000 |
| Peak weekend | 720,000 | 470,000 |

Because the deepest default LOS tier (30%) is shallower than the relative floor
(35% off), the floor does not clip the tiers — not even at the bottom of the
negotiation range, where 30% and a further 5% still come to 33.5% off. It binds
only in Low season, where the absolute half takes over, and on anything deeper
someone configures later, including a type's own ladder (§5.3 warns).

### 4.3 Negotiation range (pre-tax)

| | Formula |
| --- | --- |
| Ask | `round_inc(net × (1 + ask_buffer_pct/100))` |
| Target | `net` |
| Floor | `max(round_inc(net × (1 − max_discount_pct/100)), stay_floor)` |

Show tax and guest total for each of the three. For long stays, raising
`max_discount_pct` is what opens room down to the floor.

### 4.4 Metrics

| Metric | Formula |
| --- | --- |
| Effective nightly rate | `round(net / nights)` |
| Total discount | `round((1 − net / gross) × 100)` %, shown next to the breakdown |
| 30-night run-rate | `round(net / nights × 30)` — this stay's rate projected across 30 nights, **not** a 30-night quote, which would take the monthly tier and price well below it |
| Inventory consumed | `nights + preparation_days` (extension: `nights`, since the prep day just moves to the end) |
| Revenue per calendar night | `round(net / inventory_consumed)` |

### 4.5 Warnings and errors

- **Warnings** (the quote is still shown):
  - nights < `min_stay` of **any** night in the stay — name the night and its
    season or special date, not just the check-in night;
  - floor applied (show the amount it added);
  - **below a LOS threshold**: the stay is within 4 nights of the next
    `min_nights` in the type's LOS ladder and that tier would price it lower. The 4 is a fixed constant,
    deliberately not configurable — it is the width of a nudge a guest will
    accept, not a pricing input. Show both totals and the difference, so the
    owner can hold the line or offer the longer stay deliberately.
- **Errors** (no quote): missing dates; checkout ≤ check-in; booking date after
  check-in; unknown unit type.

---

## 5. Views

One page with three tabs.

### 5.1 Quote

- **Inputs:** unit type (default the first; hidden when there is only one),
  check-in, checkout, booking date (default today), "Extension of current stay"
  checkbox.
- **Outputs:** the steps from §4.2, showing which discount applied at step 2 and
  the one it overrode, if any; the negotiation table (§4.3); metrics (§4.4), with total discount
  next to the breakdown; warnings. Per-night rates in a collapsible table (date,
  weekday, season/special name, rate).

### 5.2 Calendar

- **Inputs:** from / to dates (default today → +90 days, max 1 year).
- **Rows:** date, weekday, season or special-date name, multiplier, weekend
  (yes/no), then a nightly rate and an OTA rate for **each** unit type, headed
  by the type's name, then minimum stay. One table shows every type side by
  side, since only the rates differ between them.
- **Channel summary:** a copyable plain-text block below the table, with one
  section per unit type listing its nightly rate per season and special date and
  its LOS ladder, followed by the shared last-minute tiers, minimum stays,
  preparation days, and tax rate — for typing into Airbnb by hand. Each type
  maps to its own listing (Airbnb) or room type (Booking.com), so a type's own
  ladder exports as-is. Rates in the summary are OTA rates and are **not**
  pre-discounted: the channel applies the exported LOS and last-minute rules
  itself. The last-minute tiers are listed only when `last_minute.enabled` is
  on; otherwise the block states that last-minute is off, so a discount already
  set on the channel gets switched off rather than left running against quotes
  that never take it.

The default ladder's three tiers are all exportable, as is any per-type ladder
on the same thresholds. Airbnb's weekly discount covers thresholds
from one up to three weeks and its monthly covers four up to twelve, and
Booking.com accepts arbitrary minimum-stay rate plans (or LOS-based pricing over
connectivity), so 7 / 14 / 28 all fit.

Airbnb picks one discount per stay by fixed priority — new-listing → custom
promotion → length-of-stay → early-bird → last-minute — and §4.2 follows the
same LOS-before-last-minute order on purpose, so the exported rules reproduce a
direct quote's discount rather than approximating it. That keeps the §4.1 promise
that an OTA booking leaves the same money in hand.

One mismatch does remain, and it belongs in the block itself because the tool
cannot enforce it:

- **The floor cannot be exported.** A channel that stacks its own promotions on
  top of the exported tiers can land below a type's `floor_nightly_rate`; check the
  resulting payout before enabling promotions there.

On PBJT: the tax is owed by the accommodation operator, not the platform, and
Airbnb does not remit it in Indonesia — so an OTA booking still owes PBJT even
though the guest never saw it as a line item. `ota_rate` grosses up for it
at `tax_pct` on the base `ota_tax_base` names (§4.1). The base is the amount
paid to the accommodation provider, and the perda language does not say plainly
whether the channel's commission sits inside or outside that base — so confirm
the treatment and the rate with the local bapenda, and switch `ota_tax_base` to
`"payout"` if the answer is that only the payout is taxable. Rates are set per
kabupaten/kota up to a 10% cap.

### 5.3 Settings

- A form for every field in §3. Unit types are a list you can add to, rename
  and remove; each has an "Own LOS tiers" toggle that, when switched on, starts
  from a copy of the top-level ladder. Valid changes save automatically to
  `localStorage` under the key `pricing-calculator/config/v1`, except while a
  link config is active (§6).
- **Copy settings link** puts the current settings in a URL (§6). **Copy quote
  link** does the same with the Quote tab's inputs included.
- A raw JSON textarea, for reading or pasting the whole config as a backup.
- **Reset to defaults.**
- **Errors** (an invalid config isn't saved; the other tabs keep using the last
  valid one):
  - overlapping special dates; start after end; an unparseable date;
  - multiplier ≤ 0; percentage outside 0–100;
  - `ota_tax_base` not `"gross"` or `"payout"`;
  - K in §4.1 ≤ 0, which divides by zero or goes negative:
    `ota_host_fee_pct + tax_pct` ≥ 100 under `"gross"`, or either one = 100
    under `"payout"`;
  - `rounding_increment` ≤ 0 (breaks every rounding helper);
  - `unit_types` empty; a type with an empty or duplicate name;
  - a type's `floor_nightly_rate` > its `base_nightly_rate` (every stay floors);
  - `seasons` empty; `month_seasons` not exactly 12 entries; a month mapped to
    an unknown season;
  - duplicate tier thresholds, in the top-level ladder or any type's;
  - a ladder — top-level or a type's — that runs backwards: `discount_pct` must not decrease as
    `min_nights` rises, and must not increase as `max_lead_days` rises. Either
    inversion prices a 14-night stay above a 13-night one — the failure §3.1
    exists to rule out, as distinct from the deliberate cliffs it defends.
- **Warnings** (saved, but flagged):
  - a special date whose `end` is in the past — it silently stops applying;
  - a LOS tier, in any ladder, deeper than `floor_pct_of_rate` allows, which
    the floor would clip to nothing — name the type when it's a type's own
    ladder;
  - with `last_minute.enabled` on, a last-minute tier deeper than the shortest
    tier of any LOS ladder. Priority (§3) then drops the discount as a stay
    crosses that threshold, so the added night prices above its own rate: in
    Normal season with a Monday check-in booked the day before, 6 nights at 15%
    come to 2,640,000 and 7 nights at 10% to 3,240,000 — 600,000 for a 500,000
    night. Name both tiers, and the type when it's a type's own ladder.

There is deliberately **no warning for a longer stay costing less than a shorter
one** (§3.1). The tiers are fences; the per-quote threshold warning in §4.5 is
where that surfaces.

---

## 6. Settings in the URL

```text
https://…/tools/pricing-calculator.html#s=<base64url payload>
```

- **Payload**: `{ "c": <config>, "q": <quote inputs, optional> }`, minified JSON,
  encoded UTF-8 → base64url (`+/` → `-_`, no `=` padding). Use
  `TextEncoder`/`TextDecoder` around `btoa`/`atob`; plain `btoa` fails on
  non-ASCII names.
- **In the fragment, not the query**, so it never reaches the server.
- **Opening a link never overwrites saved settings.** A link's config lives in
  memory for that visit only. While it is active, auto-save is off entirely —
  including edits made in the Settings form — and a banner offers **Save these
  settings** or **Keep mine**. **Save these settings** is the only path from a
  link config to `localStorage`, and it writes the config as currently edited.
  **Keep mine** discards it and reloads the saved settings. Either choice
  dismisses the banner and restores auto-save; until then the banner stays.
- Quote inputs name the unit type by its `name`.
- A payload that won't decode, won't parse, fails validation (§5.3), carries
  an unknown `version`, or names a unit type its config doesn't have shows an
  error banner, and the tool falls back to saved settings.
- Default settings encode to about 1,400 characters; each extra unit type adds
  roughly 100, or 260 with its own ladder. If a link exceeds about 8,000
  characters, warn that some browsers and chat apps may truncate it.

---

## 7. Implementation notes

- Follow the repo rules: one file, inline CSS/JS, no dependencies, the template's
  styles.
- Pricing engine as pure functions with no DOM access:
  `nightRate(config, typeName, date)`, `quote(config, input)` (the input carries
  the type name), `validateConfig(config)`, `encodeSettings` /
  `decodeSettings`. Resolve a type's LOS ladder in one helper,
  `losTiers(config, typeName)`, so no other code checks for the override. The
  UI only calls them.
- Handle dates as `YYYY-MM-DD` using UTC date arithmetic to avoid timezone
  off-by-one errors.
- Round to whole rupiah after every multiplication (§4.2) so results don't drift
  from floating-point error. Implement `round_inc` / `ceil_inc` as integer
  arithmetic on `x / increment`, not on scaled floats.
- The examples in §8 are the acceptance tests: `quote()` must reproduce them
  exactly. Ship them as a self-check the file runs on itself: opening the tool
  at `#selftest` runs all seven against `quote()` and renders pass/fail in place
  of the normal UI. No dependencies, no build step, and the examples cannot rot
  unnoticed.

---

## 8. Worked examples (acceptance tests)

All use the defaults from §3 — the single `Standard` type, with
`last_minute.enabled` `false`. Two examples change one thing, and are marked as
such: Example B switches last-minute on, and Example G adds a second type with
its own LOS ladder.

### A. Month crossing, weekend, LOS

Booked 2026-09-01 · check-in Fri 2026-09-25 · checkout Fri 2026-10-02 · 7 nights

| Step | Calculation | Result |
| --- | --- | ---: |
| Gross | Fri–Sat High+weekend 2 × 660,000 + Sun–Wed High 4 × 600,000 + Thu 1 Oct Normal 500,000 | 4,220,000 |
| Discount | LOS 7 nights → 10% (last-minute off) | 3,798,000 |
| Round | | 3,800,000 |
| Floor (2,770,000) | not binding | **3,800,000** |
| PBJT | | 380,000 |
| Guest total | | **4,180,000** |

| | Pre-tax | PBJT | Total |
| --- | ---: | ---: | ---: |
| Ask | 3,990,000 | 399,000 | 4,389,000 |
| Target | 3,800,000 | 380,000 | 4,180,000 |
| Floor | 3,610,000 | 361,000 | 3,971,000 |

Total discount 10% · effective nightly 542,857 · 30-night run-rate 16,285,714 ·
inventory consumed 8 · revenue per calendar night 475,000 · no warnings (min stay 3).

### B. Last-minute, below minimum stay

Booked Fri 2026-09-11 · check-in Sat 2026-09-12 · checkout Mon 2026-09-14 · 2 nights
· `last_minute.enabled` = `true`

| Step | Calculation | Result |
| --- | --- | ---: |
| Gross | Sat High+weekend 660,000 + Sun High 600,000 | 1,260,000 |
| Discount | LOS 2 nights → no tier, so last-minute 1 day → 15% | 1,071,000 |
| Round | | 1,070,000 |
| Floor (820,000) | not binding | **1,070,000** |
| PBJT | | 107,000 |
| Guest total | | **1,177,000** |

| | Pre-tax | PBJT | Total |
| --- | ---: | ---: | ---: |
| Ask | 1,120,000 | 112,000 | 1,232,000 |
| Target | 1,070,000 | 107,000 | 1,177,000 |
| Floor | 1,020,000 | 102,000 | 1,122,000 |

Total discount 15% · effective nightly 535,000 · 30-night run-rate 16,050,000 ·
inventory consumed 3 · revenue per calendar night 356,667 ·
**warning: below minimum stay (High, 3 nights)**.

### C. Long stay, floor binds

Booked Sat 2026-10-31 · check-in Sun 2026-11-01 · checkout Tue 2026-12-01 · 30 nights, all Low

| Step | Calculation | Result |
| --- | --- | ---: |
| Gross | 22 weekday × 450,000 + 8 weekend × 500,000 (495,000 rounded half up) | 13,900,000 |
| Discount | LOS 30 nights → 30% (last-minute off) | 9,730,000 |
| Round | | 9,730,000 |
| Floor (30 × 350,000, absolute half) | **binding**, +770,000 | **10,500,000** |
| PBJT | | 1,050,000 |
| Guest total | | **11,550,000** |

| | Pre-tax | PBJT | Total |
| --- | ---: | ---: | ---: |
| Ask | 11,030,000 | 1,103,000 | 12,133,000 |
| Target | 10,500,000 | 1,050,000 | 11,550,000 |
| Floor | 10,500,000 | 1,050,000 | 11,550,000 |

Total discount 24% · effective nightly 350,000 · 30-night run-rate 10,500,000 ·
inventory consumed 31 · revenue per calendar night 338,710 ·
**warning: floor applied (+770,000)**.

The relative half of the floor would give 9,020,000 here; the absolute half wins
in Low season, and caps the realised discount at 24% against the 30% tier.

### D. Extension of C

Booked 2026-11-28 · check-in Tue 2026-12-01 · checkout Tue 2026-12-15 · 14 nights, all High · extension

| Step | Calculation | Result |
| --- | --- | ---: |
| Gross | 10 weekday × 600,000 + 4 weekend × 660,000 | 8,640,000 |
| Discount | LOS 14 nights → 20% (the 30 nights already stayed don't count; last-minute skipped for extensions) | 6,912,000 |
| Round | | 6,910,000 |
| Floor (5,620,000) | not binding | **6,910,000** |
| PBJT | | 691,000 |
| Guest total | | **7,601,000** |

| | Pre-tax | PBJT | Total |
| --- | ---: | ---: | ---: |
| Ask | 7,260,000 | 726,000 | 7,986,000 |
| Target | 6,910,000 | 691,000 | 7,601,000 |
| Floor | 6,560,000 | 656,000 | 7,216,000 |

Total discount 20% · effective nightly 493,571 · 30-night run-rate 14,807,143 ·
inventory consumed 14 · revenue per calendar night 493,571 · no warnings.

The extension flag earns the guest nothing here beyond the 14-night tier their
own nights qualify for, and its last-minute suppression does not bind either:
a stay that reaches a LOS tier never looks at last-minute (§3), so the 3-day
lead time's 10% was never in play. Suppression bites only on extensions too
short for any LOS tier — three more nights booked the day
before would otherwise take 15% off for a guest who was never going anywhere.

### E. Calendar around a special date

| Date | Label | Multiplier | Weekend | Rate | OTA rate | Min stay |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| Sat 2026-12-19 | High | 1.20 | yes | 660,000 | 890,000 | 3 |
| Sun 2026-12-20 | Christmas & New Year | 1.40 | no | 700,000 | 940,000 | 5 |
| Fri 2026-12-25 | Christmas & New Year | 1.40 | yes | 770,000 | 1,040,000 | 5 |
| Tue 2027-01-05 | Christmas & New Year | 1.40 | no | 700,000 | 940,000 | 5 |
| Wed 2027-01-06 | High | 1.20 | no | 600,000 | 810,000 | 3 |

OTA rates divide by K = 1 − (15.5 + 10)/100 = 0.745 (`ota_tax_base` `"gross"`)
and round up (§4.1).

### F. Threshold warning

Booked 2026-01-15 · check-in Mon 2026-04-06 · checkout Sun 2026-05-03 · 27 nights, all Normal

27 nights takes the 14-night tier at 20% → 11,120,000. At 28 nights the monthly
tier gives 10,080,000. **Warning: 28 nights would price at 10,080,000, 1,040,000
below this quote.** The quote itself is unchanged.

### G. Second unit type with its own LOS ladder

Example A's stay, priced for an added type. The `Standard` type stays in the
config unchanged:

```json
{ "name": "Deluxe", "base_nightly_rate": 600000, "floor_nightly_rate": 400000,
  "los_tiers": [
    { "min_nights": 7,  "discount_pct": 5 },
    { "min_nights": 14, "discount_pct": 15 },
    { "min_nights": 28, "discount_pct": 25 }
  ] }
```

Booked 2026-09-01 · check-in Fri 2026-09-25 · checkout Fri 2026-10-02 · 7 nights · Deluxe

| Step | Calculation | Result |
| --- | --- | ---: |
| Gross | Fri–Sat High+weekend 2 × 790,000 (792,000 rounded) + Sun–Wed High 4 × 720,000 + Thu 1 Oct Normal 600,000 | 5,060,000 |
| Discount | Deluxe LOS 7 nights → 5% (last-minute off) | 4,807,000 |
| Round | | 4,810,000 |
| Floor (3,300,000) | not binding | **4,810,000** |
| PBJT | | 481,000 |
| Guest total | | **5,291,000** |

| | Pre-tax | PBJT | Total |
| --- | ---: | ---: | ---: |
| Ask | 5,050,000 | 505,000 | 5,555,000 |
| Target | 4,810,000 | 481,000 | 5,291,000 |
| Floor | 4,570,000 | 457,000 | 5,027,000 |

Total discount 5% · effective nightly 687,143 · 30-night run-rate 20,614,286 ·
inventory consumed 8 · revenue per calendar night 601,250 · no warnings.

The floor is 2 × 510,000 + 4 × 470,000 + 400,000: the relative half wins on the
High nights, and the type's own 400,000 absolute half wins on the Normal night,
where 65% gives only 390,000. The 5% tier replaces the top-level 10% rather than
adding to it; the same stay as `Standard` is still Example A.

---

## 9. Deliberately not included

- **Stored bookings, availability states, occupancy and ALOS analytics.** The
  channel calendars already own availability. Preparation days survive only as
  the inventory-consumed metric.
- **Per-unit pricing.** Units of the same type share one rate. Deciding which
  unit absorbs a long stay is an allocation question the calendar owns, not a
  pricing one.
- **Other per-type overrides.** A type sets its base rate, its floor and
  optionally its LOS ladder — the three that move together when a unit is
  bigger or smaller. Seasons, special dates, minimum stays, weekend,
  last-minute, negotiation, tax and OTA settings are shared. If a type ever
  needs one of those, it gets an optional override the same way `los_tiers`
  does: replace, don't merge, resolved in one helper.
- **Season-specific LOS depth.** One ladder, every season — a deliberate
  deviation from the market rather than a reproduction of it, and worth stating
  plainly because it runs the other way. The market discounts a month 35–40%
  off-peak and 20–25% in peak, where the common advice is to hold list price
  outright on dates that historically sell out. This design does the reverse:
  Low season realises only 24% against the 30% tier, because the absolute floor
  binds (Example C), while Peak realises the full 30%. That is accepted on
  purpose. On a property with few units, a long Low-season stay ties up
  inventory worth keeping loose, and the floor is the instrument that says so. If Low season starts
  going empty, the fix is a per-season multiplier on tier depth — one field, one
  multiplication in §4.2 step 2 — not a deeper flat ladder.
- **An extension discount.** Cut. A returning guest gets the length tier their
  extension's own nights qualify for and nothing beyond it (§4.2); 3% off was
  inside the rounding-and-negotiation noise and cost a compounding step, a
  special case and an acceptance test to carry. The flag survives only to
  suppress last-minute and to stop the preparation day being counted twice.
- **A separate commitment discount.** The 28-night tier is the commitment
  discount; a stay long enough to want more is priced by the floor and the
  negotiation range.
- Cleaning and extra-guest fees, deposits,
  cancellations, tax-inclusive (reverse) calculations, per-booking OTA quotes.
