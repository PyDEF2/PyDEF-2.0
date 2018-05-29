"""
    Project Manager in PyVALENCE GUI
    version: 2.0
    author: Adrien Stoliaroff
    email: adrien.stoliaroff@cnrs-imn.fr
"""

import Tkinter as tk
from Tkinter import Tk, Frame, Menu, Button, Label
from Tkinter import LEFT, RIGHT, TOP, BOTTOM, X, FLAT, RAISED, BOTH, END, SUNKEN, ALL
from PIL import Image, ImageTk

import ttk 
import tkinter_utilities as tu 
import re

import pydef_core.defect as dc
import pydef_core.defect_study as ds
import pydef_core.basic_functions as bf


class DefectStudyCreationWindow(tk.Toplevel):

    def __init__(self, mainwindow, project, defect_study_to_edit):

        tk.Toplevel.__init__(self, mainwindow)
        self.minsize(width=self.winfo_screenwidth()/2, height=self.winfo_screenheight()/2)
        self.mainwindow = mainwindow
        self.title('Defect Study Creation Window: Defect Creation')
        self.width=self.winfo_width()
        self.height=self.winfo_height()
        self.defect_study = defect_study_to_edit
        
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(expand=True, fill='both')
        self.project = project

        if project.hostcellid == '':
            self.mainwindow.printerror('Current project has no host cell! Please declare the perfect cell as host before creating any Defect Study.')

        if defect_study_to_edit is not None:
            self.step = 2
            self.title('Defect Study Creation Window: Defect Study Corrections')
            self.defect_corrections_frame = DefectStudyCorrectionsFrame(self, self.project, self.mainwindow, self.defect_study)
        else:
            self.step = 0
            self.defect_creation_frame = DefectCreationFrame(self, self.project, self.mainwindow)
        
        if self.defect_study is None:  
            self.edit = False
        else:
            self.edit = True
        tu.centre_window(self)
    
    def plot(self, close=False):
        self.mainwindow.plot()
        if close:
            self.cancel(ok=True)

    def create_defect(self):
        if self.step == 0:
            try:
                if self.defect_creation_frame.defect_type == 'Substitutional':
                    atom_entries = [self.defect_creation_frame.atom_entry.get(), self.defect_creation_frame.atom_entry2.get()]
                    chem_pot = [float(self.defect_creation_frame.chem_pot_entry.get()), float(self.defect_creation_frame.chem_pot_entry.get())]
                    defect = dc.Defect(self.defect_creation_frame.defect_type, atom_entries, chem_pot, nb_sites=float(self.defect_creation_frame.nb_sites.get()))
                else:
                    defect = dc.Defect(self.defect_creation_frame.defect_type, [self.defect_creation_frame.atom_entry.get()], [float(self.defect_creation_frame.chem_pot_entry.get())], nb_sites=float(self.defect_creation_frame.nb_sites.get()))
                if len(self.defect_creation_frame.defname.get()) > 0:
                    defect.name = self.defect_creation_frame.defname.get()
                self.project.add_defect(defect, self.defect_creation_frame.name_entry.get())
                self.defect_creation_frame.update_existing_defect_list()
            except ValueError, e:
                if len(self.defect_creation_frame.name_entry.get()) == 0:
                    self.mainwindow.printerror('Please specify defect attributes before trying to save it')
                else:
                    self.mainwindow.printerror('Mistyping? Please specify a float value for the number of sites')
    
    def restore_defects(self):
        """To be called when the user cancels the creation after the Defect Study has been created"""
        if self.defect_study is not None:
            defects = [defect for defect in self.defect_study.defects]
            defects = set(defects)
            for defect in defects:
                self.project.add_defect(defect, defect.name)

    def delete_defect(self):
        if self.step == 0:
            key = self.defect_creation_frame.name_entry.get()
            self.project.defects.pop(key)
            print 'Deleted Defect ' + self.defect_creation_frame.name_entry.get()
            self.defect_creation_frame.update_defect_frame(delete=True)

    def next_frame(self):
        try:
            if self.step == 0:
                # Check that project already has defects, or that all properties are correctly given so that a new one can be created
                name_entry_content = self.defect_creation_frame.name_entry.get()
                try:
                    if not(name_entry_content in self.defect_creation_frame.existing_defects_list) and len(name_entry_content)>0:
                        # Check name
                        if len(name_entry_content)<1:
                            raise bf.PyVALENCEDefectCreationError('Please specify a name for the new Defect')
                        # Check defect type
                        if not(self.defect_creation_frame.defect_type in ['Vacancy', 'Interstitial', 'Substitutional']):
                            raise bf.PyVALENCEDefectCreationError('Please select a Defect type (vacancy/substitution/interstitial) for the new Defect')
                        # Check affected atom
                        if not(self.defect_creation_frame.atom_entry.get() in self.defect_creation_frame.atoms_list):
                            raise bf.PyVALENCEDefectCreationError('Please select the atom affected by the new Defect')
                        # Check chemical potential
                        if len(self.defect_creation_frame.chem_pot_entry.get()) == 0:
                            raise bf.PyVALENCEDefectCreationError('Please specify the chemical potential of the atom affected by the new Defect')
                        elif not(float(self.defect_creation_frame.chem_pot_entry.get())<=0):
                            self.mainwindow.printerror('Chemical potentials must be negative or null floats!')
                        self.create_defect()
                        self.defect_creation_frame.update_existing_defect_list()
                    if len(self.defect_creation_frame.existing_defects_list)>0 :
                        self.defect_creation_frame.destroy()
                        self.title('Defect Study Creation Window: Defect Study Creation')
                        self.defect_study_creation_frame = DefectStudyCreationFrame(self, self.project, self.mainwindow, self.defect_study)
                        self.step += 1
                except ValueError:
                    self.mainwindow.printerror('Chemical potentials must be negative or null floats!')
                except bf.PyVALENCEDefectCreationError, e:
                    self.mainwindow.printerror(str(e))
            elif self.step == 1:
                # Create Defect Study
                if self.defect_study is None:
                    self.host_cell = self.project.cells[self.project.hostcellid]
                    
                    self.defects = [self.project.defects[defect_name] for defect_name in self.defect_study_creation_frame.defect_frame.get_choice()]
                    # [self.project.defects.pop(defect_name) for defect_name in self.defect_study_creation_frame.defect_frame.get_choice()]
                    
                    self.gaps_input = self.defect_study_creation_frame.gap_input_frame.get_gaps()
                
                    self.defect_study = ds.DefectStudy(self.host_cell, self.host_cell, self.defects, 'other', 0, 0, 0, 0, self.gaps_input)
                    # Checks
                    if len(self.defects) == 0:
                        raise bf.PyVALENCEDefectCreationError('Please select a Defect for the new Defect Study')
                else:
                    self.defects = [self.project.defects[defect_name] for defect_name in self.defect_study_creation_frame.defect_frame.get_choice()]
                    self.defect_study.defects = self.defects
                    self.defect_study.fpp = ds.FormationPlotParameters(self.defect_study)
                # Change Frame
                self.defect_study_creation_frame.destroy()
                self.title('Defect Study Creation Window: Defect Study Corrections')
                self.defect_corrections_frame = DefectStudyCorrectionsFrame(self, self.project, self.mainwindow, self.defect_study)
                self.step += 1
                
            elif self.step == 2:
                
                if self.defect_corrections_frame.host_cell_b_var.get() != 'None':
                    host_cell_b = self.project.cells[self.defect_corrections_frame.host_cell_b_var.get()]
                else:
                    host_cell_b = self.project.cells[self.project.hostcellid]
                geometry = self.defect_corrections_frame.geometry_var.get()
                if geometry == '':
                    geometry ='other'
                # Corrections
                e_r = self.defect_corrections_frame.rel_perm.get()
                mk_1_1 = self.defect_corrections_frame.mk_1_1_var.get()
                de_vbm_input = self.defect_corrections_frame.de_vbm_input_var.get()
                de_cbm_input = self.defect_corrections_frame.de_cbm_input_var.get()
                pa_correction = self.defect_corrections_frame.pa_corr_var.get()
                mb_correction = self.defect_corrections_frame.mb_corr_var.get()
                phs_correction = self.defect_corrections_frame.phs_corr_var.get()
                vbm_correction = self.defect_corrections_frame.vbm_corr_var.get()
                mp_correction = self.defect_corrections_frame.mp_corr_var.get()
                # Check that e_r > 0
                if float(e_r) <=0:
                    raise bf.PyVALENCEDefectCreationError('Relative permittivity must be a strictly positive float number!')
                if not self.edit:
                    self.defect_study = ds.DefectStudy(self.host_cell, host_cell_b, self.defects, geometry, e_r, mk_1_1, de_vbm_input, de_cbm_input, self.gaps_input, 
                    pa_correction=pa_correction, mb_correction=mb_correction, phs_correction=phs_correction, vbm_correction=vbm_correction, mp_correction=mp_correction)
                    self.mainwindow.create_defect_study(self.defect_study)
                    self.edit = True
                    self.mainwindow.currentitemid = self.defect_study.ID
                    message = 'Defect Study ' + self.defect_study.treetitle + ' created successfully!' 
                    corrlist = []
                    if pa_correction:
                        corrlist.append('PA')
                    if mb_correction:
                        corrlist.append('MB')
                    if mb_correction:
                        corrlist.append('PHS')
                    if vbm_correction:
                        corrlist.append('VBM')
                    if mp_correction:
                        corrlist.append('MP')
                    if len(corrlist)>0:
                        message += '(' + ', '.join(corrlist) 
                    if len(corrlist)>1:
                        message += ' corrections)'
                    elif len(corrlist)==1:
                        message += ' correction)'
                    print message
                else:
                    self.defect_study.host_cell_b = host_cell_b
                    self.defect_study.e_r = e_r
                    self.defect_study.mk_1_1 = mk_1_1
                    self.defect_study.de_vbm_input = de_vbm_input
                    self.defect_study.de_cbm_input = de_cbm_input
                    self.defect_study.pa_correction = pa_correction
                    self.defect_study.mb_correction = mb_correction
                    self.defect_study.phs_correction = phs_correction
                    self.defect_study.vbm_correction = vbm_correction
                    self.defect_study.mp_correction = mp_correction
                # Change Frame
                self.defect_corrections_frame.destroy()
                self.title('Defect Study Creation Window: Populate Defect Study')
                self.defect_populate_frame = DefectStudyPopulateFrame(self, self.project, self.mainwindow, self.defect_study)
                self.step += 1
        except bf.PyVALENCEDefectCreationError, e:
            self.mainwindow.printerror(str(e))
        except ValueError, e:
            self.mainwindow.printerror(str(e))

    def previous_frame(self):
        self.step -= 1
        if self.step == 0:
            self.defect_study_creation_frame.destroy()
            self.title('Defect Study Creation Window: Defect Creation')
            self.defect_creation_frame = DefectCreationFrame(self, self.project, self.mainwindow)
        elif self.step == 1:
            self.defect_corrections_frame.destroy()
            self.title('Defect Study Creation Window: Defect Study Creation')
            self.defect_study_creation_frame = DefectStudyCreationFrame(self, self.project, self.mainwindow, self.defect_study)
        elif self.step ==2:
            self.defect_populate_frame.destroy()
            self.title('Defect Study Creation Window: Defect Study Corrections')
            self.defect_corrections_frame = DefectStudyCorrectionsFrame(self, self.project, self.mainwindow, self.defect_study)

    def cancel(self, event=None, ok=False):
        if not ok:
            self.restore_defects()
        # self.mainwindow.current
        self.mainwindow.focus_set()
        self.destroy()

