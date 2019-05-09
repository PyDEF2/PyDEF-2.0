import tkinter as tk
from tkinter import Tk, Frame, Menu, Button, Label, Canvas, Scrollbar
from tkinter import LEFT, RIGHT, TOP, BOTTOM, X, FLAT, RAISED, BOTH, END, SUNKEN, ALL, VERTICAL, W

import copy

import tkinter.ttk
from tkinter.colorchooser import askcolor              

import tkinter_utilities as tu

import pydef_core.basic_functions as bf
import pydef_core.cell as cc
import pydef_core.defect as pd
import pydef_core.defect_study as ds


class DefectStudyPlotParametersWindow(tk.Toplevel):
    
    def __init__(self, mainwindow, defect_study):

        tk.Toplevel.__init__(self, mainwindow)
        self.resizable(False, False)
        
        self.mainwindow = mainwindow
        self.project = self.mainwindow.projects[self.mainwindow.currentprojectid]
        self.fpp = defect_study.fpp

        self.main_frame = tkinter.ttk.Frame(self)
        self.main_frame.pack(expand=True, fill='both')
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.title(defect_study.treetitle + ' Formation Energy Plot Parameters Edition Window')
        
        # ---------------------------------------------- FPP PARAMS ------------------------------------------------
        
        self.label0 = tk.Label(self.main_frame, text='Formation Energy Plot Specific Parameters', font='-weight bold')
        self.fpp_param_frame = tkinter.ttk.LabelFrame(self.main_frame, labelwidget=self.label0)
        self.fpp_param_frame.grid(sticky='nsew')
        
        self.display_transition_levels_var = tk.BooleanVar(value=self.fpp.display_transition_levels)
        tkinter.ttk.Checkbutton(self.fpp_param_frame, text='Display Transition Levels', variable=self.display_transition_levels_var, onvalue=True, offvalue=False).grid(row=0, column=1, sticky=W)
        
        self.display_charges_var = tk.BooleanVar(value=self.fpp.display_charges)
        tkinter.ttk.Checkbutton(self.fpp_param_frame, text='Display Charges', variable=self.display_charges_var, onvalue=True, offvalue=False).grid(row=1, column=1, sticky=W)
                
        # ---------------------------------------------- DISPLAY PARAMS ------------------------------------------------
        
        self.display_param = tu.DisplayParametersFrame(self.main_frame, 'Position in the gap', 'Formation energy', self.fpp)
        self.display_param.frame.grid(row=2, column=0, pady=3, sticky='nsew')
        
        # --------------------------------------------------- BUTTONS --------------------------------------------------

        buttons_frame = tkinter.ttk.Frame(self.main_frame)
        buttons_frame.grid(row=3, column=0, pady=3, sticky='nsew')

        tkinter.ttk.Button(buttons_frame, text='Apply', command=self.save).grid(row=0, column=0, padx=5)
        tkinter.ttk.Button(buttons_frame, text='OK', command=lambda: self.save(close=True)).grid(row=0, column=1, padx=5)
        tkinter.ttk.Button(buttons_frame, text='Cancel', command=self.destroy).grid(row=0, column=2, padx=5)
        
    def save(self, close=False):
        try:
            self.fpp.display_transition_levels = self.display_transition_levels_var.get()
            self.fpp.display_charges = self.display_charges_var.get()
            self.display_param.write_in_pp(self.fpp)
            # plot Defect Formation Energy 
            self.mainwindow.plot()
            self.attributes('-topmost', True)
            if close:
                self.destroy()
        except ValueError:
            print('Warning! Please specify range values as float values')
            
            
