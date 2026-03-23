# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Parse EVT map
# Author: Timm Nawrocki
# Last Updated: 2026-01-25
# Usage: Execute in Python 3.9+.
# Description: "Parse EVT map" implements a programmatic key to create discrete types from foliar cover and surficial features.
# ---------------------------------------------------------------------------

# Import packages
import os
import time
import numpy as np
import rasterio
from rasterio.warp import Resampling
import collections
import dbf
from akutils import *

# Set no data
nodata_value = 255

# Set round date
round_date = 'round_20260123'

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
foliar_folder = os.path.join(project_folder, 'Data_Input/foliar_data')
derived_folder = os.path.join(project_folder, 'Data_Input/derived_data')
ancillary_folder = os.path.join(project_folder, 'Data_Input/ancillary_data')
surficial_folder = os.path.join(project_folder, 'Data_Output/surficial_features', round_date)
output_folder = os.path.join(project_folder, 'Data_Output/evt', round_date)

# Define input files
area_input = os.path.join(project_folder, 'Data_Input/ArcticCoastal_MapDomain_10m_3338.tif')
alnus_input = os.path.join(foliar_folder, 'alnus_10m_3338.tif')
betshr_input = os.path.join(foliar_folder, 'betshr_10m_3338.tif')
dryas_input = os.path.join(foliar_folder, 'dryas_10m_3338.tif')
dsalix_input = os.path.join(foliar_folder, 'dsalix_10m_3338.tif')
empnig_input = os.path.join(foliar_folder, 'empnig_10m_3338.tif')
erivag_input = os.path.join(foliar_folder, 'erivag_10m_3338.tif')
forb_input = os.path.join(foliar_folder, 'forb_10m_3338.tif')
gramin_input = os.path.join(foliar_folder, 'gramin_10m_3338.tif')
lichen_input = os.path.join(foliar_folder, 'lichen_10m_3338.tif')
ndsalix_input = os.path.join(foliar_folder, 'ndsalix_10m_3338.tif')
nerishr_input = os.path.join(foliar_folder, 'nerishr_10m_3338.tif')
rhoshr_input = os.path.join(foliar_folder, 'rhoshr_10m_3338.tif')
sphagn_input = os.path.join(foliar_folder, 'sphagn_10m_3338.tif')
vaculi_input = os.path.join(foliar_folder, 'vaculi_10m_3338.tif')
vacvit_input = os.path.join(foliar_folder, 'vacvit_10m_3338.tif')
wetsed_input = os.path.join(foliar_folder, 'wetsed_10m_3338.tif')

ndshrub_input = os.path.join(derived_folder, 'alder_birch_willow_10m_3338.tif')
eridwarf_input = os.path.join(derived_folder, 'ericaceous_dwarf_10m_3338.tif')
wetind_input = os.path.join(derived_folder, 'wetland_indicator_10m_3338.tif')
herbac_input = os.path.join(derived_folder, 'herbaceous_10m_3338.tif')

flood_input = os.path.join(ancillary_folder,
                           'Floodplain_10m/processed',
                           'ArcticCoastal_Floodplain_10m_3338.tif')
wetland_input = os.path.join(ancillary_folder,
                             'Panarctic_Wetlands_10m/processed',
                             'ArcticCoastal_PanarcticWetland_v1.0_10m_3338.tif')
esa_input = os.path.join(ancillary_folder,
                         'ESA_WorldCover_10m/processed',
                         'ArcticCoastal_ESAWorldCover2_10m_3338.tif')
esri_input = os.path.join(ancillary_folder,
                          'ESRI_LandCover_10m/processed',
                          'ArcticCoastal_ESRILandCover_10m_3338.tif')
slope_input = os.path.join(ancillary_folder,
                           'Topography_10m/processed',
                           'ArcticCoastal_Slope_10m_3338.tif')
coastal_input = os.path.join(ancillary_folder,
                             'Coastal_Zone_10m/processed',
                             'ArcticCoastal_Coastal_10m_3338.tif')
surficial_input = os.path.join(surficial_folder, 'ArcticCoastal_SurficialFeatures_10m_3338.tif')

# Define output file
evt_output = os.path.join(output_folder, 'ArcticCoastal_Vegetation_10m_3338.tif')

