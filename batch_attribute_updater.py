import arcpy

#Path to target feature class
feature_class = r"PATH_TO_FEATURE_CLASS"

#Field names
name_field = "INDEX_FIELD"
type_field = "MODIFIED_FIELD"

#Target values
target_name = "INDEX_VALUE"
new_type_value = "NEW_VALUE"

#Start an update cursor to modify attribute table
with arcpy.da.UpdateCursor(feature_class, [name_field, type_field]) as cursor:
    for row in cursor:
        #Check if the name_field matches the target_name
        if row[0] == target_name:
            #update type_field to new_type_value
            row[1] = new_type_value
            cursor.updateRow(row)

print("Attribute update complete")