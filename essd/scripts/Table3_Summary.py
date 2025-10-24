from pathlib import Path
import pandas as pd


def highlight_global(df):
    is_glob = pd.Series(data=False, index=df.index)
    is_glob.loc['global'] = True
    return ['textbf:--rwrap;' if ind else '' for ind in is_glob]

# load the regional summary from the parent directory
csv_url = Path('..', 'dataset', 'regional_summary.csv')
data = pd.read_csv(csv_url)

table_data = pd.DataFrame(data=data[['region', 'name', 'numglac']])
table_data['area'] = data[[c for c in data.columns if 'area' in c]].sum(axis=1)

table_data['cat0_num'] = data[['cat0', 'cat98', 'cat99']].sum(axis=1)
table_data['cat0_pct'] = table_data['cat0_num'] / table_data['numglac']

table_data['cat0_area'] = data[['cat0area', 'cat98area', 'cat99area']].sum(axis=1)
table_data['cat0_area_pct'] = table_data['cat0_area'] / table_data['area']

for cat in range(1, 4):
    table_data[f"cat{cat}_num"] = data[f"cat{cat}"]
    table_data[f"cat{cat}_pct"] = table_data[f"cat{cat}_num"] / table_data['numglac']

    table_data[f"cat{cat}_area"] = data[f"cat{cat}area"]
    table_data[f"cat{cat}_area_pct"] = table_data[f"cat{cat}_area"] / table_data['area']

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
