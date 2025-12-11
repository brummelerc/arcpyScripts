import arcpy
import os

class Toolbox(object):
    def __init__(self):
        self.label = "Route Analysis Toolbox"
        self.description = "Calculates statistics when a route crosses an environmental layer"
        self.tools = [RouteLength_AnalysisTool, RouteCrossings_AnalysisTool, BatchSpatialJoin]

## Tool for calculating the total length of a route over an underlying environmental resource. Good for calculating
## the total distance the route moves over the resource.
class RouteLength_AnalysisTool(object):
    def __init__(self):
        self.label = "Route Length Analysis Tool"
        self.description = "Calculates the total length a route intersects an environmental layer"
        self.canRunInBackground = False

    def getParameterInfo(self):
            params = []

            input_routes = arcpy.Parameter(
                      displayName="Input Routes",
                      name="input_routes",
                      datatype="GPFeatureLayer",
                      parameterType="Required",
                      direction="Input"
                )
            params.append(input_routes)
            
            dissolve_field = arcpy.Parameter(
                      displayName="Dissolve Field",
                      name="dissolve_field",
                      datatype="Field",
                      parameterType="Required",
                      direction="Input",                     
                )
            
            dissolve_field.parameterDependencies = ["input_routes"]
            dissolve_field.filter.list = ["String"]
            params.append(dissolve_field)
            
            input_env_layer = arcpy.Parameter(
                      displayName="Input Environmental Layer",
                      name="input_env_layer",
                      datatype="GPFeatureLayer",
                      parameterType="Required",
                      direction="Input"
                )
            params.append(input_env_layer)
                 
            output_dissolve = arcpy.Parameter(
                      displayName="Output Dissolved Feature Class",
                      name="output_dissolve",
                      datatype="DEFeatureClass",
                      parameterType="Required",
                      direction="Output"
                )
            params.append(output_dissolve)
            
            coordinate_system = arcpy.Parameter(
                      displayName="Coordinate System (for Length Calculation)",
                      name="coordinate_system",
                      datatype="GPCoordinateSystem",
                      parameterType="Optional",
                      direction="Input"
                )
            params.append(coordinate_system)
            
            length_unit = arcpy.Parameter(
                      displayName="Length Unit",
                      name="length_unit",
                      datatype="GPString",
                      parameterType="Required",
                      direction="Input",
                )
            length_unit.filter.type = "ValueList"
            length_unit.filter.list = ["US SURVEY MILES", "KILOMETERS", "METERS", "FEET"]
            length_unit.defaultValue = "US SURVEY MILES"
            params.append(length_unit)
            
            buffer_distance = arcpy.Parameter(
                 displayName = "Buffer Distance",
                 name = "buffer_distance",
                 datatype = "Double",
                 parameterType = "Optional",
                 direction = "Input"
            )
            buffer_distance.value = None
            params.append(buffer_distance)

            buffer_units = arcpy.Parameter(
                 displayName = "Buffer Units",
                 name = "buffer_units",
                 datatype = "GPString",
                 parameterType = "Optional",
                 direction = "Input"
            )
            buffer_units.filter.type = "ValueList"
            buffer_units.filter.list = ["Feet", "Meters", "Kilometers", "Miles"]
            buffer_units.defaultValue = "Feet"
            params.append(buffer_units)
            
            return params
    
    def execute(self, parameters, messages):
        #parameters
        input_routes = parameters[0].valueAsText
        dissolve_field = parameters[1].valueAsText
        env_layer = parameters[2].valueAsText
        output_dissolve = parameters[3].valueAsText
        coordinate_system = parameters[4].value
        length_unit = parameters[5].valueAsText
        buffer_distance = parameters[6].value
        buffer_units = parameters[7].value

        #Use user-specified coordinate system, or fall back on input_routes
        if coordinate_system is None:
              spatial_ref = arcpy.Describe(input_routes).spatialReference
        else:
              spatial_ref = coordinate_system

          #If buffer_distance is provided, buffer the input_routes first
        if buffer_distance is not None and buffer_distance > 0:
              workspace, base_name = os.path.split(output_dissolve)
              base_name_no_ext = os.path.splitext(base_name)[0]
              buffered_routes = os.path.join("in_memory", f"{base_name_no_ext}_buffered_routes")
              if buffer_units:
                   buffer_dist_str = f"{buffer_distance} {buffer_units.lower()}"
              else:
                   buffer_dist_str = str(buffer_distance)
              messages.addMessage(f"Buffering input routes by {buffer_distance} units...")
              arcpy.analysis.Buffer(
                   in_features = input_routes,
                   out_feature_class = buffered_routes,
                   buffer_distance_or_field = buffer_dist_str,
                   line_side = "FULL",
                   line_end_type = "ROUND",
                   dissolve_option = "ALL"
              )
              buffer_count = int(arcpy.management.GetCount(buffered_routes)[0])
              messages.addMessage(f"Buffered features count: {buffer_count}")
              intersect_input = buffered_routes
        else:
              intersect_input = input_routes
              buffer_count = int(arcpy.management.GetCount(buffered_routes)[0])
              messages.addMessage(f"Buffered features count: {buffer_count}")
        

        #Create intermediate outpute in same location with '_intersect' suffix
        workspace, base_name = os.path.split(output_dissolve)
        base_name_no_ext = os.path.splitext(base_name)[0]
        output_intersect = os.path.join(workspace, f"{base_name_no_ext}_intersect")

        messages.addMessage("Running pairwise intersection...")
        arcpy.analysis.PairwiseIntersect(
            [input_routes, env_layer],
            output_intersect
        )
        intersect_count = int(arcpy.management.GetCount(output_intersect)[0])
        messages.addMessage(f"Intersect output feature count: {intersect_count}")
        
        #Project the intersect output if a spatial reference was provided
        if spatial_ref:
            projected_intersect = os.path.join("in_memory", "projected_intersect")
            arcpy.management.Project(output_intersect, projected_intersect, spatial_ref)
            output_intersect = projected_intersect #update reference to use the projected one

        messages.addMessage("Adding and calculating length field...")
        arcpy.management.AddField(
            output_intersect,
            "Dissolve_length",
            "DOUBLE"
        )
        arcpy.management.CalculateGeometryAttributes(
            output_intersect,
            [["Dissolve_length", "LENGTH"]],
            length_unit=length_unit,
            area_unit="",
            coordinate_system=spatial_ref
        )

        messages.addMessage("Dissolving by route and summarizing lengths...")
        arcpy.analysis.PairwiseDissolve(
            in_features=output_intersect,
            out_feature_class=output_dissolve,
            dissolve_field=dissolve_field,
            statistics_fields=[['Dissolve_length', 'SUM']]
        )
        dissolve_count = int(arcpy.management.GetCount(output_dissolve)[0])
        messages.addMessage(f"Output dissolved feature count: {dissolve_count}")

        messages.addMessage("Analysis complete.")

