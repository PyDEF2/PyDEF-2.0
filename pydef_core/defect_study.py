import numpy as np
import scipy.optimize as sco
import matplotlib.patches as patches

import basic_functions as bf
import formation_energy_corrections as zc
import figure as pf


class DefectCellStudy(object):
    """ Object containing data on the various corrections of the defect formation energy for a given defect cell """

    def __init__(self, host_cell, defect_cell, defects, radius, z_e, z_h, geometry, e_r, mk_1_1, de_vbm, de_cbm,
                 pa_correction=True, mb_correction=True, phs_correction=True, vbm_correction=True, mp_correction=True):
        """
        :param host_cell: Cell object of the host cell calculation
        :param defect_cell: Cell object of the defect cell calculation
        :param defects: list of Defect objects
        :param radius: radius of the spheres in angstrom (float)
        :param z_e: number of electrons in the PHS
        :param z_h: number of holes in the PHS
        :param geometry: geometry of the host cell
        :param e_r: relative permittivity
        :param mk_1_1: value of the first term of the Makov-Payne correction in the case q = 1 & e_r = 1
        :param de_vbm: correction of the VBM
        :param de_cbm: correction of the CBM
        :param pa_correction: if True, the potential alignment correction is performed
        :param mb_correction: if True, the Moss-Burstein correction is performed
        :param phs_correction: if True, the PHS correction is performed
        :param vbm_correction: if True, the VBM correction is performed
        :param mp_correction: if True, the Makov-Payne correction is performed """

        self.host_cell = host_cell
        self.defect_cell = defect_cell
        self.defects = defects
        self.radius = radius
        self.charge = defect_cell.charge
        self.de_vbm = de_vbm
        self.de_cbm = de_cbm
        self.z_e = z_e
        self.z_h = z_h
        self.pa_correction = pa_correction
        self.mb_correction = mb_correction
        self.phs_correction = phs_correction
        self.vbm_correction = vbm_correction
        self.mp_correction = mp_correction

        bf.check_cells_consistency(host_cell, defect_cell)
        if defect_cell.isym != 0:
            print('Warning! You should set ISYM to 0')

        # Title of the defects for display (name of the defects + charge of the cell)
        charge_str = bf.float_to_str(self.defect_cell.charge)
        if len(defects) == 1:
            self.defects_title = self.defects[0].name + '^{' + charge_str + '}'
        else:
            self.defects_title = '(' + ' & '.join([f.name for f in self.defects]) + ')^{' + charge_str + '}'

        # Title of the Defect Cell Study for display
        self.title = host_cell.display_rname + ' - ' + self.defects_title

        # --------------------------------------------- CORRECTIONS ---------------------------------------------------

        if pa_correction:
            self.pa, self.pa_corr = self.get_pa_correction()
        else:
            self.pa, self.pa_corr = 0.0, 0.0

        if mb_correction:
            self.mb_corr = self.get_bands_correction(self.pa)[:2]  # holes, electrons
        else:
            self.mb_corr = [0.0, 0.0]

        if phs_correction is True:
            if self.mb_corr[0] == 0.0 and self.mb_corr[1] == 0.0:
                self.phs_corr = [0.0, 0.0]
            else:
                self.phs_corr = zc.phs_correction(z_h, z_e, self.de_vbm, self.de_cbm)
        else:
            self.phs_corr = [0.0, 0.0]

        if vbm_correction:
            self.vbm_corr = self.get_vbm_correction()
        else:
            self.vbm_corr = 0.0

        if mp_correction:
            self.mp_corr = self.get_mp_correction(geometry, e_r, mk_1_1)
        else:
            self.mp_corr = 0.0

        # Total correction
        self.tot_corr = self.pa_corr + sum(self.mb_corr) + sum(self.phs_corr) + self.vbm_corr + self.mp_corr
        energy_chem_pot = sum([f.n * float(f.chem_pot) for f in defects])
        self.e_for_0 = defect_cell.total_energy - host_cell.total_energy + energy_chem_pot + defect_cell.charge * host_cell.vbm_energy + self.tot_corr
            
    def set_z(self, z_e, z_h):
        self.z_e = z_e
        self.z_h = z_h
        if self.phs_correction is True:
            if self.mb_corr[0] == 0.0 and self.mb_corr[1] == 0.0:
                self.phs_corr = [0.0, 0.0]
            else:
                self.phs_corr = zc.phs_correction(z_h, z_e, self.de_vbm, self.de_cbm)
    
    def set_radius(self, radius):
        self.radius = radius
        print 'self.radius ' + str(self.radius)
        if self.pa_correction:
            self.pa, self.pa_corr = self.get_pa_correction()
        else:
            self.pa, self.pa_corr = 0.0, 0.0

    def plot_potential_alignment(self, atoms_labels):
        """ Draw 3 plots in a same figure
        1) Graphical representation of the positions of the defects and the atoms, and the spheres around the defects
        2) Average electrostatic energy difference between defect and host cells as a function of the spheres radius
        3) Electrostatic energy difference between defect and host cells between each atom as a function of their
           minimum distance from a defect
        :param atoms_labels: if True, display the atom label on the 3D representation """

        return zc.plot_potential_alignment(self.host_cell, self.defect_cell, self.defects, self.radius, self.title, atoms_labels)

    def get_formation_energy_at_EF(self, e_fermi):
        """ Return the formation energy value at e_fermi """

        return self.e_for_0 + self.charge * e_fermi

    def get_pa_correction(self):
        """ Get the potential alignment correction value """
        pa = zc.potential_alignment_correction(self.host_cell, self.defect_cell, self.defects, self.radius, False)[-1]
        return pa, pa * self.charge

    def get_bands_correction(self, pa):
        """ Get Moss-Burstein correction values and the number of electrons and holes in the CB and VB respectively """
        return zc.get_bands_correction(self.host_cell, self.defect_cell, pa)

    def get_phs_correction(self, z_h, z_e):
        """ Get the PHS correction values """
        return zc.phs_correction(z_h, z_e, self.de_vbm, self.de_cbm)

    def get_vbm_correction(self):
        """ Get the VBM correction value """
        return zc.vbm_correction(self.defect_cell, self.de_vbm)

    def get_mp_correction(self, geometry, e_r, mk_1_1):
        """ Get the Makov-Payne correction value """
        return zc.makov_payne_correction(self.defect_cell, geometry, e_r, mk_1_1)


