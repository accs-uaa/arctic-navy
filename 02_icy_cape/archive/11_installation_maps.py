# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Icy Cape map results
# Author: Timm Nawrocki, Alaska Center for Conservation Science (Translated to Python)
# Last Updated: 2026-04-24
# Usage: Must be executed in a Python 3.9+ environment with geopandas, rioxarray, and matplotlib.
# Description: 'Icy Cape map results' creates a map figure for publication that shows the imagery, 0.5 m vegetation types, and 2 m vegetation types.
# ---------------------------------------------------------------------------

import os
import re
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap, BoundaryNorm
import geopandas as gpd
import rioxarray

# Set global font size
font_size = 20

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:/'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = os.path.join(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
imagery_folder = os.path.join(project_folder, 'Data_Input/imagery_data')
region_folder = os.path.join(project_folder, 'Data_Input/region_data')
vegetation_folder = os.path.join(project_folder, 'Data_Output/vegetation_data')
output_folder = os.path.join(project_folder, 'Data_Output/summary_results')

# Define input files
imagery_input = os.path.join(imagery_folder, 'IcyCape_Imagery_20200714_0.5m_3338.tif')
installation_input = os.path.join(region_folder, 'IcyCape_Installation_3338.shp')
coast_input = os.path.join(region_folder, 'IcyCape_CoastalZone_3338.shp')
vegtype_input = os.path.join(vegetation_folder, 'IcyCape_Vegetation_2020_0.5m_3338.tif')
vegcomplex_input = os.path.join(vegetation_folder, 'IcyCape_Vegetation_2020_900mmu_2m_3338.tif')

# Define output files
figure_output = os.path.join(output_folder, 'IcyCape_Map_Results_py.jpg')


#### DEFINE FUNCTIONS
####____________________________________________________

def get_color_palette(color_path):
    """
    Parses a .clr colormap file and returns a dictionary mapping
    values to hex colors and labels. (In Python, extracting the RAT directly
    from the TIFF requires reading the sidecar .vat.dbf, so we extract labels
    from the .clr file if present, or fallback to class values).
    """
    color_dict = {}
    with open(color_path, 'r') as f:
        for line in f:
            # Keep all lines that start with a digit
            if re.match(r'^\d', line):
                parts = line.strip().split()
                val = int(parts[0])
                r, g, b = int(parts[1]), int(parts[2]), int(parts[3])
                hex_color = f'#{r:02x}{g:02x}{b:02x}'

                # Assume label is at the end of the line if provided, else use the VALUE
                label = " ".join(parts[4:]) if len(parts) > 4 else f"Class {val}"
                color_dict[val] = {'hex': hex_color, 'label': label}

    return color_dict


def plot_categorical_raster(ax, raster_da, palette_dict, extent):
    """Helper function to plot a categorical SpatRaster equivalent in matplotlib."""
    raster_array = raster_da.squeeze().values

    # Get unique values from the raster
    unique_vals = np.unique(raster_array[~np.isnan(raster_array)])

    # Build matplotlib colormap and normalization
    colors = [palette_dict.get(v, {'hex': '#000000'})['hex'] for v in unique_vals]
    cmap = ListedColormap(colors)

    # BoundaryNorm requires boundaries between values
    bounds = list(unique_vals) + [unique_vals[-1] + 1]
    norm = BoundaryNorm(bounds, cmap.N)

    ax.imshow(raster_array, cmap=cmap, norm=norm, extent=extent, interpolation='none')


#### PREPARE VECTOR DATA & DEFINE MAP EXTENT
####____________________________________________________

# Read shapefiles and enforce EPSG:3338
coast_data = gpd.read_file(coast_input).to_crs(epsg=3338)
installation_data = gpd.read_file(installation_input).to_crs(epsg=3338)

# Buffer the installation polygon by 50 meters
installation_buffered = installation_data.buffer(50)

# Create a bounding box based on the 50 m buffered installation bounds
# total_bounds returns [xmin, ymin, xmax, ymax]
bounds = installation_buffered.total_bounds
x_limits = (bounds[0], bounds[2])
y_limits = (bounds[1], bounds[3])

# Matplotlib extent format: [xmin, xmax, ymin, ymax]
map_extent = [bounds[0], bounds[2], bounds[1], bounds[3]]

#### PREPARE RASTER DATA & COLORMAPS
####____________________________________________________

# Read and crop imagery (rioxarray uses minx, miny, maxx, maxy)
imagery_raster = rioxarray.open_rasterio(imagery_input, masked=True)
imagery_crop = imagery_raster.rio.clip_box(minx=bounds[0], miny=bounds[1], maxx=bounds[2], maxy=bounds[3])

# Read and crop vegetation type map
vegtype_raster = rioxarray.open_rasterio(vegtype_input, masked=True)
vegtype_crop = vegtype_raster.rio.clip_box(minx=bounds[0], miny=bounds[1], maxx=bounds[2], maxy=bounds[3])

