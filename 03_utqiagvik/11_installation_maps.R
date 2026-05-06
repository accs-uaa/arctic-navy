# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Utqiagvik map results
# Author: Timm Nawrocki, Alaska Center for Conservation Science
# Last Updated: 2026-04-24
# Usage: Must be executed in a R 4.4.3+ installation.
# Description: 'Utqiagvik map results' creates a map figure for publication that shows the imagery, 0.5 m vegetation types, and 2 m vegetation types.
# ---------------------------------------------------------------------------

# Import required libraries
library(dplyr)
library(fs)
library(ggplot2)
library(ggpubr)
library(cowplot)
library(ggspatial)
library(sf)
library(terra)
library(tidyterra)

# Set global font size
font_size = 19

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = path(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
imagery_folder = path(project_folder, 'Data_Input/imagery_data')
region_folder = path(project_folder, 'Data_Input/region_data')
vegetation_folder = path(project_folder, 'Data_Output/vegetation_data')
output_folder = path(project_folder, 'Data_Output/summary_results')

# Define input files
imagery_input = path(imagery_folder, 'Utqiagvik_Imagery_20240710_0.5m_3338.tif')
installation_input = path(region_folder, 'Barrow_Installation_Main_3338.shp')
coast_input = path(region_folder, 'Utqiagvik_CoastalZone_3338.shp')
vegtype_input = path(vegetation_folder, 'Utqiagvik_Vegetation_2024_0.5m_3338.tif')
vegcomplex_input = path(vegetation_folder, 'Utqiagvik_Vegetation_2024_900mmu_2m_3338.tif')

# Define output files
figure_output = path(output_folder, 'Utqiagvik_VegetationMaps_2024.jpg')

#### DEFINE FUNCTIONS
####____________________________________________________

# Define a function to append the colormap color values to the raster attribute table labels
get_color_palette = function(input_raster, color_path) {
  # Read raw lines from the colormap file
  raw_lines = readLines(color_path)
  
  # Keep all lines that start with a digit
  color_lines = raw_lines[grepl('^[0-9]', raw_lines)]
  
  # Add R, G, B values from the colormap to a table
  rgb_data = read.table(text = color_lines, header = FALSE)
  
  # Convert RGB columns to hex codes
  hex_colors = rgb(rgb_data[,2], rgb_data[,3], rgb_data[,4], maxColorValue = 255)
  
  # Create a data frame mapping VALUE to Hex
  color_data = data.frame(VALUE = rgb_data[,1], hex = hex_colors)
  
  # Extract the Raster Attribute Table
  attribute_data = levels(input_raster)[[1]]
  
  # Merge colors to the attribute data by VALUE
  merged_data = merge(attribute_data, color_data, by = 'VALUE')
  
  # Create named vector mapping LABEL to hex color for ggplot
  palette = setNames(merged_data$hex, merged_data$LABEL)
  return(palette)
}

#### PREPARE VECTOR DATA & DEFINE MAP EXTENT
####____________________________________________________

# Read shapefiles and enforce EPSG:3338
coast_data = st_read(coast_input) %>% 
  st_transform(crs = 3338)
installation_data = st_read(installation_input) %>% 
  st_transform(crs = 3338)

# Buffer the installation polygon by 50 meters
installation_buffered = st_buffer(installation_data, dist = 50)

# Create a bounding box based on the 50 m buffered installation bounds
bounding_box = st_bbox(installation_buffered)
bounding_3338 = st_as_sfc(bounding_box)

# Extract x and y limits from the buffered bounding box
x_limits = c(bounding_box['xmin'], bounding_box['xmax'])
y_limits = c(bounding_box['ymin'], bounding_box['ymax'])

#### PREPARE RASTER DATA & COLORMAPS
####____________________________________________________

# Read and crop imagery
imagery_raster = rast(imagery_input)
imagery_crop = crop(imagery_raster, bounding_3338)

# Read and crop vegetation type map
vegtype_raster = rast(vegtype_input)
vegtype_crop = crop(vegtype_raster, bounding_3338)

# Read and crop vegetation type-complex map
vegcomplex_raster = rast(vegcomplex_input)
vegcomplex_crop = crop(vegcomplex_raster, bounding_3338)

# Generate palettes from .clr files
type_palette = get_color_palette(vegtype_crop, paste0(vegtype_input, '.clr'))
complex_palette = get_color_palette(vegcomplex_crop, paste0(vegcomplex_input, '.clr'))

# Combine the two color palettes and remove duplicate types
color_palette = c(type_palette, complex_palette)
color_palette = color_palette[!duplicated(names(color_palette))]

# Extract the labels present in the cropped raster extents
type_present = na.omit(unique(values(vegtype_crop, dataframe = TRUE))[[1]])
complex_present = na.omit(unique(values(vegcomplex_crop, dataframe = TRUE))[[1]])

# Combine the unique labels from both cropped rasters and sort alphabetically
type_labels = sort(unique(c(type_present, complex_present)))

#### BUILD INDIVIDUAL MAP PANELS
####____________________________________________________

# Dynamically find the band index numbers for a CIR false color visualization
r_band = match('b04_nir', names(imagery_crop))
g_band = match('b03_red', names(imagery_crop))
b_band = match('b02_green', names(imagery_crop))

# Create imagery map panel (bottom left)
imagery_plot = ggplot() +
  # Add imagery raster as CIR false color
  geom_spatraster_rgb(
    data = imagery_crop, 
    r = r_band, 
    g = g_band, 
    b = b_band, 
    max_col_value = 220,
    stretch = 'lin'
  ) +
  # Add coastal zone overlay
  geom_sf(data = coast_data, color = 'black', fill = NA, linewidth = 0.8) +
  # Add installation boundary overlay
  geom_sf(data = installation_data, color = 'yellow', fill = NA, linewidth = 0.8) +
  # Adjust the plot to the horizontal and vertical installation bounds
  coord_sf(
    crs = st_crs(3338),
    xlim = x_limits,
    ylim = y_limits,
    expand = FALSE
  ) +
  # Add plot title
  ggtitle('c. High-resolution (0.5 m) CIR imagery') +
  # Add label with semi-transparent background
  annotate('label', 
           x = x_limits[1] + 20,
           y = y_limits[1] + 20, 
           label = 'Imagery © 2020 Maxar Technologies Inc.', 
           hjust = 0, vjust = 0, 
           size = 6, 
           color = 'black', 
           fill = alpha('white', 0.7),
           label.size = 0) +
  # Add plot styling
  theme_minimal() +
  theme(plot.margin = margin(2,2,2,2),
        axis.title = element_blank(),
        axis.text = element_blank(),
        axis.ticks = element_blank(),
        panel.grid.major = element_line(colour = 'gray'),
        plot.title = element_text(size = font_size)
  )

# Create vegetation type map panel (top left)
vegtype_plot = ggplot() +
  # Add vegetation type raster
  geom_spatraster(data = vegtype_crop) +
  scale_fill_manual(values = color_palette,               
                    breaks = type_labels,           
                    na.translate = FALSE, 
                    name = 'Vegetation Class') +
  # Add coastal zone overlay
  geom_sf(data = coast_data, color = 'black', fill = NA, linewidth = 0.8) +
  # Add installation boundary overlay
  geom_sf(data = installation_data, color = 'yellow', fill = NA, linewidth = 0.8) +
  # Adjust the plot to the horizontal and vertical installation bounds
  coord_sf(
    crs = st_crs(3338),
    xlim = x_limits,
    ylim = y_limits,
    expand = FALSE
  ) +
  # Add plot title
  ggtitle('a. Vegetation Types (1:2,500 scale)') +
  # Add plot styling
  guides(fill = guide_legend(byrow = TRUE)) +       
  theme_minimal() +
  theme(plot.margin = margin(2,2,2,2), 
        axis.title = element_blank(),
        axis.text = element_blank(),
        axis.ticks = element_blank(),
        panel.grid.major = element_line(colour = 'gray'),
        plot.title = element_text(size = font_size)
  )

# Create vegetation type-complex map panel (top right)
vegcomplex_plot = ggplot() +
  # Add vegetation complex raster
  geom_spatraster(data = vegcomplex_crop) +
  scale_fill_manual(values = color_palette,               
                    breaks = type_labels,           
                    na.translate = FALSE, 
                    name = 'Vegetation Class') +
  # Add coastal zone overlay
  geom_sf(data = coast_data, color = 'black', fill = NA, linewidth = 0.8) +
  # Add installation boundary overlay
  geom_sf(data = installation_data, color = 'yellow', fill = NA, linewidth = 0.8) +
  # Adjust the plot to the horizontal and vertical installation bounds
  coord_sf(
    crs = st_crs(3338),
    xlim = x_limits,
    ylim = y_limits,
    expand = FALSE
  ) +
  # Add plot title
  ggtitle('b. Vegetation Types-Complexes (1:10,000 scale)') +
  # Add plot styling
  guides(fill = guide_legend(byrow = TRUE)) +       
  theme_minimal() +
  theme(plot.margin = margin(2,2,2,2), 
        axis.title = element_blank(),
        axis.text = element_blank(),
        axis.ticks = element_blank(),
        panel.grid.major = element_line(colour = 'gray'),
        plot.title = element_text(size = font_size)
  )

#### CONSTRUCT MULTI-PANEL LEGEND
####____________________________________________________

# Remove legends from individual plots
vegtype_plot = vegtype_plot + theme(legend.position = 'none')
vegcomplex_plot = vegcomplex_plot + theme(legend.position = 'none')

# Alphabetize legend items
alphabetical_labels = sort(as.character(type_labels))

# Create a data frame of sorted legend items
legend_data = data.frame(
  class = factor(alphabetical_labels, levels = alphabetical_labels)
)

# Build the legend plot
legend_plot = ggplot() +
  geom_rect(data = legend_data, 
            aes(xmin = x_limits[1], xmax = x_limits[1], 
                ymin = y_limits[1], ymax = y_limits[1], 
                fill = class), 
            alpha = 0) +
  scale_fill_manual(values = color_palette,               
                    breaks = alphabetical_labels, # Assign legend order
                    drop = FALSE,                 # Ensures no items are dropped
                    name = NULL) +                # Suppress the normal legend title
  coord_sf(
    crs = st_crs(3338),
    xlim = x_limits,
    ylim = y_limits,
    expand = FALSE,
    clip = "off"
  ) +
  ggtitle('Vegetation Types and Complexes') + 
  guides(fill = guide_legend(ncol = 1, byrow = TRUE, title = NULL, override.aes = list(alpha = 1))) +
  theme_minimal() +
  theme(plot.margin = margin(2,2,2,2), 
        axis.title = element_blank(),
        axis.text = element_blank(),
        axis.ticks = element_blank(),
        panel.grid = element_blank(),
        panel.border = element_blank(),
        plot.title = element_text(size = font_size),
        legend.position = c(0, 1),
        legend.justification = c(0, 1),
        legend.text = element_text(size = font_size - 2),
        legend.spacing.y = unit(2, 'pt'),
        legend.key.height = unit(1.1, 'cm'),
        legend.key.width = unit(1.1, 'cm'),
        legend.background = element_blank(),
        legend.box.background = element_blank()
  )

#### MERGE AND EXPORT PLOTS
####____________________________________________________

# Create the top row (vegetation maps)
row1 = plot_grid(vegtype_plot, vegcomplex_plot, ncol = 2, align = 'hv')

# Create middle row (imagery and legend)
row2 = plot_grid(imagery_plot, legend_plot, ncol = 2, align = 'hv')

# Combine the rows vertically and append a NULL row at the bottom 
combine_plot = plot_grid(row1, row2, NULL, 
                         ncol = 1, 
                         rel_heights = c(1, 1, 1))

# Export plot
ggsave(figure_output,
       plot = combine_plot,
       device = 'jpeg',
       path = NULL,
       scale = 2,
       width = 6.5,     
       height = 10,     
       units = 'in',
       dpi = 600,
       limitsize = TRUE)