class DefectStudy(object):
    """ Object containing different DefectCellStudy objects """

    def __init__(self, host_cell, host_cell_b, defects, geometry, e_r, mk_1_1, de_vbm_input, de_cbm_input, gaps_input,
                 pa_correction=True, mb_correction=True, phs_correction=True, vbm_correction=True, mp_correction=True):
        """
        :param host_cell: Cell object of the host cell calculation
        :param host_cell_b: Cell object of the host cell calculation (with a different functional)
        :param defects: list of Defect objects
        :param geometry: geometry of the host cell: 'sc', 'bcc', 'fcc', 'hcp' or 'other'
        :param e_r: relative permittivity
        :param mk_1_1: value of the first term of the Makov-Payne correction in the case q = 1 & e_r = 1
        :param de_vbm_input: further correction of the VBM
        :param de_cbm_input: further correction to the CBM
        :param gaps_input: gaps as a list such as [[2.4, 'Indirect gap'], [2.8, 'Direct gap']]
        :param pa_correction: if True, the potential alignment correction is performed
        :param mb_correction: if True, the Moss-Burstein correction is performed
        :param phs_correction: if True, the PHS correction is performed
        :param vbm_correction: if True, the VBM correction is performed
        :param mp_correction: if True, the Makov-Payne correction is performed """

        self.host_cell = host_cell
        self.defects = defects
        self.host_cell_b = host_cell_b
        self.geometry = geometry
        self.e_r = e_r
        self.mk_1_1 = mk_1_1
        self.gaps_input = gaps_input
        self.de_vbm_input = de_vbm_input
        self.de_cbm_input = de_cbm_input

        self.defect_cell_studies = {}

        # Corrections
        self.pa_correction = pa_correction
        self.mb_correction = mb_correction
        self.phs_correction = phs_correction
        self.vbm_correction = vbm_correction
        self.mp_correction = mp_correction

        # ID & Title
        self.defects_title = ' & '.join([f.name for f in defects])
        if len(defects) > 1:
            self.defects_label = '(' + self.defects_title + ')'
        else:
            self.defects_label = self.defects_title

        self.ID = host_cell.ID + '_' + '_'.join([f.ID for f in defects])
        self.title = host_cell.display_rname + ' - ' + host_cell.functional_title + ' - ' + self.defects_title
        self.treetitle = host_cell.rname + ' ' + self.defects_title.replace('{', '').replace('}', '').replace('_', '')

        # Correction of the band extrema
        if self.vbm_correction is True or self.phs_correction is True:
            self.de_vbm, self.de_cbm = zc.band_extrema_correction(host_cell, host_cell_b)
            self.de_vbm += self.de_vbm_input
            self.de_cbm += self.de_cbm_input
        else:
            self.de_vbm = 0.0
            self.de_cbm = 0.0

        # Gaps
        if gaps_input != ['']:
            gaps_labels = [x[1] for x in gaps_input]  # list of gaps label
            gaps = [float(x[0]) for x in gaps_input]  # values of the gaps
            self.gaps = dict(zip(gaps_labels, gaps))
        else:
            self.gaps = {}
        self.gap = self.host_cell.gap - self.de_vbm + self.de_cbm  # corrected gap
        self.gaps['Calculated gap'] = self.gap
        self.fpp = FormationPlotParameters(self)
        self.lasttpp = TransitionPlotParameters(self)
        
    @property
    def dcs(self):
        sortlist = [[self.defect_cell_studies[key], self.defect_cell_studies[key].defect_cell.charge] for key in self.defect_cell_studies]
        sortlist.sort(key=lambda x: x[1])
        return [x[0] for x in sortlist]

    def create_defect_cell_study(self, defect_cell, radius, z_e, z_h):
        """
        :param defect_cell: Call object of the defect cell
        :param radius: radius of the spheres
        :param z_e: number of electrons in the conduction band of the defect cell
        :param z_h: number of holes in the valence band of the defect cell
        """

        defect_cell_study = DefectCellStudy(self.host_cell, defect_cell, self.defects, radius, z_e, z_h,
                                            self.geometry, self.e_r, self.mk_1_1, self.de_vbm, self.de_cbm,
                                            self.pa_correction, self.mb_correction, self.phs_correction,
                                            self.vbm_correction, self.mp_correction)

        ds_id = bf.handle_same_string(defect_cell.ID, self.defect_cell_studies.keys())
        self.defect_cell_studies[ds_id] = defect_cell_study
        defect_cell_study.ID = ds_id
        
        self.fpp = FormationPlotParameters(self)
        
        return defect_cell_study

    def get_formation_energy_low_EF(self, e_fermi):
        """ Get the lowest formation energy at a given value of the Fermi energy """
        e_for_ef, charges = np.transpose([(f.get_formation_energy_at_EF(e_fermi), f.charge) for f in self.dcs])
        # return Fermi energy, minimum formation energy at E_Fermi, charge of defect and defect label
        return [[f, g] for f, g in zip(e_for_ef, charges) if f == min(e_for_ef)][0]

    def get_transition_levels(self, e_fermi_range):
        """ Retrieve all transitions levels energy in the range of fermi energies """

        # lowest formation energy and corresponding charge of the defect(s)
        e_for_low, q_low = np.transpose([self.get_formation_energy_low_EF(f) for f in e_fermi_range])

        # indices of the transitions
        transition_indices = np.where(np.diff(q_low) != 0.)[0] + 1

        # for each transition, return the fermi energy, the formation energy, the new charge and old charge states
        return [[e_fermi_range[f], e_for_low[f], q_low[f], q_low[f - 1]] for f in transition_indices]

    def plot_formation_energy(self, ax=None, tight=True):
        """ Plot the defect formation energy as a function of the Fermi level energy """

        ax, figure = pf.auto_ax(ax)

        e_fermi = np.linspace(self.fpp.xmin, np.max(self.gaps.values() + [self.fpp.xmax]), 10000)
        e_for = [f.get_formation_energy_at_EF(e_fermi) for f in self.dcs]
        e_for_low = np.array([self.get_formation_energy_low_EF(f)[0] for f in e_fermi])
        transition_levels = self.get_transition_levels(e_fermi)
        charges = [f.charge for f in self.dcs]

        # -------------------------------------------- PLOT PARAMETERS -------------------------------------------------

        [ax.plot(e_fermi, f, color='black', lw=1.5) for f in e_for]  # formation energies
        ax.plot(e_fermi, e_for_low, color='black', lw=4)  # lowest formation energy
        [ax.axvline(f[1], label=f[0], lw=2, ls='--') for f in self.gaps.items()]
        
        if self.fpp.display_charges:
            [charges_annotation(e_fermi, f, g, ax) for f, g in zip(e_for, charges)]
        
        if self.fpp.display_transition_levels:
            for level in transition_levels:
                ax.plot([level[0], level[0]], [ax.get_ylim()[0], level[1]], ls='--', color='black')
                text = r'$\epsilon(' + bf.float_to_str(level[3]) + '/' + bf.float_to_str(level[2]) + ')$'
                annotation = ax.annotate(text, xy=(level[0], ax.get_ylim()[0] + 0.1 * np.diff(ax.get_ylim())[0]),
                                         ha='center', va='top', backgroundcolor='w')
                annotation.draggable()
        
        ax.axhline(color='black')

        pf.set_ax_parameters(ax, title=self.fpp.title, xlabel=self.fpp.x_label, ylabel=self.fpp.y_label, xlim=[self.fpp.xmin, self.fpp.xmax], ylim=[self.fpp.ymin, self.fpp.ymax], legend=self.fpp.display_legends, grid=self.fpp.grid,
                             fontsize=self.fpp.fontsize, l_fontsize=self.fpp.l_fontsize, xticks=self.fpp.xticks_var, xtick_labels=self.fpp.xticklabels_var, yticks=self.fpp.yticks_var,
                             ytick_label=self.fpp.yticklabels_var, title_fontsize=self.fpp.title_fontsize, tight=tight)
        return figure

    def plot_transition_levels(self, ax=None, tpp=None, tight=True):
        """ Plot the transition levels of the study """

        if tpp is None:
            tpp = TransitionPlotParameters(self)
            self.lasttpp = tpp
        ax, figure = pf.auto_ax(ax)

        e_fermi = np.linspace(tpp.energy_range[0], tpp.energy_range[1], 30000)  # range of fermi energies
        transition_levels = self.get_transition_levels(e_fermi)  # all transition levels in the range of fermi energies
        gap = self.gaps[tpp.gap_choice]

        # ------------------------------------------- FIGURE PARAMETERS -----------------------------------------------

        transition_figure_parameters(ax, tpp)
        ax.set_xlim(-0.01, 1.2)

        # -------------------------------------------- PLOT PARAMETERS ------------------------------------------------

        # vbm_energy and CBM
        ax.stackplot([0, 0, 1.1, 1.1], [[0, ax.get_ylim()[0] - 1, ax.get_ylim()[0] - 1, 0]], colors=['grey'], linewidths=4)
        ax.plot([0, 0, 1.1, 1.1], [ax.get_ylim()[1], gap, gap, ax.get_ylim()[1]], color='black', lw=4)

        ax.annotate(' $VBM$', xy=(1.1, 0.0), va='center', ha='left').draggable()
        ax.annotate(' $CBM$', xy=(1.1, gap), va='center', ha='left').draggable()

        # Transitions levels
        for transition in transition_levels:
            ax.plot([0.1, 1], [transition[0], transition[0]], lw=2, color='black')
            charges = sorted(list(set(np.concatenate([f[2:] for f in transition_levels]))), reverse=True)
            tr_fermi = [f[0] for f in transition_levels]
            for charge, tr in zip(charges, [tr_fermi[0] - 0.06] + list(tr_fermi[:-1] + np.diff(tr_fermi) / 2.0) + [tr_fermi[-1] + 0.06]):
                ax.annotate('$' + bf.float_to_str(charge) + '$', xy=(0.55, tr), va='center', ha='center').draggable()
        return figure

    def get_defects_concentration(self, e_fermi, temperature):

        k_b = 8.617e-5  # Boltzmann constant in eV/K
        e_for, charge = self.get_formation_energy_low_EF(e_fermi)
        if self.defects[0].nb_sites is None:
            raise bf.PyDEFInputError('Defect ' + self.defects[0].displayname + ' has no number of sites specified, please specify before computing concentrations!')
        return self.defects[0].nb_sites * np.exp(-e_for / (k_b * temperature)) / self.host_cell.volume

    def export(self, filename, separator):
        f = open(filename, mode='w')
        f.write('\n\n\n')
        f.write('DEFECT STUDY' + separator + self.treetitle + '\n')
        f.write('\nHOST CELL\n')
        f.write('Name ' + separator + ' %s \n' % self.host_cell.treetitle)
        f.write('Method ' + separator + ' %s \n' % self.host_cell.functional)
        f.write('Energy ' + separator + ' %.5f ' % self.host_cell.total_energy + separator + 'eV \n' )
        f.write('VBM energy ' + separator + ' %.5f ' % self.host_cell.vbm_energy + separator + 'eV \n')
        f.write('CBM energy ' + separator + ' %.5f ' % self.host_cell.cbm_energy + separator + 'eV \n')
        f.write('Gap ' + separator + ' %.5f ' % self.host_cell.gap + separator + 'eV \n')

        if self.host_cell != self.host_cell_b:
            f.write('\nHOST CELL B\n')
            f.write('Name ' + separator + ' %s \n' % self.host_cell_b.treetitle)
            f.write('Method ' + separator + ' %s \n' % self.host_cell_b.functional)
            f.write('VBM energy ' + separator + ' %.5f eV \n' % self.host_cell_b.vbm_energy)
            f.write('CBM energy ' + separator + ' %.5f eV \n' % self.host_cell_b.cbm_energy)
            f.write('Gap ' + separator + ' %.5f eV \n' % self.host_cell_b.gap)

            f.write('\nGAP CORRECTION\n')
        f.write('VBM correction' + separator + '%.5f' % self.de_vbm + separator + 'eV \n' )
        f.write('CBM correction' + separator + '%.5f' % self.de_cbm + separator + 'eV \n' )

        f.write('\nDEFECTS\n')
        f.write('Name' + separator + 'Type' + separator + 'atom(s)' + separator + 'coordinates' + separator + 'chemical potential(s) (eV)' + separator + 'number of affected atoms\n')
        for defect in self.defects:
            f.write(defect.ID + '' + separator + '' + defect.defect_type + '' + separator + '' + '&'.join(defect.atom) + '' + separator + '' +
                           str(defect.coord) + '' + separator + '' + str(defect.chem_pot) + '' + separator + '' + str(defect.n) + '\n')

        f.write('\nDEFECT CELLS\n')
        f.write('Name' + separator + 'Charge' + separator + 'Energy (eV)' + separator + 'VBM correction' + separator + 'PHS correction (holes)' + separator + 'PHS correction (electrons)'
                '' + separator + 'Potential alignment' + separator + 'Moss-Burstein correction (holes)' + separator + 'Moss-Burstein correction (electrons)'
                '' + separator + 'Makov-Payne correction' + separator + 'Total\n')
        for defcellstudy in self.dcs:
            f.write(defcellstudy.defect_cell.treetitle + '' + separator + '' + str(int(defcellstudy.defect_cell.charge)) +
                           '' + separator + ' %.5f' % defcellstudy.defect_cell.total_energy + '' + separator + ' %.5f' % defcellstudy.vbm_corr +
                           '' + separator + ' %.5f' % defcellstudy.phs_corr[0] + '' + separator + ' %.5f' % defcellstudy.phs_corr[1] + '' + separator + ' %.5f' % defcellstudy.pa_corr +
                           '' + separator + ' %.5f' % defcellstudy.mb_corr[0] + '' + separator + ' %.5f' % defcellstudy.mb_corr[1] + '' + separator + ' %.5f' % defcellstudy.mp_corr +
                           '' + separator + ' %.5f' % defcellstudy.tot_corr + '\n')

        f.write('\nCORRECTIONS PARAMETERS\n')
        f.write('Name' + separator + 'Nb of electrons' + separator + 'Spheres radius (A)\n')
        # for cell in self.defect_cell_studies.itervalues():
        for cell in self.dcs:
            f.write(cell.defect_cell.treetitle + '' + separator + '' + str(int(cell.defect_cell.nb_electrons)) +
                           '' + separator + ' %.5f' % cell.radius + '\n')

        f.write('\nTRANSITION LEVELS\n')
        for level in self.get_transition_levels(np.linspace(self.fpp.xmin, self.fpp.xmax, 100000)): # HERE!!!
            f.write('%.0f' % level[3] + '\%.0f' % level[2] + separator + '%.5f' % level[0] + separator + 'eV\n')

        f.close()
        
        print 'Material Study ' + self.treetitle + '\'s data exported successfully!'