class MaterialStudyPlotParametersWindow(tk.Toplevel):
    
    def __init__(self, mainwindow, material_study):

        tk.Toplevel.__init__(self, mainwindow)
        self.resizable(False, False)
        
        self.mainwindow = mainwindow
        self.project = self.mainwindow.projects[self.mainwindow.currentprojectid]
        self.fpp = material_study.lastfpp

        self.main_frame = tkinter.ttk.Frame(self)
        self.main_frame.pack(expand=True, fill='both')
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.title(material_study.treetitle + ' Defect Formation Energies Plot Parameters Edition Window')
        
        # --------------------------------------------------- FPP name -------------------------------------------------
        
        self.label0 = tk.Label(self.main_frame, text='Plot Parameters Name', pady=10)
        
        self.nameframe = tk.Frame(self.main_frame)
        self.nameframe.grid(row=1, column=0)
        namelist = [fpp.name for fpp in list(self.project.pp['fpp'].values())]
        self.fppname = tkinter.ttk.Combobox(self.nameframe, values=namelist, width=40) 
        self.fppname.set(self.fpp.name)
        self.fppname.bind("<<ComboboxSelected>>", self.fpp_select)
        self.label0.grid(row=0, column=0)
        self.fppname.grid(row=1, column=0)
        tk.Button(self.nameframe, text='Save as new parameters', command=self.fpp_create).grid(row=1, column=1)
        
        # ---------------------------------------------- FPP PARAMS ------------------------------------------------
        
        self.label0 = tk.Label(self.main_frame, text='Formation Energy Plot Specific Parameters', font='-weight bold')
        self.fpp_param_frame = tkinter.ttk.LabelFrame(self.main_frame, labelwidget=self.label0)
        self.fpp_param_frame.grid(sticky='nsew')
        
        self.display_charges_var = tk.BooleanVar(value=self.fpp.display_charges)
        tkinter.ttk.Checkbutton(self.fpp_param_frame, text='Display Charges', variable=self.display_charges_var, onvalue=True, offvalue=False).grid(row=0, column=1, sticky=W)
        
        self.highlight_charge_change_var = tk.BooleanVar(value=self.fpp.highlight_charge_change)
        tkinter.ttk.Checkbutton(self.fpp_param_frame, text='Highlight Charge Transition Levels', variable=self.highlight_charge_change_var, onvalue=True, offvalue=False).grid(row=1, column=1, sticky=W)
        
        self.display_gaps_legend_var = tk.BooleanVar(value=self.fpp.display_gaps_legend)
        tkinter.ttk.Checkbutton(self.fpp_param_frame, text='Display Gap Legend', variable=self.display_gaps_legend_var, onvalue=True, offvalue=False).grid(row=2, column=1, sticky=W)
                
        # ---------------------------------------------- DISPLAY PARAMS ------------------------------------------------
        
        self.display_param = tu.DisplayParametersFrame(self.main_frame, 'Position in the gap', 'Formation energy', self.fpp)
        self.display_param.frame.grid(row=3, column=0, pady=3, sticky='nsew')
        
        # ---------------------------------------------- COLORS ------------------------------------------------
        self.label2 = tk.Label(self.main_frame, text='Colors', font='-weight bold')
        self.colors_pane = tkinter.ttk.LabelFrame(self.main_frame, labelwidget=self.label2)
        self.colors = {}
        index = 0 
        for def_stud in material_study.ds_list:
            self.colors[def_stud.ID] = tk.Button(self.colors_pane, text='\t\t', bg=self.fpp.colors[def_stud.ID], command=lambda port = def_stud.ID: self.set_color(port))
            self.colors[def_stud.ID].grid(row=index, column=0, sticky='w')
            tk.Label(self.colors_pane, text=def_stud.treetitle).grid(row=index, column=1, sticky='w')
            index += 1
            
        self.colors_pane.grid(row=4, column=0, pady=3, sticky='nsew')
        
        # --------------------------------------------------- BUTTONS --------------------------------------------------

        buttons_frame = tkinter.ttk.Frame(self.main_frame)
        buttons_frame.grid(row=5, column=0, pady=3, sticky='nsew')

        tkinter.ttk.Button(buttons_frame, text='Apply', command=self.save).grid(row=0, column=0, padx=5)
        tkinter.ttk.Button(buttons_frame, text='OK', command=lambda: self.save(close=True)).grid(row=0, column=1, padx=5)
        tkinter.ttk.Button(buttons_frame, text='Cancel', command=self.destroy).grid(row=0, column=2, padx=5)
        
    
    def set_color(self, def_stud_ID):
        self.fpp.colors[def_stud_ID] = askcolor(parent=self)[1]
        self.colors[def_stud_ID].configure(bg=self.fpp.colors[def_stud_ID])
        

    def save(self, close=False):
        try:
            self.display_param.write_in_pp(self.fpp)
            # plot Defect Formation Energies 
            self.mainwindow.plot()
            self.attributes('-topmost', True)
            if close:
                self.destroy()
        except ValueError:
            print('Warning! Please specify range values as float values')
    
    
    def update_window(self):
        self.display_param.update_frame(self.fpp)
        self.display_param.xlim_frame.low_var.set(self.fpp.xmin)
        self.display_param.xlim_frame.high_var.set(self.fpp.xmax)
        self.display_param.ylim_frame.low_var.set(self.fpp.ymin)
        self.display_param.ylim_frame.high_var.set(self.fpp.ymax)
        self.display_charges_var = self.fpp.display_charges
        self.highlight_charge_change_var = self.fpp.highlight_charge_change
        self.display_gaps_legend_var = self.fpp.display_gaps_legend
        for key in list(self.fpp.colors.keys()):
            self.colors[key].configure(bg=self.fpp.colors[key])

            
    def fpp_select(self, event=None):
        try:
            self.fpp = self.project.pp['fpp'][self.fppname.get()]
            self.mainwindow.projects[self.mainwindow.currentprojectid].cells[self.mainwindow.currentitemid].lastfpp = self.fpp
            self.update_window()
        except KeyError:
            print('Please select existing parameters in the list or create new ones with the button')
    
    
    def fpp_create(self, event=None):
        newfpp = copy.deepcopy(self.fpp)
        newfpp.name = self.fppname.get()
        self.project.pp['fpp'][self.fppname.get()] = newfpp
        self.fpp = newfpp 
        self.mainwindow.projects[self.mainwindow.currentprojectid].material_studies[self.mainwindow.currentitemid].lastfpp = newfpp
        namelist = [fpp.name for fpp in list(self.project.pp['fpp'].values())]
        self.fppname.configure(values=namelist)
        print('Created new Defect Formation Energies Plot Parameters ' + self.fpp.name + ' in Project ' + self.mainwindow.projects[self.mainwindow.currentprojectid].name)


    def save(self, close=False):

        self.fpp.name = self.fppname.get()
        try:
            self.display_param.write_in_pp(self.fpp)
            
            self.fpp.display_charges = self.display_charges_var.get()
            self.fpp.highlight_charge_change = self.highlight_charge_change_var.get()
            self.fpp.display_gaps_legend = self.display_gaps_legend_var.get()
            
            # plot Defect Formation Energies
            self.mainwindow.plot()
            self.attributes('-topmost', True)
            
            if close:
                self.destroy()
        except ValueError:
            print('Warning! Please specify range values as float values')
            
            