# Prepare input rasters
area_raster = rasterio.open(area_input)
alnus_raster = rasterio.open(alnus_input)
betshr_raster = rasterio.open(betshr_input)
dryas_raster = rasterio.open(dryas_input)
dsalix_raster = rasterio.open(dsalix_input)
empnig_raster = rasterio.open(empnig_input)
erivag_raster = rasterio.open(erivag_input)
forb_raster = rasterio.open(forb_input)
gramin_raster = rasterio.open(gramin_input)
lichen_raster = rasterio.open(lichen_input)
ndsalix_raster = rasterio.open(ndsalix_input)
nerishr_raster = rasterio.open(nerishr_input)
rhoshr_raster = rasterio.open(rhoshr_input)
sphagn_raster = rasterio.open(sphagn_input)
vaculi_raster = rasterio.open(vaculi_input)
vacvit_raster = rasterio.open(vacvit_input)
wetsed_raster = rasterio.open(wetsed_input)

ndshrub_raster = rasterio.open(ndshrub_input)
eridwarf_raster = rasterio.open(eridwarf_input)
wetind_raster = rasterio.open(wetind_input)
herbac_raster = rasterio.open(herbac_input)

flood_raster = rasterio.open(flood_input)
wetland_raster = rasterio.open(wetland_input)
surficial_raster = rasterio.open(surficial_input)
esa_raster = rasterio.open(esa_input)
esri_raster = rasterio.open(esri_input)
slope_raster = rasterio.open(slope_input)
coastal_raster = rasterio.open(coastal_input)

# Prepare output profile
output_profile = surficial_raster.profile.copy()
output_profile.update({
    'height': area_raster.height,
    'width': area_raster.width,
    'transform': area_raster.transform,
    'crs': area_raster.crs,
    'nodata': nodata_value,
    'dtype': 'uint8',
    'compress': 'lzw',
    'bigtiff': 'YES'
})