class ArtEvent(object):

    def __init(self, widget):
        self.widget = widget

class DefectCreationFrame(object):

    def isFloat(self, chem_pot_entry):
        arg = chem_pot_entry.get()
        length = len(arg)
        if length>1:
            try:
                float(arg)
                return True
            except ValueError:
                self.parent.mainwindow.printerror('Given Chemical Potential is not a float!')
                chem_pot_entry.delete(0, END)
                return False
        else:
            return True

    def chemical_species_update(self, event):
        try:
            if event.widget == self.atom_entry:
                chemical_species = self.atom_entry.get().split()[0]
                self.label4.configure(text='Chemical potential of ' + chemical_species)
                self.chem_pot_entry.delete(0, END)
                self.chem_pot_entry.insert(0, str(dc.FERE[chemical_species]))
            elif event.widget == self.atom_entry2:
                chemical_species = self.atom_entry2.get().split()[0]
                self.label41.configure(text='Chemical potential of ' + chemical_species)
                self.chem_pot_entry2.delete(0, END)
                self.chem_pot_entry2.insert(0, str(dc.FERE[chemical_species]))
        except KeyError:
            print 'Warning! No chemical potential referenced by default for ' + chemical_species + '! Please specify it yourself'

    def atom_entry_check(self, arg):
        rex = re.compile("^([A-Z][a-z]|[A-Z]) [(](.|..|...)[)]")
        string = arg.get()
        if rex.match(string):
            event = ArtEvent()
            event.widget = arg
            self.chemical_species_update(event)
            return True
        else:
            self.parent.mainwindow.printerror('Wrong Format! Please specify atom as H (1), Li (1)...')
            return False

    def update_existing_defect_list(self):
        self.existing_defects_list = [displayname for displayname in self.project.defects.keys()]
        self.name_entry.configure(values=self.existing_defects_list)

    def update_defect_frame(self, event=None, delete=False):
        self.update_existing_defect_list()
        if delete == True:
            self.name_entry.set('')
            try:
                self.atom_entry.set('')
            except AttributeError, e:
                self.atom_entry.delete(0, END)
            try:
                self.chem_pot_entry.set('')
            except AttributeError, e:
                self.chem_pot_entry.delete(0, END)
            try:
                self.atom_entry2.delete(0, END)
                self.chem_pot_entry2.delete(0, END)
            except AttributeError, e:
                pass
        try:
            selected_defect = self.project.defects[self.name_entry.get()]
            self.select_defect_type(selected_defect.defect_type)
            print 'Viewing Defect ' + selected_defect.displayname
            if selected_defect.defect_type == 'Substitutional':
                try:
                    self.atom_entry.set(selected_defect.atom[0])
                    self.atom_entry2.set(selected_defect.atom[1])
                    self.chem_pot_entry2.insert(0, str(selected_defect.chem_pot_input[1]))
                    event = ArtEvent()
                    event.widget = self.atom_entry2
                    self.chemical_species_update(event)
                except AttributeError:
                    self.atom_entry2.delete(0, END)
                    self.atom_entry2.insert(0, selected_defect.atom[1])
                    self.chem_pot_entry2.delete(0, END)
                    self.chem_pot_entry2.insert(0, selected_defect.chem_pot_input[1])
                    self.atom_entry2.bind("<<FocusOut>>", self.chemical_species_update)
                    event = ArtEvent()
                    event.widget = self.atom_entry2
                    self.chemical_species_update(event)
            elif selected_defect.defect_type == 'Interstitial':
                try:
                    self.label31.destroy()
                    self.label41.destroy()
                    self.atom_entry2.destroy()
                    self.chem_pot_entry2.destroy()
                except AttributeError, e:
                    pass
                self.atom_entry.destroy()
                self.atom_entry = tk.Entry(self.entries_pane, validate='focusout', validatecommand=lambda: self.atom_entry_check(self.atom_entry))
                self.atom_entry.grid(row=0, column=1, sticky='nsew')
                self.atom_entry.delete(0, END)
                self.atom_entry.insert(0, selected_defect.atom[0])
                self.atom_entry.bind("<<FocusOut>>", self.chemical_species_update)
            elif selected_defect.defect_type == 'Vacancy':
                try:
                    self.label31.destroy()
                    self.label41.destroy()
                    self.atom_entry2.destroy()
                    self.chem_pot_entry2.destroy()
                except AttributeError, e:
                    pass
                self.atom_entry.destroy()
                self.atom_entry = ttk.Combobox(self.entries_pane, values=self.atoms_list, state='readonly')
                self.atom_entry.grid(row=0, column=1, sticky='nsew')
                self.atom_entry.bind("<<ComboboxSelected>>", self.chemical_species_update)
                self.atom_entry.set(selected_defect.atom[0])
            self.chem_pot_entry.delete(0, END)
            self.chem_pot_entry.insert(0, selected_defect.chem_pot_input[0])
            event = ArtEvent()
            event.widget = self.atom_entry
            self.chemical_species_update(event)
            self.nb_sites.delete(0, END)
            self.nb_sites.insert(0, str(selected_defect.nb_sites))
            self.defname.delete(0, END)
            self.defname.insert(0, selected_defect.name)
        except KeyError:
            self.select_defect_type('')

    def select_defect_type(self, def_type):
            if def_type=='Vacancy':
                # self.vacancy_button.flash()
                self.vacancy_button.configure(relief=RAISED, bg='white')
                self.substitution_button.configure(relief=SUNKEN, bg='grey')
                self.interstitial_button.configure(relief=SUNKEN, bg='grey')
                self.chem_pot_entry.delete(0, END)
                self.label3.configure(text='Removed atom')
                self.atom_entry.destroy()
                self.atom_entry = ttk.Combobox(self.entries_pane, values=self.atoms_list, state='readonly')
                self.atom_entry.grid(row=0, column=1, sticky='nsew')
                self.atom_entry.bind("<<ComboboxSelected>>", self.chemical_species_update)
                try:
                    self.label31.destroy()
                    self.label41.destroy()
                    self.atom_entry2.destroy()
                    self.chem_pot_entry2.destroy()
                except AttributeError:
                    pass
            elif def_type=='Substitutional':
                self.vacancy_button.configure(relief=SUNKEN, bg='grey')
                # self.substitution_button.flash()
                self.substitution_button.configure(relief=RAISED, bg='white')
                self.interstitial_button.configure(relief=SUNKEN, bg='grey')
                # update display: atom removed, insert new entry in self.entries_pane
                self.chem_pot_entry.delete(0, END)
                self.label3.configure(text='Replaced atom')
                self.label31 = tk.Label(self.entries_pane, text=' with atom ', padx=20)
                self.label31.grid(row=0, column=2)
                self.atom_entry.destroy()
                self.atom_entry = ttk.Combobox(self.entries_pane, values=self.atoms_list, state='readonly')
                self.atom_entry.bind("<<ComboboxSelected>>", self.chemical_species_update)
                self.atom_entry.grid(row=0, column=1, sticky='nsew')
                self.label4.configure(text='Chemical potential of the chemical species')
                self.label41 = tk.Label(self.entries_pane, text='Chemical potential of the chemical species', padx=20)
                self.label41.grid(row=1, column=2)
                self.atom_entry2 = tk.Entry(self.entries_pane, validate='focusout', validatecommand=lambda: self.atom_entry_check(self.atom_entry2))
                self.atom_entry2.grid(row=0, column=3)
                self.atom_entry2.bind("<<FocusOut>>", self.chemical_species_update)
                self.chem_pot_entry2 = tk.Entry(self.entries_pane, validate=ALL, validatecommand=lambda: self.isFloat(self.chem_pot_entry2))
                self.chem_pot_entry2.grid(row=1, column=3)
            elif def_type=='Interstitial':
                self.vacancy_button.configure(relief=SUNKEN, bg='grey')
                self.substitution_button.configure(relief=SUNKEN, bg='grey')
                self.interstitial_button.configure(relief=RAISED, bg='white')
                self.chem_pot_entry.delete(0, END)
                self.label3.configure(text='Inserted atom ')
                self.label4.configure(text='Chemical potential of the chemical species')
                self.atom_entry.destroy()
                self.atom_entry = tk.Entry(self.entries_pane, validate='focusout', validatecommand=lambda: self.atom_entry_check(self.atom_entry))
                self.atom_entry.grid(row=0, column=1, sticky='nsew')
                self.atom_entry.bind("<<FocusOut>>", self.chemical_species_update)
                try:
                    self.label31.destroy()
                    self.label41.destroy()
                    self.atom_entry2.destroy()
                    self.chem_pot_entry2.destroy()
                except AttributeError:
                    pass
            else:
                self.vacancy_button.configure(relief=RAISED, bg='white')
                self.substitution_button.configure(relief=RAISED, bg='white')
                self.interstitial_button.configure(relief=RAISED, bg='white')
                self.label3.configure(text='Affected atom')
                self.label4.configure(text='Chemical potential of the chemical species')
            self.defect_type = def_type

    def destroy(self):
        self.defect_creation_frame.destroy()

    def __init__(self, parent, project, mainwindow):
        self.defect_creation_frame = tk.Frame(parent.main_frame)
        self.parent = parent
        self.mainwindow = mainwindow
        self.project = project

        # -----------------  EXISTING DEFECTS LIST  --------------------

        self.existing_defects_pane = tk.Frame(self.defect_creation_frame, bd = 2)

        label1 = tk.Label(self.existing_defects_pane, text = 'Defect name', padx = 20)
        label1.grid(row = 0, column = 0, sticky = 'nsew')

        self.existing_defects_list = [d.displayname for d in project.defects.values()]
        self.name_entry = ttk.Combobox(self.existing_defects_pane, values=self.existing_defects_list)
        self.name_entry.grid(row = 0, column = 1, sticky = 'nsew')
        self.name_entry.bind("<<ComboboxSelected>>", self.update_defect_frame)

        self.existing_defects_pane.pack()

        label2 = tk.Label(self.defect_creation_frame, text = 'Defect type')
        label2.pack()

        # -------------------- DEFECT TYPE BUTTONS  --------------------

        self.button_pane0 = tk.Frame(self.defect_creation_frame, bd = 2)

        self.vacancy_icon = ImageTk.PhotoImage(Image.open('Pictures/DefectsButton/Vacancy.png'))
        self.interstitial_icon = ImageTk.PhotoImage(Image.open('Pictures/DefectsButton/Interstitial.png'))
        self.substitution_icon = ImageTk.PhotoImage(Image.open('Pictures/DefectsButton/Substitution.png'))

        self.vacancy_button = Button(self.button_pane0, text='Vacancy', bg='white', image=self.vacancy_icon, compound=TOP, command=lambda:self.select_defect_type('Vacancy'))
        self.vacancy_button.grid(row=0, column=0, sticky='nsew')

        self.substitution_button = Button(self.button_pane0, text='Substitution', bg='white', image=self.substitution_icon, compound=TOP, command=lambda:self.select_defect_type('Substitutional'))
        self.substitution_button.grid(row=0, column=1, sticky='nsew')

        self.interstitial_button = Button(self.button_pane0, text='Interstitial', bg='white', image=self.interstitial_icon, compound=TOP, command=lambda:self.select_defect_type('Interstitial'))
        self.interstitial_button.grid(row=0, column=2, sticky='nsew')

        self.defect_type = ''

        self.button_pane0.pack()

        self.entries_pane = tk.Frame(self.defect_creation_frame, bd=2, pady=10)

        # --------------------------  ATOM  ----------------------------

        self.label3 = tk.Label(self.entries_pane, text='Affected atom', padx=20)
        self.label3.grid(row=0, column=0, sticky='nsew')
        
        try:
            project.cells[project.hostcellid]
        except KeyError:
            self.parent.mainwindow.printerror('Please define host cell!')

        self.atoms_list = list(project.cells[project.hostcellid].atoms)

        self.atom_entry = ttk.Combobox(self.entries_pane, values=self.atoms_list, state='readonly')
        self.atom_entry.bind("<<ComboboxSelected>>", self.chemical_species_update)
        self.atom_entry.grid(row=0, column=1, sticky='nsew')

        # ---------------------  CHEM POT ENTRY  -----------------------

        self.label4 = tk.Label(self.entries_pane, text='Chemical potential of the chemical species', padx=20)
        self.label4.grid(row=1, column=0, sticky='nsew')

        self.chem_pot_entry = tk.Entry(self.entries_pane, validate=ALL, validatecommand=lambda: self.isFloat(self.chem_pot_entry))
        self.chem_pot_entry.grid(row = 1, column = 1, sticky = 'nsew')

        self.entries_pane.pack()
        
        # ---------------------  ADDITIONNAL INFO  -----------------------
        
        self.label5 = tk.Label(self.defect_creation_frame, text='Optionnal information', font = '-weight bold')
        self.add_info_pane = ttk.LabelFrame(self.defect_creation_frame, labelwidget=self.label5)
        
        tk.Label(self.add_info_pane, text='Number of sites (required for Concentrations computations)').grid(row=0,column=0)
        self.nb_sites = tk.Entry(self.add_info_pane)
        self.nb_sites.grid(row = 0, column = 1, sticky = 'nsew')
        
        tk.Label(self.add_info_pane, text='Name as displayed in plots (automatically created if not specified)').grid(row=1,column=0)
        self.defname = tk.Entry(self.add_info_pane)
        self.defname.grid(row = 1, column = 1, sticky = 'nsew')
        self.add_info_pane.pack()

        # ------------------  NAVIGATION BUTTONS  ----------------------

        self.button_pane1 = tk.Frame(self.defect_creation_frame, bd = 2, pady = 10)
        self.create_defect_button = Button(self.button_pane1, text = 'Save Defect', command=parent.create_defect)
        self.delete_defect_button = Button(self.button_pane1, text = 'Delete Defect', command=parent.delete_defect)
        self.next_button = Button(self.button_pane1, text = 'Next >>', command=parent.next_frame)
        self.cancel_button = Button(self.button_pane1, text = 'Cancel', command=parent.cancel)
        self.create_defect_button.grid(row = 0, column = 0)
        self.delete_defect_button.grid(row = 0, column = 1)
        self.next_button.grid(row = 0, column = 2)
        self.cancel_button.grid(row = 0, column = 3)

        self.button_pane1.pack(side=BOTTOM, pady=2)

        self.defect_creation_frame.pack(expand=True, fill='y')

