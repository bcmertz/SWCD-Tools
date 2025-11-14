Work in Progress

# Overview

This is a set of tools for various GIS workflows related to hydrology, wetlands, agricultural conservation, and DEM processing.

# Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Overview of tools](#overview-of-tools)
  - [Wetland tools](#wetland-tools)
    - [Berm Analysis](#1-berm-analysis)
    - [Dam Removal](#2-dam-removal)
    - [Model Potential Wetlands](#3-model-potential-wetlands)
  - [Hydrology](#hydrology)
    - [Calculate Streamlines](#1-calculate-streamlines)
    - [EFH-2](#2-efh-2-calculation)
    - [Relative Elevation Model (REM)](#3-relative-elevation-model-rem)
    - [Runoff Curve Number (RCN)](#4-runoff-curve-number)
    - [Stream Centerline Adjuster](#5-stream-centerline-adjuster)
    - [Stream Elevation Profile](#6-stream-elevation-profile)
    - [Sub-Basin Delineation](#7-sub-basin-delineation)
    - [Topographic Wetness Index (TWI)](#8-topographic-wetness-index-twi)
    - [Watershed Delineation](#9-watershed-delineation)
  - [Planting tools](#buffer-tools)
    - [Point Plots](#1-point-plots)
    - [Shrub Clusters](#2-shrub-clusters)
  - [Agricultural assessment](#automated-agricultural-assessment)
  - [Linear Analysis](#linear-analysis)
    - [Local Minimums](#1-local-minimums)
  - [Analyze Area](#analyze-area)
    - [Contour Area](#1-contour-area)
    - [Shrub Clusters](#2-shrub-clusters)
  - [Export Layouts](#export-layouts)
  - [Historical Imagery](#historical-imagery)
- [Contributing](#contributing)
- [License](#license)

# Requirements
ArcGIS Pro v3.3 or greater with access to the following licenses:
- 3D Analyst
- Spatial Analyst

# Installation

1. Download repository
	- [Option 1] Using git - Note: this has the benefit of allowing you to pull updates easily any time but is more complicated for non-developers
     	1. Clone repo locally: `git clone https://github.com/bcmertz/SWCD-Tools.git`
	- [Option 2] Download zip - Note: this is the simplest way to get access to these tools
     	1. Download zip file
			- enter this link in your browser to download the zip (https://github.com/bcmertz/SWCD-Tools/archive/refs/heads/main.zip)
			- unzip the folder into a folder where you want it to live
2. Add toolbox to ArcGIS Pro
    - ArcGIS Pro: Catalog -> Toolboxes -> Add Toolbox
    	- select `SWCD Tools.pyt` from cloned repository

# Overview of tools
## Wetland Tools
### 1. Berm Analysis

Analyze the backwater effects of a proposed berm. Optionally: calculate the lowest effective height of the berm, create contours of ponded area

<span>
<img src="./assets/readme_examples/berm_analysis_before.png" alt="berm analysis before image showing the berm drawn representing a ditch plug" height="300"/>
<img src="./assets/readme_examples/berm_analysis_after.png" alt="berm analysis after image showing the backwatered area created by the ditch plug" height="300"/>
</span>

Example above shows a ditch plug backwatering a substantial area of a field

### 2. Dam Removal

Remove a dam from a DEM. Takes a ponded area and a proposed stream line through the area, calculates the estimated thalweg elevations through the ponded area and linearly interpolates the walls of the valley to the thalway to produce a DEM with the ponded area removed.

Eventually this tool should support other valley types such as U-shaped glaciated valleys and flat floodplain creation.

<span>
<img src="./assets/readme_examples/dam_removal_before.jpg" alt="dam removal before image showing a digital elevation model (DEM) of a pond and dam" height="300"/>
<img src="./assets/readme_examples/dam_removal_after.jpg" alt="dam removal after image showing the same DEM with the dam and pond removed and pre-dam elevations estimated using the tool" height="300"/>
</span>

Example above shows the tool removing a dam and pond from a digital elevation model (DEM) and estimating the elevations which existed before.

This tool can be used to estimate storage capacity of a dammed area using a DEM.

### 3. Model Potential Wetlands

This tool uses a DEM with a slope cutoff threshold, hydrologic soil group, land use data, and existing mapped wetlands (optional) to create a shapefile of potential wetland locations.

## Hydrology

### 1. Calculate Streamlines

In a given watershed use elevation data to find streamlines for flow accumulations larger than the stream initiation threshold

### 2. EFH-2 Calculation

Perform EFH-2 runoff calculations for a given watershed using DEM and land-use data.

### 3. Relative Elevation Model (REM)

Create a relative elevation model (REM) or height above nearest drainage (HAND) model in a study area. This allows the user to see elevation normalized features above the stream elevation. This is useful for modeling streambank incision and indentifying geomorphic features.

<span>
<img src="./assets/readme_examples/rem_after.png" alt="a relative elevation model (REM) along a stream, showing high streambank incision through legacy sedient deposits behind a breached mill dam" height="300"/>
</span>

This example outputs show legacy sediment deposits behind a breached 19th century milldam, as shown by the higher relative streambank incision closest to the milldam.

### 4. Runoff Curve Number

Calculates the runoff curve numbers for a given area based off of land use and hydrologic soil group.

<span>
<img src="./assets/readme_examples/runoff_curve_numbers_after.png" alt="an example output from the runoff curve number tool showing a gradient of red-colored polygons where the darker features have higher runoff curve numbers" height="300"/>
</span>

The example above shows a sample output from this tool, where the darker colors represent a higher band of runoff curve numbers.

### 5. Stream Centerline Adjuster

Takes a streamline and optimizes each point along it's path to the lowest perpendicular point in a DEM within a search radius.

### 6. Stream Elevation Profile

TODO

### 7. Sub-Basin Delineation

Find sub-basins in a given watershed based off of a watershed flow-accumulation threshold.

### 8. Topographic Wetness Index (TWI)

Calculates topographic wetness index (TWI) as a model of wetness due to topography and surface flow.

<span>
<img src="/assets/readme_examples/twi_before.png" alt="topographic wetness index before - showing aerial photograph of study area" height="300" max-width="250"/>
<img src="/assets/readme_examples/twi_after.png" alt="topographic wetness index before - showing output TWI raster with cyan colors being higher TWI values and blue colors being lower TWI values" height="300" max-width="250"/>
</span>

This example of a topographic wetness index (TWI) raster shows cyan colors being higher TWI values and light blue colors being lower TWI values. You can clearly see the stream channel, as well as how topography impacts wetness.

### 9. Watershed Delineation

Takes a pour point and DEM and delineates the contributing watershed.

## Buffer Tools

### 1. Point Plots

Uses Upper Susquehanna Coalition (USC) point plot monitoring methodology and creates the appropriate number of randomized plots for a given riparian forest buffer.

### 2. Shrub Clusters

Create shapefile of shrub clusters in a given planting area.

## Automated Agricultural Assessment
### 1. Delineate Parcels
### 2a. Delineate Agland
### 2b. Delineate NonAg
### 2c. Delineate Forest
### 3. Process
### 4. Export Layouts

## Linear Analysis

Tools to analyze linear features with respect to elevation.

### 1. Local Minimums

Find all of the local elevation minimums along a line. Uses a minimum elevation threshold to ignore small deviations in the underlying DEM data.

## Analyze Area

Quality of life tools to improve some out of the box geoprocessing tools

### 1. Contour Area

Contour tool with ability to limit analysis to a given area

### 2. Slope Area

Slope tool with ability to limit analysis to a given area

## Export Layouts

Quality of life tool to select which layouts to export and to where

## Historical Imagery

Only for in-house use since it depends on a very specific file structure and historical imagery raster structure

## Geocode address tool

TODO

Take NYS address and geocode it to point

# Contributing

Contributions welcome, please open issues for feature requests and bugs, and pull requests for code changes.

# License

Please refer to the [LICENSE](LICENSE) file.
