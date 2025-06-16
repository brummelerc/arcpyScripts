import arcpy
import os

class Toolbox(object):
    def __init__(self):
        self.label = "Route Analysis Toolbox"
        self.description = "Calculates statistics when a route crosses an environmental layer"
        self.tools = [RouteLength_AnalysisTool, RouteCrossings_AnalysisTool]

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
            return params
    
    def execute(self, parameters, messages):
         #parameters
         input_routes = parameters[0].valueAsText
         dissolve_field = parameters[1].valueAsText
         env_layer = parameters[2].valueAsText
         output_dissolve = parameters[3].valueAsText
         coordinate_system = parameters[4].value
         length_unit = parameters[5].valueAsText

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
              output_intersect
         )
         
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