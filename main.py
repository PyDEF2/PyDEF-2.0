"""
    Main PyDEF window
    version: 2.0
    author: Adrien Stoliaroff
    email: adrien.stoliaroff@cnrs-imn.fr
"""

import cPickle as pickle
import numpy as np

# GUI imports
import Tkinter as tk
from Tkinter import Tk, Frame, Menu, Button, Label
from Tkinter import LEFT, RIGHT, TOP, BOTTOM, X, FLAT, RAISED, BOTH, END, DISABLED, NORMAL, VERTICAL
import tkFileDialog as fd
import FileDialog # needed for cx_freeze compilation
from PIL import Image, ImageTk
import ttk
import sys, traceback
import ttk
from Tkinter import Canvas
import tkMessageBox as mb

# Matplotlib for POC
import matplotlib
matplotlib.use('TkAgg')

from numpy import arange, sin, exp, pi
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg #, NavigationToolbar2TkAgg
from matplotlib.backends._backend_tk import NavigationToolbar2Tk #, NavigationToolbar2TkAgg
# implement the default mpl key bindings
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

# PyDEF
import pydef_core.cell as cc
import pydef_core.basic_functions as bf
import pydef_core.defect as dc
import pydef_core.defect_study as ds
import pydef_core.chemical_potentials as pcp
import pydef_core.optical_indices as oi

# PyDEF GUI
import project_manager as pm
import cell_windows as cw
import defect_study_creation_window as dscw
import material_study_windows as msw
import chemical_potentials_windows as cpw
import figure_windows as msfcw
import tkinter_utilities as tu

import sys


