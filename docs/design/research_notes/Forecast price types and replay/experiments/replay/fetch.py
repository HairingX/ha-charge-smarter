"""Download the public data the replay needs into a data folder given as the first argument.

- Energi Data Service DayAheadPrices for DK1, DK2 and SE3 (quarter-hour spot, DKK/MWh), 2025-10-01 on.
- Energi Data Service DatahubPricelist rows for N1 A/S, Radius Elnet A/S and Energinet, and the elafgift.
- Every elpriser.org forecast archive run for DK1 and DK2 (raw spot, DKK/MWh excl. VAT).
Never calls Carnot.
"""
import json, os, sys, time, urllib.error, urllib.parse, urllib.request

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)


def get(url, params=None):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "charge-smarter-replay/1"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 7:
                raise
            time.sleep(20 * (attempt + 1))


def save(name, obj):
    with open(os.path.join(OUT, name), "w") as f:
        json.dump(obj, f)


EDS = "https://api.energidataservice.dk/dataset/"
for area in ("DK1", "DK2", "SE3"):
    if os.path.exists(os.path.join(OUT, "dap_%s.json" % area)):
        continue
    d = get(EDS + "DayAheadPrices", {"start": "2025-10-01", "end": "2026-11-09",
                                     "filter": json.dumps({"PriceArea": [area]}), "limit": 0})
    save("dap_%s.json" % area, d)
    print(area, len(d["records"]))
# N1's rows carry the owner name "N1 A/S - 131".
for name, owner in (("N1", "N1 A/S - 131"), ("Radius", "Radius Elnet A/S")):
    path = os.path.join(OUT, "tariff_%s.json" % name)
    if os.path.exists(path) and json.load(open(path))["records"]:
        continue
    d = get(EDS + "DatahubPricelist", {"start": "2025-01-01", "filter": json.dumps({"ChargeOwner": [owner]}),
                                       "limit": 0})
    save("tariff_%s.json" % name, d)
    print(owner, len(d["records"]))
# Energinet's system and transmission tariffs (41000, 40000) and the elafgift (EA-001).
d = get(EDS + "DatahubPricelist", {"start": "2025-01-01", "limit": 0,
                                   "filter": json.dumps({"ChargeTypeCode": ["EA-001", "41000", "40000"]})})
save("tariff_state.json", d)
# Whether any grid tariff is published per quarter hour.
d = get(EDS + "DatahubPricelist", {"start": "2026-01-01", "limit": 0,
                                   "filter": json.dumps({"ResolutionDuration": ["PT15M"]})})
save("tariff_pt15m.json", d)
print("PT15M tariff rows since 2026:", len(d["records"]))
ARCH = "https://elpriser.org/api/forecast/archive"
for area in ("DK1", "DK2"):
    for issued in get(ARCH, {"area": area})["issued"]:
        name = "arch_%s_%s.json" % (area, issued)
        if not os.path.exists(os.path.join(OUT, name)):
            save(name, get(ARCH, {"area": area, "issued": issued}))
    print(area, "archive done")
