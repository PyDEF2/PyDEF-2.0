import pydef_core.cell as cc
import pydef_core.defect as dc
import pydef_core.defect_study as ds
import pydef_core.material_study as ms
import pydef_core.chemical_potential as pcp
import pydef_core.defects_concentration as pdp
import pydef_core.defect_geom_comparison as dgc

directory = 'D:/docs/Mes_Documents/Docs/02_DevPython/02_GitRepo/pydef/tests/test_files/'

#Data format : testing constructors
# ------------------------------------------------------ HOST CELL -----------------------------------------------------
C24_GGA = cc.Cell(directory + 'CdIn2S4 - GGA/OUTCAR', directory + 'CdIn2S4 - GGA/DOSCAR')

print '\n======================================================================\n'
print '			TESTING CONSTRUCTORS		\n'
print '\n======================================================================\n'
# ---------------------------------------------------- SUBSTITUTION ----------------------------------------------------
print 'Testing constructor... SUBSTITUTION...\n'
#Defect cell
C24_Cd_In_q1 = cc.Cell(directory + 'CdIn2S4 - Cd_In/q-1/OUTCAR', directory + 'CdIn2S4 - Cd_In/q-1/DOSCAR')
#Defect
Cd_In_defect = dc.Defect('Substitutional', ['In (1)', 'Cd (9)'], [-2.55, -0.95])

Cd_In_defect.set_defect_position(C24_GGA.atoms_positions,C24_Cd_In_q1.atoms_positions)

#Create GeomComparison object
test = dgc.GeomComparison(C24_GGA,Cd_In_defect,C24_Cd_In_q1, None, None, None)

print 'test.perfectCell.name: ' + str(test.perfectCell.name)
print 'test.defectCell.name: ' + str(test.defectCell.name)
#print 'test.defectCell.atoms_positions: ' + str(test.defectCell.atoms_positions)
print 'test.metrics: \n' + str(test.metrics)
print 'test.rCorrCut: ' + str(test.rCorrCut)
print 'test.rCoordSphereCut: ' + str(test.rCoordSphereCut)
print 'test.signifVarMin: ' + str(test.signifVarMin)
print 'test.perfectCellAtomFocus: ' + str(test.perfectCellAtomFocus)

# --------------------------------------------------- SULFUR VACANCY ---------------------------------------------------
print '\n ------------------------------------\n'
print 'Testing constructor... SULFUR VACANCY...\n'
#Defect cell
C24_VS_q0 = cc.Cell(directory + 'CdIn2S4 - VS/q0/OUTCAR', directory + 'CdIn2S4 - VS/q0/DOSCAR')
#Defect
VS_defect = dc.Defect('Vacancy', ['S (32)'], [-5.13])

VS_defect.set_defect_position(C24_GGA.atoms_positions,C24_VS_q0.atoms_positions)

#Create GeomComparison object
test = dgc.GeomComparison(C24_GGA,VS_defect,C24_VS_q0, None, None, None)

print 'test.perfectCell.name: ' + str(test.perfectCell.name)
print 'test.defectCell.name: ' + str(test.defectCell.name)
#print 'test.defectCell.atoms_positions' + str(test.defectCell.atoms_positions)
print 'test.metrics: \n' + str(test.metrics)
print 'test.rCorrCut: ' + str(test.rCorrCut)
print 'test.rCoordSphereCut: ' + str(test.rCoordSphereCut)
print 'test.signifVarMin: ' + str(test.signifVarMin)
print 'test.perfectCellAtomFocus: ' + str(test.perfectCellAtomFocus)

# ------------------------------------------------ INTERSTITIAL INDIUM -------------------------------------------------
print '\n ------------------------------------\n'
print 'Testing constructor... INTERSTITIAL INDIUM...\n'
C24_IIn_q0 = cc.Cell(directory + 'CdIn2S4 - I_In/q0/OUTCAR', directory + 'CdIn2S4 - I_In/q0/DOSCAR')
IIn_defect = dc.Defect('Interstitial', ['In (17)'], [-2.55])

#Create GeomComparison object
test = dgc.GeomComparison(C24_GGA,IIn_defect,C24_IIn_q0, None, None, None)

print 'test.perfectCell.name: ' + str(test.perfectCell.name)
print 'test.defectCell.name: ' + str(test.defectCell.name)
#print 'test.defectCell.atoms_positions' + str(test.defectCell.atoms_positions)
print 'test.metrics: \n' + str(test.metrics)
print 'test.rCorrCut: ' + str(test.rCorrCut)
print 'test.rCoordSphereCut: ' + str(test.rCoordSphereCut)
print 'test.signifVarMin: ' + str(test.signifVarMin)
print 'test.perfectCellAtomFocus: ' + str(test.perfectCellAtomFocus)

# ------------------------------------------------ FUNCTIONALITIES -------------------------------------------------
print '\n======================================================================\n'
print '			TESTING FUNCTIONALITIES		\n'
print '\n======================================================================\n'

print 'Testing functionalities... SUBSTITUTION...\n'
test = dgc.GeomComparison(C24_GGA,Cd_In_defect,C24_Cd_In_q1, None, None, None)
res = test.defect_geom_analysis()
#print res

print '\n ------------------------------------\n'
print 'Testing functionalities... SULFUR VACANCY...\n'
test = dgc.GeomComparison(C24_GGA,VS_defect,C24_VS_q0, None, None, None)
res= test.defect_geom_analysis()
#print res

print '\n ------------------------------------\n'
print 'Testing functionalities... INTERSTITIAL INDIUM...\n'
test = dgc.GeomComparison(C24_GGA,IIn_defect,C24_IIn_q0, None, None, None)
res = test.defect_geom_analysis()
#print res

d = test.defectCellAtomsCoordinates[1][2]
p = test.perfectCellAtomsCoordinates[1][2]

print 'pefect cell atoms coordinates: '+str(p)
print 'defect cell atoms coordinates: '+str(d)
print 'displacement: '+str(dgc.distance(test.metrics,p,d))

print '\n ------------------------------------\n'
print 'Testing functionalities... EXPORTS...\n'
test.exportAtomDisplacementListToCSV("atoms-displacements-test")
test.exportbondLengthVariationsListToCSV("bond-length-variations-test")
test.exportAtomDisplacementListToDat("atoms-displacements-test")
test.exportbondLengthVariationsListToDat("bond-length-variations-test")
