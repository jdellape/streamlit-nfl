import streamlit as st
import requests
import pandas as pd
import altair as alt

st.title('Fantasy Football Data Explorer')

#This code only for allowing tooltips to display when in full screen mode (https://discuss.streamlit.io/t/tool-tips-in-fullscreen-mode-for-charts/6800/8)
st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',
             unsafe_allow_html=True)

st.markdown("""
This app helps fantasy football owners make roster decisions by graphing historical player stats
* Use the side bar to the left to dynamically filter data.
* **Data source:** [pro-football-reference.com](https://www.pro-football-reference.com/).
""")

SCORING_TYPES = ['Normal','PPR','DraftKings','FanDuel']

SCORING_TYPE_COL_MATCHING = {'Normal':'FantPt', 'PPR':'PPR', 'DraftKings':'DKPt', 'FanDuel':'FDPt'}

SCORING_TYPE_TOOL_TIP = {'Normal':'trad style<br/>  blah blah', 'PPR':'PPR style', 'DraftKings':'Draft Kings Style', 'FanDuel':'Fan Duel Style'}

SELECTION_DETAILS_COLS = {'Normal':['FantPt','FantPtpG','Player','year'], 
                          'PPR':['PPR','PPRpG','Player','year'],
                          'DraftKings':['DKPt','DKPtpG','Player','year'], 
                          'FanDuel':['FDPt','FDPtpG','Player','year']}

st.sidebar.header('Filter Stripplot By: ')
selected_year = st.sidebar.selectbox('Year', list(reversed(range(2019,2022))))

st.sidebar.header('Set Stripplot y axis:')
selected_scoring_type = st.sidebar.selectbox('Fantasy Point Scoring Style', SCORING_TYPES)

with st.sidebar.expander("See scoring style details"):
     st.write('feature under construction')

DATA_URL = 'https://raw.githubusercontent.com/jdellape/data-sources/main/nfl/fantasy_points_by_player_by_year.csv'

# Load up data I have hosted on github
@st.cache
def load_data(url):
    data = pd.read_csv(url)
    data = data[data['FantPos'].isin(['QB','RB','WR','TE'])]
    data = data[data['FantPt'] >= 0]
    return data

data = load_data(DATA_URL)
#data = data[data['year'] == selected_year]

st.header('Write out Raw .csv file containing stats')
st.write(data)

st.header('Test a Stripplot based on feedack from Caleb')

#Try the altair plot caleb referenced
selected_y = SCORING_TYPE_COL_MATCHING[selected_scoring_type]

strip_plot_selector = alt.selection_single(empty='all', fields=['Player'])

stripplot =  alt.Chart(data[data['year'] == selected_year]).mark_circle(size=50).encode(
    x=alt.X(
        'jitter:Q',
        title=None,
        axis=alt.Axis(ticks=True, grid=False, labels=False),
        scale=alt.Scale(),
    ),
    y=alt.Y(f'{selected_y}:Q',
            scale=alt.Scale(
                domain=(0, 450)),
                axis=alt.Axis(title=None)),
    color=alt.condition(strip_plot_selector,'FantPos:N', alt.value('lightgray'), legend=None),
    tooltip='Player',
    column=alt.Column(
        'FantPos:N',
        header=alt.Header(
            labelFontSize=16,
            labelAngle=0,
            titleOrient='bottom',
            labelOrient='bottom',
            labelAlign='center',
            labelPadding=25,
        ),
    ),
).transform_calculate(
    # Generate Gaussian jitter with a Box-Muller transform
    jitter='sqrt(-2*log(random()))*cos(2*PI*random())'
).configure_facet(
    spacing=0
).configure_view(
    stroke=None
).configure_axis(
    labelFontSize=16,
    titleFontSize=16
).properties(
    height=400, 
    width=150
).add_selection(strip_plot_selector)

#Trying to make a details line chart work here, but unsuccessful so far.
base = alt.Chart(data).properties(
    width=250,
    height=250
).add_selection(strip_plot_selector)

line = base.mark_line().encode(
    y='FantPt',
    x='year'
).transform_filter(
    strip_plot_selector
)
#End of my attempt

st.altair_chart(stripplot)