class DefectStudyCreationFrame(object):

    def destroy(self):
        self.defect_study_creation_frame.destroy()

    def __init__(self, parent, project, mainwindow, defect_study_to_edit):
        self.defect_study_creation_frame = tk.Frame(parent.main_frame)
        self.parent = parent
        self.mainwindow = mainwindow
        self.defect_study = defect_study_to_edit
        self.project = project

        self.input_frame = tk.Frame(self.defect_study_creation_frame)
        self.correction_frame = tk.Frame(self.defect_study_creation_frame)

        # Variables
        self.defect_study_id_var = tk.StringVar()  # Defect Study ID
        self.host_cell_var = tk.StringVar()  # Host cell ID
        self.defects_var = tk.StringVar()  # Defects IDs (separated with a comma)
        self.gaps_var = tk.StringVar()  # gaps separated with a comma/semicolon ?
        self.defect_study_id_var.set('automatic')
        if self.defect_study is not None:
            gaps = self.defect_study.gaps_input
            string = ''
            for gap in gaps:
                string += gap[1] + ' (' + str(gap[0]) + ' eV);' 
            self.gaps_var.set(string)
        # Name
        ttk.Label(self.input_frame, text='Defect Study Name', width=15, anchor='w'
                  ).grid(row=0, column=0, padx=3, pady=3)
        ttk.Entry(self.input_frame, textvariable=self.defect_study_id_var
                  ).grid(row=0, column=1, sticky='we', padx=3, pady=3)

        # Defects
        if self.defect_study is not None:
            items_on = [d.displayname for d in self.defect_study.defects]
        else:
            items_on = []
        if self.defects_var.get() != '':
            items_on = self.defects_var.get().split(',')

        in_label = self.defect_study_id_var.get() + ' defects'
        if self.defect_study_id_var.get() == 'automatic':
            in_label = 'New Defect Study Defects'
        self.defect_title = ttk.Label(self.defect_study_creation_frame, text='Defect(s)', width=15, anchor='center', font=('', '16', 'bold'))
        self.defect_frame = tu.ItemsChoiceFrame(self.defect_study_creation_frame, self.project.defects, items_on, in_label, self.project.name + ' defects', self.defect_title)

        # Gaps input
        self.gap_title = ttk.Label(self.defect_study_creation_frame, text='Displayed Gaps', width=15, anchor='center', font=('', '16', 'bold'))
        self.gap_input_frame = tu.GapInputFrame(self.defect_study_creation_frame, self.gaps_var, self.gap_title)

        # Buttons
        self.button_pane1 = tk.Frame(self.defect_study_creation_frame, bd = 2, pady = 10)
        self.previous_button = Button(self.button_pane1, text = '<< Previous', command=parent.previous_frame)
        self.next_button = Button(self.button_pane1, text = 'Next >>', command=parent.next_frame)
        self.cancel_button = Button(self.button_pane1, text = 'Cancel', command=self.parent.cancel)
        self.previous_button.grid(row = 0, column = 0)
        self.next_button.grid(row = 0, column = 1)
        self.cancel_button.grid(row = 0, column = 2)

        self.input_frame.pack()
        self.defect_frame.pack(expand=True, fill='both', padx=5, pady=5)
        self.gap_input_frame.pack(expand=True, fill='both', padx=5, pady=5)
        self.correction_frame.pack()
        self.button_pane1.pack(side=BOTTOM, pady=2)

        self.defect_study_creation_frame.pack(expand=True, fill='y')
        

