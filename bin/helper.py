import arcpy
import sys
import os
from os.path import split, join
from string import replace
from datetime import datetime
arcpy.env.overwriteOutput = True

#..............................................................................................................................
# Creator - Seth Docherty
#
#   Helper functions for the Budding GDB toolset.  Make sure this script is called
#   to import all functions.
#
#..............................................................................................................................

def buildWhereClause(table, field, value):
    """Constructs a SQL WHERE clause to select rows having the specified value
    within a given field and table (or Feature Class)."""

    # Add DBMS-specific field delimiters
    fieldDelimited = arcpy.AddFieldDelimiters(table, field)

    # Determine field type
    fieldType = arcpy.ListFields(table, field)[0].type

    ## Add single-quotes for string field values
    #if str(fieldType) == 'String':
    #    value = "'{}'".format(value)

    # Format WHERE clause
    whereClause = "{} = {}".format(fieldDelimited, value)
    return whereClause

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

def Compare_Fields(fc1_path,fc2_path):
    fc1_fields = [field.name for field in arcpy.ListFields(fc1_path)]
    fc2_fields = [field.name for field in arcpy.ListFields(fc2_path)]
    if fc1_fields == fc2_fields:
        return True
    else:
        return False



def csv_to_table(input_csv, input_fc, selection_fields, ParentField, FigureExtentField,scratch_gdb):
    #Extracting CSV stuff
    csv_list = Extract_File_Records(input_csv,"No")
    header = Space2Underscore(csv_list.pop(0))
    fields = Extract_Input_fields_from_csv(selection_fields, ParentField, FigureExtentField)
    field_index = get_column_index(header,fields)
    csv_list = extract_list_columns(csv_list, field_index, "No")

    #Creating blank table and appending csv list
    name = "temp_csv_table"
    header_fieldInfo = get_Data_Type_FromGIS(fields, input_fc)
    Create_Empty_Table(header_fieldInfo, name, scratch_gdb)
    Add_Records_to_Table(csv_list, os.path.join(scratch_gdb, name))
    return os.path.join(scratch_gdb, name)


def Delete_Values_From_FC(values_to_delete, key_field, FC, FC_Path):
    FC = str(FC) + "_Layer"
    Create_FL(FC,FC_Path,"")
    What_to_Delete = []

    if not values_to_delete:
        print "No features were selected to be deleted"
        arcpy.AddMessage("No features were selected to be deleted")
    else:
        values_to_delete = values_to_delete.split(";")
        for value in values_to_delete:
            arcpy.AddMessage("Deleting the following from {}...........................{}".format(FC,value))
            print "Deleting the following from {}...........................{}".format(FC,value)
            clause = buildWhereClause(FC_Path, key_field, value)
            arcpy.SelectLayerByAttribute_management(FC, "NEW_SELECTION", clause)
            arcpy.DeleteRows_management(FC)
    arcpy.Delete_management(FC)

#Extract field name and type
def Extract_Field_NameType(fc):
    field_info=[]
    for field in arcpy.ListFields(fc):
        if field.name == 'Shape' or field.name == 'Shape_Length' or field.name == 'OBJECTID' or field.name == 'RID':
            pass
        else:
            item=[]
            item.append(field.name)
            item.append(field.type)
            field_info.append(item)
    return field_info

#Load a .csv file and that is convereted into a list of tuples
def Extract_File_Records(filename):
    fp = open(filename, 'Ur')
    #reader = csv.reader(fp)
    data_list = []
    for line in fp:#reader:
        data_list.append(tuple(line.strip().split(',')))
    fp.close()
    return data_list

def extract_list_columns(input_list,index_list):
    my_items = operator.itemgetter(*index_list)
    new_list = [my_items(x) for x in input_list]
    return new_list

#Load a ArcMap table and that is convereted into a list of tuples
def Extract_Table_Records(fc, fields=''):
    if fields: # User has provided a list of fields for extraction
        records=[]
        with arcpy.da.SearchCursor(fc, fields) as cursor:
            for row in cursor:
                records.append(row)
        return records
    else: #User has not provided a list. Will default to all fields.
        fields = Remove_DBMS_Specific_Fields(fc)
        records=[]
        with arcpy.da.SearchCursor(fc, fields) as cursor:
            for row in cursor:
                records.append(row)
        return records


def Extract_input_fields_from_csv(selection_fields, ParentField, FigureExtentField):
    input_fields = selection_fields.split(";")
    input_fields.append(ParentField)
    if FigureExtentField:
        input_fields.append(FigureExtentField)
    return input_fields


