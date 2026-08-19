#hitter ability metrics
import streamlit as st
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import pandas as pd
import seaborn as sns
import scipy as sp
import urllib
import os
import io


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

seasonal_constants = pd.read_csv('https://github.com/Blandalytics/streamlit_backup/blob/main/data/plv_seasonal_constants.csv?raw=true').set_index('year')

## Selectors
# Year
year = st.selectbox('Choose a year:', [2026,2025,2024,2023,2022,2021,2020],index=0)

def z_score_scaler(series):
    return (series - series.mean()) / series.std()

season_names = {
    'swing_agg':'Swing Agg (%)',
    'contact_over_expected':'Contact% Added',
    'strike_zone_judgement':'SZ Judge',
    'in_play_input':'Hittable Pitch%',
    'dec_val_runs_added':'Dec Value',
    'whiff_runs_added':'Whiff Avoid',
    'bbe_qual_runs_added':'BBE Qual',
    'contact_ability_runs_added':'Contact',
    'gap_runs_added':'Gap Power',
    'hr_runs_added':'HR Power',
    'power_runs_added':'Power',
    'plv_runs_added':'Process',
    'hitter_runs_added':'Perf',
    're12':'Results'
}

# Load Data
@st.cache_data(ttl=600,show_spinner=f"Loading {year} data")
def load_season_data(year, stat_agg):
    df = pd.DataFrame()
    for month in range(3,11):
        file_name = f'https://github.com/Blandalytics/streamlit_backup/blob/main/data/{year}_PLV_App_Data-{month}.parquet?raw=true'
        df = pd.concat([df,
                        pd.read_parquet(file_name)[['hittername','p_hand','b_hand','pitch_id','hitterteam','balls','strikes','swing_agg',
                                                 'strike_zone_judgement','decision_value','contact_over_expected',
                                                 'adj_power','batter_wOBA','PLV','hitter_mlb_id','zone_prob',
                                                 'dec_val_runs_added','swing_runs_added','take_runs_added', 
                                                 'whiff_runs_added','bbe_qual_runs_added','contact_ability_runs_added',
                                                 'gap_runs_added','hr_runs_added','power_runs_added', 
                                                 'plv_runs_added','hitter_runs_added','re12','pitchtype','pitch_type_bucket',
                                                 'in_play_input','p_x','p_z','sz_z','strike_zone_top','strike_zone_bottom','game_played'
                                                   ]]
                       ])
    
    df = df.reset_index(drop=True)

    df['pitchtype'] = df['pitchtype'].str.replace('SV','CU').str.replace('FO','FS')
    df.loc[df['p_x'].notna(),'kde_x'] = np.clip(df.loc[df['p_x'].notna(),'p_x'].astype('float').mul(12).round(0).astype('int').div(12),
                                                -20/12,
                                                20/12)
    df.loc[df['sz_z'].notna(),'kde_z'] = np.clip(df.loc[df['sz_z'].notna(),'sz_z'].astype('float').mul(24).round(0).astype('int').div(24),
                                                 -1.5,
                                                 1.25)
    
    df['base_decision_value'] = df['decision_value'].groupby([df['p_hand'],
                                                              df['b_hand'],
                                                              df['pitchtype'],
                                                              df['kde_x'],
                                                              df['kde_z'],
                                                              df['balls'],
                                                              df['strikes']]).transform('mean')
    df['base_power'] = df['adj_power'].groupby([df['p_hand'],
                                                df['b_hand'],
                                                df['pitchtype'],
                                                df['kde_x'],
                                                df['kde_z'],
                                                df['balls'],
                                                df['strikes']]).transform('mean')

    df['sa_oa'] = df['swing_agg'].copy()
    df['dv_oa'] = df['decision_value'].sub(df['base_decision_value'])
    df['ca_oa'] = df['contact_over_expected'].copy()
    df['pow_oa'] = df['adj_power'].sub(df['base_power'])

    
    df.loc[df['sz_z'].notna(),'kde_z'] = np.clip(df.loc[df['sz_z'].notna(),'p_z'].astype('float').mul(12).round(0).astype('int').div(12),
                                                 0,
                                                 4.5)
    percent_stats = []
    if stat_agg=='Rate':
        percent_stats += ['swing_agg','contact_over_expected','in_play_input']
    for stat in percent_stats:
        df[stat] = df[stat].mul(100).astype('float')
    
    df['zone'] = 1
    df.loc[(df['p_x'].abs()>10/12) | 
            (df['sz_z'].abs()>0.5),'zone'] = 0

    df['decision_value_z'] = df['dec_val_runs_added'].mul(df['zone_prob'])
    df['decision_value_o'] = df['dec_val_runs_added'].mul(1 - df['zone_prob'])
    
    df['count'] = df['balls'].astype('str')+'-'+df['strikes'].astype('str')
    df['game_played'] = pd.to_datetime(df['game_played']).dt.date
    
    return df

