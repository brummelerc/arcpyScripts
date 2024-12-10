import arcpy
import math

# Parameters
input_gdb = r"PATH_TO_GEODATABASE"
feature_class = "NAME_OF_FEATURE_CLASS"
template_layout_name = 'Site Map Template'

# Reference the project and template layout
aprx = arcpy.mp.ArcGISProject("CURRENT")
template_layout = aprx.listLayouts(template_layout_name)[0]  # Get the template layout

# Get the map associated with the template layout's map frame
template_map_frame = template_layout.listElements("MAPFRAME_ELEMENT", "Layers Map Frame")[0]
template_map = template_map_frame.map  # Get the map associated with the map frame

# Iterate through each site in the feature class
with arcpy.da.SearchCursor(f"{input_gdb}\\{feature_class}", ["OID@", "Feature_Ty", "SHAPE@"]) as cursor:
    for row in cursor:
        oid = row[0]
        site_name = row[1]
        site_geometry = row[2]
        
        # Clone the template map
        cloned_map_name = f"Map_{site_name}"
        cloned_map = aprx.copyItem(template_map, cloned_map_name)
        
        # Create a copy of the layout
        new_layout_name = f"Site_{site_name}_6.5x8.25"
        new_layout = aprx.copyItem(template_layout, new_layout_name)
        
        # Get the map frame in the new layout and set it to use the cloned map
        map_frame = new_layout.listElements("MAPFRAME_ELEMENT", "Layers Map Frame")[0]
        map_frame.map = cloned_map  # Point the map frame to the cloned map
        
        # Zoom the map frame to the site
        map_frame.camera.setExtent(site_geometry.extent)  # Corrected to use map_frame
        
        # Adjust scale to the nearest 1000
        original_scale = map_frame.camera.scale
        rounded_scale = math.ceil(original_scale / 1000) * 1000
        map_frame.camera.scale = rounded_scale
        
        print(f"Processed site: {site_name}")

# Save the project to preserve the new layouts
aprx.save()