# Overview

This is a set of tools for various GIS workflows related to hydrology, wetlands, agricultural conservation, and DEM processing.

# Table of Contents

- [Overview](#overview)
- [Requirements](#requirements-)
- [Installation](#installation-)
- [Project Structure](#project-structure-)
- [Overview of tools](#overview-of-tools-)
  - [Wetland tools](#wetland-tools-)
    - [Berm Analysis](#1-berm-analysis-)
    - [Dam Removal](#2-dam-removal-)
    - [Model Potential Wetlands](#3-model-potential-wetlands-)
  - [Hydrology](#hydrology-)
    - [Stream Elevation Profile](#1-stream-elevation-profile-)
    - [Calculate Stream Network](#2-calculate-stream-network-)
    - [Watershed Delineation](#3-watershed-delineation-)
    - [Sub-Basin Delineation](#4-sub-basin-delineation-)
    - [Runoff Curve Number (RCN)](#5-runoff-curve-number-)
    - [EFH-2](#6-efh-2-calculation-)
    - [Topographic Wetness Index (TWI)](#7-topographic-wetness-index-twi-)
    - [Relative Elevation Model (REM)](#8-relative-elevation-model-rem-)
    - [Stream Power Index (SPI)](#9-stream-power-index-spi-)
    - [Stream Centerline Adjuster](#10-stream-centerline-adjuster-)
  - [Tile Drainage](#tile-drainage-)
    - [Decision Tree Classification](#1-decision-tree-classification-dtc-)
    - [Image Differencing - Setup](#2-image-differencing---setup-)
    - [Image Differencing](#3-image-differencing-)
    - [Image Differencing - Cloud and Shadow Removal](#4-image-differencing---cloud-and-shadow-removal-)
  - [Planting tools](#buffer-tools-)
    - [Point Plots](#1-point-plots-)
    - [Shrub Clusters](#2-shrub-clusters-)
    - [Riparian Forest Buffer Potential](#3-riparian-forest-buffer-potential-)
  - [Agricultural Assessment](#automated-agricultural-assessment-)
  - [Raster Tools](#raster-tools-)
    - [Contour Polygon](#1-contour-polygon-)
    - [Slope Polygon](#2-slope-polygon-)
    - [Burn Culverts in DEM](#3-burn-culverts-in-dem-)
  - [Linear Analysis](#linear-analysis-)
    - [Local Minimums](#1-local-minimums-)
  - [Miscellaneous](#miscellaneous-)
  	- [Export Layouts](#export-layouts-)
 	- [Historical Imagery](#historical-imagery-)
 	- [Geocode Address](#geocode-address-tool-)
- [Contributing](#contributing-)
- [License](#license-)

# Requirements [↑](#table-of-contents)
ArcGIS Pro v3.3 or greater with access to the following licenses:
- Spatial Analyst

If you're not sure, each tool will verify you have the proper licenses needed. Not all tools require advanced licenses.

# Installation [↑](#table-of-contents)

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

# Project Structure [↑](#table-of-contents)
```
SWCD-Tools/
├── assets/                  # various static assets for use by tools
│   ├── readme_examples/     # contains before and after images of tools for documentation
├── scripts/                 # folder containing all python scripts / tools
│   ├── AgAssessment/        # automated agricultural assessment tools
│   ├── RasterTools/         # raster geoprocessing tools
│   ├── BufferTools/         # tools for riparian forest buffer planning
│   ├── Hydrology/           # hydrology toolbox
│   ├── TileDrainage/        # tile drainage toolbox
│   ├── LineAnalysis/        # tools for analysis of lines in 3D
│   ├── Misc/                # misc quality of life tools
│   ├── Wetlands/            # wetland tools
│   └── helpers/             # helper tools for use by other tools
├── LICENSE                  # license
├── README.md                # readme
├── SWCD Tools.*.pyt.xml     # tool metadata including parameter descriptions
└── SWCD Tools.pyt           # main entry-point to project
```

# Overview of tools [↑](#table-of-contents)
## Wetland Tools [↑](#table-of-contents)
### 1. Berm Analysis [↑](#table-of-contents)

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

### 2. Dam Removal [↑](#table-of-contents)

Remove a dam from a DEM. Takes a ponded area and a proposed stream line through the area, calculates the estimated thalweg elevations through the ponded area and linearly interpolates the walls of the valley to the thalway to produce a DEM with the ponded area removed.

Eventually this tool should support other valley types such as U-shaped glaciated valleys and flat floodplain creation.

<span>
<img src="./assets/readme_examples/dam_removal_before.jpg" alt="dam removal before image showing a digital elevation model (DEM) of a pond and dam" width="300"/>
<img src="./assets/readme_examples/dam_removal_after.jpg" alt="dam removal after image showing the same DEM with the dam and pond removed and pre-dam elevations estimated using the tool" width="300"/>
</span>

Example above shows the tool removing a dam and pond from a digital elevation model (DEM) and estimating the elevations which existed before.

This tool can be used to estimate storage capacity of a dammed area using a DEM.

### 3. Model Potential Wetlands [↑](#table-of-contents)

This tool uses a DEM with a slope cutoff threshold, hydrologic soil group, land use data, topographic wetness index (optional), and existing mapped wetlands (optional) to create a shapefile of potential wetland locations.

<span>
<img src="./assets/readme_examples/potential_wetlands_after.png" alt="picture showing output of model potential wetlands tool with areas along a stream highlited red to indicate potential wetland areas" height="250"/>
<img src="./assets/readme_examples/potential_wetlands_nwi.png" alt="picture showing national wetlands invenotry mapping of the same area in purple. There is considerable overlap between this and the previous photo" height="250"/>
</span>

Exmaple showing modeled potential wetlands (without existing wetland exclusion) in red on the left and mapped wetlands (NWI) in purple on the right.

This tool uses the following procedure:
1. Find slopes <= user specified slope threshold
2. Find all user specified hydric soils
3. Extract all user-specified valid land uses
4. Intersect all of these layers
5. Optional: erase all user-specified mapped wetlands or floodlpains from analysis
6. Optional: find mean value of topographic wetness index (TWI) raster in each output polygon and discard those < the user-specified minimum topographic wetness index

This provides a reasonable approximation of wetland soils, hydrology, and valid land use. The output of this analysis can be intersected with known agricultural ditches or other wetland manipulating structures to find potential project areas. Consider using the [USGS Hyper-Resolution Hydrology Dataset](https://www.usgs.gov/data/chesapeake-bay-hyper-resolution-hydrography-database) for mapped ag and road ditches.

## Hydrology [↑](#table-of-contents)

### 1. Stream Elevation Profile [↑](#table-of-contents)

TODO

### 2. Calculate Stream Network [↑](#table-of-contents)

Use elevation data to find streamlines for flow accumulations larger than the stream initiation threshold. The output can be restricted to existing streamlines to effectively correct hydrologically correct the input streamlines to match the DEM. For creating hydro-conditioned DEMs, see [Burn Culverts in DEM](#3-burn-culverts-in-dem)

<span>
<img src="/assets/readme_examples/stream_network_before.png" alt="before image showing original less accurate streamlines in blue against a grey hillshade background" height="350"/>
<img src="/assets/readme_examples/stream_network_after.png" alt="after image showing original less accurate streamlines in blue and more accurate new streamlines in green against a grey hillshade background" height="350" />
</span>

Before and after showing input low-res streamlines in blue and high-res output streamlines in green. It is suggested to apply some form of smoothing on the output lines.

<span>
<img src="/assets/readme_examples/stream_network_after_close.png" alt="after image showing original less accurate streamlines in blue against a grey hillshade background and more accurate new streamlines in green against a grey hillshade background closer up than previous example" height="400"/>
</span>

Close-up showing (with post-processing smoothing - PAEK 10m) derived streamlines in green.

### 3. Watershed Delineation [↑](#table-of-contents)

Takes a pour point and DEM and delineates the contributing watershed.

<span>
<img src="/assets/readme_examples/watershed_delineation_before_topo.png" alt="before image showing topographic map of study area and analysis pour point" height="250" />
<img src="/assets/readme_examples/watershed_delineation_after.png" alt="after image showing delineated watershed polygon over top of topographic map" height="250"/>
</span>

Before and after showing study area topographic map and the delineated watershed

### 4. Sub-Basin Delineation [↑](#table-of-contents)

Find sub-basins in a given watershed based off of a watershed flow-accumulation threshold.

<span>
<img src="/assets/readme_examples/sub_basin_before.png" alt="before image showing watershed on topographic map" height="250" />
<img src="/assets/readme_examples/sub_basin_after.png" alt="after image showing 4 sub-basins in the original watershed with streamlines" height="250"/>
</span>

Before and after showing the delineation of 4 sub-watersheds based off of the specified flow accumulation threshold.

### 5. Runoff Curve Number [↑](#table-of-contents)

Calculates the runoff curve numbers for a given area based off of land use and hydrologic soil group.

<span>
<img src="./assets/readme_examples/runoff_curve_numbers_after.png" alt="an example output from the runoff curve number tool showing a gradient of red-colored polygons where the darker features have higher runoff curve numbers" height="300"/>
</span>

The example above shows a sample output from this tool, where the darker colors represent a higher band of runoff curve numbers.

Note: in order to use this tool you must have land use / runoff curve number data. We recommend using [Chesapeake Bay Land Use Data](https://www.chesapeakeconservancy.org/projects/cbp-land-use-land-cover-data-project) and modifying the raster to include fields for runoff curve number values for each hydrologic soil groups A,B,C,D as shown:

<span>
<img src="./assets/readme_examples/runoff_curve_numbers_rcn_table.png" alt="a picture of a raster attribute table showing runoff curve number values for hydrologic soil groups A,B,C,D for " width="800"/>
</span>

### 6. EFH-2 Calculation [↑](#table-of-contents)

Perform EFH-2 runoff calculations for a given watershed using DEM and land-use data.

### 7. Topographic Wetness Index (TWI) [↑](#table-of-contents)

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

### 8. Relative Elevation Model (REM) [↑](#table-of-contents)

Create a relative elevation model (REM) or height above nearest drainage (HAND) model in a study area. This allows the user to see elevation normalized features above the stream elevation. This is useful for modeling streambank incision and indentifying geomorphic features.

<span>
<img src="./assets/readme_examples/rem_after.png" alt="a relative elevation model (REM) along a stream, showing high streambank incision through legacy sedient deposits behind a breached mill dam" width="300"/>
</span>

This example outputs show legacy sediment deposits behind a breached 19th century milldam, as shown by the higher relative streambank incision closest to the milldam.

### 9. Stream Power Index (SPI) [↑](#table-of-contents)

Create a stream power index (SPI) raster from a DEM. Modeling SPI gives info on landscape position and erosive potential.

<span>
<img src="./assets/readme_examples/stream_power_after.png" alt="after image showing aerial imagery of forest with a green-red raster showing output stream power index" width="500"/>
</span>

This example outputs shows stream power along a small headwater stream in the forest.

### 10. Stream Centerline Adjuster [↑](#table-of-contents)

Takes a streamline and optimizes each point along it's path to the lowest perpendicular point in a DEM within a search radius.

<span>
<img src="./assets/readme_examples/stream_centerline_after.png" alt="a picture showing aerial imagery of a stream with a red line indicating the before stream line and blue line indicating the after stream line more closely matching the layout of the stream" width="600"/>
</span>

Red line shows before blue line shows after

Note: this tool can perform poorly on highly sinuous streams and often picks up on side-channels lower than the main channel.

## Tile Drainage [↑](#table-of-contents)

### 1. Decision Tree Classification (DTC) [↑](#table-of-contents)

This tool evaluates likely areas where drainage tile has been installed based off of land usage, slope, and soil drainage. The analysis follows the AgTile protocol developed by [Gökkaya et al 2017](https://doi.org/10.1016/j.ecoleng.2017.06.048).

<span>
<img src="/assets/readme_examples/agtile_after.png" alt="image showing red hatch filled polygon over ag fields representing likely drainage tile areas" height="250" />
<img src="/assets/readme_examples/agtile_method.png" alt="flow-chart showing the ag-tile methodology" height="250" />
</span>

This example shows an example of output tiled areas, and how the AgTile protocol works.

### 2. Image Differencing - Setup [↑](#table-of-contents)

This tool finds optimal rasters for Image Differencing analysis based off of historic precipitation data.

For detailed information on finding and downloading appropriate data sources for this analysis please see [Image Differencing Documentation](<./Image Differencing Data Sources.md>).

<span>
<img src="/assets/readme_examples/image_differencing_setup_dry.png" alt="image of SWIR raster in dry conditions" height="250" />
<img src="/assets/readme_examples/image_differencing_setup_wet.png" alt="image of SWIR raster in wet conditions" height="250" />
</span>

This example shows short-wave infrared radiation rasters from dry (left) and wet (right) conditions and the effect that soil moisture has on reflectance.

### 3. Image Differencing [↑](#table-of-contents)

Image Differencing uses short-wave infrared data (SWIR) from landast 8/9 satellites taken during wet and dry conditions, to visualize the effects of drainage tile on soil moisture. This procedure is based off of research by [Valayamkunnath et al, 2020](https://doi.org/10.1038/s41597-020-00596-x).

<span>
<img src="/assets/readme_examples/image_differencing_before.png" alt="image showing ag fields before processing, some are water stained" height="350" />
<img src="/assets/readme_examples/image_differencing_after.png" alt="image showing green hatch filled polygon over ag fields representing likely drainage tile areas" height="350" />
</span>

This example shows an example of output tiled areas.

### 4. Image Differencing - Cloud and Shadow Removal [↑](#table-of-contents)

This tool uses the optional output cloud and shadow mask from the `Image Differencing` step to remove obscured areas from the output potential drainage tile feature/

<span>
<img src="/assets/readme_examples/cloud_shadow_after.png" alt="image showing green hatched polygon representing potentially tiled fields and a cloud shaped polygon clipping it representing a cloud and it's shadow." height="250" />
</span>

This example shows the potential drainage area clipped to outside of a passing cloud and it's shadow.

## Buffer Tools [↑](#table-of-contents)

### 1. Point Plots [↑](#table-of-contents)

Uses Upper Susquehanna Coalition (USC) point plot monitoring methodology and creates the appropriate number of randomized plots for a given riparian forest buffer.

<span>
<img src="/assets/readme_examples/shrub_clusters_before.png" alt="image showing a planting area polygon in blue" height="250" />
<img src="/assets/readme_examples/point_plots_after.png" alt="image showing a planting area polygon in blue and random point plots distributed over it" height="250" />
</span>

This example shows a potential planting area and randomized point plots within it.

### 2. Shrub Clusters [↑](#table-of-contents)

Create shapefile of shrub clusters in a given planting area.

<span>
<img src="/assets/readme_examples/shrub_clusters_before.png" alt="image showing a planting area polygon in blue" height="250" />
<img src="/assets/readme_examples/shrub_clusters_after.png" alt="image showing a planting area polygon in blue and square shrub cluster polygons overtop of it" height="250" />
</span>

This example shows a potential planting area and shrub clusters at a specified size and density within it.

### 3. Riparian Forest Buffer Potential [↑](#table-of-contents)

Create shapefile of potential riparian forest buffer planting areas.

<span>
<img src="/assets/readme_examples/riparian_potential_before.png" alt="aerial image showing a large stream and surrounding area" width="380" />
<img src="/assets/readme_examples/riparian_potential_after.png" alt="aerial image showing a large stream and surrounding area with green hatched lines indicating potential riparian forest buffer potential planting areas." width="380" />
</span>

This example shows a stream and it's potential riparian forest buffer areas within 200' of stream

This tool uses the following procedure:
1. Clip streamlines to analysis area and create buffer around it
2. Clip land use raster to buffer area
3. Erase non-valid land use areas
4. [Optional] Exclude specified areas
5. Calculate acreage of planting areas
6. Exclude planting areas smaller than specified size

## Raster Tools [↑](#table-of-contents)

Quality of life tools to improve some out of the box geoprocessing tools

### 1. Contour Polygon [↑](#table-of-contents)

Contour tool with ability to limit analysis to inside a given polygon

<span>
<img src="./assets/readme_examples/contour_after.png" alt="after image showing a hillshade and a polygon with red 10' contour lines inside the polygon" height="400"/>
</span>

Example showing output 10' contours in polygon.

### 2. Slope Polygon [↑](#table-of-contents)

Slope tool with ability to limit analysis to inside a given polygon

<span>
<img src="./assets/readme_examples/slope_after.png" alt="after image showing a green-red slope raster inside a polygon" height="400"/>
</span>

Example showing output slope raster in polygon.

### 3. Burn Culverts in DEM [↑](#table-of-contents)

This tool takes a DEM and culvert points shapefile and burns the culverts into the DEM for proper flow direction and accumulation analysis.

<span>
<img src="./assets/readme_examples/culvert_dem_before.png" alt="before image green to red DEM raster with bridge obstructing river" height="250"/>
<img src="./assets/readme_examples/culvert_dem_after.png" alt="after image green to red DEM raster with bridge not obstructing river" height="250"/>
</span>

Example showing before and after DEM with culvert removal.

## Automated Agricultural Assessment [↑](#table-of-contents)

### Notes:
This tool tries to assume nothing about your layer files or folder structure. This means you have to specify layers and fields in those layers to use for processing. This means you need a soils layer with a MUSYM attribute, as well as a parcel layer with parcel ID, municipality, ag district, and a street name/no (123 Apple St) field. You are able to manually specify to the program the name of these fields.

Additionally, you may want to edit the default Soil Group Worksheet template to have your County name or other data.

### 1. Delineate Parcels [↑](#table-of-contents)

Sets up ag assessment project folder and selects all relevant parcels for later analysis.

Once the tool is done, you must manually split each land use (ag, nonag, forest) for each map before proceeding.

<span>
<img src="/assets/readme_examples/ag_delienate.png" alt="Image showing aerial view of a black parcel line resulting from delineating a farm using parcel ID" height="350"/>
<img src="/assets/readme_examples/ag_delineate_split.png" alt="Image showing aerial view of a black parcel line resulting from delineating a farm using parcel ID split into its various land uses" height="350"/>
</span>

Output of step one, and the same parcel after manually splitting and saving the three land uses - ag, nonag, and forest.

### 2a. Delineate Agland [↑](#table-of-contents)

After splitting each parcel up into its agricultural, non-agricultural, and forested land areas, use this tool to classify the selected features across all maps as agricultural land.

<span>
<img src="/assets/readme_examples/ag_agland.png" alt="Aerial view of a split up parcel with the agricultural areas outlined red" height="350"/>
</span>

Output of step 2a showing agricultural land delineated.

### 2b. Delineate NonAg [↑](#table-of-contents)

After splitting each parcel up into its agricultural, non-agricultural, and forested land areas, use this tool to classify the selected features across all maps as non-agricultural land.

<span>
<img src="/assets/readme_examples/ag_nonag.png" alt="Aerial view of a split up parcel with the non-agricultural areas outlined blue" height="350"/>
</span>

Output of step 2b showing non-agricultural land delineated.

### 2c. Delineate Forest [↑](#table-of-contents)

After splitting each parcel up into its agricultural, non-agricultural, and forested land areas, use this tool to classify the selected features across all maps as forest land.

<span>
<img src="/assets/readme_examples/ag_forest.png" alt="Aerial view of a split up parcel with the forest areas outlined green" height="350"/>
</span>

Output of step 2c showing forest land delineated.

### 3. Process [↑](#table-of-contents)

Calculate acreage and soil types across each land use and fill out the soil group worksheet.

Note: you must manually add `MUSYM` and `ACRES` to the tables via the contents pane.

<span>
<img src="/assets/readme_examples/ag_process.png" alt="Image of an ArcGIS Pro layout showing ag, nonag, and forest land uses, as well as tables of acres and soils of each" height="350"/>
</span>

Output of step 3 showing the final layout.

### 4. Export Layouts [↑](#table-of-contents)

Export all relevant maps to PDF in the project folder.

## Linear Analysis [↑](#table-of-contents)

Tools to analyze linear features with respect to elevation.

### 1. Local Minimums [↑](#table-of-contents)

Find all of the local elevation minimums along a line. Uses a minimum elevation threshold to ignore small deviations in the underlying DEM data.

<span>
<img src="./assets/readme_examples/local_minimums_before.png" alt="before image showing 1 foot contours, aerial imagery and blue line" height="300"/>
<img src="./assets/readme_examples/local_minimums_after.png" alt="after image showing 1 foot contours, aerial imagery, blue line, and 3 local minimums along the line as blue dots" height="300"/>
</span>

Example showing a water line in a field and all of the local minimums along it. Lines represent 1' contours, and the local minimum threshold was 2".

## Miscellaneous [↑](#table-of-contents)

### Export Layouts [↑](#table-of-contents)

Quality of life tool to select which layouts to export and to where

### Historical Imagery [↑](#table-of-contents)

Only for in-house use since it depends on a very specific file structure and historical imagery raster structure

### Geocode address tool [↑](#table-of-contents)

Uses [NY GIS Address Geocoder](https://gis.ny.gov/address-geocoder) to take an address and return a point on the map.

# Contributing [↑](#table-of-contents)

Contributions welcome, please open issues for feature requests and bugs, and pull requests for code changes. This project uses the [Gentoo LLM policy](https://wiki.gentoo.org/wiki/Project:Council/AI_policy) and kindly asks contributors to refrain from submitting LLM generated code.

# License [↑](#table-of-contents)

Please refer to the [LICENSE](LICENSE) file.