#Find out if a Feature Class exists
def FC_Exist(FCname, DatasetPath, Template):
    FCpath = os.path.join(DatasetPath,FCname)
    FCtype = arcpy.Describe(Template).shapeType
    if arcpy.Exists(FCpath):
        if Compare_Fields(FCpath,Template):
            arcpy.AddMessage("Feature class, {}, already exists. Clearing records.......".format(FCname))
            return arcpy.TruncateTable_management(FCpath)
        else:
            arcpy.AddMessage("Additional fields have been added since the Feature class, {}, was created. Recreating Feature class.......".format(FCname))
            arcpy.Delete_management(FCpath)
            return arcpy.CreateFeatureclass_management(DatasetPath, FCname, FCtype, Template, "SAME_AS_TEMPLATE", "SAME_AS_TEMPLATE", Template)
    else:
        arcpy.AddMessage("Feature class, {}, does not exists. Creating now.......".format(FCname))
        return arcpy.CreateFeatureclass_management(DatasetPath, FCname, FCtype, Template, "SAME_AS_TEMPLATE", "SAME_AS_TEMPLATE", Template)


def FieldExist(FC,field_to_check):
    fields = [field.name for field in arcpy.ListFields(FC)]
    if field_to_check in fields:
      return True
    else:
      return False

def Find_New_Features(Layer_To_Checkp, Initial_Checkp, Intermediate_Checkp, Final_Check, clause, in_count):
    #Make Feature Layer output names for all FC of interest and then run make feature layer tool
    Layer_To_Check = arcpy.Describe(Layer_To_Checkp).name+"_layer"
    Initial_Check = arcpy.Describe(Initial_Checkp).name +"_layer"
    Intermediate_Check = arcpy.Describe(Intermediate_Checkp).name +"_layer"

    Create_FL(Layer_To_Check, Layer_To_Checkp, clause)
    Create_FL(Initial_Check, Initial_Checkp, clause)
    Create_FL(Intermediate_Check, Intermediate_Checkp, clause)

    #Select all features in the in bucket layer and append to temporary point check FC
    arcpy.SelectLayerByLocation_management(Initial_Check, "INTERSECT", Initial_Check, "", "NEW_SELECTION")
    arcpy.Append_management(Initial_Check, Intermediate_Check,"NO_TEST","","")
    #Select all samples in the Report Sample FC
    arcpy.SelectLayerByLocation_management(Layer_To_Check, "INTERSECT", Layer_To_Check, "", "NEW_SELECTION")
    #Select Features from Bucket FC that intersect the Report Sample FC and invert
    arcpy.SelectLayerByLocation_management(Intermediate_Check, "INTERSECT", Layer_To_Check, "", "NEW_SELECTION")
    arcpy.SelectLayerByLocation_management(Intermediate_Check, "INTERSECT", Intermediate_Check, "", "SWITCH_SELECTION")
    arcpy.AddMessage("Selecting the new features that fall inside the figure")
    print "Selecting the new records that fall inside the figure"
    #Append selected features to Report Sample Location FC
    arcpy.Append_management(Intermediate_Check, Final_Check,"NO_TEST","","")
    out_count = int(arcpy.GetCount_management(Final_Check).getOutput(0))
    print "Number of new locations found in the figure: " + str(out_count - in_count)
    arcpy.AddMessage("Number of new locations found in the figure: " + str(out_count - in_count))
    arcpy.AddMessage("Added the new locations to " + Final_Check)
    print "Added the new locations to " + Final_Check
    return out_count

##    #Search for locations that are intersect existing points.
##    FigureGeometryCheck(Layer_To_Checkp, Initial_Checkp, Final_Checkp,clause)

    #Delete Feature Layers
    arcpy.Delete_management(Intermediate_Check)
    arcpy.Delete_management(Initial_Check)
    arcpy.Delete_management(Layer_To_Check)


def get_column_index(row_header,fields):
    '''
    Return a dictionary of field names as keys and the mapped column index for the field as the dictionary value.
    '''
    index_list = list()
    for field in fields:
        try:
            index_list.append(row_header.index(field))
        except ValueError:
            arcpy.AddMessage(("{} does not exist in the header field list. Please make sure field is spelled correctly and in the header row.\n "
                            "Exiting script.  Please correct errors and try again.").format(field))
            print ("{} does not exist in the header field list. Please make sure field is spelled correctly and in the header row.\n "
                            "Exiting script.  Please correct errors and try again.").format(field)
    return index_list


def Get_Field_Type(fc,field_to_check):
    fields = [[field.name,field.type] for field in arcpy.ListFields(fc)]
    type = [type for field,type in fields if field_to_check == field][0]
    return type

#TODO Need to update my other scripts to use the BuildWhereClause Function that also use this function
def Get_Figure_List(FCpath, Keyfield, User_Selected_Figures):
    '''Get_Figure_List(FCpath, Keyfield, User_Selected_Figures)
    Return a list that contains that names of figures that user has selected to edit.  If user did not specify
    any figures in the tool parameters, a list of all figures will be returned.  The function will also return
    '''
    FigureList=[]
    if not User_Selected_Figures:
        FigureList = ListRecords(FCpath,Keyfield)
        arcpy.AddMessage(str(len(FigureList)) + " Figures are going to be updated")
    else:
        FigureList = [item.strip() for item in User_Selected_Figures.split(";")] #List Comprehension which splits delimited string and removes any qoutes that may be present in string.
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
def Remove_DBMS_Specific_Fields(fc):
    fields = [f.name for f in arcpy.ListFields(fc)]
    fields_to_remove = ['SHAPE_Area', 'SHAPE_Length', 'OBJECTID', 'GLOBALID', 'SHAPE', "RID"]
    for i,f in enumerate(fields):
        if f in fields_to_remove:
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

