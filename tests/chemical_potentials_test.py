import pydef_core.cell as cc
import pydef_core.chemical_potentials as pcp
import pydef_core.defect as dc

import matplotlib.pyplot as plt


directory = './tests/test_files/'


C24 = cc.Cell(directory + 'Functionals/CdIn2S4_GGA/OUTCAR')
Cd = cc.Cell(directory + 'Chemical_potentials/Cd/OUTCAR')
In = cc.Cell(directory + 'Chemical_potentials/In/OUTCAR')
S = cc.Cell(directory + 'Chemical_potentials/S/OUTCAR')
In2S3 = cc.Cell(directory + 'Chemical_potentials/In2S3/OUTCAR')
InS = cc.Cell(directory + 'Chemical_potentials/InS/OUTCAR')
CdS = cc.Cell(directory + 'Chemical_potentials/CdS/OUTCAR')

print '\nRAW ENERGIES'

print 'C24_GGA ' + str(C24.total_energy)
print 'S ' + str(S.total_energy)
print 'CdS ' + str(CdS.total_energy)
print 'In2S3 ' + str(In2S3.total_energy)
print 'InS ' + str(InS.total_energy)

# ---------------------------  TEST 1D PLOTS  --------------------------

figure1 = plt.figure()
ax1 = figure1.add_subplot(111)

chemPot1 = pcp.ChemicalPotentials(In2S3)
chemPot1.add_non_synthesized(S)
chemPot1.add_non_synthesized(In)
chemPot1.add_non_synthesized(InS)

chemPot1.plot_stability_domain(ax1, None)

figure1.show()

print '\n'
print chemPot1.lastppp.constrainEquation+"\n"
for ineq in chemPot1.lastppp.domainInequationsList: print ineq + "\n"

# ---------------------------  TEST 2D PLOTS  --------------------------

chemPot = pcp.ChemicalPotentials(C24)
chemPot.add_non_synthesized(S)
chemPot.add_non_synthesized(CdS)
chemPot.add_non_synthesized(In2S3)
chemPot.add_non_synthesized(InS)

print '\n\n'

print 'chemPot.synthesized: ' + str(chemPot.synthesized) + '\n'
print 'chemPot.non_synthesized: ' + str(chemPot.non_synthesized.keys()) + '\n'
print 'chemPot.synth_population: ' + str(chemPot.synth_population) + '\n'

print '\n'

figure = plt.figure()
ax = figure.add_subplot(111)

ax.set_xticks([-0.5*i for i in range(1,6)])
plt.subplots_adjust(left=0.1, bottom=0.1, right=0.9, top=0.9, wspace=0.2, hspace=0.2)

chemPot.plot_stability_domain(ax, None).show()

"""import sys
sys.exit()

figure = plt.figure()
ax = figure.add_subplot(111)

chemPot.plot_stability_domain(None, None)

figure.show()



# Testing plot parameters

ppp = pcp.PotentialsPlotParameters(chemPot)
ppp.mu_X_axis = 'S'
ppp.mu_Y_axis = 'In'
ppp.const = 'Cd'

ppp.display_summits = False
ppp.title = 'Test of plot parameters'
ppp.grid = True
ppp.hashed = False
ppp.autoscale = True
ppp.axes_label_fontsize = 40
ppp.title_fontsize = 10

chemPot.plot_stability_domain(ax, ppp)

figure.show()

print '\n'
print chemPot.lastppp.constrainEquation + "\n"
for ineq in chemPot.lastppp.domainInequationsList: print ineq + "\n"""
