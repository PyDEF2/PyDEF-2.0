import numpy as np
import copy

import Tkinter as tk
import ttk
import tkFileDialog as fd
from tkColorChooser import askcolor              
import tkMessageBox as mb
from Tkinter import LEFT, RIGHT, TOP, BOTTOM, END

import tkinter_utilities as tu
import pydef_core.basic_functions as bf
import pydef_core.cell as pc
import pydef_core.optical_indices as poi


class CellsInfoWindow(tk.Toplevel):

    def __init__(self, parent, cell):

        tk.Toplevel.__init__(self, parent)
        self.resizable(False, False)
        self.maxsize(width=self.winfo_screenwidth(), height=4*self.winfo_screenheight()/5)

        self.cell = cell

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(expand=True, fill='both')
        
        self.title(self.cell.treetitle + ' VASP Calculation Settings Window')

        # ---------------------------------------------- SYSTEM PROPERTIES ---------------------------------------------

        self.sysprop_frame_label = ttk.Label(self, text='System properties', font='-weight bold')
        self.sysprop_frame = ttk.LabelFrame(self.main_frame, labelwidget=self.sysprop_frame_label)
        self.sysprop_frame.grid(row=1, column=0, sticky='nswe', padx=5, pady=5)

        props = ('System name', 'Nb atoms', 'Nb electrons', 'Charge', 'a', 'b', 'c')
        
        cell_params = ['%.3f (A)' %np.sqrt(sum([i*i for i in cell.cell_parameters[axi]])) for axi in range(0,3)]
        props_values = (cell.name, cell.nb_atoms_tot, cell.nb_electrons, cell.charge, cell_params[0], cell_params[1], cell_params[2])
        for t, v, i in zip(props, props_values, range(len(props))):
            ttk.Label(self.sysprop_frame, text=t + ': %s' % v).grid(row=i, column=0, sticky='w')

        # ------------------------------------------------- SYSTEM TAGS ------------------------------------------------

        self.systags_frame_label = ttk.Label(self, text='Calculation properties', font='-weight bold')
        self.systags_frame = ttk.LabelFrame(self.main_frame, labelwidget=self.systags_frame_label)
        self.systags_frame.grid(row=1, column=1, sticky='nswe', padx=5, pady=5)

        tags = ('Method', 'NEDoS', 'EDIFF', 'ENCUT', 'ISMEAR', 'LORBIT', 'ISPIN', 'ICHARG')
        tags_values = (cell.functional, cell.nedos, cell.ediff, cell.encut, cell.ismear, cell.lorbit, cell.ispin,
                       cell.icharg)

        for t, v, i in zip(tags, tags_values, range(len(tags))):
            ttk.Label(self.systags_frame, text=t + ': %s' % v).grid(row=i, column=0, sticky='w')

        # -------------------------------------------- CALCULATION RESULTS ---------------------------------------------

        self.results_frame_label = ttk.Label(self, text='Calculations results', font='-weight bold')
        self.results_frame = ttk.LabelFrame(self.main_frame, labelwidget=self.results_frame_label)
        self.results_frame.grid(row=2, columnspan=2, sticky='nswe', padx=5, pady=5)
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_columnconfigure(1, weight=1)

        res_1 = ('Nb electronic iterations', 'Nb k-points', 'Nb bands')
        res_values_1 = (cell.nb_iterations, cell.nkpts, cell.nbands)
        res_2 = ('Free energy', 'Fermi energy', 'VBM energy', 'CBM energy', 'Gap')
        res_values_2 = (cell.total_energy, cell.fermi_energy, cell.vbm_energy, cell.cbm_energy, cell.gap)

        for t, v, i in zip(res_1, res_values_1, range(len(res_1))):
            ttk.Label(self.results_frame, text=t + ': %s' % v).grid(row=i, column=0, sticky='w')

        for t, v, i in zip(res_2, res_values_2, range(len(res_2))):
            ttk.Label(self.results_frame, text=t + ': %s eV' % v).grid(row=i, column=1, sticky='w')
        
        ttk.Label(self.results_frame, text=' VBM reached at K-points ' + 
        ','.join([str(i+1) for i in cell.k_pts_vbm]) + ' for bands ' 
        + ','.join([str(i+1) for i in cell.b_vbm])).grid(row=len(res_2)+1, column=1, sticky='w')
        
        ttk.Label(self.results_frame, text=' CBM reached at K-points ' + 
        ','.join([str(i+1) for i in cell.k_pts_cbm]) + ' for bands ' 
        + ','.join([str(i+1) for i in cell.b_cbm])).grid(row=len(res_2)+2, column=1, sticky='w')
        
        if cell.direct_band_gap:
            adj = 'Direct '
        elif cell.direct_band_gap:
            adj = 'Indirect '
        else:
            adj = ''
            print 'Warning! Uh oh, the gap could not be determined direct or indirect'
            
        ttk.Label(self.results_frame, text= adj + ' Band Gap' ).grid(row=len(res_2)+3, column=1, sticky='w')

        # Bands data
        self.bands_frame = ttk.Frame(self.results_frame)
        self.bands_frame.grid(row=max([len(res_1), len(res_2)])+4, columnspan=2, sticky='nswe', padx=5, pady=5)
        tree = ttk.Treeview(self.bands_frame)
        tree.pack(side='left', fill='both', expand=True)
        yscrollbar = ttk.Scrollbar(self.bands_frame, orient='vertical', command=tree.yview)
        yscrollbar.pack(side='right', fill='y')

        tree['columns'] = ('1', '2')
        tree.column('#0', width=65)
        tree.column('1', width=50)
        tree.column('2', width=40)
        tree.heading('#0', text='K-point')
        tree.heading('1', text='Energy')
        tree.heading('2', text='Occupation')
        tree.configure(yscrollcommand=yscrollbar.set)

        bands_data = cell.bands_data
        kpoints_indices = range(1, cell.nkpts + 1)

        if cell.ispin == 1.:
            
            kpoints_labels = ['kpoint %s (%.2f, %.2f, %.2f)' % (tuple([f]) + tuple(cell.kpoints_coords[f-1])) for f in kpoints_indices]
            
        else:
            kpoints_labels = ['kpoint %s (spin up, %.2f, %.2f, %.2f)' % (tuple([f]) + tuple(cell.kpoints_coords[f-1])) for f in kpoints_indices] + ['kpoint %s (spin down)' % f for f in kpoints_indices]

        for kpoint, label in zip(bands_data, kpoints_labels):
            kpoint_id = tree.insert('', kpoints_labels.index(label), text=label)
            for band, band_nb in zip(np.transpose(kpoint), range(1, cell.nbands + 1)):
                tree.insert(kpoint_id, 'end', text='band ' + str(band_nb), values=(band[0], band[1]))


