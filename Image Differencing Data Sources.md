Download NOAA historic rainfall data:

1.  Go to [NOAA Climate Data Online Search](https://www.ncdc.noaa.gov/cdo-web/search)
2.  Search for county level data over a long time (5 years recommended)
3.  Add County data to cart and go to cart
4.  Output format: Custom GHCN-Daily CSV
5.  Select custom output: Precipitation -&gt; PRCP
6.  Once complete, Download

Download [USGS Landsat 8/9 SWIR Data](https://www.usgs.gov/faqs/what-are-best-landsat-spectral-bands-use-my-research):
1.  Ensure you have Microsoft Edge installed (it’s the only browser I
    was able to get to work for this download, Chrome may also work but
    I couldn’t get it too. Unfortunately, Firefox is unsupported by USGS
    and won’t work). You also need [7-zip](https://www.7-zip.org/) installed.
2.  Go to [EarthExplorer](https://earthexplorer.usgs.gov/) and click
    Login in the top right to either login or create an account
3.  After logging in select the data you need in
    [EarthExplorer](https://earthexplorer.usgs.gov/) by doing the
    following:
    1.  Search Criteria:
        1.  Predefined Area -&gt; Add Shape
            1.  State: New York
            2.  Area Type: County
            3.  Area: &lt;County Nate&gt;
        2.  Date Range: I suggest setting the data range to be quite
            long to allow yourself to find adequate data (for example:
            01/01/2024 to 12/31/2025) but it’s up to you. Each imagery
            tile is about 1 GB of data so you may wish to download a
            smaller range of data and be careful about where you
            download to. The important thing is that there is data with
            little cloud cover of both dry and wet soil moisture
            conditions
        3.  Search months: Select the months where you expect no snow on
            the ground and no vegetation in crop fields (April/May works
            for Otsego, NY)
        4.  Cloud Cover: 0-5% or something similar (high cloud cover
            reduces the accuracy of the analysis)
    2.  Data Sets:
        1.  Select “Landsat -&gt; Landsat Collection 2 Level-2”
            1.  Overview of dataset
                [here](https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products)
    3.  Additional Criteria
        1.  Collection Category: Tier 1
    4.  Results
        1.  Show result controls
        2.  Add all results from current page to bulk order
        3.  Go through every page of results and add to bulk order
        4.  Once ready click View Item Basket
    5.  Bulk Download
        1.  Start order
        2.  Options -&gt; select all products
        3.  Bulk Download -&gt; Add name -&gt; Submit Product Selections
    6.  Use bulk downloader to download all rasters to output folder
4.  Extract all tar files using 7-zip
    1.  Check “Eliminate duplication of root folder”
