import matplotlib.pyplot as plt

import tkinter as tk
from tkinter import Tk, Frame, Menu, Button, Label, Canvas, Scrollbar
from tkinter import LEFT, RIGHT, TOP, BOTTOM, X, FLAT, RAISED, BOTH, END, SUNKEN, ALL, VERTICAL, W
from PIL import Image, ImageTk

import tkinter.ttk

import tkinter_utilities as tu
import pydef_core.defect_study as ds


def fig_num_to_grid(n, nrow, ncol):
    """Figure number to grid position (indices starting at 0 for grid manager)"""
    return (n/ncol+1, n%ncol)


def grid_to_fig_num(i, j, nrow, ncol):
    if j >= ncol:
        raise ValueError('Column index must be strictly inferior to number of columns (' + str(ncol) + ')')
    return (i+1)*nrow + j
    
    
def object_types():
    temp = ['Cell', 'Chemical Potentials', 'Defect Study', 'Material Study']
    temp.sort()
    return temp
    
    
class MultipleSubplotFigure(object):
    
    def __init__(self, name, nrow, ncol):
        self.name = name
        self.nrow = nrow
        self.ncol = ncol
        self.grid = {} # (n, data storage object, method to plot as lambda function, plot parameters)
        # self.axes = {}
    
    def plot(self):
        self.figure = plt.figure()
        for n in list(self.grid.keys()):
            # try:
            # self.axes[n] = figure.add_subplot(self.nrow, self.ncol, n + 1)
            # self.grid[n]['plot_func'](self.axes[n])
            self.subplot(n)
            """except AttributeError:
                i, j = fig_num_to_grid(n, self.nrow, self.ncol) 
                message = 'Warning! ' + self.grid[n]['object'].treetitle + ' plot in position ' + str(i+1) 
                message += ' ' + str(j+1) + ' failed!'
                print message
            except ValueError:
                message = "Matplotlib library internal error."
                message += " This is usually due to a lack of space: "
                message += "try reducing the fonts or/and the number of subplots"
                raise ValueError(message)"""
        return self.figure
    
    def subplot(self, n):
        # ax = self.axes[n]
        ax = self.figure.add_subplot(self.nrow, self.ncol, n + 1)
        selected_ptype = self.grid[n]['selected_ptype']
        try:
            selected_pp = self.grid[n]['selected_pp']
        except KeyError:
            selected_pp = None  
        if selected_pp is None:
            if selected_ptype == 'Density of States':
                self.grid[n]['object'].plot_dos(ax=ax, dpp=self.grid[n]['object'].lastdpp, tight=False)
            elif selected_ptype == 'Band diagram':
                self.grid[n]['object'].plot_band_diagram(ax=ax, bpp=self.grid[n]['object'].lastbpp, tight=False)
            elif selected_ptype == 'Optical Indices':
                self.grid[n]['object'].plot(pp=self.grid[n]['object'].lastopp, ax=ax)
            elif selected_ptype == 'Defect Formation Energies':
                if type(self.grid[n]['object'])==ds.DefectStudy:
                    self.grid[n]['object'].plot_formation_energy(ax=ax)
                else:
                    self.grid[n]['object'].plot_formation_energy(ax=ax, fpp=self.grid[n]['object'].lastfpp, tight=False)
            elif selected_ptype == 'Transition Levels':
                if type(self.grid[n]['object'])==ds.DefectStudy:
                    self.grid[n]['object'].plot_transition_levels(ax=ax)
                else:
                    self.grid[n]['object'].plot_transition_levels(ax=ax, tpp=self.grid[n]['object'].lasttpp, tight=False)
            else:
                if selected_ptype == 'Defects Concentrations':
                    self.grid[n]['object'].defect_concentrations.plot(pp=self.grid[n]['object'].cpp, ax=ax, tight=False)
                elif selected_ptype == 'Charge Carriers Concentrations':
                    self.grid[n]['object'].defect_concentrations.plot(pp=self.grid[n]['object'].ccpp, ax=ax, tight=False)
                elif selected_ptype == 'Fermi Level Variations vs. Temperature':
                    self.grid[n]['object'].defect_concentrations.plot(pp=self.grid[n]['object'].eftpp, ax=ax, tight=False)
                elif selected_ptype == 'Stability Domain':
                    self.grid[n]['object'].plot_stability_domain(ppp=self.grid[n]['object'].lastppp, ax=ax, tight=False)
        else:        
            if type(self.grid[n]['object'])==ds.DefectStudy:
                if self.elements[n]['ptype'] == 'Defect Formation Energies':
                    self.grid[n]['object'].plot_dos(ax=ax, tpp=selected_pp, tight=False)
                elif self.elements[n]['ptype'] == 'Transition Levels':
                    self.grid[n]['object'].plot_transition_levels(ax=ax, tpp=selected_pp, tight=False)
            elif selected_ptype == 'Density of States':
                self.grid[n]['object'].plot_dos(ax=ax, dpp=selected_pp, tight=False)
            elif selected_ptype == 'Band diagram':
                self.grid[n]['object'].plot_band_diagram(ax=ax, bpp=selected_pp, tight=False)
            elif selected_ptype == 'Optical Indices':
                self.grid[n]['object'].plot(pp=selected_pp, ax=ax, tight=False)
        
        
