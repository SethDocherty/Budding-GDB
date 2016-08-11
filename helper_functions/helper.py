import arcpy
import os
from os.path import split, join
from datetime import datetime
arcpy.env.overwritearcpy.env.overwriteOutput = True

#..............................................................................................................................
# Creator - Seth Docherty
#
#   Helper functions for the Budding GDB toolset.  Make sure this script is called
#   to import all functions.
#   
#..............................................................................................................................


#def EmptyFC(input,workspace):
#	arcpy.env.workspace = workspace
#	FC_Name = input.rsplit("\\",1)
#	output = FC_Name[1] + "_Layer"
#	arcpy.MakeFeatureLayer_management(input, output, "", "")
#	arcpy.SelectLayerByLocation_management(output, "INTERSECT", output, "", "NEW_SELECTION")
#	arcpy.DeleteRows_management(output)
#	arcpy.Delete_management(output)

def buildWhereClause(table, field, value):
    """Constructs a SQL WHERE clause to select rows having the specified value
    within a given field and table (or Feature Class)."""

    # Add DBMS-specific field delimiters
    fieldDelimited = arcpy.AddFieldDelimiters(table, field)

    # Determine field type
    fieldType = arcpy.ListFields(table, field)[0].type

    # Add single-quotes for string field values
    if str(fieldType) == 'String':
        value = "'{}'".format(value)

    # Format WHERE clause
    whereClause = "{} = {}".format(fieldDelimited, value)
    return whereClause

def Compare_Fields(fc1_path,fc2_path):
    fc1_fields = [field.name for field in arcpy.ListFields(fc1_path)]
    fc2_fields = [field.name for field in arcpy.ListFields(fc2_path)]
    if fc1_fields == fc2_fields:
        return True
    else:
        return False

def Delete_Values_From_FC(values_to_delete, key_field, FC, FC_Path):
    FC = str(FC) + "_Layer"
    FL_Exist(FC,FC_Path,"")
    What_to_Delete = []

    if values_to_delete:
        print "No features were selected to be deleted"
        arcpy.AddMessage("No features were selected to be deleted")
    else:
        values_to_delete = values_to_delete.split(";")
        for value in values_to_delete:
            arcpy.AddMessage("Deleting the following from {}...........................{}".format(FC,value))
            print "Deleting the following from {}...........................{}".format(FC,value)
            clause = buildWhereClause(FC_Path, key_field, value)
            arcpy.SelectLayerByAttribute_management(OutputLayer_InputFC2, "NEW_SELECTION", clause)
            arcpy.DeleteRows_management(OutputLayer_InputFC2)
    arcpy.Delete_management(FC)

#Find out if a Feature Class exists
def FC_Exist(FCname, DatasetPath, Template):
    FCpath = os.path.join(DatasetPath,FCname)
    FCtype = arcpy.Describe(FCpath).shapeType
    if arcpy.Exists(FCpath):
        if Compare_Fields(FCpath,Template):
            arcpy.TruncateTable_management(FCpath)
            #return FCpath
        else:
            arcpy.Delete_management(FCpath)
            arcpy.CreateFeatureclass_management(DatasetPath, FCname, FCtype, Template, "SAME_AS_TEMPLATE", "SAME_AS_TEMPLATE", Template)
    else:
        arcpy.CreateFeatureclass_management(DatasetPath, FCname, FCtype, Template, "SAME_AS_TEMPLATE", "SAME_AS_TEMPLATE", Template)


def Create_FL(LayerName, FCPath, expression =''):
    '''
    Create a Feature layer from a feature class. Optionally, an expression clause can be passed in to
    filter out a subset of data.
    '''
    if arcpy.Exists(LayerName):
        arcpy.Delete_management(LayerName)
    try:
        if expression:
            return arcpy.MakeFeatureLayer_management(FCPath, LayerName, expression, "")
        else:
            return arcpy.MakeFeatureLayer_management(FCPath, LayerName, "", "")
    except:
        return arcpy.AddError(arcpy.GetMessages(2))

def FieldExist(FC,field):
    fc_check = arcpy.ListFields(FC, field)
    if len(fc_check) == 1:
      return True
    else:
      return False