class MaterialStudy(object):
    """ Object made of defect studies which enables to plot formation energies of many defects for a single compound """

    def __init__(self, *defect_studies):

        self.defect_studies = {}
        for defect_study in defect_studies:
            self.add_defect_study(defect_study)
        self.keys = [f.ID for f in defect_studies]
        self.ds = defect_studies[0]
        self.defect_concentrations = None

        # Title and ID
        self.title = self.ds.host_cell.display_rname
        self.treetitle = self.ds.host_cell.rname
        self.ID = self.ds.host_cell.rname

        # Plot parameters
        self.gaps = self.ds.gaps
        self.gap = self.ds.gap
        self.host_cell = self.ds.host_cell
        self.lastfpp = FormationPlotParameters(self)
        self.lasttpp = TransitionPlotParameters(self)
        self.cpp = ConcentrationPlotParameters(self)
        self.ccpp = CarrierConcentrationPlotParameters(self)
        self.eftpp = FermiLevelVariationsPlotParameters(self)

    @property
    def ds_list(self):
        temp = [[def_stud, def_stud.treetitle] for def_stud in self.defect_studies.values()]
        temp.sort(key=lambda x: x[1])
        return [def_stud for def_stud, title in temp]

    def add_defect_study(self, defect_study):

        object_id = bf.handle_same_string(defect_study.ID, self.defect_studies.keys())
        self.defect_studies[object_id] = defect_study

    def plot_formation_energy(self, ax=None, fpp=None, tight=True):
        """ Plot the formation energy of all defect studies """

        if fpp is None:
            fpp = FormationPlotParameters(self)
        ax, figure = pf.auto_ax(ax)

        e_fermi = np.linspace(fpp.xmin, np.max(self.gaps.values() + [fpp.xmax]), 10000)

        # -------------------------------------------------- PLOT ------------------------------------------------------

        e_for_lines = []  # list of lowest formation energy lines

        for ds in self.ds_list:
            color = fpp.colors[ds.ID]
            e_for_low, charges = np.transpose([ds.get_formation_energy_low_EF(f) for f in e_fermi])
            line = ax.plot(e_fermi, e_for_low, lw=3, label='$' + ds.defects_title.replace(' ', '\ ') + '$', c=color)
            e_for_lines.append(line[0])

            # Annotations
            indices = np.where(np.diff(charges) != 0)[0] + 1  # indices where the charge changes
            e_for_low_div = np.split(e_for_low, indices)
            e_fermi_div = np.split(e_fermi, indices)
            charges_div = np.split(charges, indices)

            # Add a dot where the charge changes
            if fpp.highlight_charge_change:
                for f, g in zip(e_fermi_div[1:], e_for_low_div[1:]):
                    ax.scatter(f[0], g[0], s=100, marker='o', color=color)

            # Display charge value
            if fpp.display_charges:
                labels = [bf.float_to_str(f[0]) for f in charges_div]
                for f, g, h in zip(e_fermi_div, e_for_low_div, labels):
                    annotation = ax.annotate('$' + h + '$', xy=(np.mean(f), np.mean(g)), va='center', ha='center',
                                             color=color, bbox=dict(boxstyle='square', fc='1', pad=0.05, color=color))
                    annotation.draggable()

        # Gaps
        gaps_colors = ('b', 'g', 'r', 'm', 'p')
        if fpp.display_gaps_legend:
            gaps_lines = [ax.axvline(f[1], label=f[0], lw=2, ls='--', color=g) for f, g in zip(self.gaps.items(), gaps_colors)]
        else:
            gaps_lines = [ax.axvline(f[1], lw=2, ls='--', color=g) for f, g in zip(self.gaps.items(), gaps_colors)]

        pf.set_ax_parameters(ax, title=fpp.title, xlabel=fpp.x_label, ylabel=fpp.y_label, xlim=[fpp.xmin, fpp.xmax], ylim=[fpp.ymin, fpp.ymax], legend=fpp.display_legends, grid=fpp.grid,
                             fontsize=fpp.fontsize, l_fontsize=fpp.l_fontsize, xticks=fpp.xticks_var, xtick_labels=fpp.xticklabels_var, yticks=fpp.yticks_var,
                             ytick_label=fpp.yticklabels_var, title_fontsize=fpp.title_fontsize, tight=tight)
        self.lastfpp = fpp
        ax.plot([fpp.xmin, fpp.xmax],[0,0], '--', lw=3,color='black')

        return figure

    def plot_transition_levels(self, ax=None, tpp=None, tight=True):
        """ Plot the transition levels of all defect studies """
        if tpp is None:
            tpp = TransitionPlotParameters(self)
        ax, figure = pf.auto_ax(ax)

        gap = self.gaps[tpp.gap_choice]
        e_fermi = np.linspace(tpp.energy_range[0], tpp.energy_range[1], 30000)

        transition_figure_parameters(ax, tpp)

        # -------------------------------------------- PLOT PARAMETERS ------------------------------------------------

        x_high = len(self.defect_studies)

        # Band extrema
        ax.stackplot([0, 0, x_high*1.1, x_high*1.1], [[0, ax.get_ylim()[0]-1, ax.get_ylim()[0]-1, 0]], colors=['grey'], linewidths=4)
        ax.plot([0, 0, x_high*1.1, x_high*1.1], [ax.get_ylim()[1], gap, gap, ax.get_ylim()[1]], color='black', lw=4)

        ax.annotate(' $VBM$', xy=(x_high * 1.1, 0.0), va='center', ha='left').draggable()
        ax.annotate(' $CBM$', xy=(x_high * 1.1, gap), va='center', ha='left').draggable()

        # Transition levels
        x_pos = np.linspace(0, x_high, x_high + 1) * 1.1
        for ds, x in zip(self.ds_list, x_pos):
            transitions = ds.get_transition_levels(e_fermi)

            for transition in transitions:
                ax.plot([x, x + 1], [transition[0], transition[0]], lw=2, color='black')
                charges = sorted(list(set(np.concatenate([f[2:] for f in transitions]))), reverse=True)
                tr_fermi = [f[0] for f in transitions]
                for charge, tr in zip(charges, [tr_fermi[0] - 0.06] + list(tr_fermi[:-1] + np.diff(tr_fermi)/2.0) + [tr_fermi[-1] + 0.06]):
                    ax.annotate('$' + bf.float_to_str(charge) + '$', xy=(x + 0.5, tr), va='center', ha='center').draggable()
                if tpp.display_formation_energy is True:
                    ax.annotate('%.2f eV' % transition[1], xy=(x + 0.5, transition[0]), va='center', ha='center', color='red')

        # Labels
        defect_labels = ['$' + f.defects_title + '$' for f in self.ds_list]
        xticks = np.linspace(0, x_high, x_high + 1) * 1.1 + 0.5
        ax.set_xticks(xticks, minor=False)
        ax.set_xticklabels(defect_labels)
        ax.tick_params(axis='x', which='major', length=0)

        ax.set_xlim(0, x_high * 1.1 * 1.1)

        return figure
            
    def summary(self):
        ds = self.ds_list
        summary = [[study.treetitle,
        defcellstudy.defect_cell.treetitle, 
        int(defcellstudy.defect_cell.charge),
        ' %.5f' % defcellstudy.defect_cell.total_energy,
        ' %.5f' % defcellstudy.vbm_corr,
        ' %.5f' % defcellstudy.pa_corr,
        ' %.5f' % defcellstudy.phs_corr[0],
        ' %.5f' % defcellstudy.phs_corr[1],
        ' %.5f' % defcellstudy.mp_corr,
        ' %.5f' % defcellstudy.mb_corr[0],
        ' %.5f' % defcellstudy.mb_corr[1],
        ' %.5f' % defcellstudy.tot_corr] for study in ds for defcellstudy in study.dcs]
        return [['Defect Study', 
        'Defect cell', 
        'q', 
        'Cell energy (eV)',
        'VBM corr (eV)', 
        'PA corr (eV)', 
        'PHS corr h (eV)', 
        'PHS corr e- (eV)',
        'MP corr (eV)',
        'MB corr h (eV)',
        'MB corr e (eV)',
        'Total corr (eV)']] + summary
        