class RouteCrossings_AnalysisTool(object):
    def __init__(self):
        self.label = "Route Crossings Analysis Tool"
        self.description = "Calculates the number of times a route intersects a linear environmental layer"
        self.canRunInBackground = False

    def getParameterInfo(self):
            params = []

            input_routes = arcpy.Parameter(
                      displayName="Input Routes",
                      name="input_routes",
                      datatype="GPFeatureLayer",
                      parameterType="Required",
                      direction="Input"
                )
            params.append(input_routes)
            
            dissolve_field = arcpy.Parameter(
                      displayName="Dissolve Field",
                      name="dissolve_field",
                      datatype="Field",
                      parameterType="Required",
                      direction="Input",                     
                )
            
            dissolve_field.parameterDependencies = ["input_routes"]
            dissolve_field.filter.list = ["String"]
            params.append(dissolve_field)
            
            input_env_layer = arcpy.Parameter(
                      displayName="Input Environmental Layer",
                      name="input_env_layer",
                      datatype="GPFeatureLayer",
                      parameterType="Required",
                      direction="Input"
                )
            params.append(input_env_layer)
                 
            output_dissolve = arcpy.Parameter(
                      displayName="Output Dissolved Feature Class",
                      name="output_dissolve",
                      datatype="DEFeatureClass",
                      parameterType="Required",
                      direction="Output"
                )
            params.append(output_dissolve)
            
            coordinate_system = arcpy.Parameter(
                      displayName="Coordinate System (for Length Calculation)",
                      name="coordinate_system",
                      datatype="GPCoordinateSystem",
                      parameterType="Optional",
                      direction="Input"
                )
            params.append(coordinate_system)
            
            return params
    
    def execute(self, parameters, messages):
        #parameters
        input_routes = parameters[0].valueAsText
        dissolve_field = parameters[1].valueAsText
        env_layer = parameters[2].valueAsText
        output_dissolve = parameters[3].valueAsText
        coordinate_system = parameters[4].value
        
        #Use user-specified coordinate system, or fall back on input_routes
        if coordinate_system is None:
            spatial_ref = arcpy.Describe(input_routes).spatialReference
        else:
            spatial_ref = coordinate_system

        #Create intermediate outpute in same location with '_intersect' suffix
        workspace, base_name = os.path.split(output_dissolve)
        base_name_no_ext = os.path.splitext(base_name)[0]
        output_intersect = os.path.join(workspace, f"{base_name_no_ext}_intersect")

        messages.addMessage("Running pairwise intersection...")
        arcpy.analysis.PairwiseIntersect(
            [input_routes, env_layer],
            output_intersect, 
            output_type='POINT'
        )
        
        #Project the intersect output if a spatial reference was provided
        if spatial_ref:
            projected_intersect = os.path.join("in_memory", "projected_intersect")
            arcpy.management.Project(output_intersect, projected_intersect, spatial_ref)
            output_intersect = projected_intersect #update reference to use the projected one

        messages.addMessage("Dissolving by route and counting crossings...")
        arcpy.analysis.PairwiseDissolve(
            in_features=output_intersect,
            out_feature_class=output_dissolve,
            dissolve_field=dissolve_field,
            statistics_fields=[['OBJECTID', 'COUNT']]
        )

        messages.addMessage("Analysis complete.")

