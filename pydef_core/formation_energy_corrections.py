import numpy as np
import pydef_core.figure as pf
import pydef_core.basic_functions as bf
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def potential_alignment_correction(host_cell, defect_cell, defects, spheres_radius, plotsphere=True, display_atom_name=False):
    """ Compute the potential alignment correction by calculating the average difference of electrostatic potentials of atoms
    far away from the defects and their images. This is done by considering spheres around the defects and their images with the
    same radius. Only the atoms outside these spheres (so at a minimum distance from a defect) are considered.

    :param host_cell: Cell object of the host cell calculation
    :param defect_cell: Cell object of the defect cell calculation
    :param defects: list of Defect objects
    :param spheres_radius: radius of the spheres in angstrom (float)
    :param plotsphere: if True, then represent the spheres and positions of the atoms
    :param display_atom_name: if True, display the name of each atom on the representation """

    atoms_pos_d = defect_cell.atoms_positions
    atoms_pos_h = host_cell.atoms_positions
    potentials_h = host_cell.potentials  # electrostatic potentials of the atoms of the host cell
    potentials_d = defect_cell.potentials  # electrostatic potentials of the atoms of the defect cell
    atoms_h = list(host_cell.atoms)  # atoms labels of the host cell
    atoms_d = list(defect_cell.atoms)  # atoms labels of the defect cell

    # Positions of the defects and their images
    defects_position = [f.set_defect_position(atoms_pos_h, atoms_pos_d) for f in defects]  # defects positions

    defect_images_positions = [np.dot(host_cell.cell_parameters, f) for f in
                               [[0, 0, 0], [0, 0, -1], [0, 0, 1], [1, 0, 0],
                                [-1, 0, 0], [0, -1, 0], [0, 1, 0]]]  # relative position of the images of the defects

    defects_positions = [[f + g for g in defect_images_positions]
                         for f in defects_position]  # all positions of the defects and their respective images

    # Removing useless data
    for Defect in defects:
        if Defect.defect_type == 'Vacancy':
            potentials_h.pop(Defect.atom[0])  # remove the electrostatic potential of the atom removed from the host cell data
            atoms_h.remove(Defect.atom[0])
        elif Defect.defect_type == 'Interstitial':
            potentials_d.pop(Defect.atom[0])  # remove the electrostatic potential of the atom added from the defect cell data
            atoms_pos_d.pop(Defect.atom[0])  # remove the position of the corresponding atom so the number of positions and potentials match
            atoms_d.remove(Defect.atom[0])
        elif Defect.defect_type == 'Substitutional':
            potentials_h.pop(Defect.atom[0])
            potentials_d.pop(Defect.atom[1])
            atoms_pos_d.pop(Defect.atom[1])
            atoms_h.remove(Defect.atom[0])
            atoms_d.remove(Defect.atom[1])

    # Compute the average electrostatic potential outside the spheres
    potentials_list_h = [potentials_h[f] for f in atoms_h]
    potentials_list_d = [potentials_d[f] for f in atoms_d]
    atoms_pos_list_d = [atoms_pos_d[f] for f in atoms_d]

    distances = [np.array([bf.distance(f, g) for f in atoms_pos_list_d])
                 for g in np.concatenate(defects_positions)]  # distance of each atom from each defect

    min_distances = [min(f) for f in np.transpose(distances)]  # minimum distance between an atom and any defect or its image

    index_out = [np.where(f > spheres_radius)[0] for f in distances]  # index of the atoms outside the spheres which centers are the defects

    common_index_out = bf.get_common_values(index_out)  # index of the atoms outside all the spheres radius

    energy_diff = np.array(potentials_list_d) - np.array(potentials_list_h)  # difference of electrostatic energy between the defect and host cells
    pot_al = np.mean(energy_diff[common_index_out])  # average electrostatic difference between the defect and host cells taking into account only the atoms outside the spheres

    if plotsphere is True:
        figure = plt.figure()
        ax = figure.add_axes([0.01, 0.1, 0.45, 0.8], projection='3d', aspect='equal')
        
        # Display the spheres and defects
        [bf.plot_sphere(spheres_radius, f[0], ax, '-') for f in defects_positions]  # spheres around the defects
        [[bf.plot_sphere(spheres_radius, f, ax, '--') for f in q[1:]] for q in defects_positions]  # spheres around the images of the defects
        [[ax.scatter(f[0], f[1], f[2], color='red', s=400, marker='*') for f in q] for q in defects_positions]  # Position of the defects objects and images
        [[ax.text(f[0], f[1], f[2] + 0.2, s='$' + g.name + '$', ha='center', va='bottom', color='red') for f in q]
         for q, g in zip(defects_positions, defects)]

        # Atoms positions
        atoms_positions = np.transpose(atoms_pos_list_d)
        scatterplot = ax.scatter(atoms_positions[0], atoms_positions[1], atoms_positions[2], s=100, c=energy_diff, cmap='hot', depthshade=False)
        if display_atom_name is True:
            [ax.text(f[0], f[1], f[2], s=g, ha='center', va='bottom') for f, g in zip(atoms_pos_list_d, atoms_d)]

        # Plot parameters
        ax.set_axis_off()

        # X limit is set as the maximum value of the projection of the cristallographic parameters on the x-axe, etc.
        ax.set_xlim(0, np.max(np.transpose(defect_cell.cell_parameters)[0]))
        ax.set_ylim(0, np.max(np.transpose(defect_cell.cell_parameters)[1]))
        ax.set_zlim(0, np.max(np.transpose(defect_cell.cell_parameters)[2]))

        # Colorbar
        temp1 = figure.get_window_extent()
        temp2 = ax.get_window_extent()
        ax_cb = figure.add_axes([temp2.x0 / temp1.x1, temp2.y0 / temp1.y1 - 0.04, (temp2.x1 - temp2.x0) / temp1.x1, 0.03])
        cb = figure.colorbar(scatterplot, cax=ax_cb, orientation='horizontal')
        cb.set_label('$\Delta V\ (eV)$')
        
        return pot_al, figure

    else:
        return min_distances, energy_diff, pot_al