class MultipleSubplotFigureCreationWindow(tk.Toplevel):
    
    def __init__(self, mainwindow):
        tk.Toplevel.__init__(self, mainwindow)
        self.resizable(False, False)
        self.mainwindow = mainwindow
        
        self.main_frame = tk.Frame(self)
        self.main_frame.grid(sticky='nsew')

        self.title('Multiple Figure Creation Window')
        
        self.grid_param_frame = tk.Frame(self.main_frame)
        self.grid_param_frame.grid(sticky='nsew')
        
        tk.Label(self.grid_param_frame, text='Figure Name').grid(row=0, column=0)
        self.name_var = tk.StringVar()
        tk.Entry(self.grid_param_frame, textvariable=self.name_var).grid(row=0, column=1)
        
        tk.Label(self.grid_param_frame, text='Number of rows').grid(row=1, column=0)
        tk.Label(self.grid_param_frame, text='Number of columns').grid(row=2, column=0)
        
        self.nrow_var = tk.IntVar(value=2)
        self.ncol_var = tk.IntVar(value=2)
        
        tk.Entry(self.grid_param_frame, textvariable=self.nrow_var).grid(row=1, column=1)
        tk.Entry(self.grid_param_frame, textvariable=self.ncol_var).grid(row=2, column=1)
        
        tk.Button(self.grid_param_frame, text='OK', command=self.configure).grid(column=1, sticky='nsew')
        
        self.grid_frame = tk.Frame(self.main_frame)
    
        # --------------------------------------------------- BUTTONS --------------------------------------------------

        self.buttons_frame = tkinter.ttk.Frame(self.main_frame)

        tk.Button(self.buttons_frame, text='Apply', command=self.save).grid(row=0, column=0, padx=5)
        tk.Button(self.buttons_frame, text='OK', command=lambda: self.save(close=True)).grid(row=0, column=1, padx=5)
        tk.Button(self.buttons_frame, text='Cancel', command=self.destroy).grid(row=0, column=2, padx=5)
        
        self.white_bg_icon = ImageTk.PhotoImage(Image.open('Pictures/FigureIcons/white.png'))
        self.bands_icon = ImageTk.PhotoImage(Image.open('Pictures/FigureIcons/Bands.png'))
        self.dos_icon = ImageTk.PhotoImage(Image.open('Pictures/FigureIcons/DoS.png'))
        self.oi_icon = ImageTk.PhotoImage(Image.open('Pictures/FigureIcons/OpticalIndex.png'))
        self.stability_domain_icon = ImageTk.PhotoImage(Image.open('Pictures/FigureIcons/StabilityDomain.png'))
        self.dfe_icon = ImageTk.PhotoImage(Image.open('Pictures/FigureIcons/DFE.png'))
        self.defect_conentrations_icon = ImageTk.PhotoImage(Image.open('Pictures/FigureIcons/DefectConcentrations.png'))
        self.transitions_icon = ImageTk.PhotoImage(Image.open('Pictures/FigureIcons/TransitionLevels.png'))
        self.fermi_level_icon = ImageTk.PhotoImage(Image.open('Pictures/FigureIcons/FermiLevel.png'))
        
    
    def save(self, close=False):
        self.attributes('-topmost', True)
        project = self.mainwindow.projects[self.mainwindow.currentprojectid]
        # add figure to figures manager
        self.mainwindow.fm.add(self.figure, project.pid)
        # save figure in current project
        project.mfigures[self.figure.name] = self.figure
        # plot
        self.mainwindow.plot_mfigure(self.figure)
        print('Multiple Subplot Figure ' + self.figure.name + ' successfully saved in Project ' + project.name)
        if close:
            self.destroy()
        
    
    def configure(self):
        if len(self.name_var.get()) > 0 and len(self.name_var.get().split()) > 0:
            self.name = self.name_var.get()
            self.nrow = self.nrow_var.get()
            self.ncol = self.ncol_var.get()
            self.figure = MultipleSubplotFigure(self.name, self.nrow, self.ncol)
            self.grid_param_frame.grid_forget()
            self.elements = {}
            for i in range(0, self.nrow*self.ncol):
                frame = tk.Frame(self.grid_frame)
                self.elements[i] = {}
                self.elements[i]['b'] = tk.Button(frame, bg='white', image=self.white_bg_icon)
                self.elements[i]['b'].grid(row=0, column=0, sticky='nsew', columnspan=2)
                tk.Label(frame, text='Object Type').grid(row=1, column=0, sticky='nsew')            
                self.elements[i]['otype'] = tkinter.ttk.Combobox(frame, values=object_types(), state="readonly")
                self.elements[i]['otype'].grid(row=1, column=1, sticky='nsew')
                tk.Label(frame, text='Object').grid(row=2, column=0, sticky='nsew') 
                self.elements[i]['obj'] = tkinter.ttk.Combobox(frame, state="readonly")
                self.elements[i]['obj'].grid(row=2, column=1, sticky='nsew')
                tk.Label(frame, text='Plot Type').grid(row=3, column=0, sticky='nsew') 
                self.elements[i]['ptype'] = tkinter.ttk.Combobox(frame, state="readonly")
                self.elements[i]['ptype'].grid(row=3, column=1, sticky='nsew')
                tk.Label(frame, text='Plot Parameters').grid(row=4, column=0, sticky='nsew')
                self.elements[i]['pp'] = tkinter.ttk.Combobox(frame, state="readonly")
                self.elements[i]['pp'].grid(row=4, column=1, sticky='nsew')
                row, col = fig_num_to_grid(i, self.nrow, self.ncol)
                frame.grid(row=int(row), column=int(col), sticky='nsew')
                self.elements[i]['otype'].bind("<<ComboboxSelected>>", lambda event, n=i: self.on_select_obj_type(event, n))
                self.elements[i]['obj'].bind("<<ComboboxSelected>>", lambda event, n=i: self.on_select_obj(event, n))
                self.elements[i]['ptype'].bind("<<ComboboxSelected>>", lambda event, n=i: self.on_select_plot_type(event, n))
                self.elements[i]['pp'].bind("<<ComboboxSelected>>", lambda event, n=i: self.on_select_pp(event, n))
                
            self.grid_frame.grid(sticky='nsew')
            self.buttons_frame.grid(pady=3, sticky='nse')
        else:
            print('Warning! Please specify figure name')
    
    def on_select_obj_type(self, event, n):
        # affect values list for nth Object Combobox
        # affect values list for nth Plot type Combobox
        selected_otype = self.elements[n]['otype'].get()
        project = self.mainwindow.projects[self.mainwindow.currentprojectid]
        if selected_otype == 'Cell':
            select_list = [cell.treetitle for cell in list(project.cells.values())]
            select_list.sort()
            self.elements[n]['obj'].configure(values=select_list)
            self.elements[n]['ptype'].configure(values=['Density of States', 'Band diagram', 'Optical Indices'])
        elif selected_otype == 'Chemical Potentials':
            if project.chemical_potentials is not None:
                self.elements[n]['obj'].configure(text=project.chemical_potentials.lastppp.name)
                self.elements[n]['ptype'].set('Stability Domain')
                self.add_element_to_figure({'object': project.chemical_potentials, 'pp': project.chemical_potentials.lastppp, 'selected_ptype': 'Stability Domain'}, n)
                self.update_icon('Stability Domain', n)
                self.elements[n]['pp'].configure(values=[cpp for cpp in list(project.pp['cpp'].values())])
            else:
                print('Warning! There is no Chemical Potentials in Project ' + str(project.name))
        elif selected_otype == 'Defect Study':
            self.elements[n]['obj'].configure(values=[def_stud.treetitle for def_stud in list(project.defect_studies.values())])
            self.elements[n]['ptype'].configure(values=['Defect Formation Energies', 'Transition Levels'])
        elif selected_otype == 'Material Study':
            self.elements[n]['obj'].configure(values=[mat_stud.treetitle for mat_stud in list(project.material_studies.values())])
            self.elements[n]['ptype'].configure(values=['Defect Formation Energies', 
            'Transition Levels', 'Defects Concentrations', 'Charge Carriers Concentrations', 
            'Fermi Level Variations vs. Temperature'])
    
    def on_select_obj(self, event, n):
        project = self.mainwindow.projects[self.mainwindow.currentprojectid]
        treetitle = self.elements[n]['obj'].get()
        selected_otype = self.elements[n]['otype'].get()
        if selected_otype == 'Cell':
            self.add_element_to_figure({'object': [cell for cell in list(project.cells.values()) if cell.treetitle==treetitle][0]}, n)
        elif selected_otype == 'Defect Study':
            findlist = [def_stud for def_stud in list(project.defect_studies.values()) if def_stud.treetitle==treetitle]
            if len(findlist)==0:
                findlist = [def_stud for def_stud in project.material_studies[mat_stud_key] for mat_stud_key in project.material_studies if def_stud.treetitle==treetitle]
            self.add_element_to_figure({'object': findlist[0]}, n)
        elif selected_otype == 'Material Study':
            self.add_element_to_figure({'object': [mat_stud for mat_stud in list(project.material_studies.values()) if mat_stud.treetitle==treetitle][0]}, n)
    
    def on_select_plot_type(self, event, n):
        # affect values list for nth Plot Parameters Combobox
        # update picture
        selected_ptype = self.elements[n]['ptype'].get()
        project = self.mainwindow.projects[self.mainwindow.currentprojectid]
        self.add_element_to_figure({'selected_ptype': selected_ptype}, n)
        if selected_ptype == 'Density of States':
            self.elements[n]['pp'].configure(values=[dpp.name for dpp in list(project.pp['dpp'].values())])
        elif selected_ptype == 'Band diagram':
            self.elements[n]['pp'].configure(values=[bpp.name for bpp in list(project.pp['bpp'].values())])
        elif selected_ptype == 'Optical Indices':
            self.elements[n]['pp'].configure(values=[opp.name for opp in list(project.pp['opp'].values())])
            self.figure.grid[n]['object'] = self.figure.grid[n]['object'].optical_indices
        elif selected_ptype == 'Defect Formation Energies':
            if type(self.figure.grid[n]['object'])==ds.DefectStudy:
                self.elements[n]['pp'].set(self.figure.grid[n]['object'].treetitle + ' Defect Formation Energies Plot Parameters')
            else:
                self.elements[n]['pp'].configure(values=[fpp.name for fpp in list(project.pp['fpp'].values())])
        elif selected_ptype == 'Transition Levels':
            if type(self.figure.grid[n]['object'])==ds.DefectStudy:
                self.elements[n]['pp'].set(self.figure.grid[n]['object'].treetitle + ' Transition Levels Plot Parameters')
            else:
                self.elements[n]['pp'].configure(values=[tpp for tpp in list(project.pp['tpp'].values())])
        self.update_icon(selected_ptype, n)
    
    def on_select_pp(self, event, n):
        # store in figure object
        project = self.mainwindow.projects[self.mainwindow.currentprojectid]
        selected_pp_name = self.elements[n]['pp'].get()
        selected_ptype = self.elements[n]['ptype'].get()
        if self.elements[n]['otype'].get() == 'Defect Study':
            if self.elements[n]['ptype'] == 'Defect Formation Energies':
                selected_pp = [fpp for fpp in list(project.pp['fpp'].values()) if fpp.name==selected_pp_name][0]
            elif self.elements[n]['ptype'] == 'Transition Levels':
                selected_pp = [bpp for bpp in list(project.pp['bpp'].values()) if bpp.name==selected_pp_name][0]
        elif selected_ptype == 'Density of States':
            selected_pp = [dpp for dpp in list(project.pp['dpp'].values()) if dpp.name==selected_pp_name][0]
        elif selected_ptype == 'Band diagram':
            selected_pp = [bpp for bpp in list(project.pp['bpp'].values()) if bpp.name==selected_pp_name][0]
        elif selected_ptype == 'Optical Indices':
            selected_pp = [opp for opp in list(project.pp['opp'].values()) if opp.name==selected_pp_name][0]
        self.add_element_to_figure({'selected_pp': selected_pp}, n)
    
    def update_icon(self, ptype, n):
        if ptype == 'Density of States':
            self.elements[n]['b'].configure(image=self.dos_icon)
        elif ptype == 'Band diagram':
            self.elements[n]['b'].configure(image=self.bands_icon)
        elif ptype == 'Optical Indices':
            self.elements[n]['b'].configure(image=self.oi_icon)
        elif ptype == 'Defect Formation Energies':
            self.elements[n]['b'].configure(image=self.dfe_icon)
        elif ptype == 'Transition Levels':
            self.elements[n]['b'].configure(image=self.transitions_icon)
        elif ptype == 'Defects Concentrations':
            self.elements[n]['b'].configure(image=self.defect_conentrations_icon)
        elif ptype == 'Charge Carriers Concentrations':
            self.elements[n]['b'].configure(image=self.defect_conentrations_icon)
        elif ptype == 'Fermi Level Variations vs. Temperature':
            self.elements[n]['b'].configure(image=self.fermi_level_icon)
        else:
            self.elements[n]['b'].configure(image=self.stability_domain_icon)
    
    def add_element_to_figure(self, argdict, n):
        try:
            self.figure.grid[n].update(argdict)
        except KeyError:
            self.figure.grid[n] = argdict
        

if __name__ == "__main__":
    root = Tk()
    w = MultipleSubplotFigureCreationWindow(root)
    w.mainloop()       
