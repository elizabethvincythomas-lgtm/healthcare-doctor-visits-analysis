# Healthcare Analytics for Doctor Visits

A descriptive data analysis project exploring how doctor visits vary with personal details, reported illness, reduced activity, chronic conditions and healthcare support.

## View the project

- [Executed analysis notebook](Healthcare_Analysis.ipynb) — view the code and recorded outputs directly on GitHub.
- [Offline analysis report](Analysis_Report.html) — download the repository ZIP, extract it, and open this file in your browser.
- [Calculated tables](calculated_tables) — exact group counts, totals and averages.
- [Original dataset](1776250375-P2-Healthcare%20Analytics%20for%20Doctor%20Visits%20%281%29.csv).

## Main results

| Measure | Result |
| --- | ---: |
| Records | 5,190 |
| Source columns including identifier | 13 |
| Recorded doctor visits | 1,566 |
| Average visits per record | 0.302 |
| Records with at least one visit | 1,049 (20.2%) |
| Records with zero visits | 4,141 (79.8%) |

Average visits are higher in records with more reported illnesses and with reduced activity. Records with `lchronic = yes` average 0.603 visits, compared with 0.262 for `lchronic = no`. These are unadjusted associations within the supplied sample, not causal effects.

## Data integrity and limitations

All numerical evidence comes from the single supplied CSV. All 5,190 records are retained. No values are fabricated, filled, converted, or removed.

- No missing cells and no repeated record IDs.
- 1,320 later records repeat earlier measurements under different IDs. These are retained because matching measurements do not prove duplicate people.
- Age and income remain in their original CSV scale. The supplied references do not specify conversion rules.
- The visit observation period, income units and health-score direction are unspecified.
- Chronic and healthcare-support flags are compared separately because groups can overlap.
- Results do not establish treatment needs, program effectiveness or population-level effects.

Original CSV SHA256: `6967773d1f794bc32138478352c3ed507d87faedc73174b1cd179bd11efab225`.

## Run the analysis

Install Python 3, then open a terminal in the downloaded repository folder:

```bash
python -m pip install -r requirements.txt
python run_analysis.py
```

The script recreates the calculation tables, summary metrics, notebook and offline HTML report from the original CSV. The notebook can also be run in Jupyter or VS Code with a Python kernel.

Average visits = total visits in a group / records in that group. Share with a visit (%) = 100 × records with visits greater than zero / records in the group. Reported summary averages are rounded to three decimals and shares to one decimal. Detailed tables retain more precision.