def plot_potential_alignment(host_cell, defect_cell, defects, spheres_radius, title_plot, display_atom_name=False):
    """ Draw 3 plots in a same figure
    1) Graphical representation of the positions of the defects and the atoms, and the spheres around the defects
    2) Average electrostatic energy difference between defect and host cells as a function of the spheres radius
    3) Electrostatic energy difference between defect and host cells between each atom as a function of their minimum distance from a defect

    :param host_cell: Cell object of the host cell calculation
    :param defect_cell: Cell object of the defect cell calculation
    :param defects: list of Defect objects
    :param spheres_radius: radius of the spheres in angstrom (float)
    :param title_plot: title of the plot
    :param display_atom_name: if True, display the name of each atom on the representation
    """

    fig = potential_alignment_correction(host_cell, defect_cell, defects, spheres_radius, True, display_atom_name)[1]  # plot the spheres and ions
    min_distances, energy_diff = potential_alignment_correction(host_cell, defect_cell, defects, spheres_radius, False)[0:2]  # minimum distance and potential alignment for each atom
    spheres_radii = np.linspace(0, 1, 100) * np.max(defect_cell.cell_parameters)
    pot_all = [potential_alignment_correction(host_cell, defect_cell, defects, f, False)[-1] for f in spheres_radii]  # mean potential alignment for each spheres radius

    # Average electrostatic energy difference between defect and host cells as a function of the spheres radius
    ax1 = fig.add_subplot(222)
    ax1.plot(spheres_radii, pot_all, 'x', ms=7)
    ax1.axvline(spheres_radius, ls='--', c='g')  # plot a line corresponding to the current sphere radii value
    ax1.set_xlabel(r'Spheres radius $R$ ($\AA$)')
    ax1.set_ylabel(r"$\overline{\Delta V(r>R)}$ ($eV$)")

    if np.nanmin(pot_all) <= 0:
        ax1.set_ylim(bottom=np.round(np.nanmin(pot_all) * 1.1, 2))
    else:
        ax1.set_ylim(bottom=np.round(np.nanmin(pot_all) * 0.9, 2))

    if np.nanmax(pot_all) <= 0:
        ax1.set_ylim(top=np.round(np.nanmax(pot_all) * 0.9, 2))
    else:
        ax1.set_ylim(top=np.round(np.nanmax(pot_all) * 1.1, 2))

    # Electrostatic energy difference between defect and host cells between each atom as a function of their minimum distance from a defect
    ax2 = fig.add_subplot(224)
    ax2.plot(min_distances, energy_diff, 'x', ms=7)
    ax2.set_xlabel(r'Distance to the closest defect ($\AA$)')
    ax2.set_ylabel(r"$\Delta V(r)$ ($eV$)")
    ax2.set_xlim(np.min(min_distances)*0.9, np.max(min_distances)*1.02)

    if np.nanmin(energy_diff) <= 0:
        ax2.set_ylim(bottom=np.round(np.nanmin(energy_diff) * 1.1, 2))
    else:
        ax2.set_ylim(bottom=np.round(np.nanmin(energy_diff) * 0.9, 2))

    if np.nanmax(energy_diff) <= 0:
        ax2.set_ylim(top=np.round(np.nanmax(energy_diff) * 0.9, 2))
    else:
        ax2.set_ylim(top=np.round(np.nanmax(energy_diff) * 1.1, 2))

    fig.suptitle('$' + title_plot.replace(' ', '\ ') + '$', x=0.22)
    # fig.tight_layout()  # might be removed to solve the non updating 3d plot
    fig.show()
    # return fig


