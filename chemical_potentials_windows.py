"""
    Project Manager in PyDEF GUI
    version: 2.0
    author: Adrien Stoliaroff
    email: adrien.stoliaroff@cnrs-imn.fr
"""

import Tkinter as tk
from Tkinter import Tk, Frame, Menu, Button, Label
from Tkinter import LEFT, RIGHT, TOP, BOTTOM, X, FLAT, RAISED, BOTH, END, SUNKEN, ALL

import ttk
from tkColorChooser import askcolor              
import tkinter_utilities as tu

import pydef_core.defect_study as ds
import pydef_core.basic_functions as bf
import pydef_core.chemical_potentials as pcp


class ChemicalPotentialsCreationWindow(tk.Toplevel):
    
    def plot(self, close=False):
        self.mainwindow.plot()
        if close:
            self.cancel()
    
    def cancel(self):
        self.mainwindow.focus_set()
        self.destroy()

    def __init__(self, mainwindow, project, chemical_potentials_to_edit):
        
        tk.Toplevel.__init__(self, mainwindow)
        self.mainwindow = mainwindow
        self.project = project
        host = self.project.cells[self.project.hostcellid]
        self.title('Stability domain of ' + host.rname)
        self.width=self.winfo_width()
        self.height=self.winfo_height()
        self.chemical_potentials = chemical_potentials_to_edit

        if self.chemical_potentials is None:
            self.edit = False
        else:
           self.edit = True 

        if project.hostcellid == '':
            self.mainwindow.printerror('Current project has no host cell! Please declare the perfect cell as host before creating Chemical Potentials.')
        
        # -------------------  GRAPHICAL OBJECTS  ----------------------
        
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(expand=True, fill='both')
        
        all_phases = self.project.unboundcells.values()
        items = [cell.treetitle for cell in all_phases if not self.project.is_host(cell)]
        
        if self.chemical_potentials is not None:    
            items_on = [cell.treetitle for cell in self.chemical_potentials.non_synthesized.values()]
        else:
            items_on = []
            
        label_on = 'Phases competing with ' + host.rname
        label_off = self.project.name + ' Calculations'
        labeltitle = tk.Label(self.main_frame, text='Phases choice')
        
        self.phase_choice_frame = tu.ItemsChoiceFrame(self.main_frame, items, items_on, label_on, label_off, labeltitle)
        
        # ------------------  NAVIGATION BUTTONS  ----------------------
        
        def validate(close=False):
            def has_energy(cell):
                    if cell.total_energy is None:
                        print 'Ignoring ' + cell.treetitle + ' which is not an energy calculation'
                        return False
                    else:
                        return cell.total_energy != 0
            choice = self.phase_choice_frame.get_choice()
            unboundcells = self.project.unboundcells.values()
            self.attributes('-topmost', True)
            if not self.edit:
                print 'Calculating ' + host.rname + ' Stability Domain...'
                # Create core object
                self.chemical_potentials = pcp.ChemicalPotentials(host)
                phase_list_to_add = [cell for treetitle in choice for cell in unboundcells if cell.treetitle == treetitle and cell.ID != self.project.hostcellid and has_energy(cell)]
                for phase in phase_list_to_add:
                    self.chemical_potentials.add_non_synthesized(phase)
                    
                # Add to project
                self.chemical_potentials.ID = self.project.pid + '/chem-pot'
                self.project.chemical_potentials = self.chemical_potentials
                
                # Add to tree
                self.mainwindow.pm.new_chemical_potentials(self.project.pid)
                self.edit = True
            else:
                ns = self.chemical_potentials.non_synthesized.values()
                phase_list_to_add = [cell for treetitle in choice for cell in unboundcells if cell.treetitle == treetitle and cell not in ns]
                print 'phase_list_to_add ' + str(phase_list_to_add)
                if len(choice) == 0:
                    phase_list_to_remove = [cell for cell in ns]
                else:
                    phase_list_to_remove = [cell for cell in ns if cell.treetitle not in choice]
                # Edit core object
                for cell in phase_list_to_add:
                    print 'Adding phase ' + cell.rname + '(' + cell.treetitle + ') to ' + host.rname + ' Stability Domain'
                    self.mainwindow.pm.add_phase_in_chemical_potentials(cell, self.project.pid)
                for cell in phase_list_to_remove:
                    self.mainwindow.pm.remove_phase_from_chemical_potentials(cell, self.project.pid)
            if len(self.chemical_potentials.non_synthesized)>0:
                try:
                    self.plot(close=close)
                except ValueError, e:
                    self.mainwindow.printerror(e)
                except ZeroDivisionError, e:
                    self.mainwindow.printerror(str(e))
            else:
                print 'Warning! Impossible to plot Defect Formation Energies for empty Chemical Potentials' 
                if close :
                    self.cancel()
            
        self.button_pane = tk.Frame(self.main_frame, bd = 2, pady = 10)
        self.apply_button = Button(self.button_pane, text = 'Apply', command=validate)
        self.next_button = Button(self.button_pane, text = 'OK', command=lambda: validate(close=True))
        self.cancel_button = Button(self.button_pane, text = 'Cancel', command=self.cancel)
        self.apply_button.grid(row = 0, column = 0)
        self.next_button.grid(row = 0, column = 1)
        self.cancel_button.grid(row = 0, column = 2)

        self.phase_choice_frame.pack(expand=True, fill='y')
        self.button_pane.pack(side=BOTTOM, expand=True, fill='y')
            
        tu.centre_window(self)
        
        
