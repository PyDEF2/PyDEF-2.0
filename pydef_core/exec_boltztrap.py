# -*- coding: utf-8 -*

import os
import os.path
import pickle
import logging

import numpy as np
import matplotlib.pylab as pl
import pickle

from BoltzTraP2 import dft as BTP
from BoltzTraP2 import sphere
from BoltzTraP2 import fite
from BoltzTraP2 import bandlib as BL
from BoltzTraP2 import serialization
from BoltzTraP2 import units

logging.basicConfig(
    level=logging.DEBUG, format="{levelname:8s}│ {message:s}", style="{")

savedata = {}

def boltztrap(dirname, bt2file, title, T):
    print(("\n\nWorking in %s for %s at %i K" %(dirname, title, T)))
    # If a ready-made file with the interpolation results is available, use it
    # Otherwise, create the file.
    if not os.path.exists(bt2file):
        # Load the input
        data = BTP.DFTData(dirname)
        # Select the interesting bands
        nemin, nemax = data.bandana(emin=data.fermi - .2, emax=data.fermi + .2)
        # Set up a k point grid with roughly five times the density of the input
        equivalences = sphere.get_equivalences(data.atoms, len(data.kpoints) * 5)
        # Perform the interpolation
        coeffs = fite.fitde3D(data, equivalences)
        # Save the result
        serialization.save_calculation(bt2file, data, equivalences, coeffs,
                                       serialization.gen_bt2_metadata(
                                           data, data.mommat is not None))

    # Load the interpolation results
    print("Load the interpolation results")
    data, equivalences, coeffs, metadata = serialization.load_calculation(bt2file)

    # Reconstruct the bands
    print("Reconstruct the bands")
    lattvec = data.get_lattvec()
    eband, vvband, cband = fite.getBTPbands(equivalences, coeffs, lattvec)

    # Obtain the Fermi integrals for different chemical potentials at
    # room temperature.
    TEMP = np.array([T])
    epsilon, dos, vvdos, cdos = BL.BTPDOS(eband, vvband, npts=4000)
    margin = 9. * units.BOLTZMANN * TEMP.max()
    mur_indices = np.logical_and(epsilon > epsilon.min() + margin,
                                 epsilon < epsilon.max() - margin)
    mur = epsilon[mur_indices]
    N, L0, L1, L2, Lm11 = BL.fermiintegrals(
        epsilon, dos, vvdos, mur=mur, Tr=TEMP, dosweight=data.dosweight)

    # Compute the Onsager coefficients from those Fermi integrals
    print("Compute the Onsager coefficients")
    UCvol = data.get_volume()
    sigma, seebeck, kappa, Hall = BL.calc_Onsager_coefficients(
        L0, L1, L2, mur, TEMP, UCvol)

    fermi = BL.solve_for_mu(epsilon, dos, data.nelect, T, data.dosweight)
    
    savedata[title+'-%s' %T] = {"sigma":sigma, "seebeck":seebeck, 
    "kappa":kappa, "Hall":Hall, "mu":(mur - fermi) / BL.eV, "temp": T, "n":N[0]+data.nelect}

files = ["00_no_GD3-BJ/02_SAVE_DOS/", "01_GD3-BJ/01_SAVE_DOS/"]
names = ["no_VdW", "VdW"]

print("Starting\n\n")
for i in range(0,len(files)):
    print(("\n%s\n" %names[i]))
    for T in [1]+list(range(300,800,100)):
        figures(files[i],files[i]+names[i]+'.bt2',names[i],T)
        print("Exporting data...\n")
        pickle.dump(savedata[names[i]+'-%s' %T],open('boltzdata-'+names[i]+'-%s' %T,'wb'), protocol=2)
        print("Done!")

