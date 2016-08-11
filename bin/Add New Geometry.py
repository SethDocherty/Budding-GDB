#..............................................................................................................................
# Creator - Seth Docherty  Test
# Purpose - Figure creator for SMSR Report.  Updates figures with new locations which are used for field status maps.
# 
# Log:          
#	1. Added the following geoprocessing tools to the part of the program that creates a FC of samples inside Figure Extent. 12/1/2014. Can be found towards
#	   the beginning of PART 1
#        - Add Field: Gauging Status Field -
#        - Calculate Field: Gauging Status field with the following text "Null Status"
#	2. Added a message to let the user know how many new locations were found in each figure during during the Sample Check phase of program. 12/1/2014
#   3. Moved the section to "delete selected features" to the top of the code right after the part of the code that selected locations within
#      figure extent. 01/22/2015
#   4. Added additional code in the section, "getting number of figures to update" 01/25/2015
#        - The list that is produced in the section of code is used to create definition queries.  If the key field used to extract attributes
#          is a string, single quotes at the beginning/end of each item in the list is need for the definition query to be valid.  An if statement
#          checks to see if the key field is a string or a number (looks at the field type).  If it passes for a string, single quotes are added.
#   5. Added check to see if feature layers exists.  This helps to ensure that feature layers from a previous run are deleted from memory. 01/25/2015
#   6. Removed user input of 3 FC's that were saved to the Scratch GDB.  All the user has to do is specify the Feature Dataset path in the Scratch GDB.
#      The FC's needed will be created and stored in the user specified FD. 01/30/2015
#   7. New ability to select layers from the table of contents when running the script from ArcMap.  To utlize this ability, the user input FC's have to
#      be passed through a logic gate to extract the full path. 01/30/2015
#   8. Created definition called FC_Exists.  This will check to see if a FC exists.  If it exists, it passes on the result otheriwse it creates the FC. 2/24/2015
#       - Cuts back on redundent code. Cuts out 15 lines of code since it is called 3 times.
#   9. Created definition called FL_Exists.  This will check to see if a FL exists.  If it exists, it passes on the result otheriwse it creates the FL. 2/24/2015
#		 - Cuts back on redundent code. Cuts out 60 lines of code since it is called 12 times.
#   10. Created definition called InputCheck.  Will extract the FC names and FC path from input layers. 2/24/2015
#        - Cuts back on redundent code. Cuts out 20 lines of code since it is called 4 times.
#   11. Added a check to see if users input for figures to be updated and samples to be deleted has 'qoutes' at the beginning/end and no spaces between ' and ;. 3/3/2015
#        - Use of strip() will delete spaces at front and end for each item in list.
#   12. Added a check to see if key field is present in all 3 key FC's: ReportSamples, FigureExtent, and Group_Boundary. 3/3/2015
#        - Maybe add an additional check which compares and the number of unique values in the key field and if the unique values are the same across all 3 FC's?
#   13. Created an additional definition which adds specific fields of interest into the script for Reports.  Example LNAPL adds a field called Gauging_Status and ESS_ISS adds a
#       field called CM_Action_Limit. Defintion is called Report_FieldUpdate. 3/3/2015 
#   14. Added a check to look for point locations that are stacked on top of each other. 3/31/2015 
#        - Compares the number of records in the output "Locations in secondary output" and the report FC.
#        - If the number of records are the same, continue with script
#        - If the number of records are not the same, will need to create a list of locations that are not in the report FC.
#        - The additional records will be added to the Feature_Check_Selection which is the Sample_Check FC.
#   15. Commented out code that use the defintion, Report_FieldUpdate. I built into my FC's default values and other scripts I've created can update necessary fields for symbolizing/annotation. 10/20/2015
#        - Code shows up near line 336
#
#..............................................................................................................................

# Import arcpy module
import os, arcpy
from datetime import datetime
from os.path import split, join
arcpy.env.overwriteOutput = True

