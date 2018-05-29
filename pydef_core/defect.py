"""
    Module for defect label creation
    version: 1.0.0
"""


class Defect(object):
    """ Object containing various data on a defect """

    def __init__(self, defect_type, atom, chem_pot, nb_sites=None, username=None):
        """
        :param defect_type: Type of defect ('Vacancy', 'Interstitial' or 'Substitutional')
        :param atom: list of atom(s) affected by the defect with the following pattern for each
                    "atomic_species + space + ( + atom_number + )". The atom number depends on the defect_type:
                        Vacancy : with respect to all atoms of the same species in the host cell
                        Interstitial : with respect to all atoms of the same species in the defect cell
                in the case of a substitution, a list of 2 atoms must be provided, the first one is the one removed and
                the second one is the one added.
                Ex: ['Cd (3)']
        :param chem_pot: list of chemical potentials corresponding to the affected atoms.
        """

        self.defect_type = defect_type
        self.atom = atom
        self.chem_pot_input = chem_pot
        self.nb_sites = nb_sites

        if defect_type == 'Vacancy':
            atomic_species = atom[0].split()[0]
            self.name = 'V_{' + atomic_species + '}'  # for matplotlib display
            if username is None:
                self.ID = 'Vac_' + atom[0].replace(' ', '')
            else:
                self.ID = username
            self.n = +1
            self.chem_pot = chem_pot[0]
            self.population = {atomic_species: +1}

        elif defect_type == 'Interstitial':
            atomic_species = atom[0].split()[0]
            self.name = atomic_species + '_i'
            if username is None:
                self.ID = 'Inter_' + atom[0].replace(' ', '')
            else:
                self.ID = username
            self.n = -1
            self.chem_pot = chem_pot[0]
            self.population = {atomic_species: -1}

        elif defect_type == 'Substitutional':
            atomic_species = [f.split()[0] for f in atom]
            self.name = atomic_species[1] + '_{' + atomic_species[0] + '}'
            if username is None:
                self.ID = 'Subs(' + atom[0].replace(' ', '') + '_by_' + atom[1].replace(' ', '') + ')'
            else:
                self.ID = username
            self.n = +1
            self.chem_pot = chem_pot[0] - chem_pot[1]
            self.population = {atomic_species[0]: +1, atomic_species[1]: -1}
        if username is None:
            self.displayname = self.name
        else:
            self.name = username
            self.displayname = self.name.replace('_','').replace('{','').replace('}','')

    def set_defect_position(self, atoms_positions_host, atoms_positions_defect):
        """
        :param atoms_positions_host: atoms positions in the host cell (dictionary)
        :param atoms_positions_defect: atoms positions in the defect cell (dictionary)
        :return: position of the defect """

        if self.defect_type == 'Vacancy':
            self.coord = atoms_positions_host[self.atom[0]]
        elif self.defect_type == 'Interstitial':
            self.coord = atoms_positions_defect[self.atom[0]]
        elif self.defect_type == 'Substitutional':
            self.coord = atoms_positions_defect[self.atom[1]]

        return self.coord


FERE = {
'Ag': -0.83,
'Al': -3.02,
'As': -5.06,
'Au': -2.23,
'Ba': -1.39,
'Be': -3.4,
'Bi': -4.39,
'Ca': -1.64,
'Cd': -0.56,
'Cl': -1.63,
'Co': -4.75,
'Cr': -7.22,
'Cu': -1.97,
'F': -1.7,
'Fe': -6.15,
'Ga': -2.37,
'Ge': -4.14,
'Hf': -7.4,
'Hg': -0.12,
'In': -2.31,
'Ir': -5.96,
'K': -0.8,
'La': -3.66,
'Li': -1.65,
'Mg': -0.99,
'Mn': -7,
'N': -8.51,
'Na': -1.06,
'Nb': -6.69,
'Ni': -3.57,
'O': -4.73,
'P': -5.64,
'Pd': -3.12,
'Pt': -3.95,
'Rb': -0.68,
'Rh': -4.76,
'S': -4,
'Sb': -4.29,
'Sc': -4.63,
'Se': -3.55,
'Si': -4.99,
'Sn': -3.79,
'Sr': -1.17,
'Ta': -8.82,
'Te': -3.25,
'Ti': -5.52,
'V': -6.42,
'Y': -4.81,
'Zn': -0.84,
'Zr': -5.87}