def Find_New_Features(ChildPath, Group_Boundary_Selection_Path, TempCheck_Path, Feature_Check_Selection_Path, FigureExtent_KeyField,in_count):
    #Make Feature Layer output names for all FC of interest and then run make feature layer tool
    OutputLayer_TempCheck = TempCheck + "_Layer"
    OutputLayer_Group_Boundary_Selection = Group_Boundary_Selection + "_Layer"
    OutputLayer_ChildFC = ChildFC + "_Layer"
    FL_Exist(OutputLayer_TempCheck, TempCheck_Path, Feature_Layer_Expression)
    FL_Exist(OutputLayer_Group_Boundary_Selection, Group_Boundary_Selection_Path, Feature_Layer_Expression)
    FL_Exist(OutputLayer_ChildFC, ChildPath, Feature_Layer_Expression)

    #Select all features in the in bucket layer and append to temporary point check FC
    arcpy.SelectLayerByLocation_management(OutputLayer_Group_Boundary_Selection, "INTERSECT", OutputLayer_Group_Boundary_Selection, "", "NEW_SELECTION")
    arcpy.Append_management(OutputLayer_Group_Boundary_Selection, OutputLayer_TempCheck,"NO_TEST","","")
    #Select all samples in the Report Sample FC
    arcpy.SelectLayerByLocation_management(OutputLayer_ChildFC, "INTERSECT", OutputLayer_ChildFC, "", "NEW_SELECTION")
    #Select Features from Bucket FC that intersect the Report Sample FC and invert
    arcpy.SelectLayerByLocation_management(OutputLayer_TempCheck, "INTERSECT", OutputLayer_ChildFC, "", "NEW_SELECTION")
    arcpy.SelectLayerByLocation_management(OutputLayer_TempCheck, "INTERSECT", OutputLayer_TempCheck, "", "SWITCH_SELECTION")
    arcpy.AddMessage("Selecting the new features that fall inside the figure")
    print "Selecting the new records that fall inside the figure"
            
    #Append selected features to Report Sample Location FC
    arcpy.Append_management(OutputLayer_TempCheck, OutputLayer_Feature_Check_Selection,"NO_TEST","","")
    out_count = int(arcpy.GetCount_management(OutputLayer_Feature_Check_Selection).getOutput(0))
    print "Number of new locations found in the figure: " + str(out_count - in_count)
    arcpy.AddMessage("Number of new locations found in the figure: " + str(out_count - in_count))
    arcpy.AddMessage("Added the new locations to " + Feature_Check_Selection)
    print "Added the new locations to " + Feature_Check_Selection
    return out_count


    #Search for locations that are intersect existing points.
    FigureGeometryCheck(OutputLayer_ChildFC,OutputLayer_Group_Boundary_Selection,OutputLayer_Feature_Check_Selection,Feature_Layer_Expression)
            
    #Delete Feature Layers
    arcpy.Delete_management(OutputLayer_TempCheck)
    arcpy.Delete_management(OutputLayer_Group_Boundary_Selection)
    arcpy.Delete_management(OutputLayer_ChildFC)

def Get_Figure_List(FCpath, Keyfield, User_Selected_Figures):
    '''Get_Figure_List(FCpath, Keyfield, User_Selected_Figures)
    Return a list that contains that names of figures that user has selected to edit.  If user did not specify
    any figures in the tool parameters, a list of all figures will be returned.  The function will also return 
    '''
    FigureList=[]
    if User_Selected_Figures == "0":
        if arcpy.ListFields(FCpath,Keyfield,"String"): #Check if the field type of the of the Figure Extent Key field is a string or not.
            Figures = ListRecords(FCpath,Keyfield)
            #FigureList = ["'" + item + "'" for item in Figures] #Adding single quotes at the beginning/end of each item. 
            # Using the create delimiters arcpy function.  The above line was used to add single quotes aronund text values in order to create a definition query.
            arcpy.AddMessage(str(len(FigureList)) + " Figures are going to be updated")
        else:
            FigureList = ListRecords(FCpath,Keyfield)
            arcpy.AddMessage(str(len(FigureList)) + " Figures are going to be updated")
    elif arcpy.ListFields(FCpath,Keyfield,"String"):  #Check if the field type of the of the Figure Extent Key field is a string or not.
        split = [item.strip("'") for item in User_Selected_Figures.split(";")] #List Comprehension which splits delimited string and removes any qoutes.
        #FigureList = ["'" + item.strip() + "'" for item in split] #List Comprehension which adds single quotes at the beginning/end of each item in the List. The qoutes are added for ArcMap Definition query expressions.
        # Using the create delimiters arcpy function.  The above line was used to add single quotes aronund text values in order to create a definition query.
        arcpy.AddMessage(str(len(FigureList)) + " Figure(s) are going to be updated")
    else:
        FigureList = [item.strip("'") for item in User_Selected_Figures.split(";")] #List Comprehension which splits delimited string and removes any qoutes that may be present in string.
        arcpy.AddMessage(str(len(FigureList)) + " Figure(s) are going to be updated")
    return FigureList

