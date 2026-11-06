# Compose the right price, then anchor forecasts

The cheapest way to charge an EV at home is still, in order: buy in the hours the **grid tariff**
makes cheap, rank the **billed total price** of the hours already published, and only then use
forecasts to move energy between days. For the maintainer (DK1, N1, billed per hour, about 6 kWh a
night) a plain midnight timer is worth about **1,090 DKK a year** against charging on arrival, and
ranking tonight's published totals about **410 DKK** more ([review §1][rv]). A forecast, used with
soft future demands under a 60 % ceiling on extra stock, added **44–52 DKK in an October-like month
in DK1** in a replay that used only what the engine would know at each moment ([replay][rp]). The
earlier report's backbone survives an independent review: every tariff, tax and savings number
re-queried at source matched. But its money was computed for quarter-hour billing, and the review
found **two blocking gaps in the price adapter**, not in the planner: an additive forecast markup
whose unit and VAT basis nobody converts, and dates silently priced with a grid tariff of zero
([review §5][rv]). Forecasts are indeed usually low (16–22 % of spot in DK1, 25–34 % in DK2, in one
autumn month), and right on trend, but the trend helps only when it is tied to the forecast's own
value for slots that have since become known; discarding the level and keeping the shape cost more
than the bias did ([forecast note §2][fb]). The engine should therefore take two price kinds,
KNOWN and EXPECTED, while a pure library helper turns any forecast or trend into EXPECTED by an
additive shift anchored on the last publication and fading over about four days. The same contract
serves any bidding zone and any settlement period, provided slots carry a start and an end and the
integration passes the price of the period it is actually billed.

## The earlier report holds, but its money was quarter-hour money

