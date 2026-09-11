# Guesthouse Pricing Calculator — PRD

## 1. Objective

Build a pricing calculator for a small guesthouse that supports:

* Nightly, weekly, monthly, and long-term stays
* Seasonal pricing
* Direct and OTA channels
* Rolling monthly extensions
* Long-term commitments
* Last-minute discounts
* Guest negotiation ranges
* PBJT/tax
* One-day preparation time between bookings
* Pricing calendar generation
* Airbnb pricing/configuration guidance

The system should keep all pricing rules configurable.

---

## 2. Core Pricing Principle

Pricing is calculated in layers:

```text
Base Rate
→ Seasonal / Date Adjustments
→ Length-of-Stay Discount
→ Booking-Time Discount
→ Commitment / Renewal Discount
→ Price Floor
→ Negotiation / Channel Adjustment
→ Tax
→ Guest Price
```

Availability and preparation days are calculated separately from pricing.

---

# 3. Configuration

## 3.1 Base Settings

```text
base_nightly_rate
minimum_nightly_rate
minimum_monthly_rate
currency
rounding_increment
```

Example:

```text
currency = IDR
rounding_increment = 50,000
```

---

## 3.2 Monthly Season Multipliers

Each month has a multiplier.

```text
January   1.10
February  0.90
March     0.90
...
August    1.30
```

Daily seasonal price:

```text
seasonal_rate
= base_nightly_rate × season_multiplier
```

---

## 3.3 Special Date Overrides

Allow custom date ranges:

```text
start_date
end_date
multiplier
name
```

Example:

```text
20 Dec – 5 Jan
multiplier = 1.40
```

Special-date multiplier overrides the monthly multiplier.

---

## 3.4 Optional Weekend Adjustment

```text
weekend_multiplier
weekend_days
```

Example:

```text
Friday/Saturday = +5%
```

---

# 4. Gross Stay Value

Calculate each night independently.

```text
night_rate
=
base_nightly_rate
× applicable_season_multiplier
× weekend_multiplier
```

Then:

```text
gross_stay_value
= SUM(all night rates)
```

A reservation crossing months must use the appropriate rate for each date.

---

# 5. Length-of-Stay Discounts

Configurable discount tiers.

Example:

| Nights | Discount |
| ------ | -------: |
| 1–6    |       0% |
| 7–13   |       5% |
| 14–27  |      10% |
| 28+    |      20% |

```text
price_after_los
=
gross_stay_value
× (1 - los_discount)
```

---

# 6. Last-Minute Discounts

Configurable based on:

```text
lead_time_days
= checkin_date - booking_date
```

Example:

| Lead time | Discount |
| --------- | -------: |
| 15+ days  |       0% |
| 8–14 days |       5% |
| 2–7 days  |      10% |
| 0–1 day   |      15% |

```text
price_after_booking_time
=
price_after_los
× (1 - last_minute_discount)
```

Last-minute discount can be enabled/disabled per channel or booking type.

Default behavior:

```text
standard/direct stay   enabled
OTA                     configurable
long-term commitment    disabled
```

---

# 7. Commitment Pricing

Commitment is different from payment frequency.

Example:

```text
6-month contract paid monthly
= 6-month commitment
```

Possible commitment tiers:

| Commitment | Extra Discount |
| ---------- | -------------: |
| <3 months  |             0% |
| 3 months   |             3% |
| 6 months   |             5% |
| 12 months  |             8% |

For committed stays:

```text
contract_price
=
seasonal value of entire period
× LOS discount
× commitment discount
```

Fixed monthly payment:

```text
monthly_payment
=
contract_price / contract_months
```

The monthly payment stays fixed during the committed contract.

---

# 8. Rolling Monthly Extensions

If the guest has no future commitment:

```text
extension = new pricing calculation
```

Use:

* Seasonal value of extension dates
* LOS discount
* No commitment discount
* Optional renewal discount

Previous pricing must NOT automatically continue.

Future dates remain available until extension is confirmed.

---

# 9. Existing Guest Renewal Discount

Optional configurable discount.

Example:

