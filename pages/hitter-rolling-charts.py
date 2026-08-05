#hitter ability metrics
import streamlit as st
import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import seaborn as sns
import scipy as sp
import urllib
import os
import io


from datetime import timedelta
from matplotlib import ticker
from matplotlib import colors
from PIL import Image
from scipy import stats
from io import StringIO

logo_loc = 'https://github.com/Blandalytics/PLV_viz/blob/main/data/PL-text-wht.png?raw=true'
logo = Image.open(urllib.request.urlopen(logo_loc))
st.image(logo, width=200)

## Set Styling
# Plot Style
pl_white = '#FEFEFE'
pl_background = '#162B50'
pl_text = '#72a3f7'
pl_line_color = '#293a6b'

sns.set_theme(
    style={
        'axes.edgecolor': pl_white,
        'axes.facecolor': pl_background,
        'axes.labelcolor': pl_white,
        'xtick.color': pl_white,
        'ytick.color': pl_white,
        'figure.facecolor':pl_background,
        'grid.color': pl_background,
        'grid.linestyle': '-',
        'legend.facecolor':pl_background,
        'text.color': pl_white
     }
    )

line_color = sns.color_palette('vlag', n_colors=100)[0]

seasonal_constants = pd.read_csv('https://github.com/Blandalytics/PLV_viz/blob/main/data/plv_seasonal_constants.csv?raw=true').set_index('year')
## Selectors
col1, col2 = st.columns([0.5,0.5])
# Year
with col1:
    # Metric Selection
    year = st.selectbox('Choose a year:', [2026,2025,2024,2023,2022,2021,2020], index=0)
# Chart Format
with col2:
    # Metric Selection
    chart_format = st.selectbox('Choose a chart style:', ['Square','16:9'])

def z_score_scaler(series):
    return (series - series.mean()) / series.std()

season_names = {
    'PLV':'Pitch Runs',
    'swing_agg':'Swing Agg (%)',
    'strike_zone_judgement':'SZ Judge',
    'dec_val_runs_added':'Dec Value',
    'in_play_input':'Pitch Hittability',
    'whiff_runs_added':'Whiff Avoid',
    'bbe_qual_runs_added':'BBE Qual',
    'contact_ability_runs_added':'Contact',
    'gap_runs_added':'Gap Power',
    'hr_runs_added':'HR Power',
    'power_runs_added':'Power',
    'plv_runs_added':'Process',
    'hitter_runs_added':'HP'
}

# Load Data
@st.cache_data(ttl=900,show_spinner=f"Loading {year} data")
def load_season_data(year):
    df = pd.DataFrame()
    for month in range(3,11):
        file_name = f'https://github.com/Blandalytics/PLV_viz/blob/main/data/{year}_PLV_App_Data-{month}.parquet?raw=true'
        df = pd.concat([df,
                        pd.read_parquet(file_name)[['hittername','hitter_mlb_id','p_hand','b_hand','pitch_id','balls','strikes',
                                                 'zone_prob','PLV','swing_agg',
                                                 'strike_zone_judgement','decision_value','contact_over_expected',
                                                 'adj_power','batter_wOBA','dec_val_runs_added', 
                                                 'whiff_runs_added','bbe_qual_runs_added','contact_ability_runs_added',
                                                 'gap_runs_added','hr_runs_added',
                                                 'power_runs_added', 'plv_runs_added','hitter_runs_added','pitchtype','pitch_type_bucket',
                                                 'in_play_input','p_x','p_z','sz_z','strike_zone_top','strike_zone_bottom',
                                                 'game_played'
                                                   ]]
                       ],
                       ignore_index=True)
    
    df = df.reset_index(drop=True)

    df['pitchtype'] = df['pitchtype'].str.replace('SV','CU').str.replace('FO','FS')
    for stat in ['swing_agg','strike_zone_judgement','contact_over_expected','in_play_input']:
        df[stat] = df[stat].mul(100).astype('float')
    
    # Convert to runs added
    # df['decision_value'] = df['decision_value'].div(seasonal_constants.loc[year]['run_constant']).mul(100)
    # df['batter_wOBA'] = df['batter_wOBA'].div(seasonal_constants.loc[year]['run_constant']).mul(100)
    
    df['zone'] = 1
    df.loc[(df['p_x'].abs()>10/12) | 
            (df['sz_z'].abs()>0.5),'zone'] = 0

    df['decision_value_z'] = df['dec_val_runs_added'].mul(df['zone_prob'])
    df['decision_value_o'] = df['dec_val_runs_added'].mul(1 - df['zone_prob'])
    
    df['count'] = df['balls'].astype('str')+'-'+df['strikes'].astype('str')
    
    # buffer = io.BytesIO()
    # object=s3.Object('bucketeer-36fc68cd-e621-4eac-885d-541aa0f10b85',f'public/data/date_pitch_map.parquet')
    # object.download_fileobj(buffer)    
    # df['game_played'] = df['pitch_id'].map(pd.read_parquet(buffer).set_index('pitch_id').to_dict()['game_played'])
    # df['game_played'] = pd.to_datetime(df['game_played']).dt.date
    
    return df

