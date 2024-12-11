# -*- coding: utf-8 -*-
"""
Created on Wed Sep 13 12:20:01 2023

@author: steve hamilton
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

#### Creating Data Files ####################################################################
#
# Use shared queries in Jira to export Excel (CSV) files. Note: Jira only exports
#  1,000 rows at a time. At the time of this script it required three batches.
# Place all raw .csv files into the folder called raw_data. The script will read
# any/all .csv files in the directory and stitch them together.
# Explore Jira/Python plugins if you want to automate this step
#
##############################################################################################
pd.set_option('display.max_columns', None)

def read_and_combine_csv():
    path = 'raw_data'
    csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]

    dataframes = []

    for file in csv_files:
        file_path = os.path.join(path, file)
        df = pd.read_csv(file_path)
        dataframes.append(df)

    combined_df = pd.concat(dataframes, ignore_index=True, sort=False)

    return combined_df

def calc_cycle_time(row):
    # note: This isn't exactly a true cycle time calculation but should provide directionally
    #       correct analysis. Jira does not provide a systematic way to understand when work started on an issue.
    #       instead this query returns issues that were moved to 'in progress' in the last 6
    #       months and also closed in the last 6 months. So this calculation returns the date
    #       that the issue was resolved if populated (some workflows removed this at ARC -- in 
    #       those cases we default to using the last date updated)
    if row['resolved'] == 0 or row['resolved'] is None:
        return np.inf
    else:
        return (row['resolved'] - row['created']).days

if os.path.exists('summary_data.txt'):
    os.remove('summary_data.txt')
    
raw = read_and_combine_csv()
raw['updated'] = pd.to_datetime(raw['Updated'], errors='coerce')
raw['created'] = pd.to_datetime(raw['Created'], errors='coerce')
raw['resolved'] = pd.to_datetime(raw['Resolved'], errors='coerce')
#raw['resolved'] = raw.fillna(0, inplace=True)  #GPI does not set resolved for any issues
raw['cycle_time'] = raw.apply(calc_cycle_time, axis=1)
#raw['cycle_time'] = (raw['resolved'] - raw['created']).dt.days #if resolved is set consistently this calc can be used
colnames = {'Summary':'summary','Project name':'project_name','Custom field (Story Points)':'story_points','Description':'description'}
raw.rename(columns=colnames,inplace=True)
raw['story_points'].fillna(0,inplace=True)
raw['cycle_time'].fillna(0,inplace=True)

df = raw.loc[:,['project_name','updated','created','resolved','story_points','cycle_time']]

df['count'] = 1
df['date'] = df['resolved'].combine_first(df['updated'])

df.set_index('date', inplace=True)

# Grouping by 2-week intervals and project, then summing
df_bi_weekly = df.groupby([pd.Grouper(freq='2W'), 'project_name']).agg({
    'story_points': 'sum',
    'cycle_time': 'mean',
    'count': 'sum'  # Counting the number of rows in each group
}).reset_index()
df_bi_weekly.set_index('date', inplace=True)

# Calculate bi-weekly average cycle time
df_bi_weekly_average = df.groupby(['project_name']).resample('2W').mean().reset_index()
df_bi_weekly_average.set_index('date', inplace=True)

descriptions = raw.loc[:,['project_name','description']]
descriptions['length'] = descriptions['description'].str.len()
descriptions['length'].fillna(0,inplace=True)
descriptions = descriptions.loc[:,['project_name','length']]

# Plotting
projects = set(df_bi_weekly['project_name'])

for project in projects:
    p = df_bi_weekly[df_bi_weekly['project_name'] == project]
    p_avg = df_bi_weekly_average[df_bi_weekly_average['project_name'] == project]
    std_bi_weekly_points = p['story_points'].rolling(window=2).std()
    std_bi_weekly_cycle = p['cycle_time'].rolling(window=2).std()
    std_bi_weekly_count = p['count'].rolling(window=2).std()
    
    d = descriptions[descriptions['project_name'] == project]

    #calculate cumulative sum diff for st.dev on cycle time
    cusum_cycle_stdev = np.cumsum(std_bi_weekly_cycle)
    cusum_cycle_stdev[np.isnan(cusum_cycle_stdev)]=0
    cusum_cycle_shift_stdev = np.roll(cusum_cycle_stdev,1)
    cusum_cycle_shift_stdev[np.isnan(cusum_cycle_shift_stdev)]=0
    cusum_cycle_shift_stdev[0] = 0
    change_cycle_stdev = np.where(np.abs(cusum_cycle_stdev - cusum_cycle_shift_stdev) > 1)[0]
    changes_cycle_stdev = np.zeros_like(std_bi_weekly_cycle)
    changes_cycle_stdev[change_cycle_stdev] = 1
    changes_cycle_stdev = pd.Series(changes_cycle_stdev, index = p.index)

    #calculate cumulative sum diff for st.dev on story points
    cusum_points_stdev = np.cumsum(std_bi_weekly_points)
    cusum_points_shift_stdev = np.roll(cusum_points_stdev,1)
    cusum_points_shift_stdev[0] = 0
    change_points_stdev = np.where(np.abs(cusum_points_stdev - cusum_points_shift_stdev) > 1)[0]
    changes_points_stdev = np.zeros_like(std_bi_weekly_points)
    changes_points_stdev[change_points_stdev] = 1
    changes_points_stdev = pd.Series(changes_points_stdev, index = p.index)

    #calculate cumulative sum diff for st.dev on cycle time
    cusum_count_stdev = np.cumsum(std_bi_weekly_count)
    cusum_count_shift_stdev = np.roll(cusum_count_stdev,1)
    cusum_count_shift_stdev[0] = 0
    change_count_stdev = np.where(np.abs(cusum_count_stdev - cusum_count_shift_stdev) > 1)[0]
    changes_count_stdev = np.zeros_like(std_bi_weekly_count)
    changes_count_stdev[change_count_stdev] = 1
    changes_count_stdev = pd.Series(changes_count_stdev, index = p.index)
    changes_count_stdev.fillna(0,inplace=True)
 
    #plot story points
    fig, ax = plt.subplots(3, 1, figsize=(12, 8))
    line1, = ax[0].plot(p['story_points'],color='blue', label='Story Points')
    line2, = ax[0].plot(std_bi_weekly_count, color='orange', label='St.Dev')
    ax2 = ax[0].twinx()
    scatter = ax2.scatter(changes_points_stdev.index,changes_points_stdev, color='red', label='St.Dev Change')
    ax[0].xaxis.set_tick_params(rotation=45)
    ax[0].xaxis_date()
    ax[0].set_title(f'Bi-weekly Story Points - {project}')
    lines, labels = ax[0].get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax[0].legend(lines + lines2, labels + labels2, loc='upper left')

    #plot cycle time
    line1, = ax[1].plot(p['cycle_time'],color='blue', label='Cycle Time')
    ax3 = ax[1].twinx()
    scatter = ax3.scatter(changes_cycle_stdev.index,changes_cycle_stdev, color='red', label='St.Dev Change')
    ax[1].xaxis.set_tick_params(rotation=45)
    ax[1].xaxis_date()
    ax[1].set_title(f'Bi-weekly Mean Cycle Time - {project}')
    lines, labels = ax[1].get_legend_handles_labels()
    lines2, labels2 = ax3.get_legend_handles_labels()
    ax[1].legend(lines + lines2, labels + labels2, loc='upper left')

    #plot story count
    line1, = ax[2].plot(p['count'],color='blue', label='Story Count')
    ax4 = ax[2].twinx()
    scatter = ax4.scatter(changes_count_stdev.index,changes_count_stdev, color='red', label='St.Dev Change')
    ax[2].xaxis.set_tick_params(rotation=45)
    ax[2].xaxis_date()
    ax[2].set_title(f'Bi-weekly Story Count - {project}')
    lines, labels = ax[2].get_legend_handles_labels()
    lines2, labels2 = ax4.get_legend_handles_labels()
    ax[2].legend(lines, labels, loc='upper left')

    h = df[df['project_name'] == project]

    figH, axH = plt.subplots(3,1, figsize=(8,8))
    axH[0].hist(h['story_points'], bins=np.arange(min(h['story_points']), max(h['story_points']) + 1, 1), align='left')
    axH[0].set_title(f'Story Point Histogram: {project}')
    axH[0].set_ylabel("Count")
    axH[0].set_xlabel("Story Size (points)")

    axH[1].hist(h['cycle_time'], bins=20, align='left')
    axH[1].set_title(f'Cycle Time Histogram: {project}')
    axH[1].set_ylabel("Count")
    axH[1].set_xlabel("Cycle Time (days)")

    axH[2].hist(d['length'], bins=20, align='left')
    axH[2].set_title(f'Description Length Histogram: {project}')
    axH[2].set_ylabel("Count")
    axH[2].set_xlabel("Description Length")

    plt.figure(fig.number)
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.6)  # adjust to your needs
    plt.savefig(f'{project}-Timeseries')

    plt.figure(figH.number)
    plt.tight_layout()
    plt.subplots_adjust(hspace=0.6)  # adjust to your needs
    plt.savefig(f'{project}-Hist')
    print(f'{project} story points: {sum(h["story_points"])}')
    print(f'{project} story count: {len(h["story_points"])}')
    with open('summary_data.txt','a') as file:
        file.write(f'*****{project}*****\n{h.describe()}\n\n')
        file.write(f'Descriptions\n{d.describe().to_string()}\n\n')
    

#    plt.show()
