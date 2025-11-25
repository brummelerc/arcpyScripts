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
                name = "hydric_csv",
                datatype = "DEFile",
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
        import geopandas as gpd
        import pandas as pd
        import arcpy
        import os

        input_features = parameters[0].valueAsText.split(";")
        hydric_csv = parameters[1].valueAsText
        output_gdb = parameters[2].valueAsText

        hydric_df = pd.read_csv(hydric_csv)

        for feat in input_features:
            # Get a valid base name for the shapefile
            base_name = os.path.splitext(os.path.basename(feat))[0]
            # Remove any invalid characters for shapefile names
            base_name = base_name.replace('.', '_')[:8]  # Shapefile base name max 8 chars

            # Always export to temp shapefile
            temp_shp = os.path.join(arcpy.env.scratchFolder, f"{base_name}_temp.shp")
            arcpy.FeatureClassToFeatureClass_conversion(feat, arcpy.env.scratchFolder, f"{base_name}_temp")
            shp_path = temp_shp
            
            gdf = gpd.read_file(shp_path)
            gdf['MUKEY'] = gdf['MUKEY'].astype(str).str.strip()
            hydric_df['mukey'] = hydric_df['mukey'].astype(str).str.strip()
            joined = gdf.merge(hydric_df, left_on="MUKEY", right_on="mukey", how="left")
            print(joined['mukey'].notna().sum())
            matched = joined.dropna(subset=["Hydric_Rating"])
            out_temp_shp = os.path.join(arcpy.env.scratchFolder, f"{base_name}_hydricsoils.shp")
            matched.to_file(out_temp_shp)
            out_fc = f"{base_name}_hydricsoils"
            arcpy.FeatureClassToFeatureClass_conversion(out_temp_shp, output_gdb, out_fc)
            arcpy.AddMessage(f"Output: {output_gdb}\\{out_fc}")