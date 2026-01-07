import arcpy
import os

class Toolbox(object):
    def __init__(self):
        self.label = "Route Analysis Toolbox"
        self.description = "Calculates statistics when a route crosses an environmental layer"
        self.tools = [RouteLength_AnalysisTool, ParallelRouteLength_AnalysisTool, RouteCrossings_AnalysisTool, RouteBufferArea_AnalysisTool]

class RouteLength_AnalysisTool(object):
     def __init__(self):
          self.label = "Route Length within Environmental Layer"
          self.description = "Calculates the length of the input routes within another layer"
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
            displayName="Dissolve Field (Route)",
            name="dissolve_field",
            datatype="Field",
            parameterType="Required",
            direction="Input"
        )
          dissolve_field.parameterDependencies = ["input_routes"]
          dissolve_field.filter.list = ["String"]
          params.append(dissolve_field)

          input_polygon_layer = arcpy.Parameter(
            displayName="Input Polygon Layer",
            name="input_polygon_layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input"
        )
          params.append(input_polygon_layer)

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
            direction="Input"
        )
          length_unit.filter.type = "ValueList"
          length_unit.filter.list = ["US SURVEY MILES", "KILOMETERS", "METERS", "FEET"]
          length_unit.defaultValue = "US SURVEY MILES"
          params.append(length_unit)

          return params

     def execute(self, parameters, messages):
        input_routes = parameters[0].valueAsText
        dissolve_field = parameters[1].valueAsText
        input_polygon_layer = parameters[2].valueAsText
        output_dissolve = parameters[3].valueAsText
        coordinate_system = parameters[4].value
        length_unit = parameters[5].valueAsText

        # Use user-specified coordinate system, or fall back on input_routes
        if coordinate_system is None:
            spatial_ref = arcpy.Describe(input_routes).spatialReference
        else:
            spatial_ref = coordinate_system

        projected_routes = arcpy.management.Project(
            input_routes,
            "in_memory\\projected_routes",
            spatial_ref
        )[0]

        projected_polygons = arcpy.management.Project(
            input_polygon_layer,
            "in_memory\\projected_polygons",
            spatial_ref
        )[0]

        # Intersect routes with polygons (output will be lines within polygons)
        workspace, base_name = os.path.split(output_dissolve)
        base_name_no_ext = os.path.splitext(base_name)[0]
        output_intersect = os.path.join("in_memory", f"{base_name_no_ext}_intersect")
        messages.addMessage("Intersecting routes with polygons...")
        arcpy.analysis.Intersect(
            in_features=[[projected_routes, ""], [projected_polygons, ""]],
            out_feature_class=output_intersect,
            join_attributes="ALL",
            cluster_tolerance=None,
            output_type="LINE"
        )
        intersect_count = int(arcpy.management.GetCount(output_intersect)[0])
        messages.addMessage(f"Intersect output feature count: {intersect_count}")

        # Add and calculate length field
        messages.addMessage("Adding and calculating length field...")
        arcpy.management.AddField(
            output_intersect,
            "Intersect_Length",
            "DOUBLE"
        )
        arcpy.management.CalculateGeometryAttributes(
            output_intersect,
            [["Intersect_Length", "LENGTH"]],
            length_unit=length_unit,
            area_unit="",
            coordinate_system=spatial_ref
        )

        # Dissolve by polygon field, summing the length
        messages.addMessage(f"Dissolving by field '{dissolve_field}' and summarizing length...")
        arcpy.analysis.PairwiseDissolve(
            in_features=output_intersect,
            out_feature_class=output_dissolve,
            dissolve_field=dissolve_field,
            statistics_fields=[["Intersect_Length", "SUM"]]
        )
        dissolve_count = int(arcpy.management.GetCount(output_dissolve)[0])
        messages.addMessage(f"Output dissolved feature count: {dissolve_count}")
        messages.addMessage("Analysis complete. Output includes summed route length within each polygon group.")

