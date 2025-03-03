from pathlib import Path
import pandas as pd


def highlight_global(df):
    is_glob = pd.Series(data=False, index=df.index)
    is_glob.loc['global'] = True
    return ['textbf:--rwrap;' if ind else '' for ind in is_glob]

# load the regional summary from github
csv_url = 'https://raw.githubusercontent.com/GLIMS-RGI/lake_terminating/refs/heads/main/tables/regional_summary.csv'
data = pd.read_csv(csv_url)

table_data = pd.DataFrame(data=data[['region', 'name', 'numglac']])
table_data['area'] = data[[c for c in data.columns if 'area' in c]].sum(axis=1)

table_data['level0_num'] = data[['level0', 'level98', 'level99']].sum(axis=1)
table_data['level0_pct'] = table_data['level0_num'] / table_data['numglac']

table_data['level0_area'] = data[['level0area', 'level98area', 'level99area']].sum(axis=1)
table_data['level0_area_pct'] = table_data['level0_area'] / table_data['area']

for lev in range(1, 4):
    table_data[f"level{lev}_num"] = data[f"level{lev}"]
    table_data[f"level{lev}_pct"] = table_data[f"level{lev}_num"] / table_data['numglac']

    table_data[f"level{lev}_area"] = data[f"level{lev}area"]
    table_data[f"level{lev}_area_pct"] = table_data[f"level{lev}_area"] / table_data['area']

pct_cols = [c for c in table_data.columns if 'pct' in c]

# now divide area by 1000 to help with space
area_cols = [c for c in table_data.columns if 'area' in c and 'pct' not in c]
table_data[area_cols] /= 1000

table_data['region'] = table_data['region'].str.pad(2, fillchar='0')
table_data.set_index('region', inplace=True)

# now, format percentages and areas with only a single decimal
keys = pct_cols + area_cols
vals = (['{:.1%}'.format] * len(pct_cols)) + (['{:.1f}'.format] * len(area_cols))

formats = dict(zip(keys, vals))

with open(Path('tables', 'Table3_Summary.tex'), 'w') as f:
    out_table = table_data.drop(columns=['name']).style.apply(highlight_global)

    print(out_table.format(formats).to_latex().replace('%', ''), file=f)
