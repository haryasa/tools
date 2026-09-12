# Guesthouse Pricing Calculator — PRD

## 1. Goal

A single-file HTML tool, `tools/pricing-calculator.html`, for a **one-unit**
guesthouse. It lets the owner:

1. **Quote** a direct booking: price breakdown, negotiation range, PBJT, guest total.
2. **View a price calendar**: nightly rate, minimum stay, and OTA rate for a date range.
3. **Edit the pricing rules** without touching code, and share them as a link.

All amounts are IDR, whole rupiah. Everything ships in one phase; §9 lists what
is deliberately left out.

---

## 2. Definitions

| Term | Meaning |
| --- | --- |
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
  "base_nightly_rate": 500000,
  "floor_nightly_rate": 350000,
  "rounding_increment": 10000,
  "tax_pct": 10,
  "preparation_days": 1,
  "ota_host_fee_pct": 15,

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
    { "min_nights": 7,  "discount_pct": 8 },
    { "min_nights": 14, "discount_pct": 14 },
    { "min_nights": 21, "discount_pct": 18 },
    { "min_nights": 28, "discount_pct": 20 }
  ],

  "last_minute": {
    "enabled": true,
    "tiers": [
      { "max_lead_days": 1,  "discount_pct": 15 },
      { "max_lead_days": 7,  "discount_pct": 10 },
      { "max_lead_days": 14, "discount_pct": 5 }
    ]
  },

  "extension_discount_pct": 3,

  "negotiation": { "ask_buffer_pct": 5, "max_discount_pct": 5 }
}
```

Rules:

- **Seasons**: each month maps to one named season.
- **Special dates** belong to a specific year. `start` and `end` are the first
  and last nights included. `min_stay` is optional; if it's missing, the
  season's value is used. Special dates must not overlap.
- **LOS tier**: the tier with the highest `min_nights` ≤ nights; no match → 0%.
- **Last-minute tier**: the tier with the smallest `max_lead_days` ≥ lead time;
  no match → 0%.

### 3.1 Why the LOS tiers stop at 28 nights

A tier at threshold `t` can only be about `(1 − previous discount) ÷ t` deeper
than the tier before it. Beyond that, a stay one night short of the threshold
costs more than one at the threshold. At 28 nights that headroom is already down
to roughly 0.9%, so tiers like "90 nights, 25%" are not possible without that
inversion. Long stays are priced by the floor and the negotiation range instead
(see Example C), not by deeper tiers.

---

## 4. Pricing rules

### 4.1 Nightly rate

```text
night_rate(D) = round_inc(base_nightly_rate × M × W)

M = special date multiplier if D is in a special date, else D's season multiplier
W = weekend.multiplier if D's weekday is in weekend.nights, else 1