class CellExportWindow(tk.Toplevel):

    def __init__(self, mainwindow, comparison=False, optical_indices=False):
        tk.Toplevel.__init__(self, mainwindow)
        self.resizable(False, False)
        self.maxsize(width=self.winfo_screenwidth(), height=3*self.winfo_screenheight()/5)

        self.main_frame = tk.Frame(self)
        self.main_frame.grid(sticky='nsew')
        self.choice = tk.StringVar()
        tk.Label(self.main_frame, text='Export ').grid(row=0, column=0)
        tk.Radiobutton(self.main_frame, value='DoS', variable=self.choice, text='Density of States', tristatevalue='x').grid(sticky='w')
        tk.Radiobutton(self.main_frame, value='Bands', variable=self.choice, text='Bands', tristatevalue='x').grid(sticky='w')
        if optical_indices:
            tk.Radiobutton(self.main_frame, value='OI', variable=self.choice, text='Optical Indices', tristatevalue='x').grid(sticky='w')
        if comparison:
            tk.Radiobutton(self.main_frame, value='D', variable=self.choice, text='Atomic Displacements after Defect Introduction', tristatevalue='x').grid(sticky='w')
            tk.Radiobutton(self.main_frame, value='A-A D', variable=self.choice, text='Interatomic Distances Variations', tristatevalue='x').grid(sticky='w')
        tk.Button(self.main_frame, text='OK', command=self.validate).grid(sticky='e')
        
    def validate(self):
        choice = self.choice.get()
        self.destroy()
        return choice
        

