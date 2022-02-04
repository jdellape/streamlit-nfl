import streamlit as st
import pandas as pd
import base64
#import matplotlib.pyplot as plt
import numpy as np
import altair as alt

st.title('NFL Football Stats (Rushing) Explorer')

st.markdown("""
This app performs simple webscraping of NFL Football player stats data (focusing on Rushing)!
* **Python libraries:** base64, pandas, streamlit, numpy, matplotlib, seaborn
* **Data source:** [pro-football-reference.com](https://www.pro-football-reference.com/).
""")

st.sidebar.header('User Input Features')
selected_year = st.sidebar.selectbox('Year', list(reversed(range(2019,2022))))

# Web scraping of NFL player stats
# https://www.pro-football-reference.com/years/2019/rushing.htm
@st.cache
def load_normal_data(year):
    url = "https://www.pro-football-reference.com/years/" + str(year) + "/rushing.htm"
    html = pd.read_html(url, header = 1)
    df = html[0]
    raw = df.drop(df[df.Age == 'Age'].index) # Deletes repeating headers in content
    raw = raw.fillna(0)
    playerstats = raw.drop(['Rk'], axis=1)
    playerstats['Yds'] = pd.to_numeric(playerstats['Yds'])
    playerstats['TD'] = pd.to_numeric(playerstats['TD'])
    return playerstats

adv_rush_df = pd.read_csv("https://raw.githubusercontent.com/jdellape/data-sources/main/nfl/advanced_rushing_2021.csv")
st.write(adv_rush_df)

#Simply adding to fetch advanced stats table example
# @st.cache
# def load_advanced_data(year):
#     url = "https://www.pro-football-reference.com/years/" + str(year) + "/rushing_advanced.htm"
#     html = pd.read_html(url, header = 1)
#     df = html[0]

#     raw = df.drop(df[df.Age == 'Age'].index) # Deletes repeating headers in content
#     raw = raw.fillna(0)
#     playerstats = raw.drop(['Rk'], axis=1)
#     return playerstats

playerstats = load_normal_data(selected_year)
# player_adv_stats = load_advanced_data(selected_year)
#Write advanced stats out to show verify I have captured the table
#st.dataframe(player_adv_stats)

# Sidebar - Team selection
sorted_unique_team = sorted(playerstats.Tm.unique())
selected_team = st.sidebar.multiselect('Team', sorted_unique_team, sorted_unique_team)

# Sidebar - Position selection
unique_pos = ['RB','QB','WR','FB','TE']
selected_pos = st.sidebar.multiselect('Position', unique_pos, unique_pos)

# Filtering data
df_selected_team = playerstats[(playerstats.Tm.isin(selected_team)) & (playerstats.Pos.isin(selected_pos))]

st.header('Display Player Stats of Selected Team(s)')
st.write('Data Dimension: ' + str(df_selected_team.shape[0]) + ' rows and ' + str(df_selected_team.shape[1]) + ' columns.')
st.dataframe(df_selected_team)


#Convert columns to integer for testing out a chart
scatter = alt.Chart(playerstats[['Yds','TD', 'Player']]).mark_circle(size=60).encode(
    x='Yds',
    y='TD',
    tooltip='Player'
).interactive()

st.altair_chart(scatter, use_container_width=True)

# Download NBA player stats data
# https://discuss.streamlit.io/t/how-to-download-file-in-streamlit/1806
def filedownload(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()  # strings <-> bytes conversions
    href = f'<a href="data:file/csv;base64,{b64}" download="playerstats.csv">Download CSV File</a>'
    return href

st.markdown(filedownload(df_selected_team), unsafe_allow_html=True)