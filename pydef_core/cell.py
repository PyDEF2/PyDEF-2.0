""" Module used to import results of VASP calculations in PyVALENCE """

import numpy as np
import scipy.optimize as sco
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import re
import copy
import math

import pydef_core.basic_functions as bf
import pydef_core.figure as pf
import pydef_core.optical_indices as oi


class Cell(object):
    """ Object containing various data on a VASP calculation """

    def __init__(self, outcar_file, doscar_file=''):
        """ Read the OUTCAR and DOSCAR output files of a VASP calculation
        :param outcar_file: location of the OUTCAR file (string)
        :param doscar_file: location of the DOSCAR file (string) """

        print 'Starting import...'

        self.OUTCAR = outcar_file
        self.DOSCAR = doscar_file

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------- OUTCAR ---------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        self.outcar = bf.read_file(outcar_file)  # content of the OUTCAR file

        # Check that the OUTCAR file start with "vasp."
        if self.outcar[0][:6] != ' vasp.':
            raise bf.PyVALENCEOutcarError('The given file appears not to be a valid OUTCAR file.')

        # ---------------------------------------------- CALCULATION TAGS ----------------------------------------------

        self._functional, self.functional_title = get_functional(self.outcar)  # functional used
        self._nedos =  bf.grep(self.outcar, 'NEDOS =',  0, 'number of ions',  'int',   1)  # NEDOS
        self._encut =  bf.grep(self.outcar, 'ENCUT  =', 0, 'eV',              'float', 1)  # ENCUT
        self._ediff =  bf.grep(self.outcar, 'EDIFF  =', 0, 'stopping',        'float', 1)  # EDIFF
        self._emin =   bf.grep(self.outcar, 'EMIN   =', 0, ';',               'float', 1)  # EMIN
        self._emax =   bf.grep(self.outcar, 'EMAX   =', 0, 'energy-range',    'float', 1)  # EMAX
        self._ismear = bf.grep(self.outcar, 'ISMEAR =', 0, ';',               'int',   1)  # ISMEAR
        self._lorbit = int(bf.grep(self.outcar, 'LORBIT', 0, '0 simple, 1 ext', 'str',   1).split()[1])  # LORBIT
        self._isym =   bf.grep(self.outcar, 'ISYM   =', 0, '0-nonsym',        'int',   1)  # ISYM
        self._istart = bf.grep(self.outcar, 'ISTART =', 0, 'job',             'int',   1)  # ISTART
        self._ispin =  bf.grep(self.outcar, 'ISPIN  =', 0, 'spin',            'int',   1)  # ISPIN
        self._icharg = bf.grep(self.outcar, 'ICHARG =', 0, 'charge:',         'int',   1)  # ICHARG

        # --------------------------------------------- SYSTEM PROPERTIES ----------------------------------------------

        self._nb_atoms_tot = bf.grep(self.outcar, 'NIONS =', 0, False, 'int', 1)  # total number of atoms
        self._nb_atoms = bf.grep(self.outcar, 'ions per type =', 0, delimiter=None, data_type='int')
        self._atoms_types = get_atomic_species(self.outcar)  # chemical species
        self._population = dict(zip(self._atoms_types, self._nb_atoms))
        self._atoms_valence = bf.grep(self.outcar, 'ZVAL   =', -1, delimiter=None, data_type='int')  # valence
        self._atoms = np.concatenate([[f + ' (' + str(g) + ')' for g in range(1, q + 1)]
                                      for f, q in zip(self._atoms_types, self._nb_atoms)])  # atoms list
        self._nb_electrons = int(bf.grep(self.outcar, 'NELECT =', 0, 'total number', 'float', 1))  # number of electrons
        self._charge = sum(np.array(self._nb_atoms) * np.array(self._atoms_valence)) - self._nb_electrons  # charge
        self._orbitals = bf.grep(self.outcar, '# of ion', 0, 'tot', delimiter=None)

        # Check the consistence of the data retrieved
        if self._nb_atoms_tot != sum(self._nb_atoms) or \
                len(self._nb_atoms) != len(self._atoms_types) or \
                len(self._nb_atoms) != len(self._atoms_valence):
            raise bf.PyVALENCEImportError('Numbers of atoms retrieved are not consistent')

        self.name, self.display_name = get_system_name(self._atoms_types, self._nb_atoms, False)  # full name
        self.rname, self.display_rname = get_system_name(self._atoms_types, self._nb_atoms, True)  # reduced name

        # --------------------------------------------- CALCULATION RESULT ---------------------------------------------

        # Number of electronic steps
        if self._functional not in ['G0W0@GGA', 'GW0@GGA']:
            self._nb_iterations = len(bf.grep(self.outcar, 'Iteration'))  # for non GW calculations
        else:
            self._nb_iterations = bf.grep(self.outcar, 'NELM    =', 0, 'number', 'int', 1)  # for GW calculations

        # Crystallographic properties
        self._cell_parameters = get_cell_parameters(self.outcar)  # cristallographic parameters
        self._atoms_positions = get_atoms_positions(self.outcar, self._atoms)  # atoms positions
        self._volume = np.linalg.det(self._cell_parameters) * 1e-30  # volume in m^3

        # Energy & Density of states
        self._total_energy = bf.grep(self.outcar, 'free energy    TOTEN  =', -1, 'eV', 'float', self._nb_iterations)
        
        try:
            if self._ismear == 0:
                self._fermi_energy = bf.grep(self.outcar, 'E-fermi :', 0, 'XC(G=0)', 'float', nb_found=1)
                if self._fermi_energy == '':
                    self._fermi_energy = bf.grep(self.outcar, 'E-fermi :', 0, 'float', nb_found=1)
            else:
                self._fermi_energy = bf.grep(self.outcar, ' BZINTS: Fermi energy:', -1, ';', 'float')
        except ValueError:
            self._fermi_energy = None
        if self._fermi_energy is None:
            print 'Warning! I could not retrieve the Fermi level, sorry...'

        self._nkpts = bf.grep(self.outcar, 'NKPTS =', 0, 'k-points in BZ', 'int', 1)  # number of k-points
        self._kpoints_coords, self._kpoints_weights = get_kpoints_weights_and_coords(self.outcar, self._nkpts)
        self._kpoints_coords_r = get_kpoints_weights_and_coords(self.outcar, self._nkpts, True)[0]
        self._nbands = bf.grep(self.outcar, 'NBANDS=', 0, False, 'int', 1)  # number of bands
        
        try:
            self._bands_data = get_band_occupation(self.outcar, self._nkpts, self._functional)  # bands energy and occupation
            self._bands_energies, self._bands_positions, self._vbm_energy, self._cbm_energy, self._vb_energy, self._cb_energy, self.b_vbm, self.k_pts_vbm, self.b_cbm, self.k_pts_cbm, self.direct_band_gap = self.analyse_bands()
            self._gap = self._cbm_energy - self._vbm_energy  # electronic gap            
            
        except TypeError, e:
            print 'Warning! Could not retrieve bands data. This calculation may be a dielectric function calculation, or the file may be corrupted.'
            self._bands_data = None
            self._bands_energies = None
            self._bands_positions = None
            self._vbm_energy = None
            self._cbm_energy = None
            self._vb_energy = None 
            self._cb_energy = None
            self._gap = None

        # Electrostatic averaged potentials
        if self._functional not in ['G0W0@GGA', 'GW0@GGA']:
            self._potentials = get_electrostatic_potentials(self.outcar, self._atoms)
        else:
            self._potentials = None

        # --------------------------------------------------- OTHERS ---------------------------------------------------

        self.ID = self.name + '_' + self._functional + '_q%i' % self._charge
        self.title = '$' + self.display_rname + '$ ' + self.functional_title 
        if self._charge != 0:
            self.title += ' q=%i' % self._charge

        self.treetitle = self.rname
        if self._charge != 0:
            if self._charge > 0:
                self.treetitle += ' (q+'
            elif self._charge < 0:
                self.treetitle += ' (q'
            self.treetitle += '%i)' % self._charge
        
        self.optical_indices = None

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------- DOSCAR ---------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        if self.DOSCAR != '':
            doscar = bf.read_file(self.DOSCAR)  # content of the DOSCAR file

            self._dos_energy, self._total_dos, self._total_dos_up, self._total_dos_down, self._dos_opa, \
            self._dos_opa_up, self._dos_opa_down, self._dos_opas, self._dos_opas_up, self._dos_opas_down \
                = self.analyse_dos(doscar)

            # Maximum value of each DOS excluding the first value (sometimes too high)
            self.dosmax = np.max(self.total_dos[1:])
            if self.ispin == 2:
                self.dosmax_up = np.max(self.total_dos_up[1:])
                self.dosmax_down = np.max(self.total_dos_down[1:])
            self.lastdpp = DosPlotParameters(self)
            
        try:
            self.lastbpp = BandDiagramPlotParameters(self)
            self.bfp = BandFitPlotParameters(self)
            self.optical_indices = None 
        except TypeError:
            # if calculation is actually an optical indices calculation
            self.lastbpp = None
            self.bfp = None
            try:
                self.optical_indices = oi.OpticalIndices(self.outcar) 
            except TypeError:
                raise bf.PyVALENCEImportError('Sorry... Something went wrong... Could not complete import')
        self.gc = None # Geom Comparison
        

        print('\nImport of calculation ' + self.treetitle + ' finished successfully!\n')

    @property
    def functional(self):
        return self._functional

    @property
    def nedos(self):
        return self._nedos

    @property
    def encut(self):
        return self._encut

    @property
    def ediff(self):
        return self._ediff

    @property
    def emin(self):
        return self._emin

    @property
    def emax(self):
        return self._emax

    @property
    def ismear(self):
        return self._ismear

    @property
    def lorbit(self):
        return self._lorbit

    @property
    def isym(self):
        return self._isym

    @property
    def istart(self):
        return self._istart

    @property
    def ispin(self):
        return self._ispin

    @property
    def icharg(self):
        return self._icharg

    @property
    def nb_atoms_tot(self):
        return self._nb_atoms_tot

    @property
    def nb_atoms(self):
        return self._nb_atoms

    @property
    def atoms_types(self):
        return self._atoms_types

    @property
    def population(self):
        return self._population

    @property
    def atoms_valence(self):
        return self._atoms_valence

    @property
    def atoms(self):
        return self._atoms

    @property
    def nb_electrons(self):
        return self._nb_electrons

    @property
    def charge(self):
        return self._charge

    @property
    def orbitals(self):
        return self._orbitals

    @property
    def nb_iterations(self):
        return self._nb_iterations

    @property
    def cell_parameters(self):
        return copy.deepcopy(self._cell_parameters)

    @property
    def atoms_positions(self):
        return copy.deepcopy(self._atoms_positions)

    @property
    def total_energy(self):
        return self._total_energy

    @property
    def fermi_energy(self):
        return self._fermi_energy

    @property
    def nkpts(self):
        return self._nkpts

    @property
    def kpoints_coords(self):
        return self._kpoints_coords

    @property
    def kpoints_coords_r(self):
        """coordinates of kpoint in reciprocal space"""
        return self._kpoints_coords_r

    @property
    def nbands(self):
        return self._nbands

    @property
    def bands_data(self):
        return self._bands_data

    @property
    def vbm_energy(self):
        return self._vbm_energy

    @property
    def cbm_energy(self):
        return self._cbm_energy

    @property
    def gap(self):
        return self._gap

    @property
    def potentials(self):
        return copy.deepcopy(self._potentials)

    @property
    def dos_energy(self):
        return copy.deepcopy(self._dos_energy)

    @property
    def total_dos(self):
        return copy.deepcopy(self._total_dos)

    @property
    def total_dos_up(self):
        return copy.deepcopy(self._total_dos_up)

    @property
    def total_dos_down(self):
        return copy.deepcopy(self._total_dos_down)

    @property
    def dos_opa(self):
        return copy.deepcopy(self._dos_opa)

    @property
    def dos_opa_up(self):
        return copy.deepcopy(self._dos_opa_up)

    @property
    def dos_opa_down(self):
        return copy.deepcopy(self._dos_opa_down)

    @property
    def dos_opas(self):
        return copy.deepcopy(self._dos_opas)

    @property
    def dos_opas_up(self):
        return copy.deepcopy(self._dos_opas_up)

    @property
    def dos_opas_down(self):
        return copy.deepcopy(self._dos_opas_down)

    @property
    def kpoints_weights(self):
        return copy.deepcopy(self._kpoints_weights)

    @property
    def bands_energies(self):
        return copy.deepcopy(self._bands_energies)

    @property
    def bands_positions(self):
        return copy.deepcopy(self._bands_positions)

    @property
    def vb_energy(self):
        return copy.deepcopy(self._vb_energy)

    @property
    def cb_energy(self):
        return copy.deepcopy(self._cb_energy)

    @property
    def volume(self):
        return self._volume

    def analyse_dos(self, doscar_content):
        """ Read the DOSCAR file """

        # Check that the OUTCAR and DOSCAR files are consistent
        doscar_length = len(doscar_content)

        if self.lorbit == 11:
            expected_doscar_length = 6 + sum(self._nb_atoms) * (self._nedos + 1) + self._nedos
            if doscar_length != expected_doscar_length:
                print 'Warning! Found %i lines instead of %i as expected (%i atoms, NEDOS=%i)' % (doscar_length, expected_doscar_length, sum(self._nb_atoms), self._nedos)
                raise bf.PyVALENCEDoscarError('Analysing DoS... The DOSCAR file is not consistent with the OUTCAR file: '
                                     'length of DOSCAR content not as expected')
        else:
            expected_doscar_length = 6 + self.nedos  # Beware of the white line at the end of the file

        raw_data = doscar_content[6:]  # total and projected DOS

        # -------------------------------------------- ENERGY AND TOTAL DOS --------------------------------------------

        tot_dos_data = bf.fast_stringcolumn_to_array(raw_data[:self.nedos])

        if self.ispin == 2:
            energy, total_dos_up, total_dos_down = tot_dos_data[:3]  # Total DOS and energy
            total_dos = total_dos_up + total_dos_down
        else:
            energy, total_dos = tot_dos_data[:2]  # Total DOS and energy
            total_dos_up = None
            total_dos_down = None

        # ------------------------------------------ PROJECTED DOS PROCESSING ------------------------------------------

        if self.lorbit == 11:

            # Orbitals projected DOS
            dos_op_raw = raw_data[self.nedos:]

            # Remove useless lines from the projected DOS
            for i in range(sum(self._nb_atoms) - 1, -1, -1):
                del dos_op_raw[(self.nedos + 1) * i]

            # DOS projected on every orbitals (s, px, py, pz, dxx, ...)
            dos_op_xyz = bf.fast_stringcolumn_to_array(dos_op_raw)[1:]
            if self.ispin == 2:
                dos_op_up_xyz = dos_op_xyz[::2]
                dos_op_down_xyz = dos_op_xyz[1:][::2]
            else:
                dos_op_up_xyz = None
                dos_op_down_xyz = None

            # DOS projected on each main orbital (s, p, d...)
            orbitals_sizes = np.array([1, 3, 5, 7])
            orbitals_size = orbitals_sizes[:len(self.orbitals)]

            if self.ispin == 2:
                dos_op = [np.sum(f, axis=0) for f in bf.split_into_chunks(dos_op_xyz, orbitals_size*2)]
                dos_op_up = [np.sum(f, axis=0) for f in bf.split_into_chunks(dos_op_up_xyz, orbitals_size)]
                dos_op_down = [np.sum(f, axis=0) for f in bf.split_into_chunks(dos_op_down_xyz, orbitals_size)]
            else:
                dos_op = [np.sum(f, axis=0) for f in bf.split_into_chunks(dos_op_xyz, orbitals_size)]
                dos_op_up = None
                dos_op_down = None

            # DOS projected on every main orbital (s, p, d...) for each atom
            dos_opa = [np.transpose(f) for f in np.split(np.transpose(dos_op), self.nb_atoms_tot)]

            if self.ispin == 2:
                dos_opa_up = [np.transpose(f) for f in np.split(np.transpose(dos_op_up), self.nb_atoms_tot)]
                dos_opa_down = [np.transpose(f) for f in np.split(np.transpose(dos_op_down), self.nb_atoms_tot)]
            else:
                dos_opa_up = None
                dos_opa_down = None

            # Projected DOS on each atomic species
            dos_opas = [np.sum(f, axis=0) for f in bf.split_into_chunks(dos_opa, self.nb_atoms)]
            if self.ispin == 2.:
                dos_opas_up = [np.sum(f, axis=0) for f in bf.split_into_chunks(dos_opa_up, self.nb_atoms)]
                dos_opas_down = [np.sum(f, axis=0) for f in bf.split_into_chunks(dos_opa_down, self.nb_atoms)]
            else:
                dos_opas_up = None
                dos_opas_down = None

        else:
            dos_opa, dos_opa_up, dos_opa_down, dos_opas, dos_opas_up, dos_opas_down = None, None, None, None, None, None

        return energy, total_dos, total_dos_up, total_dos_down, dos_opa, dos_opa_up, dos_opa_down, \
               dos_opas, dos_opas_up, dos_opas_down

    def plot_dos(self, ax=None, dpp=None, tight=True):
        """ Plot the DOS
        :param ax: matplotlib ax object
        :param dpp: DosPlotParameters object """
        
        if dpp is None:
            dpp = DosPlotParameters(self)
        ax, figure = pf.auto_ax(ax)

        spin_cond = self.ispin == 2 and dpp.display_spin is True
        
        # --------------------------------------------------- ENERGY ---------------------------------------------------

        energy = self.dos_energy
        fermi_energy = self.fermi_energy
        cbm_energy = self.cbm_energy
        vbm_energy = self.vbm_energy

        if dpp.fermi_shift is True:
            shift = - fermi_energy - dpp.input_shift
        else:
            shift = - dpp.input_shift

        energy += shift
        if fermi_energy is not None:
            fermi_energy += shift
        cbm_energy += shift
        vbm_energy += shift

        # ----------------------------------------------- DOS PROCESSING -----------------------------------------------

        total_dos = self.total_dos
        total_dos_up = self.total_dos_up
        total_dos_down = self.total_dos_down

        if dpp.display_proj_dos and dpp.dos_type == 'OPAS':

            dos_opas = self.dos_opas
            dos_opas_up = self.dos_opas_up
            dos_opas_down = self.dos_opas_down

            p_labels = [np.concatenate([['$' + f + '\ ' + g + '$'] for g in self.orbitals]) for f in self.atoms_types]
            colors = copy.deepcopy(dpp.colors_proj)

            # Total projected DOS for each atomic species
            if dpp.tot_proj_dos is True:
                dos_opas = [np.sum(f, axis=0) for f in dos_opas]
                if spin_cond is True:
                    dos_opas_up = [np.sum(f, axis=0) for f in dos_opas_up]
                    dos_opas_down = [np.sum(f, axis=0) for f in dos_opas_down]

                p_labels = [['$' + f + '$'] for f in self.atoms_types]
                colors = copy.deepcopy(dpp.colors_tot)

            # Atomic species selection
            p_labels = np.concatenate(bf.choose_in(self.atoms_types, p_labels, dpp.choice_opas))
            p_dos = np.row_stack(bf.choose_in(self.atoms_types, dos_opas, dpp.choice_opas))
            if spin_cond is True:
                p_dos_up = np.row_stack(bf.choose_in(self.atoms_types, dos_opas_up, dpp.choice_opas))
                p_dos_down = np.row_stack(bf.choose_in(self.atoms_types, dos_opas_down, dpp.choice_opas))
            else:
                p_dos_up = None
                p_dos_down = None

        elif dpp.display_proj_dos and dpp.dos_type == 'OPA':

            dos_opa = self.dos_opa
            dos_opa_up = self.dos_opa_up
            dos_opa_down = self.dos_opa_down

            p_labels = [np.concatenate([['$' + f + '\ ' + g + '$'] for g in self.orbitals]) for f in self.atoms]
            colors = copy.deepcopy(dpp.colors_proj)

            # Total projected DOS on s, p, d orbitals for every atoms
            if dpp.tot_proj_dos is True:
                dos_opa = [np.sum(f, axis=0) for f in dos_opa]
                if spin_cond is True:
                    dos_opa_up = [np.sum(f, axis=0) for f in dos_opa_up]
                    dos_opa_down = [np.sum(f, axis=0) for f in dos_opa_down]

                p_labels = [['$' + f + '$'] for f in self.atoms]
                colors = copy.deepcopy(dpp.colors_tot)

            # Atoms selection
            p_labels = np.concatenate(bf.choose_in(self.atoms, p_labels, dpp.choice_opa))
            p_dos = np.row_stack(bf.choose_in(self.atoms, dos_opa, dpp.choice_opa))
            if spin_cond is True:
                p_dos_up = np.row_stack(bf.choose_in(self.atoms, dos_opa_up, dpp.choice_opa))
                p_dos_down = np.row_stack(bf.choose_in(self.atoms, dos_opa_down, dpp.choice_opa))
            else:
                p_dos_up = None
                p_dos_down = None

        else:
            p_dos = None
            p_dos_up = None
            p_dos_down = None
            colors = None
            p_labels = None
        
        # ---------------------------------------------------- PLOT ----------------------------------------------------

        
        if dpp.smooth:
            length = len(energy)
            if dpp.n_smooth %2 == 0:
                energy = energy[dpp.n_smooth/2:length-dpp.n_smooth/2+1]
            else:
                energy = energy[dpp.n_smooth/2:length-dpp.n_smooth/2]
        
        # Total DOS  
        if dpp.display_total_dos is True:
            if dpp.smooth:
                if dpp.normalize:
                    if spin_cond is True:
                        ax.plot(energy, bf.normalize_list(bf.moving_avg(total_dos_up, dpp.n_smooth)), color='black', label='Total DOS', lw=dpp.lw)
                        ax.plot(energy, -bf.normalize_list(bf.moving_avg(total_dos_down, dpp.n_smooth)), color='black', lw=dpp.lw)
                    else:
                        ax.plot(energy, bf.normalize_list(bf.moving_avg(total_dos, dpp.n_smooth)), color='black', label='Total DOS', lw=dpp.lw)
                else:
                    if spin_cond is True:
                        ax.plot(energy, bf.moving_avg(total_dos_up, dpp.n_smooth), color='black', label='Total DOS', lw=dpp.lw)
                        ax.plot(energy, bf.moving_avg(-total_dos_down, dpp.n_smooth), color='black', lw=dpp.lw)
                    else:
                        ax.plot(energy, bf.moving_avg(total_dos, dpp.n_smooth), color='black', label='Total DOS', lw=dpp.lw)
            else:
                if dpp.normalize:
                    if spin_cond is True:
                        ax.plot(energy, bf.normalize_list(total_dos_up), color='black', label='Total DOS', lw=dpp.lw)
                        ax.plot(energy, -bf.normalize_list(total_dos_down), color='black', lw=dpp.lw)
                    else:
                        ax.plot(energy, bf.normalize_list(total_dos), color='black', label='Total DOS', lw=dpp.lw)
                else:
                    if spin_cond is True:
                        ax.plot(energy, total_dos_up, color='black', label='Total DOS', lw=dpp.lw)
                        ax.plot(energy, -total_dos_down, color='black', lw=dpp.lw)
                    else:
                        ax.plot(energy, total_dos, color='black', label='Total DOS', lw=dpp.lw)
            
        # Projected DOS
        if dpp.display_proj_dos is True:
            if dpp.smooth:
                if dpp.normalize:
                    if dpp.plot_areas is True:
                        if spin_cond is True:
                            ax.stackplot(energy, bf.normalize_list(bf.moving_avg(p_dos_up, dpp.n_smooth)), colors=colors, lw=0, labels=p_labels)
                            ax.stackplot(energy, -bf.normalize_list(bf.moving_avg(p_dos_down, dpp.n_smooth)), colors=colors, lw=0)
                        else:
                            ax.stackplot(energy, bf.moving_avg(p_dos, dpp.n_smooth), colors=colors, lw=0, labels=p_labels)
                    else:
                        if spin_cond is True:
                            [ax.plot(energy, bf.normalize_list(bf.moving_avg(f, dpp.n_smooth)), c=g, label=h, lw=dpp.lw) for f, g, h in zip(p_dos_up, colors, p_labels) if not bf.is_zero(f)]
                            [ax.plot(energy, -bf.normalize_list(bf.moving_avg(f, dpp.n_smooth)), c=g, lw=dpp.lw) for f, g in zip(p_dos_down, colors) if not bf.is_zero(f)]
                        else:
                            [ax.plot(energy, bf.normalize_list(bf.moving_avg(f, dpp.n_smooth)), c=g, label=h, lw=dpp.lw) for f, g, h in zip(p_dos, colors, p_labels) if not bf.is_zero(f)]
                else:
                    # smoothed and not normalized
                    if dpp.plot_areas is True:
                        if spin_cond is True:
                            [ax.stackplot(energy, bf.moving_avg(f, dpp.n_smooth), color=g, labels=h) for f, g, h in zip(p_dos_up, colors, p_labels) if not bf.is_zero(f)]
                            [ax.stackplot(energy, bf.moving_avg(-f, dpp.n_smooth), color=g) for f, g, h in zip(p_dos_down, colors, p_labels) if not bf.is_zero(f)]
                        else:
                            [ax.stackplot(energy, bf.moving_avg(f, dpp.n_smooth), color=g, lw=0) for f, g, h in zip(p_dos, colors, p_labels) if not bf.is_zero(f)]
                    else:
                        if spin_cond is True:
                            print p_labels
                            [ax.plot(energy, bf.moving_avg(f, dpp.n_smooth), c=g, label=h, lw=dpp.lw) for f, g, h in zip(p_dos_up, colors, p_labels) if not bf.is_zero(f)]
                            [ax.plot(energy, bf.moving_avg(-f, dpp.n_smooth), c=g, lw=dpp.lw) for f, g in zip(p_dos_down, colors) if not bf.is_zero(f)]
                        else:
                            [ax.plot(energy, bf.moving_avg(f, dpp.n_smooth), c=g, label=h, lw=dpp.lw) for f, g, h in zip(p_dos, colors, p_labels) if not bf.is_zero(f)]

            else:
                # not smoothed
                if dpp.normalize:
                    # not smoothed and normalized
                    if dpp.plot_areas is True:
                        if spin_cond is True:
                            [ax.stackplot(energy, bf.normalize_list(f), color=g, labels=h, lw=dpp.lw) for f, g, h in zip(p_dos_up, colors, p_labels) if not bf.is_zero(f)]
                            [ax.stackplot(energy, -bf.normalize_list(f), color=g, lw=dpp.lw) for f, g in zip(p_dos_down, colors) if not bf.is_zero(f)]
                        else:
                            ax.stackplot(energy, bf.normalize_list(p_dos), colors=colors, lw=0, labels=p_labels)
                    else:
                        # not smoothed, normalized, lines
                        if spin_cond is True:
                            [ax.plot(energy, bf.normalize_list(f), color=g, label=h, lw=dpp.lw) for f, g, h in zip(p_dos_up, colors, p_labels) if not bf.is_zero(f)]
                            [ax.plot(energy, -bf.normalize_list(f), color=g, lw=dpp.lw) for f, g in zip(p_dos_down, colors) if not bf.is_zero(f)]
                        else:
                            [ax.plot(energy, bf.normalize_list(f), color=g, label=h, lw=dpp.lw) for f, g, h in zip(p_dos, colors, p_labels) if not bf.is_zero(f)]
                else:
                    # not smoothed not normalized
                    if dpp.plot_areas is True:
                        if spin_cond is True:
                            [ax.stackplot(energy, f, color=g, labels=h, lw=dpp.lw) for f, g, h in zip(p_dos_up, colors, p_labels) if not bf.is_zero(f)]
                            [ax.stackplot(energy, f, color=g, lw=dpp.lw) for f, g in zip(p_dos_down, colors) if not bf.is_zero(f)]
                        else:
                            ax.stackplot(energy, p_dos, colors=colors, lw=0, labels=p_labels)
                    else:
                        if spin_cond is True:
                            [ax.plot(energy, f, c=g, label=h, lw=dpp.lw) for f, g, h in zip(p_dos_up, colors, p_labels) if not bf.is_zero(f)]
                            [ax.plot(energy, -f, c=g, lw=dpp.lw) for f, g in zip(p_dos_down, colors) if not bf.is_zero(f)]
                        else:
                            [ax.plot(energy, f, c=g, label=h, lw=dpp.lw) for f, g, h in zip(p_dos, colors, p_labels) if not bf.is_zero(f)]

        # ------------------------------------------------ ANNOTATIONS -------------------------------------------------

        # Display energy levels
        if dpp.display_BM_levels:
            ax.axvline(cbm_energy, ls='--', color='blue')
            ax.annotate('$E_C$', xy=(cbm_energy, 0.75), color='blue', xycoords=('data', 'axes fraction')).draggable()
            ax.axvline(vbm_energy, ls='--', color='red')
            ax.annotate('$E_V$', xy=(vbm_energy, 0.75), color='red', xycoords=('data', 'axes fraction')).draggable()

        # Display fermi level
        if dpp.display_Fermi_level:
            if fermi_energy is not None:
                ax.axvline(fermi_energy, ls='--', color='black')
                ax.annotate('$E_F$', xy=(fermi_energy, 0.75), color='black', xycoords=('data', 'axes fraction')).draggable()
            else:
                print 'Warning! I could not retrieve the Fermi Energy, sorry...'

        if spin_cond:
            ax.pydef_anot = self.annotate_dos(ax)

            def update_annot():
                pf.delete_annotations(*ax.pydef_anot)
                ax.pydef_anot = self.annotate_dos(ax)

            ax.callbacks.connect('ylim_changed', lambda x: update_annot())

        # ---------------------------------------------- PLOT PARAMETERS -----------------------------------------------

        if dpp.fermi_shift is True:
            xlabel = '$E - E_F$ (eV)'
        else:
            xlabel = 'E (eV)'

        ylabel = 'DOS (states/eV)'
        
        ax.axhline(color='black')

        pf.set_ax_parameters(ax, title=dpp.title, xlabel=dpp.x_label, ylabel=dpp.y_label, xlim=[dpp.xmin, dpp.xmax], ylim=[dpp.ymin, dpp.ymax], legend=dpp.display_legends, grid=dpp.grid,
                             fontsize=dpp.fontsize, l_fontsize=dpp.l_fontsize, xticks=dpp.xticks_var, xtick_labels=dpp.xticklabels_var, yticks=dpp.yticks_var,
                             ytick_label=dpp.yticklabels_var, title_fontsize=dpp.title_fontsize, tight=tight)
        
        if dpp.plot_areas and dpp.display_legends is True and dpp.display_proj_dos is True:
            # stackplot does not support math mode in legend
            ax.get_legend().remove()
            rectangles = [Rectangle((0, 0), 1, 1, fc=c) for c in colors]
            if dpp.display_total_dos is True:
                rectangles = [Line2D([0], [0], color='black', lw=4)] + rectangles
                p_labels = ['Total DoS'] + [str(h) for h in p_labels]
            ax.legend(fontsize=dpp.l_fontsize)
            ax.legend(rectangles, p_labels, fontsize=dpp.l_fontsize).draggable()
            

        # store dpp for next plot
        self.lastdpp = dpp
        
        return figure

    @staticmethod
    def annotate_dos(ax):
        """ Annotate the plot """

        ylim = ax.get_ylim()

        """if ylim[0] < 0 < ylim[1]:
            xline = ax.annotate('', xy=(1, 0), xytext=(0, 0), arrowprops=dict(facecolor='k', width=0.5),
                                xycoords=('axes fraction', 'data'), textcoords=('axes fraction', 'data'))
        else:
            xline = None"""

        if ylim[1] > 0.:
            anot_up = ax.annotate('Spin up', xy=(0, 1.04), xycoords='axes fraction', ha='center', va='center')
            anot_up.draggable()
        else:
            line_up, anot_up = None, None

        if ylim[0] < 0.:
            anot_down = ax.annotate('Spin down', xy=(0, -0.06), xycoords='axes fraction', ha='center', va='center')
            anot_down.draggable()
        else:
            line_down, anot_down = None, None

        return anot_up, anot_down

    def analyse_bands(self):
        """ Analyse the band energies and positions """

        bands_data = self.bands_data
        band_energies = np.transpose([f[0] for f in bands_data])  # energies of each band at each kpoint

        # Extrema
        vbm_indices = [np.where(f[1] > 0.001)[0][-1] for f in bands_data]  # index of the maximum energy of the occupied bands at each k-point
        vbm_energy = float(max([f[0, i] for f, i in zip(bands_data, vbm_indices)])) # Valence Band Maximum (eV)
        b_vbm =  [i for f, i in zip(bands_data, vbm_indices) if f[0, i] == vbm_energy] # band indices where VBM is reached
        k_pts_vbm = np.where(bands_data[bn][i] == max(bands_data[bn]) for bn in b_vbm for i in range(0, len(bands_data[b_vbm])))[0] # k point indices where VBM is reached
        
        cbm_indices = [np.where(f[1] < 0.001)[0][0] for f in bands_data]  # index of the minimum energy of the unoccupied bands at each k-point
        cbm_energy = float(min([f[0, i] for f, i in zip(bands_data, cbm_indices)])) # Conduction Band Minimum (eV)
        b_cbm =  [i for f, i in zip(bands_data, cbm_indices) if f[0, i] == cbm_energy] # band indices where CBM is reached
        k_pts_cbm = np.where(bands_data[bn][i] == min(bands_data[bn]) for bn in b_cbm for i in range(0, len(bands_data[b_cbm])))[0] # k point indices where CBM is reached
        
        direct_band_gap = True
        for i in range(0, min(len(k_pts_cbm),len(k_pts_vbm))):
            direct_band_gap = (direct_band_gap and k_pts_vbm[i]==k_pts_cbm[i])
        
        # Bands
        vb_energy = band_energies[max(b_vbm)]
        cb_energy = band_energies[min(b_cbm)]

        # K points
        x_values_temp = [bf.distance(f, g) for f, g in zip(self.kpoints_coords_r[:-1], self.kpoints_coords_r[1:])]
        positions = np.cumsum([0] + x_values_temp)
        if self.ispin == 2:
            positions = np.append(positions, positions)

        return band_energies, positions, vbm_energy, cbm_energy, vb_energy, cb_energy, b_vbm, k_pts_vbm, b_cbm, k_pts_cbm, direct_band_gap

    def export_bands(self, filename, separator):
        """ Export the position and energies of the bands to a file """

        energies = self.bands_energies
        positions = self.bands_positions
        header = 'Positions' + separator + separator.join(['Band %s' % f for f in range(1, len(energies) + 1)])
        data = np.transpose(np.insert(energies, 0, positions, axis=0))
        np.savetxt(filename, data, header=header, delimiter=separator, comments='')
        print self.treetitle + ' Bands exported successfully!'
    
    def export_dos(self, filename, separator):
        """Export the DoS"""
        
        spin_cond = self.ispin == 2 and dpp.display_spin is True
        
        energy = self.dos_energy
        fermi_energy = self.fermi_energy
        cbm_energy = self.cbm_energy
        vbm_energy = self.vbm_energy
        dpp = self.lastdpp

        if dpp.fermi_shift is True:
            if fermi_energy is not None:
                shift = - fermi_energy - dpp.input_shift
            else:
                shift = - dpp.input_shift
                print 'Warning! I could not retrieve Fermi energy, sorry...'
        else:
            shift = - dpp.input_shift

        energy += shift

        # ----------------------------------------------- DOS PROCESSING -----------------------------------------------

        total_dos = self.total_dos
        total_dos_up = self.total_dos_up
        total_dos_down = self.total_dos_down

        if dpp.dos_type == 'OPAS':

            dos_opas = self.dos_opas
            dos_opas_up = self.dos_opas_up
            dos_opas_down = self.dos_opas_down

            p_labels = [np.concatenate([['$' + f + '\ ' + g + '$'] for g in self.orbitals]) for f in self.atoms_types]

            # Total projected DOS for each atomic species
            if dpp.tot_proj_dos is True:
                dos_opas = [np.sum(f, axis=0) for f in dos_opas]
                if spin_cond is True:
                    dos_opas_up = [np.sum(f, axis=0) for f in dos_opas_up]
                    dos_opas_down = [np.sum(f, axis=0) for f in dos_opas_down]

                p_labels = [['$' + f + '$'] for f in self.atoms_types]

            # Atomic species selection
            p_labels = np.concatenate(bf.choose_in(self.atoms_types, p_labels, dpp.choice_opas))
            p_dos = np.row_stack(bf.choose_in(self.atoms_types, dos_opas, dpp.choice_opas))
            if spin_cond is True:
                p_dos_up = np.row_stack(bf.choose_in(self.atoms_types, dos_opas_up, dpp.choice_opas))
                p_dos_down = np.row_stack(bf.choose_in(self.atoms_types, dos_opas_down, dpp.choice_opas))
            else:
                p_dos_up = None
                p_dos_down = None

        elif dpp.dos_type == 'OPA':

            dos_opa = self.dos_opa
            dos_opa_up = self.dos_opa_up
            dos_opa_down = self.dos_opa_down

            p_labels = [np.concatenate([['$' + f + '\ ' + g + '$'] for g in self.orbitals]) for f in self.atoms]

            # Total projected DOS on s, p, d orbitals for every atoms
            if dpp.tot_proj_dos is True:
                dos_opa = [np.sum(f, axis=0) for f in dos_opa]
                if spin_cond is True:
                    dos_opa_up = [np.sum(f, axis=0) for f in dos_opa_up]
                    dos_opa_down = [np.sum(f, axis=0) for f in dos_opa_down]

                p_labels = [['$' + f + '$'] for f in self.atoms]

            # Atoms selection
            p_labels = np.concatenate(bf.choose_in(self.atoms, p_labels, dpp.choice_opa))
            p_dos = np.row_stack(bf.choose_in(self.atoms, dos_opa, dpp.choice_opa))
            if spin_cond is True:
                p_dos_up = np.row_stack(bf.choose_in(self.atoms, dos_opa_up, dpp.choice_opa))
                p_dos_down = np.row_stack(bf.choose_in(self.atoms, dos_opa_down, dpp.choice_opa))
            else:
                p_dos_up = None
                p_dos_down = None

        else:
            p_dos = None
            p_dos_up = None
            p_dos_down = None
            p_labels = None

        # ---------------------------------------------------- PLOT ----------------------------------------------------

        data = [energy]
        header = 'Energy (eV)'
        # Total DOS
        if spin_cond is True:
            data.append(total_dos_up)
            header += separator + ' Total DoS (up)'
            data.append(-total_dos_down)
            header += separator + ' Total DoS (down)'
        else:
            data.append(total_dos)
            header += separator + ' Total DoS'

        # Projected DOS
        if dpp.display_proj_dos is True:
            if spin_cond is True:
                for proj_dos, p_dos_name in zip(p_dos_up, p_labels):
                    header += separator + p_dos_name.replace('$','') + '(up)'
                    data.append(proj_dos)
                for proj_dos, p_dos_name in zip(p_dos_down, p_labels):
                    header += separator + p_dos_name.replace('$','') + '(down)'
                    data.append(proj_dos)
            else:
                for proj_dos, p_dos_name in zip(p_dos, p_labels):
                    header += separator + p_dos_name.replace('$','') 
                    data.append(proj_dos)
        
        data = np.transpose(data)
        np.savetxt(filename, data, header=header, delimiter=separator, comments='')
        print self.treetitle + ' Density of states exported successfully!'


    def plot_band_diagram(self, ax=None, bpp=None, tight=True):
        """ Plot the band diagram """
        if bpp is None:
            bpp = BandDiagramPlotParameters(self)

        ax, figure = pf.auto_ax(ax)
        
        # energies
        if self.functional in ['HSE', 'PBE0', 'Hybrid']:
            if bpp.nkpts_hybrid_bands == 0:
                temp_list = zip(self.kpoints_coords, self.kpoints_weights, range(0,len(self.kpoints_coords)))
                bands_kpoints = [coords for (coords, w, index) in temp_list if w == 0]
                indices = [index for (coords, w, index) in temp_list if w == 0]
                if len(indices) > 0:
                    energies = self.bands_energies[:,indices[0]:indices[-1]+1]
                    print '%i k-points used in Band Structure Calculation' %len(indices)
                else:
                    bands_kpoints = self.kpoints_coords
                    energies = self.bands_energies
            else:
                bands_kpoints = self.kpoints_coords[-bpp.nkpts_hybrid_bands:]
                energies = self.bands_energies[:,-bpp.nkpts_hybrid_bands:]
        else: 
            energies = self.bands_energies
        
        vbm_index = self.nb_electrons/2 - 1    
        vbm_energy = self.vbm_energy
        
        if bpp.vbm_shift is True or bpp.highlight_vbm_cbm is True:
            vbm_band_energy = energies[vbm_index]  # energy of the VBM band
            cbm_band_energy = energies[vbm_index+1]  # energy of the CBM band
            if bpp.vbm_shift is True:
                shift = self.vbm_energy
                energies -= vbm_energy
                vbm_energy -= vbm_energy
        else:
            shift = 0
            
        # positions    
        if bpp.discontinuities:
            nkpts = len(self.kpoints_coords)
            nb_seg_end = nkpts/bpp.nkpts_per_seg
            seg_extr_pos = [0]
            positions = []
            for i in range(1, nb_seg_end+1):
                if i*bpp.nkpts_per_seg < nkpts and sum(self.kpoints_coords[i*bpp.nkpts_per_seg-1] - self.kpoints_coords[i*bpp.nkpts_per_seg]) == 0:
                    seg_extr_pos.append(seg_extr_pos[i-1] + bf.distance(self.kpoints_coords[(i-1)*bpp.nkpts_per_seg], self.kpoints_coords[i*bpp.nkpts_per_seg]))
                elif i*bpp.nkpts_per_seg == nkpts:
                    seg_extr_pos.append(seg_extr_pos[i-1] + bf.distance(self.kpoints_coords[(i-1)*bpp.nkpts_per_seg], self.kpoints_coords[nkpts-1]))
                else:
                    # discontinuity
                    seg_extr_pos.append(seg_extr_pos[i-1] + 
                    bf.distance(self.kpoints_coords[(i-1)*bpp.nkpts_per_seg+1], self.kpoints_coords[i*bpp.nkpts_per_seg]))
            for i in range(1, nb_seg_end+1):
                for energy in energies[:,(i-1)*bpp.nkpts_per_seg:i*bpp.nkpts_per_seg]:
                    if seg_extr_pos[i-1] < seg_extr_pos[i]:
                        seg_pos = np.arange(seg_extr_pos[i-1], seg_extr_pos[i], (seg_extr_pos[i]-seg_extr_pos[i-1])/bpp.nkpts_per_seg)
                        
                        
                        if len(seg_pos) == len(energy):
                            ax.plot(seg_pos, energy, lw=3, c='k')
                        positions = positions + list(seg_pos)
            positions = np.array(positions)
            bpp.xmax = max(positions)
        else:
            if self.functional in ['HSE', 'PBE0', 'Hybrid']:
                x_values_temp = [bf.distance(f, g) for f, g in zip(bands_kpoints[:-1], bands_kpoints[1:])]
                positions = np.cumsum([0] + x_values_temp)
                if self.ispin == 2:
                    positions = np.append(positions, positions)
            else:
                positions = self.bands_positions
        
        # ---------------------------------------------------- PLOT ----------------------------------------------------
        
        if not bpp.discontinuities:
            if bpp.colors is True:
                colored_bands = range(vbm_index-3, vbm_index + 4)
                colors = ['green', 'goldenrod', 'orange', 'red', 'blue', 'purple', 'turquoise']
                k = 0
                for energy in energies:
                    k += 1
                    if k in colored_bands:
                        ax.plot(positions, energy, c=colors[k-vbm_index+3], lw=3)
            else:
                for energy in energies:
                    ax.plot(positions, energy, c='k', lw=3) 

        if bpp.highlight_vbm_cbm is True:
            if bpp.discontinuities is True:
                for i in range(1, nb_seg_end+1):
                    if seg_extr_pos[i-1] < seg_extr_pos[i]:
                        seg_pos = np.arange(seg_extr_pos[i-1], seg_extr_pos[i], (seg_extr_pos[i]-seg_extr_pos[i-1])/bpp.nkpts_per_seg)
                        
                        ax.plot(seg_pos, energies[self.b_cbm[0],(i-1)*bpp.nkpts_per_seg:i*bpp.nkpts_per_seg], color='blue', label='CBM', lw=4)
                        ax.plot(seg_pos, energies[vbm_index,(i-1)*bpp.nkpts_per_seg:i*bpp.nkpts_per_seg], color='red', label='VBM', lw=4)
                    else:
                        ax.plot(positions, energies[elf.b_cbm, (i-1)*bpp.nkpts_per_seg:i*bpp.nkpts_per_seg], color = 'blue', label='CBM', lw=4)
                        ax.plot(positions, energies[vbm_index, (i-1)*bpp.nkpts_per_seg:i*bpp.nkpts_per_seg], color = 'red', label='VBM', lw=4)
            else:
                ax.plot(positions, energies[vbm_index], c='red', label='VBM', lw=3)
                ax.plot(positions, energies[vbm_index+1], c='blue', label='CBM', lw=3)
                
            ax.legend()
        
        if bpp.colors is True and bpp.discontinuities is True:
                colored_bands = range(vbm_index-3, vbm_index + 4)
                colors = ['green', 'goldenrod', 'orange', 'red', 'blue', 'purple', 'turquoise']
                for k in range(0, len(colored_bands)): 
                    for i in range(1, nb_seg_end+1):
                        if seg_extr_pos[i-1] < seg_extr_pos[i]:
                            seg_pos = np.arange(seg_extr_pos[i-1], seg_extr_pos[i], (seg_extr_pos[i]-seg_extr_pos[i-1])/bpp.nkpts_per_seg)
                            ax.plot(seg_pos, self.bands_energies[colored_bands[k],(i-1)*bpp.nkpts_per_seg:i*bpp.nkpts_per_seg] - shift, color=colors[k], lw=4)
                        else:
                            ax.plot(positions, self.bands_energies[colored_bands[k], (i-1)*bpp.nkpts_per_seg:i*bpp.nkpts_per_seg] - shift, color=colors[k], lw=4)
            
        if bpp.highlight_zero_line  is True:
            ax.axhline(0, ls='--', color='black')

        # ---------------------------------------------- PLOT PARAMETERS -----------------------------------------------

        pf.set_ax_parameters(ax, title=bpp.title, xlabel=bpp.x_label, ylabel=bpp.y_label, xlim=[bpp.xmin, bpp.xmax], ylim=[bpp.ymin ,bpp.ymax], legend=bpp.display_legends, grid=bpp.grid,
                            fontsize=bpp.fontsize, l_fontsize=bpp.l_fontsize, xticks=bpp.xticks_var, xtick_labels=bpp.xticklabels_var, yticks=bpp.yticks_var,
                            ytick_label=bpp.yticklabels_var, title_fontsize=bpp.title_fontsize, tight=tight, box=True)
        
        if bpp.hs_kpoints_names != ['']:
            nb_hs_kpoints = len(bpp.hs_kpoints_names)
            try:
                print 'test'
                ax.set_xticks([f[0] for f in np.split(positions, nb_hs_kpoints-1)] + [positions[-1]])
                ax.set_xticklabels(['$' + f + '$' for f in bpp.hs_kpoints_names])
                for x in [f[0] for f in np.split(positions, nb_hs_kpoints-1)][1:]:
                    ax.axvline(x, linestyle='--', lw=2, color='black')
            except ValueError:
                print 'Warning! ' + str(len(positions)) + ' k-points, cannot be split into ' + str(nb_hs_kpoints-1) + ' segments of equal length'
        return figure
    
    def fit_bands(self):
        figure = plt.figure()
        ax = figure.add_subplot(211)
        figure = self.plot_band_diagram(ax=ax, bpp=self.bfp)
        
        ax1 = figure.add_subplot(223)
        ax2 = figure.add_subplot(224)
        self.fit_band(self.bfp.bands_fit['CBM'], ax_main=ax, ax_sec=ax1)         
        self.fit_band(self.bfp.bands_fit['VBM'], ax_main=ax, ax_sec=ax2)
        figure.subplots_adjust(hspace=10./self.bfp.fontsize)         
        
        return figure

    def fit_band(self, bfp, ax_main=None, ax_sec=None):

        ax, figure = pf.auto_ax(ax_main)
        
        if bfp.xfitmin is not None and bfp.xfitmax is not None:
            print '\n\nStarting fitting ' + bfp.band_fit + ' between ' + str(bfp.xfitmin) + ' and ' + str(bfp.xfitmax) + '...'
            fit_region = [p for p in self.bands_positions if p >= bfp.xfitmin and p<=bfp.xfitmax ]
            fit_region_indices = [list(self.bands_positions).index(p) for p in fit_region]
            print str(len(fit_region)) + ' K-points detected in fitting region'
            
            if len(fit_region)<5:
                message = 'Warning! The fitting region includes only ' + str(len(fit_region)) 
                message += ' K-points, you may want to enlarge it, or provide a calculation with a denser K-mesh'
                print message

            if bfp.band_fit == 'CBM':
                band_energy = self.cb_energy
            else:
                band_energy = self.vb_energy
            
            en_to_fit = band_energy[fit_region_indices]  
            ymiddle = en_to_fit[len(fit_region)/2]
            if ymiddle > en_to_fit[0]: # convex
                y_extr = max(en_to_fit)
            else:
                y_extr = min(en_to_fit)
            
            length = len(fit_region)
            x_extr = fit_region[list(en_to_fit).index(y_extr)]
            
            print 'Parabol summit located in %.3f %.3f' % (x_extr, y_extr)
            self.steps = 0
            if ymiddle > en_to_fit[0]:
                print 'Fitting E = %.3f-(x-%.3f)**2/(2*m) by changing effective mass m...\n' % (y_extr, x_extr)
                def parabol(x, m):
                    self.steps += 1
                    return y_extr-(x-x_extr)**2/(2*m)
            else:
                print 'Fitting E = %.3f+(x-%.3f)**2/(2*m) by changing effective mass m...\n' % (y_extr, x_extr)
                def parabol(x, m):
                    self.steps += 1
                    return y_extr+(x-x_extr)**2/(2*m)

            popt, pcov = sco.curve_fit(parabol, fit_region, en_to_fit)
            
            print 'Convergence reached in ' + str(self.steps) + ' steps'
            print 'Standard deviation: ' + str(float(np.sqrt(np.diag(pcov)))) + ' eV'
            
            if bfp.band_fit == 'VBM':
                print '\n\nEffective mass of electrons in Valence Band is %.4f me' %float(popt)
            else:
                print '\n\nEffective mass of electrons in Conduction Band is %.4f me' %float(popt)
                
            if bfp.band_fit == 'VBM':
                color = 'red'
            else:
                color = 'blue'
                
            x = np.arange(min(self.bands_positions), max(self.bands_positions), 0.001)  
            
            ax.plot(x, parabol(x, *popt), '--', color=color, ms=10, mew=1.5, lw=4)
            ax.plot(fit_region, parabol(fit_region, popt), 'o-', label='fit ' + bfp.band_fit, color=color, ms=10, mew=1.5, lw=4)
                        
            

            pf.set_ax_parameters(ax, title=bfp.pp.title, xlabel=bfp.pp.x_label, ylabel=bfp.pp.y_label, xlim=[bfp.pp.xmin, bfp.pp.xmax], ylim=[bfp.pp.ymin ,bfp.pp.ymax], legend=bfp.pp.display_legends, grid=bfp.pp.grid,
                                fontsize=bfp.pp.fontsize, l_fontsize=bfp.pp.l_fontsize, xticks=bfp.pp.xticks_var, xtick_labels=bfp.pp.xticklabels_var, yticks=bfp.pp.yticks_var,
                                ytick_label=bfp.pp.yticklabels_var, title_fontsize=bfp.pp.title_fontsize)
                                
            x = np.arange(min(fit_region), max(fit_region), (max(fit_region) - min(fit_region))/500.)
            ax_sec.plot(x, parabol(x, *popt), label='fit ' + bfp.band_fit, color='black')
            ax_sec.plot(fit_region, en_to_fit, 'o', label=bfp.band_fit + ' points to fit', color=color)
            ax_sec.legend()
            
            pf.set_ax_parameters(ax_sec, fontsize=bfp.pp.fontsize, l_fontsize=bfp.pp.l_fontsize, grid=bfp.pp.grid)
            
            return figure
        else:
            print 'Warning! No range for ' + bfp.band_fit + ' fit specified!'


