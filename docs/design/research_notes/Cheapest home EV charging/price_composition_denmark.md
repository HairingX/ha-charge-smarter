# The Danish household price per kWh for home EV charging (DK1/DK2, as of 2026-10-28)

Method note. Every cited finding comes from a page or dataset opened on 2026-10-28. Three kinds of
source are used:

- **Energi Data Service datasets, queried directly through the API.** `DayAheadPrices` for DK1 and
  DK2 from 2025-10-01 to 2026-10-29 (37,828 quarter-hour rows per area). `DatahubPricelist` for
  tariff rows valid from 2025 onwards.
- **Official and consumer pages:** skat.dk, Forbrugerrådet Tænk, FDM, Nord Pool, Norlys press
  releases and Mobilsiden.
- **My own calculations** on the Energi Data Service data, labelled **(own calculation)**. They
  use the following assumptions:
  - Total price = (spot + grid tariff + Energinet tariffs + elafgift) × 1.25 VAT.
  - The supplier markup is set to 0. It is flat per kWh, so it does not change the ranking.
  - DK1 is represented by N1 A/S (grid area 131) "Nettarif C". DK2 is represented by Radius
    "Nettarif C".
  - Subscriptions are ignored because they are fixed per month.

Anything labelled "Reasoning" is inference, not a sourced fact.

## 1. What makes up the Danish household price per kWh in 2026, and which parts vary by hour?

### Takeaway
Spot price and the grid company's time-of-use tariff are the only per-kWh parts that vary within a
day, and the tariff swing (≈0.85 DKK/kWh excl. VAT between night and the 17–21 winter peak) is as
large as the typical daily spot spread. Since the elafgift fell from 0.72 to 0.008 DKK/kWh on
1 January 2026, the flat state part is now small (≈0.12 DKK/kWh excl. VAT), so the variable parts
dominate the price spread.