class MaterialStudyExportWindow(tk.Toplevel):

    def __init__(self, mainwindow):
        tk.Toplevel.__init__(self, mainwindow)
        self.resizable(False, False)

        self.main_frame = tk.Frame(self)
        self.main_frame.grid(sticky='nsew')
        self.choice = tk.StringVar()
        tk.Label(self.main_frame, text='Export ').grid(row=0, column=0)
        # tk.Radiobutton(self.main_frame, value='Defect formation energies', 
        # variable=self.choice, text='Defect formation energies', tristatevalue='x').grid(sticky='w')
        tk.Radiobutton(self.main_frame, value='Defect Concentrations', variable=self.choice, 
        text='Defect Concentrations', tristatevalue='x').grid(sticky='w')
        tk.Radiobutton(self.main_frame, value='Charge Carriers Concentrations', variable=self.choice, 
        text='Charge Carriers Concentrations', tristatevalue='x').grid(sticky='w')
        tk.Radiobutton(self.main_frame, value='Fermi Level Variations', variable=self.choice, 
        text='Fermi Level Variations', tristatevalue='x').grid(sticky='w')
        tk.Button(self.main_frame, text='OK', command=self.validate).grid(sticky='e')
        
    def validate(self):
        choice = self.choice.get()
        self.destroy()
        return choice


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
                if self.material_study is not None:
                    find_ds_to_remove = [def_study for def_study in list(self.material_study.defect_studies.values()) if def_study.treetitle not in ds_choice]
                else:
                    find_ds_to_remove = []
            if self.edit is False:
                self.material_study = ds.MaterialStudy(*find_ds_to_add) 
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
        
        
class SummaryWindow(tk.Toplevel):
    
    def __init__(self, mainwindow, material_study):
        tk.Toplevel.__init__(self, mainwindow)
        
        self.title(material_study.treetitle + ' summary')
        self.maxsize(width=self.winfo_screenwidth(), height=3*self.winfo_screenheight()/5)
        self.mainwindow = mainwindow

        self.main_frame = tk.Frame(self)
        self.main_frame.grid(sticky='nsew')
        
        summary = material_study.summary()
        
        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = tkinter.ttk.Scrollbar(self.main_frame, orient=VERTICAL)
        # vscrollbar.pack(fill='y', side=RIGHT, expand=False)
        vscrollbar.grid(row=0, column=1, sticky = 'nse')
        canvas = tk.Canvas(self.main_frame, bd=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set)
        # canvas.pack(side=LEFT, fill='both', expand=True)
        canvas.grid(row=0, column=0, sticky = 'nsew')
        vscrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor='nw')

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)
        
        nrows = len(summary)
        if nrows >0:
            i = -1 
            for line in summary:
                i += 1
                j = -1
                for tablecell in line:
                    j += 1
                    color = 'white'
                    if i == 0:
                        color = 'grey'
                    else:
                        try:
                            if float(tablecell) > 0:
                                color = 'pale turquoise'
                            elif float(tablecell) < 0:
                                color = 'peach puff'
                        except ValueError:
                            pass
                    tk.Label(self.interior, text=str(tablecell), relief="ridge", bg=color, padx=2, font = ('', 16, '')).grid(row=i, column=j, sticky ='nsew')
        
        tk.Button(self.main_frame, text='OK', command=self.cancel).grid()
    
    def cancel(self):
        self.mainwindow.focus_set()
        self.destroy()