plv_df = load_season_data(year)

# @st.cache_data(ttl=3600,show_spinner=f"Loading baseline data")
def load_baselines():
    file_name = 'https://github.com/Blandalytics/PLV_viz/blob/main/data/hitter_stat_baselines.csv?raw=true'
    return pd.read_csv(file_name)

grouped_df = load_baselines()

max_pitches = plv_df.groupby('hittername')['pitch_id'].count().max()
start_val = int(plv_df.groupby('hittername')['pitch_id'].count().quantile(0.4)/50)*50

# Num Pitches threshold
# pitch_thresh = st.number_input(f'Min # of Pitches faced:',
#                                min_value=min(100,start_val), 
#                                max_value=2000,
#                                step=50, 
#                                value=500)
pitch_thresh = 100 #hard code for now since seems redundant

### Rolling Charts
stat_names = {
    'PLV':'Pitch Runs',
    'swing_agg':'Swing Aggression',
    'strike_zone_judgement':'Strikezone Judgement',
    'dec_val_runs_added':'Decision Value',
    'decision_value_z':'In-Zone Decision Value',
    'decision_value_o':'Out-of-Zone Decision Value',
    'in_play_input':'Pitch Hittability',
    'whiff_runs_added':'Whiff Avoid',
    'bbe_qual_runs_added':'BBE Qual',
    'contact_ability_runs_added':'Contact Ability',
    'gap_runs_added':'Gap Power',
    'hr_runs_added':'HR Power',
    'power_runs_added':'Power',
    'plv_runs_added':'Process',
    'hitter_runs_added':'Hitter Performance'
}

stat_values = {
    'PLV':'Per-Pitch Quality',
    'swing_agg':'Swing Frequency, Above Expected',
    'strike_zone_judgement':'Ball/Strike Correctness',
    'dec_val_runs_added':'Runs Added, per 100 Pitches',
    'decision_value_z':'Runs Added, per 100 Pitches',
    'decision_value_o':'Runs Added, per 100 Pitches',
    'in_play_input':'Batted Ball Likelihood of Pitches',
    'whiff_runs_added':'Runs Added, per 100 Swings',
    'bbe_qual_runs_added':'Runs Added, per 100 Swings',
    'contact_ability_runs_added':'Runs Added, per 100 Swings',
    'gap_runs_added':'Runs Added, per 100 Batted Balls',
    'hr_runs_added':'Runs Added, per 100 Batted Balls',
    'power_runs_added':'Runs Added, per 100 Batted Balls',
    'plv_runs_added':'Runs Added, per 100 Pitches',
    'hitter_runs_added':'Runs Added, per 100 Pitches'
}

stat_colors = {
    'Pitch Runs':'w',
    'Swing Aggression':'w',
    'Strikezone Judgement':'w',
    'Decision Value':sns.color_palette('tab10')[4],
    'In-Zone Decision Value':sns.color_palette('tab10')[4],
    'Out-of-Zone Decision Value':sns.color_palette('tab10')[4],
    'Pitch Hittability':'w',
    'Whiff Avoid':sns.color_palette('tab10')[1],
    'BBE Qual':sns.color_palette('tab10')[1],
    'Contact Ability':sns.color_palette('tab10')[1],
    'Gap Power':sns.color_palette('tab10')[2],
    'HR Power':sns.color_palette('tab10')[2],
    'Power':sns.color_palette('tab10')[2],
    'Process':'w',
    'Hitter Performance':'w'
}


plv_df = plv_df.rename(columns=stat_names)

# Player
players = (
    plv_df
    .groupby(['hittername','hitter_mlb_id'])
    [['pitch_id','Process']]
    .agg({
        'pitch_id':'count',
        'Process':'mean'
    })
    .query(f'pitch_id >={pitch_thresh}')
    .sort_values('Process', ascending=False)
    .reset_index()
    .assign(id_col = lambda x: np.where(x.groupby('hittername')['hittername'].transform('count')==1,
                                        x['hittername'],
                                        x['hittername'].astype('str')+' - '+x['hitter_mlb_id'].astype('str')))
    .set_index('id_col')
    [['hitter_mlb_id','hittername']]
    .to_dict(orient='index')
)

default_player = list(players.keys()).index('Juan Soto')
player = st.selectbox('Choose a hitter:', list(players.keys()), index=default_player)
player_id = players[player]['hitter_mlb_id']
player_name = players[player]['hittername']

