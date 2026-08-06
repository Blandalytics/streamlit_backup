#Pitch Analysis Cards
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

kde_min = '#236abe'
kde_max = '#a9373b'

kde_palette = (sns.color_palette(f'blend:{kde_min},{pl_white}', n_colors=1001)[:-1] +
               sns.color_palette(f'blend:{pl_white},{kde_max}', n_colors=1001)[:-1])

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
    'ST':'#C95EBE',
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
    'ST':'#C95EBE',
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
    'ST':'Sweeper',
    'CU':'Curveball',
    'CH':'Changeup', 
    'KN':'Knuckleball',
    'SC':'Screwball', 
    'UN':'Unknown', 
}

sz_bot = 1.5
sz_top = 3.5
x_ft = 2.5
y_bot = -0.5
y_lim = 6
plate_y = -.25

logo_loc = 'https://github.com/Blandalytics/PLV_viz/blob/main/data/PL-text-wht.png?raw=true'
logo = Image.open(urllib.request.urlopen(logo_loc))
st.image(logo, width=200)

# Year
years = [2026, 2025, 2024,2023,2022,2021,2020]
year = st.selectbox('Choose a year:', years, index=0)
# Load Data
@st.cache_data(ttl=60*15,show_spinner=f"Loading {year} data")
def load_data(year):
    df = pd.DataFrame()
    for chunk in [1,2,3]:
        file_name = f'https://github.com/Blandalytics/PLV_viz/blob/main/data/{year}_Pitch_Analysis_Data-{chunk}.parquet?raw=true'
        load_cols = ['pitchername','pitchtype','pitch_id',
                     'p_hand','b_hand','IHB','IVB','called_strike_pred',
                     'ball_pred','PLV','velo','pitch_extension',
                     'adj_vaa','p_x','p_z','PLV_loc_plus']
        # if year == 2023:
        #     load_cols += ['b_hand']
        df = pd.concat([df,
                        pd.read_parquet(file_name)[load_cols]
                       ])

    df = (df
          .sort_values('pitch_id')
          .astype({'pitch_id':'int'})
          .query(f'pitchtype not in {["KN","SC","UN"]}')
          .reset_index(drop=True)
         )
    df['pitchtype'] = df['pitchtype'].str.replace('SV','CU').str.replace('FO','FS')
    date_file = f'https://github.com/Blandalytics/streamlit_backup/blob/main/data/date_pitch_map.parquet?raw=true'
    df['game_played'] = df['pitch_id'].map(pd.read_parquet(date_file).set_index('pitch_id').to_dict()['game_played'])
    df['game_played'] = pd.to_datetime(df['game_played']).dt.date
  
    return df

base_df = load_data(year)
pitch_thresh = 5

# Has at least 1 pitch with at least 50 thrown
pitcher_list = list(base_df.groupby(['pitchername','pitchtype'])['pitch_id'].count().reset_index().query(f'pitch_id >={pitch_thresh}')['pitchername'].sort_values().unique())

col1, col2, col3 = st.columns([0.4,0.35,0.25])

with col1:
    # Player
    default_ix = pitcher_list.index('Dylan Cease')
    card_player = st.selectbox('Choose a player:', pitcher_list, index=default_ix)

with col2:
    # Pitch
    pitches = (base_df
     .loc[base_df['pitchername']==card_player,'pitchtype']
     .map(pitch_names)
     .value_counts(normalize=True)
     .where(lambda x : x>0.005)
     .dropna()
     .to_dict()
    )
    
    select_list = []
    for pitch in pitches.keys():
        select_list += [f'{pitch} ({pitches[pitch]:.1%})'] if (card_player != 'Kutter Crawford') | (pitch != 'Cutter') else [f'Kutter ({pitches[pitch]:.1%})']
    pitch_type = st.selectbox('Choose a pitch (season usage):', select_list)
    pitch_type = pitch_type.split('(')[0][:-1]
    pitch_type = pitch_type if pitch_type != 'Kutter' else 'Cutter'
  
with col3:
    # Chart Type
    # charts = ['Bar','Violin']
    # chart_type = st.selectbox('Chart style:', charts)
    chart_type = 'Bar'

season_start = base_df.loc[base_df['pitchername']==card_player,'game_played'].min()
season_end = base_df.loc[base_df['pitchername']==card_player,'game_played'].max()

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(f"Start Date (First game: {season_start:%b %d})", 
                               season_start,
                               min_value=season_start,
                               max_value=season_end,
                               format="MM/DD/YYYY")