class DosPlotParametersWindow(tk.Toplevel):

    def __init__(self, mainwindow, cell, dpp):

        tk.Toplevel.__init__(self, mainwindow)
        self.resizable(False, False)
        self.maxsize(width=self.winfo_screenwidth(), height=4*self.winfo_screenheight()/5)
        self.minsize(height=4*self.winfo_screenheight()/5)
        
        self.cell = cell
        self.dpp = dpp
        self.mainwindow = mainwindow
        self.project = self.mainwindow.projects[self.mainwindow.currentprojectid]

        self.main_frame = ttk.Frame(self)
        self.main_frame.grid(sticky='nsew')
        self.contain_frame = tu.ScrollableTableFrame(self.main_frame, '', []).interior
        
        cb_kwargs = {'onvalue': True, 'offvalue': False}
        
        self.title(self.cell.treetitle + ' DoS Plot Parameters Edition Window')
        
        # --------------------------------------------------- DPP name -------------------------------------------------
        
        self.label1 = tk.Label(self.contain_frame, text='Plot Parameters Name', pady=10)
        
        self.nameframe = tk.Frame(self.contain_frame)
        self.nameframe.grid(row=1, column=0)
        namelist = [dpp.name for dpp in self.project.pp['dpp'].values()]
        self.dppname = ttk.Combobox(self.nameframe, values=namelist, width=40) #, validate='focusout', validatecommand=self.dpp_select_create)
        self.dppname.set(self.dpp.name)
        self.dppname.bind("<<ComboboxSelected>>", self.dpp_select)
        self.label1.grid(row=0, column=0)
        self.dppname.grid(row=1, column=0)
        tk.Button(self.nameframe, text='Save as new parameters', command=self.dpp_create).grid(row=1, column=1)
        
        # --------------------------------------------------- DoS type -------------------------------------------------

        self.spin_var = tk.BooleanVar(value=dpp.display_spin)

        # Frame label
        self.dostype_frame_label_frame = ttk.Frame(self)
        ttk.Label(self.dostype_frame_label_frame, text='DoS displayed', font='-weight bold').pack(side='left')
        # if self.cell.ispin == 2:
        #     ttk.Checkbutton(self.dostype_frame_label_frame, text='Spin projection', variable=self.spin_var, **cb_kwargs).pack()

        # Frame
        self.dostype_frame = ttk.LabelFrame(self.contain_frame, labelwidget=self.dostype_frame_label_frame)
        self.dostype_frame.grid(row=2, column=0, sticky='nswe', padx=5)
        self.dostype_frame.grid_columnconfigure(0, weight=1)

        # Variables
        self.opas_items_choice = dpp.choice_opas  # Initial choice for the OPAS items choice
        self.opa_items_choice = dpp.choice_opa  # Initial choice for the OPA items choice
        self.proj_colors_choice = dpp.colors_proj  # Projected DoS colors choice
        self.tot_colors_choice = dpp.colors_tot  # Total projected DoS colors choice

        # -------------------------------------------------- TOTAL DoS -------------------------------------------------

        self.totdos_var = tk.BooleanVar(value=dpp.display_total_dos)
        ttk.Checkbutton(self.dostype_frame, text='Total DoS', variable=self.totdos_var, **cb_kwargs).grid(row=2, column=0)

        # ------------------------------------------------ PROJECTED DoS -----------------------------------------------

        self.projdos_var = tk.BooleanVar()

        # Labelframe and checkbutton
        self.projdos_cb = ttk.Checkbutton(self, text='Projected DoS', variable=self.projdos_var, command=self.enable_proj_dos, **cb_kwargs)
        self.projdos_frame = ttk.LabelFrame(self.dostype_frame, labelwidget=self.projdos_cb, labelanchor='n')
        self.projdos_frame.grid(row=1, column=0, sticky='nswe', padx=5)
        self.projdos_frame.grid_columnconfigure(0, weight=1)
        self.projdos_frame.grid_columnconfigure(1, weight=1)

        # DoS type
        self.dostype_var = tk.StringVar(value=dpp.dos_type)
        ttk.Label(self.projdos_frame, text='DoS for each').grid(row=0, column=0, sticky='w')
        ttk.Radiobutton(self.projdos_frame, text='Atomic species', variable=self.dostype_var, value='OPAS').grid(row=1, column=0)
        ttk.Radiobutton(self.projdos_frame, text='Atom', variable=self.dostype_var, value='OPA').grid(row=1, column=1)

        # Projection choice
        self.totprojdos_var = tk.BooleanVar(value=dpp.tot_proj_dos)
        ttk.Label(self.projdos_frame, text='Projection').grid(row=2, column=0, sticky='w')
        ttk.Radiobutton(self.projdos_frame, text='Orbitals projection', variable=self.totprojdos_var, value=False).grid(row=3, column=0)
        ttk.Radiobutton(self.projdos_frame, text='Total DoS', variable=self.totprojdos_var, value=True).grid(row=3, column=1)

        # Areas or lines
        self.plotareas_var = tk.BooleanVar(value=dpp.plot_areas)
        ttk.Label(self.projdos_frame, text='Projected DoS style').grid(row=4, column=0, sticky='w')
        ttk.Radiobutton(self.projdos_frame, text='Filled areas', variable=self.plotareas_var, value=True).grid(row=5, column=0)
        ttk.Radiobutton(self.projdos_frame, text='Lines', variable=self.plotareas_var, value=False).grid(row=5, column=1)

        ttk.Label(self.projdos_frame, text=' ').grid(row=6, column=0)  # white space

        ttk.Button(self.projdos_frame, text='Data plotted', command=self.open_atoms_choice_window).grid(row=7, column=0)
        ttk.Button(self.projdos_frame, text='Colours', command=self.open_colour_choice_window).grid(row=7, column=1)
        
        if self.cell.lorbit == 11:
            self.projdos_var.set(dpp.display_proj_dos)
        else:
            self.projdos_var.set(False)
            self.projdos_cb.configure(state='disabled')
            tu.disable_frame(self.projdos_frame)

        # ------------------------------------------------ PLOT DISPLAY ------------------------------------------------

        self.display_frame_label = ttk.Label(self, text='Options on data displayed', font="-weight bold")
        self.display_frame = ttk.LabelFrame(self.contain_frame, labelwidget=self.display_frame_label)
        self.display_frame.grid(row=3, column=0, sticky='nswe', padx=5)

        # Fermi level
        self.efdisplay_var = tk.BooleanVar(value=dpp.display_Fermi_level)
        ttk.Checkbutton(self.display_frame, text='Fermi level', variable=self.efdisplay_var, **cb_kwargs).grid(row=0, column=0, sticky='w')

        # Band extrema
        self.bedisplay_var = tk.BooleanVar(value=dpp.display_BM_levels)
        ttk.Checkbutton(self.display_frame, text='Band extrema levels', variable=self.bedisplay_var, **cb_kwargs).grid(row=1, column=1, sticky='w')

        self.fermishift_var = tk.BooleanVar(value=dpp.fermi_shift)
        ttk.Checkbutton(self.display_frame, text='Fermi level as zero of energy', variable=self.fermishift_var,
                        command=self.update_energy_range, **cb_kwargs).grid(row=0, column=1, sticky='w')
        
        self.normalize_var = tk.BooleanVar(value=dpp.normalize)
        ttk.Checkbutton(self.display_frame, text='Normalize plots', variable=self.normalize_var,
                        command=self.update_normalize, **cb_kwargs).grid(row=1, column=0, sticky='w')
                        
        self.display_spin_var = tk.BooleanVar(value=dpp.display_spin)
        ttk.Checkbutton(self.display_frame, text='Display spin projections', variable=self.display_spin_var, **cb_kwargs).grid(row=2, column=0, sticky='w')
        
        self.smooth_var = tk.BooleanVar(value=dpp.smooth)
        ttk.Checkbutton(self.display_frame, text='Smooth DoS', variable=self.smooth_var, **cb_kwargs).grid(row=3, column=0, sticky='w')
        
        self.n_smooth_var = tk.IntVar(value=dpp.n_smooth)
        group_frame = ttk.Frame(self.display_frame)
        ttk.Label(group_frame, text='Moving average order').grid(row=0, column=0, sticky='nsew')
        tk.Spinbox(group_frame, textvariable=self.n_smooth_var, width=3, from_=2, to=dpp.nedos/2).grid(row=0, column=1, sticky='nsew')
        group_frame.grid(row=3, column=1, sticky='w')    

        # ---------------------------------------------- DISPLAY PARAMS ------------------------------------------------
        
        self.display_param = tu.DisplayParametersFrame(self.contain_frame, 'E', 'DoS', self.dpp)
        self.display_param.frame.grid(row=4, column=0, pady=3, sticky='nsew')

        # --------------------------------------------------- BUTTONS --------------------------------------------------

        buttons_frame = ttk.Frame(self.main_frame)
        buttons_frame.grid(row=1, column=0, pady=3, sticky='nsew')

        ttk.Button(buttons_frame, text='Apply', command=self.save).grid(row=0, column=0, padx=5)
        ttk.Button(buttons_frame, text='OK', command=lambda: self.save(close=True)).grid(row=0, column=1, padx=5)
        ttk.Button(buttons_frame, text='Cancel', command=self.destroy).grid(row=0, column=2, padx=5)
        

    def enable_proj_dos(self):
        """ Enable the projected dos frame is the checkbutton is checked and disable it if it is not """
        if self.projdos_var.get():
            tu.enable_frame(self.projdos_frame)
        elif not self.projdos_var.get():
            tu.disable_frame(self.projdos_frame)

    def open_atoms_choice_window(self):

        if self.dostype_var.get() == 'OPAS':
            items = self.cell.atoms_types
            items_on = self.opas_items_choice
            label_on = 'Atomic species plotted'
            label_off = 'Atomic species not plotted'
            output = 'opas_items_choice'
        else:
            items = self.cell.atoms
            items_on = self.opa_items_choice
            label_on = 'Atoms plotted'
            label_off = 'Atoms not plotted'
            output = 'opa_items_choice'

        tu.ItemsChoiceWindow(self, items, items_on, output, label_on, label_off)


    def open_colour_choice_window(self):

        if self.dostype_var.get() == 'OPAS':
            items_temp = self.opas_items_choice
        else:
            items_temp = self.opa_items_choice

        if self.totprojdos_var.get() is False:
            items = list(np.concatenate([[f + ' %s' % g for g in self.cell.orbitals] for f in items_temp]))
            colors = self.proj_colors_choice
            output = 'proj_colors_choice'
        else:
            items = items_temp
            colors = self.tot_colors_choice
            output = 'tot_colors_choice'

        self.wait_window(tu.ColoursChoiceWindow(self, items, colors, output))


    def update_energy_range(self):
        if self.fermishift_var.get() is True:
            self.display_param.xlim_frame.low_var.set(np.round((self.display_param.xlim_frame.low_var.get() - self.cell.fermi_energy), 3))
            self.display_param.xlim_frame.high_var.set(np.round((self.display_param.xlim_frame.high_var.get() - self.cell.fermi_energy), 3))
            self.display_param.xlabel_var.set('$E - E_F (eV)$')
        else:
            self.display_param.xlim_frame.low_var.set(np.round((self.display_param.xlim_frame.low_var.get() + self.cell.fermi_energy), 3))
            self.display_param.xlim_frame.high_var.set(np.round((self.display_param.xlim_frame.high_var.get() + self.cell.fermi_energy), 3))
            self.display_param.xlabel_var.set('E(eV)')
    
    
    def update_normalize(self):
        if self.normalize_var.get() is True:
            self.display_param.ylim_frame.low_var.set(0)
            self.display_param.ylim_frame.high_var.set(1)
        else:
            self.display_param.ylim_frame.low_var.set(self.dpp.energy_range[0])
            self.display_param.ylim_frame.high_var.set(self.dpp.energy_range[1])
    
    
    def dpp_select(self, event=None):
        try:
            self.dpp = self.project.pp['dpp'][self.dppname.get()]
            self.mainwindow.projects[self.mainwindow.currentprojectid].cells[self.mainwindow.currentitemid].lastdpp = self.dpp
            self.update_window()
        except KeyError:
            print 'Please select existing parameters in the list or create new ones with the button'
    
    
    def dpp_create(self, event=None):
        newdpp = copy.deepcopy(self.dpp)
        newdpp.name = self.dppname.get()
        self.project.pp['dpp'][self.dppname.get()] = newdpp
        self.dpp = newdpp 
        self.mainwindow.projects[self.mainwindow.currentprojectid].cells[self.mainwindow.currentitemid].lastdpp = newdpp
        namelist = [dpp.name for dpp in self.project.pp['dpp'].values()]
        self.dppname.configure(values=namelist)
        print 'Created new DoS Plot Parameters ' + self.dpp.name + ' in Project ' + self.mainwindow.projects[self.mainwindow.currentprojectid].name


    def save(self, close=False):

        self.dpp.display_spin = self.spin_var.get()
        self.dpp.display_total_dos = self.totdos_var.get()
        self.dpp.display_proj_dos = self.projdos_var.get()
        self.dpp.dos_type = self.dostype_var.get()
        self.dpp.tot_proj_dos = self.totprojdos_var.get()
        self.dpp.plot_areas = self.plotareas_var.get()
        self.dpp.choice_opa = self.opa_items_choice
        self.dpp.choice_opas = self.opas_items_choice
        self.dpp.colors_tot = self.tot_colors_choice
        self.dpp.colors_proj = self.proj_colors_choice
        self.dpp.display_Fermi_level = self.efdisplay_var.get()
        self.dpp.display_BM_levels = self.bedisplay_var.get()
        self.dpp.fermi_shift = self.fermishift_var.get()
        self.dpp.normalize = self.normalize_var.get()
        self.dpp.display_spin = self.display_spin_var.get()
        self.dpp.smooth = self.smooth_var.get()
        self.dpp.n_smooth = self.n_smooth_var.get()

        self.dpp.name = self.dppname.get()
        
        try:
            self.display_param.write_in_pp(self.dpp)
            # plot DoS 
            self.mainwindow.plot()
            self.attributes('-topmost', True)
            
            if close:
                self.destroy()
        except ValueError:
            print 'Warning! Please specify range values as float values'
        
    
    def update_window(self):
        # update entries after selection
        self.spin_var.set(self.dpp.display_spin)
        self.totdos_var.set(self.dpp.display_total_dos)
        self.projdos_var.set(self.dpp.display_proj_dos)
        self.dostype_var.set(self.dpp.dos_type)
        self.totprojdos_var.set(self.dpp.tot_proj_dos)
        self.plotareas_var.set(self.dpp.plot_areas)
        
        self.opa_items_choice = self.dpp.choice_opa
        self.opas_items_choice = self.dpp.choice_opas
        self.tot_colors_choice = self.dpp.colors_tot
        self.proj_colors_choice = self.dpp.colors_proj
        
        self.efdisplay_var.set(self.dpp.display_Fermi_level)
        self.bedisplay_var.set(self.dpp.display_BM_levels)
        self.fermishift_var.set(self.dpp.fermi_shift)
        
        self.display_param.update_frame(self.dpp)
        self.display_param.xlim_frame.low_var.set(self.dpp.xmin)
        self.display_param.xlim_frame.high_var.set(self.dpp.xmax)
        self.display_param.ylim_frame.low_var.set(self.dpp.ymin)
        self.display_param.ylim_frame.high_var.set(self.dpp.ymax)


