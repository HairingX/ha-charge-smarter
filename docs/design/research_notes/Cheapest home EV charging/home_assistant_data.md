# What Home Assistant integrations actually give a charging planner (S3)

Researched 2026-10-28. Every finding below comes from a page, a source file or an API document
that was opened during this task; the URL is given. Source files were read from the integrations'
repositories through `raw.githubusercontent.com`, from the branch named in the URL, on that date.
GitHub's own HTML pages and API could not be reached from this session, so release pages,
issue trackers and star counts were **not** examined. Anything marked "Reasoning" is not a sourced
fact.

Versions seen: Home Assistant 2026.10.4 is the newest release and 2026.11.0b0 the newest beta on
PyPI ([PyPI homeassistant](https://pypi.org/pypi/homeassistant/json)); Energi Data Service 1.6.22;
Strømligning 1.2.0; Monta (hass-monta) 1.3.0; Home Assistant core `skoda` on `dev` pins
`skoda-public-api==1.3.0`; core `nordpool` on `dev` pins `pynordpool==0.4.0`.

## Price integrations: what they expose and how to read them

### Takeaway
Since 1 October 2025 the day-ahead market in Europe has used 15-minute slots. Home Assistant's
price integrations handle this in different ways. Core Nord Pool's actions return 15-, 30- or
60-minute prices on request, but its price excludes VAT and tariffs. Energi Data Service averages
to hourly prices by default, with 15-minute prices as an option; it can add Danish grid tariffs
and VAT, and it can add a Carnot forecast that needs an API key. Strømligning shows the Danish
total price, and its forecast sensors carry only the spot price. Tibber's action returns
`price_total` (energy plus taxes). The engine's assumption of hourly prices (§4.5, O11) is
already out of date. No two integrations expose prices in the same format, so the integration
needs one adapter per source.

### Cited Findings
**Market resolution**
- Nord Pool lists "European 15-minute MTU go-live: 30 September 2025" for the Single Day-ahead Coupling. The page does not name DK1/DK2 separately — [Nord Pool, transition to 15-minute MTU](https://www.nordpoolgroup.com/en/trading/transition-to-15-minute-market-time-unit-mtu/).

**Home Assistant core Nord Pool (`nordpool`)**
- Introduced in HA 2024.12. Sensors: current, previous and next price, daily average, lowest and highest price (start and end in attributes), peak and off-peak block sensors (disabled by default), and diagnostics including a "Tomorrow price available" binary sensor — [HA docs: Nord Pool](https://www.home-assistant.io/integrations/nordpool/).
- "VAT and other additional costs are not included". The docs show template sensors that add fixed costs and VAT — [HA docs: Nord Pool](https://www.home-assistant.io/integrations/nordpool/).
- The sensors carry no full price list. To get the prices for a day, call the action `nordpool.get_prices_for_date`, which returns currency/MWh (the docs divide by 1000 to get kWh). There is also `nordpool.get_price_indices_for_date` — [HA docs: Nord Pool](https://www.home-assistant.io/integrations/nordpool/).
- The docs still say the sensors show the "current (hourly) energy price" and will "automatically switch and use the 15-minute MTU" — [HA docs: Nord Pool](https://www.home-assistant.io/integrations/nordpool/). The code on `dev` is newer than this text. The price-indices action takes `resolution` 15, 30 or 60, default 60 ([services.py](https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/nordpool/services.py), [services.yaml](https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/nordpool/services.yaml)). The coordinator fetches every 60 minutes and "Update[s] entity listeners every 15 minutes" ([coordinator.py](https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/nordpool/coordinator.py)).

**Energi Data Service (HACS, MTrab/energidataservice, v1.6.22)**
- A single sensor whose state is the current price. The other slots are in attributes: `today`, `tomorrow`, `raw_today`, `raw_tomorrow` (objects with a timestamp and a price), `tomorrow_valid` ("Prices will be released between 13:00 and 14:00"), `next_data_update`, `forecast` (only with Carnot), `tariffs` and `net_operator` (only with automatic tariff data) — [README](https://raw.githubusercontent.com/MTrab/energidataservice/master/README.md).
- Options: add VAT; an additional-costs Jinja2 template; "Automatically fetch tariff data" from the selected net operator, available for Denmark; Carnot forecasts ("5 day price forecast for the next week thru Carnot.dk", which "requires registration and API key from Carnot - this is free of charge") — [README](https://raw.githubusercontent.com/MTrab/energidataservice/master/README.md).
- The attribute objects use the keys `"hour"` and `"price"` — [sensor.py](https://raw.githubusercontent.com/MTrab/energidataservice/master/custom_components/energidataservice/sensor.py).
- The README still describes `raw_today` as "24 objects … each hour". The code has a `resolution` option. With the default `True`, each 4 quarter-hour prices from Energi Data Service's `DayAheadPrices` dataset are averaged into one hourly price; otherwise every quarter-hour is kept — [connector code](https://raw.githubusercontent.com/MTrab/energidataservice/master/custom_components/energidataservice/connectors/energidataservice/__init__.py), [const.py](https://raw.githubusercontent.com/MTrab/energidataservice/master/custom_components/energidataservice/const.py). The sensor state changes every 15 minutes (`minute="/15"`) and Carnot is fetched every 30 minutes — [__init__.py](https://raw.githubusercontent.com/MTrab/energidataservice/master/custom_components/energidataservice/__init__.py).

**Strømligning (HACS, mtrab/stromligning, v1.2.0)**
- "Automatically recognises tariff settings from the Home Assistant home location coordinates" and lets the user select their electricity vendor. Requires HA 2024.12+. Has sensors for the current price with and without VAT, the spot price, electricity tax, surcharges, the system tariff, today and tomorrow min/max/mean, and `price_resolution` — [README](https://raw.githubusercontent.com/mtrab/stromligning/main/README.md), [sensor.py](https://raw.githubusercontent.com/mtrab/stromligning/main/custom_components/stromligning/sensor.py).
- Forecasts are an option. `forecasts_vat` / `forecasts_ex_vat` start the day after tomorrow. The newer `forecasts_spotprice_vat` / `_ex_vat` hold a `prices` attribute of `{price, start, end}`, in which "Tariffs, taxes, and supplier surcharges are excluded". A forecast sensor's state is its last successful update time, not a price — [README](https://raw.githubusercontent.com/mtrab/stromligning/main/README.md).

**Tibber (core)**
- The sensor's current price is "The total price (energy + taxes)", with `max_price`/`min_price` attributes. Prices for a range come from the action `tibber.get_prices`, which the docs describe as fetching "hourly Tibber energy prices for a date range" — [HA docs: Tibber](https://www.home-assistant.io/integrations/tibber/).
- The action returns `{start_time, price}` from `price_total` for each home, for today and tomorrow only, and filters to `[start, end)` — [services.py](https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/tibber/services.py).
- Through Tibber's Data API, the integration also exposes binary sensors "Charging" and "Plug" for chargers and for EVs, plus storage SoC/target SoC, remaining range and max/offline-fallback charging current — [HA docs: Tibber](https://www.home-assistant.io/integrations/tibber/).

**Other**
- EV Smart Charging, a HACS planner, reads the HACS Nord Pool, Energi Data Service, GE-Spot, Entso-e and TGE integrations natively. It needs a template sensor to read core Nord Pool, "supports price information given with 15 minutes and 60 minutes intervals", and defines a generic format: `prices_today` / `prices_tomorrow` lists of `{time, price}` — [README](https://raw.githubusercontent.com/jonasbkarlsson/ev_smart_charging/main/README.md), [Price-sensor wiki](https://raw.githubusercontent.com/wiki/jonasbkarlsson/ev_smart_charging/Price-sensor.md).
- The 2026.10 release added Zonneplan (Dutch dynamic prices) — [HA 2026.10 release notes](https://www.home-assistant.io/blog/2026/10/07/release-202610/). No new Danish price integration was found in those notes.

### Inferences
- Reasoning: §4.5's assumption of "one per hour" no longer matches the data. Denmark's day-ahead price has been per 15 minutes since October 2025, and two of the four sources can deliver it. O11 should be decided rather than left open. The simplest fit is a `PricePoint` with `start` and an explicit `end` (or a duration), with the API layer checking that the series is continuous. Hourly data then remains a special case.
- Reasoning: for a Danish user, the price that should rank slots is the total price including grid tariff and taxes. The tariff (for example the 17–21 peak) changes which hours are cheapest. Energi Data Service with automatic tariffs, Strømligning and Tibber deliver totals. Core Nord Pool does not, so the integration would have to add tariffs itself. Under D13 that work belongs in the caller, not the engine. The adapter should record per source whether its price is a total or the spot price only.
- Reasoning: forecasts mix price bases. Energi Data Service's `forecast` follows its own settings (the tariffs presumably are not in Carnot's figure, which was not verified in code). Strømligning's spot-price forecast explicitly excludes tariffs. If a total price is joined to a spot-only forecast, the series shows a false cliff at the joint. The adapter must put both on the same basis (add tariffs to the forecast) before `is_forecast=True` points reach the engine. This also bears on S1/O4, because the markup would apply to a different quantity.
- Reasoning: reading `raw_today`, `raw_tomorrow` and `forecast` attributes, or calling an action with `return_response`, gives one list per refresh. The integration should re-read the list on a price-entity state change and when tomorrow's prices become valid (`tomorrow_valid` or "Tomorrow price available"). Re-reading on every call is unnecessary.

### Gaps
- Not checked in code: whether core Nord Pool's `get_prices_for_date` returns 15-minute entries for DK1/DK2 today. The docs and the code disagree on wording.
- Carnot's horizon in hours, and whether its values include tariffs or VAT: not verified beyond the README's "5 day" text.
- Tibber in Denmark: whether `price_total` includes the DSO grid tariff was not found. The HA docs say only "energy + taxes".
- Not examined: GE-Spot, Entso-e and the HACS `custom-components/nordpool` attributes (the README was downloaded but not reviewed).

## Charger integrations: what can be read and controlled, latency, limits, and charger-side automation (D28)

### Takeaway
All the chargers reach Home Assistant through cloud APIs or local protocols, and none exposes
a common "EV charger" entity. Each has its own vocabulary for start/stop and for current. The
reliable control primitive is usually a current limit or pause/resume, not start/stop. The
charger side is the most dependable source of "plugged in" and "charging" for an Enyaq, because
it is pushed or polled within seconds to minutes. Several chargers have their own schedules or
price-based smart charging, which can fight an external planner.

### Cited Findings
**Easee (HACS, nordicopen/easee_hass)**
- Status values: `disconnected, awaiting_start, charging, ready_to_charge, completed, error` — [README](https://raw.githubusercontent.com/nordicopen/easee_hass/master/README.md). Entities include `power`, `session_energy`, `output_current`, `dynamic_charger_limit`, `reason_for_no_current`, `smart_charging`, `cost_per_kwh`, and schedule state — [const.py](https://raw.githubusercontent.com/nordicopen/easee_hass/master/custom_components/easee/const.py).
- Data is pushed from Easee's cloud over SignalR: "it is not possible to change how often data updates"; "polling the API too often usually leads to being locked out for a time period" — [wiki: UpdateFrequency](https://raw.githubusercontent.com/wiki/nordicopen/easee_hass/UpdateFrequency.md). "Not possible to have more than 5 sites active" because of API call limits — [wiki: Limits](https://raw.githubusercontent.com/wiki/nordicopen/easee_hass/Limits.md).
- Control: `easee.action_command` with `start, stop, pause, resume, toggle, … override_schedule, …`, together with basic and weekly charge plans, dynamic, max and offline circuit and charger limits, phase mode and surplus charging — [services.yaml](https://raw.githubusercontent.com/nordicopen/easee_hass/master/custom_components/easee/services.yaml).
- "Pause and resume are the commands you should use, not start and stop. Start and stop controls authentication…". A dynamic circuit limit below 6 A pauses charging. The charger dynamic limit "is automatically reset when a new charging session is started". Use only the "dynamic" limits regularly, because others are written to flash. The "smart charging" switch "only changes the color of the LEDs" — [wiki: ChargingControl](https://raw.githubusercontent.com/wiki/nordicopen/easee_hass/ChargingControl.md). Easee's own docs: "enabling the smart charging LED, will disable any basic or weekly plans" — [Easee developer: smart charging](https://developer.easee.com/docs/api-smart-charging).

**Zaptec (HACS, custom-components/zaptec)**
- Cloud API. Start and stop through "Stop charging" and "Resume charging" buttons (the services are deprecated). "Resume" "will only start charging if the charger was stopped by a 'Stop charging' command"; it fails after a 0 A limit, a stop from the car's app, or a stop outside the charger's own schedule. "Zaptec will by default start charging as soon as everything is ready". To prevent auto-start: delay authorisation or set the current to 0 A. "Zaptec recommends not changing the values more often than every 15 minutes." The Energy Meter entity is "delayed by 1 hour". Custom poll intervals "will have unexpected effects" — [README](https://raw.githubusercontent.com/custom-components/zaptec/master/README.md).

**Wallbox (core, since 2021.6)**
- Sensors for added energy, charging power, status description, max charging current and a "State of charge (%)" sensor. Numbers for max charging current and energy price, a pause/resume switch, a select for solar charging, and a "Resume schedule" button that resumes "the charger's programmed schedule and EcoSmart mode after a manual stop". "Data is refreshed once every 90 seconds … chosen in conjunction with Wallbox … Altering this refresh rate is not recommended." — [HA docs: Wallbox](https://www.home-assistant.io/integrations/wallbox/).

**go-e (HACS, marq24/ha-goecharger-api2)**
- Local HTTP APIv2 or WebSocket (local or cloud). With WebSocket "you will get the latest data in HA as soon as something changes". When polling with no car connected it enters a hibernation mode and does a full read only "every 5 minutes". It has an `awc` field, "awattar country (Austria=0, Germany=1)", for the charger's built-in price mode — [README](https://raw.githubusercontent.com/marq24/ha-goecharger-api2/main/README.md).

**OCPP (HACS, lbbrhzn/ocpp)**
- A local central system for OCPP 1.6j, 2.0.1 and 2.1 (experimental) — [README](https://raw.githubusercontent.com/lbbrhzn/ocpp/main/README.md). The status covers Available/Preparing/Charging/`SuspendedEV` ("The EV has paused energy transfer (e.g., target SoC reached, schedule, thermal limit)")/`SuspendedEVSE`/Finishing. The Charge Control switch remote-stops; turning it on "does not force a new session to start". Maximum Current is station-wide and Session Current Limit per connector. Measurands depend on the charger, and "Some of these sensor entities will give erroneous readings whilst others give no readings at all" — [OCPP user guide](https://home-assistant-ocpp.readthedocs.io/en/latest/user-guide.html), [OCPP docs index](https://home-assistant-ocpp.readthedocs.io/en/latest/).
- Easee chargers can be pointed at this local OCPP server (`easee.set_charger_ocpp`), which is experimental. Once that is set, the charger "will no longer start automatically but will rely on the OCPP server" — [wiki: LocalOCPP](https://raw.githubusercontent.com/wiki/nordicopen/easee_hass/LocalOCPP.md).

**Monta (HACS, nickknissen/hass-monta, v1.3.0)**
- Platforms: binary_sensor (`cable_plugged_in`), sensor (charger state, charge state, meter reading, charge cost), switch, and the services `start_charging` / `stop_charging`. The public API is in beta. "Last Meter Reading" refreshes only after unplugging — [README](https://raw.githubusercontent.com/nickknissen/hass-monta/main/README.md), [binary_sensor.py](https://raw.githubusercontent.com/nickknissen/hass-monta/main/custom_components/monta/binary_sensor.py), [services.yaml](https://raw.githubusercontent.com/nickknissen/hass-monta/main/custom_components/monta/services.yaml). The default charge-point poll is every 120 s — [const.py](https://raw.githubusercontent.com/nickknissen/hass-monta/main/custom_components/monta/const.py).
- Monta's own smart charging schedules "the cheapest … windows before each driver's departure time" and "pulls spot electricity prices … every 15 minutes" — [Monta: smart charging](https://monta.com/en/energy-and-grid-services/smart-charging/).

**Tibber, Tuya, Peblar (core)**
- Tibber exposes charger "Charging"/"Plug" binary sensors and current numbers — [HA docs: Tibber](https://www.home-assistant.io/integrations/tibber/). HA 2026.10 added Tuya EV chargers ("charging current, charging mode, and session energy") and Peblar session authorisation — [HA 2026.10 release notes](https://www.home-assistant.io/blog/2026/10/07/release-202610/).

**Clever**
- No Home Assistant integration for Clever chargers was found. One web search found only an unrelated "Cleverio" forum thread.

### Inferences
- Reasoning: the engine's `START_CHARGING`/`STOP_CHARGING` have to be translated per charger, often into "set the dynamic current to ≥ 6 A / < 6 A" (Easee), "resume/stop button" (Zaptec), "pause/resume switch" (Wallbox), or "charge control switch" (OCPP). Zaptec's "only resume what stop stopped" and Easee's per-session reset of the charger limit mean the adapter must verify after acting (read the status back) and re-assert where needed. This is caller state and retry logic (D10 places it there correctly).
- Reasoning: chargers start charging on plug-in by default (Zaptec explicitly; OCPP's Easee note shows the opposite once under OCPP control). Between plug-in and the first planned window, the integration must actively hold the charge off. That means a STOP or pause action is needed at plug-in, not only at window ends. The action list should allow (or the caller should infer) a "hold" state when `should_charge_now` is false while plugged in.
- Reasoning on D28 (`charger_auto_threshold`): Easee, Wallbox, go-e and Monta all have their own schedules or price modes. Easee's "smart charging" is only an LED, and enabling it disables the plans. go-e's price mode lists only Austria and Germany. The common pattern is that an external planner turns the charger's own automation off rather than sharing control with it. Letting the charger's automation run below a threshold means two controllers each believe they own start and stop. Zaptec's resume rules show how they can block each other. **D28 is weakly supported:** the feature exists on some chargers, but no integration was found that exposes the charger's own price threshold as something HA can read back. Lean: keep `charger_auto_threshold` optional and off by default, and treat it as advanced. Alternatively, drop it from the engine and let the caller express "free charging below X" as ordinary cheap slots (D13). Calling this a recommendation would be reasoning, not a finding.
- Reasoning: `charger_power_session_steps` cannot be read from any integration. Chargers expose a current limit and live power, not a ramp curve. The caller must build it from configuration or from history.

### Gaps
- Easee's official API rate limits: not found on developer.easee.com. Only community claims were seen in search snippets, and they are not used here.
- Zaptec's default poll interval and cloud rate limits: not found in the README.
- Whether Monta's or Clever's smart charging can be switched off or read through their APIs: not found.
- Command-to-effect latency (seconds from a command to the change in power) was not documented for any charger.

## Car integrations: SoC freshness, wake-up, rate limits, charge limit, plugged-in

### Takeaway
For the maintainer's Enyaq, the ground has just moved. The HACS **MySkoda** integration
announces end of life ("will stop working in October 2026"). Its replacement, the **core Škoda
integration**, ships in **HA 2026.11** (currently beta) and is **read-only**. It polls every
5 minutes against a quota of **20 requests per hour per VIN**. It has no wake-up, no refresh, no
start/stop and no charge-limit control, and it does not expose the car's capture timestamp as an
entity. The underlying Škoda Public API does support start/stop, setting the limit
(50–100 % in steps of 10) and the charge mode. It does not support wake-up, and it returns
`carCapturedTimestamp`. Volkswagen's HACS integration has had its authentication blocked again.
Tesla Fleet is the counter-example: it has a wake button, a charge-limit number and a
charge-cable sensor.

### Cited Findings
**Škoda Public API (the official B2C API behind the core integration)**
- "Remote commands let you start and stop charging and air conditioning, set the charging limit (target state of charge) and change the charge mode." For personal use only. Keys are created in the MyŠkoda app and expire (`X-API-Key-Expires-At`) — [MyŠkoda Public API docs](https://public.api.connect.skoda-auto.cz/docs).
- "Requests are rate-limited per VIN. The current limit is 20 requests per hour; this value is not final and may change." Errors count against the quota too. A 429 response is either `rate-limit-exceeded` or `vehicle-not-accepting-requests` ("the vehicle itself declined the operation, for example to limit how often it executes requests or because its battery level is too low") — [docs](https://public.api.connect.skoda-auto.cz/docs), [OpenAPI spec](https://public.api.connect.skoda-auto.cz/v3/api-docs).
- Endpoints: `GET /api/v1/vehicles/{vin}`; `POST …/charging/start|stop`; `PUT …/charging/limit`; `PUT …/charging/mode`; `PUT …/charging-profiles/{id}`. There is **no wake-up or refresh endpoint** — [OpenAPI spec](https://public.api.connect.skoda-auto.cz/v3/api-docs).
- `ChargingLimit.targetStateOfChargeInPercent`: "Vehicles typically accept values between 50 and 100 in steps of 10 and reject other values." — [OpenAPI spec](https://public.api.connect.skoda-auto.cz/v3/api-docs).
- `Charging.carCapturedTimestamp`: "Timestamp when the data was last captured and sent by the vehicle". `BatteryStatus.stateOfChargeInPercent`. `ChargingStatus` has `chargePowerInKw`, `remainingTimeToFullyChargedInMinutes`, `fullyChargedAt` and `chargeType` — [OpenAPI spec](https://public.api.connect.skoda-auto.cz/v3/api-docs).
- `ChargingStatus.state` ∈ `CONNECT_CABLE, CHARGING, CONSERVING, READY_FOR_CHARGING, DISCHARGING, CHARGING_INTERRUPTED`. It "is omitted … for example when the cable is plugged in and unlocked while no charging process runs, or when the vehicle reports its charging status as invalid, for example shortly after a drive … treat an omitted state as unknown". API 1.1.0 added `plugConnectionState` (CONNECTED/DISCONNECTED) and `plugLockState` — [OpenAPI spec](https://public.api.connect.skoda-auto.cz/v3/api-docs), [changelog](https://public.api.connect.skoda-auto.cz/docs/changelog).
- Charging profiles carry `preferredChargingTimes`, `timers`, a profile target SoC, `minBatteryStateOfCharge` ("If battery drop below this value, then start immediate charging") and `maxChargingCurrent` REDUCED/MAXIMUM. Charge modes include `MANUAL`, `TIMER` and `PREFERRED_CHARGING_TIMES` — [OpenAPI spec](https://public.api.connect.skoda-auto.cz/v3/api-docs).

**Home Assistant core `skoda` (Bronze, cloud_polling)**
- "The Škoda device was introduced in Home Assistant 2026.11" — [HA next docs: Škoda](https://next.home-assistant.io/integrations/skoda/). It was not in the 2026.10 release notes (no "Škoda/Skoda" string found) — [HA 2026.10 release notes](https://www.home-assistant.io/blog/2026/10/07/release-202610/). 2026.11.0b0 is on PyPI — [PyPI](https://pypi.org/pypi/homeassistant/json). The library `skoda-public-api` 1.3.0 was released 2026-09-18 — [PyPI](https://pypi.org/pypi/skoda-public-api/json).
- "The integration is read-only. It reports vehicle status but cannot start or stop charging … cannot start, stop, or schedule charging." It "polls the current vehicle status every 5 minutes", and on hitting the per-VIN limit it "waits before attempting to retrieve data again" — [HA next docs: Škoda](https://next.home-assistant.io/integrations/skoda/).
- Code: `_PLATFORMS = [Platform.SENSOR]` only; `UPDATE_INTERVAL = timedelta(minutes=5)` — [__init__.py](https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/skoda/__init__.py), [coordinator.py](https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/skoda/coordinator.py).
- Sensors: mileage, fuel level, `battery_percentage`, ranges, `charging_power`, `charging_state` (enum `charging, connect_cable, ready_for_charging, conserving, discharging, charging_interrupted`), `remaining_time_to_full_battery` (timestamp) and `charge_type`. `carCapturedTimestamp` is used only for auxiliary heating. There is **no last-updated sensor for charging or SoC and no plug binary sensor** — [sensor.py](https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/skoda/sensor.py).

**MySkoda (HACS, skodaconnect/homeassistant-myskoda), end of life**
- "This integration will stop working in October 2026 … The new integration is expected to ship with Home Assistant 2026.10 … the current API will stop working for unofficial third-party clients … later in October" — [README](https://raw.githubusercontent.com/skodaconnect/homeassistant-myskoda/main/README.md). (This contradicts the core docs' "introduced in 2026.11"; see Gaps.)
- What it had, which shows what the Enyaq can do: `car_captured` "Last Updated" timestamp; `charger_connected` binary sensor; `charging` switch (start/stop); `target_battery_percentage` number; `departure_timer_1..3` switches; a `wakeup` button, disabled by default: "Most models have a strict limit on the number of wake-ups allowed before the car must be started, to protect the 12V battery. **USE WITH CARE.**" — [docs/entities.md](https://raw.githubusercontent.com/skodaconnect/homeassistant-myskoda/main/docs/entities.md).
- Push plus pull: MQTT events from the car ("Unlock/Lock/Odometer update/SoC update/GPS update") trigger partial refreshes. There is a full poll after 30 quiet minutes by default (1–1440 configurable). "We never contact your car directly" — [docs/design.md](https://raw.githubusercontent.com/skodaconnect/homeassistant-myskoda/main/docs/design.md), [README](https://raw.githubusercontent.com/skodaconnect/homeassistant-myskoda/main/README.md).

**Volkswagen We Connect (HACS, robinostlund/homeassistant-volkswagencarnet)**
- "Volkswagen has blocked the authentication mechanism once again" (issue #989). The default interval is 5 minutes; "The Volkswagen API has a connection limit of **480 calls per day**" — [README](https://raw.githubusercontent.com/robinostlund/homeassistant-volkswagencarnet/master/README.md).

**Tesla Fleet (core, since 2024.8)**
- Polls "each vehicle every 10 minutes while it's awake", designed to stay within "Tesla's $10 monthly credit". Entities include a **Wake** button, a **Charge limit** number, a Charge current number, a "Charge cable" binary sensor and a Battery level sensor. Polling stops 15 minutes after inactivity so older S/X can sleep; `homeassistant.update_entity` forces a poll — [HA docs: Tesla Fleet](https://www.home-assistant.io/integrations/tesla_fleet/). Teslemetry gained local Bluetooth commands in 2026.10 — [HA 2026.10 release notes](https://www.home-assistant.io/blog/2026/10/07/release-202610/).

**How other planners take SoC**
- EV Smart Charging needs an "EV SOC entity", and warns that if live SoC is not available the user must read its guidance. It suggests an `input_number` helper fed by automation. The target SoC defaults to 100 when not provided — [README](https://raw.githubusercontent.com/jonasbkarlsson/ev_smart_charging/main/README.md).
- evcc's Home Assistant vehicle maps `soc`, `range`, `status` (A/B/C), `limitSoc` (number/input_number), `odometer`, `climater`, `start_charging`/`stop_charging` scripts, `wakeup` (script or button) and `setMaxCurrent`; `capacity` is a number, not an entity — [evcc docs: Home Assistant vehicle](https://docs.evcc.io/en/vehicles/home-assistant).

### Inferences
- Reasoning on the **Enyaq on core HA from 2026.11**:
  - `current_soc`: available (`sensor.*_battery_percentage`).
  - `soc_last_updated`: **not available as an entity**. HA's state timestamps only record when HA saw a change. That can be up to 5 minutes after the cloud got it, and the cloud's value may itself be hours old if the car is asleep. `carCapturedTimestamp` is in the API but not exposed. Lean: request it upstream as a diagnostic timestamp sensor, which is a small change in a Bronze core integration. Until then the adapter falls back to `last_changed`, which is wrong whenever the SoC did not change (an idle, parked car).
  - `is_plugged_in`: derivable from `charging_state != connect_cable`. The API says an omitted state "never means … disconnected", so it becomes `unknown` in HA. The charger's plug state (Easee `status`, Monta `cable_plugged_in`, OCPP status) is more reliable and faster.
  - `is_currently_charging`: `charging_state == charging` from the car, or charger power > 0. Prefer the charger.
  - `battery_capacity_kwh`: not exposed by any car integration seen (evcc too takes `capacity` as configuration).
  - `WAKE_UP_CAR` / `REQUEST_SOC_REFRESH`: **no target in core Škoda**. `homeassistant.update_entity` re-reads the cloud and costs quota (20/h; the built-in poll already uses 12/h). It does not wake the car.
  - `SET_CHARGE_LIMIT`: not in core yet. The API would allow only 50–100 in steps of 10.
  - Start/stop: via the charger.
- Reasoning on **SoC while charging**: the API reports `chargePowerInKw`, `remainingTimeToFullyChargedInMinutes` and `fullyChargedAt`, and MySkoda's design lists "SoC update" events while the car is active. So the car does report SoC during a charge, but at the car's own pace. The engine needs a SoC that it can project between readings. Reasoning: estimate SoC from the charger's session energy since the last reading, `soc + kWh × efficiency / capacity`. The engine's caller, not the engine, should own that estimate under D10.
- Reasoning on the **20 requests per hour budget**: a planner calling `update_entity` "every replan" would exhaust it. The caller must budget refreshes. Charger-side push events (plug, start, stop) should trigger replans, not car polls.

### Gaps
- Whether the old MySkoda API has actually been shut off as of 2026-10-28: could not confirm, because GitHub issues and releases were unreachable. The README says "later in October".
- Whether core Škoda will add control platforms (switch, number) or a captured-timestamp sensor: its `quality_scale.yaml` lists no such rule. No roadmap was found.
- How stale the Enyaq's SoC gets while parked and asleep, measured: no source found. Forum search results (Homey, openHAB) were seen only as snippets and are not used.
- Whether Škoda's 20/h quota is per API key or per VIN across all keys: the docs say "per VIN" in one place and "per key" in the changelog.

## Departure schedules: what users and integrations use

### Takeaway
There is no standard Home Assistant entity for "departure". Planners use a daily completion time
(a `select` or a time entity), a target-SoC `number`, or calendar events. Cars keep their own
departure timers and charging profiles in the vendor cloud.

### Cited Findings
- EV Smart Charging: `select.*_charge_completion_time` ("latest time of the day for charging to reach the target", options "00:00"…"23:45", "None") and `select.*_charge_start_time`. These are daily, not dated — [README](https://raw.githubusercontent.com/jonasbkarlsson/ev_smart_charging/main/README.md).
- Calendar: the `calendar.get_events` action ("Gets the events on a calendar within a date range") and calendar triggers with an `offset`; "calendars are read once every 15 minutes" — [HA docs: Calendar](https://www.home-assistant.io/integrations/calendar/).
- Car-side schedules: MySkoda had `departure_timer_1..3` switches with the timer configuration in attributes, plus a `set_preferred_charging_time` action ([README](https://raw.githubusercontent.com/skodaconnect/homeassistant-myskoda/main/README.md), [entities.md](https://raw.githubusercontent.com/skodaconnect/homeassistant-myskoda/main/docs/entities.md)). The Škoda Public API exposes the profile `timers` and `preferredChargingTimes` ([OpenAPI spec](https://public.api.connect.skoda-auto.cz/v3/api-docs)). Core Škoda exposes neither ([sensor.py](https://raw.githubusercontent.com/home-assistant/core/dev/homeassistant/components/skoda/sensor.py)).

### Inferences
- Reasoning: D15 and D27 (the caller generates `ChargeTarget`/`AbsenceWindow`) fit. The integration needs at least three sources: (1) a recurring weekday departure (its own `time` entities per weekday, or a select like EV Smart Charging's); (2) a calendar entity read with `calendar.get_events` over the price horizon; (3) a one-off "ready by" `datetime` entity. The 15-minute calendar read interval is fine for a planner.
- Reasoning: the car's own timers (Škoda `TIMER`/`PREFERRED_CHARGING_TIMES` modes) can stop the car from accepting charge outside their windows. The integration should tell the user to set the car to `MANUAL`/immediate and leave the timing to the planner. Today that cannot be checked through core HA, because the charge mode is not exposed.

### Gaps
- No community thread on the patterns people actually use was opened (one search returned nothing relevant). Prevalence is unknown.

## Manual controls: entity conventions to follow (O12)

### Takeaway
The pattern that recurs is: a master `switch` for "smart charging on/off", `button`s for manual
start and stop, `number`s for SoC levels and price limits, a `select` or time entity for times,
and a `sensor` with the plan in its attributes. Core HA has no EV-specific entity platform and no
developer guidance on EV charging.

### Cited Findings
- EV Smart Charging: `switch.*_smart_charging_activated`, `switch.*_apply_price_limit`, `switch.*_low_soc_charging`, `switch.*_low_price_charging`, `switch.*_ev_connected` (fed by automation), `switch.*_keep_charger_on`, `button.*_manually_start_charging` / `_manually_stop_charging` ("totally independent of the automatic charging"), `number.*_minimum_ev_soc`, `number.*_electricity_price_limit`, `select.*_charge_completion_time`. It has a `sensor.*_status` enum (`waiting_for_new_prices`, `no_charging_planned`, `waiting_for_charging_to_begin`, `charging`, `keeping_charger_on`, `low_price_charging`, `low_soc_charging`, `disconnected`, `smart_charging_not_active`) and a `charging_schedule` attribute — [README](https://raw.githubusercontent.com/jonasbkarlsson/ev_smart_charging/main/README.md).
- Wallbox (core) uses a pause/resume `switch` and a "Resume schedule" `button` that resumes the charger's own schedule after a manual stop — [HA docs: Wallbox](https://www.home-assistant.io/integrations/wallbox/).
- Core entity platforms listed for developers include button, calendar, date, datetime, number, select, sensor, switch, time and valve. There is **no EV charger or vehicle platform** — [contributors docs: entities](https://contributors.home-assistant.io/core/entities/entity-class/). The developer blog from January to 28 October 2026 has no EV- or charging-related post among its titles — [contributors blog](https://contributors.home-assistant.io/blog/).
- HA's Energy docs treat prices only as a "schedule or … market price" for the grid cost — [HA docs: Energy grid](https://www.home-assistant.io/docs/energy/electricity-grid/).

### Inferences
- Reasoning for O12: two kinds of manual control are needed, and the D10 split holds. (a) An **override** that bypasses the engine ("charge now" button or switch; "pause" switch). This is pure caller state, persisted across restarts, with an expiry: until unplug, or until the target is reached. (b) **Inputs** to the engine as entities: `number` for `default_target_soc`, `min_safety_soc` and `min_idle_soc`; `datetime` for a one-off "ready by"; `time` per weekday for recurring departures; `select` for the price source or mode. A `datetime` entity fits a dated "ready by" better than EV Smart Charging's daily `select`.
- Reasoning: expose the plan as a `sensor` (enum of `PlanReason`, translated) with windows in attributes, plus a `binary_sensor` "should charge now". A `sensor` "SoC age" helps make staleness visible.

### Gaps
- No architecture discussion (home-assistant/architecture) about an EV charger or vehicle entity was found. One web search returned none, and GitHub could not be browsed directly.

## Mapping to the engine's contract: S3, O7, O12, D10, D28, inputs and actions

### Takeaway
The contract mostly fits reality on the charger side. On the car side, for a current Škoda on
core HA, it assumes freshness signals and car commands that do not exist. Prices need sub-hour
slots now.

### Cited Findings
- All facts used here are cited in the sections above: Škoda read-only, 5-minute poll, 20/h quota, no wake endpoint, `carCapturedTimestamp` not exposed, limit 50–100 in steps of 10; 15-minute prices since 2025-10-01 and Energi Data Service/Nord Pool resolution options; charger push and poll latencies; chargers' own schedules.

### Inferences
Each verdict below is reasoning on the findings above, with the change it suggests.

| Item | Verdict | What should change |
|---|---|---|
| **S3** (how integrations expose SoC, plug, limits, power; how stale SoC gets) | **Answered, in part** | Plug and charging state: take them from the charger. SoC: from the car, and the age is often not available. Record the adapter rule "charger first for plug and charging, car for SoC" in `docs/design.md`. Real staleness figures still need measuring on the maintainer's Enyaq after 2026.11 |
| §4.1 `current_soc` | Supported | — |
| §4.1 `soc_last_updated` | **Contradicted** for core Škoda (no entity); supported by Tesla Fleet only through HA timestamps | Allow `soc_last_updated` to be an estimate: the caller passes the best value it has (captured timestamp → HA `last_changed` → unknown). Consider `soc_is_estimated: bool`, or let the caller pass a projected SoC from charger energy. Ask upstream for a captured-timestamp sensor |
| §4.1 `is_plugged_in` | Supported, best from the charger | Accept tri-state (unknown). Škoda's `charging_state` goes to unknown in everyday cases |
| §4.1 `is_currently_charging` | Supported, best from the charger | — |
| §4.2 `battery_capacity_kwh` | **Silent**: no integration exposes it | User configuration |
| §4.2 `car_power_soc_steps`, `charger_power_session_steps`, `charger_efficiency` | **Silent**: no integration exposes curves or efficiency | Configuration with defaults. A later improvement could learn them from history (charger power against SoC) |
| §4.2 `car_max_soc` | Partly supported: the Škoda API's limit is 50–100 in steps of 10 | If `SET_CHARGE_LIMIT` is ever sent to a Škoda, the caller must round **up** to the step. The engine might take an optional `charge_limit_step` so its planned SoC matches what the car will do |
| §4.2 `charger_auto_threshold` / **D28** | **Weakly supported**: chargers have their own schedules and price modes, but none exposes a readable threshold, and two controllers conflict (Zaptec resume semantics; Easee's LED disables plans) | Keep it optional and off by default, or drop it from the engine and model "free below X" as ordinary cheap slots in the caller (D13). Document that the user must turn off the charger's or car's own timers |
| §4.5 `PricePoint` hourly; **O11** | **Contradicted**: 15-minute market since 2025-10-01; two integrations offer 15 minutes | Decide O11: add `end` (or `duration_minutes`) to `PricePoint` and allow mixed resolutions (15-minute known + hourly forecast). Plan in the finest slot given. Check the 10 ms budget for 4×168 = 672 points (§7) |
| §4.5 `is_forecast` | Supported (Carnot through Energi Data Service, Strømligning forecasts) | The caller must make forecast and known prices the same basis (tariffs) |
| §4.6 `soc_max_age_minutes` = 30 | **Contradicted for Škoda**: with a 5-minute cloud poll and an unknown car capture age, "stale" cannot be judged and cannot be cured | Keep the tunable, but see O7 |
| `WAKE_UP_CAR` | **Contradicted for core Škoda** (no wake); supported for Tesla Fleet; MySkoda's wake button was rate-limited by the 12 V battery | Keep the action. The caller maps it to a no-op and reports `CAR_CANNOT_BE_WOKEN` where there is no target. The engine must not *depend* on waking: see O7 |
| `REQUEST_SOC_REFRESH` | Partly: `homeassistant.update_entity` refreshes the cloud copy only, and costs quota (20/h Škoda) | Caller-side rate budget. A refresh that does not reach the car does not make the reading fresh |
| `SET_CHARGE_LIMIT {soc_limit}` | **Contradicted for core Škoda today**; supported by Tesla Fleet (`number` Charge limit); the API supports it in steps of 10 | Treat it as optional. When there is no car limit, `STOP_CHARGING` at the planned SoC is the fallback, which needs projected SoC between readings (see above). Feeds O9 |
| `START_CHARGING` / `STOP_CHARGING` | Supported through chargers, each with its own primitive (pause/resume, dynamic current, button, switch) | Add a "hold" semantic: while plugged in and not in a window, the caller must actively hold the charge off, because chargers auto-start on plug-in |
| **O7** (stale SoC below `min_safety_soc`: wake first or charge first?) | **Answered by the data, as reasoning**: for an Enyaq on core HA, waking is impossible, so "wake first" would never charge | Charge first: if the last known SoC (however old) < `min_safety_soc` and the car is plugged in, charge. Staleness should lower confidence, not block action. `STALE_SOC_NEEDS_WAKEUP` should not stop the plan; issue the refresh *alongside* a plan made on the last known value |
| **O12** (manual controls) | Conventions found (EV Smart Charging, Wallbox) | A `switch` for smart charging on/off; a `button` (or `switch` with expiry) for "charge now"; a `switch` "pause"; `number` for the SoC levels; `datetime` for a one-off ready-by; `time` per weekday; `sensor` for the plan. Overrides are caller state (D10) |
| **D10** (pure engine; caching and debounce in the caller) | **Supported** | The data's realities belong in the caller: rate budgets (Škoda 20/h; Zaptec "not more often than every 15 minutes"; Easee lock-outs), re-asserting per-session limits, SoC projection from charger energy. The engine stays pure. The caller grows, and `docs/design.md` should list these duties |

### Gaps
- No live measurement was possible. The figures for SoC staleness on the maintainer's Enyaq, the command latency on his charger (unknown brand) and the real 15-minute output of core Nord Pool for DK1/DK2 should be measured once 2026.11 is installed.