class ConcentrationsCalculation(object):
    """ Class to calculate the defect and quasi-particles concentrations """

    def __init__(self, material_study):
        """
        :param material_study: MaterialStudy object"""

        self.m_e = material_study.cpp.m_e
        self.m_h = material_study.cpp.m_h
        
        self.material_study = material_study
        self.defect_studies = material_study.ds_list
        self.host_cell = material_study.host_cell
        self.gap = material_study.gap
        self.volume = self.host_cell.volume

        defect_ids = [d.ID for d in self.defect_studies]
        self.data_id = ['n (holes)', 'n (electrons)', 'E Fermi (growth)', 'E Fermi (room)'] + defect_ids

        defect_labels = [' & '.join([f.name for f in def_stud.defects]) for def_stud in self.defect_studies]
        self.labels = ['n_h', 'n_e', 'E_{Fermi} (growth)', 'E_{Fermi} (room)'] + defect_labels
        self.units =  ['cm^{-3}', 'cm^{-3}', 'eV', 'eV'] + len(defect_ids) * ['cm^{-3}']

        self.labels_dict = dict(zip(self.data_id, self.labels))
        self.units_dict = dict(zip(self.data_id, self.labels))

        # Theoretical DOS method
        if self.m_e is not None and self.m_h is not None :
           self.eval_energies_theoretical_dos()
        # Computed DOS method
        else:
            self.eval_energies_computed_dos()
            
    def eval_energies_theoretical_dos(self):
        e_max = 10.  # maximum energy (positive)
        e_min = -10.  # minimum energy (negative)
        self.de = 0.0001  # energy difference between 2 points

        self.energy = np.linspace(e_min, e_max + self.gap, int((e_max + self.gap - e_min) / self.de + 1))
        self.cb_energy = np.linspace(0, e_max, int(e_max / self.de + 1)) + self.gap
        self.vb_energy = np.linspace(e_min, 0, int(-e_min / self.de + 1))

        self.cb_dos = compute_dos(self.cb_energy - self.gap, self.m_e)
        self.vb_dos = compute_dos(self.vb_energy, self.m_h)
        
    def eval_energies_computed_dos(self):
        self.energy, self.dos = self.host_cell.dos_energy, self.host_cell.total_dos  # DOS and energy of the Host Cell
        self.de = np.mean(np.diff(self.energy))
        self.dos /= self.volume  # DOS per unit volume
        self.energy -= self.host_cell.fermi_energy  # set fermi energy at 0

        vb_indices = np.where(self.energy <= 0.0)[0]
        cb_indices = np.where(self.energy >= self.host_cell.gap)[0]

        self.vb_energy = self.energy[vb_indices]
        self.cb_energy = self.energy[cb_indices]
        self.cb_energy += self.gap - self.host_cell.gap  # shift the energy to the corrected CBM

        self.vb_dos = self.dos[vb_indices]  # DOS of the CB
        self.cb_dos = self.dos[cb_indices]  # DOS of the VB
    
    def set_masses(self, m_e, m_h):
        self.m_e = m_e
        self.m_h = m_h
        self.eval_energies_computed_dos()
    
    def export(self, filename, separator, pp):
        if filename is not None and filename != '':
            data = []
            if pp.growth:
                temperatures, data_dict = self.get_concentrations_temperature((pp.xmin, pp.xmax, pp.dt), pp.temperature)
                header = 'Growth Temperature (K)'
            else:
                temperatures, data_dict = self.get_concentrations_temperature(pp.temperature, (pp.xmin, pp.xmax, pp.dt))
                header = 'Ambiant Temperature (K)'

            for i in pp.data_id:
                y = data_dict[i]
                if type(pp) == CarrierConcentrationPlotParameters or type(pp) == ConcentrationPlotParameters:
                    y *= 1e-10
                header += separator + pp.data_id
                data.append(y)
            np.savetxt(filename, np.transpose(data), header, comments='', delimiter=separator)

    def get_qp_concentration_at_ef(self, e_fermi, temperature):
        """ Get the quasi-particles concentration at E_F """

        f_fd_e = fermi_dirac(self.cb_energy, e_fermi, temperature)
        f_fd_h = fermi_dirac(np.abs(self.vb_energy[::-1]), - e_fermi, temperature)[::-1]

        # Quasiparticles concentrations per m^3
        n_e = np.sum(self.cb_dos * f_fd_e * self.de)
        n_h = np.sum(self.vb_dos * f_fd_h * self.de)

        return n_h, n_e

    def get_defect_charge_at_ef(self, e_fermi, temperature):
        """ Get the the total charge of the defects at a given E_F and a given temperature """

        return np.sum([ds.get_formation_energy_low_EF(e_fermi)[1] * ds.get_defects_concentration(e_fermi, temperature)
                       for ds in self.defect_studies])

    def get_defect_concentration_at_ef(self, e_fermi, temperature):
        """ Get the defects concentrations as e_fermi and at a given temperature """

        return np.array([ds.get_defects_concentration(e_fermi, temperature) for ds in self.defect_studies])

    def get_neutrality(self, e_fermi, temperature, qn_defects=None):
        """ Calculate the neutrality of the system """

        n_h_growth, n_e_growth = self.get_qp_concentration_at_ef(e_fermi, temperature)  # qp per unit volume
        if qn_defects is None:
            qn_defects = self.get_defect_charge_at_ef(e_fermi, temperature)  # defect total charge per unit volume
        return - n_e_growth + n_h_growth + qn_defects

    def get_concentrations(self, t_growth, t_room):
        """ Compute the defect concentration at growth temperature """

        try:
            e_f_growth = sco.brentq(lambda e: self.get_neutrality(e, t_growth), 0., self.gap)
        except ValueError:
            error_message = 'Unable to find a root while solving neutrality of charge equation at growth temperature! '
            error_message += 'Consider specifying effective masses of carriers.'
            raise bf.PyDEFSolveError(error_message)
            return

        n_defects = self.get_defect_concentration_at_ef(e_f_growth, t_growth)
        qn_defects = self.get_defect_charge_at_ef(e_f_growth, t_growth)

        # At room temperature
        try:
            e_f_room = sco.brentq(lambda e: self.get_neutrality(e, t_room, qn_defects), 0., self.gap)
        except ValueError:
            error_message = 'Unable to find a root while solving neutrality of charge equation at room temperature! '
            error_message += 'Consider specifying effective masses of carriers.'
            raise bf.PyDEFSolveError(error_message)
            return

        # noinspection PyTypeChecker
        n_h, n_e = self.get_qp_concentration_at_ef(e_f_room, t_room)

        # return the concentrations in 1/(10^10 cm^3)
        return n_h/1e16, n_e/1e16, n_defects/1e16, e_f_growth, e_f_room, qn_defects

    def get_concentrations_temperature(self, t_growth, t_room):
        """ Get the defects concentrations for a range of growth temperature """

        if type(t_growth) is tuple:
            temperatures = np.arange(t_growth[0], t_growth[1] + t_growth[2], t_growth[2])
            temp = [self.get_concentrations(t, t_room) for t in temperatures]
        else:
            temperatures = np.arange(t_room[0], t_room[1] + t_room[2], t_room[2])
            temp = [self.get_concentrations(t_growth, t) for t in temperatures]

        data = map(list, zip(*temp))

        n_defects = np.transpose(data[2])
        del data[2]
        data = np.array(data)
        data = np.append(data, n_defects, axis=0)
        data_dict = dict(zip(self.data_id, data[:-1]))

        return temperatures, data_dict
        
    def plot(self, pp=None, ax=None, tight=True):
        
        if ax is None:
            ax, figure = pf.auto_ax()
            
        if pp is not None:
        
            print 'Computing concentrations... This may take some time... Please wait...'
            if pp.growth:
                temperatures, data_dict = self.get_concentrations_temperature((pp.xmin, pp.xmax, pp.dt), pp.temperature)
            else:
                temperatures, data_dict = self.get_concentrations_temperature(pp.temperature, (pp.xmin, pp.xmax, pp.dt))

            for i in pp.data_id:
                y = data_dict[i]
                if type(pp) == CarrierConcentrationPlotParameters or type(pp) == ConcentrationPlotParameters:
                    y *= 1e-10
                else:
                    # add CB and VB
                    cband = patches.Rectangle(
                            (pp.xmin, self.gap),   # (x,y)
                            pp.xmax - pp.xmin,    # width
                            1,                          # height
                            alpha = 0.5,
                            edgecolor = "blue",
                            facecolor = 'white', 
                            hatch ='/'
                        )
                    ax.add_patch(cband)
                    ax.text(pp.xmin + 0.5*(pp.xmax-pp.xmin), self.gap + (pp.ymax - self.gap)*0.5 , 'CB', fontsize=pp.fontsize)

                    vband = patches.Rectangle(
                            (pp.xmin, -1),   # (x,y)
                            pp.xmax - pp.xmin,    # width
                            1,                    # height
                            alpha = 0.5,
                            edgecolor = "red",
                            facecolor = 'white',
                            hatch ='/'
                        )
                    ax.add_patch(vband)
                    ax.text(pp.xmin + 0.5*(pp.xmax-pp.xmin), pp.ymin*0.5 , 'VB', fontsize=pp.fontsize)

                    ax.plot([pp.xmin, pp.xmax], [0.5*self.gap, 0.5*self.gap], '--', color = 'black', label = 'Middle \nof the band gap')
                    ax.plot([pp.xmin, pp.xmax], [0,0], '--', color = 'red', label = 'VBM', lw=4)
                    ax.plot([pp.xmin, pp.xmax], [self.gap, self.gap], '--', color = 'blue', label = 'CBM', lw=4)
                label = pf.convert_string_to_pymath(self.labels_dict[i])
                if type(pp) == FermiLevelVariationsPlotParameters:
                    ax.plot(temperatures, y, lw=3, label=label, color='black')
                else:
                    ax.plot(temperatures, y, lw=3, label=label, color=pp.colors[i])
            
            if type(pp) == ConcentrationPlotParameters and pp.fill_type:
                ne = data_dict['n (electrons)']
                nh = data_dict['n (holes)']
                ax.fill_between(temperatures, ne, nh, where= ne >= nh, facecolor=pp.colors['n type'], alpha=0.5, interpolate=True, label=r'$n_e > n_h$ ($n$ type)')
                ax.fill_between(temperatures, ne, nh, where= ne <= nh, facecolor=pp.colors['p type'], alpha=0.5, interpolate=True, label=r'$n_e < n_h$ ($p$ type)')
            
            pf.set_ax_parameters(ax, title=pp.title, xlabel=pp.x_label, ylabel=pp.y_label, xlim=[pp.xmin, pp.xmax], ylim=[pp.ymin, pp.ymax], legend=pp.display_legends, grid=pp.grid,
                                 fontsize=pp.fontsize, l_fontsize=pp.l_fontsize, xticks=pp.xticks_var, xtick_labels=pp.xticklabels_var, yticks=pp.yticks_var,
                                 ytick_label=pp.yticklabels_var, title_fontsize=pp.title_fontsize, ylog=pp.ylog, tight=False)
                   
            return figure