def get_functional(outcar):
    """ Retrieve the functional used from the outcar data
    :param outcar: content of the OUTCAR file (list of strings)
    :return: functional of used
    """

    # Default values
    functional = ''  # used for display inline
    functional_title = ''  # used for display in matplotlib

    lexch = bf.grep(outcar, 'LEXCH   =', 0, 'internal', 'str', 1)
    lhfcalc = bf.grep(outcar, 'LHFCALC =', 0, 'Hartree', 'str', 1)
    hfscreen = bf.grep(outcar, 'HFSCREEN=', 0, 'screening', 'float', 1)
    gw = bf.grep(outcar, 'Response functions by sum over occupied states:', nb_found=2)

    if lexch == '2' and lhfcalc == 'F':
        functional = 'LDA'
        functional_title = 'LDA'
    if lexch == '8' and lhfcalc == 'F':
        functional = 'GGA'
        functional_title = 'GGA'
    if lhfcalc == 'T':
        functional = 'Hybrid'
        functional_title = 'Hybrid'
        if lexch == '8' and lhfcalc == 'T':
            if hfscreen == 0.2:
                functional = 'HSE'
                functional_title = 'HSE'
            if hfscreen == 0.0:
                functional = 'PBE0'
                functional_title = 'PBE0'
    if gw is not None:
        nelm = bf.grep(outcar, 'NELM    =', 0, 'number', 'int', 1)
        if nelm == 1:
            functional = 'G0W0@GGA'
            functional_title = 'G_0W_0@GGA'
        elif nelm > 1:
            functional = 'GW0@GGA'
            functional_title = 'GW_0@GGA'

    return functional, functional_title


