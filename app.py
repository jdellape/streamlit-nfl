import streamlit as st
import requests
import pandas as pd
import altair as alt

st.title('Fantasy Football Data Explorer')

st.markdown("""
This app helps fantasy football owners make roster decisions by graphing historical player stats
* Use the side bar to the left to dynamically filter for players and statistics of interest.
* **Data source:** [pro-football-reference.com](https://www.pro-football-reference.com/).
""")

REGULAR_QB_STAT_OPTIONS = ['TD', 'YDS']
ADVANCED_QB_STAT_OPTIONS = ['BadTh', 'Prss']
STAT_OPTIONS_DROP_DOWN = []

st.sidebar.header('Filter Dataset By: ')
selected_year = st.sidebar.selectbox('Year', list(reversed(range(2019,2022))))
selected_position = st.sidebar.selectbox('Position',  ['QB','RB','WR','TE'])
selected_stat_category = st.sidebar.selectbox('Stat Category',  ['advanced','regular'])
if selected_stat_category == 'advanced':
    STAT_OPTIONS_DROP_DOWN = ADVANCED_QB_STAT_OPTIONS
else:
    STAT_OPTIONS_DROP_DOWN = REGULAR_QB_STAT_OPTIONS
selected_stats = st.sidebar.selectbox('Stat To Present', STAT_OPTIONS_DROP_DOWN)


# Load up json data I have hosted on github
@st.cache
def load_json_data():
    url = 'https://raw.githubusercontent.com/jdellape/data-sources/main/nfl/qb/season_summaries/qb_summary.json'
    r = requests.get(url)
    return r.json()

#Capture and filter stat data
tuple_list_to_analyze = []
test_json = load_json_data()

data_set_to_analyze = list(filter(lambda d: d['category'] == selected_stat_category and d['year'] == str(selected_year), test_json))

for row in data_set_to_analyze:
    try:
        tuple_list_to_analyze.append((row['player_id'], row['TD_overall'], row['Yds_overall']))
    except:
        pass

df_qbs = pd.DataFrame(tuple_list_to_analyze, columns =['ID', 'TD', 'Yds'])
df_qbs['Yds'] = pd.to_numeric(df_qbs['Yds'])
df_qbs['TD'] = pd.to_numeric(df_qbs['TD'])

st.header('Write out Raw json file containing stats filered by user input')
st.write(data_set_to_analyze)

st.header('Test a scatter plot based upon QB Data. Hard Coded to Only Present yards by TDs')
st.markdown("""
Must select "regular" from Stat Category drop down in order for this to display while under development.
""")
#Test a scatter plot with my json data
#Convert columns to integer for testing out a chart
qb_scatter = alt.Chart(df_qbs).mark_circle(size=60).encode(
    x='Yds',
    y='TD',
    tooltip='ID'
).interactive()

st.altair_chart(qb_scatter, use_container_width=True)