with col2:
    end_date = st.date_input(f"End Date (Last game: {season_end:%b %d})", 
                             season_end,
                             min_value=season_start,
                             max_value=season_end,
                             format="MM/DD/YYYY")

pitch_type = {v: k for k, v in pitch_names.items()}[pitch_type]

pitch_df = base_df.loc[(base_df['game_played']>=start_date) &
                        (base_df['game_played']<=end_date)].copy()


plus_palette = 'vlag'
plus_norm = mpl.colors.CenteredNorm(100,75)

data_date = pitch_df['game_played'].max()
filename = f'{year}/{card_player}-{chart_type}-{pitch_type}-{start_date}-{end_date}.png'.replace(' ','-').lower()
def pitch_analysis_card(card_player,pitch_type,chart_type,filename):
    pitches_thrown = int(pitch_df.loc[(pitch_df['pitchername']==card_player) & (pitch_df['pitchtype']==pitch_type)].shape[0]/100)*100
    n_pitchers = min(75,
                     len(pitch_df.loc[(pitch_df['pitchtype']==pitch_type),'pitchername'].unique())
                    )
    league_thresh = int(pitch_df.loc[(pitch_df['pitchtype']==pitch_type)].groupby('pitchername')['pitch_id'].count().nlargest(n_pitchers).min()/50)*50
    pitch_num_thresh = max(pitch_thresh,
                           min(pitches_thrown,
                               league_thresh
                              )
                          )

    pitch_stats_df = (
        pitch_df
        .assign(IHB = lambda x: np.where(x['p_hand']=='R',x['IHB']*-1,x['IHB']))
        .loc[(pitch_df['pitchtype']==pitch_type)]
        .groupby(['pitchername'])
        [['pitch_id','p_hand','PLV','velo','pitch_extension','IVB','IHB','adj_vaa','PLV_loc_plus']]
        .agg({
            'pitch_id':'count',
            'p_hand':pd.Series.mode,
            'PLV':'mean',
            'velo':'mean',
            'pitch_extension':'mean',
            'IVB':'mean',
            'IHB':'mean',
            'adj_vaa':'mean',
            'PLV_loc_plus':'mean'
        })
         .query(f'pitch_id>={pitch_num_thresh}')
        .reset_index()
        .sort_values('PLV_loc_plus', ascending=False)
    )

    def min_max_scaler(x):
        return ((x-x.min())/(x.max()-x.min()))

    for col in ['PLV','velo','pitch_extension','IVB','IHB','adj_vaa','PLV_loc_plus']:
        pitch_stats_df[col+'_scale'] = min_max_scaler(pitch_stats_df[col])
        pitch_stats_df[col+'_pct'] = pitch_stats_df[col].rank(pct=True)

    chart_stats = ['velo','pitch_extension','IVB','IHB','adj_vaa','PLV_loc_plus','PLV']
    fig = plt.figure(figsize=(10,10))

    stat_name_dict = {
        'velo':'Velocity',
        'pitch_extension':'Release\nExtension',
        'IVB':'Induced\nVertical\nBreak',
        'IHB':'Arm-Side\nBreak',
        'adj_vaa':'Adj. Vert.\nApproach\nAngle',
        'PLV_loc_plus':'plvLoc+',
        'PLV':'PLV',
    }

    stat_tops = {
        'velo':'Faster',
        'pitch_extension':'Longer',
        'IVB':'Rise',
        'IHB':'Arm',
        'adj_vaa':'Flatter',
        'PLV_loc_plus':'Good',
        'PLV':'Good',
    }
    stat_bottoms = {
        'velo':'Slower',
        'pitch_extension':'Shorter',
        'IVB':'Drop',
        'IHB':'Glove',
        'adj_vaa':'Steeper',
        'PLV_loc_plus':'Bad',
        'PLV':'Bad',
    }

    # Divide card into tiles
    grid = plt.GridSpec(2, len(chart_stats),height_ratios=[5,5],hspace=0.2)

    hand = pitch_df.loc[(pitch_df['pitchername']==card_player),'p_hand'].values[0]
    ax1 = plt.subplot(grid[0, 2:5])
    circle1 = plt.Circle((0, 0), 6, color=pl_white,fill=False,alpha=0.2,linestyle='--')
    ax1.add_patch(circle1)
    circle2 = plt.Circle((0, 0), 12, color=pl_white,fill=False,alpha=0.5)
    ax1.add_patch(circle2)
    circle3 = plt.Circle((0, 0), 18, color=pl_white,fill=False,alpha=0.2,linestyle='--')
    ax1.add_patch(circle3)
    circle4 = plt.Circle((0, 0), 24, color=pl_white,fill=False,alpha=0.5)
    ax1.add_patch(circle4)
    ax1.axvline(0,ymin=4/58,ymax=54/58,color=pl_white,alpha=0.5,zorder=1)
    ax1.axhline(0,xmin=4/58,xmax=54/58,color=pl_white,alpha=0.5,zorder=1)
    
    for dist in [12,24]:
        label_dist = dist-0.25
        ax1.text(label_dist,-0.3,f'{dist}"',ha='right',va='top',fontsize=6,color=pl_white,alpha=0.5,zorder=1)
        ax1.text(-label_dist,-0.3,f'{dist}"',ha='left',va='top',fontsize=6,color=pl_white,alpha=0.5,zorder=1)
        ax1.text(0.25,label_dist-0.25,f'{dist}"',ha='left',va='top',fontsize=6,color=pl_white,alpha=0.5,zorder=1)
        ax1.text(0.25,-label_dist,f'{dist}"',ha='left',va='bottom',fontsize=6,color=pl_white,alpha=0.5,zorder=1)
    
    if hand=='R':
        ax1.text(28.5,0,'Arm\nSide',ha='center',va='center',fontsize=8,color=pl_white,alpha=0.75,zorder=1)
        ax1.text(-28.5,0,'Glove\nSide',ha='center',va='center',fontsize=8,color=pl_white,alpha=0.75,zorder=1)
    else:
        ax1.text(28.5,0,'Glove\nSide',ha='center',va='center',fontsize=8,color=pl_white,alpha=0.75,zorder=1)
        ax1.text(-28.5,0,'Arm\nSide',ha='center',va='center',fontsize=8,color=pl_white,alpha=0.75,zorder=1)
    
    ax1.text(0,27,'Rise',ha='center',va='center',fontsize=8,color=pl_white,alpha=0.75,zorder=1)
    ax1.text(0,-27,'Drop',ha='center',va='center',fontsize=8,color=pl_white,alpha=0.75,zorder=1)
    
    sns.scatterplot((pitch_df
                     .loc[(pitch_df['pitchername']==card_player) &
                           (pitch_df['pitchtype']==pitch_type)]
                     .assign(IHB = lambda x: x['IHB'].mul(-1))
                    ),
                    x='IHB',
                    y='IVB',
                   color=marker_colors[pitch_type],
                   # palette=marker_colors,
                    edgecolor=pl_white,
                    s=85,
                    linewidth=0.3,
                    alpha=1,
                    zorder=10,
                   ax=ax1,
                   legend=False)    
    
    ax1.set(xlim=(-29,29),
           ylim=(-29,29),
           aspect=1)
    ax1.set_title('Movement',fontsize=18)
    ax1.axis('off')
    sns.despine(left=True,bottom=True)

    sz_bot = 1.5
    sz_top = 3.5
    x_ft = 2.5
    y_bot = -0.5
    y_lim = 6.5
    plate_y = -.25
    alpha_val = 1
    title_y = 0.95
    
    ax2 = plt.subplot(grid[0, :2])
    sns.scatterplot(data=(pitch_df
                          .loc[(pitch_df['pitchername']==card_player) &
                               (pitch_df['pitchtype']==pitch_type) &
                                (pitch_df['b_hand']=='L')].assign(p_x = lambda x: x['p_x']*-1,
                                                                  sort_val = lambda x: x['PLV_loc_plus'].sub(100).abs())
                          .sort_values('sort_val')),
                    x='p_x',
                    y='p_z',
                    color=marker_colors[pitch_type],
                    # hue='PLV_loc_plus',
                    # palette=plus_palette,
                    edgecolor=pl_white,
                    s=85,
                    linewidth=0.3,
                    alpha=1,
                    legend=False,
                   zorder=0,
                   ax=ax2)

    # Inner Strike zone
    ax2.plot([-8/12,8/12], [1.5+2/3,1.5+2/3], color=pl_background, linewidth=2.5, alpha=alpha_val)
    ax2.plot([-8/12,8/12], [1.5+4/3,1.5+4/3], color=pl_background, linewidth=2.5, alpha=alpha_val)
    ax2.axvline(10/36, ymin=(sz_bot-y_bot+0.05)/(y_lim-1-y_bot), ymax=(sz_top-y_bot-0.05)/(y_lim-1-y_bot), color=pl_background, linewidth=2.5, alpha=alpha_val)
    ax2.axvline(-10/36, ymin=(sz_bot-y_bot+0.05)/(y_lim-1-y_bot), ymax=(sz_top-y_bot-0.05)/(y_lim-1-y_bot), color=pl_background, linewidth=2.5, alpha=alpha_val)
    ax2.plot([-8.25/12,8.25/12], [1.5+2/3,1.5+2/3], color=pl_white, linewidth=1, alpha=alpha_val)
    ax2.plot([-8.25/12,8.25/12], [1.5+4/3,1.5+4/3], color=pl_white, linewidth=1, alpha=alpha_val)
    ax2.axvline(10/36, ymin=(sz_bot-y_bot+0.025)/(y_lim-1-y_bot), ymax=(sz_top-y_bot-0.025)/(y_lim-1-y_bot), color=pl_white, linewidth=1, alpha=alpha_val)
    ax2.axvline(-10/36, ymin=(sz_bot-y_bot+0.025)/(y_lim-1-y_bot), ymax=(sz_top-y_bot-0.025)/(y_lim-1-y_bot), color=pl_white, linewidth=1, alpha=alpha_val)
    
    # Outer Strike Zone
    zone_outline_shadow = plt.Rectangle((-8.5/12, sz_bot), 17/12, 2, 
                                 color=pl_background,fill=False,alpha=alpha_val, linewidth=3)
    ax2.add_patch(zone_outline_shadow)
    zone_outline = plt.Rectangle((-8.5/12, sz_bot), 17/12, 2, color=pl_white,fill=False,alpha=alpha_val)
    ax2.add_patch(zone_outline)
    
    # Plate
    ax2.plot([-8.5/12,8.5/12], [plate_y,plate_y], color=pl_white, linewidth=1, alpha=alpha_val)
    ax2.plot([-8.5/12,-8.25/12], [plate_y,plate_y+0.15], color=pl_white, linewidth=1, alpha=alpha_val)
    ax2.plot([8.5/12,8.25/12], [plate_y,plate_y+0.15], color=pl_white, linewidth=1, alpha=alpha_val)
    ax2.plot([8.28/12,0], [plate_y+0.15,plate_y+0.25], color=pl_white, linewidth=1, alpha=alpha_val)
    ax2.plot([-8.28/12,0], [plate_y+0.15,plate_y+0.25], color=pl_white, linewidth=1, alpha=alpha_val)
    
    ax2.set(xlim=(-2,2),
           ylim=(y_bot,y_lim-1),
           aspect=1,
           title='Locations\nvs LHH')
    ax2.set_title('Locations\nvs LHH',fontsize=18,y=title_y)
    ax2.axis('off')
    
    ax3 = plt.subplot(grid[0,5:])
    # Inner Strike zone
    ax3.plot([-8/12,8/12], [1.5+2/3,1.5+2/3], color=pl_background, linewidth=2.5, alpha=alpha_val)
    ax3.plot([-8/12,8/12], [1.5+4/3,1.5+4/3], color=pl_background, linewidth=2.5, alpha=alpha_val)
    ax3.axvline(10/36, ymin=(sz_bot-y_bot+0.05)/(y_lim-1-y_bot), ymax=(sz_top-y_bot-0.05)/(y_lim-1-y_bot), color=pl_background, linewidth=2.5, alpha=alpha_val)
    ax3.axvline(-10/36, ymin=(sz_bot-y_bot+0.05)/(y_lim-1-y_bot), ymax=(sz_top-y_bot-0.05)/(y_lim-1-y_bot), color=pl_background, linewidth=2.5, alpha=alpha_val)
    ax3.plot([-8.25/12,8.25/12], [1.5+2/3,1.5+2/3], color=pl_white, linewidth=1, alpha=alpha_val)
    ax3.plot([-8.25/12,8.25/12], [1.5+4/3,1.5+4/3], color=pl_white, linewidth=1, alpha=alpha_val)
    ax3.axvline(10/36, ymin=(sz_bot-y_bot+0.025)/(y_lim-1-y_bot), ymax=(sz_top-y_bot-0.025)/(y_lim-1-y_bot), color=pl_white, linewidth=1, alpha=alpha_val)
    ax3.axvline(-10/36, ymin=(sz_bot-y_bot+0.025)/(y_lim-1-y_bot), ymax=(sz_top-y_bot-0.025)/(y_lim-1-y_bot), color=pl_white, linewidth=1, alpha=alpha_val)
    
    # Outer Strike Zone
    zone_outline_shadow = plt.Rectangle((-8.5/12, sz_bot), 17/12, 2, 
                                 color=pl_background,fill=False,alpha=alpha_val, linewidth=3)
    ax3.add_patch(zone_outline_shadow)
    zone_outline = plt.Rectangle((-8.5/12, sz_bot), 17/12, 2, color=pl_white,fill=False,alpha=alpha_val)
    ax3.add_patch(zone_outline)
    
    # Plate
    ax3.plot([-8.5/12,8.5/12], [plate_y,plate_y], color=pl_white, linewidth=1, alpha=alpha_val)
    ax3.plot([-8.5/12,-8.25/12], [plate_y,plate_y+0.15], color=pl_white, linewidth=1, alpha=alpha_val)
    ax3.plot([8.5/12,8.25/12], [plate_y,plate_y+0.15], color=pl_white, linewidth=1, alpha=alpha_val)
    ax3.plot([8.28/12,0], [plate_y+0.15,plate_y+0.25], color=pl_white, linewidth=1, alpha=alpha_val)
    ax3.plot([-8.28/12,0], [plate_y+0.15,plate_y+0.25], color=pl_white, linewidth=1, alpha=alpha_val)
    
    sns.scatterplot(data=(pitch_df
                          .loc[(pitch_df['pitchername']==card_player) &
                               (pitch_df['pitchtype']==pitch_type) &
                                (pitch_df['b_hand']=='R')].assign(p_x = lambda x: x['p_x']*-1,
                                                                  sort_val = lambda x: x['PLV_loc_plus'].sub(100).abs())
                          .sort_values('sort_val')),
                    x='p_x',
                    y='p_z',
                    color=marker_colors[pitch_type],
                    # hue='PLV_loc_plus',
                    # palette=plus_palette,
                    edgecolor=pl_white,
                    s=85,
                    linewidth=0.3,
                    alpha=1,
                    legend=False,
                   zorder=0,
                   ax=ax3)
    
    ax3.set(xlim=(-2,2),
           ylim=(y_bot,y_lim-1),
           aspect=1)
    ax3.set_title('Locations\nvs RHH',fontsize=18,y=title_y)
    ax3.axis('off')
    
    sns.despine(left=True,bottom=True)
  
    adjusted_pitch_name = pitch_names[pitch_type] if (card_player != 'Kutter Crawford') | (pitch_names[pitch_type] != 'Cutter') else 'Kutter'
    fig.text(0.5125,0.45,'Pitch Characteristics',ha='center',fontsize=18)
    fig.text(0.5125,0.425,f'(Compared to MLB {adjusted_pitch_name}s; Min {pitch_num_thresh} Thrown; - - - is MLB Median)',ha='center',fontsize=12)
    for stat in chart_stats:
        if chart_type=='Violin':
            val = pitch_stats_df.loc[(pitch_stats_df['pitchername']==card_player),
                                     stat].item()
            up_thresh = max(pitch_stats_df[stat].quantile(0.99),
                            val)
            low_thresh = min(pitch_stats_df[stat].quantile(0.01),
                             val)
            ax = plt.subplot(grid[1, chart_stats.index(stat)])
            sns.violinplot(data=pitch_stats_df.loc[(pitch_stats_df[stat] <= up_thresh) &
                                                   (pitch_stats_df[stat] >= low_thresh)],
                           y=stat+'_scale',
                           inner=None,
                           orient='v',
                           cut=0,
                           color=marker_colors[pitch_type],
                           linewidth=1
                         )
            ax.collections[0].set_edgecolor('w')
    
            top = ax.get_ylim()[1]
            bot = ax.get_ylim()[0]
            plot_height = top - bot
    
            format_dict = {
                'PLV':f'{val:.2f}',
                'velo':f'{val:.1f}mph',
                'pitch_extension':f'{val:.1f}ft',
                'IVB':f'{val:.1f}"',
                'IHB':f'{val:.1f}"',
                'adj_vaa':f'{val:.1f}°',
                'PLV_loc_plus':f'{val:.0f}'
            }
            ax.axhline(pitch_stats_df[stat+'_scale'].median(),
                       linestyle='--',
                       color='w')
            ax.axhline(top + (0.25 * plot_height),
                       xmin=0.1,
                       xmax=0.9,
                       color='w')
            ax.text(0,
                    pitch_stats_df.loc[(pitch_stats_df['pitchername']==card_player),
                                       stat+'_scale'],
                    format_dict[stat],
                    va='center',
                    ha='center',
                    fontsize=12 if stat=='velo' else 14,
                    bbox=dict(facecolor=pl_background, alpha=0.75, edgecolor='w'))
            ax.text(0,
                    top + (0.5 * plot_height),
                    stat_name_dict[stat],
                    va='center',
                    ha='center',
                    fontsize=14)
            ax.text(0,
                    top + (0.2 * plot_height),
                    stat_tops[stat],
                    va='top',
                    ha='center',
                    fontsize=12)
            ax.text(0,
                    bot - (0.2 * plot_height),
                    stat_bottoms[stat],
                    va='bottom',
                    ha='center',
                    fontsize=12)
            ax.tick_params(left=False, bottom=False)
            ax.set_yticklabels([])
            ax.set(xlabel=None,ylabel=None,ylim=(bot - (0.15 * plot_height),
                                                 top + plot_height))
            ax.xaxis.set_label_position('top')
        else:
            plot_val = pitch_stats_df.loc[(pitch_stats_df['pitchername']==card_player),stat+'_pct'].item()
            text_val = pitch_stats_df.loc[(pitch_stats_df['pitchername']==card_player),stat].item()

            format_dict = {
                'PLV':f'{text_val:.2f}',
                'velo':f'{text_val:.1f}mph',
                'pitch_extension':f'{text_val:.1f}ft',
                'IVB':f'{text_val:.1f}"',
                'IHB':f'{text_val:.1f}"',
                'adj_vaa':f'{text_val:.1f}°',
                'PLV_loc_plus':f'{text_val:.0f}'
            }
            
            ax = plt.subplot(grid[1, chart_stats.index(stat)])
            ax.axhline(1.15,
                       xmin=0.1,
                       xmax=0.9,
                       color='w')
            ax.bar(1, 1, color='w',alpha=0.1)
            ax.bar(1, plot_val, color=marker_colors[pitch_type])
            ax.axhline(0.5,
                       linestyle='--',
                       color='w')
            ax.text(1, plot_val+0.01,
                    format_dict[stat],
                    va='bottom',
                    ha='center',
                    fontsize=12 if stat=='velo' else 14,
                    bbox=dict(facecolor='#2d4061', alpha=0.75 if plot_val<0.5 else 0, linewidth=0, pad=1))
            ax.text(1,
                    1.4,
                    stat_name_dict[stat],
                    va='center',
                    ha='center',
                    fontsize=14)
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.set(ylim=(0,1.9))
            ax.tick_params(left=False, bottom=False)

    # Add PL logo
    # pl_ax = fig.add_axes([0.41,0.025,0.2,0.2], anchor='S', zorder=1)
    pl_ax = fig.add_axes([0.41,0.475,0.2,0.2], anchor='S', zorder=1)
    pl_ax.imshow(logo)
    pl_ax.axis('off')

    apostrophe_text = "'" if card_player[-1]=='s' else "'s"
    
    fig.suptitle(f"{card_player}{apostrophe_text} {year} {adjusted_pitch_name}",y=0.97,fontsize=20)
    date_text = '' if (start_date==season_start) & (end_date==season_end) else f'{start_date:%b %-d} - {end_date:%b %-d}; '
    fig.text(0.5,0.925,f"({date_text}From Pitcher's Perspective; as of {data_date.strftime('%-m-%-d-%Y')})",ha='center',fontsize=12)
    # fig.text(0.77,0.07,"@Blandalytics",ha='center',fontsize=10)
    # fig.text(0.77,0.05,"pitch-analysis-card.streamlit.app",ha='center',fontsize=10)
    sns.despine(left=True,bottom=True)
    #plot the fig
    st.pyplot(fig)
