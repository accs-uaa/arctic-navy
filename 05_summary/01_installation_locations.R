# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Map installation locations
# Author: Timm Nawrocki, Alaska Center for Conservation Science
# Last Updated: 2026-04-25
# Usage: Must be executed in a R 4.4.3+ installation.
# Description: "Map installation locations" creates a map figure for publication that shows the locations of the three Arctic Naval Installations within northwest North America.
# ---------------------------------------------------------------------------

# Import required libraries
library(dplyr)
library(fs)
library(ggplot2)
library(ggrepel)
library(sf)
library(terra)
library(tidyterra)

#### SET UP DIRECTORIES, FILES, AND FIELDS
####____________________________________________________

# Set root directory
drive = 'C:'
root_folder = 'ACCS_Work'

# Define folder structure
project_folder = path(drive, root_folder, 'Projects/VegetationEcology/DoD_Navy_Arctic/Data')
base_folder = path(project_folder, 'Data_Input/basemap')
region_folder = path(project_folder, 'Data_Input/region_data')
output_folder = path(project_folder, 'Data_Output/summary_results')

# Define input files
ocean_input = path(base_folder, 'Basemap_Ocean_3338.shp')
russia_input = path(base_folder, 'Russia_Coastline_3571.shp')
na_input = path(base_folder, 'NorthAmerica_Coastline_4269.shp')
river_input = path(base_folder, 'NaturalEarth_10m_Rivers_Centerlines.shp')
region_input = path(region_folder, 'AlaskaYukon_Regions_v2.0_3338.shp')
icycape_input = path(region_folder, 'IcyCape_Installation_3338.shp')
barrow_input = path(region_folder, 'Barrow_Installation_Main_3338.shp')
mcintyre_input = path(region_folder, 'McIntyre_Installation_3338.shp')

# Define output files
figure_output = path(output_folder, '00_Installation_Locations.jpg')

#### CREATE MAP PLOT
####____________________________________________________

# Read shapes
ocean_data = st_read(ocean_input)
russia_data = st_read(russia_input) %>%
  st_transform(crs = 3338)
na_data = st_read(na_input) %>%
  st_transform(crs = 3338)
river_data = st_read(river_input) %>%
  st_transform(crs = 3338)
region_data = st_read(region_input)
icycape_data = st_read(icycape_input)
barrow_data = st_read(barrow_input)
mcintyre_data = st_read(mcintyre_input)

# Subset the arctic biome
arctic_data = region_data %>%
  filter(biome == 'Arctic')

# Calculate centroids and attach custom labels
icycape_centroid = st_point_on_surface(icycape_data) %>% mutate(label = 'Icy Cape')
barrow_centroid = st_point_on_surface(barrow_data) %>% mutate(label = 'Point Barrow')
mcintyre_centroid = st_point_on_surface(mcintyre_data) %>% mutate(label = 'Point McIntyre')

# Merge centroids into a single data frame
installation_centroids = bind_rows(icycape_centroid, barrow_centroid, mcintyre_centroid)

# Create a buffered bounding box for the map frame
region_bbox = st_bbox(region_data)
buffer_dist = 50000 
x_limits = c(region_bbox['xmin'] - buffer_dist, region_bbox['xmax'] + buffer_dist)
y_limits = c(region_bbox['ymin'] - buffer_dist, region_bbox['ymax'] + 200000)

# Create map of regions and installations
map_plot = ggplot() +
  # Add basemap data
  geom_sf(data = ocean_data, color = NA, fill = '#BEE8FF', alpha = 0.3) +
  geom_sf(data = russia_data, color = 'black', fill = 'white', linewidth = 0.2, alpha = 0.5) +
  geom_sf(data = na_data, color = 'black', fill = 'white', linewidth = 0.2, alpha = 0.5) +
  geom_sf(data = arctic_data, fill = '#ABC5AF', color = 'black', linewidth = 0.5, alpha = 0.5) +
  geom_sf(data = river_data, color = '#BFD9F2', linewidth = 1) +
  geom_sf(data = russia_data, color = 'white', fill = NA, linewidth = 1.2) +
  geom_sf(data = russia_data, color = 'black', fill = NA, linewidth = 0.2) +
  geom_sf(data = na_data, color = 'white', fill = NA, linewidth = 1.2) +
  geom_sf(data = na_data, color = 'black', fill = NA, linewidth = 0.2) +
  # Add the installation centroids and labels
  geom_sf(data = installation_centroids, color = 'black', size = 5) +
  geom_label_repel(
    data = installation_centroids,
    aes(geometry = geometry, label = label),
    stat = "sf_coordinates",
    segment.color = "black",
    min.segment.length = 0,
    seed = 6,
    size = 6,
    box.padding = 0.8,
    point.padding = unit(1, "cm"),
    nudge_y = 150000,
    nudge_x = -100000,
    fill = alpha('white', 0.5),
    label.size = NA
  ) +
  # Adjust the plot to the horizontal and vertical installation bounds
  coord_sf(
    crs = st_crs(3338),
    xlim = x_limits,
    ylim = y_limits,
    expand = FALSE
  ) +
  # Add x and y scale breaks
  scale_x_continuous(breaks = seq(-180, 180, by = 20)) +
  scale_y_continuous(breaks = seq(50, 70, by = 5)) +
  # Add plot styling
  theme_minimal() +
  theme(
    axis.title = element_blank(),
    axis.text = element_text(size = 16),
    panel.grid.major = element_line(colour = 'gray')
  )

# Export plot
ggsave(figure_output,
       plot = map_plot,
       device = 'jpeg',
       path = NULL,
       scale = 2,
       width = 6.5,
       height = 4,
       units = 'in',
       dpi = 600,
       limitsize = TRUE)