class DefectStudyCorrectionsFrame(object):

    def destroy(self):
        self.defect_study_corrections_frame.destroy()

    def __init__(self, parent, project, mainwindow, defect_study_to_edit):

        self.defect_study_corrections_frame = tk.Frame(parent.main_frame)
        self.parent = parent
        self.mainwindow = mainwindow
        self.project = project
        self.defect_study = defect_study_to_edit
        
        # --------------------------------------------------------------------------------------------------------------
        # ------------------------------------------------- CORRECTIONS ------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.correction_frame = tk.Frame(self.defect_study_corrections_frame)
        self.corr_frame_label = ttk.Label(self.correction_frame, text='Corrections', font=('', '16', 'bold'))
        self.corr_frame = ttk.LabelFrame(self.correction_frame, labelwidget=self.corr_frame_label, labelanchor='n')
        self.corr_frame.grid(row=1, column=0, sticky='nswe', padx=10, pady=3)
        self.corr_frame.grid_columnconfigure(0, weight=1)

        # Variables
        self.host_cell_b_var = tk.StringVar()  # Host cell B ID
        self.geometry_var = tk.StringVar()  # geometry of the host cell
        self.rel_perm = tk.DoubleVar()
        self.rel_perm.set(1.0)  # relative permittivity
        self.mk_1_1_var = tk.DoubleVar()  # makov-payne correction for e_r=1 and q=1

        # Corrections
        self.vbm_corr_var = tk.BooleanVar()
        self.pa_corr_var = tk.BooleanVar()
        self.mb_corr_var = tk.BooleanVar()
        self.phs_corr_var = tk.BooleanVar()
        self.mp_corr_var = tk.BooleanVar()
        
        if self.defect_study is not None:
            self.vbm_corr_var.set(self.defect_study.vbm_correction)
            self.pa_corr_var.set(self.defect_study.pa_correction)
            self.mb_corr_var.set(self.defect_study.mb_correction)
            self.phs_corr_var.set(self.defect_study.phs_correction)
            self.mp_corr_var.set(self.defect_study.mp_correction)
        else:
            self.vbm_corr_var.set(True)
            self.pa_corr_var.set(True)
            self.mb_corr_var.set(True)
            self.phs_corr_var.set(True)
            self.mp_corr_var.set(True)

        # ------------------------------------------- VBM & PHS CORRECTIONS --------------------------------------------

        self.de_vbm_input_var = tk.DoubleVar()  # input correction of the VBM
        self.de_cbm_input_var = tk.DoubleVar()  # input correction of the CBM
        self.tot_de_vbm_var = tk.DoubleVar()  # Total correction of the VBM
        self.tot_de_cbm_var = tk.DoubleVar()  # Total correction of the CBM

        def enable_gap_corr_frame():
            """ Enable the gap correction frame if the two checkbuttons are checked and disable it if it is not """
            self.defect_study.mb_correction=self.mb_corr_var.get()
            self.defect_study.vbm_correction=self.vbm_corr_var.get()
            self.defect_study.pa_correction=self.pa_corr_var.get()
            self.defect_study.phs_correction=self.phs_corr_var.get()
            self.defect_study.mp_correction=self.mp_corr_var.get()
            if self.vbm_corr_var.get() is False and self.phs_corr_var.get() is False:
                self.host_cell_b_ccb.configure(state='disabled')
                self.add_de_vbm.configure(state='disabled')
                self.add_de_cbm.configure(state='disabled')
            else:
                self.host_cell_b_ccb.configure(state='readonly')
                self.add_de_vbm.configure(state='enabled')
                self.add_de_cbm.configure(state='enabled')

        # Checkboxes
        self.gap_corr_frame_labelframe = ttk.Frame(self.correction_frame)
        ttk.Checkbutton(self.gap_corr_frame_labelframe, text='VBM correction', variable=self.vbm_corr_var, onvalue=True,
                        offvalue=False, style='Bold.TCheckbutton', command=enable_gap_corr_frame).pack(side='left')
        ttk.Checkbutton(self.gap_corr_frame_labelframe, text='PHS correction', variable=self.phs_corr_var, onvalue=True,
                        offvalue=False, style='Bold.TCheckbutton', command=enable_gap_corr_frame).pack(side='right')

        # LabelFrame
        self.gap_corr_frame = ttk.LabelFrame(self.corr_frame, labelwidget=self.gap_corr_frame_labelframe,
                                             labelanchor='n')
        self.gap_corr_frame.grid(row=3, column=0, columnspan=2, sticky='we', padx=5, pady=5)
        self.gap_corr_frame.grid_columnconfigure(1, weight=1)

        # Host Cell B
        ttk.Label(self.gap_corr_frame, text='Host cell (better gap)').grid(row=0, column=0)
        def treetitle_if_not_host(cell):
            if cell.ID != project.hostcellid: 
                return cell.treetitle
        host_cell_b_list = [treetitle_if_not_host(d) for d in self.project.unboundcells.values()]
        self.host_cell_b_ccb = ttk.Combobox(self.gap_corr_frame, values=host_cell_b_list,
                                            textvariable=self.host_cell_b_var, state='readonly') # , values=self.project.Cells.keys() + ['None']
        self.host_cell_b_var.set('None')
        self.host_cell_b_ccb.grid(row=0, column=1, sticky='we', padx=3, pady=3)

        # VBM & CBM correction frames
        self.vbm_corr_frame = ttk.Frame(self.gap_corr_frame)
        self.vbm_corr_frame.grid(row=1, column=0, columnspan=2)
        self.cbm_corr_frame = ttk.Frame(self.gap_corr_frame)
        self.cbm_corr_frame.grid(row=2, column=0, columnspan=2)

        ttk.Label(self.vbm_corr_frame, text='Additional correction to the VBM energy: ').pack(side='left')
        ttk.Label(self.cbm_corr_frame, text='Additional correction to the CBM energy: ').pack(side='left')

        self.add_de_vbm = ttk.Entry(self.vbm_corr_frame, textvariable=self.de_vbm_input_var, width=6)
        self.add_de_vbm.pack(side='left')
        self.add_de_cbm = ttk.Entry(self.cbm_corr_frame, textvariable=self.de_cbm_input_var, width=6)
        self.add_de_cbm.pack(side='left')

        ttk.Label(self.vbm_corr_frame, text='eV dEV(tot)=').pack(side='left')
        ttk.Label(self.cbm_corr_frame, text='eV dEC(tot)=').pack(side='left')

        ttk.Entry(self.vbm_corr_frame, textvariable=self.tot_de_vbm_var, state='disabled', width=6).pack(side='left')
        ttk.Entry(self.cbm_corr_frame, textvariable=self.tot_de_cbm_var, state='disabled', width=6).pack(side='left')

        ttk.Label(self.vbm_corr_frame, text='eV').pack(side='left')
        ttk.Label(self.cbm_corr_frame, text='eV').pack(side='left')

        def get_tot_gap_corr(event):
            """ Retrieve the total VBM correction """
            self.defect_study.mb_correction=self.mb_corr_var.get()
            self.defect_study.vbm_correction=self.vbm_corr_var.get()
            self.defect_study.pa_correction=self.pa_corr_var.get()
            self.defect_study.phs_correction=self.phs_corr_var.get()
            self.defect_study.mp_correction=self.mp_corr_var.get()
            try:
                host_cell = self.project.Cells[self.host_cell_var.get()]
                host_cell_b = self.project.Cells[self.host_cell_b_var.get()]

                de_vbm = host_cell_b.VBM - host_cell.VBM
                de_cbm = host_cell_b.CBM - host_cell.CBM
            except KeyError:
                de_vbm = 0.0
                de_cbm = 0.0

            try:
                de_vbm_input = self.de_vbm_input_var.get()
                de_cbm_input = self.de_cbm_input_var.get()
            except ValueError:
                de_vbm_input = 0.0
                de_cbm_input = 0.0

            self.tot_de_vbm_var.set(de_vbm + de_vbm_input)
            self.tot_de_cbm_var.set(de_cbm + de_cbm_input)

        self.host_cell_b_ccb.bind('<<ComboboxSelected>>', get_tot_gap_corr)
        self.add_de_vbm.bind('<KeyRelease>', get_tot_gap_corr)  # update the VBM correction when a number is pressed
        self.add_de_cbm.bind('<KeyRelease>', get_tot_gap_corr)  # update the CBM correction when a number is pressed
        
        def retrieve():
            self.defect_study.mb_correction=self.mb_corr_var.get()
            self.defect_study.vbm_correction=self.vbm_corr_var.get()
            self.defect_study.pa_correction=self.pa_corr_var.get()
            self.defect_study.phs_correction=self.phs_corr_var.get()
            self.defect_study.mp_correction=self.mp_corr_var.get()
            
        # --------------------------------------- POTENTIAL ALIGNMENT CORRECTION ---------------------------------------

        ttk.Checkbutton(self.corr_frame, text='Potential alignment correction', onvalue=True, offvalue=False,
                        variable=self.pa_corr_var, style='Bold.TCheckbutton', command=retrieve
                        ).grid(row=4, column=0, columnspan=2, pady=5)

        # ------------------------------------------ MOSS-BURSTEIN CORRECTION ------------------------------------------

        ttk.Checkbutton(self.corr_frame, text='Moss-Burstein correction', onvalue=True, offvalue=False,
                        variable=self.mb_corr_var, style='Bold.TCheckbutton', command=retrieve 
                        ).grid(row=5, column=0, columnspan=2, pady=5)

        # ------------------------------------------- MAKOV-PAYNE CORRECTION -------------------------------------------

        def enable_mp_frame():
            """ Enable the Makov-Payne correction frame if the two checkbuttons are checked
             and disable it if it is not """
            self.defect_study.mp_correction = self.mp_corr_var.get()
            if self.mp_corr_var.get() is True:
                tu.enable_frame(self.mp_frame)
            else:
                tu.disable_frame(self.mp_frame)

        self.mp_frame_label = ttk.Checkbutton(self.correction_frame, text='Makov-Payne correction', variable=self.mp_corr_var,
                                              onvalue=True, offvalue=False, style='Bold.TCheckbutton', command=enable_mp_frame)
        self.mp_frame = ttk.LabelFrame(self.corr_frame, labelwidget=self.mp_frame_label, labelanchor='n')
        self.mp_frame.grid(row=6, column=0, columnspan=2, sticky='we', padx=5, pady=5)
        self.mp_frame.grid_columnconfigure(0, weight=1)
        
        # Geometry
        ttk.Label(self.mp_frame, text='Geometry of the host cell').grid(row=0, column=0)
        ttk.Combobox(self.mp_frame, values=['sc', 'fcc', 'bcc', 'hcp', 'other'], textvariable=self.geometry_var,
                     state='readonly', width=5).grid(row=0, column=1)

        # Relative permittivity
        ttk.Label(self.mp_frame, text='Relative permittivity').grid(row=1, column=0)
        ttk.Entry(self.mp_frame, textvariable=self.rel_perm, width=7).grid(row=1, column=1)

        # Makov-Payne correction for e_r=1 and q=1
        self.mp_ratio_image = ImageTk.PhotoImage(Image.open('Pictures/Makov_Payne_ratio_small.png'))
        ttk.Label(self.mp_frame, text='Value of the ratio (eV)', compound='right'
                  , image=self.mp_ratio_image).grid(row=2, column=0)
        ttk.Entry(self.mp_frame, textvariable=self.mk_1_1_var, width=7).grid(row=2, column=1)
        
        if self.defect_study.vbm_correction is False and self.defect_study.phs_correction is False:
            self.host_cell_b_ccb.configure(state='disabled')
            self.add_de_vbm.configure(state='disabled')
            self.add_de_cbm.configure(state='disabled')
        
        if not(self.defect_study.mp_correction):
            tu.disable_frame(self.mp_frame)

        # ------------------  NAVIGATION BUTTONS  ----------------------

        self.button_pane1 = tk.Frame(self.defect_study_corrections_frame, bd = 2, pady = 10)
        self.previous_button = Button(self.button_pane1, text = '<< Previous', command=parent.previous_frame)
        try:
            self.next_button = Button(self.button_pane1, text = 'Next>>', command=parent.next_frame)
        except bf.PyVALENCEDefectCreationError, e:
            selfparent.mainwindow.printerror(str(e))
        self.cancel_button = Button(self.button_pane1, text = 'Cancel', command=parent.cancel)
        self.previous_button.grid(row = 0, column = 0)
        self.next_button.grid(row = 0, column = 1)
        self.cancel_button.grid(row = 0, column = 2)

        self.correction_frame.pack()
        self.button_pane1.pack(side=BOTTOM, pady=2)

        self.defect_study_corrections_frame.pack(expand=True, fill='y')

