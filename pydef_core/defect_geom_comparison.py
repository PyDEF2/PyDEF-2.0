"""
    Module used to compare structures before and after defect introduction
    version: 
    author: Adrien Stoliaroff
    email: adrien.stoliaroff@cnrs-imn.fr
"""
import math
import numpy as np

import pydef_core.basic_functions as bf
import pydef_core.cell as cc
import pydef_core.defect as defect


########################################################################
#       Intended use: compare the geometries before/after insertion of a defect
#       (taking into account the fact that atoms are re-numbered after 
#       defect insertion)
# 
#       Prerequisit: the defect cell must have the same parameters as the perfect cell
# 
########################################################################

class GeomComparison:
    """Comparison of host cell and simple defect cell"""
#######################    CONSTRUCTOR AND DESTRUCTOR ##################
    def __init__(self, perfect_cell, defects, defect_cell, r_corr_cut=2.0, r_coord_sphere_cut=7.0, signif_var_min=3.5):
        """Load perfect_cell, defect_cell and parameters user-specified parameters. 
        perfect_cell_atom_focus must be ['Atom type', atom number], ex.: ['Cd',2] 
        param r_corr_cut: (A) Radius used to determine which atom in the defect cell
            corresponds to a given atom in the perfect cell
        param r_coord_sphere_cut: (A) Radius used to build the coordinence spheres
        param signif_var_min: Minimum percentage of bond length variation between
            perfect and defect cell to consider the variation significant"""
        
        self.perfect_cell = perfect_cell
        self.defect_cell = defect_cell
        self.defects = defects
        
        self.r_corr_cut = r_corr_cut
        self.r_coord_sphere_cut = r_coord_sphere_cut
        self.signif_var_min = signif_var_min 
        
        bf.check_cells_consistency(perfect_cell, defect_cell)
        self.metrics = np.transpose(np.matrix(perfect_cell.cell_parameters))
        
        self.perfect_cell_atoms_positions = perfect_cell.atoms_positions
        self.defect_cell_atoms_positions = defect_cell.atoms_positions
        
        # insert reference (former position of atom) in defect cell to enable comparison
        i = 0 
        self.perfect_cell_atom_focus = []
        for defect in self.defects:
            i += 1
            defect.set_defect_position(perfect_cell.atoms_positions,defect_cell.atoms_positions)
            if defect.defect_type=='Vacancy':
                self.defect_cell_atoms_positions.update({'X (%i)' %i:defect.coord}) 
                
                self.perfect_cell_atom_focus.append([defect.atom[0].split()[0], 
                int(defect.atom[0].split(' (')[1].replace(')','')), 
                np.transpose(np.matrix(defect.coord))])
            # insert reference (future position of atom) in perfect cell to enable comparison
            elif defect.defect_type=='Interstitial':
                self.perfect_cell_atoms_positions.update({'X (%i)' %i:defect.coord})
                
                self.perfect_cell_atom_focus.append(['X', 
                i, 
                np.transpose(np.matrix(defect.coord))])
            elif defect.defect_type=='Substitutional':
                self.perfect_cell_atom_focus.append([defect.atom[0].split()[0], 
                int(defect.atom[0].split(' (')[1].replace(')','')), 
                np.transpose(np.matrix(defect.coord))])
        
        self.d_var_header = ['Atom in ' + self.perfect_cell.treetitle,  
                ' Same atom in ' + self.defect_cell.treetitle,
                ' Displacement (A)']
        
        self.inter_a_var_header = ['Bond name \nin perfect cell\n' + self.perfect_cell.treetitle,
                'Corresponding bond\nin defect cell\n' + self.defect_cell.treetitle,
                'Bond length\nbefore defect\nintroduction (A)',
                'Bond length\nafter defect\nintroduction (A)',
                'Absolute difference (0.01A)',
                'Relative difference (%)']
        
