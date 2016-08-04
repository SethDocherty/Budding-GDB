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


def EmptyFC(input,workspace):
	arcpy.env.workspace = workspace
	FC_Name = input.rsplit("\\",1)
	output = FC_Name[1] + "_Layer"
	arcpy.MakeFeatureLayer_management(input, output, "", "")
	arcpy.SelectLayerByLocation_management(output, "INTERSECT", output, "", "NEW_SELECTION")
	arcpy.DeleteRows_management(output)
	arcpy.Delete_management(output)

#Find out if a Feature Class exists
def FC_Exist(FCname, DatasetPath, Template):
	FCpath = os.path.join(DatasetPath,FCname)
	if arcpy.Exists(FCpath):
		return FCpath 
	else:
		return arcpy.CreateFeatureclass_management(DatasetPath, FCname, "POINT", Template, "SAME_AS_TEMPLATE", "SAME_AS_TEMPLATE", Template)

#Find out if a Feature Layer exists.
def FL_Exist(LayerName, FCPath, Expression):
	if arcpy.Exists(LayerName):
		arcpy.Delete_management(LayerName)
	try:
		return arcpy.MakeFeatureLayer_management(FCPath, LayerName, Expression, "")
	except:
		return arcpy.AddError(arcpy.GetMessages(2))

def FieldExist(FC,field):
    fc_check = arcpy.ListFields(FC, field)
    if len(fc_check) == 1:
      return True
    else:
      return False

#Pull out recrods and make lists. Final List that is returned to variable
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

def unique_values(fc,field):
	with arcpy.da.SearchCursor(fc,[field])as cur:
		return sorted({row[0] for row in cur})