def get_atomic_species(outcar):
    """ Get the atoms species from the outcar content """

    lines = bf.grep(outcar, 'VRHFIN =')
    return [bf.grep(outcar, 'VRHFIN =', f, ':') for f in range(len(lines))]


def get_system_name(atoms_types, nb_atoms, reduced):
    """ Return the name of the system defined with the atom types and their number
    :param atoms_types: atomic species in the system (list of strings)
    :param nb_atoms: population of each atomic species (list of integers)
    :param reduced: if True, then tries to reduce the name of the system. Ex: Cd8In16S32 --> CdIn2S4
    :return: name of the system studied
    """
    if len(atoms_types) > 1:
        if reduced is True:
            common_factor = bf.get_gcd(nb_atoms)  # common factor between atomic population
            nb_atoms = [f/common_factor for f in nb_atoms]
    else:
        nb_atoms = [1]

    name = ''
    name_display = ''  # name for display in matplotlib

    for f, g in zip(nb_atoms, atoms_types):
        if f != 1:
            name += g + str(f)
            name_display += g + '_{' + str(f) + '}'
        else:
            name += g
            name_display += g

    return name, name_display


def get_cell_parameters(outcar):
    """ Retrieve the cell parameters from the OUTCAR file content """

    index = bf.grep(outcar, 'direct lattice vectors')[-1][1]  # location of the cristallographic parameters in the OUTCAR
    raw_data = outcar[index + 1:index + 4]  # direct and reciprocal lattice vectors
    return np.transpose(bf.fast_stringcolumn_to_array(raw_data)[:3])