#######################    METHODS      ################################
    
    # Get corresponding atom in defect_cell
    def getcorr_atom_in_defect_cell(self, atom):
        i=0
        l=len(self.correspondance_table)
        stop=False
        while (not(stop) and i<l):
            if (atom[0]==self.correspondance_table[i][0][0]
            and atom[1]==self.correspondance_table[i][0][1]
            and np.array_equal(atom[2],self.correspondance_table[i][0][2])):
                    stop=True
                    return self.correspondance_table[i][1]
            i = i+1
                    
    # For test purposes, export correspondance_table in file
    def exportcorrespondance_table(self, argfile):
        for atom_couple in self.correspondance_table:
            argfile.write('\n'+atom_couple[0][0]+str(atom_couple[0][1])+','+
                atom_couple[1][0]+str(atom_couple[1][1])+','+
                str(atom_couple[0][2]).replace('[','').replace(']','').replace('\n',' ')
                +','+
                str(atom_couple[1][2]).replace('[','').replace(']','').replace('\n',' '))
            
    def compare_geom(self):
        """Return atom displacement list(Atom in host cell, Equivalent atom in defect cell, Displacement (A))
        and interatomic distance variations list(Distance name in perfect cell, in defect cell, Interatomic distance before defect introduction, 
        after introduction, Absolute variation (1e-2 A), Relative variation (%) filtered by criteria:
        Relative variation>self.signif_var_min"""
        
#                         0) Load Data                                 # 
        perfect_compound_name = self.perfect_cell.treetitle
        defect_compound_name = self.defect_cell.treetitle

        self.perfect_cell_atoms_coordinates = convert_PyVALENCE_pos_to_list(self.perfect_cell_atoms_positions)
        self.defect_cell_atoms_coordinates = convert_PyVALENCE_pos_to_list(self.defect_cell_atoms_positions)
        # To fractional coordinates (easier to get neighbouring cells, and already implemented)
        self.perfect_cell_atoms_coordinates = toFracCoord(self.perfect_cell_atoms_coordinates,self.metrics)
        self.defect_cell_atoms_coordinates = toFracCoord(self.defect_cell_atoms_coordinates,self.metrics)     

        print 'Comparing Geometry of ' + self.defect_cell.treetitle + ' to host cell (' + self.perfect_cell.treetitle + ')...\n'
        print perfect_compound_name + ': %i atoms loaded from calculation' %len(self.perfect_cell.atoms_positions)
        print defect_compound_name + ': %i atoms loaded from calculation' %len(self.defect_cell.atoms_positions)
        
#              1) Get focus atoms' fractional coordinates              # 
        f_index = -1
        for fspecies, fnum, fcoords in self.perfect_cell_atom_focus:
            f_index += 1
            stop = False
            i = 0
            l = len(self.perfect_cell_atoms_coordinates)
            while not(stop) and i<l:
                atom = self.perfect_cell_atoms_coordinates[i]
                if atom[0] == fspecies and atom[1] == fnum:
                    stop = True
                    self.perfect_cell_atom_focus[f_index][2] = atom[2]
                i = i+1
            
# 2) Build coordinence sphere of the future defect in the perfect cell # 
        
        self.perfect_cell_coord_sphere = []
        
        for fspecies, fnum, fcoords in self.perfect_cell_atom_focus:
            # Perfect cell
            trans_vectList = next_cells(self.metrics, fcoords, self.r_coord_sphere_cut)
            
            for atom0 in self.perfect_cell_atoms_coordinates:
                if distance(self.metrics, fcoords, atom0[2]) < self.r_coord_sphere_cut:
                    self.perfect_cell_coord_sphere.append(atom0)
            self.perfect_cell_coord_sphere = tuple(self.perfect_cell_coord_sphere)
        
