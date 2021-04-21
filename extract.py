import pandas as pd
import numpy as np
from scipy.stats import ttest_1samp
from scipy.stats.distributions import norm

with open("hko_data.csv".format(), 'r') as csvfile:
    df_all = pd.read_csv(csvfile, index_col=None)

# define season names
season_names = ['spring', 'summer', 'autumn', 'winter']

# define field names
fields=['avgtemp', 'rf']

# define climat years
# https://www.hko.gov.hk/en/wxinfo/season/fcvsobs_seasonal.htm
climat_yrs = [(1981, 2011), (1991, 2021)]

# seasonal prediction by HKO
# 0: "Normal to below normal"
# 1: "Normal to above normal"
# https://www.hko.gov.hk/en/wxinfo/season/fcvsobs_seasonal.htm
b_norm = [
    [1,1,1,1,1,1,1,0], #temp
    [1,1,0,0,0,1,1,0]  #rf
]

# CDF to Z-scores for above normal and below normal
CDF_AN = 0.7
CDF_BN = 0.3
Z_AN = norm.ppf(CDF_AN)
Z_BN = norm.ppf(CDF_BN)

# Get all data filter by season only
def extract_by_season(season='spring'):
    if season == 'spring':
        return df_all[df_all['month'].isin([3, 4, 5])]
    elif season == 'summer':
        return df_all[df_all['month'].isin([6, 7, 8])]
    elif season == 'autumn':
        return df_all[df_all['month'].isin([9, 10, 11])]
    elif season == 'winter':
        return df_all[df_all['month'].isin([12, 1, 2])]
    else:
        raise ValueError('Season not defined')

# Get all data filter by season and year
def extract_by_season_and_year(season='spring', year = 1990):
    if season == 'spring':
        return df_all[df_all['month'].isin([3, 4, 5]) & df_all['year'].isin([year])]
    elif season == 'summer':
        return df_all[df_all['month'].isin([6, 7, 8]) & df_all['year'].isin([year])]
    elif season == 'autumn':
        return df_all[df_all['month'].isin([9, 10, 11]) & df_all['year'].isin([year])]
    elif season == 'winter':
        return pd.concat([df_all[df_all['month'].isin([12]) & df_all['year'].isin([year])],
                          df_all[df_all['month'].isin([1, 2]) & df_all['year'].isin([year + 1])]])
    else:
        raise ValueError('Season not defined')

# evalulate seasonal average of a selected year
def eval_selected_year_seasonal_avg(field='avgtemp', season='spring', year=1990):
    df = extract_by_season_and_year(season=season, year=year)
    # calculate seasonal avg for temp
    if field == 'avgtemp':
        return np.average(df[field])
    # calculate cumulative sum for rainfall
    elif field == 'rf':
        return np.sum(df[field])

# get seasonal averages into a dictionary
def get_seasonal_avg_in_dict(field='avgtemp', season='spring'):
    return {
        year: eval_selected_year_seasonal_avg(field=field, season=season, year=year) for year in range(1980, 2021)
    }

# save every seasonal statistic into a list of list
seasonal_avg_dict_ls_ls = [
    [
        get_seasonal_avg_in_dict(field=field, season=season) for season in season_names
    ] for field in fields
]

# yield the mu and sigma given a sample of seasonal statistics
def norm_fit():
    # this is used to define AN and BN thresholds
    # https://www.hko.gov.hk/en/wxinfo/season/intpret.htm

    # loop through two fields and four seasons
    return [
        [
            [
                norm.fit(
                    [seasonal_avg_dict_ls_ls[f][s][year] for year in range(*yrs)]
                ) for yrs in climat_yrs
            ] for s, season in enumerate(season_names)
        ] for f, field in enumerate(fields)
    ]

# temperature categories specified by HKO
# read: https://www.hko.gov.hk/en/wxinfo/season/catTT_91-20.htm
# an = [23.3, 28.9, 25.5, 17.7]
# bn = [22.6, 28.4, 25.0, 16.8]
args = norm_fit() # get the mu and sigmas into this variable