# Use image saved on the server if it exists
# if (key_exists(client, AWS_S3_BUCKET, filename) == 'true')  & (card_player != 'Zack Wheeler'):
#     st.markdown(f"![image](https://s3.amazonaws.com/{AWS_S3_BUCKET}/{filename}#full)")
# else:

def kde_calcs(df,pitcher,pitchtype,year=year):
    p_hand = df.loc[(df['pitchername']==pitcher),'p_hand'].iloc[0]
    kde_diffs = []
    for b_hand in ['L','R']:
        kde_df = (df
                  .loc[(df['pitchtype']==pitchtype) &
                       (df['b_hand']==b_hand) &
                       (df['p_hand']==p_hand)
                      ]
                  .assign(kde_x = lambda x: np.clip(x['p_x'].astype('float').mul(12).round(0).astype('int').div(12),-20/12,20/12),
                          kde_z = lambda x: np.clip(x['p_z'].astype('float').mul(12).round(0).astype('int').div(12),0,4.5))
                  .reset_index(drop=True)
                 )
        if kde_df.loc[kde_df['pitchername']==pitcher].shape[0] < 10:
            kde_diffs += [pd.DataFrame()]
            continue
        x_loc_league = kde_df['kde_x']
        y_loc_league = kde_df['kde_z']

        x_loc_pitcher = kde_df.loc[(kde_df['pitchername']==pitcher) &
                                    (kde_df['game_played']>=start_date) &
                                    (kde_df['game_played']<=end_date),'kde_x']
        y_loc_pitcher = kde_df.loc[(kde_df['pitchername']==pitcher) &
                                    (kde_df['game_played']>=start_date) &
                                    (kde_df['game_played']<=end_date),'kde_z']

        xmin = x_loc_league.min()
        xmax = x_loc_league.max()
        ymin = y_loc_league.min()
        ymax = y_loc_league.max()

        X, Y = np.mgrid[xmin:xmax:41j, ymin:ymax:55j]
        positions = np.vstack([X.ravel(), Y.ravel()])

        # league matrix
        values_league = np.vstack([x_loc_league, y_loc_league])
        kernel_league = sp.stats.gaussian_kde(values_league)
        f_league = np.reshape(kernel_league(positions).T, X.shape)

        # pitcher matrix
        values_pitcher = np.vstack([x_loc_pitcher, y_loc_pitcher])
        kernel_pitcher = sp.stats.gaussian_kde(values_pitcher)
        f_pitcher = np.reshape(kernel_pitcher(positions).T, X.shape)
        
        kde_diffs += [pd.DataFrame(f_pitcher-f_league).T]
    return kde_diffs