class MaterialStudyEnergyPlotParametersWindow(tk.Toplevel):

    def __init__(self, parent, material_study, fpp):

        tk.Toplevel.__init__(self, parent)

        self.material_study = material_study
        self.fpp = fpp

        self.main_frame = tkinter.ttk.Frame(self)
        self.main_frame.pack(expand=True, fill='both')
        self.main_frame.grid_columnconfigure(0, weight=1)

        tkinter.ttk.Label(self.main_frame, text=material_study.treetitle, font='-weight bold -size 30').grid(padx=20, pady=20)

        # Energy range
        self.e_range = tu.RangeFrame(self.main_frame, fpp.energy_range[0], fpp.energy_range[1], 'Fermi energy', 'eV', width=7)
        self.e_range.grid(sticky=W, padx=5, pady=5)

        # Transition levels highlight
        self.tr_levels_var = tk.BooleanVar(value=fpp.highlight_charge_change)
        tkinter.ttk.Checkbutton(self.main_frame, text='Highlight transition levels', onvalue=True, offvalue=False,
                        var=self.tr_levels_var).grid(sticky=W, padx=5, pady=5)

        # Charge display
        self.charge_display_var = tk.BooleanVar(value=fpp.display_charges)
        tkinter.ttk.Checkbutton(self.main_frame, text='Show charges', onvalue=True, offvalue=False, var=self.charge_display_var
                        ).grid(sticky=W, padx=5, pady=5)

        # Colors
        self.color_choice = None
        tkinter.ttk.Button(self.main_frame, text='Colours', command=self.open_color_choice
                   ).grid(sticky=W, padx=5, pady=5)

        # Gap legend display
        self.gap_var = tk.BooleanVar(value=fpp.display_gaps_legend)
        tkinter.ttk.Checkbutton(self.main_frame, text='Show charges', onvalue=True, offvalue=False, var=self.gap_var
                        ).grid(sticky=W, padx=5, pady=5)

        # --------------------------------------------------- BUTTONS --------------------------------------------------

        buttons_frame = tkinter.ttk.Frame(self.main_frame)
        buttons_frame.grid(pady=5, padx=5)

        tkinter.ttk.Button(buttons_frame, text='OK', command=self.validate).pack(side='left', padx=5)
        tkinter.ttk.Button(buttons_frame, text='Cancel', command=self.destroy).pack(side='left', padx=5)

    def open_color_choice(self):

        items = [d.ID for d in self.material_study.ds_list]
        window = tu.ColoursChoiceWindow(self, items, self.fpp.lines_colors, 'color_choice')
        window.grab_set()
        self.wait_window(window)
        window.grab_release()

    def validate(self):

        e_low = tu.get_var(self.e_range.low_var, 'Fermi energy must be a number')
        e_high = tu.get_var(self.e_range.high_var, 'Fermi energy must be a number')
        self.fpp.energy_range = [e_low, e_high]
        self.fpp.highlight_charge_change = self.tr_levels_var.get()
        self.fpp.display_charges = self.charge_display_var.get()
        self.fpp.display_gaps_legend = self.gap_var.get()

        self.destroy()