class Main_Window(tk.Tk):

    def todo(self):
            print 'Warning! Sorry, this feature has not been developped yet'

    def __init__(self, dev=False):
        tk.Tk.__init__(self, className='PyDEF')
        self.geometry("{0}x{1}+0+0".format(self.winfo_screenwidth()-15, self.winfo_screenheight()))
        self.wm_minsize(width = self.winfo_screenwidth()/2, height = self.winfo_screenwidth()/2)
        self.title('PyDEF 2.0')
        print sys.platform
        platform = sys.platform
        if platform == 'win32' :
            self.state("zoomed")
            icon = ImageTk.PhotoImage(Image.open('Pictures/icon.png'))
            self.call('wm','iconphoto', self._w, '-default', icon)
            self.last_import_dir = 'D:'
            self.last_export_dir = 'D:'
        elif platform == 'linux2':
            icon = ImageTk.PhotoImage(Image.open('Pictures/icon.png'))
            self.call('wm','iconphoto', self._w, icon)
            self.last_import_dir = '.'
            self.last_export_dir = '.'
        else:

            self.last_import_dir = '.'
            self.last_export_dir = '.'
        self.dev = dev
        self.init = False

        # --------------------------------------------------- PROJECTS -------------------------------------------------

        self.projects_mem = self.load_mem()
        self.projects = {}
        for pid in self.projects_mem.keys():
            if pid not in ['last_import_dir', 'last_export_dir']:
                name = self.projects_mem[pid]['name']
                path = self.projects_mem[pid]['path']
                self.load_project(pid)

        try:
            self.last_import_dir = self.projects_mem['last_import_dir']
            self.last_export_dir = self.projects_mem['last_export_dir']
        except KeyError:
            pass

        if len(self.projects.keys()) > 0:
            self.currentprojectid = list(self.projects.keys())[0]
        else:
            self.currentprojectid = ''
        self.currentitemid = ''

        # --------------------------------------------------- MENUBAR --------------------------------------------------

        self.menubar = tk.Menu(self)
        # File menu
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.file_menu.add_command(label='New PyDEF project', accelerator='Ctrl+N', command=self.new_project)
        self.file_menu.add_command(label='Open PyDEF project', accelerator='Ctrl+O', command=self.load_pyd_file)
        self.file_menu.add_command(label='Save all PyDEF projects', accelerator='Ctrl+S', command=lambda:self.save(save_all_projects=True))
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Import VASP calculation', accelerator='Ctrl+I', command=self.importcalc)
        self.menubar.add_cascade(label='File', menu=self.file_menu)
        # Help menu
        self.about_menu = tk.Menu(self.menubar, tearoff=0)
        self.about_menu.add_command(label='About', accelerator='Ctrl+A', command=self.about)
        self.menubar.add_cascade(label='About', menu=self.about_menu)

        self.config(menu=self.menubar)

        # ---------------------------------------------------- TOOLBAR  ------------------------------------------------

        self.toolbar  =  tk.Frame(self.master, bd = 1, relief = RAISED)

        self.newicon = ImageTk.PhotoImage(Image.open('Pictures/Toolbar/new.png'))

        self.createButton = Button(self.toolbar, text='New', image=self.newicon, compound=TOP, command=self.new)
        self.createButton.pack(side=LEFT, padx=2, pady=2)

        self.img2 = Image.open('Pictures/Toolbar/import.png')
        self.useImg2 = ImageTk.PhotoImage(self.img2)

        importButton = Button(self.toolbar, text='Import', image=self.useImg2, compound=TOP, command=self.importcalc)
        importButton.pack(side=LEFT, padx=2, pady=2)

        self.exporticon = ImageTk.PhotoImage(Image.open('Pictures/Toolbar/export.png'))

        exportButton = Button(self.toolbar, text='Export', image=self.exporticon, compound=TOP, command=self.export)
        exportButton.pack(side=LEFT, padx=2, pady=2)

        self.saveicon = ImageTk.PhotoImage(Image.open('Pictures/Toolbar/save.png'))

        saveButton = Button(self.toolbar, text='Save', image=self.saveicon, compound=TOP, command=self.save)
        saveButton.pack(side=LEFT, padx=2, pady=2)

        self.binicon = ImageTk.PhotoImage(Image.open('Pictures/Toolbar/bin.png'))

        deleteButton = Button(self.toolbar, text='Delete', image=self.binicon, compound=TOP, command=self.delete)
        deleteButton.pack(side=LEFT, padx=2, pady=2)

        self.ploticon = ImageTk.PhotoImage(Image.open('Pictures/Toolbar/plot2.png'))

        plotButton = Button(self.toolbar, text='Plot', image=self.ploticon, compound=TOP, command=self.plot)
        plotButton.pack(side=LEFT, padx=2, pady=2)

        self.closeicon = ImageTk.PhotoImage(Image.open('Pictures/Toolbar/delete.png'))

        closeButton = Button(self.toolbar, text='Close', image=self.closeicon, compound=TOP, command=self.close_current_viewed_pane)
        closeButton.pack(side=LEFT, padx=2, pady=2)

        self.exiticon = ImageTk.PhotoImage(Image.open('Pictures/Toolbar/exit.png'))

        exitButton = Button(self.toolbar, text='Exit', image=self.exiticon, compound=TOP, command=self.exit_pydef)
        exitButton.pack(side=LEFT, padx=2, pady=2)

        if self.dev:
            checkButton = Button(self.toolbar, text='Check', command=self.check)
            checkButton.pack(side=LEFT, padx=2, pady=2)

        self.toolbar.pack(side = TOP, fill = X)

        self.def_stud_icon = ImageTk.PhotoImage(Image.open('Pictures/Icons/Defect_Study-50.png'))
        self.mat_stud_icon = ImageTk.PhotoImage(Image.open('Pictures/Icons/Material_Study-50.png'))
        self.mfig_icon = ImageTk.PhotoImage(Image.open('Pictures/Icons/Multiple_subplot_figure-50.png'))
        self.chem_pot_icon = ImageTk.PhotoImage(Image.open('Pictures/FigureIcons/StabilityDomain-50.png'))

        # -------------------------------------------- KEYBOARD SHORTCUTS  ----------------------------------------------

        self.bind("<Control-Key-n>", lambda x:self.new_project())
        self.bind("<Control-Key-s>", lambda x:self.save(save_all_projects=True))
        self.bind("<Control-Key-w>", lambda event: self.close_current_viewed_pane())
        self.bind("<Control-Key-q>", lambda event: self.exit_pydef())
        self.bind("<Control-Key-i>", lambda event: self.importcalc())
        self.bind("<Control-Key-o>", lambda event: self.load_pyd_file())
        self.bind("<Control-Key-e>", lambda event: self.export())
        self.bind("<Control-Key-a>", lambda event: self.about())
        self.bind('<Escape>', lambda event: self.exit_pydef())
        self.bind('<Delete>', lambda event: self.delete())

        # -------------------------------------------- REST OF THE WINDOW  ----------------------------------------------

        self.container = tk.PanedWindow(self.master, bd = 2, bg = 'white', relief = RAISED, showhandle=True)

        # PROJECT MANAGEMENT
        self.project_management_panel = tk.Frame(self.container, bd = 2, bg = 'white', relief = RAISED)
        self.project_notebook = ttk.Notebook(master=self.project_management_panel)
        self.pm_pane = tk.Frame(self.project_notebook, bg = 'white', relief = RAISED)
        self.pm = pm.ProjectsManager(self.pm_pane, self)
        treescrollb = tk.Scrollbar(self.pm_pane, command=self.pm.tree.yview)
        self.pm.tree['yscrollcommand'] = treescrollb.set
        treescrollb.pack(side='left', fill='y')
        self.pm.tree.pack(side='right', fill='both', expand=True)

        self.fm_pane = tk.Frame(self.project_notebook, bg = 'white', relief = RAISED)
        self.fm = pm.FigureManager(self.fm_pane, self)
        fmtreescrollb = tk.Scrollbar(self.fm_pane, command=self.fm.tree.yview)
        self.fm.tree['yscrollcommand'] = fmtreescrollb.set
        fmtreescrollb.pack(side='left', fill='y')
        self.fm.tree.pack(side='right', fill='both', expand=True)

        self.project_notebook.add(self.pm_pane, text='Projects')
        self.project_notebook.add(self.fm_pane, text='Figures')
        self.project_notebook.pack(fill='both', expand=True)

        self.work_container = tk.PanedWindow(self.container, bd = 2, bg = 'white', relief = RAISED, showhandle=True, orient=VERTICAL)
        # WORK FRAME
        self.work_frame = tu.CustomNotebook(master=self.work_container)

        label1 = Label(self.work_frame).pack()

        self.logo_full_name = ImageTk.PhotoImage(Image.open('Pictures/Welcome.png'))

        self.background = tk.Frame(self.work_frame, bd = 2, bg = 'white', relief = RAISED)
        self.logo_full_name = ImageTk.PhotoImage(Image.open('Pictures/Welcome.png'))
        self.welcome = tk.Label(self.background, image=self.logo_full_name, bg = 'white')
        self.welcome.pack(side=TOP, fill= BOTH, expand=True)
        self.background.pack(side=TOP, fill= BOTH, expand=True)

        self.welcome_pane = tk.Frame(self.work_frame, bd = 2, bg = 'white', relief = RAISED)
        welcomtext='Welcome to PyDEF 2.0!'
        tutotext='To start working, please import a calculation using the toolbar button.\n\n'
        tutotext += 'If successfully imported, the calculation appears in the Project Manager on the left of the screen\n'
        tutotext += 'and you are notified in the consol at the bottom of the screen.\n'
        tutotext += 'In the Project Manager, right-click on the calculation to display all possible options.\n\n'
        tutotext += 'Good work!\n'
        self.logo_full_name_transp_bg = ImageTk.PhotoImage(Image.open('Pictures/Welcome-small.png'))
        self.welcome_pane_lab = tk.Label(self.welcome_pane, image=self.logo_full_name_transp_bg, bg = 'white')
        self.welcome_text=tk.Label(self.welcome_pane, text=welcomtext,
        bg = 'white', font=("Courrier", 30))
        self.welcome_pane_text=tk.Label(self.welcome_pane, text=tutotext,
        bg = 'white', justify=LEFT, anchor='w', padx=20,  font=("Courrier", 16))
        self.welcome_pane_lab.pack(side=TOP, fill= BOTH, expand=True)
        self.welcome_text.pack(side=TOP, fill= BOTH, expand=True)
        self.welcome_pane_text.pack(side=LEFT, fill= BOTH, expand=True)
        self.work_frame.add(self.welcome_pane, text='Tutorial')

        # Consol
        self.consol = tk.Frame(self.work_container, bd = 2, bg = 'white', relief = RAISED)
        self.consolText = tk.Text(self.consol, relief = FLAT)
        self.consolText.insert(END, 'Welcome to PyDEF 2.0\n')
        self.consolText.config(font=("consolas", 12), wrap='word')
        self.consolText.grid(row = 0, column = 0, sticky = 'nsew')

        sys.stdout = StdoutRedirector(self.consolText)

        self.consolText.tag_configure('err', foreground = 'red')
        self.consolText.tag_configure('warning', foreground = 'orange')
        self.consolText.tag_configure('info', foreground = 'blue')

        consolscrollb = tk.Scrollbar(self.consol, command=self.consolText.yview)
        self.consolText['yscrollcommand'] = consolscrollb.set
        consolscrollb.grid(row=0, column=1, sticky='nsew', padx=2)

        self.consol.columnconfigure(0, weight=50)
        self.consol.columnconfigure(1, weight=1)
        self.consol.rowconfigure(0, weight=1)
        self.consol.rowconfigure(1, weight=0)

        # Add the 3 panels above to container
        self.container.add(self.project_management_panel, sticky='nsew')
        label = tk.Label(self.container, text='TEST')
        self.work_container.add(self.work_frame, sticky='nsew', minsize=self.winfo_screenheight()*0.66)
        self.work_container.add(self.consol, sticky='nsew')
        self.container.add(self.work_container, sticky='nsew')

        self.container.pack(side=TOP, fill=BOTH, expand=True)

        self.init = True

    def check(self):
        # For Development only
        print 'check'
        print self.projects

    def delete(self):
        self.pm.delete()

    def exit_pydef(self):
        """ Close the main window """
        close = mb.askokcancel('Quit', 'Do you really wish to quit PyDEF?', parent=self)
        if close:
            SaveBeforeExitWindow(self)
            self.save(save_all_projects=True)
            self.quit()
            self.destroy()
        else:
            return None

    def export(self):
        project = self.projects[self.currentprojectid]
        def get_filename():
            filename = fd.asksaveasfilename(parent = self, initialdir = self.last_export_dir,
            title = "Export", filetypes=[("Comma-Separated Values", "*.csv"), ("Tab-Separated Values", "*")])
            if filename.split('.')[-1] == 'csv':
                separator = ','
            else:
                separator = '\t'
            return filename, separator
        if project.object_str_type(self.currentitemid) == 'cell':
            comparison=project.cells[self.currentitemid].gc is not None
            optical_indices = project.cells[self.currentitemid].optical_indices is not None

            choicew = cw.CellExportWindow(self,comparison=comparison, optical_indices=optical_indices)
            choice = choicew.choice
            self.wait_window(choicew)
            filename, separator = get_filename()
            if len(filename) > 0:
                if choice.get() == 'DoS':
                    project.cells[self.currentitemid].export_dos(filename, separator)
                elif choice.get() == 'Bands':
                    project.cells[self.currentitemid].export_bands(filename, separator)
                elif choice.get() == 'OI':
                    try:
                        project.cells[self.currentitemid].optical_indices.export(filename, separator)
                    except AttributeError:
                        message = 'Warning! No optical indices in ' + project.cells[self.currentitemid].treetitle
                        message += ' yet. Plot optical indices and retry please.'
                        print message
                elif choice.get() == 'D':
                    project.cells[self.currentitemid].gc.export_atom_displacements(filename, separator)
                elif choice.get() == 'A-A D':
                    project.cells[self.currentitemid].gc.export_interatomic_distances_variations(filename, separator)
        elif project.object_str_type(self.currentitemid) == 'defect-study':
            filename, separator = get_filename()
            is_embedded, containerID, removeID = project.is_embedded(self.currentitemid)
            if is_embedded:
                project.material_studies[containerID].defect_studies[self.currentitemid].export(filename, separator)
            else:
                project.defect_studies[self.currentitemid].export(filename, separator)
        elif project.object_str_type(self.currentitemid) == 'material-study':
            choicew = msw.MaterialStudyExportWindow(self)
            choice = choicew.choice
            self.wait_window(choicew)
            filename, separator = get_filename()
            if len(filename) > 0:
                mat_stud = project.material_studies[self.currentitemid]
                if choice.get() == 'Defect Concentrations':
                    mat_stud.defect_concentrations.export(filename, separator, mat_stud.cpp)
                elif choice.get() == 'Charge Carriers Concentrations':
                    mat_stud.defect_concentrations.export(filename, separator, mat_stud.ccpp)
                elif choice.get() == 'Fermi Level Variations':
                    mat_stud.defect_concentrations.export(filename, separator, mat_stud.eftpp)

    def printerror(self, message):
        self.consolText.config(state=NORMAL)
        self.consolText.insert(END, '\n' + '!!!Error!!! ' + message + '\n', 'err')
        self.consolText.see(END)
        self.consolText.config(state=DISABLED)
        if self.dev:
            print ('Traceback:\n')
            type_, value_, traceback_ = sys.exc_info()
            traceback.print_tb(traceback_, limit=10, file = sys.stdout)

    def importcalc(self):
        try:
            self.projects[self.currentprojectid]
            filenames = fd.askopenfilenames(parent = self, initialdir = self.last_import_dir,title = "Select OUTCAR and DOSCAR files by pressing Ctrl + left click")
            if len(filenames)>0:
                # recognize which one is the OUTCAR (start with vasp)
                if len(filenames)>1:
                    line0 = open(filenames[0], 'r').readline()
                    if line0.find('vasp') > -1:
                        outcarpath = filenames[0]
                        doscarpath = filenames[1]
                    else:
                        outcarpath = filenames[1]
                        doscarpath = filenames[0]
                    try:
                        self.projects[self.currentprojectid].add_cell(cc.Cell(outcarpath, doscarpath))
                    except AssertionError, e:
                        self.printerror(str(e))
                    except Exception, e:
                        self.printerror(str(e))
                else:
                    try:
                        outcarpath = filenames[0]
                        self.projects[self.currentprojectid].add_cell(cc.Cell(outcarpath, ''))
                    except Exception, e:
                        self.printerror(str(e))
                self.last_import_dir = '/'.join(outcarpath.split('/')[0:-1])
        except KeyError, e:
            self.printerror('Please select a project before importing calculations!')


    def new(self):
        try:
            self.new_cascade.destroy()
        except AttributeError:
            pass
        self.new_cascade = tk.Menu(self, tearoff=0)
        self.new_cascade.items = 5
        try:
            self.new_cascade.add_command(label="Project", compound=LEFT, command=self.new_project) #, image=self.icontest)
            self.new_cascade.add_command(label="Chemical Potentials", compound=LEFT, command=self.new_chemical_potentials, image=self.chem_pot_icon)
            self.new_cascade.add_command(label="Defect Study", compound=LEFT, command=self.new_defect_study, image=self.def_stud_icon)
            self.new_cascade.add_command(label="Material Study", compound=LEFT, command=self.new_material_study, image=self.mat_stud_icon)
            self.new_cascade.add_command(label="Mutltiple subplots figure", compound=LEFT, command=self.new_multiple_subplot_figure, image=self.mfig_icon)
            self.new_cascade.post(self.createButton.winfo_rootx(), self.createButton.winfo_rooty() + self.createButton.winfo_height())
        except bf.pydefDefectCreationError, e:
            self.printerror(str(e))
        # Close contextual menu when mouse leaves menu
        def popupFocusOut(event=None):
            self.new_cascade.unpost()
            self.new_cascade.delete(0, self.new_cascade.items)
        self.new_cascade.bind("<Leave>", popupFocusOut)

    def new_project(self):
        if len(self.projects)<10:
            new_id = str('P0'+str(len(self.projects)))
        else:
            new_id = str('P'+str(len(self.projects)))
        new_proj = pm.Project(new_id, 'New Project', self)
        self.projects[new_id] = new_proj
        self.projects_mem[new_id] = {'path':None, 'name': new_proj.name}
        self.pm.new_project(new_proj)
        self.fm.new_project(new_proj)
        print 'New Project created successfully'

    def new_chemical_potentials(self):
        try:
            cpw.ChemicalPotentialsCreationWindow(self, self.projects[self.currentprojectid], None)
        except KeyError:
            if self.currentprojectid not in self.projects.keys():
                self.printerror('No Project! Please create a Project first')
            else:
                self.printerror('No host cell! Please declare a host cell first')

    def new_defect_study(self):
        try:
            dscw.DefectStudyCreationWindow(self, self.projects[self.currentprojectid], None)
        except bf.pydefDefectCreationError, e:
            self.printerror(str(e))
        except KeyError:
            self.printerror('No Project! Please create a Project first')

    def new_material_study(self):
        try:
            msw.MaterialStudyCreationWindow(self, self.projects[self.currentprojectid], None)
        except bf.pydefDefectCreationError, e:
            self.printerror(str(e))
        except KeyError:
            self.printerror('No Project! Please create a Project first')

    def new_multiple_subplot_figure(self):
        msfcw.MultipleSubplotFigureCreationWindow(self)

    def update_work_frame(self, frame, panetitle):
        """update the work frame of the main window with the given frame"""
        self.work_frame.add(frame, text=panetitle)
        self.work_frame.select(frame)

    def close_current_viewed_pane(self):
        try:
            self.work_frame.forget(self.work_frame.index(self.work_frame.select()))
        except tk.TclError:
            pass
            # nothing to remove

    def create_defect_study(self, new_defect_study):
        self.projects[self.currentprojectid].add_defect_study(new_defect_study)

    def plot(self):
        """plot the default figure of the currently selected object in the work frame"""
        fig = None
        project = self.projects[self.currentprojectid]
        if project.object_str_type(self.currentitemid) == 'cell':
            cell =  project.cells[self.currentitemid]
            panetitle = cell.treetitle
            print 'Plot DoS of cell ' + panetitle
            # project.cells[self.currentitemid]
            try:
                fig = cell.plot_dos(dpp=cell.lastdpp)
            except AttributeError, e:
                self.printerror('Impossible to plot DoS as no DOSCAR provided for this calculation!')
        elif project.object_str_type(self.currentitemid) == 'chem-pot':
            fig = project.chemical_potentials.plot_stability_domain(None, project.chemical_potentials.lastppp)
            listname = [ppp.name for ppp in project.pp['ppp'].values()]
            if project.chemical_potentials.lastppp.name not in listname:
                project.pp['ppp'][project.chemical_potentials.lastppp.name] = project.chemical_potentials.lastppp
            panetitle = project.chemical_potentials.synthesized.rname
            print 'Plot ' + panetitle + ' Stability Domain'
        elif project.object_str_type(self.currentitemid) == 'defect-study':
            is_embedded, containerID, removeID = project.is_embedded(self.currentitemid)
            if not is_embedded:
                defect_study = project.defect_studies[self.currentitemid]
                panetitle = defect_study.treetitle
                print 'Plot Defect Formation Energy of Defect Study ' + panetitle
                fig = defect_study.plot_formation_energy()
            else:
                defect_study = project.material_studies[containerID].defect_studies[self.currentitemid]
                panetitle = defect_study.treetitle
                print 'Plot Defect Formation Energy of Defect Study ' + panetitle
                fig = defect_study.plot_formation_energy()
        elif project.object_str_type(self.currentitemid) == 'material-study':
            material_study = project.material_studies[self.currentitemid]
            panetitle = material_study.treetitle
            print 'Plot Defect Formation Energies of Material Study ' + panetitle
            fig = material_study.plot_formation_energy(fpp=material_study.lastfpp)

        if fig is not None:
            frame = tk.Frame(self.work_frame, bd = 2, bg = 'white', relief = RAISED)

            figframe = self.fig_to_canvas(fig, frame)
            self.update_work_frame(frame, panetitle)

    def plot_mfigure(self, mfigure):
        try:
            fig = mfigure.plot()
            if fig is not None:
                frame = tk.Frame(self.work_frame, bd = 2, bg = 'white', relief = RAISED)
                figframe = self.fig_to_canvas(fig, frame)
                self.update_work_frame(frame, mfigure.name)
        except AttributeError, e:
            self.printerror(str(e))
        except ValueError, e:
            self.printerror(str(e))

    def plot_optical_indices(self, opp=None):
        project = self.projects[self.currentprojectid]
        if project.object_str_type(self.currentitemid) == 'cell':
            cell = project.cells[self.currentitemid]
            # check if cell already has OpticalIndices attribute
            try:
                len(cell.optical_indices.components)
            except AttributeError, e:
                if bf.grep(cell.outcar, "DIELECTRIC FUNCTION") is not None or bf.grep(cell.outcar, "DIELECTRIC TENSOR") is not None:
                    cell.optical_indices = oi.OpticalIndices(cell.outcar)
                else:
                    message = 'Warning! There is no dielectric function to plot in this file! '
                    message += '\nSee https://cms.mpi.univie.ac.at/wiki/index.php/Dielectric_properties_of_SiC for VASP help'
                    print message
                    return None
            if opp is None:
                fig = cell.optical_indices.plot(pp=cell.optical_indices.lastopp)
            else:
                fig = cell.optical_indices.plot(pp=opp)
            frame = tk.Frame(self.work_frame, bd = 2, bg = 'white', relief = RAISED)
            self.fig_to_canvas(fig, frame)
            self.update_work_frame(frame, cell.treetitle)

    def plot_band_diagram(self):
        project = self.projects[self.currentprojectid]
        if project.object_str_type(self.currentitemid) == 'cell':
            cell = project.cells[self.currentitemid]
            fig = cell.plot_band_diagram(bpp=cell.lastbpp)
            frame = tk.Frame(self.work_frame, bd = 2, bg = 'white', relief = RAISED)
            self.fig_to_canvas(fig, frame)
            self.update_work_frame(frame, cell.treetitle)

    def fit_bands(self):
        project = self.projects[self.currentprojectid]
        if project.object_str_type(self.currentitemid) == 'cell':
            cell = project.cells[self.currentitemid]
            fig = cell.fit_bands()
            frame = tk.Frame(self.work_frame, bd = 2, bg = 'white', relief = RAISED)
            self.fig_to_canvas(fig, frame)
            self.update_work_frame(frame, cell.treetitle)

    def plot_transition_levels(self):
        if self.projects[self.currentprojectid].object_str_type(self.currentitemid) == 'defect-study':
            is_embedded, containerID, removeID = self.projects[self.currentprojectid].is_embedded(self.currentitemid)
            if not is_embedded:
                def_study = self.projects[self.currentprojectid].defect_studies[self.currentitemid]
                panetitle = def_study.treetitle
                print 'Plot Defect Transition Levels of Defect Study ' + panetitle
                fig = def_study.plot_transition_levels(tpp=def_study.lasttpp)
            else:
                def_study = self.projects[self.currentprojectid].material_studies[containerID].defect_studies[self.currentitemid]
                panetitle = def_study.treetitle
                print 'Plot Defect Transition Levels of Defect Study ' + panetitle
                fig = def_study.plot_transition_levels(tpp=def_study.lasttpp)
        elif self.projects[self.currentprojectid].object_str_type(self.currentitemid) == 'material-study':
            material_study = self.projects[self.currentprojectid].material_studies[self.currentitemid]
            panetitle = material_study.treetitle
            print 'Plot Defect Transition Levels of Defect Study ' + panetitle
            fig = material_study.plot_transition_levels(tpp=material_study.lasttpp)
        frame = tk.Frame(self.work_frame, bd = 2, bg = 'white', relief = RAISED)

        self.fig_to_canvas(fig, frame)
        self.update_work_frame(frame, panetitle)

    def plot_defect_concentrations(self, code=0):
        """code: 0 for Defect Concentrations, 1 for Charge Carriers concentration and 2 for E_F"""
        if code in [0,1,2]:
            if self.projects[self.currentprojectid].object_str_type(self.currentitemid) == 'material-study':
                material_study = self.projects[self.currentprojectid].material_studies[self.currentitemid]
                for defstud in material_study.ds_list:
                    defe = defstud.dcs[0].defects[0]
                try:
                    material_study.defect_concentrations = ds.ConcentrationsCalculation(material_study)
                except bf.PyDEFInputError, e:
                    self.printerror(str(e))
                try:
                    if code == 0:
                        fig = material_study.defect_concentrations.plot(pp=material_study.cpp)
                    elif code ==1:
                        fig = material_study.defect_concentrations.plot(pp=material_study.ccpp)
                    else:
                        fig = material_study.defect_concentrations.plot(pp=material_study.eftpp)
                    frame = tk.Frame(self.work_frame, bd = 2, bg = 'white', relief = RAISED)
                    self.fig_to_canvas(fig, frame)
                    panetitle = material_study.treetitle + ' dc'
                    self.update_work_frame(frame, panetitle)
                except bf.PyDEFSolveError, e:
                    self.printerror(str(e))
                except TypeError, e:
                   self.printerror('Unknown number of sites for the defects! Please specify the number of sites for each defect')
                except AttributeError, e:
                    message = 'Please specify a DOSCAR file for each calculation in Material Study ' + material_study.treetitle
                    message += ' as it is mandatory for Concentrations Calculations'
                    self.printerror(message)

    def fig_to_canvas(self, fig, frame):

        self.mem = None

        def on_pick(event):
            picked_obj = event.artist
            self.mem = picked_obj

        def on_move(event):
            if self.mem is not None:
                if type(self.mem) == matplotlib.legend.Legend:
                    try:
                        inv = event.inaxes.transAxes.inverted()
                        self.mem.set_bbox_to_anchor(inv.transform((event.x,event.y)))
                        canvas.draw()
                    except AttributeError, e:
                        pass
                    except TypeError:
                        pass
                else:
                    self.mem.set_position((event.xdata,event.ydata))
                    try:
                        canvas.draw()
                    except TypeError:
                        pass

        def on_release(event):
            self.mem = None

        def on_scroll(event):

            xmin, xmax = event.inaxes.get_xlim()
            ymin, ymax = event.inaxes.get_ylim()
            if event.step > 0:
                event.inaxes.set_xlim((1.05*xmin, 0.95*xmax))
                event.inaxes.set_ylim((1.05*ymin, 0.95*ymax))
            else:
                event.inaxes.set_xlim((0.95*xmin, 1.05*xmax))
                event.inaxes.set_ylim((0.95*ymin, 1.05*ymax))
            try:
                canvas.draw()
            except TypeError:
                pass

        figure_frame = Frame(frame)
        toolbar_frame = Frame(frame)

        # frame.rowconfigure(0, weight = 5)
        # frame.rowconfigure(1, weight = 1)

        self.update()
        c_height = self.container.winfo_height()
        c_width = self.container.winfo_width()

        # print 'h %s '%c_height
        # print 'w %s ' %c_width

        pix_per_inch = self.winfo_fpixels('1i')
        fig.set_size_inches(0.8*c_width/pix_per_inch,0.65*c_height/pix_per_inch)
        # print fig.get_size_inches()
        canvas = FigureCanvasTkAgg(fig, master=figure_frame)
        canvas.draw()
        canvas.mpl_connect('pick_event', on_pick)
        canvas.mpl_connect('motion_notify_event', on_move)
        canvas.mpl_connect('button_release_event', on_release)
        canvas.mpl_connect('scroll_event', on_scroll)
        # canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=False)
        # canvas.get_tk_widget().grid(row=0,  sticky='nsew')
        # self.ctoolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        self.ctoolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
        self.ctoolbar.update()
        canvas._tkcanvas.pack(side=TOP, fill=BOTH, expand=False)
        # canvas._tkcanvas.grid(row=0,  sticky='nsew')
        # figure_frame.grid(row=0,  sticky='nsew')
        # toolbar_frame.grid(row=1,  sticky='nsew')
        figure_frame.pack(side=TOP, fill=BOTH, expand=False)
        toolbar_frame.pack(side=BOTTOM, fill=BOTH, expand=True)


    def load_project(self, pid):
        try:
            projectpath = self.projects_mem[pid]['path']
            if projectpath.split('.')[-1] != 'pyd':
                print 'Warning! Are you sure this project was saved correctly? The file\'s extension is not *.pyd.'
            with open(projectpath, "rb") as f:
                self.projects[pid] = pickle.load(f)
                self.projects[pid].mainwindow = self
                self.projects[pid].pid = pid
            print 'Project ' + self.projects[pid].name + ' loaded successfully!\n'
        except IOError:
            print 'No *.pyd file found for Project ' + pid + '! Project deleted.'
            if pid in self.projects.keys():
                self.projects.pop(pid)
        except KeyError:
            self.printerror('Sorry! I do not remember any path to a *.pyd save file for this project.')
        except EOFError:
            if self.init:
                self.printerror('Error while reading saved *.pyd file.')
            else:
                print '!!!Error!!! Error while reading saved *.pyd file.'


    def save_project(self, project):
        if project.pid in self.projects_mem.keys() and self.projects_mem[project.pid]['path'] is not None:
            projectpath = self.projects_mem[project.pid]['path']
        else:
           projectpath = "./Save-Projects/" + project.name.replace(' ', '_') + "_" + str(np.random.randint(0, sys.maxint)) + ".pyd"
           # The random integer here is to ensure unicity of the path in case users want to exchange *.pyd files
        if len(project.mfigures.values()) > 0:
            for mfig in project.mfigures.values():
                mfig.figure = None
        with open(projectpath, "wb") as f:
            project.mainwindow = None
            pickle.dump(project, f, pickle.HIGHEST_PROTOCOL)
            project.mainwindow = self
        self.projects_mem[project.pid] = {'name': project.name, 'path': projectpath}
        self.projects_mem['last_import_dir'] = self.last_import_dir
        self.projects_mem['last_export_dir'] = self.last_export_dir


    def load_mem(self):
        try:
            with open("./Save-Projects/PyDEF_memory.pyd", "rb") as f:
                return pickle.load(f)
        except EOFError, e :
            print 'Warning! PyDEF memory file found but is empty. '
            return {}
        except IOError, e:
            print 'Warning! No PyDEF memory found. '
            return {}


    def save(self, save_all_projects=False):
        if save_all_projects:
            for project in self.projects.values():
                self.save_project(project)
            print 'All %i projects saved successfully!' %len(self.projects.keys())
        else:
            self.save_project(self.projects[self.currentprojectid])
            print 'Project ' + self.projects[self.currentprojectid].name + ' saved successfully!'
        with open("./Save-Projects/PyDEF_memory.pyd", "wb") as f:
            pickle.dump(self.projects_mem, f, pickle.HIGHEST_PROTOCOL)


    def load_pyd_file(self):
        try:
            path = fd.askopenfilenames(parent=self, initialdir=self.last_import_dir,title="Import *.pyd file")[0]
            if path.split('.')[-1] != 'pyd':
                print 'Warning! Are you sure this project was saved correctly? The file\'s extension is not *.pyd.'
            pid = self.new_project_key()
            with open(path, "rb") as f:
                self.projects[pid] = pickle.load(f)
                self.projects[pid].mainwindow = self
                self.projects_mem[pid] = {'name': self.projects[pid].name, 'path': path}
                self.load_project(pid)
                self.projects[pid].pid = pid
                self.currentprojectid = pid
            if self.projects[pid] is not None:
                self.pm.new_project(self.projects[pid])
                self.fm.new_project(self.projects[pid])
                self.last_import_dir = path
        except IndexError:
            # The user has closed the FileDialog window
            pass

    def about(self):
        AboutPyDEF(self)

    def new_project_key(self):
        if len(self.projects.keys()) + 1 <10:
            return 'P0' + str(len(self.projects.keys()) + 1)
        else:
            return 'P' + str(len(self.projects.keys()) + 1)