# season names
start_year = 2019
end_year = 2020
start_season = 'spring'
end_season = 'winter'

# generate a list of seasons forecasted
# we could have hard-coded the list, but this is just to make the code more robust
def get_seasons(start_year, start_season, end_year, end_season):
    ls = []
    for year in range(start_year, end_year + 1):
        season = start_season
        while True:
            ls.append([year, season])
            if (season == end_season):
                break
            season = season_names[season_names.index(season) + 1]
    return ls

# put the seasons into a list
season_lists = get_seasons(start_year, start_season, end_year, end_season)

# function to evaluate the score of the forecasts given the forecasts
def eval_score(b_norm=b_norm):
    Score = []

    for f, field in enumerate(fields):
        # physical meaning of penalty: absolute difference between z-score of forecast and observations
        # no penalty when the forecast is correct
        Penalty = 0 ; Total_Penalty = 0

        for i, (year, season) in enumerate(season_lists):
            s = season_names.index(season)
            selected_yr_seasonal_avg = seasonal_avg_dict_ls_ls[f][s][year]
            if season == 'winter' and year == 2020:
                arg_index = 0
            else:
                arg_index = 1

            # extract mean and var from args
            mean, var = args[f][s][arg_index]
            Z_avg = (selected_yr_seasonal_avg - mean) / (var ** 1/2)
            if (Z_avg > Z_AN):
                if not b_norm[f][i]:
                    Penalty += abs(Z_avg - Z_AN)
                Total_Penalty += abs(Z_avg - Z_AN)
            elif (Z_avg < Z_BN):
                if b_norm[f][i]:
                    Penalty += abs(Z_avg - Z_BN)
                Total_Penalty += abs(Z_avg - Z_BN)
            else:
                pass
        Score.append(1 - Penalty / Total_Penalty)
    return Score

Scores = eval_score()
for f, field in enumerate(fields):
    print('score:', field, Scores[f])

# demonstration purpose: suppose a forecast without skill, only outputting random ranges
o_temp = [1,1,1,1,1,1,1,1] #temp observation
o_rf = [2,2,0,2,2,0,1,0]  #rf observation
Scores_rand = []
a = []
n_trials = 100
for _ in range(n_trials):
    b_norm_rand = np.random.randint(2, size=16).reshape(2,8)
    Scores_rand.append(eval_score(b_norm_rand))
    a.append(b_norm_rand)

# glance at the average scores
Score_T_rand = np.array(Scores_rand).T[0]
Score_Rf_rand = np.array(Scores_rand).T[1]
print('averages:', np.average(Score_T_rand), np.average(Score_Rf_rand))

# hypothesis:
# H0: the scores of the HKO seasonal forecast does not differ from that of the random forecast without skill
# HA: ~H0
# Hypothesized population mean: score of the HKO seasonal forecast
print('pval:', ttest_1samp(Score_T_rand, Scores[0]).pvalue)
print('pval:', ttest_1samp(Score_Rf_rand, Scores[1]).pvalue)
# ==> H0 can be rejected

# skill score (0 = below, 1 = above, 2 = norm )
temp_rand = []
rf_rand = []
for i in range(n_trials):
    temp, rf = a[i]
    temp_hit = 0
    rf_hit = 0
    for j in range(8):
        if temp[j] == o_temp[j] or o_temp[j] == 2:
            temp_hit = temp_hit + 1
        if rf[j] == o_rf[j] or o_rf[j] == 2:
            rf_hit = rf_hit + 1
    temp_rand.append(temp_hit)
    rf_rand.append(rf_hit)

exp_hit_temp = np.average(temp_rand)
exp_hit_rf = np.average(rf_rand)
hit_skill_temp = (7 - exp_hit_temp) / (8 - exp_hit_temp) * 100
hit_skill_rf = (7 - exp_hit_rf) / (8 - exp_hit_rf) * 100
print('hs temp:', hit_skill_temp)
print('hs rf:', hit_skill_rf)