col1, col2 = st.columns([0.5,0.5])

with col1:
    # Metric Selection
    metrics = [x for x in list(stat_names.values()) if x != 'Process']
    default_stat = metrics.index('HR Power')
    metric = st.selectbox('Choose a metric:', metrics, index=default_stat)

with col2:
    # Pitchtype Selection
    pitchtype_help = '''
    **Fastballs**: 4-Seam, Sinkers, some Cutters\n
    **Breaking Balls**: Sliders, Sweepers, Curveballs, most Cutters\n
    **Offspeed**: Changeups, Splitters
    '''
    pitchtype_base = st.selectbox('Vs Pitchtype', 
                                  ['All','Fastballs', 'Breaking Balls', 'Offspeed'],
                                  index=0,
                                  help=pitchtype_help
                                    )
    if pitchtype_base == 'All':
        pitchtype_select = ['Fastball', 'Breaking Ball', 'Offspeed', 'Other']
    else:
        pitchtype_select = [pitchtype_base] if pitchtype_base=='Offspeed' else [pitchtype_base[:-1]] # remove the 's'

rolling_denom = {
    'Pitch Runs':'Pitches Faced',
    'Swing Aggression':'Pitches Faced',
    'Strikezone Judgement':'Pitches Faced',
    'Decision Value':'Pitches Faced',
    'In-Zone Decision Value':'Pitches Faced',
    'Out-of-Zone Decision Value':'Pitches Faced',
    'Pitch Hittability':'Pitches Faced',
    'Whiff Avoid':'Swings',
    'BBE Qual':'Swings',
    'Contact Ability':'Swings',
    'Gap Power': 'BBE',
    'HR Power': 'BBE',
    'Power': 'BBE',
    'Process':'Pitches Faced',
    'Hitter Performance':'Pitches Faced'
}

rolling_threshold = {
    'Pitch Runs':800,
    'Swing Aggression':400,
    'Strikezone Judgement':400,
    'Decision Value':400,
    'In-Zone Decision Value':200,
    'Out-of-Zone Decision Value':200,
    'Pitch Hittability':400,
    'Whiff Avoid':200,
    'BBE Qual':200,
    'Contact Ability':200,
    'Gap Power':75,
    'HR Power':75,
    'Power': 75,
    'Process':400,
    'Hitter Performance':800
}

count_select = st.radio('Count Group', 
                        ['All','Hitter-Friendly','Pitcher-Friendly','Early','Late','Even','2-Strike','3-Ball','Custom'],
                        index=0,
                        horizontal=True
                       )
 
if count_select=='All':
    selected_options = ['0-0', '1-0', '2-0', '3-0', '0-1', '1-1', '2-1', '3-1', '0-2', '1-2', '2-2', '3-2']
elif count_select=='Hitter-Friendly':
    selected_options = ['1-0', '2-0', '3-0', '2-1', '3-1']
elif count_select=='Pitcher-Friendly':
    selected_options = ['0-1','0-2','1-2']
elif count_select=='Early':
    selected_options = ['0-0','0-1','1-0']
elif count_select=='Late':
    selected_options = ['2-0', '3-0', '1-1', '2-1', '3-1', '0-2', '1-2', '2-2', '3-2']
elif count_select=='Even':
    selected_options = ['0-0','1-1','2-2']
elif count_select=='2-Strike':
    selected_options = ['0-2','1-2','2-2','3-2']
elif count_select=='3-Ball':
    selected_options = ['3-0','3-1','3-2']
else:
    selected_options = st.multiselect('Select the count(s):',
                                       ['0-0', '1-0', '2-0', '3-0', '0-1', '1-1', '2-1', '3-1', '0-2', '1-2', '2-2', '3-2'],
                                       ['0-0', '1-0', '2-0', '3-0', '0-1', '1-1', '2-1', '3-1', '0-2', '1-2', '2-2', '3-2'])

# Hitter Handedness
handedness = st.select_slider(
    'Pitcher Handedness',
    options=['Left', 'All', 'Right'],
    value='All')
# Pitcher Handedness
if handedness=='All':
    hitter_hand = ['L','R']
else:
    hitter_hand = [plv_df.loc[(plv_df['hitter_mlb_id']==player_id) & (plv_df['p_hand']==handedness[0]),'b_hand'].value_counts().index[0]]

hand_map = {
    'Left':['L'],
    'All':['L','R'],
    'Right':['R']
}

sample_size = (plv_df
                  .sort_values('pitch_id')
                  .loc[(plv_df['hitter_mlb_id']==player_id) &
                       plv_df['p_hand'].isin(hand_map[handedness]) &
                       plv_df['count'].isin(selected_options) &
                       plv_df['pitch_type_bucket'].isin(pitchtype_select),
                       ['pitch_id',metric]]
                  .dropna()
              ).shape[0]

