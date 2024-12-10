import arcpy
import math

#Parameters
input_gdb = r"PATH_TO_GEODATABASE"
feature_class = "NAME_OF_FEATURE_CLASS"
template_layout_name = 'Site Map Template'

#Reference the project and template layout
aprx = arcpy.mp.ArcGISProject("CURRENT")
template_layout = aprx.listLayouts(template_layout_name)[0] #get the template layout

#Get the map associated with the map frame
map_obj = map_frame.map

#Iterate through each site in the feature class
with arcpy.da.SearchCursor(f"{input_gdb}\\{feature_class}", ["OID@", "Feature_Ty", "SHAPE@"]) as cursor:
    for row in cursor:
        oid = row[0]
        site_name = row[1]
        site_geometry = row[2]
        
        #Create a copy of the layout
        new_layout_name = f"Site_{site_name}_6.5x8.25"
        new_layout = aprx.copyItem(template_layout, new_layout_name)
        
        #Get the map frame in the new layout
        new_map_frame = new_layout.listElements("MAPFRAME_ELEMENT")[0]
        
        #Zoom the map frame to the site
        new_map_frame.camera.setExtent(site_geometry.extent)
        
        #Adjust scale to the nearest 1000
        original_scale = new_map_frame.camera.scale
        rounded_scale = math.ceil(original_scale / 1000) * 1000
        new_map_frame.camera.scale = rounded_scale
        
        #Access the map frame and layer
        map_frame = new_layout.listElements("MAPFRAME_ELEMENT")[0]
        map_layer = map_frame.map.listLayers(feature_class)[0]

        #Rename the layer to match the site name (updates the legend)
        map_layer.name = site_name        
        
#Save the project to preserve the new layouts
aprx.save()