class ConcentrationsPlotParametersWindow(tk.Toplevel):

    def __init__(self, mainwindow, material_study):
        
        tk.Toplevel.__init__(self, mainwindow)
        
        self.mainwindow = mainwindow
        
        self.material_study = material_study

        self.cpp = material_study.cpp

        self.main_frame = tkinter.ttk.Frame(self)
        self.main_frame.grid(sticky='nsew')
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.title(material_study.treetitle + ' Defect Concentrations Plot Parameters Window')
        
        # --------------------------------------------- EFFECTIVE MASSE --------------------------------------------------

        label0 = tk.Label(self.main_frame, text='Charge Carriers Effective Masses', font='-weight bold')
        masses_frame = tkinter.ttk.LabelFrame(self.main_frame, labelwidget=label0)
        masses_frame.grid(sticky='nsew')
        
        self.m_e_entry = tu.QuantityEntry(masses_frame, 'Electrons effective mass', self.cpp.m_e, ' me', width=5)
        self.m_e_entry.pack(padx=5, pady=5)
        self.m_h_entry = tu.QuantityEntry(masses_frame, 'Holes effective mass', self.cpp.m_h, ' me', width=5)
        self.m_h_entry.pack(padx=5, pady=5)

        # --------------------------------------------- TEMPERATURES --------------------------------------------------

        label1 = tk.Label(self.main_frame, text='Temperatures', font='-weight bold')
        temperature_frame = tkinter.ttk.LabelFrame(self.main_frame, labelwidget=label1)
        temperature_frame.grid()

        tk.Label(temperature_frame, text='Ambiant Temperature (fixed) ').grid(row=0, column=0)
        self.cte_temp = tu.QuantityEntry(temperature_frame, '', self.cpp.temperature, 'K', width=7)
        self.cte_temp.grid(row=0, column=1)

        self.temp_range = tu.RangeFrame(temperature_frame, self.cpp.xmin, self.cpp.xmax, 'Growth Temperature', 'K', step=self.cpp.dt, width=7)
        self.temp_range.grid(row=1, column=0, columnspan=2, pady=5, padx=5)
        
        # --------------------------------------------- SPECIFIC OPTIONS --------------------------------------------------
        self.charge_carriers_var = tk.BooleanVar(value=self.cpp.charge_carriers)
        self.fill_type_var = tk.IntVar(value=self.cpp.fill_type)
        
        label11 = tk.Label(self.main_frame, text='Specific options', font='-weight bold')
        options_frame = tkinter.ttk.LabelFrame(self.main_frame, labelwidget=label11)
        options_frame.grid(sticky='nsew')
        
        # Display charge carriers
        tkinter.ttk.Checkbutton(options_frame, text='Display charge carriers concentrations ', variable=self.charge_carriers_var, command=self.set_display_charge_carriers).pack(side='left')
        # Fill conductivity type
        tkinter.ttk.Checkbutton(options_frame, text='Fill conductivity type ', variable=self.fill_type_var, command=self.set_fill_type).pack(side='left')
        
        # ---------------------------------------------- DISPLAY PARAMS ------------------------------------------------
        
        self.display_param = tu.DisplayParametersFrame(self.main_frame, 'Growth Temperature', 'Defect Concentrations', self.cpp)
        self.display_param.frame.grid(row=3, column=0, pady=3, sticky='nsew')
        
        # ---------------------------------------------- COLORS ------------------------------------------------
        self.label2 = tk.Label(self.main_frame, text='Colors', font='-weight bold')
        self.colors_pane = tkinter.ttk.LabelFrame(self.main_frame, labelwidget=self.label2)
        self.colors = {}
        self.labels = {}
        self.index = 0 
        
        def title(key):
            if key in ['n (electrons)', 'n (holes)', 'n type', 'p type']:
                return key
            else:
                return self.material_study.defect_studies[key].treetitle
        sort_list = [[key, title(key)] for key in list(self.cpp.colors.keys())]
        sort_list.sort(key=lambda x: x[1])
        
        for key, treetitle in sort_list:
            if key in self.cpp.data_id or (key in ['n type', 'p type'] and self.cpp.fill_type):
                self.colors[key] = tk.Button(self.colors_pane, text='\t\t', bg=self.cpp.colors[key], command=lambda port = key: self.set_color(port))
                self.colors[key].grid(row=self.index, column=0, sticky='w')
                self.labels[key] =  tk.Label(self.colors_pane, text=treetitle)
                self.labels[key].grid(row=self.index, column=1, sticky='w')
                self.index += 1
            
        self.colors_pane.grid(row=4, column=0, pady=3, sticky='nsew')
        
        # --------------------------------------------------- BUTTONS --------------------------------------------------

        buttons_frame = tkinter.ttk.Frame(self.main_frame)
        buttons_frame.grid(row=5, column=0, pady=3, sticky='nsew')

        tkinter.ttk.Button(buttons_frame, text='Apply', command=self.save).grid(row=0, column=0, padx=5)
        tkinter.ttk.Button(buttons_frame, text='OK', command=lambda: self.save(close=True)).grid(row=0, column=1, padx=5)
        tkinter.ttk.Button(buttons_frame, text='Cancel', command=self.destroy).grid(row=0, column=2, padx=5)
    
    def set_display_charge_carriers(self):
        self.cpp.charge_carriers = self.charge_carriers_var.get()
        if self.cpp.charge_carriers:
            for key in ['n (electrons)', 'n (holes)']:
                self.colors[key] = tk.Button(self.colors_pane, text='\t\t', bg=self.cpp.colors[key], command=lambda port = key: self.set_color(port))
                self.colors[key].grid(row=self.index, column=0, sticky='w')
                self.labels[key] = tk.Label(self.colors_pane, text=key)
                self.labels[key].grid(row=self.index, column=1, sticky='w')
                self.index += 1
            self.cpp.data_id += ['n (electrons)', 'n (holes)']
        else:
            for key in ['n (electrons)', 'n (holes)', 'n type', 'p type']:
                try:
                    self.colors[key].grid_forget()
                    self.labels[key].grid_forget()
                    self.colors.pop(key)
                    self.labels.pop(key)                    
                    self.index -= 1
                except KeyError:
                    pass
            self.fill_type_var.set(False)
            self.cpp.fill_type = False
            temp = [self.cpp.data_id[i] for i in range(0, len(self.cpp.data_id)) if self.cpp.data_id[i] not in ['n (electrons)', 'n (holes)']]
            self.cpp.data_id = temp
    
    def set_fill_type(self):
        self.cpp.fill_type = self.fill_type_var.get()
        if self.cpp.fill_type:
            if not self.cpp.charge_carriers:
                self.cpp.charge_carriers = True
                self.charge_carriers_var.set(True)
                self.cpp.data_id += ['n (electrons)', 'n (holes)']
            for key in ['n (electrons)', 'n (holes)', 'n type', 'p type']:
                self.index += 1
                if key not in list(self.colors.keys()):
                    self.colors[key] = tk.Button(self.colors_pane, text='\t\t', bg=self.cpp.colors[key], command=lambda port = key: self.set_color(port))
                    self.colors[key].grid(row=self.index, column=0, sticky='w')
                    self.labels[key] = tk.Label(self.colors_pane, text=key)
                    self.labels[key].grid(row=self.index, column=1, sticky='w')
                
        else:
            for key in ['n type', 'p type']:
                self.colors[key].grid_forget()
                self.labels[key].grid_forget()
                self.colors.pop(key)
                self.labels.pop(key)
                self.index -= 1
    
    def set_color(self, def_stud_ID):
        self.cpp.colors[def_stud_ID] = askcolor(parent=self)[1]
        self.colors[def_stud_ID].configure(bg=self.cpp.colors[def_stud_ID])
        
    def save(self, close=False):
        try:
            self.cpp.m_e = float(self.m_e_entry.var.get())
            self.cpp.m_h = float(self.m_h_entry.var.get())
            if self.material_study.defect_concentrations is not None:
                self.material_study.defect_concentrations.set_masses(self.cpp.m_e, self.cpp.m_h)
        except ValueError:
            self.cpp.m_e = None
            self.cpp.m_h = None
            print('Warning! At least one of the effective masses is not specified, both are set to None')
        try:
            self.cpp.temperature = float(self.cte_temp.var.get())
            self.display_param.write_in_pp(self.cpp)
            self.cpp.xmin = float(self.temp_range.low_var.get())
            self.cpp.xmax = float(self.temp_range.high_var.get())
            self.cpp.dt = float(self.temp_range.step_var.get())
            self.mainwindow.plot_defect_concentrations()
            self.attributes('-topmost', True)
            if close:
                self.destroy()
        except ValueError:
            print('Warning! Please specify range values as float values')