class BandPlotParametersWindow(tk.Toplevel):

    def __init__(self, mainwindow, cell, bpp):

        tk.Toplevel.__init__(self, mainwindow)

        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(expand=True, fill='both')
        self.mainwindow = mainwindow
        self.project = self.mainwindow.projects[self.mainwindow.currentprojectid]
        self.bpp = bpp
        self.cell = cell
        
        self.title(self.cell.treetitle + ' Band Plot Parameters Edition Window')
        
        # --------------------------------------------------- BPP name -------------------------------------------------
        
        self.label0 = tk.Label(self.main_frame, text='Plot Parameters Name', pady=10)
        
        self.nameframe = tk.Frame(self.main_frame)
        self.nameframe.grid(row=1, column=0)
        namelist = [bpp.name for bpp in self.project.pp['bpp'].values()]
        self.bppname = ttk.Combobox(self.nameframe, values=namelist, width=40) 
        self.bppname.set(self.bpp.name)
        self.bppname.bind("<<ComboboxSelected>>", self.bpp_select)
        self.label0.grid(row=0, column=0)
        self.bppname.grid(row=1, column=0)
        tk.Button(self.nameframe, text='Save as new parameters', command=self.bpp_create).grid(row=1, column=1)

        # -------------------------------------------------- VARIABLES -------------------------------------------------
        
        self.label1 = tk.Label(self.main_frame, text='Band plot parameters', font='-weight bold')
        self.band_frame = ttk.LabelFrame(self.main_frame, labelwidget=self.label1)
        self.band_frame.grid(row=2, column=0, pady=3, sticky='nsew')

        self.vbm_shift_var = tk.BooleanVar(value=bpp.vbm_shift)
        self.highlight_vbm_cbm_var = tk.BooleanVar(value=bpp.highlight_vbm_cbm)
        self.hs_kpoints_var = tk.StringVar(value=','.join(bpp.hs_kpoints_names))
        self.discontinuities_var = tk.BooleanVar(value=bpp.discontinuities)
        self.nkpts_per_seg_var = tk.IntVar(value=bpp.nkpts_per_seg)
        # self.disc_hshift_var = tk.DoubleVar(value=bpp.disc_hshift)
        self.highlight_zero_line_var = tk.BooleanVar(value=bpp.highlight_zero_line)
        self.nkpts_hybrid_bands_var = tk.IntVar(value=bpp.nkpts_hybrid_bands)

        # VBM as zero of energy
        ttk.Checkbutton(self.band_frame, text='VBM as zero of energy', variable=self.vbm_shift_var,
                        onvalue=True, offvalue=False, command=self.update_energy_range).grid(pady=3, sticky='nsew') 

        # VBM & CBM highlight
        ttk.Checkbutton(self.band_frame, text='Highlight VBM & CBM', variable=self.highlight_vbm_cbm_var,
                        onvalue=True, offvalue=False).grid(pady=3, sticky='nsew')
                        
        # Highlight zero line
        ttk.Checkbutton(self.band_frame, text='Highlight zero-line', variable=self.highlight_zero_line_var,
                        onvalue=True, offvalue=False).grid(pady=3, sticky='nsew')

        # High Symmetry K-points
        hs_kpoints_frame = ttk.Frame(self.band_frame)
        hs_kpoints_frame.grid(pady=3, sticky='nsew')
        ttk.Label(hs_kpoints_frame, text='High symmetry K-points (comma-separated)').pack(side='left')
        ttk.Entry(hs_kpoints_frame, textvariable=self.hs_kpoints_var, width=20).pack(side='left')
        
        # Discontinuities
        ttk.Checkbutton(self.band_frame, text='Discontinuities in the K-pts path', variable=self.discontinuities_var,
                        onvalue=True, offvalue=False).grid(pady=3, sticky='nsew')
        
        nkpts_per_seg_frame = ttk.Frame(self.band_frame)
        nkpts_per_seg_frame.grid(pady=3, sticky='nsew')
        ttk.Label(nkpts_per_seg_frame, text='Number of K-pts per segment').pack(side='left')
        ttk.Entry(nkpts_per_seg_frame, textvariable=self.nkpts_per_seg_var, width=3).pack(side='left')
        
        nkpts_hybrid_bands_frame = ttk.Frame(self.band_frame)
        nkpts_hybrid_bands_frame.grid(pady=3, sticky='nsew')
        if self.cell.functional in ['PBE0', 'HSE', 'Hybrid']:
            ttk.Label(nkpts_hybrid_bands_frame, text='Number of K-pts used for \nBand Structure Calculation (Hybrid functionals only)').pack(side='left')
            ttk.Entry(nkpts_hybrid_bands_frame, textvariable=self.nkpts_hybrid_bands_var, width=3).pack(side='left')
        
        # ---------------------------------------------- DISPLAY PARAMS ------------------------------------------------
        
        self.display_param = tu.DisplayParametersFrame(self.main_frame, 'High-symmetry K-points', 'Energy', self.bpp)
        self.display_param.frame.grid(row=3, column=0, pady=3, sticky='nsew')

        # --------------------------------------------------- BUTTONS --------------------------------------------------

        buttons_frame = ttk.Frame(self.main_frame)
        buttons_frame.grid(pady=3, sticky='nsew')

        ttk.Button(buttons_frame, text='Apply', command=self.save).grid(row=0, column=0, padx=5)
        ttk.Button(buttons_frame, text='OK', command=lambda: self.save(close=True)).grid(row=0, column=1, padx=5)
        ttk.Button(buttons_frame, text='Cancel', command=self.destroy).grid(row=0, column=2, padx=5)

    def update_energy_range(self):
        if self.vbm_shift_var.get():
            self.bpp.vbm_shift = True
            self.bpp.ymin -= self.cell.vbm_energy
            self.bpp.ymax -= self.cell.vbm_energy
            self.bpp.y_label = '$E - E_F$ (eV)'
        else:
            self.bpp.vbm_shift = False
            self.bpp.ymin += self.cell.vbm_energy
            self.bpp.ymax += self.cell.vbm_energy
            self.bpp.y_label = 'E (eV)'
        self.update_window()
            
    def bpp_select(self, event=None):
        try:
            self.bpp = self.project.pp['bpp'][self.bppname.get()]
            self.mainwindow.projects[self.mainwindow.currentprojectid].cells[self.mainwindow.currentitemid].lastbpp = self.bpp
            self.update_window()
        except KeyError:
            print 'Please select existing parameters in the list or create new ones with the button'
    
    def bpp_create(self, event=None):
        newbpp = copy.deepcopy(self.bpp)
        newbpp.name = self.bppname.get()
        self.project.pp['bpp'][self.bppname.get()] = newbpp
        self.bpp = newbpp 
        self.mainwindow.projects[self.mainwindow.currentprojectid].cells[self.mainwindow.currentitemid].lastbpp = newbpp
        namelist = [bpp.name for bpp in self.project.pp['bpp'].values()]
        self.bppname.configure(values=namelist)
        print 'Created new Band Plot Parameters ' + self.bpp.name + ' in Project ' + self.mainwindow.projects[self.mainwindow.currentprojectid].name

    def save(self, close=False):

        self.bpp.vbm_shift = self.vbm_shift_var.get()
        self.bpp.highlight_vbm_cbm = self.highlight_vbm_cbm_var.get()
        self.bpp.hs_kpoints_names = [f.strip() for f in self.hs_kpoints_var.get().split(',')]
        self.bpp.name = self.bppname.get()
        self.bpp.discontinuities = self.discontinuities_var.get()
        self.bpp.nkpts_per_seg = self.nkpts_per_seg_var.get()
        self.bpp.highlight_zero_line = self.highlight_zero_line_var.get()
        self.bpp.nkpts_hybrid_bands = self.nkpts_hybrid_bands_var.get()
        
        # try:
        self.display_param.write_in_pp(self.bpp)
        
        # plot Band Diagram 
        self.mainwindow.plot_band_diagram()
        self.attributes('-topmost', True)
        
        if close:
            self.destroy()
        # except ValueError:
            # print 'Warning! Please specify range values as float values'
            
    
    def update_window(self):
        self.vbm_shift_var.set(self.bpp.vbm_shift)
        self.highlight_vbm_cbm_var.set(self.bpp.highlight_vbm_cbm)
        self.hs_kpoints_var.set(', '.join(self.bpp.hs_kpoints_names))
        self.display_param.update_frame(self.bpp)
        self.display_param.xlim_frame.low_var.set(self.bpp.xmin)
        self.display_param.xlim_frame.high_var.set(self.bpp.xmax)
        self.display_param.ylim_frame.low_var.set(self.bpp.ymin)
        self.display_param.ylim_frame.high_var.set(self.bpp.ymax)
        
