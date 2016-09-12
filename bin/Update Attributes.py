#..............................................................................................................................
# Creator - Seth Docherty
# Date - 08/07/2015
# Purpose - Update feature class attributes from a source feature class. The source feature class is considered the "Master" and
#           the feature class that is going to be updated is the target.
#
#           The scripts user input requirements:
#               - Source FC (Master)
#               - Target FC (FC with attributes that need to be updated)
#               - Figure extent FC (FC that stores all the figures as objects)
#               - Figure Key Field (this is the field that stores the names of all the figure extent object. This field is
#                 required to be in the Target FC and spelled the same.
#               - Source Key Field (This is the field that will be used for joining data to the Target FC)
#               - Target Key Field (This is the field that will be used for joining data from the Source FC)
#               - Fields to update (User selects fields in the Target FC that need to be updated.  This field is
#                 required to be in the Target FC and spelled the same.)
#               - Figures to update (User selects figures that will be updated)
#
#           The script has built in error checking to make sure:
#               - Figure Key Field Exists
#               - Check to see if Target FC has GIS features for given figure. If does not exists, skips to next figure.
#
#           The script performs a simple if conditional check comparing the attributes in the Target FC against the Source FC.  If
#           the attributes are not the same, Target FC updates to match the Source FC attributes.
#
# Log:
#
#..............................................................................................................................

# Import arcpy module
import arcpy, os, operator, re, sys
from os.path import split, join
from datetime import datetime
from string import replace
from helper import *
arcpy.env.overwriteOutput = True

startTime = datetime.now()
print startTime

def Does_Figure_Exist(childFCpath, childFC, figure, child_figure_list, figure_key_field):
    print "Runtime: ", datetime.now()-startTime
    arcpy.AddMessage(40*'.' + '\n' + "Runtime: {}".format((datetime.now()-startTime)))
    print "Figure Name: {}" + str(figure)
    arcpy.AddMessage(40*'.' + "Updating Figure: {}".format(str(figure)))
    clause = buildWhereClause(childFCpath, figure_key_field, figure)

    # Check to see if figure name child FC
    # If does not exists, skip to next figure.
    if figure not in child_figure_list:
        print ("{} is not in {}.  Skipping to next figure.".format(figure,childFC))
        arcpy.AddMessage(("{} is not in {}.  Skipping to next figure.".format(figure,childFC)))
        return False
    else:
        return clause

def Update_Field(Sourcepath, targetpath, SourceTableField, TargetTableField, field, clause=''):
    SourceFCpath, SourceFC = InputCheck(Sourcepath)
    targetFCpath, targetFC = InputCheck(targetpath)

    print "."*25 + "Updating the following field: " + field + " (" + str(datetime.now()-startTime)+")"
    arcpy.AddMessage("."*25 + "Updating the following field: " + field + " (" + str(datetime.now()-startTime)+")")

    if Get_Field_Type(SourceFCpath,field) != Get_Field_Type(targetFCpath,field):
        arcpy.AddMessage("....\n.... \
                         \nThe field, {}, in {} and {} do not have matching data types. Please correct by updating the field data \
                         type to {} for {} in {}. \
                         \nSkipping to next field................. \
                         \n....\n....".format(field, SourceFC, targetFC, str(Get_Field_Type(SourceFCpath,field)), field, targetFC))
        return

    Source_dict = dict([(r[0], (r[1])) for r in arcpy.da.SearchCursor(SourceFCpath, [SourceTableField,field])])
    Target_dict = dict([(r[0], (r[1])) for r in arcpy.da.SearchCursor(targetFCpath,[TargetTableField,field],clause)])
    updateRows = arcpy.da.UpdateCursor(targetFCpath,[TargetTableField,field],clause) #Cursor to be used to update attributes in project FC
    Source_dictSet = set(Source_dict)
    Target_dictSet = set(Target_dict)
    Source_dictUpdate = dict()
    for key in Source_dictSet.intersection(Target_dictSet):
        if key not in Source_dictUpdate:
            Source_dictUpdate[key] = dict()
        Source_dictUpdate[key] = Source_dict[key]
    ls = []
    record_check = [Source_dictUpdate[k] == v for k, v in Target_dict.iteritems() if k in Source_dictUpdate] #Getting a count of values that are not the same in A:value and B:value
    if record_check.count(False) == 0: #Count
        print ("There are no records to update in {}".format(field))
        arcpy.AddMessage(("There are no records to update in {}".format(field)))
    else:
        for updateRow in updateRows:
            source_join = updateRow
            if source_join[0] in Source_dictUpdate:
                if source_join[1] != Source_dictUpdate[source_join[0]]:
                    print ("Updating {} to {}".format(source_join[0], Source_dictUpdate[source_join[0]]))
                    arcpy.AddMessage(("Updating {} to {}".format(source_join[0], Source_dictUpdate[source_join[0]])))
                    updateRow[1] = Source_dictUpdate[source_join[0]]
            updateRows.updateRow(updateRow)
        del updateRow, updateRows