filename_2 = f'{year}/{card_player}-{chart_type}-{pitch_type}-{start_date}-{end_date}-kde.png'.replace(' ','-').lower()
p_hand = pitch_df.loc[(pitch_df['pitchername']==card_player),'p_hand'].iloc[0]
def kde_chart(kde_data,p_hand=p_hand,kde_thresh=0.1):
    fig = plt.figure(figsize=(11,7))
    grid = plt.GridSpec(2, 3,height_ratios=[50,1],width_ratios=[5,1,5],hspace=0,wspace=0.05)
    for hand in ['L','R']:
        hand_index = 0 if hand=='L' else 1
        ax = plt.subplot(grid[0, 0]) if hand=='L' else plt.subplot(grid[0, 2])
        ax.set(xlabel=None, ylabel=None)
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.tick_params(left=False, bottom=False)
        if kde_diffs[hand_index].empty:
            ax.text(0.5,0.5,f'None thrown\nto {hand}HH',va='center',ha='center',fontsize=18)
            continue
        sns.heatmap(kde_diffs[hand_index],
                    cmap=kde_palette,
                    center=0,
                    vmin=-kde_thresh,
                    vmax=kde_thresh,
                    cbar=False,
                    ax=ax
                   )

        # Strikezone
        ax.axhline(18, xmin=1/4, xmax=3/4, color='black', linewidth=2)
        ax.axhline(42, xmin=1/4, xmax=3/4, color='black', linewidth=2)
        ax.axvline(10, ymin=1/3, ymax=7/9, color='black', linewidth=2)
        ax.axvline(30, ymin=1/3, ymax=7/9, color='black', linewidth=2)
    
        # Inner Strikezone
        ax.axhline(26, xmin=1/4, xmax=3/4, color='black', linewidth=1)
        ax.axhline(34, xmin=1/4, xmax=3/4, color='black', linewidth=1)
        ax.axvline(10+20/3, ymin=1/3, ymax=7/9, color='black', linewidth=1)
        ax.axvline(30-20/3, ymin=1/3, ymax=7/9, color='black', linewidth=1)
    
        # Plate
        ax.plot([11.52,27.48], [1,1], color='k', linewidth=1)
        ax.plot([11.5,11.75], [1,2], color='k', linewidth=1)
        ax.plot([27.5,27.25], [1,2], color='k', linewidth=1)
        ax.plot([27.3,20], [2,3], color='k', linewidth=1)
        ax.plot([11.7,20], [2,3], color='k', linewidth=1)
        
        ax.text(37.5 if hand=='L' else 2.5,
                30,
                'Hitter Stands Here',
                rotation=270 if hand=='L' else 90,
                fontsize=16,
                color='k',
                ha='center',
                va='center',
                bbox=dict(boxstyle='round',
                          color='w',
                          alpha=0.5,
                          pad=0.2)
               )
    
        ax.set(xlim=(40,0),
               ylim=(0,54),
               aspect=1)
    
        ax.text(20,55,f"{p_hand}HP vs {hand}HH",ha='center',fontsize=16)
        ax.axis('off')
    ax = plt.subplot(grid[0, 1])
    norm = mpl.colors.Normalize(vmin=-kde_thresh, vmax=kde_thresh)
    cb1 = mpl.colorbar.ColorbarBase(ax, 
                                    cmap=mpl.colors.ListedColormap(kde_palette),
                                    norm=norm,
                                    values=[x/100 for x in range(-int(kde_thresh*100),int(kde_thresh*100)+1)],
                                   )
    
    cb1.outline.set_visible(False)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.tick_params(right=False, bottom=False)
    ax.set(ylim=(-kde_thresh*1.5,kde_thresh*1.5))
    ax.text(0.5,kde_thresh,f'+{int(kde_thresh*100)}%\n',ha='center',va='bottom',color=kde_palette[-150],fontweight='bold')
    ax.text(0.5,kde_thresh*1.25,'More\nOften',ha='center',va='bottom',color=kde_palette[-150],fontweight='bold')
    ax.text(0.5,-kde_thresh/100,'0%',ha='center',va='center',color='k',fontweight='bold')
    ax.text(0.5,-kde_thresh,f'\n-{int(kde_thresh*100)}%',ha='center',va='top',color=kde_palette[150],fontweight='bold')
    ax.text(0.5,-kde_thresh*1.25,'Less\nOften',ha='center',va='top',color=kde_palette[150],fontweight='bold')
    ax.axis('off')
  
    apostrophe_text = "'" if card_player[-1]=='s' else "'s"
    adjusted_pitch_name = pitch_names[pitch_type] if (card_player != 'Kutter Crawford') | (pitch_names[pitch_type] != 'Cutter') else 'Kutter'
    fig.suptitle(f"{card_player}{apostrophe_text} {year} {adjusted_pitch_name} Locations",ha='center',y=1, fontsize=18)
    date_text = '' if (start_date==season_start) & (end_date==season_end) else f'{start_date:%b %-d} - {end_date:%b %-d}; '
    fig.text(0.5,0.88,f"({date_text}From Pitcher's Perspective; Relative to MLB; as of {data_date.strftime('%-m-%-d-%Y')})\n\n", ha='center', va='bottom')
    # fig.text(0.5,0.88,"(From Pitcher's Perspective; Relative to MLB)\n\n",ha='center',va='bottom')
    sns.despine(left=True,bottom=True)

    # Add PL logo
    pl_ax = fig.add_axes([0.41,0.015,0.2,0.2], anchor='S', zorder=1)
    pl_ax.imshow(logo)
    pl_ax.axis('off')
    #plot the fig
    st.pyplot(fig)

