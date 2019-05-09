""" Test file for the 'cell' module """

import pydef_core.cell as cc
import matplotlib.pyplot as plt


directory = './tests/test_files/'

# Functionals
gga = cc.Cell(directory + 'Functionals/CdIn2S4 - GGA/OUTCAR', directory + 'Functionals/CdIn2S4 - GGA/DOSCAR')
pbe0 = cc.Cell(directory + 'Functionals/CdIn2S4 - PBE0/OUTCAR', directory + 'Functionals/CdIn2S4 - PBE0/DOSCAR')
hse_spin = cc.Cell(directory + 'Functionals/CdIn2S4 - SPIN/OUTCAR', directory + 'Functionals/CdIn2S4 - SPIN/DOSCAR')
bands_gga = cc.Cell(directory + 'Bands/GGA/OUTCAR', directory + 'Bands/GGA/DOSCAR')
bands_pbe0 = cc.Cell(directory + 'Bands/PBE0/OUTCAR', directory + 'Bands/PBE0/DOSCAR')


# DOS
def plot_dos(cell):
    dpp = cc.DosPlotParameters(cell)
    dpp.display_BM_levels = True
    figure = plt.figure()
    ax = figure.add_subplot()
    cell.plot_dos(ax, dpp)


plot_dos(gga)
plot_dos(pbe0)
plot_dos(hse_spin)


# bands
def plot_bands(cell):
    bpp = cc.BandDiagramPlotParameters(cell)
    bpp.highlight_vbm_cbm = True
    bpp.energy_range = [0, 8]
    figure = plt.figure()
    ax = figure.add_subplot(111)
    cell.plot_band_diagram(ax, bpp)


plot_bands(bands_gga)
plot_bands(bands_pbe0)