def load_talent_data(year):
    file_name = f'https://github.com/Blandalytics/PLV_viz/blob/main/data/hitter_talent_{year}.parquet'
    df = pd.read_parquet(file_name)
    return df

col1, col2 = st.columns([1,3])
with col1:
    stat_agg = st.selectbox('Stat Type', ['Rate','Volume',
                                          # 'Talent',
                                          ],index=0)
    if stat_agg != 'Talent':
        plv_df = load_season_data(year,stat_agg)
    else:
        plv_df = load_talent_data(year)
with col2:
    if stat_agg=='Rate':
        max_pitches = plv_df.groupby('hitter_mlb_id')['pitch_id'].count().max()
        start_val = np.clip(int(plv_df.groupby('hitter_mlb_id')['pitch_id'].count().quantile(0.4)/50)*50,50,400)
        
        # Num Pitches threshold
        pitch_thresh = st.number_input(f'Min # of Pitches faced:',
                                       min_value=0, 
                                       max_value=2000,
                                       step=50, 
                                       value=start_val)
    else:
        pitch_thresh = 0

if stat_agg != 'Talent':
    season_start = plv_df['game_played'].min()
    season_end = plv_df['game_played'].max()

    handedness = st.select_slider(
        'Pitcher Handedness',
        options=['Left', 'All', 'Right'],
        value='All')
    
    hand_map = {
        'Left':['L'],
        'All':['L','R'],
        'Right':['R']
    }

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(f"Start Date (Season started: {season_start:%b %d})", 
                                   season_start,
                                   min_value=season_start,
                                   max_value=season_end,
                                   format="MM/DD/YYYY")
    with col2:
        end_date = st.date_input(f"End Date (Season ended: {season_end:%b %d})", 
                                 season_end,
                                 min_value=season_start,
                                 max_value=season_end,
                                 format="MM/DD/YYYY")
    
    team_wide = st.checkbox("Team Stats",value=False,
                            help=" Group at the team level")
else:
    team_wide = None

agg_type = 'mean' if stat_agg=='Rate' else 'sum'
agg_dict = {
    'Pitches':'count',
    'SZ Judge':'mean',
    'Swing Agg (%)':agg_type,
    'Contact% Added':agg_type,
    'Hittable Pitch%':agg_type,
    'Pitch Runs':agg_type,
    'Dec Value':agg_type,
    'Whiff Avoid':agg_type,
    'BBE Qual':agg_type,
    'Contact':agg_type,
    'Gap Power':agg_type,
    'HR Power':agg_type,
    'Power':agg_type,
    'Process':agg_type,
    'Perf':agg_type,
    'zDV':agg_type,
    'oDV':agg_type,
    'Results':agg_type
             }
header_colors = {
    'zDV':'#9467bd',
    'oDV':'#9467bd',
    'Dec Value':'#9467bd',
    'Whiff Avoid':'#ff7f0e',
    'BBE Qual':'#ff7f0e',
    'Contact':'#ff7f0e',
    'Gap Power':'#2ca02c',
    'HR Power':'#2ca02c',
    'Power':'#2ca02c'
}

stat_constants = {
    "SZ Judge":{"mean":0.675316155,"std":0.0290055387},
    "Dec Value":{"mean":-0.0000503136,"std":0.0036539419},
    "zDV":{"mean":0.0007590034,"std":0.0030419173},
    "oDV":{"mean":-0.0006012572,"std":0.0071538037},
    "Whiff Avoid":{"mean":-0.00061714,"std":0.0075011551},
    "BBE Qual":{"mean":0.0002293162,"std":0.0028061836},
    "Contact":{"mean":-0.0002394206,"std":0.0091400752},
    "Gap Power":{"mean":-0.0027771776,"std":0.0203606356},
    "HR Power":{"mean":-0.0042889849,"std":0.0353546292},
    "Power":{"mean":-0.0070661628,"std":0.046277944},
    "Process":{"mean":-0.0018315846,"std":0.008036172},
    "Perf":{"mean":-0.0032695362,"std":0.0086914413},
    "Results":{"mean":-0.0034159869,"std":0.0089861099},
    "Pitch Runs":{"mean":5.0030889511,"std":0.0745003298}
}

