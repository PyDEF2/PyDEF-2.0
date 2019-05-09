"""
    Project Manager in PyDEF GUI
    version:
    author: Adrien Stoliaroff
    email: adrien.stoliaroff@cnrs-imn.fr
"""

# GUI imports
import tkinter as tk
from tkinter import Tk, Frame, Menu, Button, Label
from tkinter import LEFT, RIGHT, TOP, BOTTOM, X, FLAT, RAISED, BOTH, END
import tkinter.ttk
import tkinter.messagebox as mb

import sys

# PyDEF imports
import cell_windows as cw
import chemical_potentials_windows as cpw
import defect_study_creation_window as dscw
import material_study_windows as msw
import pydef_core.basic_functions as bf
import pydef_core.optical_indices as oi
import pydef_core.defect_geom_comparison as gc


class ProjectsManager(object):
    """Project management tree: the tree displayed on the main window corresponding to the main window dictionary of Projects"""

    def __init__(self, parent, mainwindow): #Add command to make New Project button functionnal

        self.parent = parent
        self.mainwindow = mainwindow
        def rename():
            # To be able to rename tree elements
            # memory
            initialname = self.tree.item(self.popup.selection)['text']
            parent.isHost = len(initialname)>len(initialname.replace(' (host)',''))
            self.tree.item(self.popup.selection, text = initialname.replace(' (host)',''))
            treepointer = self.tree
            selectionpointer = self.popup.selection
            mainwindow.capitalLetter = False
            #Listen to keyboard and change text accordingly
            def keyboardname(event):
                name = treepointer.item(selectionpointer)['text']
                if event.keysym_num == 65293:
                    # when Enter key pressed, save changes to Project object and exit function
                    mainwindow.unbind("<Key>", listener)
                    otype = ''
                    pid, cid = self.tree.item(self.popup.selection)['values']
                    if pid == cid:
                        # item is the project
                        pid = self.tree.item(self.popup.selection, 'values')[0]
                        self.mainwindow.projects[pid].name = name
                        self.mainwindow.fm.rename_proj(pid)
                        otype = 'project'
                    otype = mainwindow.projects[pid].object_str_type(cid)
                    if otype == 'cell':
                        self.mainwindow.projects[pid].cells[cid].treetitle = name
                    elif otype == 'defect-study':
                        is_embedded, containerID, removeID = self.mainwindow.projects[pid].is_embedded(cid)
                        if not is_embedded:
                            self.mainwindow.projects[pid].defect_studies[cid].treetitle = name
                        else:
                            self.mainwindow.projects[pid].material_studies[containerID].defect_studies[cid].treetitle = name
                    elif otype == 'material-study':
                        self.mainwindow.projects[pid].material_studies[cid].treetitle = name
                    print('Renamed ' + initialname.replace(' (host)','') + ' to ' + name)
                    if parent.isHost:
                        treepointer.item(selectionpointer, text = name + ' (host)')
                elif event.keysym_num == 65288: # Delete
                    mainwindow.capitalLetter = False
                    treepointer.item(selectionpointer, text = name[:-1])
                elif event.keysym_num == 65505 or event.keysym_num == 65506:# Shift
                    mainwindow.capitalLetter = True
                elif event.keysym_num == 65307: # Escape
                    treepointer.item(selectionpointer, text = initialname)
                else:
                    if len(event.keysym) == 1:
                        if mainwindow.capitalLetter:
                            treepointer.item(selectionpointer, text = name + event.keysym.capitalize())
                        else:
                            treepointer.item(selectionpointer, text = name + event.keysym)
                    if event.keysym.find('KP') > -1:#number from keypad
                        treepointer.item(selectionpointer, text = name + event.keysym.split('_')[1])
                    if event.keysym == 'space':
                        treepointer.item(selectionpointer, text = name + " ")
                    if event.keysym == 'minus':
                        treepointer.item(selectionpointer, text = name + "-")
                    if event.keysym == 'underscore':
                        treepointer.item(selectionpointer, text = name + "_")
                    mainwindow.capitalLetter = False
            listener = mainwindow.bind("<Key>", keyboardname)# Calls function keyboardname defined earlier
            # Flash so that the user knows he/she can rename
            for i in range(0, 2):
                mainwindow.after(i*500, lambda: treepointer.item(selectionpointer, text = ''))
                mainwindow.after(i*500+250, lambda: treepointer.item(selectionpointer, text = initialname))

        # Create context menu
        self.popup = tk.Menu(parent, tearoff=0)
        self.popup.items = 0

        def plot(event = None):
            try:
                self.mainwindow.currentitemid = self.tree.item(self.tree.identify_row(event.y))['values'][1] #in case of double-click
                self.mainwindow.currentprojectid = self.tree.item(self.tree.identify_row(event.y))['values'][0] #in case of double-click
            except AttributeError as e:
                # selected from button or contextual menu
                pass
            self.mainwindow.plot()
            
        def plot_optical_indices(event = None):
            try:
                self.mainwindow.currentitemid = self.tree.item(self.tree.identify_row(event.y))['values'][1] #in case of double-click
                self.mainwindow.currentprojectid = self.tree.item(self.tree.identify_row(event.y))['values'][0] #in case of double-click
            except AttributeError as e:
                # selected from button or contextual menu
                pass
            self.mainwindow.plot_optical_indices()    
        
        def declare_as_host():
            pid, cid = self.tree.item(self.popup.selection)['values']
            if self.mainwindow.projects[pid].hostcellid != '':
                if mb.askokcancel('Declare Host', 'This project already has a host, are you sure you want to change host ? (This will delete all current Defect Studies and Material Studies)', parent=self.mainwindow):
                    formerhostid = mainwindow.projects[pid].hostcellid 
                    self.delete_tree_entry(pid, formerhostid, header=self.mem[pid]['cells_header']) 
                    self.newunboundcalc(self.mainwindow.projects[pid].cells[formerhostid], pid)
                    self.clear_studies(pid)
                    mainwindow.projects[pid].hostcellid = cid
                    self.delete_tree_entry(pid, cid, header=self.mem[pid]['cells_header'])
                    self.newunboundcalc(self.mainwindow.projects[pid].cells[cid], pid, isHost=True)
            else:
                self.delete_tree_entry(pid, cid, header=self.mem[pid]['cells_header'])
                self.newunboundcalc(self.mainwindow.projects[pid].cells[cid], pid, isHost=True)
                mainwindow.projects[pid].hostcellid = cid

        def show_cell_info_window():
            cell = self.mainwindow.projects[self.mainwindow.currentprojectid].cells[self.mainwindow.currentitemid]
            cw.CellsInfoWindow(self.mainwindow, cell)

        def show_dpp_window():
            cell = self.mainwindow.projects[self.mainwindow.currentprojectid].cells[self.mainwindow.currentitemid]
            # dpp = cell.lastdpp
            # cw.DosPlotParametersWindow(self.mainwindow, cell, dpp)
            try:
                dpp = cell.lastdpp
                cw.DosPlotParametersWindow(self.mainwindow, cell, dpp)
            except AttributeError as e:
                print('Warning! ' + cell.treetitle + ' has no DOSCAR! Please import a DOSCAR to plot DoS')
                # self.mainwindow.printerror(str(e))

        def show_bpp_window():
            cell = self.mainwindow.projects[self.mainwindow.currentprojectid].cells[self.mainwindow.currentitemid]
            # try:
            bpp = cell.lastbpp
            cw.BandPlotParametersWindow(self.mainwindow, cell, bpp)
            # except AttributeError:
                # print 'Warning! ' + cell.treetitle + ' has no Band Diagram Plot Parameters!'
        
        def show_gc_window():
            project = self.mainwindow.projects[self.mainwindow.currentprojectid]
            cid = self.mainwindow.currentitemid
            cell = project.cells[cid]
            is_embedded, dsid, cid1 = project.is_embedded(cid)
            if is_embedded: # necessarily embedded
                if project.object_str_type(dsid) == 'material-study':
                    mat_stud = project.material_studies[dsid]
                    def_stud1 = [def_stud for def_stud in list(mat_stud.defect_studies.values()) for dc_stud in list(def_stud.defect_cell_studies.values()) if dc_stud.defect_cell == cell][0]
                    defects = def_stud1.defects
                else:
                    defects = project.defect_studies[dsid].defects  
            # Window asking to specify params
            choicew = cw.GeomComparisonParametersWindow(self.mainwindow)
            r_corr_cut = choicew.r_corr_cut
            r_coord_sphere = choicew.r_coord_sphere
            signif_var_min = choicew.signif_var_min
            self.mainwindow.wait_window(choicew) 
            cell.gc = gc.GeomComparison(project.cells[project.hostcellid], defects, cell, 
            r_corr_cut=r_corr_cut, r_coord_sphere_cut=r_coord_sphere, signif_var_min=signif_var_min)
            cell.gc.compare_geom()
            # display results
            cw.GeomComparisonResultsWindow(self.mainwindow, cell.gc)
        
        def show_bfp_window():
            cell = self.mainwindow.projects[self.mainwindow.currentprojectid].cells[self.mainwindow.currentitemid]
            cw.BandFitParametersWindow(self.mainwindow, cell)
        
        def show_fpp_window():
            is_embedded, msid, dsid = self.mainwindow.projects[self.mainwindow.currentprojectid].is_embedded(self.mainwindow.currentitemid)
            if is_embedded:
                defect_study = self.mainwindow.projects[self.mainwindow.currentprojectid].material_studies[msid].defect_studies[dsid]
                msw.DefectStudyPlotParametersWindow(self.mainwindow, defect_study)
            else:
                defect_study = self.mainwindow.projects[self.mainwindow.currentprojectid].defect_studies[self.mainwindow.currentitemid]
                msw.DefectStudyPlotParametersWindow(self.mainwindow, defect_study)
        
        def show_ms_fpp_window():
            material_study = self.mainwindow.projects[self.mainwindow.currentprojectid].material_studies[self.mainwindow.currentitemid]
            msw.MaterialStudyPlotParametersWindow(self.mainwindow, material_study)
            
        def show_ppp_window():
            project = self.mainwindow.projects[self.mainwindow.currentprojectid]
            cpw.PotentialsPlotParametersWindow(self.mainwindow, project, project.chemical_potentials)
        
        def show_opp_window():
            project = self.mainwindow.projects[self.mainwindow.currentprojectid]
            def print_m():
                message = 'Warning! There is no dielectric function to plot in this file! '
                message += '\nSee https://cms.mpi.univie.ac.at/wiki/index.php/Dielectric_properties_of_SiC for VASP help'
                print(message)
                return None
            try:
                cell = project.cells[self.mainwindow.currentitemid]
                len(cell.optical_indices.components)
            except TypeError as e :
                if bf.grep(cell.outcar, "DIELECTRIC FUNCTION") is not None or bf.grep(cell.outcar, "DIELECTRIC TENSOR") is not None:
                    cell.optical_indices = oi.OpticalIndices(cell.outcar)
                else:
                    print_m()
            except AttributeError as e:
                print_m()
            opp = project.cells[self.mainwindow.currentitemid].optical_indices.lastopp
            if opp not in project.pp['opp']:
              project.pp['opp'].update({opp.name: opp})
            cw.OpticalIndicesPlotParametersWindow(self.mainwindow, project, opp)
        
        def show_cpp_window():
            material_study = self.mainwindow.projects[self.mainwindow.currentprojectid].material_studies[self.mainwindow.currentitemid]
            msw.ConcentrationsPlotParametersWindow(self.mainwindow, material_study)
            
        def show_ccpp_window():
            material_study = self.mainwindow.projects[self.mainwindow.currentprojectid].material_studies[self.mainwindow.currentitemid]
            msw.ChargeCarriersConcentrationsPlotParametersWindow(self.mainwindow, material_study)
            
        def show_eftpp_window():
            material_study = self.mainwindow.projects[self.mainwindow.currentprojectid].material_studies[self.mainwindow.currentitemid]
            msw.FermiLevelVariationsPlotParametersWindow(self.mainwindow, material_study)

        def show_ms_summary_window():
          project = self.mainwindow.projects[self.mainwindow.currentprojectid]
          ms = project.material_studies[self.mainwindow.currentitemid]
          msw.SummaryWindow(self.mainwindow, ms)
        
        def select(event):
            self.selection = selection = self.tree.identify_row(event.y)
            try:
                self.mainwindow.currentprojectid = self.tree.item(selection)['values'][0]
                self.mainwindow.currentitemid = self.tree.item(selection)['values'][1]
            except IndexError:
                pass
            
        def edit_chem_pot():
            project = self.mainwindow.projects[self.mainwindow.currentprojectid] 
            cpw.ChemicalPotentialsCreationWindow(self.mainwindow, project, project.chemical_potentials)
        
        def edit_ds():
            is_embedded, msid, dsid = self.mainwindow.projects[self.mainwindow.currentprojectid].is_embedded(self.mainwindow.currentitemid)
            if is_embedded:
                dscw.DefectStudyCreationWindow(self.mainwindow, self.mainwindow.projects[self.mainwindow.currentprojectid], self.mainwindow.projects[self.mainwindow.currentprojectid].material_studies[msid].defect_studies[dsid])
            else:
                dscw.DefectStudyCreationWindow(self.mainwindow, self.mainwindow.projects[self.mainwindow.currentprojectid], self.mainwindow.projects[self.mainwindow.currentprojectid].defect_studies[self.mainwindow.currentitemid])
        
        def edit_ms():
            msw.MaterialStudyCreationWindow(self.mainwindow, self.mainwindow.projects[self.mainwindow.currentprojectid], self.mainwindow.projects[self.mainwindow.currentprojectid].material_studies[self.mainwindow.currentitemid])
        
        def load():
            pid = self.tree.item(self.popup.selection)['values'][1]
            self.mainwindow.load_project(pid)
            # refresh tree
            self.delete_tree_entry(pid,pid)
            self.new_project(self.mainwindow.projects[pid])

        def do_popup(event):
            """display the popup menu"""
            select(event)
            self.popup.delete(0, self.popup.items + 2) 
            self.popup.selection = self.tree.identify_row(event.y)
            # change self.mainwindow.currentprojectid to selected project ID
            self.mainwindow.currentprojectid = self.tree.item(self.popup.selection)['values'][0]
            self.mainwindow.currentitemid = self.tree.item(self.popup.selection)['values'][1]

            # print 'Tree entry ID: ' + self.tree.item(self.popup.selection)['values'][1]
            if self.mainwindow.projects[self.mainwindow.currentprojectid].object_str_type(self.tree.item(self.popup.selection)['values'][1]) == 'cell':
                self.popup.add_command(label="Rename", command=rename)
                self.popup.add_command(label="Delete", command=self.delete)
                self.popup.add_separator()
                if not self.mainwindow.projects[self.mainwindow.currentprojectid].hostcellid == self.tree.item(self.popup.selection)['values'][1]:
                    self.popup.add_command(label="Declare as host", command=declare_as_host)
                self.popup.add_command(label="View calculation summary", command=show_cell_info_window)
                self.popup.add_separator()
                self.popup.add_command(label="Plot DoS", command=plot)
                self.popup.add_command(label="Plot Band Diagram", command=self.mainwindow.plot_band_diagram)
                self.popup.add_command(label="Plot Optical Indices", command=plot_optical_indices)
                self.popup.add_command(label="Fit Bands to get effective masses", command=show_bfp_window)
                if not self.mainwindow.projects[self.mainwindow.currentprojectid].hostcellid == self.tree.item(self.popup.selection)['values'][1]:
                    is_embedded, dsid, cid = self.mainwindow.projects[self.mainwindow.currentprojectid].is_embedded(self.tree.item(self.popup.selection)['values'][1])
                    if is_embedded:
                        self.popup.add_command(label="Compare geometry to host cell", command=show_gc_window)
                self.popup.add_separator()
                self.popup.add_command(label="Edit DoS plot settings", command=show_dpp_window)
                self.popup.add_command(label="Edit Band Diagram settings", command=show_bpp_window)
                self.popup.add_command(label="Edit Optical Indices settings", command=show_opp_window)
                self.popup.items = 12
            elif self.mainwindow.projects[self.mainwindow.currentprojectid].object_str_type(self.tree.item(self.popup.selection)['values'][1]) == 'project':
                self.popup.add_command(label="Rename", command=rename)
                self.popup.add_command(label="Delete", command=self.delete)
                self.popup.items = 2
            elif self.mainwindow.projects[self.mainwindow.currentprojectid].object_str_type(self.tree.item(self.popup.selection)['values'][1]) == 'chem-pot':
                self.popup.add_command(label="Delete", command=self.delete)
                self.popup.add_command(label="Edit Phases", command=edit_chem_pot)
                self.popup.add_separator()
                self.popup.add_command(label="Edit Plot Parameters", command=show_ppp_window)
                self.popup.items = 3
            elif self.mainwindow.projects[self.mainwindow.currentprojectid].object_str_type(self.tree.item(self.popup.selection)['values'][1]) == 'defect-study':
                self.popup.add_command(label="Rename", command=rename)
                self.popup.add_command(label="Edit", command=edit_ds)
                self.popup.add_command(label="Delete", command=self.delete)
                self.popup.add_separator()
                self.popup.add_command(label="Plot Defect Formation Energy", command=self.mainwindow.plot)
                self.popup.add_command(label="Plot Transitions Levels", command=self.mainwindow.plot_transition_levels)
                self.popup.add_separator()
                self.popup.add_command(label="Edit Defect Formation Energy plot settings", command=show_fpp_window)
                self.popup.items = 6
            elif self.mainwindow.projects[self.mainwindow.currentprojectid].object_str_type(self.tree.item(self.popup.selection)['values'][1]) == 'material-study':
                self.popup.add_command(label="Rename", command=rename)
                self.popup.add_command(label="Edit", command=edit_ms)
                self.popup.add_command(label="Delete", command=self.delete)
                self.popup.add_separator()
                self.popup.add_command(label="Defect Formation Energy Corrections Summary", command=show_ms_summary_window)
                self.popup.add_command(label="Plot Defect Formation Energies", command=self.mainwindow.plot)
                self.popup.add_command(label="Plot Transitions Levels", command=self.mainwindow.plot_transition_levels)
                self.popup.add_command(label="Plot Defect Concentrations vs Tgrowth", command=self.mainwindow.plot_defect_concentrations)
                self.popup.add_command(label="Plot Charge Carriers Concentrations vs Troom", command=lambda: self.mainwindow.plot_defect_concentrations(code=1))
                self.popup.add_command(label="Plot EF vs Troom", command=lambda: self.mainwindow.plot_defect_concentrations(code=2))
                self.popup.add_separator()
                self.popup.add_command(label="Edit Defect Formation Energies plot settings", command=show_ms_fpp_window)
                self.popup.add_command(label="Edit Defect Concentrations plot settings", command=show_cpp_window)
                self.popup.add_command(label="Edit Charge Carriers Concentrations plot settings", command=show_ccpp_window)
                self.popup.add_command(label="Edit Fermi Level plot settings", command=show_eftpp_window)
                self.popup.items = 13
            self.tree.focus(self.popup.selection)
            self.tree.selection_set(self.popup.selection)
            self.popup.post(event.x_root, event.y_root)
            # Close contextual menu when mouse leaves menu
            def popupFocusOut(event=None):
                self.popup.unpost()
                self.popup.delete(0, self.popup.items)
            self.popup.bind("<Leave>", popupFocusOut)
            
        
        # Prepare tree
        self.tree = tkinter.ttk.Treeview(parent)
        self.tree.heading("#0", text = "New Project")
        self.mem = {}
        sortlist = [(proj.pid, proj) for proj in list(mainwindow.projects.values())]
        sortlist.sort(key=lambda x: x[0])
        for name, project in sortlist:
            self.mainwindow.currentprojectid = project.pid
            self.new_project(project)
        self.tree.bind("<Button-1>", select)
        self.tree.bind("<Button-3>", select)
        self.tree.bind("<Button-3>", do_popup)
        if sys.platform == 'darwin':
            # on MacOSX, right-click button is button 2
            # https://stackoverflow.com/questions/30668425/tkinter-right-click-popup-unresponsive-on-osx
            self.tree.bind("<Button-2>", select)
            self.tree.bind("<Button-2>", do_popup)
        self.tree.bind("<Double-Button-1>", plot)
        
    
    
    def delete(self):
            # if not embedded, remove
            # if embedded, go back to unsorted calculations
            otype = ''
            pid, cid = self.tree.item(self.selection)['values']
            mainwindow = self.mainwindow
            if pid == cid:
                # item is the project
                if mb.askokcancel('Delete', 'Are you sure you want to delete this Project ?', parent=self.mainwindow):
                    mainwindow.projects.pop(pid)
                    mainwindow.fm.delete_proj(pid)
                    mainwindow.pm.delete_proj(pid)
                    mainwindow.projects_mem.pop(pid)
                    otype = 'project'
                else:
                    return None
            if len(otype)<1:
                otype = mainwindow.projects[pid].object_str_type(cid)
            # print 'otype: ' + otype

            if otype == 'cell':
                res, containerID, removeID = mainwindow.projects[pid].is_embedded(cid)
                if not res:
                    if mainwindow.projects[pid].hostcellid == cid:
                        if mb.askokcancel('Delete', 'Are you sure you want to delete the host cell ? (This will delete Defect Studies and Material Studies)', parent=self.mainwindow):
                            mainwindow.projects[pid].hostcellid = ''
                            mainwindow.projects[pid].cells.pop(cid)
                            mainwindow.projects[pid].unboundcells.pop(cid)
                            # Delete Defect Studies and Material Studies
                            self.clear_studies(pid)
                    else:
                        mainwindow.projects[pid].cells.pop(cid)
                        mainwindow.projects[pid].unboundcells.pop(cid) 
                else:
                    if removeID.find('//')>0:
                        # Cell is inside a Defect Study inside a Material Study
                        dsID, dcsID = removeID.split('//')
                        cell = mainwindow.projects[pid].material_studies[containerID].defect_studies[dsID].defect_cell_studies.pop(dcsID).defect_cell
                    else:
                        # Cell is inside an unbounded Defect Study
                        cell = mainwindow.projects[pid].defect_studies[containerID].defect_cell_studies.pop(removeID).defect_cell
                    self.tree.insert(self.mem[pid]['cells_header'], self.mem[pid]['ncalc'], text = cell.treetitle, values = [pid, cell.ID])
            elif otype == 'chem-pot':
                nonsyn = list(self.mainwindow.projects[pid].chemical_potentials.non_synthesized.values())
                for cell in nonsyn:
                    self.mainwindow.projects[pid].add_cell(cell)
                self.remove_chemical_potentials(pid)
            elif otype == 'defect-study':
                is_embedded, containerID, removeID = self.mainwindow.projects[self.mainwindow.currentprojectid].is_embedded(self.mainwindow.currentitemid)
                if is_embedded:
                    self.mainwindow.pm.remove_defect_study_from_material_study(self.mainwindow.projects[pid].material_studies[containerID].defect_studies[self.mainwindow.currentitemid], self.mainwindow.projects[pid].material_studies[containerID], pid)
                else:
                    sort_charge_list = [[dcstud, dcstud.defect_cell.charge] for dcstud in list(self.mainwindow.projects[pid].defect_studies[cid].defect_cell_studies.values())]
                    sort_charge_list.sort(key=lambda x: x[1])
                    for dcstud, q in sort_charge_list:
                        self.mainwindow.projects[pid].add_cell(dcstud.defect_cell)
                    self.mainwindow.projects[pid].defect_studies.pop(cid)
            elif otype == 'material-study':
                sortmslist = [[dstud.treetitle, dstud] for dstud in list(self.mainwindow.projects[pid].material_studies[cid].defect_studies.values())]
                sortmslist.sort(key=lambda x: x[0])
                for treetitle, defstud in sortmslist:
                    self.mainwindow.projects[pid].add_defect_study(defstud)
                self.mainwindow.projects[pid].material_studies.pop(cid)
            try:
                self.tree.delete(self.selection)
            except tk.TclError:
                # entry already removed by previously called method
                pass
            try:
                project = self.mainwindow.projects[pid]
                if (len(list(project.defect_studies.keys())) == 0) and ('defect_studies_header' in self.mem[pid]):
                    try:
                        self.tree.delete(self.mem[pid]['defect_studies_header'])
                    except TclError:
                        pass
                    self.mem[pid].pop('defect_studies_header')
                if (len(list(project.material_studies.keys())) == 0) and ('material_studies_header' in self.mem[pid]):
                    self.tree.delete(self.mem[pid]['material_studies_header'])
                    self.mem[pid].pop('material_studies_header')
            except KeyError:
                # The project has been deleted
                pass
    
    def newunboundcalc(self, newcell, projid, isHost=False):
        if isHost:
            self.tree.insert(self.mem[projid]['cells_header'], 0, text = newcell.rname + '(host)', values = [projid, newcell.ID])
        else:
            self.tree.insert(self.mem[projid]['cells_header'], self.mem[projid]['ncalc'], text = newcell.treetitle, values = [projid, newcell.ID])
        self.mem[projid]['ncalc'] += 1
            
    def new_chemical_potentials(self, projid):
        project = self.mainwindow.projects[self.mainwindow.currentprojectid]
        try:
            chem_pot_entry = self.tree.insert(self.mem[projid]['proj'], 1, 
            text=project.cells[project.hostcellid].rname + ' Stability Domain', 
            values=[projid, project.chemical_potentials.ID])
            self.mem[projid]['chem_pot_header'] = chem_pot_entry
            self.mem[projid]['chem_pot_n_ns'] = 0
            cells_list = [[cell, cell.treetitle] for cell in list(project.chemical_potentials.non_synthesized.values())]
            cells_list.sort(key=lambda x: x[1])
            for cell, title in cells_list:
                self.add_phase_in_chemical_potentials(cell, projid)
            self.mainwindow.currentitemid = project.chemical_potentials.ID
        except KeyError:
            print('KeyError while trying to create chemical potentials in ' + project.name + '(' + project.pid + ')')
        
    def add_phase_in_chemical_potentials(self, cell, projid):
        self.delete_tree_entry(projid, cell.ID, header=self.mem[projid]['cells_header'])
        self.tree.insert(self.mem[projid]['chem_pot_header'], self.mem[projid]['chem_pot_n_ns'], text = cell.rname, values = [projid, cell.ID])
        self.mem[projid]['chem_pot_n_ns'] += 1
        
    def remove_phase_from_chemical_potentials(self, cell, projid):
        self.delete_tree_entry(projid, cell.ID, header=self.mem[projid]['chem_pot_header'])
        self.mainwindow.projects[projid].chemical_potentials.non_synthesized.pop(cell.ID)
        self.mem[projid]['chem_pot_n_ns'] -= 1
        self.newunboundcalc(cell, projid)
    
    def remove_chemical_potentials(self, projid):
        project = self.mainwindow.projects[self.mainwindow.currentprojectid]
        self.tree.delete(self.mem[projid]['chem_pot_header'])
        self.mem[projid].pop('chem_pot_header')
        self.mem[projid].pop('chem_pot_n_ns')
    
    def new_defect_study(self, newdefstudy, projid):
        if not 'defect_studies_header' in list(self.mem[projid].keys()):
            defect_studies_header = self.tree.insert(self.mem[projid]['proj'], 1, text = 'Defect studies', values = [projid, 'title-entry-ds'])
            self.mem[projid].update({'defect_studies_header':defect_studies_header, 'n_defstudy':0})
        def_study_dict = {}
        def_study_dict[newdefstudy.ID] = self.tree.insert(self.mem[projid]['defect_studies_header'], self.mem[projid]['n_defstudy'], text = newdefstudy.treetitle, values = [projid, newdefstudy.ID])
        sort_charge_list = [[dcstud, dcstud.defect_cell.charge] for dcstud in list(newdefstudy.defect_cell_studies.values())]
        sort_charge_list.sort(key=lambda x: x[1])
        
        def_study_dict['n_dcs'] = 0
        if 'def_study_dict' not in list(self.mem[projid].keys()):
            self.mem[projid]['def_study_dict'] = def_study_dict
        else:
            self.mem[projid]['def_study_dict'].update(def_study_dict)
        self.mem[projid]['n_defstudy'] += 1
        for dcstud, q in sort_charge_list:
            self.new_defect_cell_study(dcstud, projid, newdefstudy.ID, dcstud.defect_cell.ID)
    
    def new_defect_cell_study(self, newdcs, projid, dsid, cid):
        """:param newdcs: new Defect Cell Study (Core object)
        :param projid: ID of the project (project.pid)
        :param dsid: ID of the Defect Study containing the Defect Cell Study
        :param cid: ID of the Cell contained in the new Defect Cell Study"""
        self.tree.insert(self.mem[projid]['def_study_dict'][dsid], self.mem[projid]['def_study_dict']['n_dcs'], text = newdcs.defect_cell.treetitle, values = [projid, newdcs.ID])
        self.mem[projid]['def_study_dict']['n_dcs'] += 1
        try:
            tree_entries = self.tree.get_children(self.mem[projid]['cells_header'])
            for item in tree_entries:
                item_entry = self.tree.item(item)
                if item_entry['values'][1] == cid:
                    self.tree.delete(item)
        except KeyError:
            pass
    
    def remove_defect_cell_study(self, dcsid, cell, dsid, projid):
        """remove Defect Cell Study from Tree (under Defect Study entry) and put Cell entry back under Calculation header"""
        tree_entries = self.tree.get_children(self.mem[projid]['def_study_dict'][dsid])
        for item in tree_entries:
            item_entry = self.tree.item(item)
            if item_entry['values'][1] == dcsid:
                self.tree.delete(item)
        self.tree.insert(self.mem[projid]['cells_header'], self.mem[projid]['ncalc'], text = cell.treetitle, values = [projid, cell.ID])
    
    def new_material_study(self, newms, projid):
        project = self.mainwindow.projects[projid]
        if not 'material_studies_header' in list(self.mem[projid].keys()):
            material_studies_header = self.tree.insert(self.mem[projid]['proj'], 2, text = 'Material studies', values = [project.pid, 'title-entry-ms'])
            self.mem[projid].update({'material_studies_header':material_studies_header, 'n_matstudy':0})
        if newms.ID not in list(project.material_studies.keys()):
            project.add_material_study(newms)
        matstudentry = self.tree.insert(self.mem[projid]['material_studies_header'], self.mem[projid]['n_matstudy'], text = newms.treetitle, values = [projid, newms.ID])
        # add Defect Studies under Material study entry
        i = 0
        for defstudy in newms.ds_list:
            def_study_entry = self.tree.insert(matstudentry, i, text=defstudy.treetitle, values=[projid, defstudy.ID])
            sort_charge_list = [[dcstudy.defect_cell.ID, dcstudy.defect_cell.charge] for dcstudy in list(defstudy.defect_cell_studies.values())]
            sort_charge_list.sort(key=lambda x: x[1])
            n_dcstudy = 0
            if 'def_study_dict' not in list(self.mem[projid].keys()):
                self.mem[projid]['def_study_dict'] = {}
            for dcsid, charge in sort_charge_list:
                dcstudy = defstudy.defect_cell_studies[dcsid]
                def_cell_study_entry = self.tree.insert(def_study_entry, n_dcstudy, text = dcstudy.defect_cell.treetitle, values = [projid, dcsid])
                n_dcstudy += 1
                self.mem[projid]['def_study_dict'][defstudy.ID] = def_study_entry    
                    
            i += 1
        self.mem[projid][newms.ID] = {'matstudentry': matstudentry, 'n_defect_studies': len(newms.defect_studies)}
        self.mem[projid]['n_matstudy'] += 1
        
        # remove defect studies in Material study from tree
        try:
            [self.delete_tree_entry(projid, defstud.ID, header=self.mem[projid]['defect_studies_header']) for defstud in list(newms.defect_studies.values())]
        except KeyError:
            pass
        if (len(list(project.defect_studies.keys())) == 0) and ('defect_studies_header' in self.mem[projid]):
            self.tree.delete(self.mem[projid]['defect_studies_header'])
            self.mem[projid].pop('defect_studies_header')
    
    def add_defect_study_to_material_study(self, argdefstudy, matstudy, projid):
        if argdefstudy.ID not in [defstudy.ID for defstudy in list(matstudy.defect_studies.values())]:
            # add Defect Study to Core Object
            matstudy.add_defect_study(argdefstudy)
            # delete Defect Study tree entry under Defect Studies header
            self.tree.delete(self.mem[projid]['def_study_dict'][argdefstudy.ID])
            self.mem[projid]['def_study_dict'].pop(argdefstudy.ID)
            defstudyentry = self.tree.insert(self.mem[projid][matstudy.ID]['matstudentry'], self.mem[projid][matstudy.ID]['n_defect_studies'], text=argdefstudy.treetitle, values = [projid, argdefstudy.ID])
            self.mem[projid]['def_study_dict'][argdefstudy.ID] = defstudyentry
            sort_charge_list = [[dcstudy.defect_cell.ID, dcstudy.defect_cell.charge] for dcstudy in list(argdefstudy.defect_cell_studies.values())]
            sort_charge_list.sort(key=lambda x: x[1])
            n_dcstudy = 0
            for dcsid, charge in sort_charge_list:
                dcstudy = argdefstudy.defect_cell_studies[dcsid]
                def_cell_study_entry = self.tree.insert(defstudyentry, n_dcstudy, text = dcstudy.defect_cell.treetitle, values = [projid, dcsid])
                n_dcstudy += 1
            self.mem[projid][matstudy.ID]['n_defect_studies'] += 1
            if (len(list(self.mainwindow.projects[projid].defect_studies.keys())) == 0) and ('defect_studies_header' in self.mem[projid]):
                self.tree.delete(self.mem[projid]['defect_studies_header'])
                self.mem[projid].pop('defect_studies_header')
    
    def remove_defect_study_from_material_study(self, argdefstudy, matstudy, projid):
        print('Removing Defect Study ' + argdefstudy.treetitle + ' fom Material Study ' + matstudy.treetitle)
        oldID = argdefstudy.ID
        matstudy.defect_studies.pop(oldID)
        self.mainwindow.projects[projid].add_defect_study(argdefstudy)
        self.tree.delete(self.mem[projid]['def_study_dict'][oldID])
        
    def new_project(self, project):
        index = int(project.pid.replace('P',''))
        proj = self.tree.insert("" , index, text = project.name, values = [project.pid, project.pid])
        if project.pid not in list(self.mem.keys()):
            self.mem[project.pid] = {'proj': proj}
        # cells_header = self.tree.insert(proj, 1, text = 'Calculations', values = [project.pid, 'title-entry'])
        cells_header = self.tree.insert(proj, 1, text = 'Calculations', values = [project.pid, 'title-entry-calculation'])
        self.mem[project.pid].update({'cells_header': cells_header})
        # Display host cell first
        ncalc = 0
        if len(project.hostcellid)>0:
            host = self.tree.insert(cells_header , 0, text = project.cells[project.hostcellid].rname + " (host)", values = [project.pid, project.hostcellid])
            ncalc = 1
        # List of unattached calculations
        for calckey in project.unboundcells:
            if project.unboundcells[calckey].ID != project.hostcellid:
                host = self.tree.insert(cells_header , ncalc, text = project.unboundcells[calckey].treetitle, values = [project.pid, calckey])
                ncalc += 1
        self.mem[project.pid].update({'ncalc': ncalc})
        # List of Chemical Potentials
        if project.chemical_potentials is not None and host is not None:
            self.new_chemical_potentials(project.pid)
        # List of Defect Studies
        sortmslist = [[dstud.treetitle, dstud] for dstud in list(project.defect_studies.values())]
        sortmslist.sort(key=lambda x: x[0])
        for treetitle, dstud in sortmslist:
            self.new_defect_study(dstud, project.pid)
        # List of Material Studies
        sortmslist = [[mstud.treetitle, mstud] for mstud in list(project.material_studies.values())]
        sortmslist.sort(key=lambda x: x[0])
        for treetitle, mstud in sortmslist:
            self.new_material_study(mstud, project.pid)
        self.mem[project.pid].update({'proj': proj}) #, 'cells_header': cells_header, , 'defect_studies_header': None, 'n_defstudy': 0}
    
    def delete_tree_entry(self, pid, cid, header=None):
        if header is not None:
            tree_entries = self.tree.get_children(header)
        else:
            tree_entries = self.tree.get_children()
        for item in tree_entries:
            item_pid, item_cid = self.tree.item(item)['values']
            if item_pid == pid and item_cid == cid:
                self.tree.delete(item)
        # if pid == cid:
            # self.mem.pop(pid)
    
    def delete_tree_category(self, pid, keyword):
        project_entries = self.tree.get_children()
        for project_entry in project_entries:
            children = self.tree.get_children(project_entry)
            for item in children:
                item_pid, item_cid = self.tree.item(item)['values']
                if item_cid.find(keyword)>=0 and item_pid == pid:
                    self.tree.delete(item)
                    
    def clear_studies(self, pid):
        if len(self.mainwindow.projects[pid].defect_studies)>0:
            keys = list(self.mainwindow.projects[pid].defect_studies.keys())
            for key in keys:
                self.mainwindow.projects[pid].defect_studies.pop(key)
            self.delete_tree_category(pid, 'title-entry-ds') 
        if len(self.mainwindow.projects[pid].material_studies)>0:
            keys = list(self.mainwindow.projects[pid].material_studies.keys())
            for key in keys:
                self.mainwindow.projects[pid].material_studies.pop(key)
            self.delete_tree_category(pid, 'title-entry-ms')
    
    def delete_proj(self, project_id):
        self.tree.delete(self.mem[project_id]['proj'])