class ChargeCarriersConcentrationsPlotParametersWindow(tk.Toplevel):

    def __init__(self, mainwindow, material_study):

        tk.Toplevel.__init__(self, mainwindow)
        
        self.mainwindow = mainwindow
        
        self.material_study = material_study

        self.ccpp = material_study.ccpp

        self.main_frame = tkinter.ttk.Frame(self)
        self.main_frame.grid(sticky='nsew')
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.title(material_study.treetitle + ' Charge Carriers Concentrations Plot Parameters Window')
        
        # --------------------------------------------- EFFECTIVE MASSE --------------------------------------------------

        label0 = tk.Label(self.main_frame, text='Charge Carriers Effective Masses', font='-weight bold')
        masses_frame = tkinter.ttk.LabelFrame(self.main_frame, labelwidget=label0)
        masses_frame.grid(sticky='nsew')
        
        self.m_e_entry = tu.QuantityEntry(masses_frame, 'Electrons effective mass', self.ccpp.m_e, ' me', width=5)
        self.m_e_entry.pack(padx=5, pady=5)
        self.m_h_entry = tu.QuantityEntry(masses_frame, 'Holes effective mass', self.ccpp.m_h, ' me', width=5)
        self.m_h_entry.pack(padx=5, pady=5)

        # --------------------------------------------- TEMPERATURES --------------------------------------------------

        label1 = tk.Label(self.main_frame, text='Temperatures', font='-weight bold')
        temperature_frame = tkinter.ttk.LabelFrame(self.main_frame, labelwidget=label1)
        temperature_frame.grid()

        tk.Label(temperature_frame, text='Growth Temperature (fixed) ').grid(row=0, column=0)
        self.cte_temp = tu.QuantityEntry(temperature_frame, '', self.ccpp.temperature, 'K', width=7)
        self.cte_temp.grid(row=0, column=1)

        self.temp_range = tu.RangeFrame(temperature_frame, self.ccpp.xmin, self.ccpp.xmax, 'Ambiant Temperature', 'K', step=self.ccpp.dt, width=7)
        self.temp_range.grid(row=1, column=0, columnspan=2, pady=5, padx=5)
        
        # Display parameters
        
        # ---------------------------------------------- DISPLAY PARAMS ------------------------------------------------
        
        self.display_param = tu.DisplayParametersFrame(self.main_frame, 'Ambiant Temperature', 'Charge Carriers Concentrations', self.ccpp)
        self.display_param.frame.grid(row=2, column=0, pady=3, sticky='nsew')
        
        # ---------------------------------------------- COLORS ------------------------------------------------
        self.label2 = tk.Label(self.main_frame, text='Colors', font='-weight bold')
        self.colors_pane = tkinter.ttk.LabelFrame(self.main_frame, labelwidget=self.label2)
        self.colors = {}
        self.labels = {}
        self.index = 0 
        
        for key in ['n (electrons)', 'n (holes)']:
            self.colors[key] = tk.Button(self.colors_pane, text='\t\t', bg=self.ccpp.colors[key], command=lambda port = key: self.set_color(port))
            self.colors[key].grid(row=self.index, column=0, sticky='w')
            self.labels[key] =  tk.Label(self.colors_pane, text=key)
            self.labels[key].grid(row=self.index, column=1, sticky='w')
            self.index += 1
            
        self.colors_pane.grid(row=4, column=0, pady=3, sticky='nsew')

        # --------------------------------------------------- BUTTONS --------------------------------------------------

        buttons_frame = tkinter.ttk.Frame(self.main_frame)
        buttons_frame.grid(row=5, column=0, pady=3, sticky='nsew')

        tkinter.ttk.Button(buttons_frame, text='Apply', command=self.save).grid(row=0, column=0, padx=5)
        tkinter.ttk.Button(buttons_frame, text='OK', command=lambda: self.save(close=True)).grid(row=0, column=1, padx=5)
        tkinter.ttk.Button(buttons_frame, text='Cancel', command=self.destroy).grid(row=0, column=2, padx=5)
    
    def set_color(self, def_stud_ID):
        self.ccpp.colors[def_stud_ID] = askcolor(parent=self)[1]
        self.colors[def_stud_ID].configure(bg=self.ccpp.colors[def_stud_ID])
        
    def save(self, close=False):
        try:
            self.ccpp.m_e = float(self.m_e_entry.var.get())
            self.ccpp.m_h = float(self.m_h_entry.var.get())
            if self.material_study.defect_concentrations is not None:
                self.material_study.defect_concentrations.set_masses(self.ccpp.m_e, self.ccpp.m_h)
        except ValueError:
            self.ccpp.m_e = None
            self.ccpp.m_h = None
            print('Warning! At least one of the effective masses is not specified, both are set to None')
        try:
            self.ccpp.temperature = float(self.cte_temp.var.get())
            self.display_param.write_in_pp(self.ccpp)
            self.ccpp.xmin = float(self.temp_range.low_var.get())
            self.ccpp.xmax = float(self.temp_range.high_var.get())
            self.ccpp.dt = float(self.temp_range.step_var.get())
            self.mainwindow.plot_defect_concentrations(code=1)
            self.attributes('-topmost', True)
            if close:
                self.destroy()
        except ValueError:
            print('Warning! Please specify range values as float values')

        self.destroy()
        