min_stay(D) = special date min_stay if set, else D's season min_stay
ota_rate(D) = ceil_inc(night_rate(D) / (1 − ota_host_fee_pct/100))
```

A special date replaces the season. The weekend multiplier still applies on top.
The calendar shows these exact rates, and quotes sum them, so the calendar and
quotes always agree. The OTA rate rounds **up**, so channel fees never eat into
the direct-booking equivalent.

### 4.2 Stay price

| # | Step | Formula | Notes |
| --- | --- | --- | --- |
| 1 | Gross | Σ `night_rate` over the stay's nights | |
| 2 | LOS discount | `p = round(p × (1 − los_pct/100))` | An extension counts **only its own nights**, not the stay so far |
| 3 | Last-minute | `p = round(p × (1 − lm_pct/100))` | Skipped if disabled or for an extension |
| 4 | Extension discount | `p = round(p × (1 − extension_discount_pct/100))` | Extension only |
| 5 | Round | `p = round_inc(p)` | |
| 6 | Floor | `net = max(p, stay_floor)`, `stay_floor = ceil_inc(nights × floor_nightly_rate)` | |
| 7 | PBJT | `tax = round(net × tax_pct/100)` | |
| 8 | Guest total | `net + tax` | |

Discounts stack with no cap. The floor is the only safeguard.

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
| 30-night equivalent | `round(net / nights × 30)` |
| Inventory consumed | `nights + preparation_days` (extension: `nights`, since the prep day just moves to the end) |
| Revenue per calendar night | `round(net / inventory_consumed)` |

### 4.5 Warnings and errors

- **Warnings** (the quote is still shown): nights < `min_stay` of the check-in
  night; floor applied (show the amount it added).
- **Errors** (no quote): missing dates; checkout ≤ check-in; booking date after
  check-in.

---

## 5. Views

One page with three tabs.

### 5.1 Quote

- **Inputs:** check-in, checkout, booking date (default today), "Extension of
  current stay" checkbox.
- **Outputs:** the steps from §4.2 with the discount % applied at each; the
  negotiation table (§4.3); metrics (§4.4); warnings. Per-night rates in a
  collapsible table (date, weekday, season/special name, rate).

### 5.2 Calendar

- **Inputs:** from / to dates (default today → +90 days, max 1 year).
- **Rows:** date, weekday, season or special-date name, multiplier, weekend
  (yes/no), nightly rate, OTA rate, minimum stay.
- **Channel summary:** a copyable plain-text block below the table, listing the
  nightly rate per season and special date, the LOS tiers, the last-minute
  tiers, the minimum stays, preparation days, and the tax rate — for typing into
  Airbnb by hand. Rates in the summary are OTA rates and are **not**
  pre-discounted: the channel applies the exported LOS and last-minute rules
  itself. Check how the channel treats PBJT in its fee base before relying on
  the payout.

### 5.3 Settings

- A form for every field in §3. Valid changes save automatically to
  `localStorage`.
- **Copy settings link** puts the current settings in a URL (§6). **Copy quote
  link** does the same with the Quote tab's inputs included.
- A raw JSON textarea, for reading or pasting the whole config as a backup.
- **Reset to defaults.**
- **Errors** (an invalid config isn't saved; the other tabs keep using the last
  valid one): overlapping special dates; start after end; multiplier ≤ 0;
  percentage outside 0–100; month mapped to an unknown season; duplicate tier
  thresholds.
- **Warning**: an LOS tier that makes a longer stay cheaper than a shorter one.
  For each tier with threshold `t` and discount `d`, where the previous tier's
  discount is `p`: warn if `(t − 1) × (1 − p) > t × (1 − d)`. This check assumes
  a flat nightly rate. Example: tiers 7+ 5%, 14+ 10%, 28+ 20% warn at 28, because
  27 nights × 0.90 = 24.3 costs more than 28 × 0.80 = 22.4.

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
- **Opening a link never overwrites saved settings.** The link's settings are
  used for that visit, and a banner offers "Save these settings" or "Keep mine".
  The banner stays until it's dismissed.
- A payload that won't decode, won't parse, fails validation (§5.3), or carries
  an unknown `version` shows an error banner, and the tool falls back to saved
  settings.
- Default settings encode to about 1,400 characters. If a link exceeds about 8,000
  characters, warn that some browsers and chat apps may truncate it.

---

## 7. Implementation notes

- Follow the repo rules: one file, inline CSS/JS, no dependencies, the template's
  styles.
- Pricing engine as pure functions with no DOM access: `nightRate(config, date)`,
  `quote(config, input)`, `validateConfig(config)`, `encodeSettings` /
  `decodeSettings`. The UI only calls them.
- Handle dates as `YYYY-MM-DD` using UTC date arithmetic to avoid timezone
  off-by-one errors.
- Round to whole rupiah after every multiplication (§4.2) so results don't drift
  from floating-point error.
- The examples in §8 are the acceptance tests: `quote()` must reproduce them
  exactly.

---

## 8. Worked examples (acceptance tests)

All use the defaults from §3.

### A. Month crossing, weekend, LOS

Booked 2026-09-01 · check-in Fri 2026-09-25 · checkout Fri 2026-10-02 · 7 nights

| Step | Calculation | Result |
| --- | --- | ---: |
| Gross | Fri–Sat High+weekend 2 × 660,000 + Sun–Wed High 4 × 600,000 + Thu 1 Oct Normal 500,000 | 4,220,000 |
| LOS (7 nights → 8%) | × 0.92 | 3,882,400 |
| Last-minute (24 days → 0%) | — | 3,882,400 |
| Round | | 3,880,000 |
| Floor (2,450,000) | not binding | **3,880,000** |
| PBJT | | 388,000 |
| Guest total | | **4,268,000** |

| | Pre-tax | PBJT | Total |
| --- | ---: | ---: | ---: |
| Ask | 4,070,000 | 407,000 | 4,477,000 |
| Target | 3,880,000 | 388,000 | 4,268,000 |
| Floor | 3,690,000 | 369,000 | 4,059,000 |

Effective nightly 554,286 · 30-night equivalent 16,628,571 · inventory consumed 8 ·
revenue per calendar night 485,000 · no warnings (min stay 3).

### B. Last-minute, below minimum stay

Booked Fri 2026-09-11 · check-in Sat 2026-09-12 · checkout Mon 2026-09-14 · 2 nights

| Step | Calculation | Result |
| --- | --- | ---: |
| Gross | Sat High+weekend 660,000 + Sun High 600,000 | 1,260,000 |
| LOS (2 nights → 0%) | — | 1,260,000 |
| Last-minute (1 day → 15%) | × 0.85 | 1,071,000 |
| Round | | 1,070,000 |
| Floor (700,000) | not binding | **1,070,000** |
| PBJT | | 107,000 |
| Guest total | | **1,177,000** |

| | Pre-tax | PBJT | Total |
| --- | ---: | ---: | ---: |
| Ask | 1,120,000 | 112,000 | 1,232,000 |
| Target | 1,070,000 | 107,000 | 1,177,000 |
| Floor | 1,020,000 | 102,000 | 1,122,000 |

Effective nightly 535,000 · 30-night equivalent 16,050,000 · inventory consumed 3 ·
revenue per calendar night 356,667 · **warning: below minimum stay (High, 3 nights)**.

### C. Long stay, floor binds

Booked Sat 2026-10-31 · check-in Sun 2026-11-01 · checkout Tue 2026-12-01 · 30 nights, all Low

| Step | Calculation | Result |
| --- | --- | ---: |
| Gross | 22 weekday × 450,000 + 8 weekend × 500,000 (495,000 rounded half up) | 13,900,000 |
| LOS (30 nights → 20%) | × 0.80 | 11,120,000 |
| Last-minute (1 day → 15%) | × 0.85 | 9,452,000 |
| Round | | 9,450,000 |
| Floor (30 × 350,000) | **binding**, +1,050,000 | **10,500,000** |
| PBJT | | 1,050,000 |
| Guest total | | **11,550,000** |

| | Pre-tax | PBJT | Total |
| --- | ---: | ---: | ---: |
| Ask | 11,030,000 | 1,103,000 | 12,133,000 |
| Target | 10,500,000 | 1,050,000 | 11,550,000 |
| Floor | 10,500,000 | 1,050,000 | 11,550,000 |

Effective nightly 350,000 · 30-night equivalent 10,500,000 · inventory consumed 31 ·
revenue per calendar night 338,710 · **warning: floor applied (+1,050,000)**.

### D. Extension of C

Booked 2026-11-28 · check-in Tue 2026-12-01 · checkout Tue 2026-12-15 · 14 nights, all High · extension

| Step | Calculation | Result |
| --- | --- | ---: |
| Gross | 10 weekday × 600,000 + 4 weekend × 660,000 | 8,640,000 |
| LOS (14 nights → 14%; the 30 nights already stayed don't count) | × 0.86 | 7,430,400 |
| Last-minute | skipped (extension) | 7,430,400 |
| Extension discount (3%) | × 0.97 | 7,207,488 |
| Round | | 7,210,000 |
| Floor (14 × 350,000 = 4,900,000) | not binding | **7,210,000** |
| PBJT | | 721,000 |
| Guest total | | **7,931,000** |

| | Pre-tax | PBJT | Total |
| --- | ---: | ---: | ---: |
| Ask | 7,570,000 | 757,000 | 8,327,000 |
| Target | 7,210,000 | 721,000 | 7,931,000 |
| Floor | 6,850,000 | 685,000 | 7,535,000 |

Effective nightly 515,000 · 30-night equivalent 15,450,000 · inventory consumed 14 ·
revenue per calendar night 515,000 · no warnings.

### E. Calendar around a special date

| Date | Label | Multiplier | Weekend | Rate | OTA rate | Min stay |
| --- | --- | ---: | --- | ---: | ---: | ---: |
| Sat 2026-12-19 | High | 1.20 | yes | 660,000 | 780,000 | 3 |
| Sun 2026-12-20 | Christmas & New Year | 1.40 | no | 700,000 | 830,000 | 5 |
| Fri 2026-12-25 | Christmas & New Year | 1.40 | yes | 770,000 | 910,000 | 5 |
| Tue 2027-01-05 | Christmas & New Year | 1.40 | no | 700,000 | 830,000 | 5 |
| Wed 2027-01-06 | High | 1.20 | no | 600,000 | 710,000 | 3 |

---

## 9. Deliberately not included

- **Stored bookings, availability states, occupancy and ALOS analytics.** The
  channel calendars already own availability. Preparation days survive only as
  the inventory-consumed metric.
- **A separate commitment discount.** Threshold discounts on total stay length
  can't grow much once stays are long (§3.1), so a committed 6-month stay is
  priced by the floor and the negotiation range, not by an extra tier.
- **Multiple units or room types**, cleaning and extra-guest fees, deposits,
  cancellations, tax-inclusive (reverse) calculations, per-booking OTA quotes.