def get_bands_correction(host_cell, defect_cell, pot_al):
    """ Get the number of electrons and holes in the conduction and valence bands with respect to the host cell """

    bands_data = defect_cell.bands_data

    if defect_cell.ispin == 1:
        kpoints_weights = defect_cell.kpoints_weights
        max_occupation = 2.
    else:
        kpoints_weights = list(defect_cell.kpoints_weights / 2.) * 2
        max_occupation = 1.

    cbm_aligned = host_cell.cbm_energy + pot_al
    vbm_aligned = host_cell.vbm_energy + pot_al

    nb_electrons = sum([k * sum(f[1] * bf.heaviside(f[0] - cbm_aligned)) for f, k in zip(bands_data, kpoints_weights)])
    nb_holes = sum([k * sum((max_occupation - f[1]) * bf.heaviside(vbm_aligned - f[0])) for f, k in zip(bands_data, kpoints_weights)])

    e_donnor = - sum([k * sum(f[1] * (f[0] - cbm_aligned) * bf.heaviside(f[0] - cbm_aligned)) for f, k in zip(bands_data, kpoints_weights)])
    e_acceptor = - sum([k * sum((max_occupation - f[1]) * (vbm_aligned - f[0]) * bf.heaviside(vbm_aligned - f[0])) for f, k in zip(bands_data, kpoints_weights)])

    return e_acceptor, e_donnor, nb_holes, nb_electrons


def band_extrema_correction(host_cell, host_cell_b):
    """ Compute the correction of the band extrema computed with a functional (Host_Cell)
    in order to retrieve the same gap computed with another functional (Host_Cell_B)
    :param host_cell: Cell object of the host cell calculation
    :param host_cell_b: Cell object of the host cell calculation (with a different functional) """

    de_vbm = host_cell_b.vbm_energy - host_cell.vbm_energy
    de_cbm = host_cell_b.cbm_energy - host_cell.cbm_energy

    return de_vbm, de_cbm


def phs_correction(z_h, z_e, de_vbm, de_cbm):
    """ Compute the PHS correction
    :param z_h: number of holes in the PHS
    :param z_e: number of electrons in the PHS
    :param de_vbm: correction of the VBM
    :param de_cbm: correction of the CBM"""

    return - z_h * de_vbm, z_e * de_cbm


def vbm_correction(defect_cell, de_vbm):
    """ Correction of the VBM energy
    :param defect_cell: Cell object of the defect cell calculation
    :param de_vbm: correction of the VBM """

    return defect_cell.charge * de_vbm


def makov_payne_correction(defect_cell, geometry, e_r, mk_1_1):
    """ Makov-Payne correction
    :param defect_cell: Cell object of the defect cell calculation
    :param geometry: geometry of the host cell
    :param e_r: relative permittivity
    :param mk_1_1: Value of the first term of the Makov-Payne correction in the case q = 1 & e_r = 1 """

    c_sh_dico = {'sc': -0.369, 'fcc': -0.343, 'bcc': -0.342, 'hcp': -0.478, 'other': -1./3}
    c_sh = c_sh_dico[geometry]

    return (1. + c_sh * (1. - 1./e_r)) * defect_cell.charge ** 2 * mk_1_1 / e_r