default_sample = np.clip(int(sample_size/20)*10,25,rolling_threshold[metric])

window_max = max(rolling_threshold[metric],
                 int(round(sample_size/10)*7))

if metric == 'Process':
    col1, col2 = st.columns(2)
    with col1:
        # Rolling Window
        window = st.number_input(f'Rolling {rolling_denom[metric]}:', 
                                 min_value=25, 
                                 max_value=window_max,
                                 step=5, 
                                 value=default_sample)
    with col2:
        graphic_filter = st.selectbox('Select graphic filter:', ['Standard','Line Only','Bar Only'], index=0)
else:
    # Rolling Window
    window = st.number_input(f'Rolling {rolling_denom[metric]}:', 
                             min_value=25, 
                             max_value=window_max,
                             step=5, 
                             value=default_sample)
    graphic_filter = ''

updated_threshold = int(round(window*len(selected_options)/12/5)*5)

plv_df[metric] = plv_df[metric].replace([np.inf, -np.inf], np.nan)
if metric!='Process':
    rolling_df = (plv_df
                  .sort_values('pitch_id')
                  .loc[(plv_df['hitter_mlb_id']==player_id) &
                       plv_df['p_hand'].isin(hand_map[handedness]) &
                       plv_df['count'].isin(selected_options) &
                       plv_df['pitch_type_bucket'].isin(pitchtype_select),
                       ['hittername','game_played',metric]]
                  .dropna()
                  .reset_index(drop=True)
                  .reset_index()
                  .rename(columns={'index':'pitches_faced'})
                 )

    chart_thresh_list = (plv_df
                         .loc[plv_df['count'].astype('str').isin(selected_options) &
                              plv_df['pitch_type_bucket'].isin(pitchtype_select) &
                              plv_df['b_hand'].isin(hitter_hand) &
                              plv_df['p_hand'].isin(hand_map[handedness])
                             ]
                         .groupby('hitter_mlb_id')
                         [['pitch_id',metric]]
                         .agg({
                             'pitch_id':'count',
                             metric:'mean'
                         })
                         .query(f'pitch_id >= {updated_threshold}')
                         .copy()
                        )
    chart_avgs = chart_thresh_list[metric].mean()
else:
    rolling_df = (plv_df
                  .fillna({'Decision Value':0,
                           'Contact Ability':0,
                           'Power':0,
                           'Process':0})
                  .sort_values('pitch_id')
                  .loc[(plv_df['hitter_mlb_id']==player_id) &
                       plv_df['p_hand'].isin(hand_map[handedness]) &
                       plv_df['count'].isin(selected_options) &
                       plv_df['pitch_type_bucket'].isin(pitchtype_select),
                  ['hittername', 'game_played', 'Decision Value', 'Contact Ability', 'Power', 'Process']]
                  .reset_index(drop=True)
                  .reset_index()
                  .rename(columns={'index':'pitches_faced'})
                  )
    
    chart_thresh_list = (plv_df
                         .fillna({'Decision Value':0,
                           'Contact Ability':0,
                           'Power':0,
                           'Process':0})
                         .loc[plv_df['count'].astype('str').isin(selected_options) &
                              plv_df['pitch_type_bucket'].isin(pitchtype_select) &
                              plv_df['b_hand'].isin(hitter_hand) &
                              plv_df['p_hand'].isin(hand_map[handedness])
                             ]
                         .groupby('hitter_mlb_id')
                         [['pitch_id','Decision Value','Contact Ability', 'Power', 'Process']]
                         .agg({
                             'pitch_id':'count',
                             'Decision Value':'mean',
                             'Contact Ability':'mean',
                             'Power':'mean',
                             'Process':'mean'
                         })
                         .query(f'pitch_id >= {updated_threshold}')
                         .copy()
                        )
    
    chart_avgs = chart_thresh_list[['Decision Value','Contact Ability', 'Power', 'Process']].mean()

    try: 
        fill_vals = list(grouped_df.loc[(grouped_df['hittername']==player) & (grouped_df['year_played']==year-1),['fill_dec_val','fill_contact', 'fill_power', 'fill_process']].to_dict(orient='index').values())[0]
    except:
        fill_vals = {
            'fill_dec_val': 0,#chart_avgs['Decision Value'],
            'fill_contact': 0,#chart_avgs['Contact Ability'],
            'fill_power': 0,#chart_avgs['Power'],
            'fill_process': 0,#chart_avgs['Process']
            }
        
    rolling_df = pd.concat([pd.DataFrame([[0,player_name,
                                           rolling_df['game_played'].min()-pd.Timedelta(1, "d"),
                                           fill_vals['fill_dec_val'],
                                           fill_vals['fill_contact'],
                                           fill_vals['fill_power'],
                                           fill_vals['fill_process']]]*int(2.25*window-1),
                                         columns=['pitches_faced','hittername', 'game_played', 'Decision Value',
                                                  'Contact Ability', 'Power', 'Process']),
                            rolling_df],
                           ignore_index=True
                          )

