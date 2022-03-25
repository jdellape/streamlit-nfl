import streamlit as st
import pandas as pd
import altair as alt

st.title('Fantasy Football Draft Helper 🏈')

#This code only for allowing tooltips to display when in full screen mode (https://discuss.streamlit.io/t/tool-tips-in-fullscreen-mode-for-charts/6800/8)
st.markdown('<style>#vg-tooltip-element{z-index: 1000051}</style>',
             unsafe_allow_html=True)

st.markdown("""
This app helps fantasy football owners make roster decisions by graphing historical player stats
* Use the side bar to the left to dynamically filter data.
* **Data source:** [pro-football-reference.com](https://www.pro-football-reference.com/).
""")

# Load up data I have hosted on github
DATA_URL = 'https://raw.githubusercontent.com/jdellape/data-sources/main/nfl/fantasy_points_by_player_by_year.csv'
WEEKLY_DATA_URL = 'https://raw.githubusercontent.com/jdellape/data-sources/main/nfl/fantasy_weekly_results_by_player.csv'

@st.cache
def load_data(url):
    data = pd.read_csv(url)
    return data

# Load data with notes to user
data_load_state = st.text('Loading summary data...')
data = load_data(DATA_URL)
distinct_player_names = list(set(data.Player))
data_load_state = st.text('Loading weekly fantasy data...')
weekly_data = load_data(WEEKLY_DATA_URL)
data_load_state.text('All data loaded!')

#Write out raw yearly summary to ui
st.header('Raw .csv data containing yearly stats')
st.write(data)


SCORING_TYPES = ['Normal','PPR', 'Halfpoint PPR', 'DraftKings','FanDuel']

SCORING_TYPE_COL_MATCHING = {'Normal':'FantPt', 'PPR':'PPR', 'Halfpoint PPR':'HalfpointPPR', 'DraftKings':'DKPt', 'FanDuel':'FDPt'}

SCORING_TYPE_TOOL_TIP = {'Normal':'trad style<br/>  blah blah', 'PPR':'PPR style', 'Halfpoint PPR':'Halfpoint PPR', 'DraftKings':'Draft Kings Style', 'FanDuel':'Fan Duel Style'}

SELECTION_DETAILS_COLS = {'Normal':['FantPt','FantPtpG','Player','year'], 
                          'PPR':['PPR','PPRpG','Player','year'],
                          'Halfpoint PPR':['HalfpointPPR','HalfpointPPRpG','Player','year'],
                          'DraftKings':['DKPt','DKPtpG','Player','year'], 
                          'FanDuel':['FDPt','FDPtpG','Player','year']}

def get_pivot_table(df, start, end, agg_func, scoring_type):
    """Function to get yearly player data to plot on stripplot based on user input
       Shout out to mito for making this way easier to do: https://www.trymito.io/ 
    """
    #Filter dataframe according to years specified by user
    df = df[df.year.isin(range(int(start), int(end) + 1))]
    #Drop columns I don't need
    unused_columns = df.columns.difference(set(['Player','FantPos']).union(set([])).union(set({SCORING_TYPE_COL_MATCHING[scoring_type]})))
    tmp_df = df.drop(unused_columns, axis=1)
    #Compile pivot table df
    pivot_table = tmp_df.pivot_table(
        index=['Player','FantPos'],
        values=[SCORING_TYPE_COL_MATCHING[scoring_type]],
        aggfunc={SCORING_TYPE_COL_MATCHING[scoring_type]: [agg_func]}
    )
    #Formatting stuff
    pivot_table.set_axis([col for col in pivot_table.keys()], axis=1, inplace=True)
    fantasy_points_by_year_pivot = pivot_table.reset_index()
    fantasy_points_by_year_pivot.columns = ['Player', 'FantPos', SCORING_TYPE_COL_MATCHING[scoring_type]]
    #round last column if needed
    if agg_func != 'sum':
        fantasy_points_by_year_pivot[SCORING_TYPE_COL_MATCHING[scoring_type]] = fantasy_points_by_year_pivot[SCORING_TYPE_COL_MATCHING[scoring_type]].round(1)
    return fantasy_points_by_year_pivot

st.sidebar.header('Season Total Data Settings')

