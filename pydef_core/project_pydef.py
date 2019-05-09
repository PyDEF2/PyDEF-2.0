import pydef_core.cell as cc
import pydef_core.defect_study as ds
import pydef_core.basic_functions as bf
import pydef_core.figure as pf
import pydef_core.defect as dd


class PydefProject(object):

    def __init__(self, name):

        self.cells = {}  # dictionary containing VASP calculations results
        self.defects = {}  # dictionary containing defects labels
        self.defect_studies = {}  # dictionary containing defect studies
        self.material_studies = {}  # dictionary containing material studies
        self.figures = {}  # dictionary containing pydef figures

        self.ID = name  # name of the project

        self.dd_vasp = ''  # VASP data default directory
        self.dd_pydef = ''  # PyDED data default directory

    def add_object(self, obj):
        """ Add a pydef object to the project """

        typ = type(obj)
        if typ is cc.Cell:
            container = self.cells
        elif typ is dd.Defect:
            container = self.defects
        elif typ is ds.DefectStudy:
            container = self.defect_studies
        elif typ is ds.MaterialStudy:
            container = self.material_studies
        elif typ is pf.Figure:
            container = self.figures
        else:
            return

        bf.add_object_to_dict(obj, container)