def start_edit_session(fc_to_edit):
    # Start an edit session. Must provide the worksapce.
    workspace = get_geodatabase_path(fc_to_edit)
    edit = arcpy.da.Editor(workspace)
    # Edit session is started without an undo/redo stack for versioned data and starting edit operation
    #  (for second argument, use False for unversioned data)
    edit.startEditing(False, False)
    edit.startOperation()
    return edit

def stop_edit_session(edit):
    # Stop the edit session and save the changes
    edit.stopOperation()
    edit.stopEditing(True)
    

def Select_and_Append(feature_selection_path, select_from_path, append_path, clause=''):
    Create_FL("Feature_Selection", feature_selection_path, clause)
    Create_FL("Select_From", select_from_path, clause)
    arcpy.SelectLayerByLocation_management("Feature_Selection", "INTERSECT", "Feature_Selection", "", "NEW_SELECTION")
    arcpy.SelectLayerByLocation_management("Select_From", "INTERSECT", "Feature_Selection", "", "NEW_SELECTION")
    arcpy.Append_management("Select_From", append_path, "NO_TEST", "", "")

    print "Selecting features from {} that intersect {} \nSelected features were appened to {}".format(os.path.basename(feature_selection_path),os.path.basename(select_from_path),os.path.basename(append_path))
    arcpy.AddMessage("Selecting features from {} that intersect {} \nSelected features were appened to {}".format(os.path.basename(feature_selection_path),os.path.basename(select_from_path),os.path.basename(append_path)))

    arcpy.Delete_management("Feature_Selection")
    arcpy.Delete_management("Select_From")

def unique_values(fc,field):
    with arcpy.da.SearchCursor(fc,[field])as cur:
        return sorted({row[0] for row in cur})

# TODO

#def FigureGeometryCheck(fc1,fc2,fc3,expression):
#	fc1_lyr1 = "lyr1"
#	fcl_lyr2 = "lyr2"
#	fcl_lyr3 = "lyr3"
#	Create_FL(fc1_lyr1,fc1,expression)
#	Create_FL(fcl_lyr2,fc2,expression)
#	Create_FL(fcl_lyr3,fc3,expression)
#	fc1_count = RecordCount(fc1_lyr1)
#	fc2_count = RecordCount(fcl_lyr2)
#	field = "Location_ID"
#	if fc1_count == fc2_count:
#		pass
#	else:
#		fc1_list = unique_values(fc1_lyr1,field)
#		fc2_list = unique_values(fcl_lyr2,field)
#		fc3_list = unique_values(fcl_lyr3,field)
#		difference = list(set(fc2_list) - set(fc1_list)- set(fc3_list))
#		if len(difference) != 0:
#			print str(len(difference)) + " additional locations have been found that intersect previous locations that are in the figure. They are:\n"
#			arcpy.AddMessage(str(len(difference)) + " additional locations have been found that intersect previous locations that are in the figure. They are:\n")
#			for record in difference:
#				clause =  '"' + field + '"' + " = '" + record + "'"
#				arcpy.SelectLayerByAttribute_management(fcl_lyr2,"ADD_TO_SELECTION",clause)
#				arcpy.AddMessage(str(record))
#				print str(record)
#			arcpy.Append_management(fcl_lyr2, fcl_lyr3,"NO_TEST","","")


#FigureGeometryCheck(Layer_To_Checkp, Initial_Checkp, Final_Checkp,clause)
def Check_Coincident_Features(Layer_To_Check, Initial_Check, Final_Check):
       
    #Get field names:
    field1 = Remove_DBMS_Specific_Fields(Layer_To_Check) #[f.name for f in arcpy.ListFields(Layer_To_Checkp)]
    field2 = Remove_DBMS_Specific_Fields(Final_Check) #[f.name for f in arcpy.ListFields(Final_Checkp)]
    fields = list(set(field1)&set(field2))
    fields.remove("SHAPE")

    table1 = Extract_Table_Records(Layer_To_Checkp, fields)
    table2 = Extract_Table_Records(Initial_Checkp, fields)
    table3 = Extract_Table_Records(Final_Checkp, fields)
    difference = list(set(table1) - set(table3) - set(table2))
    
    if len(difference) != 0:
        arcpy.AddMessage("{} features have been found which were coincident".format(len(difference)))
        #arcpy.Append_management()

    #append difference to final check