# Parse foliar cover
print(f'Parsing foliar cover to types...')
iteration_start = time.time()
with rasterio.open(evt_output, 'w', **output_profile) as dst:
    # Find number of raster blocks
    window_list = []
    for block_index, window in area_raster.block_windows(1):
        window_list.append(window)
    # Iterate processing through raster blocks
    count = 1
    progress = 0
    for block_index, window in area_raster.block_windows(1):
        #### LOAD BLOCKS
        area_block = area_raster.read(window=window, masked=False)
        alnus_block = alnus_raster.read(window=window, masked=False)
        betshr_block = betshr_raster.read(window=window, masked=False)
        dryas_block = dryas_raster.read(window=window, masked=False)
        dsalix_block = dsalix_raster.read(window=window, masked=False)
        empnig_block = empnig_raster.read(window=window, masked=False)
        erivag_block = erivag_raster.read(window=window, masked=False)
        forb_block = forb_raster.read(window=window, masked=False)
        gramin_block = gramin_raster.read(window=window, masked=False)
        lichen_block = lichen_raster.read(window=window, masked=False)
        ndsalix_block = ndsalix_raster.read(window=window, masked=False)
        nerishr_block = nerishr_raster.read(window=window, masked=False)
        rhoshr_block = rhoshr_raster.read(window=window, masked=False)
        sphagn_block = sphagn_raster.read(window=window, masked=False)
        vaculi_block = vaculi_raster.read(window=window, masked=False)
        vacvit_block = vacvit_raster.read(window=window, masked=False)
        wetsed_block = wetsed_raster.read(window=window, masked=False)

        ndshrub_block = ndshrub_raster.read(window=window, masked=False)
        eridwarf_block = eridwarf_raster.read(window=window, masked=False)
        wetind_block = wetind_raster.read(window=window, masked=False)
        herbac_block = herbac_raster.read(window=window, masked=False)

        flood_block = flood_raster.read(window=window, masked=False)
        wetland_block = wetland_raster.read(window=window, masked=False)
        esa_block = esa_raster.read(window=window, masked=False)
        esri_block = esri_raster.read(window=window, masked=False)
        slope_block = slope_raster.read(window=window, masked=False)
        coastal_block = coastal_raster.read(window=window, masked=False)
        surficial_block = surficial_raster.read(window=window, masked=False)

        #### BEGIN PROGRAMMATIC KEY

        # Set base value
        out_block = np.where(area_block == 1, 0, nodata_value)

        #### GROWTH HABIT SPLITS

        # 254. shrub mesic
        out_block = np.where((out_block == 0)
                             & ((ndshrub_block + eridwarf_block + vaculi_block
                                + dryas_block + dsalix_block ) >= 15)
                             & (wetind_block < 8),
                             254, out_block)

        # 253. shrub wet
        out_block = np.where((out_block == 0)
                             & ((ndshrub_block + eridwarf_block + vaculi_block
                                 + dryas_block + dsalix_block) >= 15)
                             & (wetind_block >= 8),
                             253, out_block)

        # 252. herbaceous mesic
        out_block = np.where((out_block == 0)
                             & ((herbac_block >= 12) & (wetind_block < 8)),
                             252, out_block)

        # 251. herbaceous wet
        out_block = np.where((out_block == 0)
                             & (((herbac_block >= 12) & (wetind_block >= 8))
                                | (wetind_block >= 8)),
                             251, out_block)

        #### TUSSOCK TUNDRA TYPES

        # 22. Arctic Tussock Low Shrub Tundra
        out_block = np.where(((out_block == 0) | (out_block == 254) | (out_block == 253)
                              | (out_block == 252) | (out_block == 251))
                             & (erivag_block >= 20),
                             22, out_block)
        out_block = np.where(((out_block == 0) | (out_block == 254) | (out_block == 253)
                              | (out_block == 252) | (out_block == 251))
                             & (erivag_block >= 10) & (ndshrub_block < 35),
                             22, out_block)
        out_block = np.where(((out_block == 0) | (out_block == 254) | (out_block == 253)
                              | (out_block == 252) | (out_block == 251))
                             & (erivag_block >= 8) & (ndshrub_block < 25)
                             & ((erivag_block / (erivag_block + wetind_block  + 0.1)) >= 0.3),
                             22, out_block)

        # 24. Arctic Tussock Dwarf Shrub Tundra
        out_block = np.where((out_block == 22) & (ndshrub_block < 8),
                             24, out_block)

        #### SHRUB MESIC

        # 16. Arctic Willow Low Shrub
        out_block = np.where((out_block == 254)
                             & (ndsalix_block >= 12),
                             16, out_block)

        # 19. Arctic Alder(-Willow) Shrub
        out_block = np.where(((out_block == 254) | (out_block == 16))
                             & (alnus_block >= 8),
                             19, out_block)

        # 18. Arctic Birch(-Willow) Mesic
        out_block = np.where(((out_block == 254) | (out_block == 16))
                             & (ndsalix_block >= 8)
                             & ((betshr_block + ndsalix_block) >= 12)
                             & ((betshr_block / (betshr_block + ndsalix_block  + 0.1)) >= 0.3),
                             18, out_block)

        # 17. Arctic Birch(-Ericaceous) Mesic
        out_block = np.where((out_block == 254)
                             & (betshr_block >= 8)
                             & ((betshr_block + rhoshr_block + vaculi_block
                                 + vacvit_block + nerishr_block) >= 12)
                             & ((betshr_block / (betshr_block + rhoshr_block + vaculi_block
                                 + vacvit_block + nerishr_block + 0.1)) >= 0.3),
                             17, out_block)

        # 20. Arctic Ericaceous(-Dryas) Dwarf Shrub
        out_block = np.where((out_block == 254)
                             & ((eridwarf_block + dryas_block) >= 12)
                             & ((eridwarf_block / (eridwarf_block + dryas_block  + 0.1)) >= 0.2)
                             & (eridwarf_block >= dsalix_block),
                             20, out_block)

        # 21. Arctic Dryas(-Willow) Dwarf Shrub
        out_block = np.where((out_block == 254)
                             & (((dsalix_block + dryas_block) >= 12)
                                | (dryas_block >= 8) | (dsalix_block >= 8))
                             & (eridwarf_block < dsalix_block),
                             21, out_block)

        #### SHRUB WET

        # 30. Arctic Shrub-Sedge Peatland, Ombrotrophic (Betula or Sphagnum present)
        out_block = np.where((out_block == 253)
                             & (betshr_block + ndsalix_block >= 12)
                             & ((sphagn_block >= 12)
                                | ((betshr_block / (betshr_block + ndsalix_block  + 0.1)) >= 0.2)),
                             30, out_block)

        # 31. Arctic Shrub-Sedge Peatland, Minerotrophic (Betula or Sphagnum absent)
        out_block = np.where((out_block == 253)
                             & ((betshr_block + ndsalix_block) >= 12)
                             & ((sphagn_block < 12)
                                & ((betshr_block / (betshr_block + ndsalix_block + 0.1)) < 0.2)),
                             31, out_block)

        #### HERBACEOUS WET

        # 28. Arctic Shrub-Sedge peatland, ombrotrophic
        out_block = np.where((out_block == 251) & (sphagn_block >= 8),
                             28, out_block)

        # 29. Arctic shrub-sedge peatland, minerotrophic
        out_block = np.where((out_block == 251) & (sphagn_block < 8),
                             29, out_block)

        #### POLYGONAL COMPLEXES

        # 9.33 Arctic Non-tussock (Mesic) Polygonal Complex
        out_block = np.where(((out_block == 253) | (out_block == 0))
                             & ((dryas_block + eridwarf_block + dsalix_block) >= 5)
                             & (wetind_block >= 8),
                             33, out_block)

        # 32. Arctic Tussock Tundra Polygonal Complex
        out_block = np.where(((out_block == 22) | (out_block == 24))
                             & (wetsed_block >= 7),
                             32, out_block)
        out_block = np.where((out_block == 33) & (erivag_block >= 5),
                             32, out_block)

        # 9.34 Arctic peatland polygonal complex
        out_block = np.where(((out_block == 30) | (out_block == 31)
                              | (out_block == 28) | (out_block == 29))
                             & ((erivag_block >= 7)
                                | ((dryas_block + eridwarf_block + dsalix_block) >= 8)),
                             34, out_block)

        #### 10. APPLY SURFICIAL FEATURES

        # 10.2 Arctic Herbaceous Coastal Beach
        out_block = np.where(((out_block == 252) | (out_block == 0))
                             & ((surficial_block == 2) | (surficial_block == 3))
                             & (herbac_block >= 5) & (wetind_block < 3),
                             2, out_block)

        # 10.3 Arctic Herbaceous & Shrub Coastal Dune
        out_block = np.where(((out_block == 252) | (out_block == 254) | (out_block == 16)
                             | (out_block == 18) | (out_block == 0))
                             & (surficial_block == 4)
                             & ((herbac_block >= 5) | (ndshrub_block >= 5)),
                             3, out_block)

        # 10.5 Arctic Coastal Salt Marsh
        out_block = np.where(((out_block == 253) | (out_block == 251) | (out_block == 28)
                              | (out_block == 29) | (out_block == 0))
                             & ((surficial_block == 2) | (surficial_block == 3) | (surficial_block == 4)
                                | (surficial_block == 9))
                             & (wetsed_block >= 5) & ((dsalix_block + dryas_block) < 8),
                             5, out_block)

        # 10.6 Arctic Coastal Dwarf Shrub Graminoid Non-tussock Tundra
        out_block = np.where(((surficial_block == 2) | (surficial_block == 3) | (surficial_block == 4))
                             & (dsalix_block >= 8)
                             & (ndshrub_block < 12) & (erivag_block < 8) & (wetind_block < 8),
                             6, out_block)

        # 10.1 Arctic Coastal & Estuarine Barren
        out_block = np.where((out_block == 0)
                             & ((surficial_block == 2) | (surficial_block == 4)),
                             1, out_block)

        # 10.11 Freshwater marsh
        out_block = np.where(((out_block == 251) | (out_block == 28) | (out_block == 29)
                              | (out_block == 0))
                             & (surficial_block == 8) & (wetsed_block >= 5),
                             11, out_block)

        # 10.13 Arctic Herbaceous Inland Dune
        out_block = np.where(((out_block == 254) | (out_block == 252)
                              | (out_block == 16) | (out_block == 0))
                             & (surficial_block == 5)
                             & ((ndshrub_block < 30) & (erivag_block < 5) & (herbac_block < 30)),
                             13, out_block)

        # 10.14 Arctic Willow Inland Dune
        out_block = np.where((out_block == 13) & (ndshrub_block >= 8),
                             14, out_block)

        # 10.10 Arctic Alder(-Willow) Floodplain
        out_block = np.where((flood_block == 1)
                             & (alnus_block >= 8),
                             10, out_block)

        # 10.9 Arctic Willow Floodplain
        out_block = np.where((flood_block == 1)
                             & (ndsalix_block >= 12)
                             & (alnus_block < 8),
                             9, out_block)

        # 10.15 Arctic Dryas(-Willow) Floodplain
        out_block = np.where((flood_block == 1)
                             & ((dryas_block + dsalix_block) >= 8)
                             & (alnus_block < 8) & (ndsalix_block < 12)
                             & (wetind_block < 5) & (nerishr_block < 5),
                             15, out_block)

        # 10.12 Arctic Wet Meadow (Floodplain)
        out_block = np.where(((flood_block == 1) | (surficial_block == 5))
                             & (wetsed_block >= 8)
                             & (sphagn_block < 3)
                             & ((dryas_block + dsalix_block) < 8)
                             & ((alnus_block < 8) & (ndsalix_block < 12)),
                             12, out_block)

        # 10.8 Arctic herbaceous floodplain
        out_block = np.where((flood_block == 1)
                             & (herbac_block >= 8)
                             & (wetsed_block < 8)
                             & (sphagn_block < 3)
                             & ((dryas_block + dsalix_block) < 8)
                             & ((alnus_block < 8) & (ndsalix_block < 12)),
                             8, out_block)

        # 10.7 Arctic Barren & Sparsely Vegetated Floodplain
        out_block = np.where((out_block == 0) & (flood_block == 1) & (surficial_block == 1),
                             7, out_block)

        # 10.36 Arctic Barren & Sparsely Vegetated
        out_block = np.where((out_block == 0) & (surficial_block == 1),
                             36, out_block)

        # 10.26 Arctic herbaceous (nontussock) tundra
        out_block = np.where(out_block == 252,
                             26, out_block)

        #### CORRECT ERRORS

        # Parse unassigned to coastal barren
        out_block = np.where((out_block == 0)
                             & ((esri_block == 8) | (esa_block == 60))
                             & ((surficial_block == 2) | (surficial_block == 3) | (surficial_block == 4)),
                             1, out_block)

        # Parse unassigned to floodplain barren
        out_block = np.where((out_block == 0)
                             & ((esri_block == 8) | (esa_block == 60))
                             & (flood_block == 1),
                             7, out_block)

        # Parse unassigned to barren
        out_block = np.where((out_block == 0)
                             & ((esri_block == 8) | (esri_block == 6) | (esa_block == 60)),
                             36, out_block)

        # Parse unassigned to coastal beach
        out_block = np.where((out_block == 0)
                             & ((surficial_block == 2) | (surficial_block == 3) | (surficial_block == 4))
                             & (forb_block >= 3)
                             & (wetsed_block < 5),
                             2, out_block)

        # Parse unassigned to salt marsh
        out_block = np.where((out_block == 0)
                             & ((surficial_block == 2) | (surficial_block == 3) | (surficial_block == 4)
                                | (surficial_block == 9))
                             & ((wetsed_block >= 5) | (esri_block == 4)),
                             5, out_block)

        # Correct non-tussock polygonal on slopes
        out_block = np.where((out_block == 33) & (slope_block >= 3) & (sphagn_block >= 5),
                             28, out_block)
        out_block = np.where((out_block == 33) & (slope_block >= 3),
                             29, out_block)

        # Correct mesic polygonal
        out_block = np.where(((out_block == 28) | (out_block == 29) | (out_block == 34))
                             & ((dryas_block + dsalix_block) >= 8),
                             33, out_block)

        #### INFRASTRUCTURE AND WATER

        # 10.39 Infrastructure
        out_block = np.where(surficial_block == 7,
                             39, out_block)

        # 10.40 Disturbed Tundra
        out_block = np.where(
            (out_block == 39)
            & ((alnus_block + betshr_block + dryas_block + dsalix_block
                + erivag_block + ndsalix_block + nerishr_block + rhoshr_block
                + sphagn_block + vaculi_block + vacvit_block + wetsed_block) >= 20),
            40, out_block
        )

        # 10.38 Persistent Waterbody
        out_block = np.where(((out_block != 11) & (out_block != 5))
                              & ((surficial_block == 8) | (surficial_block == 9)),
                             38, out_block)
        out_block = np.where((out_block == 0) & (coastal_block == 1),
                             38, out_block)

        #### WRITE DATA

        # Set no data values from area raster to no data
        out_block = np.where(area_block == 1, out_block, nodata_value)

        # Write results
        dst.write(out_block,
                  window=window)
        # Report progress
        count, progress = raster_block_progress(100, len(window_list), count, progress)