st.write(f'{player_name} has {sample_size} {rolling_denom[metric]}')

chart_avg = chart_thresh_list[metric].mean()
chart_stdev = chart_thresh_list[metric].std()

if (metric in ['Swing Aggression','Pitch Hittability']):
    chart_90 = chart_thresh_list[metric].quantile(0.9)
    chart_75 = chart_thresh_list[metric].quantile(0.75)
    chart_25 = chart_thresh_list[metric].quantile(0.25)
    chart_10 = chart_thresh_list[metric].quantile(0.1)
elif metric == 'Pitch Runs':
    chart_90 = (chart_avg-chart_thresh_list[metric].quantile(0.1))/chart_stdev*15+100
    chart_75 = (chart_avg-chart_thresh_list[metric].quantile(0.25))/chart_stdev*15+100
    chart_25 = (chart_avg-chart_thresh_list[metric].quantile(0.75))/chart_stdev*15+100
    chart_10 = (chart_avg-chart_thresh_list[metric].quantile(0.9))/chart_stdev*15+100
else:
    chart_90 = (chart_thresh_list[metric].quantile(0.9)-chart_avg)/chart_stdev*15+100
    chart_75 = (chart_thresh_list[metric].quantile(0.75)-chart_avg)/chart_stdev*15+100
    chart_25 = (chart_thresh_list[metric].quantile(0.25)-chart_avg)/chart_stdev*15+100
    chart_10 = (chart_thresh_list[metric].quantile(0.1)-chart_avg)/chart_stdev*15+100
    
if metric != 'Process':
    rolling_df['Rolling_Stat'] = rolling_df[metric].rolling(window).mean()
    fixed_window = window if (rolling_df[metric].mean() < rolling_df['Rolling_Stat'].max()) and (rolling_df[metric].mean() > rolling_df['Rolling_Stat'].min()) else int(window*2/3)
    rolling_df['Rolling_Stat'] = rolling_df[metric].rolling(window, min_periods=fixed_window).mean()
    if metric != 'Pitch Runs':
        rolling_df['Rolling_Stat+'] = rolling_df['Rolling_Stat'].sub(chart_avg).div(chart_stdev).mul(15).add(100)
    else:
        rolling_df['Rolling_Stat+'] = (chart_avg-rolling_df['Rolling_Stat'])/chart_stdev*15+100
    season_avg = rolling_df[metric].mean() if (metric in ['Swing Aggression','Pitch Hittability']) else rolling_df['Rolling_Stat+'].mean()
else:
    for stat in ['Decision Value', 'Contact Ability']:
        rolling_df['rolling_'+stat] = rolling_df[stat].rolling(updated_threshold).mean()
        
    rolling_df['rolling_Power'] = rolling_df['Power'].rolling(int(updated_threshold*2.25)).mean()
    
    rolling_df['rolling_Process'] = rolling_df[['rolling_Decision Value','rolling_Contact Ability','rolling_Power']].sum(axis=1)
    rolling_df['rolling_Process+'] = rolling_df['rolling_Process'].sub(chart_avg).div(chart_stdev).mul(15).add(100)

rolling_df['game_played'] = pd.to_datetime(rolling_df['game_played']).dt.date
rolling_df = rolling_df.loc[rolling_df['pitches_faced']==rolling_df['pitches_faced'].groupby(rolling_df['game_played']).transform('max')].copy()

chart_week = min(datetime.date(year,10,1),datetime.datetime.today().date()).isocalendar()[1]
data_date = plv_df['game_played'].max()