**The factual backbone was re-opened and matches.** An independent reviewer re-queried 22 numbers
from the report on 2026-11-06. Elafgift of 0.008 DKK/kWh for 2026–27, Energinet's 0.115, Radius's
and N1's winter rates, the 2.5 % of negative DK1 spot quarters and the two negative DK1 total
quarters (minimum −0.075 DKK/kWh) all matched DataHub
([DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist);
[DayAheadPrices](https://api.energidataservice.dk/dataset/DayAheadPrices)). The price note's 2026
savings table (plug-in 3,836, timer 3,106, smart 2,487, spot-ranked 2,672 DKK a year) was reproduced
**to the krone** from N1's dated rows ([review §1][rv]). N1's own press release confirms its winter
rates of 11 / 33 / 99 øre incl. VAT from October 2026 to March 2027
([Ritzau](https://via.ritzau.dk/pressemeddelelse/15176319/n1-overgar-til-vintertariffer-1-oktober-brug-strommen-uden-for-myldretiden-og-fa-en-billigere-elregning?lang=da)).

**What does not hold for this maintainer is the billing basis.** Every savings figure in the
earlier report assumed quarter-hour billing, but households on the default product pay "et simpelt
gennemsnit" of the four quarters in each hour
([Tænk](https://taenk.dk/forbrugerliv/bolig/flere-elpriser-i-doegnet-giver-minimale-besparelser)).
Re-run on hourly billing with N1 area 131's dated rows, 301 nights of 2026 scaled to a year, the
numbers move in opposite directions ([review §1][rv]):

| Case (hourly billing, DK1, N1) | Plug-in at 17:00 | Timer at 00:00 | Smart by total | Smart by spot | Timer's value | Ranking over the timer | Loss from ranking on spot |
|---|---|---|---|---|---|---|---|
| 6 kWh a night, 11 kW | 4,119 | 3,033 | 2,622 | 2,775 | **1,087** | **411** | 154 |
| 6 kWh a night, 3.7 kW | 4,345 | 2,991 | 2,673 | 2,792 | 1,354 | 317 | 119 |
| 15 kWh a night, 11 kW | 10,690 | 7,508 | 6,643 | 6,967 | 3,182 | 865 | 324 |

The timer is worth more on hourly billing (1,087 against 730) because a charge starting at 17:00
pays the whole hour's mean rather than its cheap first quarter; ranking is worth less (411 against
470–630) because there is less to rank. The ramp inside the hour is large: in 2026 the four DK1
quarters of 17:00–18:00 averaged **0.681 / 0.810 / 0.921 / 1.042 DKK/kWh** of spot ([review §1][rv]).
Hourly billing therefore **strengthens** the report's central message that tariff timing comes
first and the planner's sophistication last. A slow charger gains less from ranking (317 DKK at
3.7 kW), because it needs more of the night and has less to choose from.

**The end-to-end replay shows the value of ranking depends on how the car is used.** With a
commuter whose car is home in the daytime and at weekends, a planner on published prices beat a
midnight timer by **1,484 / 1,992 / 2,292 DKK a year** in DK1 for the three schedules tested, two to
five times the 410–630 above ([replay, places][rp]). The difference is not a contradiction. The
nightly calculation charges a fixed 6 kWh every night and lets the timer stop at the need; the
replay's timer charges from midnight to 80 % and never sees a cheap afternoon or weekend hour. The
honest range for "ranking over a timer" is therefore about **300–900 DKK a year for a car plugged
in only at night**, rising towards 1,300–2,300 when the car is often home while daytime prices are
low. That replay timer also held the car above 55 % for 5,500–7,000 hours a year, a wear cost the
money figures leave out.

**Smaller corrections to the earlier text.** The headline swing of 1.06 DKK/kWh is Radius's; N1's is
**0.88 DKK/kWh incl. VAT** now and 0.98 from 2027-01-01. The headline "600–1,100 DKK" for the timer
should read 730–1,090 on quarter billing, or the hourly figures above. Register row S1's "23–38 %"
should be "23–32 %" (35–38 % was the naive baseline's share). The summary's verdict counts omit L1,
L4 and O10 (changed) and O5, S2 and S4 (answered). "As motor.md §6.2 now says" states the opposite
of motor.md, which plans only "within the price data" ([motor.md][mm]; [review §1, §4][rv]). The
report's plan to read the maintainer's past Carnot forecasts from Home Assistant's recorder is
**dead**: the Energi Data Service (EDS) integration has excluded its `forecast` attribute from the
recorder since commit `966dbab` of 2025-09-13
([EDS sensor.py](https://github.com/MTrab/energidataservice/blob/4b4085d004c5c3721258e7802b88b05d441e2670/custom_components/energidataservice/sensor.py)).
No history exists; his Carnot runs exist only from the moment his own logging started.

**One feared failure does not occur.** The earlier report warned of a "false price cliff" where a
spot-only forecast is joined to a total price. In EDS, with tariffs switched on, Carnot's spot
forecast passes through the same `_calculate` as the known prices: spot, the user's markup
template, the system tariffs and the charge owner's tariff for the slot's local date and clock
hour, all times one plus VAT
([EDS sensor.py](https://github.com/MTrab/energidataservice/blob/4b4085d004c5c3721258e7802b88b05d441e2670/custom_components/energidataservice/sensor.py);
[Carnot connector](https://github.com/MTrab/energidataservice/blob/4b4085d004c5c3721258e7802b88b05d441e2670/custom_components/energidataservice/forecasts/carnot/__init__.py)).
The connector file itself converts nothing, which is why the forecast note read it as unconverted;
the conversion happens in the sensor ([forecast note §1][fb]). So the maintainer's "always lower"
is not an artefact of mixed bases. The refusal to mix bases still matters for other sources, such
as core Nord Pool and Strømligning's forecasts, which exclude tariffs.

## Twelve ways the composed price can still pick the wrong hour

The reviewer traced the price from Nord Pool to the engine and found that the planner's logic is
sound; the risks sit in composition. The replay then priced several of them by deliberately
planning on the faulty price and billing the correct one. **Each composition fault that cost
anything cost 60–165 DKK a year, while the choice between a greedy and an exact DP was worth nothing
measurable in Denmark** ([replay, defaults][rp]). The table orders the mechanisms by what is known
about their cost.

| # | Mechanism | Where it bites | Measured or estimated cost | Scope |
|---|---|---|---|---|
| 1 | **Markup unit and VAT not converted.** EDS shows DKK or øre, per kWh or MWh, with or without VAT; its template is excl. VAT and the VAT setting is not exposed as an attribute | A "0.08 DKK/kWh incl. VAT" default is off by ×100, ×1,000 or ×1.25; too small a markup makes the engine wait for forecast days | Not measured; **blocking** | Any source |
| 2 | **Silent zero tariff.** When no DataHub row covers a date, EDS sets the owner tariff to 0 with no warning | That day looks 0.11–1.1 DKK/kWh cheaper incl. VAT and the engine defers to it | Not measured; **blocking**. Cannot happen for N1 now (rows to 2028); several companies' rows end 2027-02-01 | Denmark (EDS) |
| 3 | Tariff hour read in UTC instead of local time | Moves every period boundary by 1–2 h; peak share 2.8 → 7.6 % | **+97 / +155 / +60 DKK/yr** | Any time-of-use tariff |
| 4 | Hourly price taken as the first quarter, not the mean of four | Ranks on a price nobody bills | **+106 / +163 / +119 DKK/yr** | Hourly billing |
| 5 | Quarters ranked while billed per hour (EDS 15-minute mode) | Picks 17:00 over 17:45, a difference not paid; starts +78 % | **+82 / +109 / +70 DKK/yr** | Hourly billing |
| 6 | Tomorrow published late or decoupled | Tomorrow is priced from the forecast until it arrives | 13:00 → 18:00: +180 to +354 DKK/yr; only from midnight: +745 to +922 | Any once-daily auction |
| 7 | No proxy price for a departure beyond the published prices (N8 absent) | Buys Sunday evening at high load instead of Monday 00–06 | +21 to +147 DKK/yr at 13:00 publication; +1,300 to +3,500 if prices arrive only at midnight | Any place |
| 8 | Wrong charge owner: EDS's "N1" is area 131 only; N1 also publishes for areas 016 and 344 | Identical rates today; in April 2027 area 131 calls 06–07 low load, area 016 high load at summer rates | 0 today; real from spring 2027 | DK1/N1 |
| 9 | Hardcoded periods or seasons | N1-131's 2027 rows keep winter rates through April, price 00–01 at the high rate and make 06–07 low load; N1-344 shifts periods 29 Mar–22 Jun | Not measured; the panel's own `prices.py` and `arbitrage.py` hardcode 00–06 / 17–21 | N1 now, any company later |
| 10 | Index-based EDS attributes (`today[0]` is 00:00) | 23 or 25 entries on DST days; `today` is `None` if tomorrow is missing at midnight | 0 for N1 (the shifted hour lies inside 00–06); non-zero for a boundary at 02–03 | Any |
| 11 | Supplier product ignored (fixed price, monthly average) | The spot part vanishes; all 00–06 hours tie and the tie-break decides | Not measured | Any |
| 12 | The car takes less power than planned | At 15 kWh a night and 3.7 kW the plan ran out of night on 167 of 301 nights; at 6 kWh and 7.4 kW never | Taper 11 → 7.5 kW from 65 %: −0.6 to +8.8 DKK per 31 days | Any |

Sources: mechanisms 1, 2, 8–12 from the code and DataHub rows the reviewer opened at EDS commit
`4b4085d` ([EDS tariffs](https://github.com/MTrab/energidataservice/blob/4b4085d004c5c3721258e7802b88b05d441e2670/custom_components/energidataservice/tariffs/energidataservice/__init__.py);
[chargeowners.py](https://github.com/MTrab/energidataservice/blob/4b4085d004c5c3721258e7802b88b05d441e2670/custom_components/energidataservice/tariffs/energidataservice/chargeowners.py);
[review §2][rv]); costs for 3–7, 10 and 12 from the replay's twelve months in DK1, DK2 and SE3
([replay, defaults][rp]).

Three further points sharpen the list. First, **N1's 2027 rows may be data errors or intentions**;
the reviewer could not open N1's own tariff page (HTTP 403), and neither the 2026 rows nor N1's press
release show the changes. Either way the rule is the same: read the dated hour-by-hour row, never a
rule, and flag a row whose period boundaries differ from the previous row's. Second, **mid-season
changes are routine**: N1 published December-only rows in 2024 and 2025, and other companies
publish weekday-and-weekend rows (Aal El-Net), November-only cuts (Elektrus), no low-load block
(FLOW Elnet) or flat 2027 tariffs ([DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist);
[review §2][rv]). A cache of "the tariff for this hour of day" breaks on all of them. Third,
**publication delays are real**: on 17 May 2026 Nord Pool announced at 13:50 CET a delayed coupling
"with a risk of Full Decoupling" ([Nord Pool](https://www.nordpoolgroup.com/en/trading/Operational-Message-List/2026/05/sdac_exc_03b-further-delay-of-the-market-coupling-session-20260517115000/)),
and 3 of the 11 elpriser.org runs made after the switch to CET were generated before the next day's
prices were out ([replay, method][rp]). The plan must re-run when a forecast slot is replaced by a
published one, not only on the next hourly tick.

The forecast's level bias is the remaining way to pick the wrong hour, and it acts on a different
choice. A uniform low bias does not reorder forecast days among themselves, which is why the
maintainer sees the trend as right. It does distort **the choice between a known day and a forecast
day**, making waiting look better than it is. The replay found that this did not turn any
forecast policy negative on average, for two reasons: the hard target of the next departure is
always bought from published prices (or the N8 proxy), and the 60 % ceiling limits pre-buying to
about a day ([replay, forecasts][rp]). The bias becomes dangerous only if the ceiling is lifted or
the markup is mis-scaled, which is mechanism 1 again.

**Not risks, after checking:** VAT applies to every component (class D02); grid tariffs are hourly
(`PT1H`), so metering per quarter or per hour gives the same grid charge; other household load in
the same hour does not change the marginal per-kWh price; a stale EUR→DKK rate scales every hour
alike ([review §2][rv]).

## Forecasts run a quarter low, but discarding their level costs more

### The bias is real, large and unstable

**Measured on every elpriser.org run of one month** (31 runs per area, 2026-10-06 to 11-05, 30
target days), the median forecast was low at every horizon from D+2 to D+9: by **210–307 DKK/MWh in
DK1 (16–22 % of spot)** and **339–495 in DK2 (25–34 %)**. On the total price that is −0.26 to −0.38
DKK/kWh incl. VAT for N1 and −0.42 to −0.62 for Radius ([forecast note §1][fb];
[elpriser OpenAPI](https://elpriser.org/api/openapi.json)). The live MAE of 354–532 DKK/MWh was 2.4–2.7
times the provider's own backtest of 149–197
([model card](https://huggingface.co/Elpriser/denmark-price-forecast)). The replay's independent
count on the same archive, by lead day from the last published day, found the same: DK1 +177 to
+328 DKK/MWh (actual minus forecast), under-forecast on 62–79 % of days; DK2 +306 to +517, on 78–85 %
of days ([replay, method][rp]). The bias has grown as data accumulated: −55 to +42 with actuals to
2026-10-27, −62 to −122 to 10-29, and −210 to −307 with 30 target days ([forecast note §1][fb]).

The maintainer's observation is **right in sign on 77–90 % of runs and 80 % of days, but not
"always"**. On windy low-price days the forecast was too **high** by +200 to +460 DKK/MWh, and in the
cheapest fifth of actual hours it was too high 79–85 % of the time ([forecast note §1][fb]). Binning
on the outcome exaggerates this through regression to the mean; binned on the forecast itself, which
the engine can see, the bias still grows with the forecast level, from −59 (cheapest fifth) to −438
(dearest) in DK1. The night hours 00–05, where an EV charges, were under-forecast least: −156
DKK/MWh in DK1, **−0.195 DKK/kWh on the total**. The forecast's within-day shape is too flat; its
Mincer-Zarnowitz slope was 1.37 (DK1) and 1.54 (DK2), meaning its swings are too small. A rule
"the forecast is low, so add X" would be wrong exactly when a cheap day is coming.

The bias is **not a constant**. It went from −132 to −358 DKK/MWh between the first and second half
of the month in DK1 as prices rose to 1,900–2,200 DKK/MWh, and the Mincer-Zarnowitz fit changed sign
between the halves. The day-level error has a lag-1 autocorrelation of 0.73–0.76, so the 30 days
carry the information of **only 4–5 independent days**, and the mean bias is not significant at the
5 % level ([forecast note §1][fb]). The provider says the same in its own words: "a model trained on
the older, calmer prices tends to run too low when the level rises", and its backtest "ends on
2026-07-30, before the price rise of September 2026"
([model card](https://huggingface.co/Elpriser/denmark-price-forecast)). What *is* stable is
persistence: the error of the latest run on the day just published correlates **0.72–0.78** with
the next run's error on D+2, 0.42–0.44 on D+4, and about zero by D+6 ([forecast note §1][fb]). That
is the error structure of a level that lags the market, and it is the structure an anchor can
remove and a long rolling average cannot.

**Carnot, the maintainer's source, is untested.** Its site states no model, accuracy or bias
([carnot.dk](https://www.carnot.dk/)), no public description was found, and it was never called in
this work. Everything above is elpriser.org's model in one rising autumn month.

### Five ways to use a biased forecast, measured twice

The forecast-bias researcher defined the candidate methods and scored them in a rolling daily
replanning simulation (a linear program at 14:00 each day over the known hours plus six forecast
days, car away 07–17, 10 kWh a day, 30 or 50 kWh of headroom, **no ceiling**, 30 decisions). The
replay researcher independently ran three of them inside the hourly-replanning engine with real
schedules and the 60 % ceiling ([forecast note §2][fb]; [replay, forecasts][rp]).

| Method | Definition | Forecast note: share of the oracle's saving over known-only (8 cells) | Replay, 60 % ceiling: DKK per 31 days vs P2, schedules 1 / 2 / 3 | Replay, no ceiling |
|---|---|---|---|---|
| Raw forecast (markup 0) | f | 71–87 % | DK1 −39.1 / −47.7 / −51.2 | DK1 −154.7 / −124.5 / −131.5; DK2 −172.4 / −146.5 / −140.2 |
| (a) Additive markup | f + m | a+0.1: 66–85 %; a+0.3: 56–89 %, helped DK2 and hurt DK1 | m = 0.05–0.10: within 7 DKK of m = 0 | m = 0.20: DK1 −155.9 / −110.4 / −148.3; no consistent best |
| (b) Rolling bias correction (≈ replay P4) | f minus the mean error of the last 14–15 settled days | b_mean: DK1 66–78 %, DK2 81–87 % | DK1 −45.8 / −33.1 / −50.0 (m 0); DK2 −75.7 / −85.6 / −60.8 (m 0.08); 3 of 30 DK1 seeds worse than P2 with m 0.08 | DK1 −140.9 / −102.7 / −129.6; DK2 −187.1 / −152.6 / −141.9 |
| (c) Anchored shift, undecayed (≈ replay P5) | f + δ, δ = latest day's actual mean − the earlier run's forecast of it | c_shift: DK1 77–78 %, DK2 77–87 %; worse than raw in all four DK1 second-half cells | DK1 −49.5 / −55.3 / −53.9 (m 0); DK2 −76.9 / −74.6 / −58.4 (m 0.08) | DK1 −145.6 / −96.9 / −136.4; DK2 −187.7 / −133.7 / −153.5 |
| (c) **Anchored shift, decaying** | f + w·δ, w = 1, .75, .5, .25, 0 for successive forecast days | **84–94 %**; not below raw in 14 of 16 half-sample cells | **Not tested** | Not tested |
| (d) Shape only around the known level | known mean + (f − mean f) | 31–61 %; below raw in 15 of 16 half-sample cells | Not tested | Not tested |
| (e) Rank only (quantile map onto known hours) | rank of f mapped onto known prices | 8–29 % | Not tested | Not tested |

In money, for DK1 on the total price with 30 kWh of headroom, the forecast note's simulation paid
1.624 DKK/kWh with no forecast, **1.395 with the raw forecast and 1.358 with the decaying anchor**:
about 69 DKK a month for using the forecast at all, and about 11 DKK more for the best correction
([forecast note §2][fb]).

### Where the notes disagree, and what to do about it

At first sight the two researchers disagree: the forecast note found the decaying anchored shift
best, and the replay found no consistent winner among markup, rolling correction and anchoring.
Read against their definitions, **they disagree less than they seem**. On the two methods both
tested they agree. The rolling correction helped DK2 and hurt DK1 in both (forecast note: b_mean 81–87
against raw 71–87 in DK2, 66–78 against 72–79 in DK1; replay: −2 to −15 DKK in DK2, +1 to +36 in
DK1 except one schedule). The undecayed anchor was mixed in both (forecast note: worse than raw in every DK1 second-half
cell; replay: better than raw in all three DK1 schedules under the ceiling, worse in two of three
without it). **The replay never ran the decaying anchor**: its P5 adds the latest day's error to
every forecast day, undecayed ([replay sim.py](../research_notes/Forecast%20price%20types%20and%20replay/experiments/replay/sim.py)).
And the replay's 60 % ceiling compresses every forecast policy into a range of about 10 DKK a
month, because no policy may pre-buy more than about a day; inside that range no method can be told
apart with 4–5 independent price regimes.

Both pieces of evidence are thin. The forecast note's lead rests on 30 decisions, 4–5 effective
independent days, and decay weights chosen **after** seeing the correlation table, so part of it is
in-sample. The replay's seeds (10 for DK1, 5 for DK2) vary consumption, not prices, so its price
evidence is the same single month. The literature points the same way as the forecast note. NCEP's
decaying-average bias correction for weather ensembles "works well for the first few days"
([Cui et al., NCEP](https://www.emc.ncep.noaa.gov/gmb/ens/papers/manuscript_thorpex_bocui.pdf)), and
its slow 2 % variant "is failed in March and April, when error characteristics experience a dramatic
change", with a faster 10 % variant slightly better
([Guan, Zhu & Cui, AMS 2014](https://ams.confex.com/ams/94Annual/webprogram/Manuscript/Paper232804/AMS94_extabs_hg_20140220.pdf)).
That is exactly what the 14-day rolling correction did here in a rising month. Price-forecasting
work warns that "selecting ex-ante one window is risky" and recommends averaging across windows
([Marcjasz, Serafin & Weron 2018](https://ideas.repec.org/a/gam/jeners/v11y2018i9p2364-d168385.html)).
Errors predictable from information known at issue, as the 0.72–0.78 correlation shows, are by
definition a bias an efficient forecast would not have
([Hansen, "Evaluating Forecasts"](https://users.ssc.wisc.edu/~bhansen/390/2010/390Lecture23.pdf)).

**Recommendation.** Make the **decaying anchored shift** the helper's default, additive, with a full
shift on the first forecast day fading to none by the fourth or fifth; keep the raw forecast as a
switch; ship **no rolling bias correction** and **no markup** by default. The reasons: it is the
only variant that matches the measured error structure, it was never materially below raw in either
area or either half, its failure mode (over-correcting a level that has just turned) is bounded by
the decay, and under the recommended ceiling the money at stake between methods is under 10 DKK a
month, so being wrong is cheap. Confidence: **medium that the decaying anchor is at least as good as
the raw forecast; low that it beats it by the 3–20 points measured; low on the weights.** Adding it
to the replay is desk work that can be done now, and the maintainer's Carnot log will test it on his
own source. Two refinements remain untested: anchoring per hour of day, since the night bias is about
60 % of the mean bias and a daily shift may over-correct night hours; and a blend such as
0.7 × anchor + 0.3 × a 14-day mean, which the window-averaging literature suggests is more robust.

**The markup.** Once the anchor removes the systematic error, the markup only prices the residual,
the optimiser's curse. No markup between 0.05 and 0.2 DKK/kWh could be told apart from zero in the
forecast note; 0.3–0.4 helped DK2 and hurt DK1; in the replay 0 to 0.10 spanned at most 7 DKK a
month under the ceiling and 1–23 DKK without it, with no consistent best value ([forecast note §2][fb];
[replay, forecasts][rp]). The earlier recommendation of an integration default of 0.08 DKK/kWh,
0.10 from D+4, rested on 21–23 decisions with elpriser.org, not Carnot ([review §1][rv]). Ship the
**integration default as 0**, keep the step table `[(lead_hours, amount)]` keyed on the lead from
the last publication, and calibrate it from the Carnot log. Confidence: medium.

### Known, expected and trend: two engine kinds and a helper

The maintainer proposed three price types. The evidence supports all three as **sources** and two
as **engine inputs**.

KNOWN is a published price. It carries no markup and is costed as given. EXPECTED is a price per
slot the engine plans on but does not trust: it carries the markup, and costs are still computed on
`price` (D20). TREND, the forecast's shape without a trustworthy level, should **not** be an engine
kind. To turn a trend into a usable price, the engine would need three things it does not and should
not have: the forecast that was in hand before the last publication, which the source has since
replaced (state across calls, against D10); the split of each price into its uncertain spot part and
its known tariff and tax parts (against D3, prices are opaque); and a rule specific to each source.
A dimensionless index applied to an all-in total would scale the grid tariff and the taxes; one
spread flat over a day would erase the 17–21 peak. And the shape-only methods that a trend kind
would naturally implement, (d) and (e), were the worst measured ([forecast note §3][fb]).

The recommended contract, with the engine kept a pure, currency-agnostic function:

```
PriceKind = KNOWN | EXPECTED
PricePoint(start, end, price, kind=KNOWN, origin=None, spread=None)

anchor_forecast(forecast, anchor_forecast, anchor_known,
                decay_days=(1, .75, .5, .25), mode=ADDITIVE)
    -> list[PricePoint(kind=EXPECTED, origin=...)]          # library helper, outside plan()
```

`price` is the billed price of the settlement period containing the slot, in the caller's units and
composition. `origin` is the end of the last published slot the expectation was anchored to; the
markup is keyed on `start − origin`, the lead from the last publication rather than from `now`. A
forecast for tomorrow night is a D+2 forecast whether it is read at 13:05 or at 23:00. `spread` is an
optional per-point uncertainty (such as P90 − P50) that a markup rule may use; note that elpriser.org's
band was too narrow in this month, with 30–38 % of actuals above P90 against a nominal 10 %
([forecast note §1][fb]). The helper works on the **uncertain component only** (spot), before the
caller adds the known tariffs and taxes; it accepts a level in any currency or a dimensionless trend
index; and with no anchor available it returns the forecast unchanged rather than a shape-only
guess. In the maintainer's terms: known → KNOWN; expected → EXPECTED after the anchor; trend → an
input of the helper, never of the engine.

The anchor needs one thing the integration must capture itself: **the forecast it held just before
each publication**, for the slots that publication covers. For elpriser.org that is the previous
day's archived run ([elpriser OpenAPI](https://elpriser.org/api/openapi.json)). For Carnot through
EDS it is the forecast for tomorrow read before about 13:00, because the integration drops
tomorrow's forecast entries once tomorrow's real prices are valid and records no fetch time
([review §2][rv]). A source with no overlap at all, a forecast that starts after the published
horizon with no past runs kept, cannot be anchored; for it only the raw level and a markup remain.

The trend still needs one thing the earlier report identified and the replay confirmed: **the
coming days' consumption must be in the input**. A markup or an anchor acts only on energy the engine
has been told it needs, so the integration expands usual departures over the forecast horizon as
soft targets. In the replay those soft targets produced 0 missed hard targets for every greedy
policy ([replay, method][rp]).

## A replay with only what the engine knows ranks the rules by money

The replay re-planned one Enyaq-like car (77 kWh usable, 11 kW, 90 % wall-to-battery) every hour and
at every plug-in, from exactly the information the integration would hold at that minute: published
prices to the end of tomorrow from 13:00 local, otherwise to the end of today; the newest forecast
run already generated, each from its own `generatedAt`; trips already announced; consumption already
observed. It executed only the first part of each plan, at the billed price. It covered the 31 days
with real forecast runs (2026-10-07 to 11-06) in DK1/N1 and DK2/Radius, and twelve months
(2025-11-07 to 2026-11-06) for the known-price policies in DK1, DK2 and a tariff-less SE3 model, on
hourly and quarter-hour billing, across three schedules: a weekday commute, the same with a weekend
trip in the calendar, and irregular trips announced 24 hours ahead ([replay, method][rp]).

**The ordering is robust everywhere: P0 ≫ P1 > P2 > forecast policies > foresight.**

| Policy, DK1/N1 hourly | 31 days, DKK (sched. 1 / 2 / 3) | vs P2 | Hours > 60 % | Year, vs P2 |
|---|---|---|---|---|
| P0 charge on plug-in | 1,680 / 2,290 / 1,267 | +828 / +1,114 / +427 | 541 / 489 / 654 | +5,193 / +7,696 / +3,976 |
| P1 midnight timer | 897 / 1,261 / 892 | +45 / +85 / +51 | 380 / 308 / 570 | +1,484 / +1,992 / +2,292 |
| P2 corrected greedy, published prices + N8 proxy | 852 / 1,176 / 840 | 0 | 0 / 68 / 62 | 0 |
| P3 forecast, markup 0.08, soft targets, 60 % ceiling | 809 / 1,126 / 789 | **−43.7 / −49.7 / −51.8** | 0 / 65 / 63 | — |
| P3 without the ceiling | 697 / 1,054 / 700 | −155.6 / −122.0 / −140.1 | 264 / 199 / 242 | — |
| P7c foresight under the 60 % rule | — | −59.3 / −54.9 / −86.1 | — | — |
| P7 perfect foresight, ten days | 656 / 1,012 / 638 | −196.6 / −164.2 / −202.7 | 299 / 239 / 360 | −2,003 / −1,612 / −1,818 |

Source: [replay][rp], 10 seeds for DK1 in the forecast window, 3 for the year; costs adjusted for
end-of-window SoC. P2 put 89 % of its energy into 00–06 and none into 17–21 in October; P0 put 57 %
into the peak.

**Forecasts add 4–7 % of the bill under the ceiling, and the ceiling decides the money.** Every
forecast policy beat P2 on average: P3 by 44–52 DKK per 31 days in DK1 and 58–86 in DK2, which is
60–91 % of what perfect foresight under the same ceiling could gain. Only P4 with a markup was ever
worse than P2, in 3 of 30 seeds, all in the long-trip schedule. Annualised as if every month were
like this October, that is roughly **500–700 DKK a year in DK1**, an upper-half estimate because
October 2026 moved more from day to day than the year did; summer is untested ([replay,
forecasts][rp]). Without the ceiling the same forecasts gain about three times as much (−122 to −156
DKK per 31 days), bought with 200–265 hours a month above 60 %. **The ceiling is the single largest
lever, and it is a battery-wear decision, not a price decision**: the 55–60 % default costs about
70–110 DKK a month in an October-like month relative to none. Whether that is worth it rests on the
wear value the earlier work put at 1,000–3,700 DKK per capacity point, which is reasoning on lab
cells, not a measurement.

**Exact optimisation buys no money under realistic information.** With published prices only, the
exact DP (P6a) and the corrected greedy (P2) paid the same to within ±1 DKK a month and +9 to +16
DKK a year in DK1 and DK2. With forecasts, soft targets and the ceiling, the DP (P6b) was 1–22 DKK a
month **worse** than the greedy, because the two encode the ceiling differently (the DP caps the SoC
reachable in a slot, the greedy only soft stock). Both act on the same wrong forecast, and the first
hour, the only part executed, is almost always the same. The DP won money only where the total
price went negative, which in this data happened only in the SE3 model without flat charges: 482
negative quarters, worth 74–198 DKK a year to the DP ([replay, DP][rp]). The replay also showed that
the greedy can carry soft targets and the ceiling, which weakens the earlier argument that only a
DP carries the whole objective. The DP's costs are elsewhere: 32–47 ms mean per plan with forecasts,
up to 130 ms on quarter-hours (on a cloud container, not a Raspberry Pi), and a 0.25 kWh SoC grid
that loses 9 % of every quarter-hour slot's reach at 9.9 kW. A grid of 0.2475 kWh, an exact tenth of
a full quarter, removed that loss and cut the quarter-hour DP's starts from 153–222 to 84–99 a month.

**What moves money and what does not.** More than 50 DKK a month or 100 DKK a year: the surplus
ceiling, the N8 proxy and the publication time, the composition faults in the previous section, and
using a plain timer at all. A few kroner: the idle floor (0 for commuters, −11 to +15 DKK per 31
days for the irregular schedule), the completion buffer (0 to +5), the markup size (≤7), replanning
every 15 minutes instead of 60 (−0.7 to +1.7), the taper (−0.6 to +8.8), and a stale season row or
DST position fault for N1 (0, because N1's low rate is the same either side of 1 October and the
shifted hour falls inside 00–06). The start overhead of N5 changed costs by −3 to +1 DKK a month; on
hourly billing it trimmed 0.6–2.6 starts a month, and on quarter-hours it **raised** starts by 35–40
a month, because the DP counts a slot as "on" whenever it charges at all and so rewards chains of
partly used quarters that execution can run only as separate sessions ([replay, billing][rp]). On
hourly billing the corrected greedy already started only about 1.2 sessions a day.

**Limits of the replay.** One month and one provider for the forecasts, elpriser.org as a stand-in
for Carnot with a similar low bias; one grid company per Danish area; synthetic schedules; no
battery wear in the money; and no late publication other than synthetic delays. Its seeds vary
consumption, so they measure robustness to driving, not to prices.

## One contract serves every bidding zone and settlement period

**The engine needs no notion of place or billing period if slots carry their own length.** Known
day-ahead prices have been quarter-hourly in every SDAC bidding zone since delivery day 1 October
2025 ([APG](https://markt.apg.at/en/news-press/sdac-go-live-of-15-minute-market-time-unit-in-day-ahead-market-coupling-successful-as-of-september-30-2025/)).
Forecasts are hourly in both Danish sources ([elpriser OpenAPI](https://elpriser.org/api/openapi.json);
[Carnot connector](https://github.com/MTrab/energidataservice/blob/4b4085d004c5c3721258e7802b88b05d441e2670/custom_components/energidataservice/forecasts/carnot/__init__.py)).
Danish grid tariffs stay hourly: every N1 and Radius row has resolution `PT1H`, `P1D` or `P1M`, and a
query for `PT15M` rows from 2026 returns none
([DatahubPricelist](https://api.energidataservice.dk/dataset/DatahubPricelist); [replay, method][rp]).
A single plan therefore mixes quarter energy prices, an hourly tariff and hourly forecasts. The
engine should build its grid from the **union of all slot boundaries**, apply a longer slot's price
unchanged to every finer piece inside it, and never interpolate or invent a shape. Its simulation step
and SoC grid must fit the shortest slot (the 0.2475 kWh lesson). DST days of 92 and 100 quarters,
both present in the data, are handled by continuity in absolute time ([forecast note §3][fb]).

**The integration passes the price of the period it is billed.** Under hourly billing it averages
the four quarters **by timestamp** (EDS averages by position, which one missing quarter would
misalign; DK1 has had none from October 2025 to November 2026) before calling the engine, so the
engine never chooses a cheap quarter nobody bills ([review §2][rv]). Under quarter-hour billing it
passes the quarters as they are, and hourly forecasts are step-mapped; the fixed intra-hour ramp of
up to about ±190 DKK/MWh is real but smaller than the forecast's D+2 error of 350–450, so a learned
quarter pattern is at most an option ([forecast note §3][fb]). A source that gives one level per day
must be shaped by the integration from an hourly forecast or the last known day's shape, plus the
dated tariff per slot; a flat daily total must never reach the engine. The engine needs no setting
for any of this: it sees what is billed.

**Quarter-hour billing is worth little and costs starts.** Against hourly billing, a planner on
published prices saved **21–92 DKK a year in DK1 and DK2 and 61–89 in SE3**, with the same targets met;
a midnight timer lost 5–18 DKK. But the greedy's starts more than doubled, from 36 to 80 a month
(over the year 402 → 836 in DK1), and a 0.25 kWh-grid DP's rose four- to sixfold ([replay,
billing][rp]). That matches a supplier's own estimate that a family "måske vil kunne spare 200
kroner om året" by planning around quarter prices
([Tænk](https://taenk.dk/forbrugerliv/bolig/flere-elpriser-i-doegnet-giver-minimale-besparelser)),
and it is smaller than any single composition fault. For the maintainer, a switch to a quarter-hour
product later needs no engine change: only the adapter's product setting changes. Whether two or
three sessions a night matter depends on the charger and car, which the replay cannot price.

**The anchor is defined without anything Danish.** "The latest published day-ahead slots, compared
with the forecast that covered them before publication" exists wherever prices come from a
once-daily auction. The decay runs in days since that publication, not in clock hours or CET; the
shift is additive in the caller's currency on the component the forecast covers; tariffs, taxes and
VAT are added afterwards by that market's adapter; and every default is relative (the weights) while
every amount (a markup) is set by the caller in its own units ([forecast note §3][fb]).

**Other grid companies and markets break rules, not the contract.** Weekday-dependent rows,
month-only cuts, missing low-load blocks, flat tariffs and moved period boundaries all reduce to one
duty: read the dated row for each slot's local date and clock hour, keyed on the company's GLN and
charge type code, never a rule. Three changes ahead would break the one-price-per-slot contract
itself. Tarifmodel 3.0 is reported to apply until 2027 with no household successor found, and N1 has
notified a dynamic capacity payment for larger consumers; a household capacity term would make a
slot's cost depend on power and on the rest of the house ([review §3][rv]). The fuse and base load
already cap available power. And solar makes the first kWh in a sunny hour cost the lost export
value, a piecewise price `PricePoint` cannot carry. Reserving an **optional per-slot power ceiling**
now covers the first two; solar needs its own decision.

**What holds across places and billing, and what is specific.**

| Finding | DK1/N1 | DK2/Radius | SE3 model (spot × 1.25, no tariff) | Hourly and quarter billing | Status |
|---|---|---|---|---|---|
| Ordering P0 ≫ P1 > P2 > forecast policies > foresight | ✓ | ✓ | ✓ (no forecast policies run) | ✓ | **General** |
| DP adds no money over the corrected greedy | ✓ | ✓ | ✗: DP gains 74–198 DKK/yr from negative totals | ✓ | General wherever totals carry tariffs or flat charges |
| N8 proxy needed | +21 to +147 DKK/yr | +7 to +135 | 0 to +62 | ✓ | **General** |
| Ceiling dominates the forecast policies | ✓ | ✓ | not run | ✓ | General where forecasts exist |
| Composition faults outweigh algorithm choice | ✓ | ✓ | (tariff faults n/a) | ✓ | General |
| Order of forecast methods: decaying anchor ≥ raw ≫ shape/rank only | ✓ | ✓ | not run | hourly only | General in sign, one month |
| Timer's loss against P2 | 1,484–2,292 DKK/yr | 1,337–2,093 | 787–986 (about half; no night tariff) | ✓ | **Size specific** |
| Forecast gain under the ceiling | 44–52 DKK per 31 days | 58–86 (about 40 % larger; more biased forecast) | not run | — | **Size specific** |
| Zero cost of stale-season and DST-position faults | ✓ | not measured | n/a | — | **N1-specific**: a company with a boundary at 02–03 or a season-dependent low rate would pay |
| Absolute DKK amounts, swing 0.88 DKK/kWh, rows to 2028 | ✓ | swing 1.06 | — | — | **N1-specific** |
| 2027 period shifts, three charge owners under one name | ✓ | — | — | — | **N1-specific** |
| Bias size −16 to −22 % of spot (DK1), −25 to −34 % (DK2) | ✓ | ✓ | — | — | One provider, one rising month |

Sources: [replay, places][rp]; [forecast note §1–§3][fb]; [review §2][rv]. The SE3 column models no
real Swedish grid company; it shows what happens when the night is not systematically cheapest.

## Conclusion

The new evidence moves the weight of the work further from the optimiser. The earlier report said
the price adapter was worth more than the planner's sophistication; the replay now prices that
claim, and it holds by an order of magnitude. Each of three composition faults costs 60–165 DKK a
year, two unmeasured adapter gaps are blocking, and a late publication without the N8 proxy can cost
thousands, while the DP and the corrected greedy are indistinguishable wherever Danish tariffs sit in
the price. The planner's real settings are not algorithmic but behavioural: how much stock it may
hold above the wear step decides most of the forecast money, and that is a battery question still
answered by reasoning on lab cells.

The maintainer's intuition about forecasts survives, but in a sharper form than "low but right on
trend". The useful information is **the forecast's own recent miss**: its error on the day just
published predicts its error on the next two or three days, and correcting with that, fading to
nothing within a week, is the trend view made usable. Throwing the level away to keep only the
shape loses more than the bias costs. Because the correction needs memory of the pre-publication
forecast and knowledge of which part of the price is uncertain, it belongs in a pure library helper
the integration calls, not in the engine, and it can be written once for every bidding zone. The
cheapest evidence left is the maintainer's own Carnot log, provided it records the forecast he held
just before each publication.

## Decision register, updated

Verdicts: **confirm** (the earlier recommendation stands as written), **amend** (it stands with the
change shown), **revise** (the recommendation itself changes), **new**. "Earlier recommendation" is
the earlier report's, abbreviated.

| ID | Earlier recommendation | New verdict | Change | Confidence |
|---|---|---|---|---|
| D3 | `price` = marginal cost per wall kWh, all components incl. VAT, same basis known and forecast | amend | `price` is the **billed** price of the settlement period containing the slot; KNOWN or EXPECTED kind; EDS verified to compose forecasts on the same basis when tariffs are on | High |
| D4 | Engine defaults for markup, start cost, ceiling, terminal value empty or `None` | confirm | Also the anchor's decay weights may have relative defaults; no amounts | High |
| D10 | Pure function; plan lock and hysteresis in the caller | amend | The pre-publication forecast snapshot and the anchor computation are caller state, via the library helper outside `plan()` | High |
| D11 | API checks continuity, mixed slots, DST, overdue targets | amend | Grid from the union of slot boundaries; step mapping; no interpolation | High |
| D13 | Tariffs composed by the caller | amend | Plus the product type, dated tariff rows keyed on GLN and charge code, and unit/VAT normalisation (see the checklist) | High |
| D14 | Greedy and brute-force DP live in the tests | confirm | — | High |
| D16 | Optional `charging_overhead_kw`; wall-side curves | amend | Plan on measured session power (a low percentile) from the first week; add a one-phase case | Medium |
| D19 | Replace with soft `start_overhead_kwh` | revise | Lower priority: cost effect −3 to +1 DKK a month; on quarter-hours it raised starts. Adopt only with "on" meaning "charging to the slot's end" and a SoC grid that fits the slot | Medium-low |
| D20 | Additive markup keyed on lead from the last published slot; large first step | amend | Additive and keyed on `start − origin` confirmed; the systematic error belongs to the anchor, the markup only to residual uncertainty; motor.md §6.4's percentage formula and O4's wording must be rewritten | High (shape) |
| D22 | DP replaces pass 2 if D19/O1 terms adopted; else corrected greedy | revise | Prefer the **corrected greedy** with soft targets and the ceiling; the replay shows it carries them with no money lost. Keep the DP as a test oracle and as the option if a wear or start term proves necessary | Medium |
| D25 | Negative prices supported; no special rule | amend | Where totals go negative (tariff-less markets), the DP's ability to value free energy is worth 74–198 DKK a year; in Danish totals nothing | Medium |
| D27 | Caller expands usual departures over the horizon | confirm | The replay used it with 0 missed hard targets | Medium-high |
| D28 | Remove the charger's low-price automation | confirm | Not re-examined | Medium |
| O1 | Soft demands, concave stored value, surplus ceiling 55–60 % | amend | Money now measured: forecasts add 44–52 DKK per 31 days in DK1 (58–86 in DK2) under the ceiling, about three times that without it | Medium (mechanism); low (annual money, ceiling value) |
| O3 | Naming pass after these decisions | amend | Include `kind`, `origin`, `spread`, and the orphans the removals leave (see N9, N13, N15) | — |
| O4 | Step table; integration ≈0.08 DKK/kWh, 0.10 from D+4, uncalibrated | revise | Integration default **0** while the anchor is on; the step table stays, keyed on lead from `origin`, calibrated from the Carnot log | Medium |
| O6 | Partly answered | amend | Refuse a slot without a covering tariff row or price it pessimistically and flag it; refuse a source of unknown unit or VAT state | High |
| O8 | DP precision knob `soc_resolution_kwh` = 0.25 | revise | The grid must be a whole fraction of one slot's full-power energy (e.g. 0.2475 kWh at 9.9 kW), or reach must not be floored per slot | High |
| O10 | Warn on safety ≥ arrival; markup additive and non-negative | amend | Add markup unit check against the price source | High |
| O11 | `PricePoint` gains `end`; mixed 15/60 slots; ≈50 ms budget | amend | Confirmed; budget holds on average only (15–47 ms mean, up to 130 ms on quarter-hours, desktop); Pi untimed | High (contract); medium (budget) |
| S1 | MAE 23–38 % of the mean | revise | 23–32 % (backtest); live MAE now 354–532 DKK/MWh, bias −210 to −307 (DK1), one rising month | Medium |
| Summary | Timer worth 600–1,100; ranking 470–630 | revise | Quarter billing: 730–1,090 and 470–630. Hourly billing (maintainer): ≈1,090 and ≈410 at 6 kWh a night; ranking up to 1,300–2,300 when the car is home in the daytime | High |
| N1 | `price` is the total on one basis; integration refuses mixed bases | amend | Add unit and VAT normalisation and tariff-coverage checks as integration duties; EDS is on the same basis with tariffs on | High |
| N2 | `PricePoint(start, end, price, is_forecast[, markup])` | revise | `PricePoint(start, end, price, kind, origin, spread)`; billed-period price; mixed slot lengths | High |
| N3 | Additive markup keyed on lead from last published slot; engine default empty | confirm | Lead measured from `origin` | High (shape) |
| N4 | Partial slot = most expensive chosen, full power, late start; ties later | confirm | The replay's corrected start rule (only a session's first slot starts late) is the execution rule | High |
| N5 | `start_overhead_kwh` replaces `min_session_kwh` | revise | As D19 | Medium-low |
| N6 | Optional `charging_overhead_kw` | confirm | — | Medium |
| N7 | Overdue targets accepted (`TARGET_OVERDUE`) | confirm | — | High |
| N8 | Plan covers all time; pessimistic proxy for unpriced slots | confirm | Now measured: +21 to +147 DKK/yr without it at 13:00 publication, thousands if prices arrive at midnight | Medium-high |
| N9 | Control = windows + `should_charge_now`; car commands leave | amend | Name the orphans: motor.md §6.1 step 2, `requires_wakeup`, `STALE_SOC_NEEDS_WAKEUP`, the three wake tunables, §5 `actions` made informational | High |
| N10 | Soft targets never make the plan `PARTIAL` | confirm | 0 missed hard targets in the replay | Medium |
| N11 | Optional `surplus_max_soc`, integration default 55–60 % | amend | The single largest forecast lever: ≈70–110 DKK a month in an October-like month against none. Show its cost to the user; the default remains a wear judgement | High (that it is the lever); low (right value) |
| N12 | Concave `stored_energy_value_steps`; a user threshold is one step | revise | State a user threshold relative to tonight's prices, or accept re-entry at every tariff change | Medium |
| N13 | `min_idle_soc` a floor at every departure; deadline at expected plug-out | amend | State what becomes of `idle_planning_horizon_hours`; idle floor 30–50 % moved 0 DKK for commuters | Medium |
| N14 | Exact DP once N5, N10–N12 are in | revise | As D22: corrected greedy as the planner; DP as oracle; if adopted, a fitting SoC grid | Medium |
| N15 | `soc_source` replaces `soc_last_updated` | amend | Say whether `soc_max_age_minutes` survives | High |
| N16 | Danish defaults in the integration, labelled uncalibrated | amend | Markup default 0 (not 0.08); ceiling 55–60 % | High |
| N17 | Log prices, forecast runs, charger and car data from the first release | revise | Drop the recorder idea (EDS excludes `forecast`); log every forecast run with its fetch time, and a pre-publication snapshot daily | High |
| N18 | — | new | TREND is not an engine price kind. A pure library helper outside `plan()` turns a forecast or trend into EXPECTED by an additive anchored shift on the uncertain component, fading over about four days (1, .75, .5, .25, 0); with no anchor it returns the forecast unchanged, never a shape-only guess | Medium (mechanism); low (weights) |
| N19 | — | new | The integration snapshots the forecast it holds just before each publication, for the slots that publication covers, and keeps it as the anchor and as calibration data | High |
| N20 | — | new | The plan is re-run on every publication event (a forecast slot replaced by a known one), and a late or decoupled day is a test case | High |
| N21 | — | new | Under hourly billing, the hourly price is the timestamp-keyed mean of the four quarters; under quarter billing, the quarters. The product type (spot hourly, spot quarter, fixed, monthly average) is an adapter setting | High |
| N22 | — | new | Tariffs are read as dated hour-by-hour rows by local date and clock hour, keyed on GLN plus charge type code; never periods or seasons by rule; a row whose boundaries differ from the previous row's is flagged | High |
| N23 | — | new | The markup is stored in one canonical unit (currency per kWh incl. VAT) and converted to the price source's unit and VAT basis; a source whose unit or VAT state cannot be established is refused | High |
| N24 | — | new | A slot with no covering tariff row is never priced at tariff 0: it is refused or priced pessimistically and flagged | High |
| N25 | — | new | Reserve an optional per-slot power ceiling in the contract, for the fuse and base load and a possible post-2027 capacity term | Medium-low |
| N26 | — | new | Solar self-consumption's piecewise price needs its own contract decision before solar is built; one price per slot cannot carry it | Medium (that it is needed) |
| N27 | — | new | Verify the maintainer's settings once at setup: N1 charge owner area, EDS tariffs on, VAT, unit, and 60-minute resolution | High |

## The price adapter's duties

The review found the blocking issues here, and the replay found the adapter's faults costlier than any
planner choice. Every item applies to any market unless marked.

- [ ] **Normalise unit and VAT.** Read the source's unit (currency, øre or kroner, per kWh or MWh) and
  its VAT state; convert the markup from its canonical unit; refuse a source whose VAT state cannot be
  established (EDS does not expose it). *Blocking.*
- [ ] **Never price a slot at tariff 0.** Check that a grid-tariff row covers every slot; otherwise
  refuse it or price it pessimistically and flag it. *Blocking for EDS users whose company publishes
  late.*
- [ ] **Read tariffs as dated rows** by the slot's local date and clock hour, keyed on GLN plus charge
  type code, with overlapping rows summed (N1's `CD` and rebate `CD R`); never hardcode periods or
  seasons; flag boundary changes. (Denmark.)
- [ ] **Pass the billed price.** Hourly billing: the mean of four quarters, averaged by timestamp, not
  position. Quarter billing: the quarters. Check that EDS's `resolution` option matches the product.
- [ ] **Know the product type**: spot per hour, spot per quarter, fixed price or monthly average.
- [ ] **Use timestamped data only.** Ignore index-based attributes (`today`, `tomorrow`); check dates;
  handle 23- and 25-hour days and a missing tomorrow at midnight.
- [ ] **Keep one basis** for known and expected prices; refuse to join a spot-only forecast to totals.
- [ ] **Snapshot the pre-publication forecast** each day before about 13:00 local (EDS drops tomorrow's
  forecast once real prices are valid), and log every forecast run with its fetch time.
- [ ] **Anchor the forecast** through the library helper, on the spot component, before adding tariffs
  and taxes; set `origin`; pass `spread` only if the band is trusted.
- [ ] **Re-plan on publication**, and price tomorrow from the forecast plus the N8 proxy until it
  arrives; treat a delay past plug-in as a normal case.
- [ ] **Fill unpriced time** with tariff plus a pessimistic spot proxy as EXPECTED (N8).
- [ ] **Shape daily-level forecasts** into slots with an hourly or last-known-day shape plus the dated
  tariff; never pass a flat daily total.
- [ ] **Treat the forecast's sign as unknown**: it was too high on cheap windy days; apply no fixed
  upward correction.
- [ ] **Verify the charge owner** once (N1 alone publishes under areas 131, 016 and 344). (DK1/N1.)
- [ ] **Leave room for a per-slot power ceiling** (fuse, base load, a future capacity term), and for a
  solar caller's piecewise price.

## What remains to be measured

| Measurement | Source | Settles | When |
|---|---|---|---|
| His N1 charge owner (area 131, 016 or 344), supplier, product, and EDS settings: tariffs on, VAT, unit, resolution | Bill, Eloverblik, EDS options | Mechanisms 1, 2, 5, 8, 11; N27 | Now |
| **Carnot log**: every run with its fetch time, and the pre-publication snapshot of tomorrow | Integration log (EDS excludes the recorder) | Everything below on Carnot | From now |
| From the Carnot log: signed bias by lead day from `origin`, by hour of day and by forecast level; whether it is "always lower" or, as with elpriser.org, too high on cheap days | Carnot log against `DayAheadPrices` | Whether the anchor is needed for his source | A month for a first look; both seasons by about April 2027 |
| From the Carnot log: correlation of the latest miss with the next days' errors | Same | Decay weights for N18 | Two to three months |
| From the Carnot log: decaying anchor against raw against markup in the rolling replay | Replay harness with his runs | O4 size; N18 default | After a season |
| From the Carnot log: Carnot's time resolution, whether its value is a mean or median, and what happens to tomorrow's values after 13:00 | Log | Helper inputs; anchor timing | Weeks |
| The decaying anchor (c_decay) inside the end-to-end replay, with and without the ceiling; per-hour anchoring; a 0.7/0.3 blend with a 14-day mean; anchor plus markup | Existing replay on the elpriser archive | Whether the forecast note's lead survives the realistic setting | Desk work, now |
| A calm month, summer, and a falling-price regime for elpriser.org | elpriser archive (400 days from 2026-10-06) | Whether the bias reverses when prices fall; year-round forecast gain | April 2027; a full year by October 2027 |
| Whether N1 intends its 2027 rows | N1 | Spring 2027 hours; experiment tariffs | Now |
| Wear value of stock above 55–60 % on MEB cells | Literature or long-term data; none found | The ceiling's value (N11), the largest forecast lever | Open |
| Session power, per-phase current and taper; one-phase case | Maintainer's charger | D16; mechanism 12 | Weeks |
| Plan time on a Raspberry Pi-class host, greedy and DP, hourly and quarter | Maintainer's HA hardware | O11 budget; D22/N14 | Now |
| A second grid company per area, including one with a boundary at 02–03 or a season-dependent low rate | DataHub rows in the replay | Whether DST and stale-row faults cost money elsewhere | Desk work |
| A real late or decoupled publication | Logged event | N20 behaviour | When it happens |
| How DataHub encodes a 25-hour day in 24 tariff columns | DataHub | DST handling | Desk work |
| Successor to Tarifmodel 3.0; elafgift from 2028 | Grid companies, Skat | N25 | 2027 |
| Danish suppliers offering quarter-hour products, and any with an hour-varying markup | Supplier terms | Product setting; whether ranking changes | Desk work |

[rv]: ../research_notes/Forecast%20price%20types%20and%20replay/report_review.md
[fb]: ../research_notes/Forecast%20price%20types%20and%20replay/forecast_bias_and_price_types.md
[rp]: ../research_notes/Forecast%20price%20types%20and%20replay/end_to_end_replay.md
[mm]: ../motor.md
[dec]: ../decisions.md