### Cited Findings
- **Elafgift (electricity tax).**
  - 2026 and 2027: 0.8 øre/kWh (0.008 DKK/kWh), "fra 1. januar 2026 til 31. december 2027", a
    temporary reduction. The EU minimum used for business refunds is 0.4 øre/kWh. —
    [skat.dk](https://skat.dk/erhverv/afgifter-paa-varer-og-ydelser-punktafgifter/nyhedsbrev-afgifter/midlertidig-nedsaettelse-af-elafgiften-i-2026-og-2027)
  - DataHub carries the same figure: elafgift `EA-001` = 0.008 DKK/kWh, valid 2026-01-01 →
    2028-01-01. For 2025 it was 0.72 DKK/kWh. —
    [Energi Data Service, DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist)
  - Before the cut it was 72.7 øre/kWh, and the cut covers all household electricity, EV charging
    included (article of 21 Aug 2025, written before the cut took effect). —
    [Mobilsiden](https://mobilsiden.dk/?p=240988)
  - FDM rounds the same figures to "from about 90 øre to about 1 øre per kWh", including VAT. —
    [FDM, 20 Nov 2025](https://fdm.dk/nyheder/bilist/2025-11-fra-2026-kan-du-tjene-penge-paa-saette-elbilen-til-opladning)
- **Energinet tariffs**, flat all day (DataHub resolution `P1D`):

  | Year | Systemtarif (DKK/kWh) | Transmissions nettarif (DKK/kWh) | Sum (DKK/kWh) |
  |---|---|---|---|
  | 2025 | 0.074 | 0.061 | 0.135 |
  | 2026 | 0.072 | 0.043 | 0.115 |
  | 2027 (published) | 0.049 | 0.056 | 0.105 |

  — [Energi Data Service, DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist)
- **Grid company tariffs.**
  - Every grid company's household tariff ("Nettarif C") is published with hourly resolution
    (`PT1H`, 24 prices per day). The dataset's `Price1`–`Price24` columns are the hours of the
    local Danish day. On DST transition days, the shifted hour gets the price of the hour before
    it. — [Energi Data Service, DatahubPricelist metadata](https://api.energidataservice.dk/meta/dataset/DatahubPricelist)
  - Common structure (Tarifmodel 3.0) at most grid companies:
    - lavlast (low load) 00–06;
    - højlast (high load) 06–17 and 21–24;
    - spidslast (peak) 17–21.

    Winter tariffs apply from 1 October to the end of March, with the largest winter/summer
    difference in 17–21. Most grid companies raised their tariffs from 1 October 2026. —
    [Forbrugerrådet Tænk, 29 Sep 2026](https://taenk.dk/forbrugerliv/bolig/nettariffer-betydning-for-samlet-elpris)
- **Current "Nettarif C" rates, DKK/kWh excl. VAT (low / high / peak):** —
  [Energi Data Service, DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist)

  | Grid company (area) | Winter (period) | Summer (period) |
  |---|---|---|
  | Radius (DK2) | 0.106 / 0.319 / 0.956 (2026-10-01 → 2027-04-01) | 0.106 / 0.159 / 0.414 (Apr–Sep 2026) |
  | Cerius (DK2) | 0.115 / 0.346 / 1.038 (2026-10-01 → 2027-04-01) | 0.115 / 0.173 / 0.450 |
  | N1 area 131 (DK1) | 0.088 / 0.264 / 0.791 (Oct–Dec 2026) | 0.088 / 0.132 / 0.343 |
  | TREFOR El-net Øst (DK2) | 0.095 / 0.284 / 0.852 (Oct–Nov 2026), then 0.14 / 0.42 / 1.26 from 2026-12-01 | — |
  | TREFOR El-net (DK1) | 0.043 / 0.129 / 0.386 (Oct–Dec 2026) | 0.043 / 0.064 / 0.167 (Apr–Sep 2026) |
  | Dinel (DK1) | 0.062 / 0.185 / 0.554 (Oct–Dec 2026) | — |
  | Konstant (DK1, area 151) | 0.061 / 0.182 / 0.545 (Oct–Dec 2026) | — |
  | NOE Net | 0.056 / 0.169 / 0.507 (winter) | — |
  | Vores Elnet | 0.077 / 0.231 / 0.692 (Oct–Dec 2026) | — |
  | Zeanet | 0.072 / 0.216 / 0.647 (Oct–Dec 2026) | — |

  Within a season, the peak is about 3× the high-load rate in winter and about 2.6× in summer.
- **The tariffs change often, and not only on 1 October and 1 April.**
  - Dinel has a separate April step and then a May–September step.
  - Zeanet changed on 2026-09-01.
  - TREFOR El-net Øst changes on 2026-12-01.
  - N1 area 131 had a separate December 2025 rate (0.068 / 0.204 / 0.612).
  - Rows already published for 2027 raise rates, e.g. N1 area 131 0.098 / 0.295 / 0.885 from
    2027-01-01.
  - A TREFOR El-net row valid from 2027-01-01 prices 00–03 at the high rate (0.1998) and only
    03–06 at the low rate (0.0666). This changes the period boundaries, not just the levels.

  — [Energi Data Service, DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist)
- **Spot price level in 2026.** Average spot price over the first nine months of 2026: DK1 0.80,
  DK2 0.81 DKK/kWh, 34 % above the same period of 2025. Norlys says the spot price comes on top of
  Energinet tariffs, subscriptions, a spot surcharge, VAT and grid tariffs, which "can vary hour to
  hour". — [Norlys via Ritzau, 10 Oct 2026](https://via.ritzau.dk/pressemeddelelse/15217218/elprisen-er-blevet-mere-end-30-procent-dyrere-pa-bare-et-ar?lang=da)
  My own figures agree: mean spot 2026-01-01..2026-10-29 was DK1 0.831 and DK2 0.848 DKK/kWh.
  Maximum quarter-hour spot: DK1 5.88, DK2 6.81 DKK/kWh. (own calculation, from
  [DayAheadPrices](https://api.energidataservice.dk/dataset/DayAheadPrices))
- **Supplier markup (spottillæg) and subscriptions.**
  - Markups are per-kWh surcharges. An example of 12 øre/kWh costs over 800 DKK/yr at
    7,000 kWh. —
    [Mobilsiden, 24 Jan 2026](https://mobilsiden.dk/?p=253406)
  - Some charging operators cut service subscriptions for 2026 but raised their spot markups. —
    [FDM](https://fdm.dk/nyheder/bilist/2025-11-fra-2026-kan-du-tjene-penge-paa-saette-elbilen-til-opladning)
- **VAT.** Elafgift is quoted as "1 øre pr. kWh inkl. moms (0,8 øre ekskl. moms)", which implies
  25 % VAT. — [Mobilsiden, 24 Jan 2026](https://mobilsiden.dk/?p=253406)
- **Grid tariffs apply under fixed-price contracts too.** All customers in a grid area pay the same
  grid tariff, whatever their supplier. — [Forbrugerrådet Tænk](https://taenk.dk/forbrugerliv/bolig/nettariffer-betydning-for-samlet-elpris)

### Inferences
- **Worked example (own calculation from the cited rates): Radius, winter 2026/27, with a variable
  contract.**
  - Flat parts: Energinet 0.115 + elafgift 0.008 = 0.123 DKK/kWh excl. VAT, i.e. 0.154 incl. VAT.
  - Hour-dependent tariff: 0.106 (00–06) to 0.956 (17–21) excl. VAT. The swing is 0.85 excl. VAT,
    1.06 DKK/kWh incl. VAT.
  - Total incl. VAT: ≈ 1.25 × (spot + markup + 0.229) at night, and 1.25 × (spot + markup + 1.079)
    at 17–21.
- **Which components vary by hour.** Reasoning:

  | Component | Varies with | Same for every hour of the day |
  |---|---|---|
  | Spot price | Each quarter hour (see question 3) | No |
  | Grid tariff | Hour of the day, season, and grid company | No |
  | Energinet tariffs | — | Yes |
  | Elafgift | — | Yes |
  | Supplier markup | — | Yes, as a rule (see gaps) |
  | VAT | — | No: multiplicative, 25 % of the total |

  VAT scales the spread rather than shifting it.
- **What the cut means for the engine.** Reasoning: with elafgift at 0.008, the flat part is about
  10 % of an average total price. Before 2026 it was ≈45 % (0.72 + 0.135 against an average total
  of ~1.9 incl. VAT). Hour selection therefore matters relatively more in 2026–2027 than before.

### Gaps
- Radius's own tariff page returned HTTP 503. The Radius rates above are from DataHub only, not
  from Radius's page.
- I found no source on whether supplier markups are ever time-dependent, i.e. whether any Danish
  supplier charges a markup that varies by hour.
- Fixed subscriptions (grid and Energinet "abonnement") were not quantified. They do not depend
  on the hour.
- The elafgift rate from 2028 is not found. skat.dk calls the cut temporary through 2027-12-31.
- I could not open Green Power Denmark's or Energinet's description of the "TSO-DSO" tariff model
  planned for 2027, which would fold Energinet's transmission tariff into grid company tariffs.
  The [DOI article](https://www.doi.dk/en/ptx/artikel/ny-tarifmodel-paa-vej-skal-sikre-bedre-udnyttelse-af-elnettet)
  showed only its lead, which says only that grid companies will pay for using the transmission
  grid. DataHub still lists Energinet's 2027 tariffs separately.
- The TREFOR El-net 2027 period change (00–03 priced as high load) is seen only in DataHub rows.
  I did not confirm it on TREFOR's site.

## 2. Is there a reduced electricity tax for EV charging in 2026, and does it change which hours are cheapest?

### Takeaway
The refund scheme through charging operators still exists (now extended to households with solar,
2026–2030). With elafgift at 0.8 øre, the refund is at most 0.4 øre/kWh excl. VAT (≈0.5 øre incl.
VAT), which is economically irrelevant in 2026–2027. It is a flat amount per kWh, so it never
changed which hours are cheapest.

### Cited Findings
- **The scheme for 2026–2030 (skat.dk, 18 Dec 2025).**
  - From 1 January 2026, charging operators (ladeoperatører) can get the elafgift refunded also for
    households with renewable generation, e.g. solar, and an EV charger. The scheme runs to
    31 December 2030.
  - The household must consent to DataHub access.
  - Grid import and charger consumption must be documented hour by hour. The lower of the two
    readings in each hour is the basis for the refund. Solar-supplied charging is not refunded.
  - The refund equals the current elafgift minus the EU minimum of 0.4 øre/kWh.
  - No separate-meter or registration requirement is stated on that page.

  — [skat.dk](https://skat.dk/erhverv/afgifter-paa-varer-og-ydelser-punktafgifter/nyhedsbrev-afgifter/udvidet-refusionsordning-for-elafgift-ved-opladning-af-elbiler)
- **The refund before 2026.** It was about 90 øre/kWh. As of January 2026, "ikke længere nogen
  ladeudbydere" offer it. At 3,000 kWh/yr the refund would now be about 30 DKK/yr. —
  [Mobilsiden, 24 Jan 2026](https://mobilsiden.dk/?p=253406)
- **FDM's view of the market after the cut.**
  - The refund is largely unnecessary now that the tax is almost gone.
  - EWII and Looad cut their subscriptions to 0 DKK/month, and OK and Norlys cut theirs by 20–30
    DKK/month.
  - Looad offers a discount in exchange for flexible, grid-balancing control of charging.

  — [FDM, 20 Nov 2025](https://fdm.dk/nyheder/bilist/2025-11-fra-2026-kan-du-tjene-penge-paa-saette-elbilen-til-opladning)
- **Savings from the cut.** About 2,157 DKK/yr for a driver at ~15,000 km (~3,000 kWh) without a
  refund solution. Drivers on a refund agreement gain little, since they already got the tax
  back. — [Mobilsiden, 21 Aug 2025](https://mobilsiden.dk/?p=240988)

### Inferences
- **Effect on hour ranking.** Reasoning: the refund was always a flat per-kWh amount, so it shifts
  every hour equally and never changed the ranking. In 2025 it did change the level a lot: about
  −0.90 DKK/kWh incl. VAT, which mattered for comparing home charging with public charging and for
  thresholds such as `charger_auto_threshold`. In 2026–2027 it is negligible.
- **2028 onwards.** Reasoning: if elafgift returns to near its former level after 2027 while the
  refund scheme runs to 2030, the refund becomes relevant again. The engine is unaffected, since it
  is flat, but an integration that shows absolute DKK costs would need a "refunded elafgift"
  offset.

### Gaps
- Clever, Monta, Spirii, Norlys and Andel Energi's own 2026 refund terms: not checked on their own
  pages. Search snippets mentioned Clever figures (76.1 / 95.1 øre), but those are pre-2026 and
  were not opened.
- The elafgift and refund rates for 2028+ were not found.

## 3. Day-ahead timing, 15-minute MTU, and whether Danish retail prices and tariffs are per 15 minutes or per hour

### Takeaway
Since delivery day 1 October 2025 the day-ahead spot price for DK1/DK2 is set per 15 minutes
(96 prices per day). It is published around 12:45 CET for the next day, which the Energi Data
Service API carries by roughly 13:00–14:00 CET. Grid tariffs remain hourly. Households on the
default variable product are billed an hourly price, the simple average of the four quarter
prices; large suppliers must also offer quarter-hour products. An engine that assumes hourly slots
(O11) is now behind the market's native resolution.

### Cited Findings
- **Publication time.** Nord Pool's Nordic/Baltic day-ahead auction has gate closure at 12:00 CET
  and "results are published 12:45 CET", for physical delivery the next day. —
  [Nord Pool support](https://support.nordpoolgroup.com/support/solutions/articles/8000077444-about-the-day-ahead-auction-in-nordics-baltics)
- **Energi Data Service, DayAheadPrices.**
  - Resolution "15 minutes (PT15M)", updated daily.
  - "For data before 2025-10-01 see Elspot Prices (hourly resolution)".
  - Its guidance for tomorrow's prices is to poll "every five minutes or so between 13:00 and
    14:00 CET".
  - DKK prices are converted from EUR at Danmarks Nationalbank's rate, so they may differ from
    Danish prices quoted elsewhere.

  — [Energi Data Service, DayAheadPrices metadata](https://api.energidataservice.dk/meta/dataset/DayAheadPrices)
- **Elspotprices** (hourly) is "Discontinued", with no data after 2025-09-30. —
  [Energi Data Service, Elspotprices metadata](https://api.energidataservice.dk/meta/dataset/Elspotprices)
- **The data itself.** The first DK1/DK2 quarter-hour row is 2025-10-01T00:15 (Danish time). On
  2026-10-28 the dataset already held prices to 2026-10-29T23:45, i.e. tomorrow's prices. —
  [DayAheadPrices](https://api.energidataservice.dk/dataset/DayAheadPrices) (own query)
- **What households are billed (Forbrugerrådet Tænk, 29 Sep 2025).**
  - From 1 October 2025 the Nord Pool price changes every quarter hour (96 prices per day).
  - Customers on a variable hourly price get an hourly price equal to the simple average of the
    four quarter prices.
  - Large suppliers (≥200,000 customers) must offer quarter-hour products.
  - Most meters can handle quarter-hour values. An unsuitable meter is replaced at the customer's
    expense, typically a fee of almost 1,600 DKK.
  - Price differences between quarters are typically "a couple of øre" (Green Power Denmark).
    Norlys estimates that an average family might save about 200 DKK/yr by following quarter-hour
    prices.

  — [Forbrugerrådet Tænk](https://taenk.dk/forbrugerliv/bolig/flere-elpriser-i-doegnet-giver-minimale-besparelser)
- **Grid tariffs stay hourly.** All grid tariffs in DataHub have resolution `PT1H` or `P1D`; none
  is per quarter hour. — [DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist)
- **The spot market moved to quarter-hour prices on 1 October 2025.** Two East Danish grid
  companies reviewed over 100 bills to see whether quarter-hour settlement pays; the article's
  lead suggests it does not. Its findings are behind a paywall and were not read. —
  [Ingeniøren, 3 Nov 2025](https://ing.dk/artikel/kan-det-betale-sig-afregne-elpris-hvert-kvarter-det-svarer-ny-analyse-paa)

### Inferences
- **Intra-hour variation is real but small for an EV** (own calculation, DayAheadPrices
  2025-10..2026-10).
  - The range between the dearest and cheapest quarter within one hour averages 0.16 DKK/kWh excl.
    VAT in DK1 and 0.17 in DK2 (median 0.10; 90th percentile ≈0.39).
  - Charging 5–7.5 kWh a night at 11 kW and choosing the cheapest quarters, rather than whole
    cheapest hours, saves only ≈45–75 DKK/yr. That is about 2 % of the smart-charging cost, close
    to Norlys' ~200 DKK/yr for a whole household.
- **How 15-minute slots pay off for a short charge.** Reasoning: at 11 kW a typical nightly need
  (5–7.5 kWh) takes 27–41 minutes, less than one hour. Quarter slots let the engine buy exactly the
  cheapest 2–3 quarters instead of a whole hour. The gain only reaches the bill if the household
  is on a quarter-hour product. On the default hourly product, the supplier bills the hourly
  average whichever quarters are used, so choosing quarters within an hour earns nothing.
- **What the engine therefore needs.** Reasoning: the slot length must be a property of the input
  (15 or 60 min), not an assumption. The integration must also know which billing resolution the
  user is on, to decide whether to pass quarter prices or hourly averages.
- **DST.** Reasoning: the engine must handle 92- and 100-quarter days at DST transitions. DataHub
  fills the shifted hour with the previous hour's price; the DataHub rows for 2027-03-28 and
  2027-10-31 show the shifted index.

### Gaps
- I could not open the SDAC/Market Coupling Steering Committee go-live notice: EPEX page HTTP 403,
  Nord Pool's 15-minute article HTTP 404. The 1 Oct 2025 date rests on Energi Data Service's
  metadata and data, Tænk and Ingeniøren.
- The regulation requiring large suppliers to offer quarter-hour products (a bekendtgørelse) was
  not opened; only Tænk's statement is cited.
- How a supplier settles a quarter-hour product when the meter reports hourly values (an
  unweighted average or a profile key) was not confirmed; the Ingeniøren article is paywalled.
- I found no plan by any grid company for quarter-hour tariffs.

## 4. Negative prices: how often in DK1/DK2, and is the household total ever negative?

### Takeaway
Negative spot prices occur in about 1–3 % of quarter hours: more in DK1 than DK2, concentrated in
April–July midday hours, and fewer in 2026 than in 2025. Even with elafgift at 0.8 øre, the total
household price was negative in only 2 quarter hours in DK1 and never in DK2 over the past
13 months. A negative spot price makes an hour very cheap, not paid.

### Cited Findings
- **Spot price ≤ 0 or < 0, 2025-10-01..2026-10-29** (own calculation from
  [DayAheadPrices](https://api.energidataservice.dk/dataset/DayAheadPrices)):

  | Area | Quarter hours < 0 | Days with ≥1 negative quarter | 2026 YTD share < 0 | Minimum spot (DKK/kWh) |
  |---|---|---|---|---|
  | DK1 | 951 of 37,828 (2.5 %) | 50 of 394 | 2.9 % | −0.315 |
  | DK2 | 431 (1.1 %) | 24 of 394 | 1.3 % | −0.118 |

  Share of negative quarters per month, DK1 (DK2 in brackets):
  - Oct 2025: 4 % (2 %)
  - Nov 2025 – Feb 2026: 0 % (0 %)
  - Mar 2026: 1 % (1 %)
  - Apr 2026: 7 % (4 %)
  - May 2026: 7 % (5 %)
  - Jun 2026: 4 % (1 %)
  - Jul 2026: 7 % (1 %)
  - Aug 2026: 1 % (0 %)
  - Sep 2026: 2 % (1 %)
  - Oct 2026: 0 % (0 %)
- **Negative hours in 2026, fewer than 2025.** Up to late August 2026 there were 274 hours with
  negative prices in DK1 and DK2 together, against 629 at the same point of 2025. This is the
  first decline since 2022; Norlys points to the hot summer and to consumers shifting use,
  e.g. EV charging, into cheap hours. "It is far from certain" a consumer is paid in negative
  hours, as tariffs, Energinet's system tariff and the supplier markup are added. —
  [Dagbladet/Ritzau, 27 Aug 2026](https://dagbladet.sn.dk/article/6630445/erhverv/stort-fald-i-antallet-af-timer-med-negative-elpriser)
- **July 2026.** 49 negative hours in DK1 (12 in July 2025) and 10 in DK2 (4). The cheapest
  midday hours averaged about 0.18 DKK/kWh spot. —
  [Norlys via Ritzau, 31 Jul 2026](https://via.ritzau.dk/pressemeddelelse/15067089/prisfald-i-juli-gav-elbilister-flere-billige-ladetimer-og-samtidig-flere-timer-med-negative-elpriser?lang=da)
- **A recent example.** On 10 Oct 2026 the DK1 price was briefly −0.003 DKK/kWh around 13:00. —
  [Norlys via Ritzau](https://via.ritzau.dk/pressemeddelelse/15217218/elprisen-er-blevet-mere-end-30-procent-dyrere-pa-bare-et-ar?lang=da)
- **Total household price incl. tariff, Energinet, elafgift and VAT, no markup** (own
  calculation):
  - DK1 (N1 area 131): negative in 2 quarter hours; minimum −0.075 DKK/kWh.
  - DK2 (Radius): never negative; minimum +0.205 DKK/kWh.

### Inferences
- **When the total turns negative.** Reasoning from the rates in question 1: in 2026 the total is
  negative only when spot < −(grid tariff + 0.123 + markup) DKK/kWh. For a typical DK1 summer
  midday, at the high-load rate of N1 area 131, that means a spot price below about −0.26 DKK/kWh
  before any markup. For Radius/DK2 at midday the threshold is about −0.28. Such prices are rare.
- **What D25 means in practice.** Reasoning: supporting negative prices is still right; the engine
  must not clip at 0. In practice a negative spot price mostly makes a daytime hour competitive
  with the 00–06 night tariff, which matters only when the car is plugged in at midday (home
  workers, weekends, solar homes). Before 2026 the 0.72 elafgift made a negative total impossible.

### Gaps
- Official Energinet counts of negative hours for 2026 were not found; the counts above are Norlys
  figures and my own quarter-hour counts.
- I did not check whether any Danish supplier pays out, or caps, negative spot prices for
  households.

## 5. Size of the daily spread, and what smart charging saves per year

### Takeaway
In 2026 the daily max–min spread of the hourly total price (incl. VAT) has a median of ≈1.6 DKK/kWh
(DK1) and ≈1.7 (DK2); the spot price alone spreads ≈1.0 DKK/kWh excl. VAT. For ~1,800–2,700 kWh/yr
(roughly 9,000–14,000 km), choosing the cheapest slots between 17:00 and 07:00 instead of charging
on arrival at 17:00 saves about 1,400–3,000 DKK/yr, about 40 % (own calculation). Against a simple
"start at midnight" timer the extra saving is about 600 DKK/yr. No independent Danish study was
found.

### Cited Findings
- **Daily spread, 2026-01-01..2026-10-29** (own calculation from
  [DayAheadPrices](https://api.energidataservice.dk/dataset/DayAheadPrices) and
  [DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist)). Hourly total
  incl. VAT:
  - DK1 (N1 area 131): median 1.62, mean 1.76, p10 1.13, p90 2.38 DKK/kWh.
  - DK2 (Radius): median 1.72, mean 1.88, p10 1.18, p90 2.57 DKK/kWh.
  - Spot-only daily spread excl. VAT: median 1.03 (DK1) and 1.01 (DK2).
- **Annual cost, 2025-10-01..2026-10-28 (393 nights).** The car is plugged in 17:00–07:00 every
  day. "Plug-in-at-17" means charging immediately. "Smart" means the cheapest quarters by total
  price within the window. (Own calculation.)

  | Area | Daily energy | Power | Plug-in-at-17 (DKK/yr) | Smart (DKK/yr) | Saving | Average price, plug-in → smart (DKK/kWh) |
  |---|---|---|---|---|---|---|
  | DK1 | 5.0 kWh | 11 kW | 3,689 | 2,290 | 1,399 (38 %) | 2.02 → 1.25 |
  | DK1 | 7.5 kWh | 11 kW | 5,689 | 3,482 | 2,208 (39 %) | — |
  | DK1 | 7.5 kWh | 3.7 kW | 6,196 | 3,622 | 2,574 (42 %) | — |
  | DK2 | 5.0 kWh | 11 kW | 4,041 | 2,332 | 1,708 (42 %) | 2.21 → 1.28 |
  | DK2 | 7.5 kWh | 11 kW | 6,225 | 3,539 | 2,687 (43 %) | — |
  | DK2 | 7.5 kWh | 3.7 kW | 6,709 | 3,658 | 3,051 (45 %) | — |

- **Sensitivity, 2026 only, 6 kWh/night at 11 kW** (own calculation):

  | Strategy | DK1 (DKK/yr) | DK2 (DKK/yr) |
  |---|---|---|
  | Plug in at 17:00 | 3,836 | 4,221 |
  | Plug in at 19:00 | 5,011 | 5,327 |
  | Plug in at 22:00 | 3,840 | 3,913 |
  | Fixed timer from 00:00 | 3,106 | 3,129 |
  | Smart by total price | 2,487 | 2,551 |
  | Smart by spot only (billed at total price) | 2,672 | 2,768 |

  Ranking by spot alone costs 185–217 DKK/yr more than ranking by total price. On about 70 % of
  nights (DK1 218/301, DK2 204/301) the cheapest spot quarter between 17:00 and 07:00 lies outside
  the 00–06 low-tariff period.
- **Third-party figures.**
  - Mobilsiden: 15,000 km ≈ 3,000 kWh; at 1 DKK/kWh excluding elafgift (OK customers' 2025
    average) that is ≈3,000 DKK/yr. Public fast charging typically costs 3–4 DKK/kWh. —
    [Mobilsiden, 24 Jan 2026](https://mobilsiden.dk/?p=253406)
  - Norlys: an average family could save ~200 DKK/yr from quarter-hour versus hourly
    optimisation. — [Forbrugerrådet Tænk](https://taenk.dk/forbrugerliv/bolig/flere-elpriser-i-doegnet-giver-minimale-besparelser)

### Inferences
- **Where the saving comes from.** Reasoning from the sensitivity table: roughly half of the gain
  comes from the grid tariff structure, captured even by a dumb midnight timer. The rest comes from
  following the spot price within the night and the late evening. A spot-only ranking throws away
  about 7–8 % of the smart cost, because it ignores the tariff step at 06:00, 17:00 and 21:00.
- **The baseline matters.** The saving depends strongly on when the car would otherwise charge.
  Arrival at 17–19 falls into the peak tariff, which is the worst case; arrival at 22:00 is
  milder. Reported savings should name the baseline.
- **Model simplifications.** My model ignores the taper, charger ramp, absences and multi-day
  look-ahead. A real engine with a two-day horizon (prices for tomorrow arrive around 13:00) can do
  slightly better, e.g. by deferring to a cheaper night.

### Gaps
- No independent Danish study or official calculator quantifying annual savings from smart EV
  charging in 2026 was found and opened. A vendor claim (tado, 2,250 DKK/yr) appeared only in a
  search snippet and was not opened.
- I did not model other grid companies, but their tariff ratios are similar: peak ≈3× high-load in
  winter, low ≈1/3 of high-load.

## 6. Fixed-price and other contract types that change how much hour selection matters

### Takeaway
A fixed-price or flat supplier contract removes only the spot part of the variation. The grid
tariff's time-of-use structure still applies to every household, so hour selection still matters:
about half the savings above. Variable (spot-based) contracts dominate in Denmark.

### Cited Findings
- **The grid tariff applies whatever the contract.** All customers in a grid area pay the same
  grid tariff, whatever their supplier, and tariffs vary by time of day and season. —
  [Forbrugerrådet Tænk](https://taenk.dk/forbrugerliv/bolig/nettariffer-betydning-for-samlet-elpris)
- **Tænk advises choosing a variable contract over fixed price**, which "can give an overprice",
  and moving EV charging when on a variable contract. —
  [Forbrugerrådet Tænk](https://taenk.dk/forbrugerliv/bolig/flere-elpriser-i-doegnet-giver-minimale-besparelser)
- **Contract shares (Energistyrelsen, H1 2025; businesses only, not households).**
  - The smallest band (<20 MWh/yr): 16 % of customers are on fixed price (8 % of volume) and 81 %
    on variable price (87 % of volume).
  - The share of all business electricity bought at fixed price fell from 5.73 % (H2 2024) to
    3.52 % (H1 2025).

  — [Energistyrelsen, Elprisstatistik første halvår 2025](https://ens.dk/media/7667/download)
- **Flat-rate charging subscriptions.** Clever One costs 799 DKK/month with a home charger, which
  only pays off at about 40,000–50,000 km/yr of home charging. —
  [Mobilsiden, 24 Jan 2026](https://mobilsiden.dk/?p=253406)
- **Flexibility contracts.** Looad gives a discount on its electricity contract in exchange for
  controlling charging flexibly; in other European countries, drivers get free electricity for
  15,000–25,000 km/yr if they charge at an agreed time. —
  [FDM](https://fdm.dk/nyheder/bilist/2025-11-fra-2026-kan-du-tjene-penge-paa-saette-elbilen-til-opladning)

### Inferences
- **How each contract type changes the engine's job.** Reasoning:
  - Fixed supplier price: the engine should still rank by total price, which is then the grid
    tariff plus constants. The cheapest hours are 00–06 (or 03–06 at TREFOR El-net from 2027) and
    every hour in that block ties, so the tie-break rule matters.
  - A flat-rate subscription that includes electricity (Clever One type): every hour costs the
    same, and hour selection is pointless for cost, though still useful for other ends (grid
    friendliness, battery).
  - An operator that controls charging itself (Looad-type flex): conflicts with ChargeSmarter
    controlling the same charger.

### Gaps
- No household-level share of fixed versus variable contracts for 2025/2026 was found; the
  Energistyrelsen note covers businesses.

## 7. Implications for the engine's decisions (D3, D20, D25, D28, O11 and others)

### Takeaway
The sources support keeping prices opaque in the engine (D3) only if what the caller passes is the
**total marginal price per kWh**: spot + supplier markup + grid tariff + Energinet + elafgift, ×
VAT. They contradict the hourly assumption (O11): spot is per 15 minutes since 1 Oct 2025, while
tariffs and default billing remain hourly. D25 is supported, but a negative total is rare. D28 is at
risk when a charger's own automation looks at spot only.

### Cited Findings
- Spot is quarter-hourly ([DayAheadPrices metadata](https://api.energidataservice.dk/meta/dataset/DayAheadPrices)).
  Grid tariffs are hourly and seasonal ([DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist)).
  Default retail billing is the hourly average of the quarters
  ([Tænk](https://taenk.dk/forbrugerliv/bolig/flere-elpriser-i-doegnet-giver-minimale-besparelser)).
- Tomorrow's prices are published around 12:45 CET
  ([Nord Pool](https://support.nordpoolgroup.com/support/solutions/articles/8000077444-about-the-day-ahead-auction-in-nordics-baltics)),
  and Energi Data Service advises polling 13:00–14:00 CET
  ([metadata](https://api.energidataservice.dk/meta/dataset/DayAheadPrices)).
- Ranking by spot alone costs ≈185–217 DKK/yr more than ranking by total price (own calculation,
  question 5).

### Inferences
All of the following are reasoning.

- **D3 (prices are opaque numbers): supported, with a contract on what the number means.**
  - Keep the engine opaque. Document that `price` must be the marginal cost per kWh delivered,
    including every per-kWh component: markup, grid tariff, Energinet, elafgift and VAT.
  - Composing that number is a caller (integration) job. Energi Data Service's DatahubPricelist and
    the HA integrations that already compose it can supply the tariff.
  - Consider renaming or documenting the field as `price_per_kwh_total` in the naming pass (O3).
- **D20 / O4 (forecast markup): the markup should apply to the spot part only.**
  - The tariff, elafgift and Energinet parts of a "forecast" hour are known with certainty, from
    DataHub rows published months ahead.
  - A percentage markup on the total overstates the uncertainty, most at night, where the flat
    part is a large share. It also misbehaves near zero and for negative totals, where a
    percentage markup makes a negative price more negative.
  - Proposal: either an **absolute** markup (DKK/kWh) by hours ahead, or a `PricePoint` split into
    `known_part` and `uncertain_part`, so the markup applies only to the uncertain part.
  - Known spot covers tomorrow only after about 13:00 CET. Before that, everything past midnight is
    forecast. So the "known horizon" swings daily between ~11 and ~35 hours, and S1 should measure
    error by hours ahead from the auction, not from now.
- **D25 (negative prices): supported.**
  - The total can be negative, though rarely: 2 DK1 quarter hours in 13 months.
  - Negative spot makes daytime slots compete with the night.
  - Ensure ranking and cost handle negative totals, and that the marked-up price stays meaningful
    (see D20).
- **D28 (`charger_auto_threshold`): risk.**
  - If a charger's own price automation (for example in Easee or Zaptec apps) compares the
    threshold with the **spot** price, it will charge at 17–21 on a cheap-spot evening that is
    expensive after the peak tariff. That is ≈1.06 DKK/kWh incl. VAT dearer in winter than the
    same spot price at night.
  - The threshold must be stated in the same price basis the engine uses, which is the total. The
    integration should know which basis the charger compares against, or prefer to keep control.
  - Not verified: which basis Easee or Zaptec actually use (outside this scope).
- **O11 (sub-hour slots): resolve in favour of variable slot length.**
  - `PricePoint` needs a duration, or the API layer infers it from spacing. It should allow 15 and
    60 minutes, and a mix, e.g. quarter-hour spot for tomorrow and hourly forecasts beyond.
  - The integration decides the resolution from the user's billing product: quarter prices for a
    quarter-hour product, hourly averages for the default product.
  - The 168-point performance budget becomes 672 points for 7 days of quarters. Re-measure the
    10 ms budget (motor.md §7).
  - `simulation_step_minutes` should divide 15. Of the candidate defaults in O8, 3 does and 6
    does not.
- **D19 (`min_session_kwh`) and D22 (greedy).** With quarter slots, cheapest-first may pick
  scattered single quarters. The soft minimum session and any restart penalty become more
  relevant, and S4 should test greedy on quarter data.
- **DST handling.** Days have 92/100 quarters (23/25 hours). DataHub's hourly tariffs map by local
  hour with a special rule on transition days; the caller must resolve this before the engine.
- **D13 (tariffs outside the engine): consistent.** Time-of-use tariffs are flattened into the
  per-slot total by the integration, as feature-candidates.md already says for "Time-of-use tariffs
  with fixed blocks". In Denmark this is not optional: it is half the value.
- **O1 (charging beyond floors when cheap).** With a median daily spread ≈1.6–1.7 DKK/kWh and a
  night total often ≈1.0–1.3, a threshold "below X DKK/kWh" is meaningful only on the total basis.
  The new information is that the low-tariff block makes nights systematically cheap. A percentile
  rule (O1c) adapts to tariff changes on 1 Oct / 1 Apr without user retuning.

### Gaps
- The calibration data for S1 (forecast error by hours ahead) is not covered here; that is a
  separate research item.
- Not verified: whether Home Assistant's common Danish price integrations (Energi Data Service,
  Nord Pool, Strømligning) already expose a total including tariffs per 15 minutes. That belongs
  to S3/adapters.