def get_atoms_positions(outcar, atoms):
    """
    :param outcar: content of the outcar file (list of strings)
    :param atoms: number of atoms of each atomic species (list of integers) """

    str_beg = 'position of ions in cartesian coordinates  (Angst):'
    index_beg = bf.grep(outcar, str_beg, nb_found=1)[0][1] + 1  # index of the first atom position
    index_end = outcar[index_beg:].index('') - 1
    atoms_positions = np.transpose(bf.fast_stringcolumn_to_array(outcar[index_beg: index_end+index_beg]))
    # Check that the number of positions retrieved is equal to the number of atoms
    if len(atoms_positions) != len(atoms):
        raise bf.PyVALENCEImportError("The number of atoms positions is not consistent with the total number of atoms")
    else:
        return dict(zip(atoms, atoms_positions))


def get_band_occupation(outcar, nkpts, functional):
    """ Retrieve the bands occupation for each kpoint
    :param outcar: content of the outcar file (list of strings)
    :param nkpts: number of kpoints (int)
    :param functional: functional used (string)
    :return: last energy and occupation of the bands for each kpoint """

    if functional == 'GW0@GGA':
        str_beg = "  band No. old QP-enery  QP-energies   sigma(KS)   T+V_ion+V_H  V^pw_x(r,r')   Z            occupation"
        indices_beg = np.array([f[1] for f in bf.grep(outcar, str_beg)])[-nkpts:] + 2
        col_index = 2
    elif functional == 'G0W0@GGA':
        str_beg = "  band No.  KS-energies  QP-energies   sigma(KS)   V_xc(KS)     V^pw_x(r,r')   Z            occupation"
        indices_beg = np.array([f[1] for f in bf.grep(outcar, str_beg)]) + 2
        col_index = 2
    else:
        str_beg = '  band No.  band energies     occupation'
        indices_beg = np.array([f[1] for f in bf.grep(outcar, str_beg)]) + 1
        col_index = 1

    indices_end = np.array([outcar[f:].index('') for f in indices_beg])
    raw_data = [outcar[f: g] for f, g in zip(indices_beg, indices_end + indices_beg)]
    data = [bf.fast_stringcolumn_to_array(f) for f in raw_data]
    
    if functional == 'GW0@GGA' or functional == 'G0W0@GGA':
        return [np.array([f[col_index], f[-2]]) for f in data]
    else:
        return [np.array([f[col_index], f[-1]]) for f in data]


