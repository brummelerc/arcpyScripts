 # -*- coding: utf-8 -*-

import arcpy
import os
import shutil

class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Create ArcGIS Pro Project"
        self.alias = "create"

        # List of tool classes associated with this toolbox
        self.tools = [CreateArcProProject]


class CreateArcProProject:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Create ArcGIS Pro Project"
        self.description = ""

    def getParameterInfo(self):
        """Define the tool parameters."""
        params = [
            arcpy.Parameter(displayName = "Project Name",
                            name = "project_name",
                            datatype = "GPString",
                            direction = "Input"),
            arcpy.Parameter(displayName = "Where to put the Project Directory",
                            name = "directory",
                            datatype = "DEFolder",
                            direction = "Input")
        ]

        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""

        import create_arc_pro_project

        create_arc_pro_project.execute(parameters[0].valueAsText, parameters[1].valueAsText)

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