class BandFitParametersWindow(tk.Toplevel):

    def __init__(self, mainwindow, cell):

        tk.Toplevel.__init__(self, mainwindow)

        self.main_frame = ttk.Frame(self)
        self.main_frame.grid(sticky='nsew')
        self.mainwindow = mainwindow
        self.project = self.mainwindow.projects[self.mainwindow.currentprojectid]
        self.bfp = cell.bfp
        self.cell = cell
        
        self.title(self.cell.treetitle + ' Band Fit Window')
        
        # -------------------------------------------------- VARIABLES -------------------------------------------------
        self.label1 = tk.Label(self.main_frame, text='Band fit parameters', font='-weight bold')
        self.band_frame = ttk.LabelFrame(self.main_frame, labelwidget=self.label1)
        self.band_frame.grid(row=2, column=0, pady=3, sticky='nsew')
        
        self.hs_kpoints_var = tk.StringVar(value=','.join(self.bfp.hs_kpoints_names))

        # High Symmetry K-points
        hs_kpoints_frame = ttk.Frame(self.band_frame)
        hs_kpoints_frame.grid(pady=3, sticky='nsew')
        ttk.Label(hs_kpoints_frame, text='High symmetry K-points (comma-separated)').grid(sticky='nsew')
        ttk.Entry(hs_kpoints_frame, textvariable=self.hs_kpoints_var, width=20).grid(sticky='nsew')

        # Energy range
        self.vbm_range = tu.RangeFrame(self.band_frame, self.bfp.bands_fit['VBM'].xfitmin, self.bfp.bands_fit['VBM'].xfitmax, 'VBM fit range', '', width=6)
        self.vbm_range.grid(sticky='nsew')
        self.cbm_range = tu.RangeFrame(self.band_frame, self.bfp.bands_fit['CBM'].xfitmin, self.bfp.bands_fit['CBM'].xfitmax, 'CBM fit range', '', width=6)
        self.cbm_range.grid(sticky='nsew')
        
        # ---------------------------------------------- DISPLAY PARAMS ------------------------------------------------
        
        self.display_param = tu.DisplayParametersFrame(self.main_frame, 'High-symmetry K-points', 'Energy', self.bfp)
        self.display_param.frame.grid(row=3, column=0, pady=3, sticky='nsew')

        # --------------------------------------------------- BUTTONS --------------------------------------------------

        buttons_frame = ttk.Frame(self.main_frame)
        buttons_frame.grid(pady=3, sticky='nsew')

        ttk.Button(buttons_frame, text='Apply', command=self.save).grid(row=0, column=0, padx=5)
        ttk.Button(buttons_frame, text='OK', command=lambda: self.save(close=True)).grid(row=0, column=1, padx=5)
        ttk.Button(buttons_frame, text='Cancel', command=self.destroy).grid(row=0, column=2, padx=5)
        
    def save(self, close=False):
        self.bfp.hs_kpoints_names = [f.strip() for f in self.hs_kpoints_var.get().split(',')]
        self.bfp.bands_fit['CBM'].xfitmin = self.vbm_range.low_var.get()
        self.bfp.bands_fit['CBM'].xfitmax = self.vbm_range.high_var.get()
        self.bfp.bands_fit['VBM'].xfitmin = self.cbm_range.low_var.get()
        self.bfp.bands_fit['VBM'].xfitmax = self.cbm_range.high_var.get()
        try:
            self.display_param.write_in_pp(self.bfp)
            self.mainwindow.fit_bands()
            self.attributes('-topmost', True)
            if close:
                self.destroy()
        except ValueError:
            print 'Warning! Please specify range values as float values'