def get_electrostatic_potentials(outcar, atoms):
    """ Retrieve the electrostatic averaged potentials from the OUTCAR file
    :param outcar: content of the OUTCAR file (list of strings)
    :param atoms: number of atoms of each atomic species (list of integers)
    :return: dictionary with the electrostatic potential for each atom """

    index_beg = bf.grep(outcar, 'average (electrostatic) potential at core', nb_found=1)[0][1] + 3
    index_end = outcar[index_beg:].index(' ')

    potentials_str = outcar[index_beg: index_beg + index_end]
    potentials_raw = np.concatenate([[float(f) for f in re.split(' {5}|-', q)[1:]] for q in potentials_str])
    potentials = np.array([-f[1] for f in np.split(potentials_raw, len(atoms))])

    if len(potentials) != len(atoms):
        raise bf.PyVALENCEImportError('Number of electrostatic potentials retrieved and number are not consistent')

    return dict(zip(list(atoms), potentials))


def get_kpoints_weights_and_coords(outcar, nkpts, rec=False):
    """ Retrieve the kpoints weights from the OUTCAR file content
    :param outcar: content of the OUTCAR file (list of strings)
    :param nkpts: number of kpoints (int) used to check the number of weights found
    :param rec: Boolean. If True, find the reciprocal coordinates
    :return: numpy array """

    if rec:
        string = ' k-points in units of 2pi/SCALE and weight:'
    else:
        string = 'k-points in reciprocal lattice and weights'
    index_beg = bf.grep(outcar, string, nb_found=1)[0][1] + 1
    index_end = outcar[index_beg:].index(' ')  # find the next blank line

    data_str = outcar[index_beg: index_beg+index_end]
    x, y, z, weights = bf.fast_stringcolumn_to_array(data_str)
    coordinates = np.transpose([x, y, z])

    if len(weights) != nkpts:
        raise bf.PyVALENCEImportError('Number of kpoint weights retrieved and number of kpoints are not consistent')
    else:
        return coordinates, weights


