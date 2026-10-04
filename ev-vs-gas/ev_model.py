"""
SHOW ME (my own topic) · Are EVs actually cleaner than gas cars?
Lifecycle CO2 of a midsize EV vs. a comparable gas car, charged on different state grids.
All inputs are listed here so anyone can change them and rerun:  python ev_model.py
"""
import csv, json
LB_PER_MWH = {  # EIA State Electricity Profiles, 2024 CO2 emission rate (generation-based)
    'California': 407, 'New York': 537, 'U.S. average': 785, 'Texas': 823, 'West Virginia': 1912}
KG_PER_LB = 0.453592
GAS_TAILPIPE = 8.887        # kg CO2 per gallon burned (EPA)
GAS_UPSTREAM = 0.24         # +24% for crude extraction, refining, transport (well-to-tank; GREET-style assumption)
MPG = 30                    # comparable midsize gas sedan
EV_KWH_PER_MI = 0.30        # at the wall, incl. charging losses (typical midsize EV)
GRID_LOSS = 0.05            # transmission & distribution losses
MFG_CAR = 7.0               # t CO2e to build the car body (either type)
BATTERY_KWH = 75            # ~300-mile range pack (the "heavy EV" case)
BATTERY_KG_PER_KWH = 75     # kg CO2e per kWh of battery made (published range ~60-100)
LIFE_MI = 200_000

gas_per_mi = GAS_TAILPIPE * (1 + GAS_UPSTREAM) / MPG / 1000          # t per mile
ev_mfg = MFG_CAR + BATTERY_KWH * BATTERY_KG_PER_KWH / 1000              # t
out = []
for st, lb in LB_PER_MWH.items():
    kg_kwh = lb * KG_PER_LB / 1000
    ev_per_mi = EV_KWH_PER_MI / (1 - GRID_LOSS) * kg_kwh / 1000
    breakeven = (ev_mfg - MFG_CAR) / (gas_per_mi - ev_per_mi)
    gas_life = MFG_CAR + gas_per_mi * LIFE_MI
    ev_life = ev_mfg + ev_per_mi * LIFE_MI
    out.append(dict(grid=st, lb_mwh=lb, ev_g_per_mi=round(ev_per_mi * 1e6), gas_g_per_mi=round(gas_per_mi * 1e6),
                    breakeven_mi=round(breakeven, -2), ev_life_t=round(ev_life, 1), gas_life_t=round(gas_life, 1),
                    pct_less=round(100 * (1 - ev_life / gas_life))))
with open('ev_results.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print(f"EV build = {ev_mfg:.1f} t, gas build = {MFG_CAR} t, gas = {gas_per_mi*1e6:.0f} g/mi")
for r in out: print(r)
json.dump(dict(rows=out, ev_mfg=ev_mfg, gas_mfg=MFG_CAR, gas_per_mi=gas_per_mi), open('ev_res.json', 'w'), indent=1)
