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
# st.header('Raw .csv data containing yearly stats')
# st.write(data)


SCORING_TYPES = ['Normal','PPR', 'Halfpoint PPR', 'DraftKings','FanDuel']

SCORING_TYPE_COL_MATCHING = {'Normal':'FantPt', 'PPR':'PPR', 'Halfpoint PPR':'HalfpointPPR', 'DraftKings':'DKPt', 'FanDuel':'FDPt'}

SCORING_TYPE_TOOL_TIP = {'Normal':'trad style<br/>  blah blah', 'PPR':'PPR style', 'Halfpoint PPR':'Halfpoint PPR', 'DraftKings':'Draft Kings Style', 'FanDuel':'Fan Duel Style'}

SELECTION_DETAILS_COLS = {'Normal':['FantPt','FantPtpG','Player','year'], 
                          'PPR':['PPR','PPRpG','Player','year'],
                          'Halfpoint PPR':['HalfpointPPR','HalfpointPPRpG','Player','year'],
                          'DraftKings':['DKPt','DKPtpG','Player','year'], 
                          'FanDuel':['FDPt','FDPtpG','Player','year']}

def get_y(scoring_type, normalize_check):
    "Helper function to get the appropriate score column to display on stripplot y axis"
    if normalize_check:
        return SCORING_TYPE_COL_MATCHING[scoring_type] + 'pG'
    return SCORING_TYPE_COL_MATCHING[scoring_type]

def get_pivot_table(df, start, end, agg_func, col_to_agg_name):
    """Function to get yearly player data to plot on stripplot based on user input
       Shout out to mito for making this way easier to do: https://www.trymito.io/ 
    """
    #Filter dataframe according to years specified by user
    df = df[df.year.isin(range(int(start), int(end) + 1))]
    #Drop columns I don't need
    unused_columns = df.columns.difference(set(['Player','FantPos']).union(set([])).union(set({col_to_agg_name})))
    tmp_df = df.drop(unused_columns, axis=1)
    #Compile pivot table df
    pivot_table = tmp_df.pivot_table(
        index=['Player','FantPos'],
        values=[col_to_agg_name],
        aggfunc={col_to_agg_name: [agg_func]}
    )
    #Formatting stuff
    pivot_table.set_axis([col for col in pivot_table.keys()], axis=1, inplace=True)
    fantasy_points_by_year_pivot = pivot_table.reset_index()
    fantasy_points_by_year_pivot.columns = ['Player', 'FantPos', col_to_agg_name]
    #round last column if needed
    if agg_func != 'sum':
        fantasy_points_by_year_pivot[col_to_agg_name] = fantasy_points_by_year_pivot[col_to_agg_name].round(1)
    return fantasy_points_by_year_pivot

#Sidebar for user input
st.sidebar.header('Season Total Data Settings')

start_year, end_year = st.sidebar.select_slider(
     'Range of Years to Include',
     options=list(range(2019,2022)),
     value=(2019,2021))

#Aggregation function
selected_agg_func = st.sidebar.radio('Aggregation Method to Apply',['sum','mean'])

#Option to normalize
selected_to_normalize = st.sidebar.checkbox('Normalize by games played', value=False)

#Allow user to enter a point floor
point_value_floor = st.sidebar.number_input('Point Floor for Chart Display', value=0, min_value=0)

selected_scoring_type = st.sidebar.selectbox('Fantasy Point Scoring Style', SCORING_TYPES)

with st.sidebar.expander("See scoring style details"):
     st.write('feature under construction')

#Get a df for charting season totals data based upon user entry
column_name_to_chart = get_y(selected_scoring_type, selected_to_normalize)

pivot_df = get_pivot_table(data, start_year, end_year, selected_agg_func, column_name_to_chart)

st.header('Stripplot by Position')
st.markdown("""
Hover over points on the chart to view player name and fantasy point value.
""")

#Add a new area to allow for a user to indicate which players have already been drafted
with st.expander('Players Already Drafted'):
    players_already_drafted = st.multiselect('Indicate Players Already Taken',
        distinct_player_names)

#Add an area to allow for a user to indicate which players he's watching to draft next
with st.expander('Player Watch List'):
    selected_players_to_compare = st.multiselect(
     'Select Players to Watch',
     distinct_player_names)