def get_geodatabase_path(input_table):
  '''Return the Geodatabase path from the input table or feature class.
  :param input_table: path to the input table or feature class
  '''
  workspace = os.path.dirname(input_table)
  if [any(ext) for ext in ('.gdb', '.mdb', '.sde') if ext in os.path.splitext(workspace)]:
    return workspace
  else:
    return os.path.dirname(workspace)

#Check if there is a filepath from the input layers. If not, pre-pend the path. Also extract the FC names.
def InputCheck(Input):
    if not split(Input)[0]:
        InputPath = arcpy.Describe(Input).catalogPath #join(arcpy.Describe(Input).catalogPath,arcpy.Describe(Input).name)
        InputName = arcpy.Describe(Input).name
    else:
        InputPath = Input
        InputName = arcpy.Describe(Input).name
    return InputPath, InputName 

#Pull out records and make lists. Final List that is returned to variable 
def ListRecords(fc,fields):
    records=[]
    with arcpy.da.SearchCursor(fc,fields) as cursor:
        for row in cursor:
            records.append(row)
        FigureHolder=[]
        for FigureHolder in zip(*records):
            FigureHolder
    return FigureHolder

def RecordCount(fc):
    count = int((arcpy.GetCount_management(fc)).getOutput(0))
    return count

#Remove default fields
def Remove_Fields(fc):
    fields = [f.name for f in arcpy.ListFields(fc)]
    for i,f in enumerate(fields):
        if f == 'Shape' or f == 'Shape_Length' or f == 'OBJECTID' or f == 'GLOBALID':
            del fields[i]
    return fields

def remove_space(fields):
    field_update=[]
    for field in fields:
        if field.find(" ") > 0:
            x=field.replace(' ','_')
            field_update.append(x)
        else:
            field_update.append(field)
    return field_update

def remove_underscore(fields):
    field_update=[]
    for field in fields:
        if field.find("_") > 0:
            x=field.replace('_',' ')
            field_update.append(x)
        else:
            field_update.append(field)
    return field_update

def Select_and_Append(feature_selection_path, select_from_path, append_path, clause=''):
	FL_Exist("Feature_Selection", feature_selection_path, clause)
	FL_Exist("Select_From", select_from_path, clause)
	arcpy.SelectLayerByLocation_management("Feature_Selection", "INTERSECT", "Feature_Selection", "", "NEW_SELECTION")
	arcpy.SelectLayerByLocation_management("Select_From", "INTERSECT", "Feature_Selection", "", "NEW_SELECTION")
	arcpy.Append_management("Select_From",append_path,"NO_TEST","","")

	arcpy.AddMessage("Selecting features from {} that intersect {} \nSelected features were appened to {}".format(os.path.basename(feature_selection_path),os.path.basename(select_from_path),os.path.basename(append_path)))
    print "Selecting features from {} that intersect {} \nSelected features were appened to {}".format(os.path.basename(feature_selection_path),os.path.basename(select_from_path),os.path.basename(append_path))

    arcpy.Delete_management("Feature_Selection")
    arcpy.Delete_management("Select_From")

def unique_values(fc,field):
    with arcpy.da.SearchCursor(fc,[field])as cur:
        return sorted({row[0] for row in cur})