class AboutPyDEF(tk.Toplevel):

    def __init__(self, mainwindow):
        tk.Toplevel.__init__(self, mainwindow)
        self.resizable(False, False)
        self.mainwindow = mainwindow

        self.main_frame = tk.Frame(self)
        self.main_frame.grid(sticky='nsew')

        tk.Label(self.main_frame, image=self.mainwindow.logo_full_name_transp_bg, bg = 'white').grid(row=0, column=0, sticky='nsew')
        info_pane = tk.Frame(self.main_frame, bg='white')
        tk.Label(info_pane, text='version 64-bit', bg='white', padx=10).grid()
        tk.Label(info_pane, text='Build date: March 2018', bg='white', padx=10).grid()
        info_pane.grid(row=0, column=1, sticky='nsew')
        notebook = ttk.Notebook(master=self.main_frame)
        license_pane = tk.Frame(notebook)
        credits_pane = tk.Frame(notebook)
        developers = 'Developers: Adrien Stoliaroff'
        authors = 'On an original idea of Dr. Stephane Jobic and Dr. Camille Latouche'
        acknowledgments = 'If you use this software in a scientific publication'
        acknowledgments += ', please quote the following article:'
        quote = 'Article quote'
        bibtex_quote = 'Article quote in bibtex format'
        tk.Label(credits_pane, text=developers, bg='white').grid(sticky='nsew')
        tk.Label(credits_pane, text=authors, bg='white').grid(sticky='nsew')
        tk.Label(credits_pane, text=acknowledgments, bg='white').grid(sticky='nsew')
        tk.Label(credits_pane, text=quote, bg='white').grid(sticky='nsew')
        tk.Label(credits_pane, text=bibtex_quote, bg='white').grid(sticky='nsew')
        notebook.add(license_pane, text='License')
        notebook.add(credits_pane, text='Credits')
        notebook.grid(sticky='nsew', columnspan=2)

        tk.Button(self.main_frame, text='OK', command=self.destroy).grid(columnspan=2, sticky='e')