for stat in header_colors.keys():
    header_colors.update({stat:[{"selector": "th", "props": 'background-color:'+header_colors[stat]+';'}]})

# if not team_wide:
#     agg_dict.update({'MLBAMID':'mean'})

if team_wide:
    season_df = (plv_df
                 .loc[(plv_df['game_played']>=start_date) &
                         (plv_df['game_played']<=end_date) &
                         plv_df['p_hand'].isin(hand_map[handedness])]
                 .rename(columns=season_names)
                 .rename(columns={'hitterteam':'Team',
                                  'PLV':'Pitch Runs',
                                  'pitch_id':'Pitches',
                                  'decision_value_z':'zDV',
                                  'decision_value_o':'oDV'})
                 .astype({'Team':'str'})
                 .groupby('Team')
                 [['Pitches','Pitch Runs','zDV','oDV']+list(season_names.values())]
                 .agg(agg_dict)
                 .query(f'Pitches >= {pitch_thresh}')
                 .sort_values('Process', ascending=False)
                )
elif stat_agg != 'Talent':
    season_df = (plv_df
                 .loc[(plv_df['game_played']>=start_date) &
                         (plv_df['game_played']<=end_date) &
                         plv_df['p_hand'].isin(hand_map[handedness])]
                 .rename(columns=season_names)
                 .rename(columns={'hitter_mlb_id':'MLBAMID',
                                  'hittername':'Name',
                                  'PLV':'Pitch Runs',
                                  'pitch_id':'Pitches',
                                  'decision_value_z':'zDV',
                                  'decision_value_o':'oDV'})
                 .astype({'Name':'str'})
                 .groupby(['Name','MLBAMID'])
                 [['Pitches','Pitch Runs','zDV','oDV']+list(season_names.values())]
                 .agg(agg_dict)
                 .query(f'Pitches >= {pitch_thresh}')
                 .sort_values('Process', ascending=False)
                )

metric_list = ['Whiff Avoid','BBE Qual','Contact',
               'Dec Value','zDV','oDV',
               'Gap Power','HR Power','Power',
               'Process']
if stat_agg != 'Talent':
    metric_list += ['Perf','Results']
if stat_agg=='Rate':
    for stat in ['SZ Judge']+metric_list:
        season_df[stat] = season_df[stat].sub(stat_constants[stat]['mean']).div(stat_constants[stat]['std']).mul(15).add(100)
        # season_df[stat] = z_score_scaler(season_df[stat])*15+100
        season_df[stat] = season_df[stat].fillna(100).astype('int')
    
    season_df['Pitch Runs'] = (stat_constants['Pitch Runs']['mean']-season_df['Pitch Runs'])/stat_constants['Pitch Runs']['std']*15+100
    season_df['Pitch Runs'] = season_df['Pitch Runs'].fillna(100).astype('int')

    st.write(f'Metrics on the "Plus" scale, where 100 is league average, a standard deviation is 15, and values above 100 indicate more expected runs. Table is sortable.')
    df_cols = ['Pitches','Pitch Runs','Dec Value','Whiff Avoid','BBE Qual','Contact','Gap Power','HR Power','Power','Process','Perf','Results','Swing Agg (%)','Contact% Added','Hittable Pitch%','SZ Judge','zDV','oDV']
    st.dataframe(season_df[df_cols]
             .style
             # .set_table_styles(header_colors,overwrite=True)
             .format(precision=1, thousands=',')
             .background_gradient(axis=None, 
                                  vmin=60, 
                                  vmax=140, 
                                  cmap="vlag",
                                  subset=['Pitch Runs','SZ Judge']+metric_list
                                 ), 
             height=(10 + 1) * 35 + 3, use_container_width=1,
            # column_config={"Name": st.column_config.Column(width="medium")}
            )

