# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Installation summary for Icy Cape
# Author: Timm Nawrocki
# Last Updated: 2026-01-25
# Usage: Execute in Python 3.9+.
# Description: "Installation summary for Icy Cape" calculates summary plots for Icy Cape.
# ---------------------------------------------------------------------------

# Import packages
import os
import pandas as pd
import geopandas as gpd
from rasterstats import zonal_stats
import plotly.express as px
import plotly.graph_objects as go
import kaleido
from akutils import *

# Set nodata value
nodata_value = 255

# Set round date
round_date = 'round_20260123'

# Define diagnostic sets
diagnostic_sets = ['alnus', 'betshr', 'dryas', 'dsalix', 'erivag', 'forb', 'gramin', 'lichen', 'ndsalix',
                   'nerishr', 'rhoshr', 'sphagn', 'vaculi', 'vacvit', 'wetsed']

# Initialize kaleido
kaleido.get_chrome_sync()

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
input_folder = os.path.join(project_folder, 'Data_Input')
output_folder = os.path.join(project_folder, 'Data_Output')

# Define input files
zone_input = os.path.join(input_folder, 'region_data/IcyCape_Installation_3338.shp')
evt_input = os.path.join(output_folder, 'icy_cape_1k', round_date, 'IcyCape_Vegetation_4mmu_0.5m_3338.tif')

# Define output files
type_output = os.path.join(output_folder, 'plots/IcyCape_Type.html')
diagnostic_output = os.path.join(output_folder, 'plots/IcyCape_Diagnostic.html')

#### CALCULATE TYPE ZONAL STATISTICS
####____________________________________________________

# Calculate the total area of the installation
zone_data = gpd.read_file(zone_input)[['Name', 'Owner', 'geometry']]
zone_data['shape_area'] = zone_data.geometry.area
shape_area = zone_data['shape_area'][0]

# Calculate zonal statistics for vegetation types
type_columns = ['raster_value', 'count']
type_stats = zonal_stats(zone_input, evt_input, categorical=True)
if isinstance(type_stats, list):
    stats_dict = type_stats[0]
else:
    stats_dict = type_stats
type_stats = pd.DataFrame(list(stats_dict.items()), columns=['raster_value', 'count'])

# Create dictionary of value labels
value_labels = {
    1: 'Arctic Coastal & Estuarine Barren',
    2: 'Arctic Herbaceous Coastal Beach',
    3: 'Arctic Herbaceous & Shrub Coastal Dune',
    5: 'Arctic Coastal Salt Marsh',
    6: 'Arctic Coastal Dwarf Shrub Graminoid Non-tussock Tundra',
    7: 'Arctic Barren & Sparsely Vegetated Floodplain',
    8: 'Arctic Herbaceous Floodplain',
    9: 'Arctic Willow Floodplain',
    10: 'Arctic Alder(-Willow) Floodplain',
    11: 'Arctic Freshwater Marsh',
    12: 'Arctic Wet Meadow (Floodplain/Mineral)',
    13: 'Arctic Herbaceous Inland Dune',
    14: 'Arctic Willow Inland Dune',
    15: 'Arctic Dryas(-Willow) Floodplain',
    16: 'Arctic Willow Low Shrub',
    18: 'Arctic Birch(-Willow) Shrub',
    19: 'Arctic Alder(-Willow) Shrub',
    20: 'Arctic Ericaceous(-Dryas) Dwarf Shrub',
    21: 'Arctic Dryas(-Willow) Dwarf Shrub',
    22: 'Arctic Tussock Low Shrub Tundra',
    24: 'Arctic Tussock Dwarf Shrub Tundra',
    26: 'Arctic Herbaceous Non-tussock Tundra',
    28: 'Arctic Sphagnum-Sedge Peatland, Ombrotrophic',
    29: 'Arctic Brown Moss-Sedge Peatland, Minerotrophic',
    30: 'Arctic Shrub-Sedge Peatland, Ombrotrophic',
    31: 'Arctic Shrub-Sedge Peatland, Minerotrophic',
    32: 'Arctic Tussock Tundra (Mesic) Polygonal Complex',
    33: 'Arctic Non-tussock (Mesic) Polygonal Complex',
    34: 'Arctic Peatland (Wet) Polygonal Complex',
    36: 'Arctic Barren & Sparsely Vegetated',
    38: 'Persistent Waterbody',
    39: 'Infrastructure',
    40: 'Disturbed Tundra'
}

# Assign labels to data
type_stats['stratum'] = type_stats['raster_value'].map(value_labels)

