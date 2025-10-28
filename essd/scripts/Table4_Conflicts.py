from pathlib import Path
from sklearn.metrics import confusion_matrix
import pandas as pd


base_path = Path('..', 'dataset')

# load the conflicts file
conflicts = pd.read_csv(Path(base_path, 'mappingconflicts.csv'))

# rename columns
conflicts.rename(columns={'category agreed': 'agreed',
                          'operator 1 conflict': 'operator1',
                          'operator 2 conflict': 'operator2'},
                 inplace=True)

# create the confusion matrix data
cmat = confusion_matrix(conflicts['operator1'], conflicts['operator2'])

cmat_df = pd.DataFrame(index=range(4), columns=range(4), data=cmat)

with (open(Path('tables', 'Table4_Conflicts.tex'), 'w') as f):
    texout = cmat_df.to_latex().replace('\\toprule\n', '') \
        .replace('\\midrule\n', '') \
        .replace('\\bottomrule\n', '')
    print(texout, file=f)

# go through different cases and print results
# first, both operators agreed on 0-1, but differed
is_land = conflicts.loc[conflicts['operator1'].isin([0, 1]) &
                        conflicts['operator2'].isin([0, 1]), 'agreed'].value_counts()
print("Operators disagreed between 0, 1:")
print(is_land, '\n')

# next, one operator said 2-3 and the other said 0-1, crossing the boundary
lake_land = conflicts.loc[(conflicts['operator1'].isin([0, 1]) & conflicts['operator2'].isin([2, 3])) |
                          (conflicts['operator1'].isin([2, 3]) & conflicts['operator2'].isin([0, 1])), 'agreed'].value_counts()
print("Operators disagreed between lake, land:")
print(lake_land, '\n')

# finally, both operators agreed on 2-3, but differed
is_lake = conflicts.loc[conflicts['operator1'].isin([2, 3]) &
                        conflicts['operator2'].isin([2, 3]), 'agreed'].value_counts()
print("Operators disagreed between 2, 3:")
print(is_lake, '\n')
