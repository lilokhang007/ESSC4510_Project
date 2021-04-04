import pandas as pd

with open("hko_data.csv".format(), 'r') as csvfile:
    df_all = pd.read_csv(csvfile, index_col=None)

# Get season
def extract_by_season_and_year(season='spring', year = 1990):
    if season == 'winter':
        return pd.concat([df_all[df_all['month'].isin([12]) & df_all['year'].isin([year - 1])],
                   df_all[df_all['month'].isin([1, 2])] & df_all['year'].isin([year])])
    elif season == 'spring':
        return df_all[df_all['month'].isin([3, 4, 5]) & df_all['year'].isin([year])]
    elif season == 'summer':
        return df_all[df_all['month'].isin([6, 7, 8]) & df_all['year'].isin([year])]
    elif season == 'autumn':
        return df_all[df_all['month'].isin([9, 10, 11]) & df_all['year'].isin([year])]
    else:
        raise ValueError('Season not defined')
