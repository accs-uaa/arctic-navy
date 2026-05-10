# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Organize schema
# Author: Timm Nawrocki
# Last Updated: 2026-05-08
# Usage: Execute in Python 3.9+.
# Description: 'Organize schema' combines tables relating the AKVEG map class schema to AKNVC alliances and NRCS Ecological Site Descriptions. This version follows AKNVC 3.0.3. The resulting spreadsheet is Appendix 2.
# ---------------------------------------------------------------------------

# Import packages
import os
import pandas as pd

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic')
input_folder = os.path.join(project_folder, 'Data/Data_Input/schema_data')
aknvc_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/AKNVC/Data/version_3.0.3/processed')
output_folder = os.path.join(project_folder, 'Documents/Report_Final')

# Define input files
schema_input = os.path.join(input_folder, 'NavyArctic_Appendix2_MapSchema_20260508.xlsx')
aknvc_input = os.path.join(aknvc_folder, 'AKNVC_3.0.3.xlsx')

# Define output files
schema_output = os.path.join(output_folder, 'NavyArctic_Appendix2_MapSchema_20260508.xlsx')

#### DEFINE ALLIANCE RELATIONSHIPS
####____________________________________________________

# INSTRUCTIONS: Update the table below to list all alliance codes from the AKNVC that fit within each map class. Only create entries for map classes that target subgroups or alliances. If a map class lacks any described alliances but should have alliances in the future, enter the placeholder text 'undescribed'.

# Define a nested dictionary containing relationships for each map class
class_alliances = {
    # 142.	Arctic Sphagnum-Sedge Peatland, Ombrotrophic
    142: ['undescribed'],
    # 143.	Arctic Brown Moss-Sedge Peatland, Minerotrophic
    143: ['undescribed'],
    # 145.	Arctic Tussock Dwarf Shrub Tundra
    145: ['A2438', 'A2439'],
    # 149.	Arctic Herbaceous Inland Dune
    149: ['A0043ak', 'A0045ak', 'A4294', 'A4295'],
    # 151.	Arctic Dryas(-Willow) Dwarf Shrub
    151: ['A4333', 'A4335'],
    # 152.	Arctic Ericaceous(-Dryas) Dwarf Shrub
    152: ['A4332', 'A4334', 'A4336'],
    # 158.	Arctic Coastal & Estuarine Barren
    158: ['undescribed'],
    # 159.	Arctic Herbaceous Coastal Dune
    159: ['A4296'],
    # 160.	Arctic Herbaceous Coastal Beach
    160: ['A4297'],
    # 161.	Arctic Salt-intruded Tundra
    161: ['undescribed'],
    # 162.	Arctic Coastal Dwarf Willow Graminoid
    162: ['A2217', 'A4312'],
    # 163.	Arctic Coastal Salt Marsh
    163: ['A2121', 'A2122', 'A2123', 'A4311', 'A4313'],
    # 165.	Arctic Barren & Sparsely Vegetated Active Floodplain
    165: ['A4362'],
    # 166.	Arctic Dryas(-Willow-Ericaceous) Floodplain
    166: ['undescribed'],
    # 167.	Arctic Herbaceous Active Floodplain
    167: ['undescribed']
}

#### PROCESS AKNVC ALLIANCES
####____________________________________________________

# Read input data sheets
schema_data = pd.read_excel(schema_input, sheet_name='Schema')
correspondence_data = pd.read_excel(schema_input, sheet_name='Correspondence')
alliance_data = pd.read_excel(aknvc_input, sheet_name='mid_levels')

# Join alliance by group
print('Joining alliances by group...')
schema_alliances = pd.merge(schema_data, alliance_data, on='group_code')
schema_alliances = schema_alliances[['code', 'map_class', 'alliance_code', 'alliance_akname']]

# Create a Boolean mask starting with all rows set to True
mask = pd.Series(True, index=schema_alliances.index)

# Loop through the dictionary and update the Boolean mask
print('Creating valid alliance mask...')
for code, retained_list in class_alliances.items():
    is_current_code = schema_alliances['code'] == code
    is_retained_alliance = schema_alliances['alliance_code'].isin(retained_list)
    mask = mask & (~is_current_code | is_retained_alliance)

# Apply the inclusion mask to the dataframe
schema_alliances = schema_alliances[mask]

# Collapse alliance correspondence into code list
print('Collapsing list of alliances...')
collapse_alliances = (schema_alliances
                      .groupby('code')['alliance_code']
                      .apply(lambda x: ', '.join(x.dropna().astype(str)))
                      .reset_index()
                      .rename(columns={'alliance_code': 'alliance_codes'}))

# Identify all map classes that do not correspond to any alliances
missing_codes = set(schema_data['code']) - set(collapse_alliances['code'])