end_timing(iteration_start)

#### BUILD RASTER PYRAMIDS (OVERVIEWS)
####____________________________________________________

# Define overview levels
overview_levels = [2, 4, 8, 16, 32, 64, 128, 256]

# Build pyramids
print(f'Building pyramids...')
iteration_start = time.time()
with rasterio.open(evt_output, 'r+') as dst:
    # Build pyramids with bilinear resampling
    dst.build_overviews(overview_levels, resampling=Resampling.mode)
    # Update metadata to indicate overviews exist
    dst.update_tags(ns='rio_overview', resampling='mode')
end_timing(iteration_start)

#### BUILD RASTER ATTRIBUTE TABLE
####____________________________________________________

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
    17: 'Arctic Birch(-Ericaceous) Shrub',
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

# Specify attribute table file path
attribute_output = evt_output + '.vat.dbf'
if os.path.exists(attribute_output):
    os.remove(attribute_output)

# Define new collection counter
value_counts = collections.Counter()

# Read raster blocks to build attribute values and counts
print('Building value histogram...')
iteration_start = time.time()
with rasterio.open(evt_output) as evt_raster:
    # Find number of raster blocks
    window_list = []
    for block_index, window in evt_raster.block_windows(1):
        window_list.append(window)
    # Iterate processing through raster blocks
    count = 1
    progress = 0
    for block_index, window in evt_raster.block_windows(1):
        input_block = evt_raster.read(1, window=window, masked=True)
        # Use compressed to ignore nodata
        input_data = input_block.compressed()
        if input_data.size == 0:
            # Report progress
            count, progress = raster_block_progress(100, len(window_list), count, progress)
        else:
            # Update the histogram incrementally
            value_counts.update(input_data.tolist())
            # Report progress
            count, progress = raster_block_progress(100, len(window_list), count, progress)
