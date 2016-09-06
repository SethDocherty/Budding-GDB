import arcpy
import os
import itertools
arcpy.env.overwriteOutput = True

#Load a ArcMap table and that is convereted into a list of tuples
def Extract_Table_Records(fc, fields=''):
    if fields: # User has provided a list of fields for extraction
        print "user selected fields"
        print fields
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
                row = list(row)
                records.append(row)
        return records

#Remove default fields
def Remove_DBMS_Specific_Fields(fc):
    fields = [f.name for f in arcpy.ListFields(fc)]
    fields_to_remove = ['SHAPE_Area', 'SHAPE_Length', 'OBJECTID', 'GLOBALID', 'SHAPE', "RID"]
    for field in fields:
        if field in fields_to_remove:
            fields.remove(field)
    return fields

#Extract field name and type
def Extract_Field_NameType(fc):
    field_info=[]
    for field in arcpy.ListFields(fc):
        if field.name == 'SHAPE' or field.name == 'Shape_Length' or field.name == 'OBJECTID' or field.name == 'RID':
            pass
        else:
            item=[]
            item.append(field.name)
            item.append(field.type)
            field_info.append(item)
    return field_info

##def Check_Coincident_Features(Layer_To_Checkp, Initial_Checkp, Final_Checkp):
##
##    #Get field names:
##    field1 = Remove_DBMS_Specific_Fields(Layer_To_Checkp)
##    field2 = Remove_DBMS_Specific_Fields(Final_Checkp)
##    fields = list(set(field1)&set(field2))
##    print field1,field2, fields
##    fields.remove("SHAPE")
##
##    table1 = Extract_Table_Records(Layer_To_Checkp, fields)
##    table2 = Extract_Table_Records(Initial_Checkp, fields)
##    table3 = Extract_Table_Records(Final_Checkp, fields)
##    difference = list(set(table1) - set(table3) - set(table2))
##
##    print "\n{} - Number of Rows: {}".format(Layer_To_Checkp, len(table1))
##    for item in table1:
##        print item
##    print "\n{} - Number of Rows: {}".format(Initial_Checkp, len(table2))
##    for item in table2:
##        print item
##    print "\n{} - Number of Rows: {}".format(Final_Checkp, len(table3))
##    for item in table3:
##        print item
##
##    print "\nDifference between the lists: {}".format(len(difference))
##    for item in difference:
##        print item
##
##    arcpy.CreateFeatureclass_management("in_memory", output_query, desc.shapeType, layer_name, "DISABLED", "DISABLED", layer_name)
##    with arcpy.da.InsertCursor(output_query, input_fields) as iCursor:
##        with arcpy.da.SearchCursor(layer_name, input_fields) as sCursor:
##            for row in sCursor:
##                iCursor.insertRow(row)
##    fields.append("OBJECTID")
##    fid_list = []
##    with arcpy.da.SearchCursor(layer_name, fields) as sCursor:
##        for row in sCursor:

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

def RecordCount(fc):
    count = int((arcpy.GetCount_management(fc)).getOutput(0))
    return count

def find_overlaps(input_features):
    '''Find and print OID value pairs for overlapping features.'''
    for row in arcpy.da.SearchCursor(input_features, ['OID@', 'SHAPE@']):
        for row2 in arcpy.da.SearchCursor(input_features, ['OID@', 'SHAPE@']):
            if row2[1].within(row[1]):# and row2[0] != row[0]:
                print '{0} overlaps {1}'.format(str(row2[0]), str(row[0]))

def find_overlaps2(in_features):
    with arcpy.da.SearchCursor(in_features, ['OID@', 'SHAPE@']) as cur:
        for e1,e2 in itertools.combinations(cur, 2):
            if e1[1].equals(e2[1]):
                print '{} overlaps {}'.format(e1[0],e2[0])

child = r"\\Dep-tisc\homec2\SDOCHERT2\Coding\Python\Budding-GDB\GIS\Scratch Budding GDB.gdb\TestFC\TestFC_Secondary_Boundary"
secondary_check = r"\\Dep-tisc\homec2\SDOCHERT2\Coding\Python\Budding-GDB\GIS\Child.gdb\Sample_Locations\Project_Locations"
final_check = r"\\Dep-tisc\homec2\SDOCHERT2\Coding\Python\Budding-GDB\GIS\Scratch Budding GDB.gdb\TestFC\TestFC_Feature_Check"
fig_extent = r"\\Dep-tisc\homec2\SDOCHERT2\Coding\Python\Budding-GDB\GIS\Child.gdb\LocationGroup_and_FigureExtents\Scale_Extent"
fig_seleciton = []
output_path = r"\\Dep-tisc\homec2\SDOCHERT2\Coding\Python\Budding-GDB\GIS\Scratch Budding GDB.gdb\coincident_features"
output_fcpath = r"\\Dep-tisc\homec2\SDOCHERT2\Coding\Python\Budding-GDB\GIS\Scratch Budding GDB.gdb"
##Create_FL("lyr1",child)
##Create_FL("lyr2", secondary_check)
##Create_FL("lyr3", final_check)
##Check_Coincident_Features("lyr1", "lyr2", "lyr3")
fig_seleciton = []

fig_list = Get_Figure_List(fig_extent, "AreaName", fig_seleciton)
fields = Remove_DBMS_Specific_Fields(secondary_check)

for fig in fig_list:
    print "working on {}.............................".format(fig)
    outFC = os.path.join(output_fcpath,"temp_"+fig)
    clause = buildWhereClause(secondary_check,"AreaName",fig)
    Create_FL("lyr", secondary_check, clause)
    arcpy.CopyFeatures_management("lyr",outFC)
    find_overlaps(outFC)
##    arcpy.FindIdentical_management(outFC,output_path,["SHAPE@"])
##    count = RecordCount(output_path)
##    print"Found {} in {}".format(count,fig)



