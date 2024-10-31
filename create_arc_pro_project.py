import arcpy
import os
import shutil

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

