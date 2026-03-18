# Automated Agricultural Assessment / Soil Group Worksheet Instructions

## Installation / First Time Setup

- Verify you have ArcGIS Pro 3.3 or newer
- Verify you have the following GIS shapefiles:
  - Soils (download [here](https://websoilsurvey.nrcs.usda.gov/app/WebSoilSurvey.aspx) -> Download Soils Data -> Soils Survey Area (SSURGO) -> State + County)
    - If already downloaded, verify your shapefile has fields:
      - MUSYM: data is 3 letters like "AaA"
      - MUKEY: data is a 6 digit number
  - Parcels (get from your County)
    - Verify your parcel shapefile has fields:
      - Parcel ID (often called PRINT_KEY) - often looks like 1.00-1-14.00
      - SWIS Code - 6 digit number
      - Municipality
      - Address
      - Agricultural District - yes/no, number, ID etc
- Download <https://github.com/bcmertz/SWCD-Tools/archive/refs/heads/main.zip> and unzip to where you want the tool to live
- You may wish for your ag assessments to be generated in an [ArcGIS Pro template](https://pro.arcgis.com/en/pro-app/latest/help/projects/create-your-own-project-template.htm), however it is not necessary to run this tool
- You may also wish to adapt the soil group worksheet and soil map to represent your County. You can do so by:
  - Soil Map:
    - Create a new blank project
    - Import Layout File: \\SWCD Tools\\assets\\agassessment_layout.pagx
    - Make desired edits
      - Be careful to only edit County Specific information, otherwise you may break functionality
    - Save, then Share -> Layout File, and overwrite the old agassessment_layout.pagx file

## Opening the tool

Create a new blank project or a new project from your desired template

Add the SWCD Toolbox to the project

- Catalog pane -> Right click Toolboxes -> Add Toolbox -> Navigate and select the 'SWCD Tools.pyt' toolbox wherever you have it save

Open the toolbox by clicking on it or:

- Open the Geoprocessing pane.
- Select the Toolboxes tab.
- SWCD Tools -> Automated Ag Assessment

## Running the tool

- Obtain Initial Information from Landowner/Farmer:
  - Parcel Number(s)
  - Landowner Name
  - Landowner Mailing Address
- Delineate Parcels
  - Select all necessary layers and fields
    - The program tries to help, verify any automatically selected layers / fields are correct
  - Enter tax #s and landowner information
  - Specify output folder for Soil Group Worksheet and maps
    - Can be same or different from current ArcGIS project

<span>
<img src="/assets/readme_examples/ag_delineate.png" alt="Image showing aerial view of a black parcel line resulting from delineating a farm using parcel ID" height="350"/>
<img src="/assets/readme_examples/ag_delineate_split.png" alt="Image showing aerial view of a black parcel line resulting from delineating a farm using parcel ID split into its various land uses" height="350"/>
</span>

- Delineate Agland, NonAg, and Forest
  - On each parcel's map, select and split the parcel into it's various uses, then save
  - For each land use, select across all maps the split pieces that are that land use
  - Run the tool and proceed to the next land use or step

<span>
<img src="/assets/readme_examples/ag_agland.png" alt="Aerial view of a split up parcel with the agricultural areas outlined red" height="280"/>
<img src="/assets/readme_examples/ag_nonag.png" alt="Aerial view of a split up parcel with the non-agricultural areas outlined blue" height="280"/>
<img src="/assets/readme_examples/ag_forest.png" alt="Aerial view of a split up parcel with the forest areas outlined green" height="280"/>
</span>

- Process
  - Select the soils shapefile and fields if not already selected
  - Run the program
  - This step finds the soils, acreage, and fills out the SGW and map for each parcel and for each land use
- Export layouts
  - Prior to running make any desired changes to the created layouts
    - Usually, you have to manually add data to the tables:
      - Contents -> Right click table -> Add field "MUSYM" and "Acres"
  - Run once you are happy with the layout
  - This will open the folder containing the SGW and Maps
- Restart
  - If any errors are made use the Restart tool

## Questions / Issues
If you run into any issues feel free to open an issue on [Github](https://github.com/bcmertz/SWCD-Tools/issues), or contact the maintainer directly: [mertzr@otsegosoilandwater.com](mailto:mertzr@otsegosoilandwater.com), 607-547-8337 ext 4