def rolling_chart(filename,chart_format):  
    if chart_format=='Square':
        fig, ax = plt.subplots(figsize=(6,5.5))
    else:
        fig, ax = plt.subplots(figsize=(32/3,5.5))
    sns.lineplot(data=rolling_df,
                 x='game_played',
                 y='Rolling_Stat' if (metric in ['Swing Aggression','Pitch Hittability']) else 'Rolling_Stat+',
                 color='#fefefe',
                 linewidth=2,
                   )
    
    line_text_loc = rolling_df['game_played'].min() + pd.Timedelta(days=int((rolling_df['game_played'].max() - rolling_df['game_played'].min()).days * 1.05)+1)
    
    ax.axhline(season_avg, 
               color='w',
               linestyle='--')
    ax.text(line_text_loc,
            season_avg,
            'Szn Avg',
            va='center',
            color='w')

    # Threshold Lines
    ax.axhline(chart_90,
               color=sns.color_palette('vlag', n_colors=100)[99],
               alpha=0.6)
    ax.axhline(chart_75,
               color=sns.color_palette('vlag', n_colors=100)[79],
               linestyle='--',
               alpha=0.5)
    ax.axhline(chart_avg if (metric in ['Swing Aggression','Pitch Hittability']) else 100,
               color='w',
               alpha=0.5)
    ax.axhline(chart_25,
               color=sns.color_palette('vlag', n_colors=100)[19],
               linestyle='--',
               alpha=0.5)
    ax.axhline(chart_10,
               color=sns.color_palette('vlag', n_colors=100)[0],
               alpha=0.6)
    
    ax.text(line_text_loc,
            chart_90,
            '90th %' if abs(chart_90 - season_avg) > (ax.get_ylim()[1] - ax.get_ylim()[0])/25 else '',
            va='center',
            color=sns.color_palette('vlag', n_colors=100)[99],
            alpha=1)
    ax.text(line_text_loc,
            chart_75,
            '75th %' if abs(chart_75 - season_avg) > (ax.get_ylim()[1] - ax.get_ylim()[0])/25 else '',
            va='center',
            color=sns.color_palette('vlag', n_colors=100)[74],
            alpha=1)
    ax.text(line_text_loc,
            chart_avg if (metric in ['Swing Aggression','Pitch Hittability']) else 100,
            'MLB Avg' if abs((chart_avg if (metric in ['Swing Aggression','Pitch Hittability']) else 100) - season_avg) > (ax.get_ylim()[1] - ax.get_ylim()[0])/25 else '',
            va='center',
            color='w',
            alpha=0.75)
    ax.text(line_text_loc,
            chart_25,
            '25th %' if abs(chart_25 - season_avg) > (ax.get_ylim()[1] - ax.get_ylim()[0])/25 else '',
            va='center',
            color=sns.color_palette('vlag', n_colors=100)[24],
            alpha=1)
    ax.text(line_text_loc,
            chart_10,
            '10th %' if abs(chart_10 - season_avg) > (ax.get_ylim()[1] - ax.get_ylim()[0])/25 else '',
            va='center',
            color=sns.color_palette('vlag', n_colors=100)[9],
            alpha=1)
    
    y_pad = (chart_90-chart_10)/10
    
    chart_min = min(chart_10,
                    rolling_df['Rolling_Stat'].min() if (metric in ['Swing Aggression','Pitch Hittability']) else rolling_df['Rolling_Stat+'].min()
                   ) - y_pad
    
    chart_max = max(chart_90,
                    rolling_df['Rolling_Stat'].max() if (metric in ['Swing Aggression','Pitch Hittability']) else rolling_df['Rolling_Stat+'].max()
                   ) + y_pad
    
    plus_text = ''  if (metric in ['Swing Aggression','Pitch Hittability']) else '+'
    
    ax.set(xlabel='Game Date',
           ylabel=metric+plus_text,
           ylim=(chart_min, 
                 chart_max)           
          )
    
    if metric in 'Swing Aggression':
        ax.set_yticks(ax.get_yticks())
        ax.set_yticklabels([f'{int(x)}%' for x in ax.get_yticks()])

    if metric =='Pitch Hittability':
        ax.set_yticks(ax.get_yticks())
        ax.set_yticklabels([f'{x:.1f}%' for x in ax.get_yticks()])
        
    locator = mdates.AutoDateLocator(minticks=3, maxticks=7)
    formatter = mdates.ConciseDateFormatter(locator,
                                            show_offset=False,
                                           formats=['%Y', '%-m/1', '%-m/%-d', '%H:%M', '%H:%M', '%S.%f'])
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(formatter)

    pitch_text = f'; vs {pitchtype_select[0]}' if pitchtype_base == 'Offspeed' else f'; vs {pitchtype_select[0]}s'
    
    fig.suptitle("{}'s {} {}\n{}".format(player_name,
                                                 year,
                                                 metric+plus_text,
                                                 '(Rolling {} {}{}{}{})'.format(window,
                                                                      rolling_denom[metric],
                                                                      '' if pitchtype_base == 'All' else pitch_text,
                                                                      '' if count_select=='All' else f'; in {','.join(selected_options)} counts' if count_select=='Custom' else f'; in {count_select} Counts',
                                                                      '' if (handedness=='All') else f'; {hitter_hand[0]}HH vs {hand_map[handedness][0]}HP'
                                                                     )
                                                ),
                 fontsize=14,
                 x=0.55
                )

    # Add PL logo
    if chart_format=='Square':
        pl_ax = fig.add_axes([0.8,-0.01,0.2,0.2], anchor='SE', zorder=1)
    else:
        pl_ax = fig.add_axes([0.8,-0.07,0.2,0.2], anchor='SE', zorder=1)
    pl_ax.imshow(logo)
    pl_ax.axis('off')
    fig.text(0.1,0.01,f'As of {data_date.strftime('%-m-%-d-%Y')}',ha='center',fontsize=10)
    
    sns.despine(left=True,bottom=True)
    #plot the fig
    st.pyplot(fig)