class PotentialsPlotParametersWindow(tk.Toplevel):
    
    
    def __init__(self, mainwindow, project, chemical_potentials):
        
        tk.Toplevel.__init__(self, mainwindow)
        self.mainwindow = mainwindow
        self.project = project
        host = self.project.cells[self.project.hostcellid]
        self.title(host.rname + ' Domain Stability Plot Parameters')
        self.width=self.winfo_width()
        self.height=self.winfo_height()
        self.chemical_potentials = chemical_potentials
        self.ppp = self.chemical_potentials.lastppp
        
        # -------------------  GRAPHICAL OBJECTS  ----------------------
        
        self.main_frame = tk.Frame(self)
        self.main_frame.grid(row=0, sticky='nsew')
        
        # name of PPP
        label0 = tk.Label(self.main_frame, text='Axes', font=('', '16', 'bold'))
        self.frame = ttk.LabelFrame(self.main_frame, labelwidget=label0)
        self.label1 = tk.Label(self.frame, text='Plot Parameters Name', pady=10)
        namelist = [ppp.name for ppp in self.project.pp['ppp'].values()]
        self.pppname = ttk.Combobox(self.frame, values=namelist, width=40, validate='focusout', validatecommand=self.ppp_select_create)
        self.pppname.set(self.ppp.name)
        
        self.label1.grid(row=0, column=0)
        self.pppname.grid(row=0, column=1)
        
        # X Y constrained
        binary_compound = len(self.chemical_potentials.synthesized.atoms_types) == 2
        ternary_compound = len(self.chemical_potentials.synthesized.atoms_types) == 3
        self.labelX = tk.Label(self.frame, text='X axis')
        self.labelY = tk.Label(self.frame, text='Y axis')
        self.labelC = tk.Label(self.frame, text='Constrained \nchemical potential')
        self.atom_types = self.chemical_potentials.synthesized.atoms_types
        
        self.xchoice = ttk.Combobox(self.frame, values=self.atom_types, state="readonly")
        self.ychoice = ttk.Combobox(self.frame, values=self.atom_types, state="readonly")
        self.cchoice = ttk.Combobox(self.frame, values=self.atom_types, state="readonly")
        
        select1 = self.ppp.mu_X_axis
        select2 = self.ppp.mu_Y_axis
        c_atom_list = [atom for atom in self.atom_types if atom != select1 and atom != select2]
        self.ychoice.configure(values=[atom for atom in self.atom_types if atom != select1])
        self.cchoice.configure(values=[atom for atom in self.atom_types if atom not in [select1, select2]])
        
        if binary_compound:
            self.labelX.grid(row=1, column=0)
            self.labelC.grid(row=1, column=1)
            self.xchoice.grid(row=2, column=0)
            self.cchoice = tk.Label(self.frame, text='')
            self.cchoice.grid(row=2, column=1)
            self.xchoice.bind("<<ComboboxSelected>>", lambda x: self.choice(0))
            self.xchoice.set(self.ppp.mu_Y_axis)
            self.cchoice.config(text=self.ppp.const)
        else:
            self.labelX.grid(row=1, column=0)
            self.labelY.grid(row=1, column=1)
            self.labelC.grid(row=1, column=2)
            self.xchoice.grid(row=2, column=0)
            self.ychoice.grid(row=2, column=1)
            self.cchoice.grid(row=2, column=2)
            self.xchoice.bind("<<ComboboxSelected>>", lambda x: self.choice(1))
            self.ychoice.bind("<<ComboboxSelected>>", lambda x: self.choice(2))
            self.xchoice.set(self.ppp.mu_X_axis)
            self.ychoice.set(self.ppp.mu_Y_axis)
            self.cchoice.set(self.ppp.const)
                
        self.frame.grid(row=2, sticky='nsew')
        
        # Range Frame
        def activate_range():
            if not self.autoscale.get():
                state = 'normal'
            else:
                state = 'disabled'
            for child in self.range_values_frame.winfo_children():
                child.configure(state=state)
        
        rangelabel = tk.Label(self.main_frame, text='Range', font=('', '16', 'bold'))
        self.range_frame = ttk.LabelFrame(self.main_frame, labelwidget=rangelabel)
        self.autoscale = tk.BooleanVar()
        self.autoscale.set(self.ppp.autoscale)
        
        ttk.Checkbutton(self.range_frame, text='autoscale', variable=self.autoscale, onvalue=True,
                        offvalue=False, style='Bold.TCheckbutton', command=activate_range).grid(row=0, column=0)
                        
        self.range_values_frame = tk.Frame(self.range_frame)
        self.xmin = tk.Entry(self.range_values_frame, validate='focusout', validatecommand=lambda: self.isFloat(self.xmin), width=5)
        self.ymin = tk.Entry(self.range_values_frame, validate='focusout', validatecommand=lambda: self.isFloat(self.ymin), width=5)
        self.xmax = tk.Entry(self.range_values_frame, validate='focusout', validatecommand=lambda: self.isMax(self.xmax), width=5)
        self.ymax = tk.Entry(self.range_values_frame, validate='focusout', validatecommand=lambda: self.isMax(self.ymax), width=5)
        self.xmin.grid(row=1, column=1)
        self.ymin.grid(row=2, column=1)
        self.xmax.grid(row=1, column=3)
        self.ymax.grid(row=2, column=3)
        tk.Label(self.range_values_frame, text='xmin').grid(row=1, column=0)
        tk.Label(self.range_values_frame, text='xmax').grid(row=1, column=2)
        if len(self.atom_types) > 1:
            tk.Label(self.range_values_frame, text='ymin').grid(row=2, column=0)
            tk.Label(self.range_values_frame, text='ymax').grid(row=2, column=2)
        activate_range()
        self.range_values_frame.grid(row=1, sticky = 'nsew')
        self.range_frame.grid(row=5, sticky = 'nsew')
                       
        # Display Parameters Frame
        displayparam = tk.Label(self.main_frame, text='Display parameters', font=('', '16', 'bold'))
        self.displayparam_frame = ttk.LabelFrame(self.main_frame, labelwidget=displayparam)
        self.titlepane = tk.Label(self.displayparam_frame)
        self.title = tk.Entry(self.titlepane, width=50)
        self.title.insert(0, self.ppp.title)
        tk.Label(self.titlepane, text='Title').grid(row=0, column=0, sticky='nsew')
        self.title.grid(row=0, column=1, sticky='nsew')
        self.titlepane.grid(row=0, sticky='nsew')
        # self.delta = tk.BooleanVar()
        # ttk.Checkbutton(self.displayparam_frame, text='Plot deviation from standard potential', variable=self.delta, onvalue=True,
        #                 offvalue=False, style='Bold.TCheckbutton').grid(row=1, sticky='w')
        
        self.grid = tk.BooleanVar()
        self.grid.set(self.ppp.grid)
        self.hashed = tk.BooleanVar()
        self.hashed.set(self.ppp.hashed)
        self.display_summits = tk.BooleanVar()
        self.display_summits.set(self.ppp.display_summits)
        
        self.bottom_disp_pane = tk.Frame(self.displayparam_frame)
        
        self.left_pane = tk.Frame(self.bottom_disp_pane)
        
        ttk.Checkbutton(self.left_pane, text='display grid', variable=self.grid, onvalue=True,
                        offvalue=False, style='Bold.TCheckbutton', command=activate_range).grid(row=0,column=0, sticky='w')
        ttk.Checkbutton(self.left_pane, text='hash stability domain', variable=self.hashed, onvalue=True,
                        offvalue=False, style='Bold.TCheckbutton', command=activate_range).grid(row=1,column=0, sticky='w')
        ttk.Checkbutton(self.left_pane, text='highlight domain summits', variable=self.display_summits, onvalue=True,
                        offvalue=False, style='Bold.TCheckbutton', command=activate_range).grid(row=2,column=0, sticky='w')
        
        self.left_pane.grid(row=1, column=0, sticky='nsew')
        
        def isInt(entry):
            if len(entry.get())>0:
                try:
                    
                    int(entry.get())
                    return True
                except ValueError, e:
                    self.mainwindow.printerror('Please insert an integer!')
                    entry.delete(0, END)
                    return False
            else:
                return True
        self.right_pane = tk.Frame(self.bottom_disp_pane)
                        
        tk.Label(self.right_pane, text='Title fontsize').grid(row=1,column=1, sticky='e')
        self.title_fontsize = tk.Entry(self.right_pane, validate='focusout', validatecommand=lambda: isInt(self.title_fontsize), width=4)
        self.title_fontsize.insert(0, self.ppp.title_fontsize)
        self.title_fontsize.grid(row=1,column=2, sticky='e')
        tk.Label(self.right_pane, text='Legend fontsize').grid(row=2,column=1, sticky='e')
        self.l_fontsize = tk.Entry(self.right_pane, validate='focusout', validatecommand=lambda: isInt(self.l_fontsize), width=4)
        self.l_fontsize.insert(0, self.ppp.l_fontsize)
        self.l_fontsize.grid(row=2,column=2, sticky='e')
        tk.Label(self.right_pane, text='Axes label fontsize').grid(row=3,column=1, sticky='e')
        self.fontsize = tk.Entry(self.right_pane, validate='focusout', validatecommand=lambda: isInt(self.fontsize), width=4)
        self.fontsize.grid(row=3,column=2, sticky='e')
        self.fontsize.insert(0, self.ppp.fontsize)
        
        self.right_pane.grid(row=1, column=1, sticky='nsew')
        
        self.color_englobing_pane = tk.Frame(self.bottom_disp_pane)
        
        tk.Label(self.color_englobing_pane, text='--- Colors ---').grid(row=1, column=0)
        
        self.colorpane = tk.Frame(self.color_englobing_pane)
        self.show_col = False
        def show_colors():
            self.show_col = not(self.show_col)
            if self.show_col:
                self.colorpane.grid(row=2, sticky='nsew')
                self.show_colors_button.configure(text='/\\')
            else:
                self.colorpane.grid_remove()
                self.show_colors_button.configure(text='\\/')
        self.show_colors_button = tk.Button(self.color_englobing_pane, text = '\\/', command = show_colors)
        self.show_colors_button.grid(row=1, column=1)
        
        competing_phases = [cell.ID for cell in self.chemical_potentials.non_synthesized.values() if cell.ID != self.chemical_potentials.synthesized.ID]
        competing_phases.sort()
        k = 0
        self.colortable = {}
        def setcolor(phase):
            self.ppp.colors[phase] = askcolor(parent=self)[1]
            self.colortable[phase].configure(bg=self.ppp.colors[phase])
        
        for phase_id in competing_phases:
            tk.Label(self.colorpane, text=self.chemical_potentials.non_synthesized[phase_id].rname).grid(row=2+k, column=0)
            self.colortable[phase_id] = tk.Button(self.colorpane, text='\t\t', bg=self.ppp.colors[phase_id], command=lambda port = phase_id: setcolor(port))
            self.colortable[phase_id].grid(row=2+k, column=1)
            k += 1
            
        self.color_englobing_pane.grid(row=1, column=2, sticky='nsew')
        
        self.bottom_disp_pane.grid(sticky='nsew')
        
        self.displayparam_frame.grid(row=6, sticky='nsew')
        
        # Equations 
        equations = tk.Label(self.main_frame, text='Equations', font=('', '16', 'bold'))
        self.equations_frame = ttk.LabelFrame(self.main_frame, labelwidget=equations)
        tk.Label(self.equations_frame, text=self.ppp.constrainEquation).grid(row=0, column=0)
        tk.Label(self.equations_frame, text='(Formation of ' + host.rname + ')').grid(row=0, column=1)
        k = 1
        for ineq in self.ppp.domainInequationsList:
            tk.Label(self.equations_frame, text=ineq.split(' (')[0].replace(' (','')).grid(row=k, column=0)
            tk.Label(self.equations_frame, text=' (' + ineq.split(' (')[1]).grid(row=k, column=1)
            k += 1
        
        self.equations_frame.grid(row=7, sticky='nsew')     
        
        # ------------------  NAVIGATION BUTTONS  ----------------------
        
        def validate(close=False):
            self.ppp.grid = self.grid.get()
            self.ppp.hashed = self.hashed.get()
            self.ppp.display_summits = self.display_summits.get()
            self.ppp.autoscale = self.autoscale.get()
            if not self.autoscale.get():
                self.ppp.xmin = float(self.xmin.get())
                self.ppp.ymin = float(self.ymin.get())
                self.ppp.xmax = float(self.xmax.get())
                self.ppp.ymax = float(self.ymax.get())
            self.ppp.fontsize = self.fontsize.get()
            self.ppp.title_fontsize = self.title_fontsize.get()
            self.ppp.l_fontsize = self.l_fontsize.get()
            self.ppp.title = str(self.title.get())
            # selfppp.delta = self.delta.get()
            
            if self.chemical_potentials.synth_population == 2:
                self.ppp.mu_X_axis = ''
                self.ppp.mu_Y_axis = self.xchoice.get()
                self.ppp.const = self.cchoice["text"]
            else:
                self.ppp.mu_X_axis = self.xchoice.get()
                self.ppp.mu_Y_axis = self.ychoice.get()
                self.ppp.const = self.cchoice.get()
                if self.chemical_potentials.synth_population > 3:
                    for species in self.remain_atoms.keys():
                        self.ppp.chem_pot_dict[species] = float(self.remain_atoms[species].get())            
            # Plot
            self.chemical_potentials.lastppp = self.ppp
            self.mainwindow.plot()
            self.geometry("+0+0")
            self.attributes('-topmost', True)
            if close :
                self.cancel()
        
        self.button_pane = tk.Frame(self.main_frame, bd = 2, pady = 10)
        self.apply_button = Button(self.button_pane, text = 'Apply', command=validate)
        self.next_button = Button(self.button_pane, text = 'OK', command=lambda: validate(close=True))
        self.cancel_button = Button(self.button_pane, text = 'Cancel', command=self.cancel)
        self.apply_button.grid(row = 0, column = 0)
        self.next_button.grid(row = 0, column = 1)
        self.cancel_button.grid(row = 0, column = 2)
        
        # self.button_pane.pack(side=BOTTOM, expand=True, fill='y')
        self.button_pane.grid(row=8, sticky='w')
    
    def ppp_select_create(self):
        """check if the user wants a new ppp, if so create one and select it"""
        if self.pppname.get() not in [ppp.name for ppp in self.project.pp['ppp'].values()]:
            self.project.pp['ppp'][self.pppname.get()] = pcp.PotentialsPlotParameters(self.chemical_potentials)
            self.ppp = self.project.pp['ppp'][self.pppname.get()]
            self.ppp.title = self.title.get()
    
    def open_color_picker(self):
        self.colors = {}
        self.color_picker = tu.ColoursChoiceWindow(self, [cell.rname for cell in self.chemical_potentials.non_synthesized.values()], self.ppp.colors, self.colors)
        
    def isFloat(self, entry):
        arg = entry.get()
        length = len(arg)
        if length>0:
            try:
                float(arg)
                return True
            except ValueError:
                self.parent.mainwindow.printerror('Given Chemical Potential is not a float!')
                entry.delete(0, END)
                return False
        else:
            return True
    
    def isMax(self, entry):
        if entry == self.xmax:
            min_entry = self.xmin
        elif entry == self.ymax:
            min_entry = self.ymin
        self.isFloat(entry)
        arg = entry.get()
        if len(arg)>1:
            if float(arg) <= float(min_entry.get()):
                self.parent.mainwindow.printerror('Given Chemical Potential is not a float!')
                entry.delete(0, END)
                return False
            else:
                return True

        
    def plot(self, close=False):
        self.mainwindow.plot()
        if close:
            self.cancel()
            
    
    def cancel(self):
        self.mainwindow.focus_set()
        self.destroy()
        
    
    def choice(self, category):
        """ category = 0 (binary compound), 1 (X), 2 (Y), 0 constrain"""
        if category == 1 :
            select = self.xchoice.get()
            atomslist = [atom for atom in self.atom_types if atom != select]
            self.ychoice.configure(values=atomslist)
            self.cchoice.configure(values=atomslist)
        elif category == 2 :
            select2 = self.ychoice.get()
            select1 = self.xchoice.get()
            self.xchoice.configure(values=[atom for atom in self.atom_types if atom != select2])
            c_atom_list = [atom for atom in self.atom_types if atom != select1 and atom != select2]
            self.cchoice.configure(values=c_atom_list)
            if len(c_atom_list) == 1:
                self.cchoice.set(c_atom_list[0])
        elif category == 3 :
            select = [self.xchoice.get(), self.ychoice.get(), self.cchoice.get()]
            remain_atoms_list = [atom for atom in self.atom_types if atom not in select]
            self.remain_atoms = {}
            k = 0
            self.remain_atoms_frame = tk.Frame(self.main_frame)
            tk.Label(self.remain_atoms_frame, text='Atom').grid(row=1, column=0)
            tk.Label(self.remain_atoms_frame, text='Chemical potential (eV)').grid(row=1, column=0)
            for atom in remain_atoms_list:
                tk.Label(self.remain_atoms_frame, text=atom).grid(row=1, column=1+k)
                self.remain_atoms[atom] = tk.Entry(self.remain_atoms_frame)
                self.remain_atoms[atom].grid(row=2, column=1+k)
                self.remain_atoms[atom].insert(0, str(dc.FERE[atom]))
                k += 1
            self.remain_atoms_frame.grid(row=3, sticky='nsew')
        elif category == 0:
            select = self.xchoice.get()
            atom_singlet = [atom for atom in self.atom_types if atom != select]
            self.cchoice.configure(text=atom_singlet[0])