class FormationPlotParameters(pf.PlotParameters):
    """ Plot parameters for the formation levels """

    def __init__(self, study):
        """ :param study: Defect_Study or Material_Study object"""

        super(FormationPlotParameters, self).__init__()
        # Plot parameters
        self.xmin = 0
        self.xmax = max(study.gaps.values()) * 1.05  # Fermi energy range displayed
        if type(study) == DefectStudy:
            temp = [f.get_formation_energy_at_EF(ef) for ef in [self.xmin, self.xmax] for f in study.dcs]
            if len(temp)>0:
                self.ymin = min(temp)
                self.ymax = 1.05*max(temp)
                if len(study.defects)>1:
                    self.title = ' & '.join(['$' + d.name + '$' for d in study.defects]) + ' Formation Energy'
                else:
                    self.title = '$' + study.defects[0].name + '$ Formation Energy'
                self.name = self.title
        elif type(study) == MaterialStudy:
            # MATERIAL STUDIES
            self.highlight_charge_change = True  # if True, highlight charge change
            self.colors = dict(zip([defstud.ID for defstud in study.ds_list], ['red', 'yellowgreen', 'blue', 'orange', 'black', 'brown', 'darkgreen', 'navy', 'gold',
                                 'm', 'teal', 'darkmagenta']))
            self.display_gaps_legend = True
            self.ymin = 1.05*min([stud.fpp.ymin for stud in study.defect_studies.values()])
            self.ymax = 1.05*max([stud.fpp.ymax for stud in study.defect_studies.values()])
            self.title = 'Defect formation energies'
            self.name = 'Default Defect Formation Energies Plot Parameters'
        self.for_range = ['auto', 'auto']  # formation energy range displayed
        self.display_transition_levels = True  # if True, display the transitions levels
        self.display_charges = True  # if True, display the charges associated with the formation energy lines
        
        self.display_legends = True
        self.grid = True
        
        self.x_label = '$\Delta E (eV)$'
        self.y_label = '$E^{for}_q (eV)$'