end_timing(iteration_start)

# Raise error for empty output
if not value_counts:
    raise RuntimeError('Raster contains no valid data.')

# Convert counter to sorted lists
print('Building raster attribute table...')
unique_values = sorted(value_counts.keys())
counts = [value_counts[v] for v in unique_values]

# Define DBF table fields
attribute_table = dbf.Table(
    attribute_output,
    'VALUE N(10,0); COUNT N(20,0); LABEL C(64)'
)

# Write attribute table
attribute_table.open(mode=dbf.READ_WRITE)
for value in unique_values:
    count = value_counts[value]
    label = value_labels.get(int(value), "")
    attribute_table.append((int(value), int(count), label))
attribute_table.close()

#### CREATE COLOR MAP
####____________________________________________________

# Create dictionary of value hex colors
value_colors = {
    1: 'FFEAC2',
    2: '897044',
    3: 'B07500',
    5: 'C8F1E5',
    6: 'FFD37F',
    7: 'FFFFBE',
    8: 'D5E600',
    9: 'C5BCD5',
    10: '935B79',
    11: '6A1837',
    12: '59C8A8',
    13: 'CDAA66',
    14: 'FFFF73',
    15: 'A898BE',
    16: 'C668DF',
    18: 'C668DF',
    19: 'C668DF',
    20: '466F81',
    21: '3B5D6C',
    22: 'B14647',
    24: '730000',
    26: '35CECD',
    28: '87C58F',
    29: 'B6BF8C',
    30: '448C4D',
    31: '828D4E',
    32: '942A2A',
    33: '00391F',
    34: '8400A8',
    36: 'CCCCCC',
    38: 'BEE8FF',
    39: 'FF0000',
    40: 'DF9E9E'
}

# Specify colormap file path
colormap_output = evt_output + '.clr'
if os.path.exists(colormap_output):
    os.remove(colormap_output)

# Write colormap
print('Writing colormap...')
with open(colormap_output, 'w') as f:
    for value, hex_color in value_colors.items():
        r, g, b = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        f.write(f'{value} {r} {g} {b}\n')
    f.write('END\n')