heatmap_thresh = 95 
if st.button("Generate Visualizations"):
    pitch_analysis_card(card_player,pitch_type,chart_type,filename)
    if pitch_df.loc[(pitch_df['pitchername']==card_player) & (pitch_df['pitchtype']==pitch_type)].shape[0] < heatmap_thresh :
        st.write(f'Not enough pitches (<{heatmap_thresh}) to generate heatmaps')
    else:
       # Use image saved on the server if it exists
        # if (key_exists(client, AWS_S3_BUCKET, filename_2) == 'true') & (card_player != 'Zack Wheeler'):
        #     st.markdown(f"![image](https://s3.amazonaws.com/{AWS_S3_BUCKET}/{filename_2}#full)")
        # else:    
        kde_diffs = kde_calcs(base_df,pitcher=card_player,pitchtype=pitch_type,year=year)
        kde_chart(kde_diffs,p_hand)


# st.dataframe((pitch_df
#               .loc[(pitch_df['pitchername']==card_player) &
#                       (pitch_df['pitchtype']==pitch_type)]
#               .assign(p_x = lambda x: x['p_x']*-1)))

st.title("Metric Definitions")
st.write("- ***Velocity***: Release speed of the pitch, out of the pitcher's hand (in miles per hour).")
st.write('- ***Release Extension***: Distance towards the plate when the pitcher releases the pitch (in feet).')
st.write('- ***Induced Vertical Break (IVB)***: Vertical break of the pitch, controlling for the effect of gravity (in inches).')
st.write("- ***Arm-Side Break***: Horizontal break of the pitch, relative to the pitcher's handedness (in inches).")
st.write("- ***Adjusted Vertical Approach Angle (VAA)***: Vertical angle at which the pitch approaches home plate, controlling for its vertical location at the plate (in degrees).")
st.write("- ***plvLoc+***: Modeled value of the location of the pitch (Plus scale. 100 is league average)")
st.write('- ***Pitch Level Value (PLV)***: Estimated value of the pitch, based on the predicted outcomes of the pitch (0-10 scale. 5 is league average pitch value. PLV is not adjusted for pitch type.).')