class TransitionPlotParameters(pf.PlotParameters):
    """ Plot parameters for the transition level diagram """

    def __init__(self, study):

        super(TransitionPlotParameters, self).__init__()
        self.energy_range = [-0.5, max(study.gaps.values()) * 1.05]  # Fermi energy range
        self.gap_choice = 'Calculated gap'  # gap displayed
        self.title = r'$' + study.title + '$'

        # Only for Material_Study object
        self.display_formation_energy = True


class ConcentrationPlotParameters(pf.PlotParameters):

    def __init__(self, material_study):
        
        super(ConcentrationPlotParameters, self).__init__()
        self.m_e = None
        self.m_h = None
        self.xmin = 400.
        self.xmax = 1000.
        self.ymin = 1e-50
        self.ymax = 1e50
        self.dt = 50.
        self.data_id = [d.ID for d in material_study.ds_list] 
        self.fill_type = False
        self.charge_carriers = False
        self.growth = True
        self.ylog = True
        self.temperature = 300. # Room temperature (fixed)
        self.x_label = 'Growth temperature (K)'
        self.y_label = 'Concentrations $(cm^{-3})$'
        self.title = 'Defects Concentrations Variations with Growth Temperature'
        self.colors = material_study.lastfpp.colors 
        self.colors.update({'n (electrons)': 'red', 'n (holes)': 'blue', 'n type': 'red', 'p type': 'blue'})
    
    def display_charge_carriers(self):
        self.data_id += ['n (electrons)', 'n (holes)']
        