#               3) Get correspondance table and atom displacements     # 
        
        self.correspondance_table = []
        
        # Build correspondance table
        for atom0 in self.perfect_cell_coord_sphere:
            trans_vectList = next_cells(self.metrics,atom0[2],self.r_corr_cut)
            trans_vectList.append(np.transpose(np.matrix([0.0,0.0,0.0])))
            for atom1 in self.defect_cell_atoms_coordinates: 
                for trans_vect in trans_vectList:
                    d = distance(self.metrics, atom0[2], atom1[2]+trans_vect)
                    if d<self.r_corr_cut:
                        self.correspondance_table.append([atom0, next_cell_atom(atom1,trans_vect)])
        self.correspondance_table = tuple(self.correspondance_table)
        
        self.defect_cell_atom_focus = self.getcorr_atom_in_defect_cell(self.perfect_cell_atom_focus)
        self.defect_cell_coord_sphere = []
        
        self.atom_displacements = []
        for atom_couple in self.correspondance_table:
            atom=atom_couple[0]
            atom_corr = atom_couple[1]
            self.defect_cell_coord_sphere.append(atom_corr)
            d=distance(self.metrics,atom[2],atom_corr[2])
            self.atom_displacements.append(
            [atom[0]+str(atom[1]),
            atom_corr[0]+str(atom_corr[1]),
            d
            ])
                                                
        message = str(len(self.perfect_cell_coord_sphere))
        message += ' atoms detected in sphere(s) of centre(s) '
        message += ' ' .join([fspecies + '(%i) (%.3f, %.3f, %.3f)'%(fnum, fcoords[0],fcoords[1],fcoords[2]) for fspecies, fnum, fcoords in self.perfect_cell_atom_focus])
        message += ' and radius ' + str(self.r_coord_sphere_cut) + ' A.'
        print message
        print str(len(self.defect_cell_coord_sphere)) + ' corresponding atoms detected in defect cell ' + self.defect_cell.treetitle
                        
        if(len(self.correspondance_table)<len(self.perfect_cell_coord_sphere)):
            message = 'Warning!The correspondance(s) for '
            message += str(len(self.perfect_cell_coord_sphere)-len(self.correspondance_table))
            message += ' atom correspondance(s) could not be determined!'
            print message
        
        print str(len(self.atom_displacements)) + ' atomic displacements after defect introduction computed.\n'

#                  4) Measure interatomic distances variations                   # 
        print 'Measuring interatomic distances variations...'

        self.interatomic_distances_variations = []
        i=0
        j=0
        for atoms_corr_couple in self.correspondance_table:
            i=i+1
            atom0 = atoms_corr_couple[0]# Atom in perfect cell
            atom_corr0 = atoms_corr_couple[1]# Corresponding atom in defect cell
            distances_list = []
            for atom1 in self.perfect_cell_coord_sphere:
                distances_list.append([atom1,distance(self.metrics,atom0[2],atom1[2])])
            distances_list.sort(key=lambda dist: dist[1])
            distances_list = distances_list[1:7]# exclude itself considers max an octahedron
            for atoms_dist in distances_list:
                d_perf = atoms_dist[1]
                try:
                    corr_atom = self.getcorr_atom_in_defect_cell(atoms_dist[0])
                    d_defect = distance(self.metrics,atom_corr0[2],corr_atom[2])
                    var_rel = 100.0*(d_defect-d_perf)/d_perf
                    if(var_rel*var_rel>self.signif_var_min*self.signif_var_min):
                        j = j+1
                        self.interatomic_distances_variations.append(
                            [atom0[0]+str(atom0[1])
                            +'-'+atoms_dist[0][0]+str(atoms_dist[0][1]),
                            atom_corr0[0]+str(atom_corr0[1])
                            +'-'+corr_atom[0]+str(corr_atom[1]),
                            d_perf,
                            d_defect,
                            (d_defect-d_perf)*100,
                            var_rel
                            ])
                except TypeError:
                    message  =  atoms_dist[0][0]+str(atoms_dist[0][1])
                    message += ' has no corresponding atom in the defect cell. Skipped.'
                    print 'Warning! ' + message
                
        print '%i atoms investigated, %i significant interatomic distance variations detected.\n' %(i, j)

        print 'Comparing Geometry of ' + self.defect_cell.treetitle + ' to host cell (' + self.perfect_cell.treetitle + ')... Done'
        
        return self.atom_displacements, self.interatomic_distances_variations

    def export_atom_displacements(self, filename, separator):
        outfile = open(filename, "w")
        outfile.write(separator.join([s.replace('\n','') for s in self.d_var_header])+'\n')
        if separator != ',':
            def ewrite(argfile, arglist):
               outfile.write(str(i).replace('[','').replace(']','\n').replace('\'','').replace(',', separator)) 
        else:
            def ewrite(argfile, arglist):
               outfile.write(str(i).replace('[','').replace(']','\n').replace('\'',''))
        for i in self.atom_displacements:
                ewrite(outfile, i)
        outfile.close()
                
    def export_interatomic_distances_variations(self, filename, separator):
        outfile = open(filename, "w")
        outfile.write(separator.join([s.replace('\n','') for s in self.inter_a_var_header])+'\n')
        if separator != ',':
            def ewrite(argfile, arglist):
               outfile.write(str(i).replace('[','').replace(']','\n').replace('\'','').replace(',', separator)) 
        else:
            def ewrite(argfile, arglist):
               outfile.write(str(i).replace('[','').replace(']','\n').replace('\'',''))
        for i in self.interatomic_distances_variations:
                ewrite(outfile, i)
        outfile.close()

