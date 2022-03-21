import streamlit as st
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

SCORING_TYPES = ['Normal','PPR', 'Halfpoint PPR', 'DraftKings','FanDuel']

SCORING_TYPE_COL_MATCHING = {'Normal':'FantPt', 'PPR':'PPR', 'Halfpoint PPR':'HalfpointPPR', 'DraftKings':'DKPt', 'FanDuel':'FDPt'}

SCORING_TYPE_TOOL_TIP = {'Normal':'trad style<br/>  blah blah', 'PPR':'PPR style', 'Halfpoint PPR':'Halfpoint PPR', 'DraftKings':'Draft Kings Style', 'FanDuel':'Fan Duel Style'}

SELECTION_DETAILS_COLS = {'Normal':['FantPt','FantPtpG','Player','year'], 
                          'PPR':['PPR','PPRpG','Player','year'],
                          'Halfpoint PPR':['HalfpointPPR','HalfpointPPRpG','Player','year'],
                          'DraftKings':['DKPt','DKPtpG','Player','year'], 
                          'FanDuel':['FDPt','FDPtpG','Player','year']}

st.sidebar.header('Filter Stripplot By: ')
selected_year = st.sidebar.selectbox('Year', list(reversed(range(2019,2022))))

st.sidebar.header('Set Stripplot y axis:')
selected_scoring_type = st.sidebar.selectbox('Fantasy Point Scoring Style', SCORING_TYPES)

with st.sidebar.expander("See scoring style details"):
     st.write('feature under construction')

#Allow choice of analysis by total season points OR average points per game
selected_scoring_agg = st.sidebar.radio(
     "View Points by",
     ('Average Per Game', 'Season Total'))

DATA_URL = 'https://raw.githubusercontent.com/jdellape/data-sources/main/nfl/fantasy_points_by_player_by_year.csv'
WEEKLY_DATA_URL = 'https://raw.githubusercontent.com/jdellape/data-sources/main/nfl/fantasy_weekly_results_by_player.csv'

# Load up data I have hosted on github
@st.cache
def load_data(url):
    data = pd.read_csv(url)
    return data

# Load data with notes to user
data_load_state = st.text('Loading summary data...')
data = load_data(DATA_URL)
data_load_state = st.text('Loading weekly fantasy data...')
weekly_data = load_data(WEEKLY_DATA_URL)
data_load_state.text('All data loaded!')

st.header('Raw .csv data containing yearly stats')
st.write(data)

st.header('Interactive Stripplot')
st.markdown("""
Click on a player to see their year over year statistics in the line chart details. Hold down on the 'Shift' key while clicking 
to select multiple players at a time.
""")

def get_y():
    "Helper function to get the appropriate score column to display on y axis"
    if selected_scoring_agg == 'Average Per Game':
        return SCORING_TYPE_COL_MATCHING[selected_scoring_type] + 'pG'
    else:
        return SCORING_TYPE_COL_MATCHING[selected_scoring_type]

#Get user selected y value
selected_y = get_y()

#Construct altair plot to visualize data

#Create a selector object
strip_plot_selector = alt.selection_multi(empty='all', fields=['Player'])

#Create a stripplot
stripplot =  alt.Chart(data[data['year'] == selected_year]).mark_circle(size=50).encode(
    x=alt.X(
        'jitter:Q',
        title=None,
        axis=alt.Axis(ticks=True, grid=False, labels=False),
        scale=alt.Scale(),
    ),
    y=alt.Y(f'{selected_y}:Q',
            # scale=alt.Scale(
            #     domain=(0, 450)),
                axis=alt.Axis(title=None)),
    color=alt.condition(strip_plot_selector, 'FantPos', alt.value('lightgray'), legend=None),
    #color=alt.condition(interval, 'Origin', alt.value('lightgray')
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
).add_selection(
    strip_plot_selector
).properties(
    height=400, 
    width=150
)
#Something in here was breaking my ability to create a details chart based on selection
# .configure_facet(
#     spacing=0
# ).configure_view(
#     stroke=None
# ).configure_axis(
#     labelFontSize=16,
#     titleFontSize=16
# )

#Create Selection Details line chart by year
line = alt.Chart(data).mark_line(
    point=alt.OverlayMarkDef(color="red")
    ).encode(
    x='year:O',
    y=f'{selected_y}:Q',
    strokeDash='Player',
    #color='Player',
    tooltip='Player'
).transform_filter(
    strip_plot_selector
).properties(
    height=400, 
    width=675
)

#Write out the charts to streamlit app
st.altair_chart(stripplot & line)

#Test out layered density chart
st.header('Fantasy Point Density Estimate Chart using Weekly Points Scored')
st.markdown("""
Select Players from the dropdown below to get a detailed visualization of how their weekly fantasy point distribution compares.
[Click for more info on density estimates](https://en.wikipedia.org/wiki/Kernel_density_estimation)
""")

distinct_player_names = list(set(data.Player))

selected_players_to_compare = st.multiselect(
     'Select Players to Compare',
     distinct_player_names)

data_to_chart = weekly_data[weekly_data['player_name'].isin(selected_players_to_compare)]
data_to_chart = data_to_chart[data_to_chart['fantasy_table_column']=='FantPt']
unique_selected_ids = list(data_to_chart.player_id.unique()) 

img_urls = [f'https://www.pro-football-reference.com/req/20180910/images/headshots/{id.split("/")[1]}_2021.jpg' for id in unique_selected_ids]

# st.write('You selected:')


extent_max = data_to_chart.value.max() + 1

if selected_players_to_compare:
    st.image(img_urls, caption=selected_players_to_compare)
    #Density estimate testing (https://altair-viz.github.io/gallery/density_stack.html)
    pdf_chart = alt.Chart(data_to_chart).transform_density(
        density='value',
        as_=['value', 'density'],
        # bandwidth=0.337,
        groupby=['player_name'],
        extent= [0, extent_max]
        # counts = True
        # steps=200
    ).mark_area(orient='vertical', opacity=0.5).encode(
        alt.X('value:Q'),
        alt.Y('density:Q'),
        alt.Color('player_name:N')
    ).properties(height=400, 
        width=675)

    #Write out the chart to streamlit app
    st.altair_chart(pdf_chart)

    st.header('Raw weekly data being visualized above')
    st.write(data_to_chart)