# Generate rows for missing map classes
if missing_codes:
    missing_rows = []
    for code in missing_codes:
        # Identify target from schema
        target = schema_data.loc[schema_data['code'] == code, 'target'].values[0]
        # Define placeholder value
        if class_alliances.get(code) == ['undescribed']:
            placeholder_value = 'undescribed'
        elif target == 'complex':
            placeholder_value = 'complex'
        else:
            placeholder_value = 'none'
        # Append data row
        missing_rows.append({'code': code, 'alliance_codes': placeholder_value})
    # Convert missing rows to dataframe
    missing_data = pd.DataFrame(missing_rows)
    # Combine original collapsed data with generated missing rows
    collapse_alliances = pd.concat([collapse_alliances, missing_data], ignore_index=True)

#### PROCESS ECOLOGICAL SITES
####____________________________________________________

# Create ecological site table
schema_esd = correspondence_data[['code', 'map_class', 'esd_code', 'esd_name']].dropna()

# Collapse ecological sites into code list
print('Collapsing list of Ecological Site Description codes...')
collapse_esd = (schema_esd
                .groupby('code')['esd_code']
                .apply(lambda x: ', '.join(x.dropna().astype(str)))
                .reset_index()
                .rename(columns={'esd_code': 'ecological_site_codes'}))

#### EXPORT MAP SCHEMA
####____________________________________________________

print('Exporting map schema...')

# Join the alliance lists and replace missing values with a blank string
schema_data = pd.merge(schema_data, collapse_alliances, on='code', how='left').fillna({'alliance_codes': ''})

# Join the ecological site lists and replace missing values with a blank string
schema_data = pd.merge(schema_data, collapse_esd, on='code', how='left').fillna({'ecological_site_codes': ''})

# Attribute the abiotic types
schema_data.loc[schema_data['code'].isin([173, 174, 176, 177]), 'bioclimatic_zone'] = 'None'

# Sort all export tables by map class code
schema_data = schema_data.sort_values(by='code')
schema_alliances = schema_alliances.sort_values(by=['code', 'alliance_code'])
schema_esd = schema_esd.sort_values(by=['code', 'esd_code'])

# Create output table dictionary
export_tables = {'map_schema': schema_data,
                 'schema_alliances': schema_alliances,
                 'schema_ESDs': schema_esd}

# Create the metadata dataframe
metadata = pd.DataFrame({
    'Field Name': ['bioclimatic_zone', 'structure', 'category', 'physiography_limit',
                   'code', 'map_class', 'target', 'macrogroup_code', 'macrogroup',
                   'group_code', 'group', 'alliance_codes', 'ecological_site_codes',
                   'alliance_code', 'alliance_akname', 'esd_code', 'esd_name'],
    'Description': [
        'The bioclimatic zone within which the map class occurs. Bioclimatic zone summarizes broad climate patterns that organize vegetation communities and is defined according to the AKVEG Map Bioclimatic Zones and Vegetation Regions.',
        'A categorical descriptor of the dominant vertical structural element of the map class.',
        'A categorical descriptor of the primary driving environmental factor, ignoring climate.',
        'A categorical descriptor of the physiography associated with the map class. A value of "none" indicates that the map class is not limited to a single physiography.',
        'The unique numerical id and raster value that corresponds to the map class.',
        'The name of the map class.',
        'The hierarchical level from the Alaska version of U.S. National Vegetation Classification that the map class represents.',
        'The unique code for the macrogroup from the Alaska version of U.S. National Vegetation Classification that the map class fits within.',
        'The name of the macrogroup from the Alaska version of U.S. National Vegetation Classification that the map class fits within.',
        'The unique code for the group from the Alaska version of U.S. National Vegetation Classification that the map class fits within or represents.',
        'The name of the group from the Alaska version of U.S. National Vegetation Classification that the map class fits within or represents.',
        'A machine-readable list of alliance codes from the Alaska version of U.S. National Vegetation Classification that the map class represents. If multiple alliance codes are listed (separated by commas within the brackets), then the map class does not distinguish among the corresponding alliances.',
        'A machine-readable list of Ecological Site Description (ESD) codes developed by Natural Resources Conservation Service that the map class corresponds to. Map classes and ESDs can have many-to-many relationships.',
        'In the one-to-many schema_alliances sheet, the code for each alliance from the Alaska version of U.S. National Vegetation Classification that each map class represents.',
        'In the one-to-many schema_alliances sheet, the name of each alliance from the Alaska version of U.S. National Vegetation Classification that each map class represents.',
        'In the many-to-many schema_ESDs sheet, the code for the Ecological Site Description that each map class corresponds to.',
        'In the many-to-many schema_ESDs sheet, the name of the Ecological Site Description that each map class corresponds to.'
    ],
    'Data Type': ['Text', 'Text', 'Text', 'Text', 'Numeric', 'Text', 'Text', 'Text', 'Text', 'Text', 'Text',
                  'Comma-separated Text', 'Comma-separated Text', 'Text', 'Text', 'Text', 'Text']
})

# Write output file
with pd.ExcelWriter(schema_output, engine='xlsxwriter') as writer:
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