class FigureManager(object):
    
    def __init__(self, parent, mainwindow):

        self.mainwindow = mainwindow
        
        self.tree = tkinter.ttk.Treeview(parent)
        self.tree.heading("#0", text = "Multiple Subplot Figures")
        
        project_titles = [(project, project.pid) for project in list(self.mainwindow.projects.values())]
        project_titles.sort(key=lambda x:x[1])
        
        p = -1
        self.mem = {}
        for project, pid in project_titles:
            p += 1
            proj = self.tree.insert('', p, text=project.name)
            self.mem[project.pid] = {'proj': proj}
            fig_names = [(fig, fig.name) for fig in list(project.mfigures.values())]
            fig_names.sort(key=lambda x:x[1])
            self.mem[project.pid].update({'nf':0})
            for mfigure, fname in fig_names:
                self.add(mfigure, project.pid)
                
        # Create context menu
        self.popup = tk.Menu(parent, tearoff=0)
        self.popup.items = 0
            
        def do_popup(event):
            """display the popup menu"""
            self.popup.delete(0, self.popup.items + 2) 
            self.selection = self.tree.identify_row(event.y)
            self.popup.add_command(label="Plot", command=plot)
            self.popup.add_command(label="Delete", command=self.remove_fig)
            self.popup.items = 2
            self.tree.focus(self.selection)
            self.tree.selection_set(self.selection)
            self.popup.post(event.x_root, event.y_root)
            # Close contextual menu when mouse leaves menu
            def popupFocusOut(event=None):
                self.popup.unpost()
                self.popup.delete(0, self.popup.items)
            self.popup.bind("<Leave>", popupFocusOut)
        
        def plot(event = None):
            try:
                selection = self.tree.item(self.tree.focus())
                pid, mfig_name = selection['values']
                self.mainwindow.plot_mfigure(self.mainwindow.projects[pid].mfigures[mfig_name])
            except ValueError:
                # User selected a project, not a figure
                pass
                    
        def select(event):
            self.selection = self.tree.identify_row(event.y)
        
        self.tree.bind("<Button-1>", select)
        self.tree.bind("<Button-3>", do_popup)
        if sys.platform == 'darwin':
            # on MacOSX, right-click button is button 2
            # https://stackoverflow.com/questions/30668425/tkinter-right-click-popup-unresponsive-on-osx
            self.tree.bind("<Button-2>", do_popup)
        self.tree.bind("<Double-Button-1>", plot)
        
        """for project in self.mainwindow.projects.values():
            for mfig in project.mfigures.values():
                self.add(mfig, project.pid)"""
                
    def new_project(self, new_proj):
        self.mem[new_proj.pid] = {'proj': self.tree.insert('', len(self.mem)+1, text=new_proj.name)}
    
    def rename_proj(self, pid):
        self.tree.item(self.mem[pid]['proj'], text=self.mainwindow.projects[pid].name)
                
    def add(self, mfigure, project_id):
        # if mfigure.name not in self.mainwindow.projects[project_id].mfigures.keys():
        try:
            self.mem[project_id]['nf'] += 1
        except KeyError:
            self.mem[project_id]['nf'] = 0
        self.tree.insert(self.mem[project_id]['proj'], self.mem[project_id]['nf'], text=mfigure.name, values=[project_id, mfigure.name])
    
    def remove_fig(self):
        selection = self.tree.item(self.tree.focus())
        pid, mfig_name = selection['values']
        self.tree.delete(self.tree.focus())
        project = self.mainwindow.projects[pid]
        project.mfigures.pop(mfig_name)
        self.mem[project.pid]['nf'] -= 1
        
    def delete_proj(self, project_id):
        self.tree.delete(self.mem[project_id]['proj'])
        self.mem.pop(project_id)
        
                    