class FermiLevelVariationsPlotParameters(ConcentrationPlotParameters):

    def __init__(self, material_study):
        
        super(FermiLevelVariationsPlotParameters, self).__init__(material_study)
        self.xmin = 300.
        self.gap = material_study.gap
        self.ymin = -0.5
        self.ymax = self.gap*1.05 + 0.5 
        self.data_id = ['E Fermi (room)']
        self.growth = False
        self.ylog = False
        self.temperature = 500. # Growth temperature (fixed)
        self.x_label = 'Room temperature (K)'
        self.y_label = '$E_F (eV)$'
        self.title = 'Fermi Level Variations with Room Temperature $(T_{growth} = ' + str(self.temperature) + ' K)$'
        

class CarrierConcentrationPlotParameters(ConcentrationPlotParameters):

    def __init__(self, material_study):
        
        super(CarrierConcentrationPlotParameters, self).__init__(material_study)
        self.xmin = 300.
        self.data_id = ['n (electrons)', 'n (holes)']
        self.growth = False
        self.ylog = True
        self.temperature = 500. # Growth temperature (fixed)
        self.x_label = 'Room temperature (K)'
        self.y_label = 'Carrier concentrations $(cm^{-3})$'
        self.title = 'Carrier Concentrations Variations with Room Temperature $(T_{growth} = ' + str(self.temperature) + ' K)$'


