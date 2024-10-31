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
        param0 = arcpy.Parameter(
            displayName = "Project Name",
            name = "project_name",
            datatype = "GPString",
            direction = "Input",
        )

        param1 = arcpy.Parameter(
            displayName = "Where to put the Project Directory",
            name = "directory",
            datatype = "DEFolder",
            direction = "Input",
        )

        return [param0, param1]

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

        project_name = arcpy.GetParameterAsText(0)
        directory = arcpy.GetParameterAsText(1)


        def create_project_with_folders(project_name, directory):
            
            #define the destination folder path for the new project
            target_folder = os.path.join(directory, project_name)

            #location of sample folder
            sample_folder = "T:/3-TEMPLATES/7-FOLDER_TEMPLATE_CLIENT_NAME_NO_SPACES/123456_FOLDER_TEMPLATE_PROJECT_NAME"

            #copy the sample folder structure to the target location
            project_folder = shutil.copytree(sample_folder, target_folder)
            print(f"Sample folder copied to: {target_folder}")

            #rename the geodatabase and toolbox within the target folder
            for root, dirs, files in os.walk(target_folder):
                #rename the geodatabase if found
                for folder in dirs:
                    if folder.endswith(".gdb"):
                        gdb_path = os.path.join(root, folder)
                        new_gdb_path = os.path.join(root, f"{project_name}.gdb")
                        os.rename(gdb_path, new_gdb_path)
                        print(f"Geodatabase renamed to: {new_gdb_path}")

            #rename the toolbox if found
            for file in files:
                if file.endswith(".tbx"):
                    tbx_path = os.path.join(root, file)
                    new_tbx_path = os.path.join(root, f"{project_name}.tbx")
                    os.rename(tbx_path, new_tbx_path)
                    print(f"Toolbox renamed to: {new_tbx_path}")

            #define the path for the new .aprx file in a specific subfolder within the copied structure
            aprx_folder = os.path.join(project_folder, "2-APRX")
            os.makedirs(aprx_folder, exist_ok = True)

            #define the full path of the new project
            aprx_path = os.path.join(aprx_folder, project_name + ".aprx")

            #create the ArcGIS Pro project
            arcpy.mp.CreateProject(aprx_path)
            print(f"Project '{project_name}' created at {aprx_path}")

            return aprx_path
        
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