```text
renewal_discount = 3%
```

Used for rolling extensions.

```text
extension_price
=
calculated_extension_price
× (1 - renewal_discount)
```

A new multi-month commitment should use commitment pricing instead.

---

# 10. Economic Price Floor

Pricing must never fall below the configured minimum.

```text
calculated_net_price
=
MAX(
  discounted_price,
  applicable_price_floor
)
```

Support:

```text
minimum_nightly_rate
minimum_monthly_rate
```

Price floor applies before tax.

---

# 11. Guest Negotiation Range

For direct bookings, calculate:

```text
ask_price
target_price
negotiation_floor
economic_floor
```

Configuration:

```text
negotiation_ask_buffer_percent
negotiation_max_discount_percent
```

Example:

```text
target = 11,000,000
ask buffer = 5%
max negotiation discount = 5%

ask = 11,550,000
negotiation floor = 10,450,000
```

Final floor:

```text
final_negotiation_floor
=
MAX(
  calculated_negotiation_floor,
  economic_floor
)
```

Tax is calculated after negotiation.

---

# 12. Tax / PBJT

Tax must be configurable.

Current property default:

```text
tax_rate = 10%
```

Support:

```text
tax_mode:
- exclusive
- inclusive
```

### Tax Exclusive

```text
tax = accommodation_price × tax_rate

guest_total
= accommodation_price + tax
```

### Tax Inclusive

```text
accommodation_price
=
guest_total / (1 + tax_rate)

tax
=
guest_total - accommodation_price
```

All profitability and price-floor calculations use the **pre-tax accommodation value**.

---

# 13. OTA / Channel Pricing

Do not use one generic multiplier only.

Channel configuration:

```text
channel_name
host_fee_percent
price_adjustment_percent
tax_mode
last_minute_enabled
```

Pricing order:

```text
Target Accommodation Revenue
→ OTA Adjustment / Fee Gross-Up
→ OTA Accommodation Price
→ PBJT
→ Guest-Facing Price
```

Example fee gross-up:

```text
ota_accommodation_price
=
desired_host_revenue
/
(1 - host_fee_percent)
```

PBJT is then calculated from the OTA accommodation price.

The calculator must separately display:

```text
Accommodation price
Tax
Guest total
OTA fee
Expected host payout
```

---

# 14. Preparation Time

Current property rule:

```text
preparation_days = 1
```

If a guest checks out today:

```text
today = preparation/block day
earliest next check-in = tomorrow
```

Preparation days consume inventory but generate no guest revenue.

---

# 15. Occupancy Metrics

Track both:

## Calendar Occupancy

```text
occupied_nights
/
total_calendar_room_nights
```

## Sellable Occupancy

```text
occupied_nights
/
(
  calendar_room_nights
  - preparation_nights
  - maintenance_blocks
  - owner_blocks
)
```

Both must be displayed.

---

## 15.1 Maximum Occupancy From Preparation Time

Approximation:

```text
max_calendar_occupancy
=
average_length_of_stay
/
(
  average_length_of_stay
  + preparation_days
)
```

Example:

```text
ALOS = 7
prep = 1

max ≈ 87.5%
```

---

## 15.2 Expected Occupancy

Given:

```text
target_sellable_occupancy
average_length_of_stay
preparation_days
```

Approximate expected calendar occupancy:

```text
expected_calendar_occupancy
=
(target_sellable_occupancy × ALOS)
/
(ALOS + target_sellable_occupancy × preparation_days)
```

---

# 16. Booking Efficiency

For each reservation calculate:

```text
inventory_consumed
=
stay_nights + preparation_days
```

And:

```text
effective_revenue_per_calendar_night
=
net_accommodation_revenue
/
inventory_consumed
```

This metric is important when comparing short and long stays.

---

# 17. Minimum Stay

Support configurable minimum stay.

Example:

```text
normal season   2 nights
high season     3 nights
peak season     3 nights
```

Optional last-minute rule:

```text
reduce minimum stay as arrival approaches
```

---

# 18. Main Application Views

## A. Reservation Calculator