def process_chart(filename, chart_format, graphic_filter):   
    color_scheme = [sns.color_palette('tab10')[4]]+[sns.color_palette('tab10')[1]]+[sns.color_palette('tab10')[2]]
    cmap = colors.LinearSegmentedColormap.from_list('plv_hitter_stats', color_scheme, N=3)
    bar_df = pd.DataFrame({'game_played' : pd.date_range(start=rolling_df.loc[rolling_df['pitches_faced']>0,'game_played'].min(), 
                                                         end=rolling_df['game_played'].max(), freq='d')})
    bar_df['game_played'] = pd.to_datetime(bar_df['game_played']).dt.date
    games = bar_df['game_played'].unique()
    bar_df = bar_df.merge(rolling_df,
                          how='left',on='game_played')
    bar_df['pitches_faced'] = bar_df['pitches_faced'].ffill()
    
    bar_df = (bar_df
              .drop(columns=['Decision Value', 'Contact Ability','Power','Process'])
              .loc[bar_df['pitches_faced']>0]
                  # ['game_played','rolling_Decision Value','rolling_Contact Ability','rolling_Power','rolling_Process']]
              .rename(columns={'game_played':'Game Played',
                               'rolling_Decision Value':'Decisions',
                               'rolling_Contact Ability':'Contact',
                               'rolling_Power':'Power',
                               # 'rolling_Process':'Process'
                              })
              .set_index('Game Played')
              [['Decisions', 'Contact', 'Power', 
                # 'Process'
               ]]
              .div(chart_stdev).mul(15)
             )
    bar_df['Process'] = bar_df[['Decisions','Contact','Power']].sum(axis=1,min_count=1)
    if chart_format=='Square':
        fig, ax = plt.subplots(figsize=(6,5))
    else:
        fig, ax = plt.subplots(figsize=(32/3,5))
    if graphic_filter!='Line Only':
        bar_df[['Decisions','Contact','Power']].plot(kind='bar', cmap=cmap, 
                                                     stacked=True,ax=ax,
                                                     edgecolor=pl_background,
                                                     linewidth=1/3, width=1)
    ylim_high = max(175,
               max(list(sum(x) for x in np.where(bar_df[['Decisions','Contact','Power']]>0,
                                                 bar_df[['Decisions','Contact','Power']],
                                                 0)))+105,
               bar_df['Process'].max()+105)
    ylim_low = min(50,
                   min(list(sum(x) for x in np.where(bar_df[['Decisions','Contact','Power']]<0,
                                                     bar_df[['Decisions','Contact','Power']],
                                                     0)))+95,
                   bar_df['Process'].min()+95)
    
    ax.set(xlim=(ax.get_xlim()[0],ax.get_xlim()[1]),
           ylim=(ylim_low,
                 ylim_high))
    ax.xaxis.set_visible(False)
    ax.axhline(0,color='w',alpha=0.75)
    
    ax.legend(ncol=3,bbox_to_anchor=(0.48,.99),
              loc='lower center',
              edgecolor=pl_background
             )

    ax2 = ax.twiny()
    if graphic_filter!='Bar Only':
        sns.lineplot(data=bar_df['Process'].reset_index(),
                     x='Game Played',
                     y='Process',
                     color='#fefefe',
                     linewidth=2,
                     ax=ax2)
    ax2.xaxis.tick_bottom()
    ax2.set(xlim=(bar_df.reset_index()['Game Played'].min()-timedelta(days=1),bar_df.reset_index()['Game Played'].max() + timedelta(days=1)),
            ylim=(ylim_low-100,
                  ylim_high-100),
           xlabel='')

    process_range = [(x*25)-100 for x in range(int(ylim_low/25),int(ylim_high/25+1))]
    ax2.set_yticks(process_range)
    ax2.set_yticklabels([int(y+100) for y in ax2.get_yticks()])
    
    locator = mdates.AutoDateLocator(minticks=3, maxticks=9)
    formatter = mdates.ConciseDateFormatter(locator,
                                            show_offset=False,
                                           formats=['%Y', '%-m/1', '%-m/%-d', '%H:%M', '%H:%M', '%S.%f'])
    ax2.xaxis.set_major_locator(locator)
    ax2.xaxis.set_major_formatter(formatter)
    
    # Add PL logo
    if graphic_filter == 'Standard':
        if chart_format=='Square':
            pl_ax = fig.add_axes([0.41,-0.04,0.2,0.2], anchor='S', zorder=1)
        else:
            pl_ax = fig.add_axes([0.41,-0.09,0.2,0.2], anchor='S', zorder=1)
        pl_ax.imshow(logo)
        pl_ax.axis('off')
        fig.text(0.15,0.004,f'As of {data_date.strftime('%-m-%-d-%Y')}',ha='center',fontsize=9)
    
        pitch_text = f'; vs {pitchtype_select[0]}' if pitchtype_base == 'Offspeed' else f'; vs {pitchtype_select[0]}s'
        
        filter_text = '(Rolling {} {}{}{}{})'.format(window,
                                                      rolling_denom[metric],
                                                     '' if pitchtype_base == 'All' else pitch_text,
                                                      '' if count_select=='All' else f'; in {''.join(','.join(selected_options))} counts' if count_select=='Custom' else f'; in {count_select} Counts',
                                                     '' if (handedness=='All') else f'; {hitter_hand[0]}HH vs {hand_map[handedness][0]}HP'
                                                     )
        fig.suptitle(f"{player_name}'s {year} Process+\n{filter_text}",y=1.03)
    else:
        ax.axis('off')
        ax2.axis('off')
        ax.get_legend().remove()
        fig.patch.set_alpha(0)
    sns.despine(left=True,bottom=True)
    
    #save the fig as image for next time
    #plot the fig
    st.pyplot(fig)