def charges_annotation(e_fermi, e_for, charge, ax):
    """ Add an annotation giving the charge of the formation energy at the beginning of the line
    :param e_fermi: Fermi energy range
    :param e_for: defect formation energy for a given charge 'charge'
    :param charge: charge associated with the defect formation energy
    :param ax: matplotlib.axes object """

    if float(charge) > 0:
        index = np.where(np.abs(e_for - ax.get_ylim()[0]) < 5e-4)[0]
        if len(index) != 0:
            coordinates = (e_fermi[index[-1]], e_for[index[-1]])  # coordinates of the annotation
            hor_al = 'center'  # horizontal alignment of the annotation
            ver_al = 'bottom'  # vertical alignment of the annotation
        else:
            coordinates = (e_fermi[0] + 0.01 * e_fermi[-1], e_for[0] + float(charge) * 0.05 * e_fermi[-1])
            hor_al = 'left'
            ver_al = 'center'
    else:
        index = np.where(np.abs(e_for - ax.get_ylim()[1]) < 5e-4)[0]
        if len(index) != 0:
            coordinates = (e_fermi[index[0]], e_for[index[0]])
            hor_al = 'center'
            ver_al = 'top'

        else:
            coordinates = (e_fermi[0] + 0.01 * e_fermi[-1], e_for[0] + float(charge) * 0.05 * e_fermi[-1])
            hor_al = 'left'
            ver_al = 'center'

    annotation = ax.annotate('$q = %s$' % bf.float_to_str(charge), xy=coordinates,
                             bbox=dict(boxstyle='square', fc='1', pad=0.05), ha=hor_al, va=ver_al)
    annotation.draggable()


def transition_figure_parameters(ax, tpp):
    """ Figure parameters for Transition levels plots """

    ylabel = '$\Delta E_F$ (eV)'
    pf.set_ax_parameters(ax, tpp.title, '', ylabel, None, tpp.energy_range, False, False, False, fontsize=tpp.fontsize)

    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.yaxis.set_ticks_position('left')


def compute_dos(energy, m):
    """ Compute the density of states per unit volume
    :param energy: energy range (ndarray)
    :param m: effective mass (float) """

    m_e = 9.109e-31  # electron mass in kg
    planck = 1.055e-34  # reduced planck constant in J.s
    q_e = 1.602e-19  # electron charge
    dos = 1./(2. * np.pi**2) * (2. * m * m_e / planck**2)**1.5 * (np.abs(energy) * q_e)**0.5
    return dos * q_e  # in 1/(eV*m^3)


def fermi_dirac(energy, fermi_energy, temperature):
    """ Fermi-Dirac function """

    k_b = 8.617e-5  # Boltzman constant
    return 1./(1. + np.exp((energy - fermi_energy) / (k_b * temperature)))