class DefectStudyPopulateFrame(object):

    def destroy(self):
        self.defect_study_populate_frame.destroy()

    def __init__(self, parent, project, mainwindow, defect_study_to_edit):

        self.defect_study_populate_frame = tk.Frame(parent.main_frame)
        self.parent = parent
        self.project = project
        self.mainwindow = mainwindow
        self.defect_study = defect_study_to_edit

        # ------------------  ITEMS CHOICE FRAME  ----------------------
        
        def treetitle_if_not_host(cell):
            if c.ID != project.hostcellid: 
                return c.treetitle

        items = [treetitle_if_not_host(c) for c in project.unboundcells.values()]
        items_on = self.defect_study.defect_cell_studies.values()
        self.cells_title = ttk.Label(self.defect_study_populate_frame, text='Charged cells', width=15, anchor='center', font=('', '16', 'bold'))
        self.cells_frame = DefectCellChoiceFrame(self.defect_study_populate_frame, items, items_on, self.defect_study.treetitle + ' cells', self.project.name + ' calculations', self.cells_title, self.defect_study, self.mainwindow)

        # ------------------  NAVIGATION BUTTONS  ----------------------
        
        def validate(close=False):
            self.parent.attributes('-topmost', True)
            if len(self.defect_study.defect_cell_studies)>0:
                parent.plot(close=close)
            else:
                print 'Warning! Impossible to plot Defect Formation Energies for empty Defect Study ' + self.defect_study.treetitle
                if close :
                    parent.cancel(ok=True)

        self.button_pane1 = tk.Frame(self.defect_study_populate_frame, bd = 2, pady = 10)
        self.previous_button = Button(self.button_pane1, text = '<< Previous', command=parent.previous_frame)
        self.apply_button = Button(self.button_pane1, text = 'Apply', command=validate)
        self.next_button = Button(self.button_pane1, text = 'OK', command=lambda: validate(close=True))
        self.cancel_button = Button(self.button_pane1, text = 'Cancel', command=parent.cancel)
        self.previous_button.grid(row = 0, column = 0)
        self.apply_button.grid(row = 0, column = 1)
        self.next_button.grid(row = 0, column = 2)
        self.cancel_button.grid(row = 0, column = 3)

        self.cells_frame.pack(expand='y')
        self.button_pane1.pack(side=BOTTOM, pady=2)

        self.defect_study_populate_frame.pack(expand=True, fill='y')