class DosPlotParameters(pf.PlotParameters):
    """ Parameters for plotting the DOS of a Cell object """

    def __init__(self, cell):

        super(DosPlotParameters, self).__init__()
        self.type = 'DOS'

        # Plot parameters
        self.display_proj_dos = (cell.lorbit == 11)  # if True, display the projected DOS
        self.dos_type = 'OPAS'  # type of DOS plotted ('OPA': s,p,d orbitals projected DOS for each atom or 'OPAS': s,p,d orbitals projected DOS for each atomic species)
        self.tot_proj_dos = True  # if True, then the total projected DOS is plotted (according to 'dos_type') if False, the Projections are plotted
        self.choice_opas = cell.atoms_types  # list of atomic species
        self.choice_opa = cell.atoms  # list of atoms
        self.nedos = cell.nedos
        if cell.ispin == 2:
            self.dos_range = [-cell.dosmax_down, cell.dosmax_up]  # DOS range (list of float)
        else:
            self.dos_range = [0, cell.dosmax]
        
        if cell.orbitals is not None and len(cell.orbitals) == 4:  # s p d f orbitals
            self.colors_proj = ['#990000', '#e60000', '#ff6666', '#ff66cc',
                                '#003399', '#0000e6', '#9999ff', '#cc66ff',
                                '#00802b', '#00b33c', '#1aff66', '#99ff99',
                                '#999900', '#e6e600', '#ffff33', '#ffff99']  # list of colors for orbital projected plots
        else:
            self.colors_proj = ['#990000', '#e60000', '#ff6666',
                                '#003399', '#0000e6', '#9999ff',
                                '#00802b', '#00b33c', '#1aff66',
                                '#999900', '#e6e600', '#ffff33']  # list of colors for orbital projected plots
        self.colors_tot = ['#ff0000', '#0033cc', '#33cc33', '#e6e600']  # list of colors for total projected plots
        if cell.fermi_energy is not None:
            self.fermi_shift = True  # if True, then the zero of energy is the fermi level
        else:
            self.fermi_shift = False
        self.normalise_dos = False   # if True, normalise the DOS
        self.display_total_dos = True  # if True, display the total DOS
        self.display_BM_levels = False  # if True, display the band maxima levels
        self.display_Fermi_level = True  # if True, display the fermi levels
        self.input_shift = 0.0
        self.display_spin = False  # if True, display the DOS of the spin up and down, if False, display the total DOS
        self.plot_areas = False  # if True, plot the DOS as stacked areas, else _plot the DOS as non stacked lines
        self.normalize = False
        self.smooth = False # if True, DoS smoothing using moving average of self.n_smooth order
        self.n_smooth = 100

        # Figure and axis parameters
        self.title = cell.title  # Title of the plot
        self.name = 'Default DoS plot parameters'
        if self.fermi_shift:
            self.x_label = '$E - E_F$ (eV)'
        else:
            print 'No Fermi level retrieved'
            self.x_label = '$E$ (eV)'
        self.y_label = 'DoS (states/eV)'
        self.energy_range = np.sort([cell.emin, cell.emax])
        if not self.normalize:
            self.ymin = self.dos_range[0]
            self.ymax = self.dos_range[1]
        else:
            self.ymin = 0
            self.ymax = 1
        self.xmin = self.energy_range[0]
        self.xmax = self.energy_range[1]
        self.lw = 3