def Report_FieldUpdate(fl_name):
    field = "CM_Action_Level" #"[report specific]" #"CM_Action_Level"
    expression = '"Below Action Level"' #"[report specific]" #'"Null Status"'
    #Add Gauging Status Field
    arcpy.AddField_management(fl_name, field, "TEXT", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")

    #Calculate value for the CM Action Level Field in Figure_Extent_Selection
    return arcpy.CalculateField_management(fl_name, field, expression, "PYTHON_9.3")

#def EmptyFC(input,workspace):
#	arcpy.env.workspace = workspace
#	FC_Name = input.rsplit("\\",1)
#	output = FC_Name[1] + "_Layer"
#	arcpy.MakeFeatureLayer_management(input, output, "", "")
#	arcpy.SelectLayerByLocation_management(output, "INTERSECT", output, "", "NEW_SELECTION")
#	arcpy.DeleteRows_management(output)
#	arcpy.Delete_management(output)

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

#Check if there is a filepath from the input layers. If not, pre-pend the path. Also extract the FC names.
def InputCheck(Input):
    if not split(Input)[0]:
        InputPath = arcpy.Describe(Input).catalogPath #join(arcpy.Describe(Input).catalogPath,arcpy.Describe(Input).name)
        InputName = arcpy.Describe(Input).name
    else:
        InputPath = Input
        InputName = arcpy.Describe(Input).name
    return InputPath, InputName 

def FieldExist(FC,field):
    fc_check = arcpy.ListFields(FC, field)
    if len(fc_check) == 1:
      return True
    else:
      return False

def RecordCount(fc):
    count = int((arcpy.GetCount_management(fc)).getOutput(0))
    return count

def unique_values(fc,field):
    with arcpy.da.SearchCursor(fc,[field])as cur:
        return sorted({row[0] for row in cur})

def FigureGeometryCheck(fc1,fc2,fc3,expression):
    fc1_lyr1 = "lyr1"
    fcl_lyr2 = "lyr2"
    fcl_lyr3 = "lyr3"
    FL_Exist(fc1_lyr1,fc1,expression)
    FL_Exist(fcl_lyr2,fc2,expression)
    FL_Exist(fcl_lyr3,fc3,expression)
    fc1_count = RecordCount(fc1_lyr1)
    fc2_count = RecordCount(fcl_lyr2)
    field = "Location_ID"
    if fc1_count == fc2_count:
        pass
    else:
        fc1_list = unique_values(fc1_lyr1,field)
        fc2_list = unique_values(fcl_lyr2,field)
        fc3_list = unique_values(fcl_lyr3,field)
        difference = list(set(fc2_list) - set(fc1_list)- set(fc3_list))
        if len(difference) != 0:
            print str(len(difference)) + " additional locations have been found that intersect previous locations that are in the figure. They are:\n"
            arcpy.AddMessage(str(len(difference)) + " additional locations have been found that intersect previous locations that are in the figure. They are:\n")
            for record in difference:
                clause =  '"' + field + '"' + " = '" + record + "'"
                arcpy.SelectLayerByAttribute_management(fcl_lyr2,"ADD_TO_SELECTION",clause)
                arcpy.AddMessage(str(record))
                print str(record)
            arcpy.Append_management(fcl_lyr2, fcl_lyr3,"NO_TEST","","")

startTime = datetime.now()
print startTime

try:

    #..............................................................................................................................
    #User Input data
    #..............................................................................................................................

    #Sitewide Sample Location from Chevron GDB
    Parent = arcpy.GetParameterAsText(0)
    
    #File path for the Report Sample locatcion Feature Class
    Child = arcpy.GetParameterAsText(1)
    
    #Figure Extent FC
    FigureExtent = arcpy.GetParameterAsText(2)

    #The location boundary that is associated with the Figure Extent.
    #If no location boundary is used for Report Figures, please choose the Figure Extent Feature Class.
    Group_Boundary = arcpy.GetParameterAsText(3)

    #The location boundary that is associated with the Figure Extent.
    #If no location boundary is used for Report Figures, please choose the Figure Extent Feature Class.
    FigureExtent_KeyField = arcpy.GetParameterAsText(4)

    #Input Feature Dataset in Scratch GDB
    Input_ScratchFD = arcpy.GetParameterAsText(5)

    #SQL Expression to type in the figures that need to be updated.	If all figures need to be updated, please type in '0'.
    input_figures = arcpy.GetParameterAsText(6)

    #Field that will be used to expression to delete necessary samples.  Please specify a field even if no values need to be deleted.
    Fields_to_Delete = arcpy.GetParameterAsText(7)

    #SQL Expression: Select values that need to be delted. Separate each value with a ;.  If no values need to be deleted, please type in '0'.
    What_To_Delete_List = arcpy.GetParameterAsText(8)
    
    #..............................................................................................................................
    #Hard Coded Data
    #..............................................................................................................................

    #Check if there is a filepath from the input layers. If not, pre-pend the path. Also extract the FC names.
    ParentPath, ParentFC = InputCheck(Parent)
    ChildPath, ChildFC = InputCheck(Child)
    FigureExtentpath, FigureExtentFC = InputCheck(FigureExtent)
    GroupLocationBoundarypath, GroupLocationBoundaryFC = InputCheck(Group_Boundary)

    #Check to see if all the Report feature classes have the FigureExtent Keyfield.
    if not all((FieldExist(ChildPath,FigureExtent_KeyField), FieldExist(FigureExtentpath,FigureExtent_KeyField), FieldExist(GroupLocationBoundarypath,FigureExtent_KeyField))):
        arcpy.AddError(("The field {} does not exist in {}, {} or {}".format(FigureExtent_KeyField,ChildFC,FigureExtentFC,GroupLocationBoundaryFC)))
        sys.exit()

    #Extracting File Paths for Feature Dataset and Scratch File Geodatabase
    Scratch_FDPath = join(arcpy.Describe(Input_ScratchFD).catalogPath,(Input_ScratchFD))
    Scratch_FD = Scratch_FDPath.rsplit("\\",1)[1]
    
    #Setting the file path for the Temp FC's that will be created in the Scratch GDB.
    FigSelection = Scratch_FD + "_FigureSelection"
    FigSelectionPath = os.path.join(Scratch_FDPath,FigSelection)
    SpatialTmp = Scratch_FD + "_SpatialJoinTemp"
    SpatialTmpPath = os.path.join(Scratch_FDPath,SpatialTmp)
    TempCheck = Scratch_FD + "_Point_CheckTmp"
    TempCheck_Path = os.path.join(Scratch_FDPath,TempCheck)
    Figure_Extent_Selection = Scratch_FD + "_Main_Boundary"
    Figure_Extent_Selection_Path = os.path.join(Scratch_FDPath,Figure_Extent_Selection)
    Group_Boundary_Selection = Scratch_FD + "_Secondary_Boundary"
    Group_Boundary_Selection_Path = os.path.join(Scratch_FDPath,Group_Boundary_Selection)
    Feature_Check_Selection = Scratch_FD + "_Feature_Check"
    Feature_Check_Selection_Path = os.path.join(Scratch_FDPath,Feature_Check_Selection)

    #Create the 3 Main Features Class's
    FC_Exist(Figure_Extent_Selection, Scratch_FDPath, ChildPath)
    FC_Exist(Group_Boundary_Selection, Scratch_FDPath, ChildPath)
    FC_Exist(Feature_Check_Selection, Scratch_FDPath, ChildPath)
            
    print "......................................................................Runtime: ", datetime.now()-startTime
    arcpy.AddMessage("......................................................................Runtime: " + str(datetime.now()-startTime))

    #........................................................................................................................................
    #Setting up the Feature Class that stores the Figure Extent Polygons that will be updated.
    #........................................................................................................................................
    
    #Getting the number of figures to update
    FigureList = Get_Figure_List(FigureExtentpath, FigureExtent_KeyField, input_figures)

    #Make Feature Layer from Figure Extent FC
    OutputLayer_FigureExtentFC = FigureExtentFC + "_Layer" #InputLayer + "_Layer"
    FL_Exist(OutputLayer_FigureExtentFC,FigureExtentpath,"")

    #Selecting the records found the Figure list
    for value in FigureList:
        clause = buildWhereClause(FigureExtentpath, FigureExtent_KeyField, value)
        arcpy.SelectLayerByAttribute_management(OutputLayer_FigureExtentFC,"ADD_TO_SELECTION", clause)

    #Copy all selected records to a standalone Feature Class which holds the all figure that will be updated.
    arcpy.CopyFeatures_management(OutputLayer_FigureExtentFC, FigSelectionPath)
    arcpy.Delete_management(OutputLayer_FigureExtentFC)
    arcpy.AddMessage("Successfully created the Features Class, {}, which is a list of figures that will be updated.".format(FigSelection))
    print "Successfully created the Features Class, {}, which is a list of figures that will be updated.".format(FigSelection)
    
    print "......................................................................Runtime: ", datetime.now()-startTime
    arcpy.AddMessage("......................................................................Runtime: " + str(datetime.now()-startTime))

    #..............................................................................................................................
    # PART 1
    # Samples within Figure Extent - Part of the program that performs a spatial join of sample locations from the Master GDB and
    # the selected figures in the figure selection feature classes
    #..............................................................................................................................
    print "Part 1: Selecting all locations that fall within the figure extents and deleting user specified sample types...\n...\n...\n..."
    arcpy.AddMessage("Part 1: Selecting all locations that fall within the figure extents and deleting user specified sample types...\n...\n...\n...")

    try:
        arcpy.SpatialJoin_analysis(ParentPath,FigSelectionPath,SpatialTmpPath,"JOIN_ONE_TO_MANY","KEEP_ALL","","INTERSECT", "", "" )
        Select_and_Append(FigSelectionPath, SpatialTmpPath, Figure_Extent_Selection_Path)
    except Exception, e:
        # If an error occurred, print line number and error message
        import traceback, sys
        tb = sys.exc_info()[2]
        print "line %i" % tb.tb_lineno
        arcpy.AddMessage("line %i" % tb.tb_lineno)
        arcpy.AddMessage(e.message)
        
    #...................................................................................................................................
    # Delete Samples - Part of the program that goes through Figure_Extent_Selection_Path and deletes user specified samples types.
    #...................................................................................................................................

    Delete_Values_From_FC(What_To_Delete_List, Fields_to_Delete, Figure_Extent_Selection, Figure_Extent_Selection_Path)
    
    print "......................................................................Runtime at the end of Part 1: ", datetime.now()-startTime  
    arcpy.AddMessage("......................................................................Runtime at the end of Part 1: " + str(datetime.now()-startTime))

    #.....................................................................................................................................................
    # PART 2
    # Part of the program that goes through the samples within the Figure Extent (Figure_Extent_Selection_Path)
    # and extracts all the points that fall inside a secondary boundary e.g. group location boundary, in each figure and saves to a standalone feature class.
    # This part of the program basically creates a sub-selection of points that fall inside the figure extent. e.g. 10 samples fall inside
    # figure extent but out of that 10, 5 fall in the location group boundary. If there is no location group boundary, just select the Figure Extent Feature Class.  
    #.....................................................................................................................................................
    print "Part 2: Selecting the locations within each figure extent that fall within the group boundary...\n...\n...\n..."
    arcpy.AddMessage("Part 2: Selecting the locations within each figure extent that fall within the group boundary...\n...\n...\n...")

    for Value in FigureList:
        arcpy.AddMessage("Working on figure...................." + str(Value))
        print "Working on figure...................." + str(Value)
        clause = buildWhereClause(Figure_Extent_Selection_Path, FigureExtent_KeyField, value)
        Select_and_Append(GroupLocationBoundarypath, Figure_Extent_Selection_Path, Group_Boundary_Selection_Path,clause)
                   
    print "......................................................................Runtime at the end of Part 2: ", datetime.now()-startTime
    arcpy.AddMessage("......................................................................Runtime at the end of Part 2: " + str(datetime.now()-startTime))

    #..............................................................................................................................
    # PART 3
    # Sample Check - Part of the program that goes through the each group of samples in the Sample Bucket FC and compares it against the 
    # Report Sample FC.
    # To find the difference between the Report Sample FC and the Sample Bucket FC, a spatial selection is performed to select samples in
    # in the sample bucket FC that intersetct the Report sample FC.  An inverse selection is performed which now selects features that were 
    # not selected in the intersection.  This selection are the new samples that will be added to the Report sample FC.   
    #..............................................................................................................................
    print "Part 3: Find New Locations in each figure...\n...\n...\n..."
    arcpy.AddMessage("Part 3: Find New Locations in each figure...\n...\n...\n...")

    #create feature class layer for the Sample Check FC
    OutputLayer_Feature_Check_Selection = Feature_Check_Selection + "_Layer"
    FL_Exist(OutputLayer_Feature_Check_Selection,Feature_Check_Selection_Path,"")
    
    try:
        #Counter for # of new locations found
        count = 0
        for value in FigureList:
            arcpy.AddMessage("Checking for new samples in figure...................." + str(value))
            print "Checking for new samples in figure...................." + str(value)
            buildWhereClause(Figure_Extent_Selection_Path, FigureExtent_KeyField, value)
            FC_Exist(TempCheck, Scratch_FDPath, ChildPath)
            count = Find_New_Features(ChildPath, Group_Boundary_Selection_Path, TempCheck_Path, Feature_Check_Selection_Path, FigureExtent_KeyField,count)
        arcpy.Delete_management(OutputLayer_Feature_Check_Selection)
        
        print "......................................................................Runtime at the end of Part 3: ", datetime.now()-startTime
        arcpy.AddMessage("......................................................................Runtime at the end of Part 3: " + str(datetime.now()-startTime))

    except Exception, e:
        # If an error occurred, print line number and error message
        import traceback, sys
        tb = sys.exc_info()[2]
        print "line %i" % tb.tb_lineno
        print e.message
        arcpy.AddMessage("line %i" % tb.tb_lineno)
        arcpy.AddMessage(e.message)

except Exception, e:
    # If an error occurred, print line number and error message
    import traceback, sys
    tb = sys.exc_info()[2]
    print "line %i" % tb.tb_lineno
    print e.message
    arcpy.AddMessage("line %i" % tb.tb_lineno)
    arcpy.AddMessage(e.message)