start_year, end_year = st.sidebar.select_slider(
     'Range of Years to Include',
     options=list(range(2019,2022)),
     value=(2019,2021))

selected_agg_func = st.sidebar.radio('Aggregation Method to Apply',['sum','mean','median'])

#Allow user to enter a point floor
point_value_floor = st.sidebar.number_input('Point Floor for Chart Display', value=0, min_value=0)

selected_scoring_type = st.sidebar.selectbox('Fantasy Point Scoring Style', SCORING_TYPES)

with st.sidebar.expander("See scoring style details"):
     st.write('feature under construction')

#Allow choice of analysis by total season points OR average points per game
st.sidebar.header('THIS CURRENTLY NOT DOING ANYTHING. NEED TO DISCUSS OPTIONS TO NORMALIZE.')
selected_scoring_agg = st.sidebar.radio(
     "View Points by",
     ('Average Per Game', 'Season Total'))

#Get a df for charting season totals data based upon user entry
pivot_df = get_pivot_table(data, start_year, end_year, selected_agg_func, selected_scoring_type)

st.header('Interactive Stripplot')
st.markdown("""
Click on a player to see their year over year statistics in the line chart details. Hold down on the 'Shift' key while clicking 
to select multiple players at a time.
""")

#Add a new area to allow for a user to indicate which players have already been drafted
with st.expander('Players Already Drafted'):
    players_already_drafted = st.multiselect('Indicate Players Already Taken',
        distinct_player_names)

#Don't think I need this currently
# def get_y():
#     "Helper function to get the appropriate score column to display on stripplot y axis"
#     if selected_scoring_agg == 'Average Per Game':
#         return SCORING_TYPE_COL_MATCHING[selected_scoring_type] + 'pG'
#     else:
#         return SCORING_TYPE_COL_MATCHING[selected_scoring_type]

#Get user selected y value
#selected_y = get_y()
selected_y = SCORING_TYPE_COL_MATCHING[selected_scoring_type]

#Construct altair plot to visualize data

#Create a selector object
strip_plot_selector = alt.selection_multi(empty='all', fields=['Player'])

#Create a stripplot
#Get the slice of your dataframe to plot
stripplot_data = pivot_df[(pivot_df['Player'].isin(players_already_drafted) == False) & (pivot_df[selected_y] >= point_value_floor)]

#Get values to use as the min and max values for the y-axis
stripplot_y_max = stripplot_data[selected_y].max() + 10

stripplot_y_min = point_value_floor

#compile the plot
stripplot =  alt.Chart(stripplot_data).mark_circle(size=50).encode(
    x=alt.X(
        'jitter:Q',
        title=None,
        axis=alt.Axis(ticks=True, grid=False, labels=False),
        scale=alt.Scale(),
    ),
    y=alt.Y(f'{selected_y}:Q',
            scale=alt.Scale(
            domain=(stripplot_y_min, stripplot_y_max)),
                axis=alt.Axis(title=None)),
    color=alt.condition(strip_plot_selector, 'FantPos', alt.value('lightgray'), legend=None),
    #color=alt.condition(interval, 'Origin', alt.value('lightgray')
    tooltip=['Player', selected_y],
    column=alt.Column(
        'FantPos:N',
        header=alt.Header(
            labelFontSize=16,
            labelAngle=0,
            titleOrient='bottom',
            labelOrient='bottom',
            labelAlign='center',
            labelPadding=25,
            labelColor='white'
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

#Create layered density chart for detailed player comparison
st.header('Fantasy Point Density Estimate Chart using Weekly Points Scored')
st.markdown("""
Select Players from the dropdown below to get a detailed visualization of how their weekly fantasy point distribution compares.
[Click for more info on density estimates](https://en.wikipedia.org/wiki/Kernel_density_estimation)
""")

selected_players_to_compare = st.multiselect(
     'Select Players to Compare',
     distinct_player_names)

data_to_chart = weekly_data[weekly_data['player_name'].isin(selected_players_to_compare)]
data_to_chart = data_to_chart[data_to_chart['fantasy_table_column']=='FantPt']
unique_selected_ids = list(data_to_chart.player_id.unique()) 

img_urls = [f'https://www.pro-football-reference.com/req/20180910/images/headshots/{id.split("/")[1]}_2021.jpg' for id in unique_selected_ids]

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