if window > sample_size:
    st.write(f'Not enough {rolling_denom[metric]} ({sample_size})')
elif st.button("Generate Visualization"):
    filename = f'{year}/{player_name}-{metric}-{pitchtype_base}-{count_select}-{handedness}-{window}-{chart_week}.png'.replace(' ','-').lower()
    # # Use image saved on the server if it exists
    # if (key_exists(client, AWS_S3_BUCKET, filename) == 'true') & (year >= 2024) & (player != 'Juan Soto'):
    #     # object = bucket.Object(filename)
    #     # img_data = object.get().get('Body').read()
    #     # img = get_image(bucket, filename)
    #     # st.image(img, use_column_width='always')
    #     st.markdown(f"![image](https://s3.amazonaws.com/{AWS_S3_BUCKET}/{filename}#full)")
    # else:
    rolling_chart(filename, chart_format)
    
st.title("Metric Descriptions:")
st.write('- ***Pitch Runs***: The quality of the pitches a hitter has faced. A higher number means the pitches were expected to yield more runs (so they were "easier" pitches).')
st.write('- ***Swing Aggression*** (% above/below lg avg): How much more often a hitter swings at pitches, given the swing likelihoods of the pitches they face.')
st.write('''
- ***Strikezone Judgment***: The "correctness" of a hitter's swings and takes, using the likelihood of a pitch being a called strike (for swings) or a ball/HBP (for takes).
''')
st.write("- ***Pitch Hittability***: The modeled likelihood of the pitches a hitter faces becoming batted balls.")
st.write("- ***Decision Value*** (runs per pitch): The modeled value of a hitter's decision to swing or take. These are also broken into 'Zone' and 'Out-of-Zone' components (credit to [Robert Orr](https://twitter.com/NotTheBobbyOrr)'s [SEAGER article](https://www.baseballprospectus.com/news/article/86572/the-crooked-inning-corey-seager-rangers/) and [@TJStats](https://twitter.com/TJStats) for the idea).")
st.write("- ***Whiff Avoid*** (runs added per swing): The modeled value of whiffing (or not), above the whiff expectation of each pitch.")
st.write("- ***BBE Qual*** (runs added per swing): The modeled value of a batted ball in play of each pitch, above the batted ball expectation.")
st.write("- ***Contact Ability*** (runs added per swing): The modeled value of the hitter making contact (or not), above the contact expectation of each pitch.")
st.write("- ***Gap Power*** (runs added per batted ball): The modeled non-HR hit value of each batted ball, above a pitch's non-HR hit expectation.")
st.write("- ***HR Power*** (runs added per batted ball): The modeled home run value of each batted ball, above a pitch's home run expectation.")
st.write("- ***Power*** (runs added per batted ball): The modeled value of each batted ball, above a pitch's expectation.")
st.write("- ***Process*** (runs added per pitch): The combined value of a hitter's Decision Value, Contact Ability, and Power.")
st.write("- ***Hitter Performance (HP; runs added per pitch)***: Runs added by the hitter (including swing/take decisions), after accounting for pitch quality.")
st.write()