Inputs:

```text
booking_date
checkin_date
checkout_date
channel
booking_type
commitment_months
existing_guest
renewal_discount_enabled
```

Outputs:

```text
nights
gross seasonal value
LOS discount
last-minute discount
commitment discount
renewal discount
net accommodation price
tax
guest total
effective nightly rate
inventory consumed
effective revenue/calendar night
```

---

## B. Pricing Calendar

Generate daily pricing for a configurable date range.

Each date should show:

```text
date
base rate
season
season multiplier
special-date adjustment
weekend adjustment
suggested nightly rate
minimum stay
availability state
```

Availability states:

```text
available
booked
preparation
maintenance
owner_block
unavailable
```

---

## C. Channel Configuration Summary

Generate settings that can be copied manually into Airbnb or another OTA.

Example:

```text
MONTHLY BASE / SEASON PRICING
Jan ...
Feb ...
...

LOS DISCOUNTS
7+ nights      -5%
14+ nights     -10%
28+ nights     -20%

LAST MINUTE
8–14 days      -5%
2–7 days       -10%
0–1 day        -15%

MINIMUM STAY
Normal          2 nights
Peak            3 nights

PREPARATION
1 day

TAX
PBJT            10%
```

---

# 19. Booking Types

Support:

```text
STANDARD
ROLLING_MONTHLY
LONG_TERM_COMMITTED
EXTENSION
```

Rules:

| Type                | LOS | Last Minute   | Commitment          | Renewal  |
| ------------------- | --- | ------------- | ------------------- | -------- |
| Standard            | Yes | Yes           | No                  | No       |
| Rolling Monthly     | Yes | Optional      | No                  | Optional |
| Long-Term Committed | Yes | No by default | Yes                 | No       |
| Extension           | Yes | Optional      | Only new commitment | Optional |

---

# 20. Calculation Sequence

```text
1. Determine reservation dates

2. Calculate each nightly base value

3. Apply season / special date / weekend rules

4. Sum → Gross Stay Value

5. Apply LOS discount

6. Apply booking-time discount

7. Apply commitment discount

8. Apply renewal discount

9. Enforce economic price floor

10. Determine:
    Ask / Target / Negotiation Floor

11. Apply channel economics

12. Calculate PBJT

13. Calculate guest-facing total

14. Calculate preparation inventory impact

15. Return pricing + occupancy metrics
```

---

# 21. Key Business Rules

1. **Seasonality follows each occupied date**, not the reservation start month.
2. **LOS discount rewards longer stays.**
3. **Commitment discount rewards guaranteed future occupancy.**
4. Paying monthly does not mean monthly commitment.
5. Rolling extensions are repriced using new dates.
6. Old contract prices do not automatically carry into extensions.
7. Negotiation happens on the pre-tax accommodation price.
8. PBJT is separate from room revenue.
9. OTA price must account for channel economics separately from tax.
10. No calculated price may fall below the economic floor.
11. One preparation day is automatically blocked after checkout.
12. Preparation days affect occupancy and reservation economics.
13. Display both calendar occupancy and sellable occupancy.
14. Long stays should be evaluated partly through revenue per consumed calendar night.
15. All percentages and thresholds must be configurable rather than hard-coded.
16. OTA service fees must not be calculated on custom/pass-through taxes unless the channel's documented fee rules explicitly require it. For Airbnb Custom Tax, PBJT is excluded from the Airbnb service-fee base and handled as a separate tax amount.

---

# 22. Implementation Priority

### MVP

Implement:

```text
Base rate
Monthly seasonality
Special dates
LOS discounts
Last-minute discounts
Direct booking
PBJT
Negotiation range
Price floor
Preparation days
Reservation calculator
Pricing calendar
```

### Phase 2

Add:

```text
Committed long-term pricing
Rolling extension workflow
Renewal discounts
OTA fee gross-up
Channel configuration summary
Occupancy analytics
ALOS analysis
Minimum-stay optimization
```

The implementation should keep the pricing engine independent from the UI so the same engine can later power Excel exports, an HTML calculator, or a full PMS.