class Project(object):
    """Project: the memory object which contains references to cells, optical_indexes, defect_studies, defect_concentrations, geometry_comparisons"""
    def __init__(self, argid, argname, mainwindow):
        self.mainwindow = mainwindow
        self.pid = argid # Project ID
        self.IDn = 0 # Number of objects added to the Project
        if len(argname) == 0:
            self.name = 'New Project'         # Project name
        else:
            self.name = argname
        self.hostcellid = ''
        self.cells = {}             # Dictionary of cells
        self.unboundcells = {}      # Dictionary of cells not attributed to any container
        self.defects = {} # Dictionary of Defects (not displayed)
        self.chemical_potentials = None 
        # There is only one chemical_potentials object per project as there is only one host
        self.material_studies = {}
        self.defect_studies = {}   # Dictionary of Defect studies (not embedded into any material study?)
        self.pp = {'ppp':{}, 'dpp': {}, 'bpp': {}, 'cpp': {}, 'fpp': {}, 'opp': {}}
        self.mfigures = {}
    
    def is_host(self, cell):
        return cell.ID == self.hostcellid

    def add_defect(self, defect, defect_displayname):
        name = defect.displayname
        if name in list(self.defects.keys()):
            self.defects[defect.displayname].chem_pot = defect.chem_pot
            self.defects[defect.displayname].nb_sites = defect.nb_sites
            self.defects[defect.displayname].name = defect.name
            print('Defect ' + defect.displayname + ' edited successfully')
        else:
            defect.displayname = defect_displayname
            self.defects[defect.displayname] = defect
            print('Defect ' + defect.displayname + ' created successfully')

    def add_cell(self, cell, dev = False):
        self.IDn += 1
        self.cells[self.pid + '/ID-cell-' + str(self.IDn)] = cell
        self.unboundcells[self.pid + '/ID-cell-' + str(self.IDn)] = cell
        cell.ID = self.pid + '/ID-cell-' + str(self.IDn)
        if not dev:
            self.mainwindow.pm.newunboundcalc(cell, str(self.mainwindow.currentprojectid))
        return self.pid + '/ID-cell-' + str(self.IDn)

    def define_host(self, argid):
        self.hostcellid = argid
        
    def add_defect_study(self, defect_study, dev=False):
        self.IDn += 1
        # Remove all cells in defect_study from unbounded cells
        for defect_cell_study_key in defect_study.defect_cell_studies:
            if defect_study.defect_cell_studies[defect_cell_study_key].defect_cell.ID in list(self.unboundcells.keys()):
                self.unboundcells.pop(defect_study.defect_cell_studies[defect_cell_study_key].defect_cell.ID)
        treetitle = bf.handle_same_string(defect_study.treetitle, [defstud.treetitle for defstud in list(self.defect_studies.values())])
        self.defect_studies[self.pid + '/ID-defect-study-' + str(self.IDn)] = defect_study
        defect_study.ID = self.pid + '/ID-defect-study-' + str(self.IDn)
        defect_study.treetitle = treetitle
        if not dev:
            self.mainwindow.pm.new_defect_study(defect_study, str(self.mainwindow.currentprojectid))
        return self.pid + '/ID-cell-' + str(self.IDn)        

    def add_material_study(self, material_study):
        self.IDn += 1
        for defect_study_key in material_study.defect_studies:
            try:
                self.defect_studies.pop(defect_study_key)
            except KeyError:
                pass
        treetitle = bf.handle_same_string(material_study.treetitle,[matstud.treetitle for matstud in list(self.material_studies.values())])
        self.material_studies[self.pid + '/ID-material-study-' + str(self.IDn)] = material_study
        material_study.ID = self.pid + '/ID-material-study-' + str(self.IDn)
        material_study.treetitle = treetitle
        return material_study.ID

    def is_embedded(self, objid):
        res = False
        containerID = ' '
        removeID = objid
        if self.object_str_type(objid) == 'cell':
            for key in self.defect_studies:
                for defectcellstudy in list(self.defect_studies[key].defect_cell_studies.values()):
                    try:
                        if objid == defectcellstudy.defect_cell.ID:
                            res = True
                            containerID = self.defect_studies[key].ID
                            removeID = defectcellstudy.ID
                    except Exception as e:
                        self.mainwindow.printerror(str(e))
            for material_study in list(self.material_studies.values()):
                for defect_study in list(material_study.defect_studies.values()):
                    for defect_cell_study in list(defect_study.defect_cell_studies.values()):
                        if objid == defect_cell_study.defect_cell.ID:
                            res = True
                            containerID = material_study.ID
                            removeID = defect_study.ID + '//' + defect_cell_study.ID
        elif self.object_str_type(objid) == 'defect-study':
            containerID, removeID = '', ''
            for material_study in list(self.material_studies.values()):
                for defect_study in list(material_study.defect_studies.values()):
                    if defect_study.ID == objid:
                        res = True
                        containerID = material_study.ID
                        removeID = objid
        return res, containerID, removeID

    def object_str_type(self, id):
        """Return the type of the object as a string by reading its ID"""
        res = ''
        if id.find('cell') > -1:
            res = 'cell'
        elif id.find('chem-pot') > -1:
            res = 'chem-pot'
        elif id.find('defect-study') > -1:
            res = 'defect-study'
        elif id.find('material-study') > -1:
            res = 'material-study'
        elif id.find('title-entry') > -1:
            res = 'title-entry'
        else:
            res = 'project'
        return res