elif stat_agg=='Volume':
    for stat in list(agg_dict.keys())[5:]:
        season_df[stat] = season_df[stat].sub(stat_constants[stat]['mean'])
    season_df = season_df.rename(columns={
        'Swing Agg (%)':'Swings Added',
        'Contact% Added':'Contact Added',
        'Hittable Pitch%':'Hittable Pitches'
    }).sort_values('Process',ascending=False)
    color_max = season_df[['Process','Perf','Results']].abs().max().max()
    st.write(f'All metrics are presented as runs above average, except: Pitches, Swings Added, Contact Added, Hittable Pitches, and SZ Judge. Table is sortable.')
    df_cols = ['Pitches','Dec Value','Whiff Avoid','BBE Qual','Contact','Gap Power','HR Power','Power','Process','Perf','Results','Swings Added','Contact Added','Hittable Pitches','SZ Judge','zDV','oDV']

    st.dataframe(season_df[df_cols]
                 .style
                 # .set_table_styles(header_colors,overwrite=True)
                 .format(precision=1, thousands=',')
                 .background_gradient(axis=None, 
                                      vmin=-color_max, 
                                      vmax=color_max, 
                                      cmap="vlag",
                                      subset=metric_list
                                     ), 
                 height=(10 + 1) * 35 + 3, use_container_width=1,
                )
else:
    time_text = 'right now' if year==2026 else "at season's end"
    st.write(f"These values are an estimate of what each hitter's talent is, ***{time_text}***, for each metric. Each metric uses its own prior baseline and recency weighting, and considers all pitches faced since the start of 2020. Some components (like HR Power) are very responsive, while others (like zDV) are very resistant to change over time and/or change from league average.")
    df_cols = ['Dec Value','Contact','Power','Process','Swing Agg (%)','SZ Judge','zDV','oDV','Whiff Avoid','BBE Qual','Gap Power','HR Power']
    type_dict = {x:'int' for x in df_cols}
    type_dict.update({'Swing Agg (%)':'float'})
    st.dataframe(plv_df
                 .reset_index()
                 .rename(columns={'hitter_mlb_id':'MLBAMID',
                                  'hittername':'Name'})
                 .set_index(['Name','MLBAMID'])
                 [df_cols]
                 .round(1)
                 .astype(type_dict)
                 .style
                 # .set_table_styles(header_colors,overwrite=True)
                 .format(precision=1, thousands=',')
                 .background_gradient(axis=None, 
                                      vmin=55, 
                                      vmax=145, 
                                      cmap="vlag",
                                      subset=['SZ Judge']+metric_list
                                     ), 
                 height=(10 + 1) * 35 + 3, use_container_width=1,
                )

st.title("Metric Descriptions:")
st.write('- ***Pitch Runs***: The quality of the pitches a hitter has faced. A higher number means the pitches were expected to yield more runs (so they were "easier" pitches).')
st.write('- ***Swing Aggression*** (% above/below lg avg): How much more often a hitter swings at pitches, given the swing likelihoods of the pitches they face.')
st.write('''
- ***Strikezone Judgment***: The "correctness" of a hitter's swings and takes, using the likelihood of a pitch being a called strike (for swings) or a ball/HBP (for takes).
''')
st.write('- ***Contact% Added*** (% above/below lg avg): Rate of making contact, above or below expectations of the pitches faced.')
st.write("- ***Hittable Pitch%***: The modeled likelihood of the pitches a hitter faces becoming batted balls.")
st.write("- ***Decision Value*** (runs added per pitch): The modeled value of a hitter's decision to swing or take. These are also broken into 'Zone' and 'Out-of-Zone' components (credit to [Robert Orr](https://twitter.com/NotTheBobbyOrr)'s [SEAGER article](https://www.baseballprospectus.com/news/article/86572/the-crooked-inning-corey-seager-rangers/) and [@TJStats](https://twitter.com/TJStats) for the idea).")
st.write("- ***Whiff Avoid*** (runs added per swing): The modeled value of whiffing (or not), above the whiff expectation of each pitch.")
st.write("- ***BBE Qual*** (runs added per swing): The modeled value of hitting a given pitch into play, above the batted ball expectation ofeach pitch.")
st.write("- ***Contact*** (runs added per swing): The modeled value of the hitter making contact (or not), above the contact expectation of each pitch.")
st.write("- ***Gap Power*** (runs added per batted ball): The modeled non-HR hit value of each batted ball, above a pitch's non-HR hit expectation.")
st.write("- ***HR Power*** (runs added per batted ball): The modeled home run value of each batted ball, above a pitch's home run expectation.")
st.write("- ***Power*** (runs added per batted ball): The modeled value of each batted ball, above a pitch's expectation.")
st.write("- ***Process*** (runs added per pitch): The combined value of a hitter's Decision Value, Contact Ability, and Power.")
st.write("- ***Hitter Performance (runs added per pitch)***: Runs added by the hitter (including swing/take decisions), after accounting for pitch quality.")
st.write("- ***Results (runs per pitch)***: Context-neutral runs added by the hitter, without considering pitch quality.")
