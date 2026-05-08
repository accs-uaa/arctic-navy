# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Summary tables
# Author: Timm Nawrocki
# Last Updated: 2026-05-07
# Usage: Execute in Python 3.9+.
# Description: 'Summary tables' calculates summary tables for vegetation type covers and diagnostic species covers for the Icy Cape, Point Barrow, and Point McIntyre installations. The resulting spreadsheet constitutes Appendix 4 of the monitoring plan.
# ---------------------------------------------------------------------------

# Define region and AKVEG version
regions = ['IcyCape', 'Utqiagvik', 'McIntyre']
version = 'v2.1'

# Import packages
import os
import pandas as pd
import geopandas as gpd
import json
import time
from rasterstats import zonal_stats
from akutils import *

# Define diagnostic sets
diagnostic_sets = ['betshr', 'dryas', 'dsalix', 'feather', 'halgra', 'erivag', 'lichen',
                   'ndsalix', 'nerishr', 'sphagn', 'waterterrestrial', 'wetforb', 'wetsed']

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
label_input = os.path.join(repository_folder, 'value_labels.json')

# Define output files
summary_output = os.path.join(output_folder, 'summary_results/Appendix4_SummaryTable_20260507.xlsx')

# Define dictionary for installation boundaries
zone_filenames = {
    'IcyCape': 'IcyCape_Installation_3338.shp',
    'Utqiagvik': 'Barrow_Installation_Main_3338.shp',
    'McIntyre': 'McIntyre_Installation_3338.shp'
}

# Define dictionary for installation years
region_years = {
    'IcyCape': 2020,
    'Utqiagvik': 2024,
    'McIntyre': 2022
}

# Initialize a dictionary to hold all sheet names and tables for export
export_tables = {}

#### PROCESS VEGETATION TYPE DATA SUMMARIES PER REGION
####____________________________________________________

# Create a data summary table for vegetation types for each region
for region in regions:
    print(f'Processing vegetation type summary for {region}...')
    start_time = time.time()

    # Retrieve appropriate year
    year = region_years[region]

    # Define dynamic input files for the current region
    zone_input = os.path.join(input_folder, f'region_data/{zone_filenames[region]}')
    evt_input = os.path.join(output_folder, f'vegetation_data/{region}_Vegetation_{year}_0.5m_3338.tif')

    # Calculate the total area of the installation
    zone_data = gpd.read_file(zone_input)[['geometry']]
    zone_data['shape_area'] = zone_data.geometry.area
    shape_area = zone_data['shape_area'][0]

    # Calculate zonal statistics for vegetation types
    type_stats = zonal_stats(zone_input, evt_input, categorical=True, nodata=255)
    if isinstance(type_stats, list):
        stats_dict = type_stats[0]
    else:
        stats_dict = type_stats
    type_stats = pd.DataFrame(list(stats_dict.items()), columns=['raster_value', 'count'])

    # Convert counts to area percents
    type_stats['cover_percent'] = round(((type_stats['count'] * (0.5 * 0.5)) / shape_area) * 100, 1)

    # Remove coastal barren, infrastructure, and marine water (not suitable for monitoring)
    type_stats = type_stats[~type_stats['raster_value'].isin([174, 176, 177])]

    # Define unique values
    unique_values = type_stats['raster_value'].unique()

    # Load the JSON label data (removed HTML breaks for tables)
    with open(label_input, 'r') as f:
        raw_labels = json.load(f)
    value_labels = {
        int(k): v.replace('Arctic ', '')
        for k, v in raw_labels.items() if int(k) in unique_values
    }

    # Assign labels to data
    type_stats['stratum'] = type_stats['raster_value'].map(value_labels)

    # Prepare final table
    type_stats = type_stats[['stratum', 'cover_percent']].sort_values(by='cover_percent',
                                                                      ascending=False)

    # Store table in dictionary with a sheet name
    if region == 'Utqiagvik':
        region = 'Barrow'
    export_tables[f'{region}_Type'] = type_stats
    end_timing(start_time)

#### PROCESS DIAGNOSTIC SPECIES DATA SUMMARIES PER REGION
####____________________________________________________

# Create a data summary table for diagnostic species sets for each region
for region in regions:
    print(f'Processing diagnostic species summary for {region}...')
    start_time = time.time()

    # Retrieve appropriate year
    year = region_years[region]

    # Define dynamic input files for the current region
    zone_input = os.path.join(input_folder, f'region_data/{zone_filenames[region]}')

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

    # Ensure that diagnostic sets match the target list
    diagnostic_stats = diagnostic_stats[diagnostic_stats['diagnostic_abbr'].isin(diagnostic_sets)]

    # Define names
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

    # Assign full names to abbreviations
    diagnostic_stats['diagnostic_set'] = diagnostic_stats['diagnostic_abbr'].map(diagnostic_names)

    # Prepare final table
    diagnostic_stats = diagnostic_stats[['diagnostic_set', 'cover_percent']].sort_values(by='cover_percent',
                                                                                          ascending=False)

    # Store table in dictionary with a clean sheet name
    if region == 'Utqiagvik':
        region = 'Barrow'
    export_tables[f'{region}_Species'] = diagnostic_stats
    end_timing(start_time)

#### EXPORT TO EXCEL
####____________________________________________________

print(f'Exporting compiled tables...')

# Create the metadata dataframe
metadata = pd.DataFrame({
    'Field Name': ['stratum', 'diagnostic_set', 'cover_percent'],
    'Description': [
        'The name of the vegetation type (i.e., habitat) mapped in the installation. This name corresponds to the map class schema of the AKVEG Map.',
        'The name of the diagnostic species set mapped in the installation. Each diagnostic species set is an individual species or set of ecologically similar species that indicates particular ecological characteristics or conditions.',
        'The percentage of the installation area occupied by the specified vegetation type or diagnostic species set. For the vegetation types, this is calculated as the area occupied by the vegetation type divided by the installation area. For the diagnostic species sets, this is calculated as the mean modeled absolute foliar cover within the installation.'
    ],
    'Data Type': ['Text', 'Text', 'Numeric']
})

# Write output file
with pd.ExcelWriter(summary_output, engine='xlsxwriter') as writer:
    workbook = writer.book
    # Create a format for bold text
    bold_format = workbook.add_format({'bold': True})

    # Write metadata sheet
    metadata.to_excel(writer, sheet_name='Metadata', index=False)
    worksheet = writer.sheets['Metadata']
    # Iterate through columns and write the header with bold format
    for col_num, value in enumerate(metadata.columns.values):
        worksheet.write(0, col_num, value, bold_format)

    # Write all compiled data tables to subsequent sheets
    for sheet_name, output_data in export_tables.items():
        output_data.to_excel(writer, sheet_name=sheet_name, index=False)
        worksheet = writer.sheets[sheet_name]
        # Iterate through columns and write the header with bold format
        for col_num, value in enumerate(output_data.columns.values):
            worksheet.write(0, col_num, value, bold_format)
