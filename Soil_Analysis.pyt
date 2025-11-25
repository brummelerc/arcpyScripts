class Toolbox(object):
    def __init__(self):
        self.label = "Soil Analysis Toolbox"
        self.description = "Combines and calculates datasets from the USDA Web Soil Survey"
        self.tools = [CombineDatasetsTool, JoinHydricSoilsTool]

class CombineDatasetsTool(object):
    def __init__(self):
        self.label = "Combine Spatial Soil Datasets"
        self.description = "Combine multiple spatial datasets"

    def getParameterInfo(self):
        params = [
            arcpy.Parameter(
                displayName = "Input Datasets",
                name = "input_files",
                datatype = "DEFeatureClass",
                parameterType = "Required",
                direction = "Input",
                multiValue = True
            ),
            arcpy.Parameter(
                displayName = "Output Geodatabase",
                name = "output_gdb",
                datatype = "DEWorkspace",
                parameterType = "Required",
                direction = "Input"
            ),
            arcpy.Parameter(
                displayName = "Output Feature Class Name",
                name = "output_fc",
                datatype = "GPString",
                parameterType = "Required",
                direction = "Input"
            )
        ]
        return params
    
    def execute (self, parameters, messages):
        import geopandas as gpd
        import pandas as pd
        import arcpy
        import os

        input_files = parameters[0].valueAsText.split(";")
        output_gdb = parameters[1].valueAsText
        output_fc = parameters[2].valueAsText

        gdfs = [gpd.read_file(f) for f in input_files]
        combined_gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)

        temp_shapefile = os.path.join(arcpy.env.scratchFolder, "combined_temp.shp")
        combined_gdf.to_file(temp_shapefile)

        arcpy.FeatureClassToFeatureClass_conversion(temp_shapefile, output_gdb, output_fc)
        arcpy.AddMessage(f"Combined feature class saved to {output_gdb}\\{output_fc}")

class JoinHydricSoilsTool(object):
    def __init__(self):
        self.label = "Join Hydric Soils Table"
        self.description = "Join Web Soil Survey CSV to shapefiles"

    def getParameterInfo(self):
        params = [
            arcpy.Parameter(
                displayName = "Input Features",
                name = "input_features",
                datatype = "DEFeatureClass",
                parameterType = "Required",
                direction = "Input",
                multiValue = True
            ),
            arcpy.Parameter(
                displayName = "Hydric Soils CSV",
                name = "hydric_table",
                datatype = "DETable",
                parameterType = "Required",
                direction = "Input"
            ),
            arcpy.Parameter(
                displayName = "Output Geodatabase",
                name = "output_gdb",
                datatype = "DEWorkspace",
                parameterType = "Required",
                direction = "Input"
            )
        ]
        return params
    
    def execute(self, parameters, messages):
        import arcpy
        import os

        input_features = parameters[0].valueAsText.split(";")
        hydric_table = parameters[1].valueAsText
        output_gdb = parameters[2].valueAsText

        for feat in input_features:
            arcpy.management.AddJoin(feat, "MUKEY", hydric_table, "MUKEY1")
            joined_field = None
            for f in arcpy.ListFields(feat):
                if "Hydric_Rating" in f.name:
                    joined_field = f.name
                    break
            if not joined_field:
                raise Exception("Hydric_Rating field not found after join.")
            sql_expression = f"{joined_field} = 'Yes'"
            out_fc_name = f"{os.path.splitext(os.path.basename(feat))[0]}_hydricsoils"
            out_fc_path = os.path.join(output_gdb, out_fc_name)
            arcpy.conversion.ExportFeatures(feat, out_fc_path, sql_expression)
            arcpy.management.RemoveJoin(feat)
            arcpy.AddMessage(f"Output: {out_fc_path}")