"""
CLIM-02 · Who Actually Moves Global Temperature?
Back-of-the-envelope net-zero counterfactuals for the U.S., EU, China, India and groups.

Method (same framing as the class U.S. example):
  1. Start from 2024 fossil + cement CO2 (Global Carbon Project via Our World in Data).
  2. Project each region to 2100 under a stylized CMIP7-style "Medium" (current policy)
     and "High" (worst case / policy rollback) path, using the growth rates below.
  3. Counterfactual: the region (or group) goes to net-zero CO2 from 2025; everyone else
     stays on the same path.
  4. Avoided warming = avoided cumulative CO2 (2025-2100) x TCRE (IPCC AR6: 0.45 C per
     1,000 GtCO2, likely 0.27-0.63), times a small non-CO2 factor k chosen so the global
     path reproduces the class example's end points (2.65 C Medium, 3.45 C High, from 1.33 C in 2025).
Run:  python clim02_model.py   (needs pandas, numpy; downloads the OWID file)
"""
import numpy as np, pandas as pd, csv

URL = "https://raw.githubusercontent.com/owid/co2-data/master/owid-co2-data.csv"
d = pd.read_csv(URL)
names = {'US': 'United States', 'EU': 'European Union (27)', 'China': 'China', 'India': 'India', 'World': 'World'}
e0 = {k: d[(d.country == v) & (d.year == 2024)].co2.item() / 1000 for k, v in names.items()}  # GtCO2
e0['ROW'] = e0['World'] - sum(e0[k] for k in ['US', 'EU', 'China', 'India'])

yrs = np.arange(2024, 2101)
# (last year the growth rate applies, annual growth rate)
S = {'Medium': {
        'US':    [(2100, -0.01)],
        'EU':    [(2050, -0.025), (2100, -0.02)],
        'China': [(2030, 0.0), (2060, -0.015), (2100, -0.02)],
        'India': [(2040, 0.03), (2060, 0.01), (2100, -0.01)],
        'ROW':   [(2050, 0.01), (2070, 0.0), (2100, -0.01)]},
     'High': {
        'US':    [(2100, 0.0)],
        'EU':    [(2100, -0.01)],
        'China': [(2040, 0.01), (2100, 0.0)],
        'India': [(2050, 0.035), (2100, 0.01)],
        'ROW':   [(2060, 0.02), (2100, 0.01)]}}

def path(base, segs):
    out = [base]
    for y in yrs[1:]:
        g = next(gr for end, gr in segs if y <= end)
        out.append(out[-1] * (1 + g))
    return np.array(out)

regs = ['US', 'EU', 'China', 'India', 'ROW']
P = {s: {r: path(e0[r], S[s][r]) for r in regs} for s in S}
TCRE, LO, HI = 0.45e-3, 0.27e-3, 0.63e-3
target = {'Medium': 2.65 - 1.33, 'High': 3.45 - 1.33}
mask = yrs >= 2025
ramp = np.clip((2050 - yrs) / (2050 - 2024), 0, 1)   # sensitivity: linear phase-down to zero in 2050
cases = {'United States': ['US'], 'European Union': ['EU'], 'China': ['China'], 'India': ['India'],
         'U.S. + EU': ['US', 'EU'], 'All four': ['US', 'EU', 'China', 'India'], 'Rest of world': ['ROW']}

rows = []
for s in S:
    cum = sum(P[s][r] for r in regs)[mask].sum()
    k = target[s] / (cum * TCRE)
    for c, rs in cases.items():
        av = sum(P[s][r][mask].sum() for r in rs)
        av50 = sum((P[s][r] * (1 - ramp))[mask].sum() for r in rs)
        rows.append([c, s, round(av), round(100 * av / cum, 1), round(av * TCRE * k, 3),
                     round(av * LO * k, 3), round(av * HI * k, 3), round(av50 * TCRE * k, 3)])
hdr = ['case', 'scenario', 'avoided_GtCO2_2025_2100', 'share_of_global_cum_pct', 'avoided_C_central',
       'avoided_C_low', 'avoided_C_high', 'avoided_C_if_phased_to_zero_by_2050']
with open('clim02_results.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(hdr); w.writerows(rows)
for r in rows: print(r)
