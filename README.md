# Notice: Work in Progress


# Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Overview of tools](#overview)
  - [Wetland tools](#wetlands)
  - [Hydrology](#hydrology)
  - [Planting tools](#planting)
  - [Agricultural assessment](#ag-assessment)


# Requirements[](#requirements)
ArcGIS Pro v3.3 or greater

# Installation[](#installation)

1. Download repository
	- [Option 1] Using git - Note: this has the benefit of allowing you to pull updates easily any time but is more complicated for non-developers
     	1. Clone repo locally: `git clone https://github.com/bcmertz/SWCD-Tools.git`
	- [Option 2] Download zip - Note: this is the simplest way to get access to these tools
     	1. Download zip file
			- enter this link in your browser to download the zip (https://github.com/bcmertz/SWCD-Tools/archive/refs/heads/main.zip)
			- unzip the folder into a folder where you want it to live
2. in ArcGIS Pro: Catalog -> Toolboxes -> Add Toolbox
	- select `SWCD Tools.pyt` from cloned repository

# Overview of tools (TODO)[](#overview)
## Wetland Tools[](#wetlands)
### 1. Berm Analysis
<span>
<img src="./assets/readme_examples/berm_analysis_before.png" alt="drawing" width="200"/>
<img src="./assets/readme_examples/berm_analysis_after.png" alt="drawing" width="200"/>
</span>

### 2. Dam Removal
<span>
<img src="./assets/readme_examples/dam_removal_before.jpg" alt="drawing" width="200"/>
<img src="./assets/readme_examples/dam_removal_after.jpg" alt="drawing" width="200"/>
</span>

### 3. Model Potential Wetlands
TODO
## Hydrology[](#hydrology)
### 1. Calculate Streamlines
### 2. EFH-2 Calculation
### 3. Relative Elevation Model (REM)
<span>
<img src="./assets/readme_examples/rem_after.png" alt="drawing" width="200"/>
</span>

### 4. Runoff Curve Number
Calculates the runoff curve numbers for a given area based off of land use and hydrologic soil group.

<span>
<img src="./assets/readme_examples/runoff_curve_numbers_after.png" alt="drawing" width="200"/>
</span>

### 5. Stream Centerline Adjuster
### 6. Stream Elevation Profile
### 7. Sub-Basin Delienation
### 8. Topographic Wetness Index (TWI)
<span>
<img src="/assets/readme_examples/twi_before.png" alt="drawing" width="200"/>
<img src="/assets/readme_examples/twi_after.png" alt="drawing" width="200"/>
</span>

### 9. Watershed Delineation
## Buffer Tools[](#planting)
### 1. Point Plots
### 2. Shrub Clusters
## Automated Agricultural Assessment[](#ag-assessment)
### 1. Delineate Parcels
### 2a. Delineate Agland
### 2b. Delineate NonAg
### 2c. Delineate Forest
### 3. Process
### 4. Export Layouts
## Linear Analysis
TODO
## Analyze Area
TODO
## Export Layouts
TODO
### Historical Imagery
TODO