class DefectCellChoiceFrame(tk.Toplevel):
    """ Window consisting of two listbox. The listbox on the rights contains elements which are returned
     The list on the left contains elements which are not returned"""

    def grid(self, row=None, column=None, padx=None, pady=None):
        self.main_frame.grid(row=row, column=column, padx=padx, pady=pady)

    def pack(self,expand=None, fill=None, padx=None, pady=None):
        self.main_frame.pack(expand=expand, fill=fill, padx=padx, pady=pady)

    def __init__(self, parent, items, items_on, label_on, label_off, labeltitle, defect_study, mainwindow):
        """
        :param parent: parent frame
        :param items: list of all items
        :param items_on: list of items which are used
        :param label_on: label for the list of used items
        :param label_off: label for the list of non used items
        :param labeltitle: label of the Frame"""

        self.parent = parent
        self.items = items
        self.defect_study = defect_study
        self.mainwindow = mainwindow

        self.main_frame = ttk.LabelFrame(parent, labelwidget=labeltitle)
        
        items_on_list_name = [dsc.defect_cell.treetitle for dsc in items_on]

        items_off = list(set(items) - set(items_on_list_name))

        # -------------------------------------------------- ITEMS OFF -------------------------------------------------

        self.frame_off = ttk.LabelFrame(self.main_frame, text=label_off)

        self.list_off = tk.Listbox(self.frame_off)  # list containing element not plotted
        self.list_off.config(height=5)
        self.list_off.pack(side='right')
        if (len(items_off) or len(items_on))>5:
            self.yscrollbar_off = ttk.Scrollbar(self.frame_off, orient='vertical')
            self.list_off.pack(side='left', fill='both')
            self.yscrollbar_off.pack(side='right', fill='y')
            self.list_off.config(yscrollcommand=self.yscrollbar_off.set)
            self.yscrollbar_off.config(command=self.list_off.yview)
        for i in items_off:
            self.list_off.insert('end', i)

        # ------------------------------------------------- ITEMS ON ---------------------------------------------------
        
        self.label_dc_name = {}
        self.entry_radius = {}
        self.entry_ze = {}
        self.entry_zh = {}
        self.view_spheres = {}
        self.delete_button = {}
        self.dcsids = {}

        self.on_frame = ttk.LabelFrame(self.main_frame, text=label_on)

        """self.list_on = tk.Listbox(self.on_frame)
        self.list_on.config(height=5)
        self.yscrollbar_on = ttk.Scrollbar(self.on_frame, orient='vertical')
        self.list_on.pack(side='left')
        if (len(items_off) or len(items_on))>5:
            self.yscrollbar_on.pack(side='right', fill='y')
            self.list_on.config(yscrollcommand=self.yscrollbar_on.set)
            self.yscrollbar_on.config(command=self.list_on.yview)
        for i in items_on:
            self.list_on.insert('end', i)"""
        label_dc_name = tk.Label(self.on_frame, text='Defect Cell Name')
        # if Defect Study has pa_alignment = True
        label_radius = tk.Label(self.on_frame, text='R')
        label_ze = tk.Label(self.on_frame, text='ze')
        label_zh = tk.Label(self.on_frame, text='zh')
        label_dc_name.grid(row=0,column=0)
        if self.defect_study.pa_correction:
            label_radius.grid(row=0,column=1)
        if self.defect_study.phs_correction:
            label_ze.grid(row=0,column=2)
            label_zh.grid(row=0,column=3)
        self.on_frame.nitemson = 1
        for dcs in items_on:
            self.add_dcs(dcs)    

        # --------------------------------------------------- BUTTONS --------------------------------------------------

        self.button_frame = ttk.Frame(self.main_frame)
        
        tk.Button(self.button_frame, text='>', command=self.add_selection, bg='grey').pack(side='right', expand='True', fill='both')
        tk.Button(self.button_frame, text='>>', command=self.add_all, bg='grey').pack(side='right', expand='True', fill='both')
        tk.Button(self.button_frame, text='<', command=self.remove_selection, bg='grey').pack(side='right', expand='True', fill='both')
        tk.Button(self.button_frame, text='<<', command=self.remove_all, bg='grey').pack(side='right', expand='True', fill='both')
        
        # ------------------------------------------------ EXPLANATIONS --------------------------------------------------
        
        explanations = ''
        if self.defect_study.pa_correction:
            explanations += 'R is radius of the exclusion sphere for the Potential Alignment'
        if self.defect_study.phs_correction:
            explanations += '\nze is the number of free electrons in the Conduction Band '
            explanations += '\nzh is the number of holes in the Valence Band '
        
        self.explanations = tk.Label(self.main_frame, text=explanations)
        
        self.frame_off.pack()
        self.button_frame.pack()
        self.on_frame.pack()
        self.explanations.pack(side=BOTTOM)
        
        # self.list_on.bind('<Double-Button-1>', self.remove_selected)  # remove element when double-clicked
        # self.list_off.bind('<Double-Button-1>', self.add_selected)  # add item when double-clicked
    
    def z_are_integers(self, items_ids):
                    z_e = self.entry_ze[items_ids].get()
                    z_h = self.entry_zh[items_ids].get()
                    res = True
                    zlist = [z_e, z_h]
                    i = -1
                    for z in zlist:
                        i += 1
                        length = len(z)
                        if length>0:
                            try:
                                int(z)
                                res = res and True
                            except ValueError:
                                self.mainwindow.printerror('Given value is not an integer!')
                                return False
                        else:
                            zlist[i] = 0
                    self.dcsids[items_ids].set_z(int(zlist[0]), int(zlist[1]))
                    print 'Set number of free electrons in Conduction Band to ' + str(zlist[0]) + ' and number of holes in Valence Band to ' + str(zlist[1])
                    return True
                        
    def radius_is_float(self, items_ids):
        radius = self.entry_radius[items_ids].get()
        length = len(radius)
        if length>0:
            try:
                float(radius)
                self.dcsids[items_ids].set_radius(float(radius))
                print 'Set exclusion sphere radius to ' + radius + ' A' 
                return True
            except ValueError:
                self.mainwindow.printerror('Given radius is not a float!')
                return False
        else:
            return True
    
    def plot_pa(self, items_ids):
        
        self.dcsids[items_ids].plot_potential_alignment(False)
        print 'Charged cell ' + self.dcsids[items_ids].defect_cell.treetitle + ': plot Potential Alignment'
        
    def add_dcs(self, dcs):
        items_ids = dcs.ID
        self.label_dc_name[items_ids] = tk.Label(self.on_frame, text=dcs.defect_cell.treetitle)
        self.entry_radius[items_ids] = tk.Entry(self.on_frame, width=3, validate='focusout', validatecommand=lambda: self.radius_is_float(items_ids))
        self.entry_radius[items_ids].insert(0, str(dcs.radius))
        self.entry_ze[items_ids] = tk.Entry(self.on_frame, width=3, validate='focusout', validatecommand=lambda: self.z_are_integers(items_ids))
        self.entry_ze[items_ids].insert(0, str(dcs.z_e))
        self.entry_zh[items_ids] = tk.Entry(self.on_frame, width=3, validate='focusout', validatecommand=lambda: self.z_are_integers(items_ids))
        self.entry_zh[items_ids].insert(0, str(dcs.z_h))
        self.view_spheres[items_ids] = tk.Button(self.on_frame, text='View Exclusion Sphere', padx=2, command=lambda: self.plot_pa(items_ids))
        self.delete_button[items_ids] = tk.Button(self.on_frame, text='x', bg='grey', command=lambda: self.remove_selection(items_ids), padx=2)
        self.label_dc_name[items_ids].grid(row=self.on_frame.nitemson, column=0)
        if self.defect_study.pa_correction:
            self.entry_radius[items_ids].grid(row=self.on_frame.nitemson, column=1)
        self.entry_ze[items_ids].grid(row=self.on_frame.nitemson, column=2)
        self.entry_zh[items_ids].grid(row=self.on_frame.nitemson, column=3, padx=2)
        self.delete_button[items_ids].grid(row=self.on_frame.nitemson, column=4, padx=2)
        if self.defect_study.pa_correction:
            self.view_spheres[items_ids].grid(row=self.on_frame.nitemson, column=5, padx=2)
        self.on_frame.nitemson += 1
        self.dcsids[items_ids] = dcs
            
    def add_selection(self):
        """ Add selected elements to the 'on' list and remove them from the 'off' list """
        selection = self.list_off.curselection()
        
        if len(selection) != 0:
            for selected in selection:
                items_ids = self.list_off.get(selected)
                self.label_dc_name[items_ids] = tk.Label(self.on_frame, text=items_ids)
                self.entry_radius[items_ids] = tk.Entry(self.on_frame, width=3, validate='focusout', validatecommand=lambda: self.radius_is_float(items_ids))
                self.entry_ze[items_ids] = tk.Entry(self.on_frame, width=3, validate='focusout', validatecommand=lambda: self.z_are_integers(items_ids))
                self.entry_ze[items_ids].insert(0, '0')
                self.entry_zh[items_ids] = tk.Entry(self.on_frame, width=3, validate='focusout', validatecommand=lambda: self.z_are_integers(items_ids))
                self.entry_zh[items_ids].insert(0, '0')
                self.view_spheres[items_ids] = tk.Button(self.on_frame, text='View Exclusion Sphere', padx=2, command=lambda: self.plot_pa(items_ids))
                self.delete_button[items_ids] = tk.Button(self.on_frame, text='x', bg='grey', command=lambda: self.remove_selection(items_ids), padx=2)
                self.label_dc_name[items_ids].grid(row=self.on_frame.nitemson, column=0)
                if self.defect_study.pa_correction:
                    self.entry_radius[items_ids].grid(row=self.on_frame.nitemson, column=1)
                self.entry_ze[items_ids].grid(row=self.on_frame.nitemson, column=2)
                self.entry_zh[items_ids].grid(row=self.on_frame.nitemson, column=3, padx=2)
                self.delete_button[items_ids].grid(row=self.on_frame.nitemson, column=4, padx=2)
                if self.defect_study.pa_correction:
                    self.view_spheres[items_ids].grid(row=self.on_frame.nitemson, column=5, padx=2)
                self.on_frame.nitemson += 1
                self.list_off.delete(selected)
                # add Defect Cell Study to Project and to tree
                proj_cells = self.mainwindow.projects[self.mainwindow.currentprojectid].cells.values()
                find_cell = [cell for cell in proj_cells if cell.treetitle == items_ids]
                if self.defect_study.pa_correction and len(self.entry_radius[items_ids].get())>0:
                    radius = float(self.entry_radius[items_ids].get())
                else:
                    radius = 0
                if self.defect_study.phs_correction:
                    z_e = int(self.entry_ze[items_ids].get())
                    z_h = int(self.entry_zh[items_ids].get())
                else:
                    z_e, z_h = 0, 0
                newdcs = self.defect_study.create_defect_cell_study(find_cell[0], radius, z_e, z_h)
                self.dcsids[items_ids] = newdcs
                self.mainwindow.pm.new_defect_cell_study(newdcs, self.mainwindow.currentprojectid, self.defect_study.ID, find_cell[0].ID)
                print 'Successfully added charged cell ' + find_cell[0].treetitle + ' to Defect Study' + self.defect_study.treetitle

    def remove_selection(self, dcid):
        """ Remove selected elements in the 'on' list and add them to the 'off' list """
        selection = dcid
        self.label_dc_name[dcid].destroy()
        self.entry_radius[dcid].destroy()
        self.entry_ze[dcid].destroy()
        self.entry_zh[dcid].destroy()
        self.view_spheres[dcid].destroy()
        self.delete_button[dcid].destroy()
        self.list_off.insert('end', dcid)
        self.on_frame.nitemson -= 1
        cell = self.dcsids[dcid].defect_cell
        self.defect_study.defect_cell_studies.pop(self.dcsids[dcid].ID)
        self.mainwindow.pm.remove_defect_cell_study(self.dcsids[dcid].ID, cell, self.defect_study.ID, self.mainwindow.projects[self.mainwindow.currentprojectid].pid)
        self.dcsids.pop(dcid)

    def add_all(self):
        """ Add all items to the 'on' list and remove them from the 'off' list """
        # [self.list_on.insert(0, f) for f in self.items]
        self.mainwindow.todo()

    def remove_all(self):
        """ Remove all items from the 'on' list and add them to the 'off' list """
        # [self.remove_selection(dcid) for dcid in self.label_dc_name.keys()]
        self.mainwindow.todo()

if __name__ == '__main__':
    GUI = DefectStudyCreationWindow(None, None)
    GUI.mainloop()