#Create a stripplot
#Get the slice of your dataframe to plot
stripplot_data = pivot_df[(pivot_df['Player'].isin(players_already_drafted) == False) & (pivot_df[column_name_to_chart] >= point_value_floor)]

#Get values to use as the min and max values for the y-axis
stripplot_y_max = stripplot_data[column_name_to_chart].max() + 10

stripplot_y_min = point_value_floor

#compile the plot
stripplot =  alt.Chart(stripplot_data).mark_circle(size=50).encode(
    x=alt.X(
        'jitter:Q',
        title=None,
        axis=alt.Axis(ticks=True, grid=False, labels=False),
        scale=alt.Scale(),
    ),
    y=alt.Y(f'{column_name_to_chart}:Q',
            scale=alt.Scale(
            domain=(stripplot_y_min, stripplot_y_max)),
                axis=alt.Axis(title=None)),
    color=alt.Color('FantPos', legend=None),
    tooltip=['Player', column_name_to_chart],
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
).properties(
    height=400, 
    width=150
)

#Write out the charts to streamlit app
st.altair_chart(stripplot)

#Write out top 10 available players
st.subheader(f'Top Available by {column_name_to_chart}')
positions_selected = st.multiselect(
     'Positions Included',
     options=['QB','RB','WR','TE'],
     default=['QB','RB','WR','TE'])
st.write(stripplot_data[stripplot_data['FantPos'].isin(positions_selected)].sort_values(by=column_name_to_chart, ascending=False))

st.header('Watch List Analysis')

#Create Charts based upon Players to Watch
if selected_players_to_compare:
    #Need to refactor variable names here
    data_to_chart = weekly_data[weekly_data['player_name'].isin(selected_players_to_compare)]
    data_to_chart = data_to_chart[data_to_chart['fantasy_table_column']=='FantPt']
    
    #Get player image .jpg files and display them on screen
    unique_selected_ids = list(data_to_chart.player_id.unique()) 
    img_urls = [f'https://www.pro-football-reference.com/req/20180910/images/headshots/{id.split("/")[1]}_2021.jpg' for id in unique_selected_ids]
    st.image(img_urls, caption=selected_players_to_compare)

    #Reshape data for a trellis bar chart: https://altair-viz.github.io/gallery/bar_chart_trellis_compact.html
    trellis_data = data[data['Player'].isin(selected_players_to_compare)]
    trellis_data = trellis_data[['Player','year','HalfpointPPR','HalfpointPPRpG']]
    trellis_data = pd.melt(trellis_data, id_vars =['Player','year'], value_vars =['HalfpointPPR', 'HalfpointPPRpG'])

    #Construct trellis chart
    trellis_chart = alt.Chart(trellis_data).mark_bar().encode(
    y=alt.Y("Player:N", axis=None),
    x=alt.X("value:Q", title=None),
    color=alt.Color(
        "Player:N", title="Players", legend=alt.Legend(orient="bottom", titleOrient="left")
    ),
    row=alt.Row("year:O", title="Year", header=alt.Header(labelAngle=0)),
    column=alt.Column("variable:N", title="Metric")
    ).resolve_scale(x='independent')
    #Display trellis chart to user
    st.altair_chart(trellis_chart)

    #Create a simple bar chart to sum player totals across all shared years with points
    simple_bar_data = data[data['Player'].isin(selected_players_to_compare)]
    #Filter data so that only years are included where each player being watched registered points within the year
    year_value_counts = simple_bar_data['year'].value_counts()
    years_to_include = list(year_value_counts[year_value_counts ==  len(selected_players_to_compare)].index)
    simple_bar_data = simple_bar_data[simple_bar_data['year'].isin(years_to_include)]

    #Construct the chart
    simple_bar = alt.Chart(simple_bar_data).mark_bar().encode(
    x='Player:N',
    y='sum(HalfpointPPR):Q',
    color=alt.Color("Player:N", legend=None)
    )

    #Display the chart
    st.altair_chart(simple_bar, use_container_width=True)

    #Create layered density chart for detailed player comparison
    st.header('Fantasy Point Density Estimate Chart using Weekly Points Scored')
    st.markdown("""
    [Click for more info on density estimates](https://en.wikipedia.org/wiki/Kernel_density_estimation)
    """)
    
    extent_max = data_to_chart.value.max() + 1

    #Density estimate (https://altair-viz.github.io/gallery/density_stack.html)
    #Need this to be refactored so that halfpointppr is displayed
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