## Tool for calculating the total length of a route over an underlying environmental resource. Good for calculating
## the total distance the route moves over the resource.
class ParallelRouteLength_AnalysisTool(object):
    def __init__(self):
        self.label = "Parallel Route Length Analysis Tool"
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
            dissolve_field.filter.list = ["String", "Integer", "Double", "Single"]
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

            buffer_dissolve = arcpy.Parameter(
                 displayName = "Dissolve Buffers",
                 name = "buffer_dissolve",
                 datatype = "GPString",
                 parameterType = "Optional",
                 direction = "Input"
            )
            buffer_dissolve.filter.type = "ValueList"
            buffer_dissolve.filter.list = ["ALL", "NONE"]
            buffer_dissolve.defaultValue = "ALL"
            params.append(buffer_dissolve)

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
        dissolve_option = parameters[8].value if len(parameters) > 8 and parameters[8].value else "NONE"

        #Use user-specified coordinate system, or fall back on input_routes
        if coordinate_system is None:
              spatial_ref = arcpy.Describe(input_routes).spatialReference
        else:
              spatial_ref = coordinate_system

        projected_routes = arcpy.management.Project(
             input_routes,
             "in_memory\\projected_routes",
             spatial_ref
        )[0]

        projected_env = arcpy.management.Project(
             env_layer,
             "in_memory\\projected_env",
             spatial_ref
        )[0]

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
                   in_features = projected_routes,
                   out_feature_class = buffered_routes,
                   buffer_distance_or_field = buffer_dist_str,
                   line_side = "FULL",
                   line_end_type = "ROUND",
                   dissolve_option = dissolve_option
              )
              buffer_count = int(arcpy.management.GetCount(buffered_routes)[0])
              messages.addMessage(f"Buffered features count: {buffer_count}")
              intersect_input = buffered_routes
        else:
              intersect_input = projected_routes
        
        #Create intermediate outpute in same location with '_intersect' suffix
        workspace, base_name = os.path.split(output_dissolve)
        base_name_no_ext = os.path.splitext(base_name)[0]
        output_intersect = os.path.join(workspace, f"{base_name_no_ext}_intersect")

        messages.addMessage("Running pairwise intersection...")
        arcpy.analysis.Intersect(
            [intersect_input, projected_env],
            output_intersect,
            join_attributes = "ALL"
        )
        intersect_count = int(arcpy.management.GetCount(output_intersect)[0])
        messages.addMessage(f"Intersect output feature count: {intersect_count}")
        
        fields = [f.name for f in arcpy.ListFields(output_intersect)]
        messages.addMessage(f"Fields in intersect output: {fields}")

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

            buffer_dissolve = arcpy.Parameter(
                 displayName = "Dissolve Buffers",
                 name = "buffer_dissolve",
                 datatype = "GPString",
                 parameterType = "Optional",
                 direction = "Input"
            )
            buffer_dissolve.filter.type = "ValueList"
            buffer_dissolve.filter.list = ["ALL", "NONE"]
            buffer_dissolve.defaultValue = "ALL"
            params.append(buffer_dissolve)
            
            return params
    
    def execute(self, parameters, messages):
        #parameters
        input_routes = parameters[0].valueAsText
        dissolve_field = parameters[1].valueAsText
        env_layer = parameters[2].valueAsText
        output_dissolve = parameters[3].valueAsText
        coordinate_system = parameters[4].value
        buffer_distance = parameters[5].value
        buffer_units = parameters[6].value
        dissolve_option = parameters[7].value if len(parameters) > 7 and parameters[7].value else "NONE"
        
        #Use user-specified coordinate system, or fall back on input_routes
        if coordinate_system is None:
            spatial_ref = arcpy.Describe(input_routes).spatialReference
        else:
            spatial_ref = coordinate_system

        #Project both layers to the specified coordinate system
        projected_routes = arcpy.management.Project(
             input_routes,
             "in_memory\\projected_routes",
             spatial_ref
        )[0]

        projected_env = arcpy.management.Project(
             env_layer,
             "in_memory\\projected_env",
             spatial_ref
        )[0]

        #Buffer the input_route
        if buffer_distance is not None and buffer_distance > 0:
             workspace, base_name = os.path.split(output_dissolve)
             base_name_no_ext = os.path.splitext(base_name)[0]
             buffered_routes = os.path.join("in_memory", f"{base_name_no_ext}_buffered_routes")
             if buffer_units:
                  buffer_dist_str = f"{buffer_distance} {buffer_units.lower()}"
             else:
                  buffer_dist_str = str(buffer_distance)
             arcpy.analysis.Buffer(
                  in_features = projected_routes,
                  out_feature_class = buffered_routes,
                  buffer_distance_or_field = buffer_dist_str,
                  line_side = "FULL",
                  line_end_type = "ROUND",
                  dissolve_option = dissolve_option
             )
             intersect_input = buffered_routes
        else:
             intersect_input = projected_routes

        #Create intermediate outpute in same location with '_intersect' suffix
        workspace, base_name = os.path.split(output_dissolve)
        base_name_no_ext = os.path.splitext(base_name)[0]
        output_spatialjoin = os.path.join(os.path.split(output_dissolve)[0], f"{os.path.splitext(os.path.split(output_dissolve)[1])[0]}_spatialjoin")

        messages.addMessage("Running spatial join...")
        arcpy.analysis.SpatialJoin(
             target_features = intersect_input,
             join_features = projected_env,
             out_feature_class = output_spatialjoin,
             join_type = "KEEP_ALL",
             match_option = "INTERSECT"
        )

        messages.addMessage("Analysis complete.")

