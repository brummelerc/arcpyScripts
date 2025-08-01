import arcpy
import os

#set up parameters
input_fc = r"Path_To_Input_Feature_Class"
output_folder = r"Path_To_Output_Folder"
output_spatial_ref = arcpy.SpatialReference(32159)

#name field to use for file names
name_field = "FldOrgNum"

#Iterate through the feature class
with arcpy.da.SearchCursor(input_fc, ["OID@", name_field] if name_field else ["OID@"]) as cursor:
    for row in cursor:
        oid = row[0]
        name = row[1] if name_field else f"feature_{oid}"
        safe_name = arcpy.ValidateTableName(name, output_folder)

        temp_layer_name = f"temp_layer_{oid}"

        # create a temporary feature layer for this feature only
        where_clause = f"OBJECTID = {oid}"
        arcpy.management.MakeFeatureLayer(input_fc, temp_layer_name, where_clause)

        # Path to the output shapefile (unprojected)
        temp_shp = os.path.join(output_folder, f"{safe_name}_unproj.shp")

        # Path to the final projected shapefile
        final_shp = os.path.join(output_folder, f"{safe_name}.shp")

        arcpy.management.CopyFeatures(temp_layer_name, temp_shp)
        arcpy.management.Project(temp_shp, final_shp, output_spatial_ref)

        for lyr in map_obj.listLayers():
            if lyr.name == temp_layer_name:
                map_obj.removeLayer(lyr)
        
        # Clean up temp shapefile
        arcpy.management.Delete(temp_layer_name)
        arcpy.management.Delete(temp_shp)

        print(f"Exported: {final_shp}")

print("Done.")