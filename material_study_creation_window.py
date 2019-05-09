"""
    Project Manager in PyDEF GUI
    version: 2.0
    author: Adrien Stoliaroff
    email: adrien.stoliaroff@cnrs-imn.fr
"""

import tkinter as tk
from tkinter import Tk, Frame, Menu, Button, Label
from tkinter import LEFT, RIGHT, TOP, BOTTOM, X, FLAT, RAISED, BOTH, END, SUNKEN, ALL

import tkinter_utilities as tu

import pydef_core.defect_study as ds
import pydef_core.basic_functions as bf

class MaterialStudyCreationWindow(tk.Toplevel):
    
    def plot(self, close=False):
        self.mainwindow.plot()
        if close:
            self.cancel()
    
    def cancel(self):
        self.mainwindow.focus_set()
        self.destroy()

    def __init__(self, mainwindow, project, material_study_to_edit):

        tk.Toplevel.__init__(self, mainwindow)
        self.mainwindow = mainwindow
        self.title('Material Study Creation Window')
        self.width=self.winfo_width()
        self.height=self.winfo_height()
        self.material_study = material_study_to_edit

        self.main_frame = tk.Frame(self)
        self.main_frame.pack(expand=True, fill='both')
        self.project = project
        
        if self.material_study is None:
            self.edit = False
        else:
           self.edit = True 

        if project.hostcellid == '':
            self.mainwindow.printerror('Current project has no host cell! Please declare the perfect cell as host before creating any Material Study.')
            
        items = [defstud.treetitle for defstud in list(self.project.defect_studies.values())]
        
        if self.material_study is not None:    
            label_on = self.material_study.treetitle + ' Defect Studies' 
            items_on = [defect_study.treetitle for defect_study in list(self.material_study.defect_studies.values())]
        else:
            label_on = 'New Material Study\'s Defect Studies' 
            items_on = []
        label_off = self.project.name + ' Defect Studies'
        labeltitle = tk.Label(self.main_frame, text='Defect Studies choice')
        
        self.defect_studies_choice_frame = tu.ItemsChoiceFrame(self.main_frame, items, items_on, label_on, label_off, labeltitle)
        
        # ------------------  NAVIGATION BUTTONS  ----------------------
        
        def validate(close=False):
            self.attributes('-topmost', True)
            ds_choice = self.defect_studies_choice_frame.get_choice()
            find_ds_to_add = [def_study for title in ds_choice for def_study in list(self.mainwindow.projects[self.mainwindow.currentprojectid].defect_studies.values()) if def_study.treetitle == title]
            if len(ds_choice) == 0:
                find_ds_to_remove = [def_study for def_study in list(self.material_study.defect_studies.values())]
            else:
                find_ds_to_remove = [def_study for def_study in list(self.material_study.defect_studies.values()) if def_study.treetitle not in ds_choice]
            if self.edit is False:
                rfind_ds = find_ds_to_add[1:]
                self.material_study = ds.MaterialStudy(find_ds_to_add[0])
                for def_study in rfind_ds:
                    self.material_study.add_defect_study(def_study)
                # insert in tree
                self.mainwindow.pm.new_material_study(self.material_study, self.project.pid)                
            else:
                for def_study in find_ds_to_add:
                    print('Adding defect study ' + def_study.treetitle + ' to Material Study ' + self.material_study.treetitle)
                    self.mainwindow.pm.add_defect_study_to_material_study(def_study, self.material_study, self.project.pid)
                for def_study in find_ds_to_remove:
                    self.mainwindow.pm.remove_defect_study_to_material_study(def_study, self.material_study, self.project.pid)
            if len(self.material_study.defect_studies)>0:
                self.plot(close=close)
            else:
                print('Warning! Impossible to plot Defect Formation Energies for empty Material Study ' + self.material_study.treetitle)
                if close :
                    self.cancel()

        self.button_pane = tk.Frame(self.main_frame, bd = 2, pady = 10)
        self.apply_button = Button(self.button_pane, text = 'Apply', command=validate)
        self.next_button = Button(self.button_pane, text = 'OK', command=lambda: validate(close=True))
        self.cancel_button = Button(self.button_pane, text = 'Cancel', command=self.cancel)
        self.apply_button.grid(row = 0, column = 0)
        self.next_button.grid(row = 0, column = 1)
        self.cancel_button.grid(row = 0, column = 2)

        self.defect_studies_choice_frame.pack(expand=True, fill='y')
        self.button_pane.pack(side=BOTTOM, expand=True, fill='y')
        
        tu.centre_window(self)
        
