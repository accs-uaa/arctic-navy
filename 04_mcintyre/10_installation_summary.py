# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Installation summary for Point McIntyre
# Author: Timm Nawrocki
# Last Updated: 2026-04-23
# Usage: Execute in Python 3.9+.
# Description: "Installation summary for Point McIntyre" calculates summary plots for Point McIntyre.
# ---------------------------------------------------------------------------

# Define region and AKVEG version
region = 'McIntyre'
version = 'v2.1'
plot_height = 400

# Import packages
import os
import pandas as pd
import geopandas as gpd
import json
from rasterstats import zonal_stats
import plotly.express as px
import kaleido

# Define diagnostic sets
diagnostic_sets = ['betshr', 'dryas', 'dsalix', 'feather', 'halgra', 'erivag', 'lichen',
                   'ndsalix', 'nerishr', 'sphagn', 'waterterrestrial', 'wetforb', 'wetsed']

# Initialize kaleido
kaleido.get_chrome_sync()

# Define year variable
if region == 'IcyCape':
    year = 2020
elif region == 'McIntyre':
    year = 2022
else:
    year = 2024

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
repository_folder = os.path.join(drive, root_folder, 'Repositories/arctic-navy')
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
input_folder = os.path.join(project_folder, 'Data_Input')
output_folder = os.path.join(project_folder, 'Data_Output')

# Define input files
zone_input = os.path.join(input_folder, f'region_data/{region}_Installation_3338.shp')
evt_input = os.path.join(output_folder, f'vegetation_data/{region}_Vegetation_{year}_0.5m_3338.tif')
coast10_input = os.path.join(input_folder, f'rasterized_data/{region}_CoastalZone_10m_3338.tif')
label_input = os.path.join(repository_folder, 'value_labels.json')
color_input = os.path.join(repository_folder, 'value_colors.json')

# Define output files
type_output = os.path.join(output_folder, f'summary_results/{region}_TypeProportions_{year}.html')
diagnostic_output = os.path.join(output_folder, f'summary_results/{region}_DiagnosticProportions_{year}.html')

#### CALCULATE TYPE ZONAL STATISTICS
####____________________________________________________

# Calculate the total area of the installation
zone_data = gpd.read_file(zone_input)[['geometry']]
zone_data['shape_area'] = zone_data.geometry.area
shape_area = zone_data['shape_area'][0]

# Calculate zonal statistics for vegetation types
type_columns = ['raster_value', 'count']
type_stats = zonal_stats(zone_input, evt_input, categorical=True, nodata=255)
if isinstance(type_stats, list):
    stats_dict = type_stats[0]
else:
    stats_dict = type_stats
type_stats = pd.DataFrame(list(stats_dict.items()), columns=['raster_value', 'count'])

# Convert counts to area percents
type_stats['cover_percent'] = round(((type_stats['count'] * (0.5*0.5)) / shape_area) * 100, 1)

# Remove area percents less than 2%
type_stats = type_stats[type_stats['cover_percent'] >= 2]

# Remove coastal barren, disturbed vegetation, infrastructure, and marine water (not suitable for monitoring)
type_stats = type_stats[~type_stats['raster_value'].isin([158, 173, 174, 177])]

# Define unique values
unique_values = type_stats['raster_value'].unique()

# Load the JSON label data
with open(label_input, 'r') as f:
    raw_labels = json.load(f)
value_labels = {
    int(k): v.replace('Arctic ', '')
    .replace('Brown Moss-Sedge Peatland, Minerotrophic', 'Brown Moss-Sedge Peatland,<br>Minerotrophic')
    .replace('Sphagnum-Sedge Peatland, Ombrotrophic', 'Sphagnum-Sedge<br>Peatland,<br>Ombrotrophic')
    for k, v in raw_labels.items() if int(k) in unique_values
}

# Load the JSON color data
with open(color_input, 'r') as f:
    raw_colors = json.load(f)
value_colors = {
    int(k): v for k, v in raw_colors.items() if int(k) in unique_values
}

# Load the JSON color data
with open(color_input, 'r') as f:
    raw_colors = json.load(f)
value_colors = {
    int(k): (v if v.startswith('#') else f"#{v}")
    for k, v in raw_colors.items() if int(k) in unique_values
}

# Assign labels to data
type_stats['stratum'] = type_stats['raster_value'].map(value_labels)

# Construct stratum color dictionary
stratum_colors = {value_labels[k]: color for k, color in value_colors.items() if k in value_labels}

# Create strata treemap plot
type_plot = px.treemap(
    type_stats,
    path=[px.Constant(' '), 'stratum'], # Add total sum
    values='cover_percent',
    color='stratum',
    color_discrete_map=stratum_colors
)

# Force the canvas to be white
colors = list(type_plot.data[0].marker.colors)
for i, label in enumerate(type_plot.data[0].labels):
    if label == ' ':  # Isolate only the background
        colors[i] = 'white'
type_plot.data[0].marker.colors = colors

# Update plot formatting
type_plot.update_traces(
    # Remove inner padding that exposes the root node
    tiling=dict(pad=0),
    # Turn off the gray pathbar header
    pathbar=dict(visible=False),
    # Set tile borders to white (blends into background)
    marker=dict(line=dict(color='white', width=2)),
    # Increase label font size
    textfont=dict(size=14),
    # Display label and percentage directly on the plot
    texttemplate='<b>%{label}</b><br>%{value:.1f}%',
    # Restrict hover to show only the label and the mean value (formatted)
    hovertemplate='<b>%{label}</b><br>Cover Percent: %{value:.1f}%<extra></extra>'
)