# Convert counts to area percents
type_stats['cover_percent'] = round(((type_stats['count'] * (0.5*0.5)) / shape_area) * 100, 1)

# Define standard element colors
stratum_colors = {
    'Arctic Coastal & Estuarine Barren': '#FFEAC2',
    'Arctic Herbaceous Coastal Beach': '#897044',
    'Arctic Coastal Salt Marsh': '#00A884',
    'Arctic Dryas(-Willow) Dwarf Shrub': '#3B5D6C',
    'Arctic Tussock Dwarf Shrub Tundra': '#730000',
    'Arctic Herbaceous Non-tussock Tundra': '#35CECD',
    'Arctic Brown Moss-Sedge Peatland, Minerotrophic': '#B6BF8C',
    'Persistent Waterbody': '#BEE8FF',
    'Infrastructure': '#FF0000'
}

# Create structure treemap plot
type_plot = px.treemap(
    type_stats,
    path=['stratum'],
    values='cover_percent',
    color='stratum',
    color_discrete_map=stratum_colors
)

# Update plot formatting
type_plot.update_traces(
    # Increase label font size
    textfont=dict(size=18),
    # Restrict hover to show only the label and the mean value (formatted)
    hovertemplate='<b>%{label}</b><br>Cover Percent: %{value:.1f}%<extra></extra>'
)

# Update layout for margins and dimensions
type_plot.update_layout(
    margin=dict(t=0, l=0, r=0, b=0),
    autosize=True,
    width=None,
    height=400
)

# Export to HTML (interactive) and PNG (publication)
type_plot.write_html(type_output, config={'responsive': True})

#### CALCULATE DIAGNOSTIC SET ZONAL STATISTICS
####____________________________________________________

# Initialize empty data frame for diagnostic species stats
diagnostic_stats = pd.DataFrame(columns=['diagnostic_set', 'cover_percent'])

# Calculate zonal statistics for each diagnostic species set
for diagnostic_set in diagnostic_sets:
    # Define input raster
    diagnostic_input = os.path.join(input_folder, f'foliar_data/{diagnostic_set}_10m_3338.tif')
    # Calculate zonal statistics
    stat_data = zonal_stats(zone_input, diagnostic_input, stats=['mean'])
    if isinstance(stat_data, list):
        stats_dict = stat_data[0]
    else:
        stats_dict = stat_data
    stat_data = pd.DataFrame(list(stats_dict.items()), columns=['stat', 'mean'])
    stat_data['diagnostic_set'] = diagnostic_set
    stat_data['cover_percent'] = round(stat_data['mean'], 1)
    stat_data = stat_data[['diagnostic_set', 'cover_percent']]
    diagnostic_stats = pd.concat([diagnostic_stats if not diagnostic_stats.empty else None,
                                  stat_data],
                                 axis=0)

# Remove zero values
diagnostic_stats = diagnostic_stats[diagnostic_stats['cover_percent'] > 0].copy()
diagnostic_stats = diagnostic_stats[diagnostic_stats['diagnostic_set'].isin(['dryas', 'dsalix', 'erivag',
                                                                             'forb', 'ndsalix', 'nerishr',
                                                                             'sphagn', 'wetsed', 'lichen'])]

# Define standard element colors
diagnostic_colors = {
    'dryas': '#FFEAC2',
    'dsalix': '#897044',
    'erivag': '#00A884',
    'forb': '#3B5D6C',
    'ndsalix': '#730000',
    'nerishr': '#35CECD',
    'sphagn': '#B6BF8C',
    'wetsed': '#BEE8FF',
    'lichen': '#FF0000'
}

# Create structure treemap plot
diagnostic_plot = px.treemap(
    diagnostic_stats,
    path=['diagnostic_set'],
    values='cover_percent',
    color='diagnostic_set',
    color_discrete_map=diagnostic_colors
)

# Update plot formatting
diagnostic_plot.update_traces(
    # Increase label font size
    textfont=dict(size=18),
    # Restrict hover to show only the label and the mean value (formatted)
    hovertemplate='<b>%{label}</b><br>Cover Percent: %{value:.1f}%<extra></extra>'
)

# Update layout for margins and dimensions
diagnostic_plot.update_layout(
    margin=dict(t=0, l=0, r=0, b=0),
    autosize=True,
    width=None,
    height=400
)

# Export to HTML (interactive) and PNG (publication)
diagnostic_plot.write_html(diagnostic_output, config={'responsive': True})