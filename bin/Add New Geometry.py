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
#   12. Added a check to see if key field is present in all 3 key FC's: ReportSamples, FigureExtent, and GroupLocationBoundary. 3/3/2015
#        - Maybe add an additional check which compares and the number of unique values in the key field and if the unique values are the same across all 3 FC's?
#   13. Created an additional definition which adds specific fields of interest into the script for Reports.  Example LNAPL adds a field called Gauging_Status and ESS_ISS adds a
#       field called CM_Action_Limit. Defintion is called Report_FieldUpdate. 3/3/2015 
#   14. Added a check to look for point locations that are stacked on top of each other. 3/31/2015 
#        - Compares the number of records in the output "Locations in secondary output" and the report FC.
#        - If the number of records are the same, continue with script
#        - If the number of records are not the same, will need to create a list of locations that are not in the report FC.
#        - The additional records will be added to the InputFC1 which is the Sample_Check FC.
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

	#Calculate value for the CM Action Level Field in InputFC2
	return arcpy.CalculateField_management(fl_name, field, expression, "PYTHON_9.3")

def EmptyFC(input,workspace):
	arcpy.env.workspace = workspace
	FC_Name = input.rsplit("\\",1)
	output = FC_Name[1] + "_Layer"
	arcpy.MakeFeatureLayer_management(input, output, "", "")
	arcpy.SelectLayerByLocation_management(output, "INTERSECT", output, "", "NEW_SELECTION")
	arcpy.DeleteRows_management(output)
	arcpy.Delete_management(output)

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

def ReportFieldExist(Report_SampleFC, Figure_ExtentFC, Secondary_BoundaryFC, KeyField): 
	FC1 = arcpy.ListFields(Report_SampleFC, KeyField)
	FC2 = arcpy.ListFields(Figure_ExtentFC, KeyField)
	FC3 = arcpy.ListFields(Secondary_BoundaryFC, KeyField)
	
	FC1_cnt = len(FC1)
	FC2_cnt = len(FC2)
	FC3_cnt = len(FC3)
	
	if FC1_cnt == 1 and FC2_cnt == 1 and FC3_cnt == 1:
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

