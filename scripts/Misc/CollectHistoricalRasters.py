# --------------------------------------------------------------------------------
# Name:        Collect Historical Rasters
# Purpose:     This tool pulls selected historical rasters into map.
#
# License:     GNU Affero General Public License v3.
#              Full license in LICENSE file, or at <https://www.gnu.org/licenses/>
# --------------------------------------------------------------------------------

import arcpy

from ..helpers import license, reload_module
from ..helpers import print_messages as log
from ..helpers import setup_environment as setup

class CollectRasters:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Collect historical imagery rasters"
        self.description = ""
        self.category = "Misc"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define the tool parameters."""
        param0 = arcpy.Parameter(
            displayName="Analysis Area",
            name="analysis_area",
            datatype="GPExtent",
            parameterType="Required",
            direction="Input")
        param0.controlCLSID = '{15F0D1C1-F783-49BC-8D16-619B8E92F668}'

        params = [param0]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return license(['OSWCD_GIS'])

    @reload_module(__name__)
    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Setup
        log("setting up project")
        project, orig_map = setup()

        # reading in parameters
        extent = parameters[0].value

        # find key layers
        lyrs = orig_map.listLayers("*Key")

        for lyr in lyrs:
            if lyr.visible:
                # get year from key feature class
                year = lyr.name.replace(" Key", "")
                log("Grabbing rasters for ", year)

                with arcpy.da.SearchCursor(lyr, ("FULLPATH","IMAGENAME"), spatial_filter=extent) as cursor:
                    for row in cursor:
                        # get raster filepath from attributes
                        path = "{}\{}".format(row[0], row[1])
                        # make a nice name
                        lyr_name = row[1].split(".")[0] + " " + year
                        # prevent adding existing maps
                        existing = orig_map.listLayers(lyr_name)
                        if len(existing) == 0:
                            # make raster layer from path
                            new_lyr = arcpy.management.MakeRasterLayer(path, path.split('\\')[-1])
                            new_lyr = new_lyr.getOutput(0)
                            # add raster to group
                            grp_lyr = orig_map.listLayers("In Use Map Layers")[0]
                            new_lyr = orig_map.addLayerToGroup(grp_lyr, new_lyr)[0]
                            # rename raster
                            new_lyr.name = lyr_name
                            new_lyr.visible = False
                            # collapse each added layer
                            new_lyr_cim = new_lyr.getDefinition('V3')
                            new_lyr_cim.expanded = False
                            new_lyr.setDefinition(new_lyr_cim)

        return
