# Long-term Monitoring for Arctic Naval Installations

[![Project Status: Active](https://img.shields.io/badge/Project%20Status-Active-brightgreen.svg)](#)
[![Python Version](https://img.shields.io/badge/Python-3.12+-blue.svg)](#)
[![R Version](https://img.shields.io/badge/R-4.5.2+-blue.svg)](#)

Remotely sensed monitoring indicators for U.S. Naval Installations in northern coastal Alaska

*Author*: Timm Nawrocki, Alaska Center for Conservation Science, University of Alaska Anchorage

*Created On*: 2026-01-03

*Last Updated*: 2026-05-15

*Description*: Scripts to develop remotely sensed indicators from the AKVEG Map and an SRLite imagery and segmentation pipeline

## About the Project
This repository contains the processing scripts, workflows, and spatial algorithms to develop the remotely sensed indicators supporting the *Long-term Monitoring Plan for Arctic Naval Installations* (Version 1.0, May 2026). The workflow in this repository relies on SRLite imagery and image segments developed through an imagery processing pipeline. The imagery processing pipeline is established through the [AKVEG Map project](https://github.com/orgs/akveg-map). The remotely sensed indicators monitor ecological and environmental change at three U.S. Naval Installations (Icy Cape, Point Barrow, and Point McIntyre) in northern coastal Alaska. The code in this repository facilitates a hybrid monitoring framework that integrates remotely sensed maps with field-measured indicators. Both types of indicators should be updated on regular intervals.

The methodologies in this repository align with [Federal Geographic Data Committee standard for vegetation](https://www.fgdc.gov/standards/projects/vegetation/index_html), the [U.S. National Vegetation Classification (USNVC)](https://usnvc.org/), and the [Alaska Geospatial Council](https://agc.dnr.alaska.gov/) Vegetation Working Group. Compatibility with these standards ensures interoperability with statewide mapping and monitoring efforts through the [AKVEG Map](https://akveg.org).

## Getting Started

These instructions will enable you to run scripts to update the remotely sensed indicators for Arctic Naval Installations. The scripts integrate multiple systems: Google Earth Engine, Python, and R. Some manually delineated data may need to be created or updated in GIS software (see *Long-term Monitoring Plan for Arctic Naval Installations*). Reproducing the results will require creating comparable processing environments; however, we suggest that all software and package be updated to the most recent available version. For information on the development of the AKVEG Map, see the [AKVEG Map project](https://github.com/orgs/akveg-map).

### Prerequisites

To execute the code successfully, you will need the following standard libraries and third-party geospatial libraries. This workflow requires a valid user account and project within Google Earth Engine. We recommend a setting up a Python geospatial processing environment in a [MiniForge installation](https://github.com/conda-forge/miniforge).

#### Python 3.12+

##### Standard Packages

* `os`
* `random`
* `json`
* `glob`
* `time`
* `collections`

##### Third-Party Data Science & Geospatial Packages (Latest stable versions):

* `numpy` (v2.0.0+) — *For foundational array and matrix manipulation.*
* `scipy` (v1.13.0+) — *Used specifically for spatial filtering and array dilation during site selection.*
* `pandas` (v2.2.0+) — *Used for tabular data manipulation and generating summary statistics.*
* `geopandas` (v1.0.0+) — *For vector data processing and coordinate reference system management.*
* `rasterio` (v1.3.10+) — *Used for raster manipulation, masking, and feature extraction.*
* `rio-cogeo` (v5.3.0+) — *For Cloud Optimized GeoTIFF (COG) creation and translation.*
* `shapely` (v2.0.4+) — *For geometric operations, defining spatial rules, and creating spatial objects.*
* `pyproj` (v3.6.0+) — *For cartographic projections and coordinate transformations.*
* `rasterstats` (v0.19.0+) — *For summarizing geospatial raster datasets based on vector geometries.*
* `dbf` (v0.99.0+) — *For reading and writing DBF files.*
* `plotly` (v5.20.0+) — *For interactive graphing and visualizations.*
* `kaleido` (v0.2.1+) — *For static image export of Plotly visualizations.*
* `earthengine-api` (v0.1.400+) — *For Google Earth Engine integration and remote sensing workflows.*
* `google-cloud-api` / `google-api-core` (v2.18.0+) — *For interacting with Google Cloud Storage and services.*
* `akutils` (v1.2.4) — *Utilities to simplify processing scripts.*

#### R 4.5.2+
* `sf` (v1.1-1) — *For reading, writing, and handling spatial vector features.*
* `terra` (v1.9-25) — *For efficient handling and processing of spatial raster layers.*
* `tidyterra` (v1.1.0) — *For tidyverse integration and plotting of terra raster objects.*
* `dplyr` (v1.2.1) — *For attribute data manipulation and piping workflows.*
* `ggplot2` (v4.0.3) — *For advanced map composition and plotting.*
* `ggpubr` (v0.6.3) — *For creating publication-ready plot arrangements.*
* `cowplot` (v1.2.0) — *For arranging multiple plots and maps into a single grid.*
* `ggspatial` (v1.1.10) — *For spatial data visualization annotations (e.g., scale bars, north arrows).*
* `fs` (v2.1.0) — *For robust, cross-platform file system operations.*

## Usage

This repository houses the code necessary to recreate the remotely sensed indicators and sample designs outlined in the monitoring plan. Folders and scripts are numbered to indicate the order of operations necessary to successful execution of the workflow. Key programmatic workflows include:

### 1. VHR Imagery Processing Pipeline
These scripts are necessary to the remote sensing workflow but are maintained in a [separate repository](https://github.com/orgs/akveg-map). These scripts correct, calibrate, and prepare raw Very-High-Resolution (VHR) spaceborne acquisitions to create SRLite 4-band images. 
* **Top-of-Atmosphere & Orthorectification:** Corrects pixel geometry using the 2020 Alaska IFSAR Digital Surface Model and standardizes raw values based on sun angle.
* **OmniCloudMask:** Applies deep-learning algorithms to detect and remove clouds and shadows.
* **Pansharpening & SRLite Harmonization:** Uses additive detail injection to generate 0.5-meter multispectral data, followed by calibration to Landsat surface reflectance reference using Continuous Change Detection and Classification (CCDC) harmonic models to ensure spectral consistency across different sensors and years.
* **Segmentation:** Implements Simple Non-Iterative Clustering (SNIC) to group VHR pixels into contiguous segments representing fine-scale spatial units of similar vegetation or earth surface characteristics.

### 2. Vegetation Type Mapping
A suite of mapping scripts to perform "transfer learning" from the native 10-meter resolution of the AKVEG map to the monitoring resolution at the Naval Installations. We combine the transfer learning with a map of surficial features to yield maps of vegetation types at two scales, which are suitable for monitoring and site selection stratification. These scripts run in Google Earth Engine and a local Python environment while map figures are generated in R.
* **Transfer Learning:** Transfers foliar cover and surface water map data from the 10-meter AKVEG Map resolution to the 0.5-meter SRLite imagery bands in Google Earth Engine to produce localized 1:2,500 scale intermediate maps.
* **Surficial Features:** Develops maps of surficial features based on manually selected training sample points.
* **Parse Existing Vegetation Types:** Programmatic key to parse the spatial distributions of existing vegetation types from the combination of diagnostic species indicators, surface water proportions, and surficial features.
* **Vegetation Map Post-processing:** Post-processes existing vegetation type map results to re-scale the 0.5-meter results to 2-meter image segments and enforce minimum mapping units.
* **Create Summaries:** Create summary plots and figures visualizing patterns in the geospatial data for each Arctic Naval Installation.

### 3. Monitoring Site Generation
Python scripts implementing a constrained, spatially balanced stratified random sampling design for long-term monitoring field sites. These scripts evaluate input vegetation strata against programmatic rules that enforce topological independence.
## Credits
If you use this repository, the algorithms, or the associated sampling designs in your work, please cite the *Long-term Monitoring Plan for Arctic Naval Installations*:

> Nawrocki, T.W., M.J. Macander, A.F. Wells, R.T. Choi, L.A. Flagstad, A.R. Glover, D. Wexler, G.V. Frost, and S. Thielke. 2026. *Long-term Monitoring Plan for Arctic Naval Installations. Version 1.0*. Alaska Center for Conservation Science, University of Alaska Anchorage. Anchorage, Alaska. 32 pp.

### Acknowledgements

Funding support to complete this work was provided by the U.S. Department of the Navy through the U.S. Fish and Wildlife Service (grant number F25AC01084). We thank Christina Coppenrath and Mathew Hamilton (USN Naval Facilities Energy Systems Command Northwest) for acting as technical points of contact, and Blaine Spellman (Natural Resources Conservation Service) for assistance developing the coastal map class schema.

### License

This project is provided under the GNU General Public License v3.0. It is free to use and modify in part or in whole.