class FermiLevelVariationsPlotParametersWindow(tk.Toplevel):

    def __init__(self, mainwindow, material_study):

        tk.Toplevel.__init__(self, mainwindow)
        
        self.mainwindow = mainwindow
        
        self.material_study = material_study

        self.eftpp = material_study.eftpp

        self.main_frame = tkinter.ttk.Frame(self)
        self.main_frame.grid(sticky='nsew')
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.title(material_study.treetitle + ' Fermi Level Variations Plot Parameters Window')
        
        # --------------------------------------------- EFFECTIVE MASSE --------------------------------------------------

        label0 = tk.Label(self.main_frame, text='Charge Carriers Effective Masses', font='-weight bold')
        masses_frame = tkinter.ttk.LabelFrame(self.main_frame, labelwidget=label0)
        masses_frame.grid(sticky='nsew')
        
        self.m_e_entry = tu.QuantityEntry(masses_frame, 'Electrons effective mass', self.eftpp.m_e, ' me', width=5)
        self.m_e_entry.pack(padx=5, pady=5)
        self.m_h_entry = tu.QuantityEntry(masses_frame, 'Holes effective mass', self.eftpp.m_h, ' me', width=5)
        self.m_h_entry.pack(padx=5, pady=5)

        # --------------------------------------------- TEMPERATURES --------------------------------------------------

        label1 = tk.Label(self.main_frame, text='Temperatures', font='-weight bold')
        temperature_frame = tkinter.ttk.LabelFrame(self.main_frame, labelwidget=label1)
        temperature_frame.grid()

        tk.Label(temperature_frame, text='Growth Temperature (fixed) ').grid(row=0, column=0)
        self.cte_temp = tu.QuantityEntry(temperature_frame, '', self.eftpp.temperature, 'K', width=7)
        self.cte_temp.grid(row=0, column=1)

        self.temp_range = tu.RangeFrame(temperature_frame, self.eftpp.xmin, self.eftpp.xmax, 'Ambiant Temperature', 'K', step=self.eftpp.dt, width=7)
        self.temp_range.grid(row=1, column=0, columnspan=2, pady=5, padx=5)
        
        # Display parameters
        
        # ---------------------------------------------- DISPLAY PARAMS ------------------------------------------------
        
        self.display_param = tu.DisplayParametersFrame(self.main_frame, 'Ambiant Temperature', 'Charge Carriers Concentrations', self.eftpp)
        self.display_param.frame.grid(row=2, column=0, pady=3, sticky='nsew')
        
        # --------------------------------------------------- BUTTONS --------------------------------------------------

        buttons_frame = tkinter.ttk.Frame(self.main_frame)
        buttons_frame.grid(row=5, column=0, pady=3, sticky='nsew')

        tkinter.ttk.Button(buttons_frame, text='Apply', command=self.save).grid(row=0, column=0, padx=5)
        tkinter.ttk.Button(buttons_frame, text='OK', command=lambda: self.save(close=True)).grid(row=0, column=1, padx=5)
        tkinter.ttk.Button(buttons_frame, text='Cancel', command=self.destroy).grid(row=0, column=2, padx=5)
    
    def save(self, close=False):
        try:
            self.eftpp.m_e = float(self.m_e_entry.var.get())
            self.eftpp.m_h = float(self.m_h_entry.var.get())
            if self.material_study.defect_concentrations is not None:
                self.material_study.defect_concentrations.set_masses(self.eftpp.m_e, self.eftpp.m_h)
        except ValueError:
            self.eftpp.m_e = None
            self.eftpp.m_h = None
            print('Warning! At least one of the effective masses is not specified, both are set to None')
        try:
            self.eftpp.temperature = float(self.cte_temp.var.get())
            self.display_param.write_in_pp(self.eftpp)
            self.eftpp.xmin = float(self.temp_range.low_var.get())
            self.eftpp.xmax = float(self.temp_range.high_var.get())
            self.eftpp.dt = float(self.temp_range.step_var.get())
            self.mainwindow.plot_defect_concentrations(code=2)
            self.attributes('-topmost', True)
            if close:
                self.destroy()
        except ValueError:
            print('Warning! Please specify range values as float values')

        self.destroy()