class SaveBeforeExitWindow(tk.Toplevel):

    def __init__(self, mainwindow):
        tk.Toplevel.__init__(self, mainwindow)
        self.resizable(False, False)
        self.mainwindow = mainwindow

        self.main_frame = tk.Frame(self)
        self.main_frame.grid(sticky='nsew')

        tk.Label(self.main_frame, image=self.mainwindow.logo_full_name_transp_bg, bg = 'white').grid(sticky='nsew')
        tk.Label(self.main_frame, text='Saving projects...').grid(sticky='nsew')


class IORedirector(object):
    '''A general class for redirecting I/O to this Text widget.'''
    def __init__(self, text_area):
        self.text_area = text_area


class StdoutRedirector(IORedirector):
    '''A class for redirecting stdout to this Text widget.'''
    def write(self,str):
        if len(str)>1:
            self.text_area.config(state=NORMAL)
            #so that messages are ok for both script and GUI use of PyDEF
            message = str[0].replace('\n','') + str[1:-1] + str[-1:].replace('\n','')
            if message.find('arning') >-1:
                self.text_area.insert(END, '\n' + message, 'warning')
            else:
                self.text_area.insert(END, '\n' + message)
            self.text_area.see(END)
            self.text_area.config(state=DISABLED)


if __name__ == "__main__":
    GUI = Main_Window(dev=False)
    GUI.protocol("WM_DELETE_WINDOW", GUI.exit_pydef)
    GUI.mainloop()
