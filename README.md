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
    - [Stream Centerline Adjuster](#1-stream-centerline-adjuster)
    - [Stream Elevation Profile](#2-stream-elevation-profile)
    - [Watershed Delineation](#3-watershed-delineation)
    - [Calculate Streamlines](#4-calculate-streamlines)
    - [Sub-Basin Delineation](#5-sub-basin-delineation)
    - [Runoff Curve Number (RCN)](#6-runoff-curve-number)
    - [EFH-2](#7-efh-2-calculation)
    - [Topographic Wetness Index (TWI)](#8-topographic-wetness-index-twi)
    - [Relative Elevation Model (REM)](#9-relative-elevation-model-rem)
  - [Planting tools](#buffer-tools)
    - [Point Plots](#1-point-plots)
    - [Shrub Clusters](#2-shrub-clusters)
  - [Agricultural assessment](#automated-agricultural-assessment)
  - [Linear Analysis](#linear-analysis)
    - [Local Minimums](#1-local-minimums)
  - [Analyze Area](#analyze-area)
    - [Contour Area](#1-contour-area)
    - [Slope Area](#2-slope-area)
  - [Miscelaneous](#miscelaneous)
  	- [Export Layouts](#export-layouts)
 	- [Historical Imagery](#historical-imagery)
 	- [Geocode Address](#geocode-address-tool)
- [Contributing](#contributing)
- [License](#license)

# Requirements
ArcGIS Pro v3.3 or greater with access to the following licenses:
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

<span>
<img src="./assets/readme_examples/berm_before_slope.png" alt="berm analysis before image showing the berm drawn on the map" height="220"/>
<img src="./assets/readme_examples/berm_after_slope.png" alt="berm analysis after image showing the backwatered area created by the berm" height="220"/>
<img src="./assets/readme_examples/berm_after_slope_built.png" alt="aerial imagery of the built berm with surface water similar to the analysis" height="220"/>
</span>

Example above shows a berm on a shallowly sloped hill, the GIS analysis of the backwatered area along with 1' depth contours, and aerials of the as-built conditions of the berm.

### 2. Dam Removal

Remove a dam from a DEM. Takes a ponded area and a proposed stream line through the area, calculates the estimated thalweg elevations through the ponded area and linearly interpolates the walls of the valley to the thalway to produce a DEM with the ponded area removed.

Eventually this tool should support other valley types such as U-shaped glaciated valleys and flat floodplain creation.

<span>
<img src="./assets/readme_examples/dam_removal_before.jpg" alt="dam removal before image showing a digital elevation model (DEM) of a pond and dam" width="300"/>
<img src="./assets/readme_examples/dam_removal_after.jpg" alt="dam removal after image showing the same DEM with the dam and pond removed and pre-dam elevations estimated using the tool" width="300"/>
</span>

Example above shows the tool removing a dam and pond from a digital elevation model (DEM) and estimating the elevations which existed before.

This tool can be used to estimate storage capacity of a dammed area using a DEM.

### 3. Model Potential Wetlands

This tool uses a DEM with a slope cutoff threshold, hydrologic soil group, land use data, and existing mapped wetlands (optional) to create a shapefile of potential wetland locations.

<span>
<img src="./assets/readme_examples/potential_wetlands_after.png" alt="picture showing output of model potential wetlands tool with areas along a stream highlited red to indicate potential wetland areas" height="250"/>
<img src="./assets/readme_examples/potential_wetlands_nwi.png" alt="picture showing national wetlands invenotry mapping of the same area in purple. There is considerable overlap between this and the previous photo" height="250"/>
</span>

Exmaple showing modeled potential wetlands (without existing wetland exclusion) in red on the left and mapped wetlands (NWI) in purple on the right.

## Hydrology

### 1. Stream Centerline Adjuster

Takes a streamline and optimizes each point along it's path to the lowest perpendicular point in a DEM within a search radius.

<span>
<img src="./assets/readme_examples/stream_centerline_after.png" alt="a picture showing aerial imagery of a stream with a red line indicating the before stream line and blue line indicating the after stream line more closely matching the layout of the stream" width="600"/>
</span>

Red line shows before blue line shows after

Note: this tool can perform poorly on highly sinuous streams and often picks up on side-channels lower than the main channel.

### 2. Stream Elevation Profile

TODO

### 3. Watershed Delineation

Takes a pour point and DEM and delineates the contributing watershed.

<span>
<img src="/assets/readme_examples/watershed_delineation_before_topo.png" alt="before image showing topographic map of study area and analysis pour point" height="250" />
<img src="/assets/readme_examples/watershed_delineation_after.png" alt="after image showing delineated watershed polygon over top of topographic map" height="250"/>
</span>

Before and after showing study area topographic map and the delineated watershed

### 4. Calculate Streamlines

In a given watershed use elevation data to find streamlines for flow accumulations larger than the stream initiation threshold

<span>
<img src="/assets/readme_examples/watershed_delineation_after.png" alt="before image showing delineated watershed polygon over top of topographic map" height="250"/>
<img src="/assets/readme_examples/calculate_streamlines_after.png" alt="after image showing watershed with delienated stream lines" height="250" />
</span>

### 5. Sub-Basin Delineation

Find sub-basins in a given watershed based off of a watershed flow-accumulation threshold.

<span>
<img src="/assets/readme_examples/sub_basin_before.png" alt="before image showing watershed on topographic map" height="250" />
<img src="/assets/readme_examples/sub_basin_after.png" alt="after image showing 4 sub-basins in the original watershed with streamlines" height="250"/>
</span>

Before and after showing the delineation of 4 sub-watersheds based off of the specified flow accumulation threshold.

### 6. Runoff Curve Number

Calculates the runoff curve numbers for a given area based off of land use and hydrologic soil group.

<span>
<img src="./assets/readme_examples/runoff_curve_numbers_after.png" alt="an example output from the runoff curve number tool showing a gradient of red-colored polygons where the darker features have higher runoff curve numbers" height="300"/>
</span>

The example above shows a sample output from this tool, where the darker colors represent a higher band of runoff curve numbers.

Note: in order to use this tool you must have land use / runoff curve number data. We recommend using [Chesapeake Bay Land Use Data](https://www.chesapeakeconservancy.org/projects/cbp-land-use-land-cover-data-project) and modifying the raster to include fields for runoff curve number values for each hydrologic soil groups A,B,C,D as shown:

<span>
<img src="./assets/readme_examples/runoff_curve_numbers_rcn_table.png" alt="a picture of a raster attribute table showing runoff curve number values for hydrologic soil groups A,B,C,D for " width="800"/>
</span>

### 7. EFH-2 Calculation

Perform EFH-2 runoff calculations for a given watershed using DEM and land-use data.

### 8. Topographic Wetness Index (TWI)

Calculates topographic wetness index (TWI) as a model of wetness due to topography and surface flow.

<span>
<img src="/assets/readme_examples/twi_before_aerial.png" alt="topographic wetness index before - showing aerial photograph of study area" height="250" max-width="180"/>
<img src="/assets/readme_examples/twi_before_hillshade.png" alt="topographic wetness index before - showing greyscale hillshade raster of study area" height="250" max-width="180"/>
</span>

Before images showing the study area from aerial and elevation hillshade

<span>
<img src="/assets/readme_examples/twi_after_low_res.png" alt="hi-res topographic wetness index after - showing output TWI raster with blue colors being higher TWI values and white colors being lower TWI values" height="250" max-width="180"/>
<img src="/assets/readme_examples/twi_after_hi_res.png" alt="hi-res topographic wetness index after - showing output TWI raster with blue colors being higher TWI values and white colors being lower TWI values" height="250" max-width="180"/>
</span>

After images showing output topographic wetness index (TWI) rasters for both low-res and hi-res elevation data. Blue colors represent higher (wetter) TWI values and white colors lower TWI values. You can clearly see drainage channels, as well as how topography impacts wetness.

<span>
<img src="/assets/readme_examples/twi_after_mapped_wetlands.png" alt="topographic wetness index after - output TWI raster overlaid with red hatched lines where wetlands have been mapped (DEC + NWI). There is significant overlap with the darkest TWI areas" height="350"/>
</span>

This shows a TWI output with mapped NWI and DEC wetlands. Notice the  significant overlap with the darkest TWI areas.

### 9. Relative Elevation Model (REM)

Create a relative elevation model (REM) or height above nearest drainage (HAND) model in a study area. This allows the user to see elevation normalized features above the stream elevation. This is useful for modeling streambank incision and indentifying geomorphic features.

<span>
<img src="./assets/readme_examples/rem_after.png" alt="a relative elevation model (REM) along a stream, showing high streambank incision through legacy sedient deposits behind a breached mill dam" width="300"/>
</span>

This example outputs show legacy sediment deposits behind a breached 19th century milldam, as shown by the higher relative streambank incision closest to the milldam.

## Buffer Tools

### 1. Point Plots

Uses Upper Susquehanna Coalition (USC) point plot monitoring methodology and creates the appropriate number of randomized plots for a given riparian forest buffer.

<span>
<img src="/assets/readme_examples/shrub_clusters_before.png" alt="image showing a planting area polygon in blue" height="250" />
<img src="/assets/readme_examples/point_plots_after.png" alt="image showing a planting area polygon in blue and random point plots distributed over it" height="250" />
</span>

This example shows a potential planting area and randomized point plots within it.

### 2. Shrub Clusters

Create shapefile of shrub clusters in a given planting area.

<span>
<img src="/assets/readme_examples/shrub_clusters_before.png" alt="image showing a planting area polygon in blue" height="250" />
<img src="/assets/readme_examples/shrub_clusters_after.png" alt="image showing a planting area polygon in blue and square shrub cluster polygons overtop of it" height="250" />
</span>

This example shows a potential planting area and shrub clusters at a specified size and density within it.

## Automated Agricultural Assessment
### 1. Delineate Parcels

Sets up ag assessment project folder and selects all relevant parcels for later analysis.

### 2a. Delineate Agland

After splitting each parcel up into its agricultural, non-agricultural, and forested land areas, use this tool to classify the selected features across all maps as agricultural land.

### 2b. Delineate NonAg

After splitting each parcel up into its agricultural, non-agricultural, and forested land areas, use this tool to classify the selected features across all maps as non-agricultural land.

### 2c. Delineate Forest

After splitting each parcel up into its agricultural, non-agricultural, and forested land areas, use this tool to classify the selected features across all maps as forest land.

### 3. Process

Calculate acreage and soil types across each land use and fill out the soil group worksheet.

### 4. Export Layouts

Export all relevant maps to PDF in the project folder.

## Analyze Area

Quality of life tools to improve some out of the box geoprocessing tools

### 1. Contour Area

Contour tool with ability to limit analysis to a given area

<span>
<img src="./assets/readme_examples/contour_before.png" alt="iamge showing aerial of farm field without contours" height="300"/>
<img src="./assets/readme_examples/contour_after.png" alt="after image showing same field with 1 foot contours in yellow lines" height="300"/>
</span>

Example showing a before and after of 1' contours in a sloping field.

### 2. Slope Area

Slope tool with ability to limit analysis to a given area

<span>
<img src="./assets/readme_examples/slope_before_aerial.png" alt="before image showing aerial of forest" height="300"/>
<img src="./assets/readme_examples/slope_after.png" alt="after image showing green-red slope raster of the same area" height="300"/>
</span>

Example showing before aerials and output slope raster.

## Linear Analysis

Tools to analyze linear features with respect to elevation.

### 1. Local Minimums

Find all of the local elevation minimums along a line. Uses a minimum elevation threshold to ignore small deviations in the underlying DEM data.

<span>
<img src="./assets/readme_examples/local_minimums_before.png" alt="before image showing 1 foot contours, aerial imagery and blue line" height="300"/>
<img src="./assets/readme_examples/local_minimums_after.png" alt="after image showing 1 foot contours, aerial imagery, blue line, and 3 local minimums along the line as blue dots" height="300"/>
</span>

Example showing a water line in a field and all of the local minimums along it. Lines represent 1' contours, and the local minimum threshold was 2".

## Miscelaneous

### Export Layouts

Quality of life tool to select which layouts to export and to where

### Historical Imagery

Only for in-house use since it depends on a very specific file structure and historical imagery raster structure

### Geocode address tool

TODO

Take NYS address and geocode it to point

# Contributing

Contributions welcome, please open issues for feature requests and bugs, and pull requests for code changes.

# License

Please refer to the [LICENSE](LICENSE) file.
