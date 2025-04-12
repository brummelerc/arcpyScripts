import arcpy

def REST_service_scraper(service_url, local_gdb_path, output_name):

    try:
        temp_layer = "TempLayer"
        arcpy.management.MakeFeatureLayer(Service_url, temp_layer)
        arcpy.conversion.FeatureClassToFeatureClass(temp_layer, local_gdb_path, output_name)
        full_output_path = f"{local_gdb_path}\\{output_name}"
        print(f"Feature class successfully copied to: {full_output_path}")
        return full_output_path
    except arcpy.ExectureError:
        print("ArcPy Error: ", arcpy.GetMessages(2))
    except Exception as e:
        print("General Error: ", e)