# Read and crop vegetation type-complex map
vegcomplex_raster = rioxarray.open_rasterio(vegcomplex_input, masked=True)
vegcomplex_crop = vegcomplex_raster.rio.clip_box(minx=bounds[0], miny=bounds[1], maxx=bounds[2], maxy=bounds[3])

# Generate palettes from .clr files
type_palette = get_color_palette(str(vegtype_input) + '.clr')
complex_palette = get_color_palette(str(vegcomplex_input) + '.clr')

# Combine the two color palettes
color_palette = {**type_palette, **complex_palette}

# Extract the labels present in the cropped raster extents
type_present = np.unique(vegtype_crop.squeeze().values)
complex_present = np.unique(vegcomplex_crop.squeeze().values)

# Remove NaNs
type_present = type_present[~np.isnan(type_present)]
complex_present = complex_present[~np.isnan(complex_present)]

# Combine the unique labels from both cropped rasters
all_present_vals = sorted(np.unique(np.concatenate((type_present, complex_present))))

#### BUILD INDIVIDUAL MAP PANELS
####____________________________________________________

# Set up the 2x2 grid figure
fig, axs = plt.subplots(2, 2, figsize=(16, 16), dpi=600, gridspec_kw={'wspace': 0.05, 'hspace': 0.05})

# Map axs indices to standard names
ax_vegtype = axs[0, 0]
ax_vegcomplex = axs[0, 1]
ax_imagery = axs[1, 0]
ax_legend = axs[1, 1]


# Shared styling helper
def style_map_axes(ax, title):
    coast_data.plot(ax=ax, edgecolor='black', facecolor='none', linewidth=0.8)
    installation_data.plot(ax=ax, edgecolor='yellow', facecolor='none', linewidth=0.8)
    ax.set_xlim(x_limits)
    ax.set_ylim(y_limits)
    ax.set_title(title, fontsize=font_size, pad=10, loc='left')
    ax.grid(color='gray', linestyle='-', linewidth=0.5)
    ax.set_xticks([])
    ax.set_yticks([])
    # Hide standard matplotlib border spines to mimic theme_minimal()
    for spine in ax.spines.values():
        spine.set_visible(False)


# --- 1. Create base imagery plot (Bottom Left) ---
# Extract bands 4, 3, 2 for CIR (in xarray, bands are 1-indexed: 4, 3, 2)
# Ensure your imagery's band metadata maps 4=NIR, 3=Red, 2=Green.
cir_array = imagery_crop.sel(band=[4, 3, 2]).values
cir_array = np.moveaxis(cir_array, 0, -1)  # Move bands to last dimension for matplotlib (H, W, 3)

# Apply linear stretch (max_col_value = 220 equivalent)
cir_array = cir_array / 220.0
cir_array = np.clip(cir_array, 0, 1)

ax_imagery.imshow(cir_array, extent=map_extent)
style_map_axes(ax_imagery, 'c. High-resolution (0.5 m) CIR imagery')

# Add label with semi-transparent background
bbox_props = dict(boxstyle="square,pad=0.3", fc="white", ec="none", alpha=0.7)
ax_imagery.text(x_limits[0] + 20, y_limits[0] + 20,
                'Imagery © 2020 Maxar Technologies Inc.',
                fontsize=font_size * 0.7,  # Scaled down slightly to match R scaling
                color='black',
                ha='left', va='bottom',
                bbox=bbox_props)

# --- 2. Create vegetation type map panel (Top Left) ---
plot_categorical_raster(ax_vegtype, vegtype_crop, color_palette, map_extent)
style_map_axes(ax_vegtype, 'a. Vegetation Types (1:2,500 scale)')

# --- 3. Create vegetation type-complex map panel (Top Right) ---
plot_categorical_raster(ax_vegcomplex, vegcomplex_crop, color_palette, map_extent)
style_map_axes(ax_vegcomplex, 'b. Vegetation Types-Complexes (1:10,000 scale)')

#### MERGE AND EXPORT PLOTS
####____________________________________________________

# --- 4. Render Legend (Bottom Right) ---
ax_legend.axis('off')  # Hide the axes entirely for the legend panel

# Create custom handles for the unified legend
legend_handles = []
for val in all_present_vals:
    if val in color_palette:
        color_info = color_palette[val]
        patch = mpatches.Patch(color=color_info['hex'], label=color_info['label'])
        legend_handles.append(patch)

# Add the legend to the empty bottom-right subplot
# labelspacing = 1.0 approx equals 2pt vertical spacing depending on font sizes
leg = ax_legend.legend(handles=legend_handles,
                       title='Vegetation Class',
                       loc='center',
                       fontsize=font_size - 2,
                       title_fontsize=font_size,
                       frameon=False,
                       ncol=2,  # Adjust columns (byrow equivalent)
                       labelspacing=0.8,  # Vertical spacing between items
                       handleheight=2.0,  # Key height (1.1 cm equivalent)
                       handlelength=2.0)  # Key width  (1.1 cm equivalent)

# Adjust title padding
leg._legend_box.align = "left"

# Export plot
plt.savefig(figure_output, format='jpg', dpi=600, bbox_inches='tight', pad_inches=0.1)
plt.close()