class GeomComparisonParametersWindow(tk.Toplevel):
    
    def __init__(self, mainwindow):
        tk.Toplevel.__init__(self, mainwindow)
        self.resizable(False, False)

        self.main_frame = tk.Frame(self)
        self.main_frame.grid(sticky='nsew')
        self.r_corr_cut_var = tk.DoubleVar()
        self.r_coord_sphere_var = tk.DoubleVar()
        self.signif_var_min_var = tk.DoubleVar()
        self.r_corr_cut_var.set(2.0)
        self.r_coord_sphere_var.set(7.0)
        self.signif_var_min_var.set(3.5)
        tk.Label(self.main_frame, text='Radius of sphere used to\ndetermine corresponding\natom in defect cell').grid(row=0, column=0)
        tk.Label(self.main_frame, text='Radius of sphere centered\non the defect selecting\nthe atoms to study').grid(row=1, column=0)
        tk.Label(self.main_frame, text='Minimum relative\ninteratomic distance variation\nto filter on').grid(row=2, column=0)
        tk.Entry(self.main_frame, textvariable=self.r_corr_cut_var, width=3).grid(row=0, column=1)
        tk.Entry(self.main_frame, textvariable=self.r_coord_sphere_var, width=3).grid(row=1, column=1)
        tk.Entry(self.main_frame, textvariable=self.signif_var_min_var, width=3).grid(row=2, column=1)
        tk.Label(self.main_frame, text=' A').grid(row=0, column=2)
        tk.Label(self.main_frame, text=' A').grid(row=1, column=2)
        tk.Label(self.main_frame, text=' %').grid(row=2, column=2)
        tk.Button(self.main_frame, text='OK', command=self.validate).grid(sticky='e')
        self.r_corr_cut = self.r_corr_cut_var.get()
        self.r_coord_sphere = self.r_coord_sphere_var.get()
        self.signif_var_min = self.signif_var_min_var.get()
        
    def validate(self):
        self.r_corr_cut = self.r_corr_cut_var.get()
        self.r_coord_sphere = self.r_coord_sphere_var.get()
        self.signif_var_min = self.signif_var_min_var.get()
        self.destroy()
        