class RouteBufferArea_AnalysisTool(object):
     def __init__(self):
          self.label = "Route Buffer Area Analysis Tool"
          self.description = "Buffers a route and calculates the area in acres of intersecting layers"
          self.canRunInBackground = False

     def getParameterInfo(self):
          params = []

          input_routes = arcpy.Parameter(
               displayName = "Input Routes",
               name = "input_routes",
               datatype = "GPFeatureLayer",
               parameterType = "Required",
               direction = "Input"
          )
          params.append(input_routes)

          dissolve_field = arcpy.Parameter(
               displayName = "Dissolve Field",
               name = "dissolve_field",
               datatype = "Field",
               parameterType = "Required",
               direction = "Input"
          )
          dissolve_field.parameterDependencies = ["input_routes"]
          dissolve_field.filter.list = ["String"]
          params.append(dissolve_field)

          input_env_layer = arcpy.Parameter(
               displayName = "Input Environmental Layer",
               name = "input_env_layer",
               datatype = "GPFeatureLayer",
               parameterType = "Required",
               direction = "Input"
          )
          params.append(input_env_layer)

          output_intersect = arcpy.Parameter(
               displayName = "Output Intersect Feature Class",
               name = "output_intersect",
               datatype = "DEFeatureClass",
               parameterType = "Required",
               direction = "Output"
          )
          params.append(output_intersect)

          coordinate_system = arcpy.Parameter(
               displayName = "Coordinate System (for calculation)",
               name = "coordinate_system",
               datatype = "GPCoordinateSystem",
               parameterType = "Optional",
               direction = "Input"
          )
          params.append(coordinate_system)

          buffer_distance = arcpy.Parameter(
               displayName = "Buffer Distance",
               name = "buffer_distance",
               datatype = "Double",
               parameterType = "Required",
               direction = "Input"
          )
          params.append(buffer_distance)

          buffer_units = arcpy.Parameter(
               displayName = "Buffer Units",
               name = "buffer_units",
               datatype = "GPString",
               parameterType = "Required",
               direction = "Input"
          )
          buffer_units.filter.type = "ValueList"
          buffer_units.filter.list = ["Feet", "Meters", "Kilometers", "Miles"]
          buffer_units.defaultValue = "Feet"
          params.append(buffer_units)

          buffer_dissolve = arcpy.Parameter(
               displayName = "Dissolve Buffers",
               name = "buffer_dissolve",
               datatype = "GPString",
               parameterType = "Optional",
               direction = "Input"
          )
          buffer_dissolve.filter.type = "ValueList"
          buffer_dissolve.filter.list = ["ALL", "NONE"]
          buffer_dissolve.defualtValue = "NONE"
          params.append(buffer_dissolve)

          return params
     
     def execute(self, parameters, messages):
          input_routes = parameters[0].valueAsText
          dissolve_field = parameters[1].valueAsText
          input_env_layer = parameters[2].valueAsText
          output_intersect = parameters[3].valueAsText
          coordinate_system = parameters[4].value
          buffer_distance = parameters[5].value
          buffer_units = parameters[6].value
          dissolve_option = parameters[7].value if len(parameters) > 7 and parameters[7].value else "ALL"


          #use specified coordinate system or fall back on input routes
          if coordinate_system is None:
               spatial_ref = arcpy.Describe(input_routes).spatialReference
          else:
               spatial_ref = coordinate_system
          
          projected_routes = arcpy.management.Project(
               input_routes,
               "in_memory\\projected_routes",
               spatial_ref
          )[0]

          projected_polygons = arcpy.management.Project(
               input_env_layer,
               "in_memory\\projected_polygons",
               spatial_ref
          )[0]

          #buffer the routes
          workspace, base_name = os.path.split(output_intersect)
          base_name_no_ext = os.path.splitext(base_name)[0]
          buffered_routes = os.path.join("in_memory", f"{base_name_no_ext}_buffered_routes")
          if buffer_units:
               buffer_dist_str = f"{buffer_distance} {buffer_units.lower()}"
          else:
               buffer_dist_str = str(buffer_distance)
          messages.addMessage(f"Buffering input routes by {buffer_dist_str}...")
          arcpy.analysis.Buffer(
               in_features = projected_routes,
               out_feature_class = buffered_routes,
               buffer_distance_or_field = buffer_dist_str,
               line_side = "FULL",
               line_end_type = "ROUND",
               dissolve_option = dissolve_option
          )
          buffer_count = int(arcpy.management.GetCount(buffered_routes)[0])
          messages.addMessage(f"Buffered features count: {buffer_count}")

          #Intersect buffered routes with environmental layers
          messages.addMessage("Running intersection with environmental layers...")
          intersect_fc = os.path.join("in_memory", f"{base_name_no_ext}_intersect")
          arcpy.analysis.Intersect(
               in_features = [[buffered_routes, ""], [projected_polygons, ""]],
               out_feature_class = intersect_fc,
               join_attributes = "ALL",
               cluster_tolerance = None,
               output_type = "INPUT"
          )
          intersect_count = int(arcpy.management.GetCount(intersect_fc)[0])
          messages.addMessage(f"Intersect output feature count: {intersect_count}")

          #Add and calculate area in acres
          messages.addMessage("Adding and calculating area in acres...")
          arcpy.management.AddField(
               intersect_fc,
               "Intersect_Acres",
               "DOUBLE"
          )

          arcpy.management.CalculateGeometryAttributes(
               intersect_fc,
               [["Intersect_Acres", "AREA"]],
               area_unit = "ACRES",
               coordinate_system = spatial_ref
          )

          #Dissolve by field, summing the area
          messages.addMessage(f"Dissolving by field '{dissolve_field} and summarizing acres...")
          arcpy.analysis.PairwiseDissolve(
               in_features = intersect_fc,
               out_feature_class = output_intersect,
               dissolve_field = dissolve_field,
               statistics_fields = [["Intersect_Acres", "SUM"]]
          )
          dissolve_count = int(arcpy.management.GetCount(output_intersect)[0])
          messages.addMessage(f"Output dissolved feature count {dissolve_count}")

          messages.addMessage("Analysis complete.")

