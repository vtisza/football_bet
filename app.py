import streamlit as st

import pandas as pd
pd.options.display.float_format = '{:,.4%}'.format

import numpy as np
from collections import Counter

country_list = ["AUT", "DNK", "FIN","IRL","JPN","MEX","NOR","POL","ROU","RUS",
"SWE","SWZ","USA"]

st.title('Bet Master')
st.header("Soccer Edition")

country_select = st.selectbox(
    'Country',
    country_list,
    index=1)

url = f"https://www.football-data.co.uk/new/{country_select}.csv"

fin_results = pd.read_csv(url)
fin_results.Season = fin_results.Season.astype(str)
fin_results.Season = fin_results.Season.apply(lambda x: x.split("/")[0]).astype(int)

home_teams = fin_results.Home.unique()
home_teams.sort()

away_teams = fin_results.Away.unique()
away_teams.sort()

def normalize(dict_to_normal):
  total = sum(dict_to_normal.values())
  for key in dict_to_normal.keys():
    dict_to_normal[key] = dict_to_normal[key]/total
  return dict_to_normal

home = st.selectbox(
    'Home team',
    home_teams,
    index=0)

away = st.selectbox(
    'Away team',
    away_teams,
    index=1)

year_start = st.selectbox(
    'Year start for analysis',
     list(range(fin_results.Season.min(),2020,1)))


def run_simulation(fin_results, home, away, year_start, nr_simulations=100000):
    results = fin_results[(fin_results.Home==home) & (fin_results.Away==away) & (fin_results.Season>=year_start)]
    HG_mean = results.HG.mean()
    AG_mean = results.AG.mean()

    home_goals = np.random.poisson(HG_mean, nr_simulations)
    away_goals = np.random.poisson(AG_mean, nr_simulations)

    home_goals_dict = normalize(Counter(home_goals))
    away_goals_dict = normalize(Counter(away_goals))

    simulations = dict()
    for home_values in home_goals_dict.keys():
        for away_values in away_goals_dict.keys():
            simulations[f"{home_values}:{away_values}"]=home_goals_dict[home_values]*away_goals_dict[away_values]
    
    simulations_df = pd.DataFrame.from_dict(simulations,orient="index").reset_index()
    simulations_df.columns = ["score", "prob"]
    simulations_df = simulations_df.sort_values("prob",ascending=False).reset_index(drop=True)
    simulations_df["HG"] = simulations_df.score.apply(lambda x: x.split(":")[0]) 
    simulations_df["AG"] = simulations_df.score.apply(lambda x: x.split(":")[1]) 

    return simulations_df

if fin_results[(fin_results.Home==home) & (fin_results.Away==away) & (fin_results.Season>=year_start)].shape[0]==0:
    st.header("Not enough history, please select other team combination.")
else:
    simulations_df = run_simulation(fin_results, home, away, year_start, nr_simulations=10000)

    st.header("Former games")
    st.dataframe(fin_results[(fin_results.Home==home) & (fin_results.Away==away) & (fin_results.Season>=year_start)])

    st.header("Predicted outcomes")
    st.dataframe(simulations_df)

    st.header("Predicted odds")
    draw = 1/simulations_df[simulations_df.HG==simulations_df.AG].prob.sum()
    home_win = 1/simulations_df[simulations_df.HG>simulations_df.AG].prob.sum()
    away_win = 1/simulations_df[simulations_df.HG<simulations_df.AG].prob.sum()

    st.write(f"{home_win:,.2f} - {draw:,.2f} - {away_win:,.2f}")
