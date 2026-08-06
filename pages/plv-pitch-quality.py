#PLV Aresenal Distribution
import streamlit as st
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import scipy as sp
import urllib
import os
import io


from PIL import Image
from collections import Counter
from scipy import stats
from io import StringIO
## Set Styling
# Plot Style
pl_white = '#FEFEFE'
pl_background = '#162B50'
pl_text = '#72a3f7'
pl_line_color = '#293a6b'

sns.set_theme(
    style={
        'axes.edgecolor': pl_background,
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

# Marker Style
marker_colors = {
    'FF':'#d22d49', 
    'SI':'#c57a02',
    'FS':'#00a1c5',  
    'FC':'#933f2c', 
    'SL':'#9300c7', 
    'CU':'#3c44cd',
    'CH':'#07b526', 
    'KN':'#999999',
    'SC':'#999999', 
    'UN':'#999999', 
}

cb_colors = {
    'FF':'#920000', 
    'SI':'#ffdf4d',
    'FS':'#006ddb',  
    'FC':'#ff6db6', 
    'SL':'#b66dff', 
    'CU':'#009999',
    'CH':'#22cf22', 
    'KN':'#999999',
    'SC':'#999999', 
    'UN':'#999999', 
}

diverging_palette = 'vlag'

# Pitch Names
pitch_names = {
    'FF':'Four-Seamer', 
    'SI':'Sinker',
    'FS':'Splitter',  
    'FC':'Cutter', 
    'SL':'Slider', 
    'CU':'Curveball',
    'CH':'Changeup', 
    'KN':'Knuckleball',
    'SC':'Screwball', 
    'UN':'Unknown', 
}

logo_loc = 'https://github.com/Blandalytics/PLV_viz/blob/main/data/PL-text-wht.png?raw=true'
logo = Image.open(urllib.request.urlopen(logo_loc))
st.image(logo, width=200)

# Year
years = [2026, 2025,2024,2023,2022,2021,2020]
year = st.selectbox('Choose a year:', years, index=0)

seasonal_constants = pd.read_csv('https://github.com/Blandalytics/streamlit_backup/blob/main/data/plv_seasonal_constants.csv?raw=true').set_index('year')

# Load Data
@st.cache_data
def load_data(year):
    df = pd.DataFrame()
    for month in range(3,11):
        file_name = f'https://github.com/Blandalytics/streamlit_backup/blob/main/data/{year}_PLV_App_Data-{month}.parquet?raw=true'
        df = pd.concat([df,
                        pd.read_parquet(file_name)[['pitchername','pitcher_mlb_id','pitch_id',
                                                    'p_hand','b_hand','pitchtype','PLV','velo',
                                                    'IHB','IVB','plv_runs_faced'
                                                   ]]
                       ])
    df = (df
          .sort_values('pitch_id')
          .astype({'pitch_id':'int',
                   'pitcher_mlb_id':'int'})
          .query(f'pitchtype not in {["KN","SC","UN"]}')
          .reset_index(drop=True)
         )
    
    df['pitchtype'] = df['pitchtype'].str.replace('SV','CU').str.replace('FO','FS')
    df['pitch_runs'] = df['plv_runs_faced']
    
    df['pitch_quality'] = 'Average'
    df.loc[df['PLV']>=5.5,'pitch_quality'] = 'Quality'
    df.loc[df['PLV']<4.5,'pitch_quality'] = 'Bad'

    for qual in df['pitch_quality'].unique():
      df[qual+' Pitch'] = 0
      df.loc[df['pitch_quality']==qual,qual+' Pitch'] = 1

    df['QP-BP'] = df['Quality Pitch'].sub(df['Bad Pitch'])
    
    return df
plv_df = load_data(year)
default_count = np.clip(round(plv_df.groupby('pitchername')['pitch_id'].count().quantile(0.4),-2),100,500)

def get_ids():
    id_df = pd.DataFrame()
    for chunk in list(range(0,10))+['a','b','c','d','e','f']:
        chunk_df = pd.read_csv(f'https://github.com/chadwickbureau/register/blob/master/data/people-{chunk}.csv?raw=true')
        id_df = pd.concat([id_df,chunk_df])
    return id_df[['key_mlbam','key_fangraphs']].dropna().astype('int') 

# pitch_threshold = 400

# Num Pitches threshold
pitch_threshold = st.number_input(f'Min # of Pitches:',
                                  min_value=0, 
                                  max_value=2000,
                                  step=50, 
                                  value=int(default_count))

def get_pla(year,pitch_threshold=pitch_threshold,p_hand=['L','R'],b_hand=['L','R']):
    pla_data = pd.read_csv('https://github.com/Blandalytics/streamlit_backup/blob/main/data/pla_data.csv?raw=true', encoding='latin1')
    season_df = (pla_data
             .loc[(pla_data['year_played']==year) &
                  pla_data['p_hand'].isin(p_hand) &
                  pla_data['b_hand'].isin(b_hand)]
             .assign(total_plv = lambda x: x['num_pitches'] * x['plv'])
      .groupby(['pitchername','pitchtype','pitcher_mlb_id'])
      [['num_pitches','pitch_runs','total_plv','subset_ip']]
      .agg({
          'num_pitches':'sum',
          'subset_ip':'sum',
          'pitch_runs':'sum',
          'total_plv':'sum'
      })
      .sort_values('pitch_runs', ascending=False)
      .query(f'num_pitches >={int(pitch_threshold/20)}') # 5% of total pitches threshold
      .reset_index()
      )

    # Clean IP to actual fractions
    season_df['season_IP'] = season_df['subset_ip'].groupby(season_df['pitcher_mlb_id']).transform('sum')
    season_df['season_pitches'] = season_df['num_pitches'].groupby(season_df['pitcher_mlb_id']).transform('sum')

    # Calculate PLV, in general, and per-pitchtype
    season_df['PLV'] = season_df['total_plv'].groupby(season_df['pitcher_mlb_id']).transform('sum').div(season_df['season_pitches']).astype('float')
    season_df['pitchtype_plv'] = season_df['total_plv'].div(season_df['num_pitches'])

    # Calculate PLA, in general, and per-pitchtype
    season_df['PLA'] = season_df['pitch_runs'].groupby(season_df['pitcher_mlb_id']).transform('sum').mul(9).div(season_df['season_IP']).astype('float')
    season_df['pitchtype_pla'] = season_df['pitch_runs'].mul(9).div(season_df['subset_ip']) # ERA Scale

    season_df = season_df.sort_values('PLA')

    # Pivot a dataframe of per-pitchtype PLAs
    pitchtype_df = season_df.pivot_table(index=['pitcher_mlb_id'], 
                                          columns='pitchtype', 
                                          values='pitchtype_pla',
                                          aggfunc='sum'
                                        ).replace({0:None})

    # Merge season-long PLA with pitchtype PLAs
    df = (season_df
          .drop_duplicates('pitcher_mlb_id')
          [['pitcher_mlb_id','pitchername','season_pitches','PLA','PLV']]
          .merge(pitchtype_df, how='inner',left_on='pitcher_mlb_id',right_index=True)
          .query(f'season_pitches >= {pitch_threshold}')
          .rename(columns={'pitchername':'Pitcher',
                           'season_pitches':'Num_Pitches'})
          .drop(columns=['pitcher_mlb_id'])
          .fillna(np.nan)
          .set_index('Pitcher')
          [['Num_Pitches','PLV','PLA','FF','SI','SL','CH','CU','FC','FS']]
          .copy()
          )
    return df

# Season data
pla_df = get_pla(year,pitch_threshold)

mean_plv = pla_df['PLV'].mul(pla_df['Num_Pitches']).sum() / pla_df['Num_Pitches'].sum()

format_cols = ['PLA','FF','SI','SL','CH','CU','FC','FS']

fill_val = pla_df[format_cols].max().max()+0.01

def pitchtype_color(s):
    return f"background-color: {marker_colors[s]}" if s in list(marker_colors.keys()) else None

class_df = (plv_df
             .rename(columns={
                 'pitcher_mlb_id':'MLBAMID',
                 'pitchername':'Pitcher'
             })
             .groupby(['Pitcher','MLBAMID'])
             [['Quality Pitch','Average Pitch','Bad Pitch','pitch_id']]
             .agg({
                 'Quality Pitch':'mean',
                 'Average Pitch':'mean',
                 'Bad Pitch':'mean',
                 'pitch_id':'count'
             })
             .query(f'pitch_id >={pitch_threshold}')
             .assign(QP_BP=lambda x: x['Quality Pitch'] - x['Bad Pitch'])
             .rename(columns={
                 'Quality Pitch':'QP%',
                 'Average Pitch':'AP%',
                 'Bad Pitch':'BP%',
                 'QP_BP':'QP-BP%',
                 'pitch_id':'# Pitches'
             })
             [['# Pitches','QP%','AP%','BP%','QP-BP%']]
             .mul([1,100,100,100,100])
             .sort_values('QP-BP%', ascending=False)
            .reset_index()
            .astype({'MLBAMID':'str'})
            .set_index('Pitcher')
            .copy()
           )

st.dataframe(class_df
             .style
             .format(precision=1, thousands=',')
             .background_gradient(axis=0, cmap=f"{diverging_palette}", subset=['QP%','QP-BP%'])
             .background_gradient(axis=0, cmap=f"{diverging_palette}_r", subset=['BP%'])
            , height=600, use_container_width=1)

st.title("Metric Descriptions:")
st.write('- ***Quality Pitch (QP%)***: Pitch with a PLV >= 5.5')
st.write('- ***Average Pitch (AP%)***: Pitch with 4.5 < PLV < 5.5')
st.write('- ***Bad Pitch (BP%)***: Pitch with a PLV <= 4.5')
st.write('- ***QP-BP%***: Difference between QP and BP. Avg is 7%')
