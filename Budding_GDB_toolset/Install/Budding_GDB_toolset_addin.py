import arcpy
import pythonaddins
import os
from Tkinter import Tk

rel_path = os.path.dirname(__file__)
toolbox_path = os.path.join(rel_path, r'Toolbox\Toolset.tbx')
doc_path = os.path.join(rel_path, r'Excel_Tools')
arcpy.ImportToolbox(toolbox_path)

class btn_add_features(object):
    """Implementation for Budding_GDB_toolset_addin.button_add_features (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pythonaddins.GPToolDialog(toolbox_path, 'AddNewGeometry')

class btn_add_records(object):
    """Implementation for Budding_GDB_toolset_addin.button_add_records (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pythonaddins.GPToolDialog(toolbox_path, 'AddNewRecords')

class btn_update_attrib_feat_feat(object):
    """Implementation for Budding_GDB_toolset_addin.button_update_attrib_feat_feat (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pythonaddins.GPToolDialog(toolbox_path, 'AttributeUpdateFeatureFeature')

class btn_update_attrib_feat_tbl(object):
    """Implementation for Budding_GDB_toolset_addin.button_update_attrib_feat_tbl (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pythonaddins.GPToolDialog(toolbox_path, 'AttributeUpdateFeatureTable')

class btn_update_attrib_tbl_feat(object):
    """Implementation for Budding_GDB_toolset_addin.button_update_attrib_tbl_feat (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pythonaddins.GPToolDialog(toolbox_path, 'AttributeUpdateTableFeature')

class btn_update_attrib_tbl_tbl(object):
    """Implementation for Budding_GDB_toolset_addin.button_update_attrib_tbl_tbl (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        pythonaddins.GPToolDialog(toolbox_path, 'AttributeUpdateTableTable')

class btn_xl_batch_query(object):
    """Implementation for Budding_GDB_toolset_addin.button_xl_batch_query (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        os.startfile(os.path.join(doc_path, "ArcMap Batch Definition Query.xlsm"))

class btn_xl_list_compare(object):
    """Implementation for Budding_GDB_toolset_addin.button_xl_list_compare (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        os.startfile(os.path.join(doc_path, "Dataset Comparison.xlsx"))

