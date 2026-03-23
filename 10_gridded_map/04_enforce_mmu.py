# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Enforce minimum mapping unit
# Author: Timm Nawrocki
# Last Updated: 2026-01-25
# Usage: Must be executed in an ArcGIS Pro Python 3.9+ distribution.
# Description: "Enforce minimum mapping unit" removes and replaces map units less than 1 acre in area.
# ---------------------------------------------------------------------------

# Import packages
import os
import time
from akutils import *
import arcpy
from arcpy.sa import BoundaryClean
from arcpy.sa import Con
from arcpy.sa import ExtractByAttributes
from arcpy.sa import ExtractByMask
from arcpy.sa import Expand
from arcpy.sa import MajorityFilter
from arcpy.sa import Nibble
from arcpy.sa import Raster
from arcpy.sa import RegionGroup
from arcpy.sa import SetNull

# Set round date
round_date = 'round_20260123'

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
work_geodatabase = os.path.join(project_folder, 'DoD_Navy_Arctic.gdb')
input_folder = os.path.join(project_folder, 'Data_Output/evt', round_date)
intermediate_folder = os.path.join(input_folder, 'intermediate')
output_folder = os.path.join(project_folder, 'Data_Output/evt', round_date)

# Define input datasets
area_input = os.path.join(project_folder, 'Data_Input/ArcticCoastal_MapDomain_10m_3338.tif')
vegetation_input = os.path.join(input_folder, 'ArcticCoastal_Vegetation_10m_3338.tif')

# Define intermediate datasets
disturbed_intermediate = os.path.join(intermediate_folder, 'disturbed_intermediate.tif')
smoothed_intermediate = os.path.join(intermediate_folder, 'smoothed_intermediate.tif')
region_intermediate = os.path.join(intermediate_folder, 'region_intermediate.tif')
mask_intermediate = os.path.join(intermediate_folder, 'mask_intermediate.tif')
nibble_intermediate = os.path.join(intermediate_folder, 'nibble_intermediate.tif')

# Define output datasets
vegetation_output = os.path.join(output_folder, 'ArcticCoastal_Vegetation_1600mmu_10m_3338.tif')

# Set overwrite option
arcpy.env.overwriteOutput = True

# Specify core usage
arcpy.env.parallelProcessingFactor = '0'

# Set workspace
arcpy.env.workspace = work_geodatabase

# Set snap raster and extent
arcpy.env.snapRaster = area_input
arcpy.env.extent = Raster(area_input).extent

# Set output coordinate system
arcpy.env.outputCoordinateSystem = Raster(area_input)

# Set cell size environment
cell_size = arcpy.management.GetRasterProperties(area_input, 'CELLSIZEX', '').getOutput(0)
arcpy.env.cellSize = int(cell_size)

#### IDENTIFY DISTURBED TUNDRA
####____________________________________________________

# Expand infrastructure by 50 m
print('Identifying disturbed tundra...')
iteration_start = time.time()
print('\tExpanding infrastructure...')
expand_raster = Expand(vegetation_input, 5, 39)

# Substitute disturbed tundra into original raster
print('\tSubstituting disturbed tundra into original...')
disturbed_raster = Con((expand_raster == 39) & (Raster(vegetation_input) == 26),
                       40, Raster(vegetation_input))

# Set waterbodies (38) and infrastructure (39) to null
print('\tSetting waterbodies and infrastructure to null...')
null_raster = SetNull((disturbed_raster == 38) | (disturbed_raster == 39),
                      disturbed_raster)

# Export raster
print('\tExporting intermediate raster...')
arcpy.management.CopyRaster(null_raster,
                            disturbed_intermediate,
                            '',
                            '',
                            '255',
                            'NONE',
                            'NONE',
                            '8_BIT_UNSIGNED',
                            'NONE',
                            'NONE',
                            'TIFF',
                            'NONE',
                            'CURRENT_SLICE',
                            'NO_TRANSPOSE')
arcpy.management.CalculateStatistics(disturbed_intermediate)
arcpy.management.BuildRasterAttributeTable(disturbed_intermediate, 'Overwrite')
end_timing(iteration_start)

#### SMOOTH GEOMETRIES
####____________________________________________________

# Clean raster boundaries
print('Smoothing geometries...')
iteration_start = time.time()
print('\tCleaning boundaries...')
raster_boundary = BoundaryClean(disturbed_intermediate,
                                'DESCEND',
                                'TWO_WAY')

# Apply majority filter
print('\tApplying majority filter...')
raster_majority = MajorityFilter(raster_boundary,
                                 'EIGHT',
                                 'MAJORITY')

# Export raster
print('\tExporting intermediate raster...')
arcpy.management.CopyRaster(raster_majority,
                            smoothed_intermediate,
                            '',
                            '',
                            '255',
                            'NONE',
                            'NONE',
                            '8_BIT_UNSIGNED',
                            'NONE',
                            'NONE',
                            'TIFF',
                            'NONE',
                            'CURRENT_SLICE',
                            'NO_TRANSPOSE')
arcpy.management.CalculateStatistics(smoothed_intermediate)
arcpy.management.BuildRasterAttributeTable(smoothed_intermediate, 'Overwrite')
end_timing(iteration_start)

#### ENFORCE MMU
####____________________________________________________

# Enforce MMU
print('Enforcing minimum mapping unit...')
iteration_start = time.time()

# Calculate regions
print('\tCalculating contiguous value areas...')
prelim_raster = Raster(smoothed_intermediate)
region_initial = RegionGroup(prelim_raster,
                             'FOUR',
                             'WITHIN',
                             'NO_LINK')

# Create mask
print('\tCalculating mask...')
criteria = f'COUNT > 16'
mask_1 = ExtractByAttributes(region_initial, criteria)
mask_2 = SetNull(((prelim_raster == 0) & (prelim_raster == 255)
                  | (prelim_raster == 254) | (prelim_raster == 253)
                  | (prelim_raster == 252) | (prelim_raster == 251)
                  | (prelim_raster == 38) | (prelim_raster == 39)),
                 mask_1)

# Interpolate removed data
print('\tInterpolating contiguous areas below minimum mapping unit...')
nibble_initial = Nibble(prelim_raster,
                        mask_2,
                        'DATA_ONLY',
                        'PROCESS_NODATA')

# Add removed data
print('\tReplacing removed values for linear features...')
initial_raster = Raster(vegetation_input)
replace_raster = Con(((initial_raster == 38) | (initial_raster == 39)),
                     initial_raster, nibble_initial)

# Extract raster to study area
print('\tExtracting raster to map domain...')
extract_raster = ExtractByMask(replace_raster, area_input)

# Export output raster
print('\tExporting output raster...')
arcpy.management.CopyRaster(extract_raster,
                            vegetation_output,
                            '',
                            '',
                            '255',
                            'NONE',
                            'NONE',
                            '8_BIT_UNSIGNED',
                            'NONE',
                            'NONE',
                            'TIFF',
                            'NONE',
                            'CURRENT_SLICE',
                            'NO_TRANSPOSE')
arcpy.management.CalculateStatistics(vegetation_output)
end_timing(iteration_start)