class GeomComparisonResultsWindow(tk.Toplevel):
    
    def __init__(self, mainwindow, gc):
        tk.Toplevel.__init__(self, mainwindow)
        
        self.title('Geometry comparison')
        self.resizable(False, False)
        self.maxsize(width=self.winfo_screenwidth(), height=3*self.winfo_screenheight()/5)
        self.mainwindow = mainwindow

        self.main_frame = tk.Frame(self)
        self.main_frame.grid(sticky='nsew')
        
        notebook = ttk.Notebook(master=self.main_frame)
        notebook.add(tu.ScrollableTableFrame(self.main_frame, gc.d_var_header, gc.atom_displacements).main_frame, text = 'Atom Displacements')
        notebook.add(tu.ScrollableTableFrame(self.main_frame, gc.inter_a_var_header, gc.interatomic_distances_variations).main_frame, text = 'Interatomic Distances Variations')
        notebook.grid(sticky='nsew')
        
        print str(len(gc.interatomic_distances_variations))
        
        tk.Button(self.main_frame, text='OK', command=self.cancel).grid()
    
    def cancel(self):
        self.mainwindow.focus_set()
        self.destroy()


class OpticalIndicesPlotParametersWindow(tk.Toplevel):

    def __init__(self, mainwindow, project, opp):
        
        tk.Toplevel.__init__(self, mainwindow) 
        
        self.mainwindow = mainwindow
        self.project = project
        self.cell = self.project.cells[self.mainwindow.currentitemid].optical_indices
        self.opp = opp
        
        self.resizable(False, False)
        self.maxsize(width=self.winfo_screenwidth(), height=4*self.winfo_screenheight()/5)
        
        self.main_frame = ttk.Frame(self)
        self.main_frame.grid(sticky='nsew')
        self.contain_frame = tu.ScrollableTableFrame(self.main_frame, '', []).interior
        
        self.title('Optical indices Plot Parameters Edition Window')
        
        # --------------------------------------------------- OPP name -------------------------------------------------
        
        self.label0 = tk.Label(self.contain_frame, text='Plot Parameters Name', pady=10)
        
        self.nameframe = tk.Frame(self.contain_frame)
        self.nameframe.grid(row=1, column=0)
        namelist = [opp.name for opp in self.project.pp['opp'].values()]
        self.oppname = ttk.Combobox(self.nameframe, values=namelist, width=40) 
        self.oppname.set(self.opp.name)
        self.oppname.bind("<<ComboboxSelected>>", self.opp_select)
        self.label0.grid(row=0, column=0)
        self.oppname.grid(row=1, column=0)
        tk.Button(self.nameframe, text='Save as new parameters', command=self.opp_create).grid(row=1, column=1)

        # Data ID
        oplabel = tk.Label(self.contain_frame, text='Optical properties to plot', font=('', '16', 'bold'))
        self.op_frame = ttk.LabelFrame(self.contain_frame, labelwidget=oplabel)
        data_frame = ttk.Frame(self.op_frame)
        data_frame.grid(row=3, column=0, pady=3, sticky='nsew')

        self.data_id_var = tk.StringVar()
        ttk.Label(data_frame, text='Optical property: ').pack(side='left')
        cb  = ttk.Combobox(data_frame, textvariable=self.data_id_var, values=self.cell.quantities, width=10,
                          state='readonly')
        cb.pack(side='left')
        cb.bind("<<ComboboxSelected>>", self.quantity_list_update)
        cb.current(0)
        
        self.op_frame.grid(row=4, column=0, pady=3, sticky='nsew')
        
        self.quantities_pane = ttk.Frame(self.contain_frame)
        self.quantities_rows = {}
        
        self.quantities_pane.grid(row=5, column=0, pady=3, sticky='nsew')
        
        # -------------------------------------------- SPECIFIC PARAMS ------------------------------------------------
        
        self.label0 = tk.Label(self.main_frame, text='Optical Indices Plot Specific Parameters', font='-weight bold')
        self.opp_param_frame = ttk.LabelFrame(self.contain_frame, labelwidget=self.label0)
        self.opp_param_frame.grid(row=6, column=0, padx=3, pady=3, sticky='nsew')
        
        self.trace_only_var = tk.BooleanVar(value=opp.trace_only)
        ttk.Checkbutton(self.opp_param_frame, text='Trace only', variable=self.trace_only_var).grid(row=0, padx=3, pady=3, sticky='nsew')
        
        self.h_shift_var = tk.DoubleVar(value=opp.h_shift)
        ttk.Label(self.opp_param_frame, text='Scissor operator (horizontal shift) ').grid(row=1, column=0)
        # tk.Spinbox(self.opp_param_frame, textvariable=self.title_fontsize_var, width=3, from_=0, to=100).grid(row=0, column=1)
        ttk.Entry(self.opp_param_frame, textvariable=self.h_shift_var, width=3).grid(row=1, column=1, sticky='we')
                
        # ---------------------------------------------- DISPLAY PARAMS ------------------------------------------------
        
        self.display_param = tu.DisplayParametersFrame(self.contain_frame, 'Energy', 'Optical indices', self.opp)
        self.display_param.frame.grid(row=7, column=0, pady=3, sticky='nsew')
        
        # Color
        self.label2 = tk.Label(self.contain_frame, text='Colors', font='-weight bold')
        self.colors_pane = ttk.LabelFrame(self.contain_frame, labelwidget=self.label2)
        self.color_rows = {}
        self.colors_pane.grid(row=8, column=0, pady=3, sticky='nsew')
            
        self.update_window()
        
        # --------------------------------------------------- BUTTONS --------------------------------------------------
        
        buttons_frame = ttk.Frame(self.main_frame)
        buttons_frame.grid()

        ttk.Button(buttons_frame, text='Apply', command=lambda: self.save(False)).grid(row=0, column=0, padx=5)
        ttk.Button(buttons_frame, text='OK', command=lambda: self.save(True)).grid(row=0, column=1, padx=5)
        ttk.Button(buttons_frame, text='Cancel', command=self.destroy).grid(row=0, column=2, padx=5)
    
    def update_window(self):
        rows = self.quantities_rows.keys()
        for quant in rows:
            self.quantities_rows[quant][0].grid_forget()
            self.quantities_rows[quant][1].grid_forget()
            self.quantities_rows.pop(quant)
            for component in self.color_rows[quant]:
                self.color_rows[quant][component].grid_forget()
            self.color_rows.pop(quant) 
        for quant in self.opp.data_id:
            self.add_quantity(quant)
        self.display_param.update_frame(self.opp)
    
    def set_color(self, arg):
        quantity, component = arg
        self.opp.colors[quantity][component] = askcolor(parent=self)[1]
        self.color_rows[quantity][component].configure(bg=self.opp.colors[quantity][component])
    
    def add_quantity(self, quantity, nrow=None):
        self.quantities_rows[quantity] = [tk.Label(self.quantities_pane, text= '\t\t' + quantity), 
        tk.Button(self.quantities_pane, text='x', command= lambda: self.remove_quantity(quantity))]
        if nrow is None:
            nqrows = len(self.quantities_rows) + 1
        else:
            nqrows = nrow
        self.quantities_rows[quantity][0].grid(row=nqrows, column=0)
        self.quantities_rows[quantity][1].grid(row=nqrows, column=1)
        
        self.color_rows[quantity] = {}
        sort_components = self.opp.colors[quantity].keys()
        sort_components.sort()
        
        col = 0
        
        for component in sort_components:
            col += 1
            button = tk.Button(self.colors_pane, width=4, text=poi.shorten_quantity(quantity) + component, bg=self.opp.colors[quantity][component], command=lambda port = (quantity, component): self.set_color(port))
            self.color_rows[quantity].update({component: button})
            button.grid(row=nqrows, column=col)
        
    def remove_quantity(self, quantity):
        if len(self.quantities_rows.keys()) >= 2:
            for q in self.quantities_rows.keys():
                self.quantities_rows[q][0].grid_forget()
                self.quantities_rows[q][1].grid_forget()
            self.quantities_rows.pop(quantity)
            for q in self.color_rows.keys():
                for component in self.color_rows[q].keys():
                    self.color_rows[q][component].grid_forget()
            self.color_rows.pop(quantity)
            # update rows so that row numbers are correct
            index = 0
            for q in self.quantities_rows.keys():
                self.add_quantity(q, nrow=index)
                index += 1
        else:
            print 'Warning! Leave at least one optical property to plot please!'
            
    
    def quantity_list_update(self, event=None):
        qchoice = self.data_id_var.get()
        
        if qchoice not in self.quantities_rows.keys():
            self.opp.data_id.append(qchoice)
            self.add_quantity(qchoice, nrow=len(self.opp.data_id))
            
    
    def setcolor(self):
        self.opp.colors[self.data_id_var.get()] = askcolor(parent=self)[1]
        self.color.configure(bg=self.opp.colors[self.data_id_var.get()])
        

    def opp_select(self, event=None):
        try:
            self.opp = self.project.pp['opp'][self.oppname.get()]
            self.mainwindow.projects[self.mainwindow.currentprojectid].cells[self.mainwindow.currentitemid].lastopp = self.opp
            self.update_window()
            print 'OPP selected: ' + self.opp.name
            print "%f, %f" %(self.opp.xmin, self.opp.xmax)
        except KeyError:
            print 'Please select existing parameters in the list or create new ones with the button'
            
    
    def opp_create(self, event=None):
        newopp = copy.deepcopy(self.opp)
        newopp.name = self.oppname.get()
        self.project.pp['opp'][self.oppname.get()] = newopp
        self.opp = newopp 
        self.mainwindow.projects[self.mainwindow.currentprojectid].cells[self.mainwindow.currentitemid].lastopp = newopp
        namelist = [opp.name for opp in self.project.pp['opp'].values()]
        self.oppname.configure(values=namelist)
        print 'Created new Optical Plot Parameters ' + self.opp.name + ' in Project ' + self.mainwindow.projects[self.mainwindow.currentprojectid].name
            

    def save(self, close):
        self.opp.name = self.oppname.get()
        tensorlist = self.quantities_rows.keys()
        tensorlist.sort()
        self.opp.data_id = tensorlist
        self.opp.trace_only = self.trace_only_var.get()
        self.opp.h_shift = self.h_shift_var.get()
        try: 
            self.display_param.write_in_pp(self.opp)
            
            self.mainwindow.plot_optical_indices(opp=self.opp)
            self.attributes('-topmost', True)
            
            if close:
                self.destroy()
        except ValueError:
            print 'Warning! Please specify range values as float values'