def Update_Figures(Report_Sample, MasterSample, FigureExtent, FigureExtent_KeyField, SourceTableField, TargetTableField, input_field, input_figures):
    MasterSamplepath, MasterSampleFC = InputCheck(MasterSample)
    Report_SampleFCpath, Report_SampleFC = InputCheck(Report_Sample)

    edit_session = start_edit_session(Report_SampleFCpath)

    if not input_figures:
        #Formatting the input fields to be updated
        Field_to_update = input_field.split(";")
        arcpy.AddMessage("The following fields are going to be updated: {}".format(str(Field_to_update)))
        for field in Field_to_update:
            if (not FieldExist(MasterSamplepath,field)):
                arcpy.AddMessage(("{} is not in {}.  Skipping to next field.".format(field,MasterSampleFC)))
            else:
                Update_Field(MasterSamplepath, Report_SampleFCpath, SourceTableField, TargetTableField, field)
    else:
        FigureExtentpath, FigureExtentFC = InputCheck(FigureExtent)
       #Check to see if all the Report feature classes have the FigureExtent Keyfield.
        if not (FieldExist(Report_SampleFCpath,FigureExtent_KeyField)):
            arcpy.AddError(("The field {} does not exist in {}".format(FigureExtent_KeyField,Report_SampleFC)))
            sys.exit()
   
        # Getting List of values to update.  List is based on values from Figure Extent
        FigureList = Get_Figure_List(FigureExtentpath, FigureExtent_KeyField, input_figures)
    
        #Get list of figures in the report FC
        ReportFC_FigureList = unique_values(Report_SampleFCpath,FigureExtent_KeyField)

        #Formatting the input fields to be updated
        Field_to_update = input_field.split(";")
        arcpy.AddMessage("The following fields are going to be updated: {}".format(str(Field_to_update)))

        #Loop through all figures and update Project Feature Class
        for figure in FigureList:
            clause = Does_Figure_Exist(Report_SampleFCpath, Report_SampleFC, figure, ReportFC_FigureList, FigureExtent_KeyField)
            if clause:
                for field in Field_to_update:
                    if (not FieldExist(MasterSamplepath,field)):
                      arcpy.AddMessage(("{} is not in {}.  Skipping to next field.".format(field,MasterSampleFC)))
                    else:
                        Update_Field(MasterSamplepath, Report_SampleFCpath, SourceTableField, TargetTableField, field, clause)
     
    stop_edit_session(edit_session)
           
try:

    Parent = arcpy.GetParameterAsText(0)
    Child = arcpy.GetParameterAsText(1)
    ParentTableField = arcpy.GetParameterAsText(2) #The Master/Source Feature Class
    ChildTableField = arcpy.GetParameterAsText(3) #The Project/Target Feature Class
    input_field = arcpy.GetParameterAsText(4)
    FigureExtent = arcpy.GetParameterAsText(5)
    FigureExtent_KeyField = arcpy.GetParameterAsText(6)
    input_figures = arcpy.GetParameterAsText(7)

    Update_Figures(Child, Parent, FigureExtent, FigureExtent_KeyField, ParentTableField, ChildTableField, input_field, input_figures)

    print "Script Runtime: ", datetime.now()-startTime
    arcpy.AddMessage("Script Runtime: " + str(datetime.now()-startTime))

except Exception, e:
    # If an error occurred, print line number and error message
    import traceback, sys
    tb = sys.exc_info()[2]
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback.print_exc()
    tb_error = traceback.format_tb(exc_traceback)
    print "line %i" % tb.tb_lineno
    arcpy.AddMessage("line %i" % tb.tb_lineno)
    for item in tb_error:
        print item
        arcpy.AddMessage(item)
    print e.message
    arcpy.AddMessage(e.message)