class BandDiagramPlotParameters(pf.PlotParameters):

    def __init__(self, cell):
        
        super(BandDiagramPlotParameters, self).__init__()
        self.type = 'Band diagram'
        bands_data = cell.bands_data

        # Plot parameters
        self.energy_range = [np.min(bands_data), np.max(bands_data)]
        self.hs_kpoints_names = ['']  # list of names of the kpoints of high symmetry
        self.vbm_shift = False   # if True, shift the bands energy such that the vbm_energy energy is zero
        self.highlight_zero_line = False # Highlight zero line
        self.colors = False # Color bands around VBM
        self.highlight_vbm_cbm = False
        self.title = cell.title
        self.name = 'Default Band Diagram Plot Parameters'
        self.x_label = 'High-symmetry K-points'
        self.y_label = 'E (eV)'
        self.xmin = 0
        self.xmax = max(cell.bands_positions)
        self.display_legends = False 
        self.discontinuities = False
        self.nkpts_per_seg = 0 # for discontinuities
        self.nkpts_hybrid_bands = 0
        

class BandFitPlotParameters(BandDiagramPlotParameters):

    def __init__(self, cell):
        
        super(BandFitPlotParameters, self).__init__(cell)
        self.display_legends = True
        self.highlight_vbm_cbm = True
        self.bands_fit = {'CBM': BandFitParameters(self, 'CBM'), 'VBM': BandFitParameters(self, 'VBM')}       
        

class BandFitParameters(object):
    
    def __init__(self, parent, band_fit):
        self.pp = parent
        self.band_fit = band_fit 
        self.xfitmin = None 
        self.xfitmax = None 
        