# Update layout for margins, dimensions, and background color
type_plot.update_layout(
    template='plotly_white',
    uniformtext=dict(minsize=14, mode='show'),
    margin=dict(t=0, l=0, r=0, b=0),
    autosize=True,
    width=None,
    height=plot_height,
    paper_bgcolor='white',
    plot_bgcolor='white'
)

# Export to HTML (interactive) and PNG (publication)
type_plot.write_html(type_output, config={'responsive': True})
type_plot.write_image(type_output.replace('.html', '.png'), width=800, height=plot_height, scale=10)

#### CALCULATE DIAGNOSTIC SET ZONAL STATISTICS
####____________________________________________________

# Initialize empty list to store diagnostic species summary data
diagnostic_stats_list = []

# Calculate zonal statistics for each diagnostic species set
for diagnostic_set in diagnostic_sets:
    # Set nodata value
    if diagnostic_set == 'waterterrestrial':
        nodata_value = -128
    else:
        nodata_value = -127
    # Define input raster
    diagnostic_input = os.path.join(input_folder, f'foliar_data/{version}/{region}_{diagnostic_set}_10m_3338.tif')
    # Calculate zonal statistics
    stat_data = zonal_stats(zone_input, diagnostic_input, stats=['mean'], nodata=nodata_value)
    if isinstance(stat_data, list):
        stats_dict = stat_data[0]
    else:
        stats_dict = stat_data
    # Extract mean and default to 0 if None is returned
    mean_value = stats_dict.get('mean') or 0
    # Create summary data row and append to list
    summary_data = pd.DataFrame({'diagnostic_abbr': [diagnostic_set], 'cover_percent': [round(mean_value, 1)]})
    diagnostic_stats_list.append(summary_data)

# Concatenate the compiled summary data to a data frame
diagnostic_stats = pd.concat(diagnostic_stats_list, ignore_index=True)

# Remove diagnostic sets that cover less than 2% of ground area
diagnostic_stats = diagnostic_stats[diagnostic_stats['cover_percent'] >= 2].copy()
diagnostic_stats = diagnostic_stats[diagnostic_stats['diagnostic_abbr'].isin(diagnostic_sets)]

# Define names and colors
diagnostic_names = {
    'beach': 'Beach Herbaceous',
    'betshr': 'Birch Shrubs',
    'dryas': 'Dryas Shrubs',
    'dsalix': 'Willow Dwarf Shrubs',
    'feather': 'Feathermosses',
    'halgra': 'Halophytic Graminoids',
    'erivag': 'Tussock Cottongrass',
    'lichen': 'Lichens',
    'ndsalix': 'Willow Shrubs',
    'nerishr': 'Needleleaf Ericaceous Shrubs',
    'sphagn': 'Sphagnum Mosses',
    'waterterrestrial': 'Terrestrial Water',
    'wetforb': 'Wetland Forbs',
    'wetsed': 'Wetland Sedges'
}
diagnostic_colors = {
    'Beach Herbaceous': '#FFEAC2',
    'Birch Shrubs': '#00552E',
    'Dryas Shrubs': '#446589',
    'Willow Dwarf Shrubs': '#6699CD',
    'Feathermosses': '#B4D79E',
    'Halophytic Graminoids': '#00A884',
    'Tussock Cottongrass': '#942A2A',
    'Lichens': '#FFFFBE',
    'Willow Shrubs': '#448970',
    'Needleleaf Ericaceous Shrubs': '#9EBBD7',
    'Sphagnum Mosses': '#87C58F',
    'Terrestrial Water': '#E3F5FF',
    'Wetland Forbs': '#737300',
    'Wetland Sedges': '#99A55E'
}

# Assign full names to abbreviations
diagnostic_stats['diagnostic_set'] = diagnostic_stats['diagnostic_abbr'].map(diagnostic_names)

# Create diagnostic species treemap plot
diagnostic_plot = px.treemap(
    diagnostic_stats,
    path=[px.Constant(' '), 'diagnostic_set'], # Add total sum
    values='cover_percent',
    color='diagnostic_set',
    color_discrete_map=diagnostic_colors
)

# Force the canvas to be white
colors = list(diagnostic_plot.data[0].marker.colors)
for i, label in enumerate(diagnostic_plot.data[0].labels):
    if label == ' ':  # Isolate only the background
        colors[i] = 'white'
diagnostic_plot.data[0].marker.colors = colors

# Update plot formatting
diagnostic_plot.update_traces(
    # Remove inner padding that exposes the root node
    tiling=dict(pad=0),
    # Turn off the gray pathbar header
    pathbar=dict(visible=False),
    # Set tile borders to white (blends into background)
    marker=dict(line=dict(color='white', width=2)),
    # Increase label font size
    textfont=dict(size=14),
    # Display label and percentage directly on the plot
    texttemplate='<b>%{label}</b><br>%{value:.1f}%',
    # Restrict hover to show only the label and the mean value (formatted)
    hovertemplate='<b>%{label}</b><br>Cover Percent: %{value:.1f}%<extra></extra>'
)

# Update layout for margins, dimensions, and background color
diagnostic_plot.update_layout(
    template='plotly_white',
    uniformtext=dict(minsize=14, mode='show'),
    margin=dict(t=0, l=0, r=0, b=0),
    autosize=True,
    width=None,
    height=plot_height,
    paper_bgcolor='white',
    plot_bgcolor='white'
)

# Export to HTML (interactive) and PNG (publication)
diagnostic_plot.write_html(diagnostic_output, config={'responsive': True})
diagnostic_plot.write_image(diagnostic_output.replace('.html', '.png'), width=800, height=plot_height, scale=10)
