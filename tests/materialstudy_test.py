import pydef_core.cell as cc
import pydef_core.defect as dc
import pydef_core.defect_study as ds
import pydef_core.defects_concentration as pdp
import matplotlib.pyplot as plt

directory = './tests/test_files/'

# ------------------------------------------------------ HOST CELL -----------------------------------------------------

C24_GGA = cc.Cell(directory + 'Functionals/CdIn2S4 - GGA/OUTCAR', directory + 'Functionals/CdIn2S4 - GGA/DOSCAR')
C24_PBE0 = cc.Cell(directory + 'Functionals/CdIn2S4 - PBE0/OUTCAR', directory + 'Functionals/CdIn2S4 - PBE0/DOSCAR')
C24_bands = cc.Cell(directory + 'Bands/GGA/OUTCAR', '')

# --------------------------------------------------- SULFUR VACANCY ---------------------------------------------------

C24_VS_q0 = cc.Cell(directory + 'Defects/CdIn2S4 - VS/q0/OUTCAR', directory + 'Defects/CdIn2S4 - VS/q0/DOSCAR')
C24_VS_q1 = cc.Cell(directory + 'Defects/CdIn2S4 - VS/q1/OUTCAR', directory + 'Defects/CdIn2S4 - VS/q1/DOSCAR')
C24_VS_q2 = cc.Cell(directory + 'Defects/CdIn2S4 - VS/q2/OUTCAR')
VS_defect = dc.Defect('Vacancy', ['S (32)'], [-5.13])

VS = ds.DefectStudy(C24_GGA, C24_PBE0, [VS_defect], 'fcc', 14.3, 1.853346, 0, 0, [])
VS.create_defect_cell_study(C24_VS_q0, 4, 0, 0)
VS.create_defect_cell_study(C24_VS_q1, 4, 1, 0)
VS.create_defect_cell_study(C24_VS_q2, 4, 0, 0)

# ------------------------------------------------ INTERSTITIAL INDIUM -------------------------------------------------

C24_IIn_q0 = cc.Cell(directory + 'Defects/CdIn2S4 - I_In/q0/OUTCAR', directory + 'Defects/CdIn2S4 - I_In/q0/DOSCAR')
C24_IIn_q1 = cc.Cell(directory + 'Defects/CdIn2S4 - I_In/q1/OUTCAR', directory + 'Defects/CdIn2S4 - I_In/q1/DOSCAR')
C24_IIn_q2 = cc.Cell(directory + 'Defects/CdIn2S4 - I_In/q2/OUTCAR', directory + 'Defects/CdIn2S4 - I_In/q2/DOSCAR')
C24_IIn_q3 = cc.Cell(directory + 'Defects/CdIn2S4 - I_In/q3/OUTCAR', directory + 'Defects/CdIn2S4 - I_In/q3/DOSCAR')
IIn_defect = dc.Defect('Interstitial', ['In (17)'], [-2.55])

IIn = ds.DefectStudy(C24_GGA, C24_PBE0, [IIn_defect], 'fcc', 14.3, 1.853346, 0, 0, [])
IIn.create_defect_cell_study(C24_IIn_q0, 3, 1, 0)
IIn.create_defect_cell_study(C24_IIn_q1, 3, 0, 0)
IIn.create_defect_cell_study(C24_IIn_q2, 3, 1, 0)
IIn.create_defect_cell_study(C24_IIn_q3, 3, 0, 0)

# ---------------------------------------------------- SUBSTITUTION ----------------------------------------------------

C24_Cd_In_q1 = cc.Cell(directory + 'Defects/CdIn2S4 - Cd_In/q-1/OUTCAR', directory + 'Defects/CdIn2S4 - Cd_In/q-1/DOSCAR')
C24_Cd_In_q2 = cc.Cell(directory + 'Defects/CdIn2S4 - Cd_In/q-2/OUTCAR', directory + 'Defects/CdIn2S4 - Cd_In/q-2/DOSCAR')
Cd_In_defect = dc.Defect('Substitutional', ['In (1)', 'Cd (9)'], [-2.55, -0.95])

Cd_In = ds.DefectStudy(C24_GGA, C24_PBE0, [Cd_In_defect], 'fcc', 14.3, 1.853346, 0, 0, [])
Cd_In.create_defect_cell_study(C24_Cd_In_q1, 3, 0, 0)
Cd_In.create_defect_cell_study(C24_Cd_In_q2, 3, 0, 0)

# --------------------------------------------------------- C24 --------------------------------------------------------

c24 = ds.MaterialStudy(VS, IIn, Cd_In)


# ------------------------------------------------ DEFECT CONCENTRATION ------------------------------------------------

conc = ds.ConcentrationsCalculation(c24, [32, 10, 50], 0.044, 1.065)
cpp = ds.ConcentrationPlotParameters()
cpp.data_id = ''
conc.plot(None, cpp)

fpp = ds.FormationPlotParameters(VS)
tpp = ds.TransitionPlotParameters(VS)
ax = plt.subplot()
VS.plot_formation_energy(ax, fpp)
VS.plot_transition_levels(ax, tpp)