class BatchSpatialJoin(object):
     def __init__(self):
          self.label = "Batch Spatial Join"
          self.description = "Spatially join multiple environmental layers to multiple target layers"

     def getParameterInfo(self):
          params = []

          p0 = arcpy.Parameter(
               displayName = "Target Layers",
               name = "target_layers",
               datatype = "GPFeatureLayer",
               parameterType = "Required",
               direction = "Input",
               multiValue = True
          )

          p1 = arcpy.Parameter(
               displayName = "Join Layers",
               name = "join_layers",
               datatype = "GPFeatureLayer",
               parameterType = "Required",
               direction = "Input",
               multiValue = True
          )

          p2 = arcpy.Parameter(
            displayName="Output Geodatabase",
            name="output_gdb",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
            )
          
          p3 = arcpy.Parameter(
            displayName="Join Type",
            name="join_type",
            datatype="GPString",
            parameterType="Optional",
            direction="Input")
          p3.value = "KEEP_ALL"

          p4 = arcpy.Parameter(
               displayName = "Match Option",
               name = "match_option",
               datatype = "GPString",
               parameterType = "Optional",
               direction = "Input"
          )
          p4.value = "INTERSECT"

          return[p0, p1, p2, p3, p4]
     def execute(self, parameters, messages):
          targets_input = parameters[0].valueAsText.split(";")
          joins_input = parameters[1].valueAsText.split(";")
          output_gdb = parameters[2].valueAsText
          join_type = parameters[3].valueAsText
          match_option = parameters[4].valueAsText

          aprx = arcpy.mp.ArcGISProject("CURRENT")
          m = aprx.activeMap

          def resolve_input(item):
               #try to find a layer in the map with this name
               lyr = next((lyr for lyr in m.listLayers()if lyr.name == item), None)
               return lyr if lyr is not None else item #layer object or path string
          
          def name_of(obj):
               return obj.name if hasattr(obj, "name") else os.path.splitext(os.path.basename(obj))[0]

          targets = [resolve_input(t) for t in targets_input]
          joins = [resolve_input(j) for j in joins_input]

          for target_lyr in targets:
               for join_lyr in joins:
                    out_name = f"{name_of(target_lyr)}_{name_of(join_lyr)}_SJ"
                    out_fc = os.path.join(output_gdb, arcpy.ValidateTableName(out_name, output_gdb))

                    arcpy.AddMessage(f"Running spatial join: {name_of(target_lyr)} + {name_of(join_lyr)} -> {out_name}")

                    arcpy.analysis.SpatialJoin(
                         target_features = target_lyr,
                         join_features = join_lyr,
                         out_feature_class = out_fc,
                         join_type = join_type,
                         match_option = match_option
                    )

          arcpy.AddMessage("All spatial joins completed successfully.")