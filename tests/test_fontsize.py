import pydef_core.cell as pc

directory = './tests/test_files/'
gga = pc.Cell(directory + 'Functionals/CdIn2S4 - GGA/OUTCAR', directory + 'Functionals/CdIn2S4 - GGA/DOSCAR')
dpp = pc.DosPlotParameters(gga)
dpp.text_size = 60

gga.plot_dos(None, dpp)