##	MasterSample = r"\\NJSOM02FS01\Projects\Projects\Chevron\DMS\GIS\Chevron Perth Amboy Geodatabase.gdb\Sample_Locations\Sample_Locations"
##	Report_Sample = r"\\NJSOM02FS01\Projects\Projects\Chevron\DMS\Projects\ISS-ESS\GIS\ESS-ISS.gdb\Report_Sample_Locations\ESS_ISS_PDI_Samples"
##	FigureExtent = r"\\NJSOM02FS01\Projects\Projects\Chevron\DMS\Projects\ISS-ESS\GIS\ESS-ISS.gdb\Figure_Extents_and_Locations_Groups\PDI_Figure_Extent"
##	GroupLocationBoundary = r"\\NJSOM02FS01\Projects\Projects\Chevron\DMS\Projects\ISS-ESS\GIS\ESS-ISS.gdb\Figure_Extents_and_Locations_Groups\ESS_ISS_PDI_Location_Group_Boundary"
##	FigureExtent_KeyField = "Figure_Area_Name" #"Area_ID"
##	Input_ScratchFD = r"\\NJSOM02FS01\Projects\Projects\Chevron\DMS\Projects\ISS-ESS\GIS\ESS-ISS Scratch Database.gdb\PDI_Model_FCs" 
##	input_figures = "SWMU 8"
##	Field_For_Delete = "Location_Type"
##	What_To_Delete_List = "'Monitoring Point';'Sludge Sample';'Post Excavation';'Sediment Sample'"

	#Sitewide Sample Location from Chevron GDB
	MasterSample = arcpy.GetParameterAsText(0)
	
	#File path for the Report Sample locatcion Feature Class
	Report_Sample = arcpy.GetParameterAsText(1)
	
	#Figure Extent FC
	FigureExtent = arcpy.GetParameterAsText(2)

	#The location boundary that is associated with the Figure Extent.
	#If no location boundary is used for Report Figures, please choose the Figure Extent Feature Class.
	GroupLocationBoundary = arcpy.GetParameterAsText(3)

	#The location boundary that is associated with the Figure Extent.
	#If no location boundary is used for Report Figures, please choose the Figure Extent Feature Class.
	FigureExtent_KeyField = arcpy.GetParameterAsText(4)

	#Input Feature Dataset in Scratch GDB
	Input_ScratchFD = arcpy.GetParameterAsText(5)

	#SQL Expression to type in the figures that need to be updated.	If all figures need to be updated, please type in '0'.
	input_figures = arcpy.GetParameterAsText(6)

	#Field that will be used to expression to delete necessary samples.  Please specify a field even if no values need to be deleted.
	Field_For_Delete = arcpy.GetParameterAsText(7)

	#SQL Expression: Select values that need to be delted. Separate each value with a ;.  If no values need to be deleted, please type in '0'.
	What_To_Delete_List = arcpy.GetParameterAsText(8)
	
	#..............................................................................................................................
	#Hard Coded Data
	#..............................................................................................................................

	#Check if there is a filepath from the input layers. If not, pre-pend the path. Also extract the FC names.
	MasterSamplepath = InputCheck(MasterSample)[0]
	MasterSampleFC = InputCheck(MasterSample)[1]
	Report_SampleFCpath = InputCheck(Report_Sample)[0]
	Report_SampleFC = InputCheck(Report_Sample)[1]
	FigureExtentpath = InputCheck(FigureExtent)[0]
	FigureExtentFC = InputCheck(FigureExtent)[1]
	GroupLocationBoundarypath = InputCheck(GroupLocationBoundary)[0]
	GroupLocationBoundaryFC = InputCheck(GroupLocationBoundary)[1]

	#Check to see if all the report feature classes have the FigureExtent Keyfield.
	if (not ReportFieldExist(Report_SampleFCpath, FigureExtentpath, GroupLocationBoundarypath, FigureExtent_KeyField)):
		arcpy.AddError("Field + KeyField + does not exist in " + Report_SampleFCpath + FigureExtentpath + GroupLocationBoundarypath + FigureExtent_KeyField)
		sys.exit()

	#Extracting File Paths for Feature Dataset and Scratch File Geodatabase
	if not split(Input_ScratchFD)[0]:
		ScratchReport_FDPath = join(arcpy.Describe(Input_ScratchFD).catalogPath,(Input_ScratchFD))
		DatasetNameSplit = ScratchReport_FDPath.rsplit("\\",1)
		DatasetName = DatasetNameSplit[1]
		ScratchGDBNameSplit = DatasetNameSplit[0].rsplit("\\",1)
		ScratchGDBName = ScratchGDBNameSplit[1]
		Scratch_GDBPath = GDBNameSplit[0]
	else:
		DatasetNameSplit = Input_ScratchFD.rsplit("\\",1)
		DatasetName = DatasetNameSplit[1]
		ScratchGDBNameSplit = DatasetNameSplit[0].rsplit("\\",1)
		ScratchGDBName = ScratchGDBNameSplit[1]
		ScratchReport_FDPath = Input_ScratchFD
		Scratch_GDBPath = ScratchGDBNameSplit[0]
	
	#Setting the file path for the Temp FC's that will be created in the Scratch GDB.
	FigSelection = DatasetName + "_FigureSelection"
	FigSelectionPath = os.path.join(ScratchReport_FDPath,FigSelection)
	SpatialTmp = DatasetName + "_SpatialJoinTemp"
	SpatialTmpPath = os.path.join(ScratchReport_FDPath,SpatialTmp)
	PointCheckTmp = DatasetName + "_Point_CheckTmp"
	PointCheckTmpPath = os.path.join(ScratchReport_FDPath,PointCheckTmp)
	InputFC2 = DatasetName + "_Main_Boundary"
	InputFCpath2 = os.path.join(ScratchReport_FDPath,InputFC2)
	InputFC0 = DatasetName + "_Secondary_Boundary"
	InputFCpath0 = os.path.join(ScratchReport_FDPath,InputFC0)
	InputFC1 = DatasetName + "_Sample_Check"
	InputFCpath1 = os.path.join(ScratchReport_FDPath,InputFC1)

	#Create the 3 Main Features Class's
	InputFC2 = FC_Exist(InputFC2, ScratchReport_FDPath, Report_SampleFCpath)
	InputFC0 = FC_Exist(InputFC0, ScratchReport_FDPath, Report_SampleFCpath)
	InputFC1 = FC_Exist(InputFC1, ScratchReport_FDPath, Report_SampleFCpath)
	
	#..............................................................................................................................
	#Clearing out the records in all feature classes
	#..............................................................................................................................

	#List comprehension which stores all the user input values in a list.
	InputFC_List = map(lambda x : x[1], filter(lambda x : x[0].startswith('InputFCpath'), globals().items()))

	#Need go through and delete records for all feature classes
	for x in xrange(3):
		#Delete all records for the following feature classes
		if InputFC_List[x] in (InputFCpath0, InputFCpath1, InputFCpath2):
			gdb_path = Scratch_GDBPath #this will have to be changed to since user input will be stored in InputFC_list
			InputLayer = InputFC_List[x]
			EmptyFC(InputLayer,gdb_path)
			print "Successfully Deleted all records in the Feature Class " + InputLayer
			arcpy.AddMessage("Successfully Deleted all records in the Feature Class " + InputLayer)
			
	print "......................................................................Runtime: ", datetime.now()-startTime
	arcpy.AddMessage("......................................................................Runtime: " + str(datetime.now()-startTime))

	#........................................................................................................................................
	#Setting up the Feature Class that stores the Figure Extent Polygons that will be updated.
	#........................................................................................................................................
	
	#Getting the number of figures to update
	FigureList=[]
	if input_figures == "0":
		if arcpy.ListFields(FigureExtentpath,FigureExtent_KeyField,"String"): #Check if the field type of the of the Figure Extent Key field is a string or not.
			Figures = ListRecords(FigureExtentpath,FigureExtent_KeyField)
			FigureList = ["'" + item.strip() + "'" for item in Figures] #List Comprehension which stripes out any spaces that show up at the begining/end of each item as well as adding single quotes at the beginning/end of each item.
			arcpy.AddMessage(str(len(FigureList)) + " Figures are going to be updated")
		else:
			FigureList = ListRecords(FigureExtentpath,FigureExtent_KeyField)
			arcpy.AddMessage(str(len(FigureList)) + " Figures are going to be updated")
	elif arcpy.ListFields(FigureExtentpath,FigureExtent_KeyField,"String"):  #Check if the field type of the of the Figure Extent Key field is a string or not.
		split = [item.strip("'") for item in input_figures.split(";")]
		FigureList = ["'" + item.strip() + "'" for item in split] #List Comprehension which adds single quotes at the beginning/end of each item in the List.
		arcpy.AddMessage(str(len(FigureList)) + " Figure(s) are going to be updated")
	else:
		FigureList = [item.strip("'") for item in input_figures.split(";")]
		arcpy.AddMessage(str(len(FigureList)) + " Figure(s) are going to be updated")

	#Make Feature Layer from Figure Extent FC
	OutputLayer_FigureExtentFC = FigureExtentFC + "_Layer" #InputLayer + "_Layer"
	FL_Exist(OutputLayer_FigureExtentFC,FigureExtentpath,"")

	#Selecting the records found the Figure list
	for field in FigureList:
		clause =  "\"" + FigureExtent_KeyField + "\" = " + str(field)
		arcpy.SelectLayerByAttribute_management(OutputLayer_FigureExtentFC,"ADD_TO_SELECTION",clause)

	#Copy all selected records to a standalone Feature Class which holds the all figure that will be updated.
	arcpy.CopyFeatures_management(OutputLayer_FigureExtentFC, os.path.join(ScratchReport_FDPath,FigSelection))
	arcpy.Delete_management(OutputLayer_FigureExtentFC)
	arcpy.AddMessage("Successfully created the Polygon Features Class, " + FigSelection + ", which is a list of figures that will be updated.")
	print "Successfully created the Polygon Features Class, " + FigSelection + ", which is a list of figures that will be updated."
	
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

		#Clear records in Point Check Temporary FC
		#EmptyFC(SpatialTmpPath, Scratch_GDBPath)

		arcpy.SpatialJoin_analysis(MasterSamplepath,FigSelectionPath,SpatialTmpPath,"JOIN_ONE_TO_MANY","KEEP_ALL","","INTERSECT", "", "" )

		#Make a Feature Layer of the Spatial Join Feature Class and Figure Selection FC
		OutputLayer_FigSelection = FigSelection + "_Layer"
		OutputLayer_SpatialTmp = SpatialTmp + "_Layer"
		FL_Exist(OutputLayer_FigSelection,FigSelectionPath,"")
		FL_Exist(OutputLayer_SpatialTmp,SpatialTmpPath,"")

		##Report_FieldUpdate(OutputLayer_SpatialTmp)
		
		#Select all features in the Figure Extent FC
		arcpy.SelectLayerByLocation_management(OutputLayer_FigSelection, "INTERSECT", OutputLayer_FigSelection, "", "NEW_SELECTION")
		#Select Features from Spatial Join that intersect the figure Extent FC
		arcpy.SelectLayerByLocation_management(OutputLayer_SpatialTmp, "INTERSECT", OutputLayer_FigSelection, "", "NEW_SELECTION")

		#Append All Features to the feature Class Bucket Figure View Holder.
		arcpy.Append_management(OutputLayer_SpatialTmp,InputFCpath2,"NO_TEST","","")

		arcpy.AddMessage("Successfully created the Features Class of samples that fall within each figure extent")
		print "Successfully created the Features Class of samples that fall within each figure extent"
		
		arcpy.Delete_management(OutputLayer_FigSelection)
		arcpy.Delete_management(OutputLayer_SpatialTmp)

	except Exception, e:
		# If an error occurred, print line number and error message
		import traceback, sys
		tb = sys.exc_info()[2]
		print "line %i" % tb.tb_lineno
		arcpy.AddMessage("line %i" % tb.tb_lineno)
		arcpy.AddMessage(e.message)
		
	#...................................................................................................................................
	# Delete Samples - Part of the program that goes through InputFCpath2 and deletes user specified samples types.
	#...................................................................................................................................

	OutputLayer_InputFC2 = str(InputFC2) + "_Layer"
	FL_Exist(OutputLayer_InputFC2,InputFCpath2,"")

	What_to_Delete = []

	if What_To_Delete_List == "0":
		print "No sample types were selected to be deleted"
		arcpy.AddMessage("No sample types were selected to be deleted")
	else:
		What_to_Delete = What_To_Delete_List.split(";")
		print "The following values are going to be deleted: "
		print What_to_Delete
		arcpy.AddMessage("The following values are going to be deleted: ")
		arcpy.AddMessage(What_to_Delete)
		for field in What_to_Delete:
			arcpy.AddMessage("Deleting the following from " + InputFC2 + ": " + str(field))
			CalcField_Expression = "\"" + Field_For_Delete + "\" = " + str(field)
			arcpy.SelectLayerByAttribute_management(OutputLayer_InputFC2, "NEW_SELECTION", CalcField_Expression)
			arcpy.DeleteRows_management(OutputLayer_InputFC2)

	arcpy.Delete_management(OutputLayer_InputFC2)
	
	print "......................................................................Runtime at the end of Part 1: ", datetime.now()-startTime  
	arcpy.AddMessage("......................................................................Runtime at the end of Part 1: " + str(datetime.now()-startTime))

	#.....................................................................................................................................................
	# PART 2
	# Part of the program that goes through the samples within the Figure Extent (InputFCpath2)
	# and extracts all the points that fall inside a secondary boundary e.g. group location boundary, in each figure and saves to a standalone feature class.
	# This part of the program basically creates a sub-selection of points that fall inside the figure extent. e.g. 10 samples fall inside
	# figure extent but out of that 10, 5 fall in the location group boundary. If there is no location group boundary, just select the Figure Extent Feature Class.  
	#.....................................................................................................................................................
	print "Part 2: Selecting the locations within each figure extent that fall within the secondary boundary...\n...\n...\n..."
	arcpy.AddMessage("Part 2: Selecting the locations within each figure extent that fall within the secondary boundary...\n...\n...\n...")

	#create Feature layer.  This needs to be created before the for loop so records can continuously be appended for each figure.
	OutputLayer_InputFC0 = InputFC0 + "_Layer"
	FL_Exist(OutputLayer_InputFC0,InputFCpath0,"")

	for Value in FigureList:
		arcpy.AddMessage("Working on figure...................." + str(Value))
		print "Working on figure...................." + str(Value)

		#Making feature layers from input FC's
		OutputLayer_InputFC2 = InputFC2 + "_Layer" 
		OutputLayer_GroupLocationBoundary = GroupLocationBoundaryFC + "_Layer"
		Feature_Layer_Expression = "\"" + FigureExtent_KeyField + "\" = " + str(Value)
		FL_Exist(OutputLayer_InputFC2,InputFCpath2, Feature_Layer_Expression)
		FL_Exist(OutputLayer_GroupLocationBoundary,GroupLocationBoundarypath, Feature_Layer_Expression)

		arcpy.AddMessage("Made feature layers for " + InputFC2 + " and " + GroupLocationBoundaryFC)
		print "Made feature layers for " + InputFC2 + " and " + GroupLocationBoundaryFC
			
		#Select all features in the Group Location Boundary FC
		arcpy.SelectLayerByLocation_management(OutputLayer_GroupLocationBoundary, "INTERSECT", OutputLayer_GroupLocationBoundary, "", "NEW_SELECTION")
		#Select Features from InputFC2 that intersect the Figure Extent FC
		arcpy.SelectLayerByLocation_management(OutputLayer_InputFC2, "INTERSECT", OutputLayer_GroupLocationBoundary, "", "NEW_SELECTION")
		arcpy.AddMessage("Selecting records that fall inside " + GroupLocationBoundaryFC)
		print "Selecting records that fall inside " + GroupLocationBoundaryFC
		
		#Append All Features to the feature Class Bucket Figure View Holder.
		arcpy.Append_management(OutputLayer_InputFC2, OutputLayer_InputFC0,"NO_TEST","","")
		arcpy.AddMessage("Added locations that fall inside " + GroupLocationBoundaryFC + " to " + InputFC0)
		print "Added locations that fall inside " + GroupLocationBoundaryFC + " to " + InputFC0

	#Delete Feature Layers		
	arcpy.Delete_management(OutputLayer_InputFC2)
	arcpy.Delete_management(OutputLayer_GroupLocationBoundary)
	arcpy.Delete_management(OutputLayer_InputFC0)
	
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
	OutputLayer_InputFC1 = InputFC1 + "_Layer"
	FL_Exist(OutputLayer_InputFC1,InputFCpath1,"")

	#Temporary FC that will be used to store new locations found in each figure.
	arcpy.CreateFeatureclass_management(ScratchReport_FDPath, PointCheckTmp, "POINT", InputFCpath2, "SAME_AS_TEMPLATE", "SAME_AS_TEMPLATE", MasterSamplepath)

	#Counter for # of new locations found
	count1 = 0
	
	try:
	
		for Value in FigureList:
			arcpy.AddMessage("Checking for new samples in figure...................." + str(Value))
			print "Checking for new samples in figure...................." + str(Value)
			
			#Clear records in Point Check Temporary FC
			EmptyFC(PointCheckTmpPath, Scratch_GDBPath)
			
			#Make Feature Layer output names for all FC of interest and then run make feature layer tool
			Feature_Layer_Expression = "\"" + FigureExtent_KeyField + "\" = " + str(Value)
			OutputLayer_PointCheckTmp = PointCheckTmp + "_Layer"
			OutputLayer_InputFC0 = InputFC0 + "_Layer"
			OutputLayer_Report_SampleFC = Report_SampleFC + "_Layer"
			FL_Exist(OutputLayer_PointCheckTmp, PointCheckTmpPath, Feature_Layer_Expression)
			FL_Exist(OutputLayer_InputFC0, InputFCpath0, Feature_Layer_Expression)
			FL_Exist(OutputLayer_Report_SampleFC, Report_SampleFCpath, Feature_Layer_Expression)

			arcpy.AddMessage("Made feature layers for " + PointCheckTmp + ", " + InputFC0 + " and " + Report_SampleFC)
			print "Made feature layers for " + PointCheckTmp + ", " + InputFC0 + " and " + Report_SampleFC

			#Select all features in the in bucket layer and append to temporary point check FC
			arcpy.SelectLayerByLocation_management(OutputLayer_InputFC0, "INTERSECT", OutputLayer_InputFC0, "", "NEW_SELECTION")
			arcpy.Append_management(OutputLayer_InputFC0, OutputLayer_PointCheckTmp,"NO_TEST","","")
			# Not sure if it is needed, but add a field called "Selected Features" and update records with either yes or no.
			# It gives me the ability to sort and select features based on this field.  May be useful to for certain situations where
			# a new location is on an already exisiting location in the Report Sample Location FC.  
		
			#Select all samples in the Report Sample FC
			arcpy.SelectLayerByLocation_management(OutputLayer_Report_SampleFC, "INTERSECT", OutputLayer_Report_SampleFC, "", "NEW_SELECTION")
			#Select Features from Bucket FC that intersect the Report Sample FC
			arcpy.SelectLayerByLocation_management(OutputLayer_PointCheckTmp, "INTERSECT", OutputLayer_Report_SampleFC, "", "NEW_SELECTION")
			#Invert Selection
			arcpy.SelectLayerByLocation_management(OutputLayer_PointCheckTmp, "INTERSECT", OutputLayer_PointCheckTmp, "", "SWITCH_SELECTION")
			arcpy.AddMessage("Selecting the new records that fall inside the figure")
			print "Selecting the new records that fall inside the figure"
			
			#Append selected features to Report Sample Location FC
			arcpy.Append_management(OutputLayer_PointCheckTmp, OutputLayer_InputFC1,"NO_TEST","","")
			count2 = int(arcpy.GetCount_management(OutputLayer_InputFC1).getOutput(0))
			print "Number of new locations found in the figure: " + str(count2 - count1)
			arcpy.AddMessage("Number of new locations found in the figure: " + str(count2 - count1))
			arcpy.AddMessage("Added the new locations to " + InputFC1)
			print "Added the new locations to " + InputFC1
			count1 = count2

			#Search for locations that are intersect existing points.
			FigureGeometryCheck(OutputLayer_Report_SampleFC,OutputLayer_InputFC0,OutputLayer_InputFC1,Feature_Layer_Expression)
			
			#Delete Feature Layers
			arcpy.Delete_management(OutputLayer_PointCheckTmp)
			arcpy.Delete_management(OutputLayer_InputFC0)
			arcpy.Delete_management(OutputLayer_Report_SampleFC)

		arcpy.Delete_management(OutputLayer_InputFC1)
		
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