########################################################################
#                         FUNCTION DEFINITIONS                         # 
########################################################################

# Distances     
def distance(basematrix, a, b):
    return math.sqrt(np.transpose(basematrix*(a-b))*basematrix*(a-b))
        
# Convert cartesian coordinates to fractional coordinates
def toFracCoord(atomlist,lattice):
    res = []
    inv = np.linalg.inv(lattice)
    for atom in atomlist:
            res.append([atom[0],atom[1],inv*atom[2]])
    return res
        
########################################################################

# Get to work with the neighbouring cell when necessary

# Return the projection of the given atom on the face axis=face_coord 
# (ex.: x=0)
def proj(atom_coords, axis, face_coord):
    res = []
    k = 0
    for i in atom_coords:
            if k==axis:
                    res.append(float(face_coord))
            else:
                    res.append(float(atom_coords[k]))
            k = k+1
    return np.transpose(np.matrix(res))

# Return the distance between the atom and the face axis=face_coord 
# (ex.: x=0)
# atomCoord must be in fractional coordinates
def distance_to_face(basematrix,atom_coords,axis,face_coord):
    return distance(basematrix,atom_coords,proj(atom_coords,axis,face_coord))  
        
def facetrans(face_coord):
    if face_coord==0: return -1
    elif face_coord==1: return 1
                
# For the argument atom, return the list of translation vectors 
# corresponding to the neighbour supercells to consider when 
# looking at the atom's environment     
def next_cells(basematrix ,atom_coords, rcut):
    res=[]
    for axis in range(3):
        for face_coord in [0,1]:
            if distance_to_face(basematrix,atom_coords,axis,face_coord)<rcut:
                    vec0=np.transpose(np.matrix([0,0,0]))
                    vec0[axis]=facetrans(face_coord)
                    res.append(vec0)
    l=len(res)
    resf=list(res) # makes a copy
    if l>1:
            k=0
            for vect0 in res:
                    for vect1 in res[(k+1):l]:
                            resf.append(vect0+vect1)
                    k=k+1
            if l==3: resf.append(res[0]+res[1]+res[2])
    return resf

# For the argument atom, return the same atom in the neighbouring cell
# specified by the argument translation vector 
def next_cell_atom(atom, trans_vect):
    return [atom[0],atom[1],atom[2]+trans_vect]

########################################################################

# Convert PyVALENCE positions format to convenient format for geom comparison
def convert_PyVALENCE_pos_to_list(atom_pos):
    res=[]
    for atom in atom_pos:
        line=[
                atom.split(' ')[0],# atom type
                int(atom.split('(')[1].replace(')','')),# atom number
                np.transpose(np.matrix(atom_pos[atom]))# atom coordinates as numpy matrix
        ]
        res.append(line)
    return res
