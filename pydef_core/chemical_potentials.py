"""
    Chemical Potentials
    version: 2.0
    author: Adrien Stoliaroff
    email: adrien.stoliaroff@cnrs-imn.fr
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import scipy.optimize as sco
import math

import pydef_core.figure as pf


def getVal(key, argdict):
    """auxiliary function: return the value associated with key in argdict, 0 if key is not a key of argdict"""
    try:
        return argdict[key]
    except KeyError:
        return 0
        
        
def niceSub(val):
    """auxiliary function to have a nice inequation plot"""
    if val > 0:
        return "-" + str(val)
    elif val <0:
        return "+" + str(-val)
            
            
def get_formation_enthalpy(compound, chem_pot):
    """ Compute the formation enthalpy of a compound given a set a chemical potentials
     :param compound: Cell object of the compound of which the formation enthalpy is computed
     :param chem_pot: Cell objects of calculation of one atomic species system """

    formation_enthalpy = compound.total_energy
    
    for chem in chem_pot:  # for each atomic species...
        try:
            nb_at_compound = float(compound.population[chem])  # number of atoms of this atomic species in the compound
        except KeyError:
            nb_at_compound = 0
        mu = float(chem_pot[chem])
        print chem + ': mu0 = ' + str(mu) + ' eV, nb_at_compound = ' + str(nb_at_compound)
        formation_enthalpy -= nb_at_compound * mu
    
    return formation_enthalpy
    

class ChemicalPotentials(object):
    """Object containing the information related to chemical potential calculations"""
    
    def add_non_synthesized(self, cell):
        self.non_synthesized[cell.ID] = cell

    def __init__(self, hostCell):
        """constructor"""
        self.synthesized = hostCell
        self.domainInequationsList = []
        self.non_synthesized = {}
        self.synth_population = len(self.synthesized.population)
        self.lastppp = None

    # ------------------------------------------------------ PLOT ------------------------------------------------------
    
    def plot_stability_domain(self, ax=None, ppp=None, tight=True):
        """Plot the stability domain of synthesized material (cell object) in mu_A x mu_B plane 
        (if more than 3 elements in the material of interest, on a mu_Y axis if only 2) taking into account
        the competing formation of non_synthesized materials (list of cell objects). 
        The potential of the element const
        is constrained by the formation energy equation of the studied compound. """
        
        if ax is None:
            ax, figure = pf.auto_ax(ax)
        else:
            figure = ax.get_figure()
        if ppp is None:
            self.lastppp = PotentialsPlotParameters(self)
        else:
            self.lastppp = ppp
            
        chem_pot_dict = self.lastppp.chem_pot_dict
            
        frontierList = []
        self.lastppp.constrainEquation = self.writeConstrainEquation(self.lastppp.mu_X_axis, self.lastppp.mu_Y_axis, self.lastppp.const, chem_pot_dict)
        self.domainInequationsList = []
        
        self.lastppp.domainInequationsList = []
        
        for nonSynCell in self.non_synthesized.values():
            stoechratios_list = self.getStoechiometricRatios(nonSynCell, self.lastppp.mu_X_axis, self.lastppp.mu_Y_axis, self.lastppp.const) #CHECK: OK
            # print nonSynCell.display_rname + " " + str(stoechratios_list)
            a_X, a_Y, C = self.calculateInequationCoeffs(nonSynCell, stoechratios_list, chem_pot_dict)
            # print 'a_X, a_Y, C: ' + str(a_X) + ";" + str(a_Y) + ";" + str(C)
            frontier, aboveStabDom, ineq = self.defineDomain(self.lastppp.mu_X_axis, self.lastppp.mu_Y_axis, a_X, a_Y, C)
            frontierList.append([nonSynCell.display_rname, frontier, aboveStabDom])
            self.lastppp.domainInequationsList.append(ineq + " (Competition with " + nonSynCell.rname + ")")
        
        if self.synth_population == 2:
            self.plot1D(ax, self.lastppp, frontierList, self.lastppp.delta)
            legend = True
        else:
            legendList = self.plot2D(ax, self.lastppp, frontierList, self.lastppp.delta)
            legend = False
        pf.set_ax_parameters(ax, title=self.lastppp.title, l_fontsize=self.lastppp.l_fontsize, 
            grid=self.lastppp.grid, fontsize=self.lastppp.fontsize,
            title_fontsize=self.lastppp.title_fontsize, legend=legend, tight=tight, box=True)
            
        if self.synth_population > 2:
			ax.legend(handles=legendList, fontsize=self.lastppp.l_fontsize).draggable()
        return figure 
            
    # ------------------------------------------------------ EXPORTS ------------------------------------------------------
    
    def exportDomainSummitsToCsv(self, filename, ppp, delim):
        """delim = ',' or '\t'"""
        mu_X_axis = ppp.mu_X_axis
        mu_Y_axis = ppp.mu_Y_axis
        
        extension = ''
        # if delim == ',' or delim == ';':
        #     extension = '.csv'
        if len(self.synthesized._population)>2:
            np.savetxt(filename + extension, self.domainSummits, delimiter = delim, header = 'mu_' + mu_X_axis + delim + "mu_" + mu_Y_axis, comments = '')
        else:
            np.savetxt(filename + extension, self.domainSummits, delimiter = delim, header = "mu_" + mu_Y_axis, comments = '')
    
    def exportDomainToTxt(self, filename):
        outfile = open(filename + '.txt', 'w')
        outfile.write(self.lastppp.constrainEquation + "\n")
        for ineq in self.lastppp.domainInequationsList: 
            outfile.write(ineq + "\n")
        outfile.close()
        
    # --------------------------------------------- AUXILIARY FUNCTIONS ------------------------------------------------------
    
    def plot1D(self, ax, ppp, frontierList, delta):
        """:param  ppp: PotentialsPlotParameters
        :param frontierList: list of 3-elements lists: frontier functions, competing compound name, above/under stability domain boolean
        :param ax: matplotlib ax object
        :param delta: boolean (for the text of the axis)"""

        xfrontiersunder = []
        xfrontiersabove = []
        
        mu_Y_axis = ppp.mu_Y_axis
        colorList = ppp.colorList
        
        xfrontiers = [item[1](0) for item in frontierList]
        
        for name, frontier, aboveStabDom in frontierList:
            if aboveStabDom:
                xfrontiersabove.append([name,frontier(0)])
            else:
                xfrontiersunder.append([name,frontier(0)])
        stabdomainl = max(xfrontiersunder, key=lambda x: x[1])[1]
        stabdomainr = min(xfrontiersabove, key=lambda x: x[1])[1]
        
        xfrontiersunder.sort(key=lambda x: x[1])
        xfrontiersabove.sort(key=lambda x: x[1], reverse = True)
        
        xmin = min(xfrontiers) - 1
        xmax = 0
        
        meml = xmin
        memr = xmax
        
        # Draw domains under the stability domain of the studied compound
        length = len(xfrontiersunder)
        for i in range(length):
            self.draw1Ddomain(ax, meml, xfrontiersunder[i][1], 2, xmin, xmax, xfrontiersunder[i][0], False, ppp.colors[xfrontiersunder[i][0]])
            meml = xfrontiersunder[i][1]
        
        # Draw domains above the stability domain of the studied compound
        length = len(xfrontiersabove)
        for i in range(length):
			self.draw1Ddomain(ax, xfrontiersabove[i][1], memr, 2, xmin, xmax, xfrontiersabove[i][0], False, ppp.colors[xfrontiersabove[i][0]])
			memr = xfrontiersabove[i][1]
        # Stability domain
        self.draw1Ddomain(ax, stabdomainl, stabdomainr, 2, xmin, xmax, self.synthesized.display_rname, ppp.hashed, 'white')
        self.domainSummits = np.array([stabdomainl, stabdomainr])
        
        if delta:    
            ax.set_xlabel('$\Delta \mu_{%s} (eV)$' % mu_Y_axis, fontsize=ppp.fontsize)
        else:
            ax.set_xlabel('$\mu_{%s} (eV)$' % mu_Y_axis, fontsize=ppp.fontsize)
        
        
    def draw1Ddomain(self, ax, xl, xr, height, xmin, xmax, compoundName, hashed, color):
        if hashed == True :
            h = "/"
        else:
            h = ""
        # print compoundName+" "+str(max(xmin, xl ))+ ", "+str(min(xmax, xr )) + ", "+ str(min(xmax, xr )-max(xmin, xl ))
        rect = patches.Rectangle(
                (max(xmin, xl ), -0.5*height),   # (x,y)
                min(xmax, xr )-max(xmin, xl ),    # width
                height,                          # height
                alpha = 0.5,
                edgecolor = "black",
                hatch = h,
                facecolor = color
            )
        rect.set_label('$' + compoundName + '$')
        ax.add_patch(rect)
        ax.text(0.5*(min(xmax, xr ) + max(xmin, xl )), 0.1*height , '$'  +compoundName + '$', fontsize=16)
        ax.set_xlim(xmin,xmax)
        ax.set_ylim(-height,height)
        ax.axes.get_yaxis().set_visible(False)
        
            
    def plot2D(self, ax, ppp, frontierList, delta):
        
        mu_X_axis = ppp.mu_X_axis
        mu_Y_axis = ppp.mu_Y_axis
        colors = ppp.colors
        
        # determine ymin, ymax
        if ppp.autoscale:
            extrval = []
            for name, frontier, aboveStabDomain in frontierList:
                try:
                    extrval.append(frontier(ppp.xmin))
                    extrval.append(frontier(ppp.xmax))
                except TypeError:
                    # vertical frontier: the frontier is a float, not a function
                    extrval.append(frontier)
            ppp.ymin = min(extrval)
            ppp.ymax = max(extrval)

        # autoscale
        k = 0
        length = len(colors)
        lf = len(frontierList)
        crossingPoints = []

        for name1, frontier1, aboveStabDomain1 in frontierList:
            for name2, frontier2, aboveStabDomain2 in frontierList[k+1:lf]:
                try:
                    crossPt = self.get_lines_crossing_point(frontier1, frontier2, ppp.xmin, ppp.xmax)
                    crossingPoints.append(crossPt)
                except ValueError:
                    pass
            k += 1

        domainSummits = [pt for pt in crossingPoints if self.isInDomain(pt, frontierList)]
        domainSummitsX = [pt[0] for pt in domainSummits]
        domainSummitsY = [pt[1] for pt in domainSummits]
        
        if ppp.autoscale:
            try:
                ppp.xmin, ppp.xmax = min(domainSummitsX) - 0.5, max(domainSummitsX) + 0.5
                ppp.ymin, ppp.ymax = min(domainSummitsY) - 0.5, max(domainSummitsY) + 0.5
            except ValueError, e:
                raise ValueError(host.rname + ' Stability Domain Plot: \nNo Domain Summit found in proposed range! You may try a larger range.')
        
        X_axis_sampling = np.linspace(ppp.xmin, ppp.xmax, 1000)
        
        # plot forbidden domains
        k = 0
        legendList = []
        for name, frontier, aboveStabDomain in frontierList:
            yfrontierPoints = []
            key = name.replace('_','').replace('{', '').replace('}','')
            try:
                for x in X_axis_sampling:
                    yfrontierPoints.append(frontier(x))
                ax.plot(X_axis_sampling, yfrontierPoints, '-', color='black')
                if aboveStabDomain:
                    ax.fill_between(X_axis_sampling, yfrontierPoints, ppp.ymax, alpha=0.5, facecolor=colors[key])
                else:
                    ax.fill_between(X_axis_sampling, ppp.ymin, yfrontierPoints, alpha=0.5, facecolor=colors[key])
            except TypeError:
                # vertical frontier is a float, not a function
                ax.plot([frontier, frontier], [ppp.ymin, ppp.ymax], '-', color='black')
                if aboveStabDomain:
                    ax.fill_between([frontier, ppp.xmax], ppp.ymin, [ppp.ymax, ppp.ymax], alpha=0.5, facecolor=colors[key])
                else:
                    ax.fill_between([ppp.xmin, frontier], ppp.ymin, [ppp.ymax, ppp.ymax], alpha=0.5, facecolor=colors[key])
            
            legendList.append(patches.Patch(color=colors[key], alpha=0.5, label='$' + name + '$')) 
            k +=1
        
        if ppp.display_summits:
            ax.plot(domainSummitsX, domainSummitsY, 'ro')
        
        hashed = ""
        if ppp.hashed:
            # https://stackoverflow.com/questions/10846431/ordering-shuffled-points-that-can-be-joined-to-form-a-polygon-in-python
            # J. O'Rourke, "Uniqueness of orthogonal connect-the-dots", Computational Morphology, G.T. Toussaint (editor), Elsevier Science Publishers, B.V.(North-Holland), 1988, 99-104
            # compute centroid
            cent = (sum([p[0] for p in domainSummits])/len(domainSummits),sum([p[1] for p in domainSummits])/len(domainSummits))
            # sort by polar angle
            domainSummits.sort(key=lambda p: math.atan2(p[1]-cent[1], p[0]-cent[0]))
            hashed = "/"
        
        ppp.domainSummits = np.array(domainSummits)
        
        stabilityDomain = patches.Polygon(domainSummits, closed=True, hatch=hashed, facecolor='white')
        ax.add_patch(stabilityDomain)
        legendList.append(patches.Patch(linestyle='solid', edgecolor='black', facecolor='white', hatch=hashed, label='$' + self.synthesized.display_rname + '$'))
        
        if delta:    
            ax.set_xlabel('$\Delta \mu_{%s} (eV)$' % mu_X_axis, fontsize=ppp.fontsize)
            ax.set_ylabel('$\Delta \mu_{%s} (eV)$' % mu_Y_axis, fontsize=ppp.fontsize)
        else:
            ax.set_xlabel('$\mu_{%s} (eV)$' % mu_X_axis, fontsize=ppp.fontsize)
            ax.set_ylabel('$\mu_{%s} (eV)$' % mu_Y_axis, fontsize=ppp.fontsize)
        # ax.set_title('Stability domain of $' + str(self.synthesized.display_rname) + '$', fontsize = ppp.title_fontsize)
        ax.set_xlim(ppp.xmin, ppp.xmax)
        ax.set_ylim(ppp.ymin, ppp.ymax)
        
        return legendList
        
    def isInDomain(self, pt, frontierList):
        """:param pt: a (X,Y) point
        :param frontierList: a str x function x boolean list for name, frontier, above stability domain"""
        res = True
        k = 0
        length = len(frontierList)
        while res and k < length:
            name, frontier, aboveStabDomain = frontierList[k]
            if aboveStabDomain:
                try:
                    res = pt[1] <= frontier(pt[0]) + 0.01
                except TypeError:
                    #vertical frontier
                    res = pt[0] <= frontier + 0.01
            else:
                try:
                    res = pt[1] >= frontier(pt[0]) - 0.01
                except:
                    #vertical frontier is a float
                    res = pt[0] >= frontier - 0.01
            k += 1
        return res
        
    def get_lines_crossing_point(self, func1, func2, xmin, xmax):
        """ Return the point where two lines cross"""
        if type(func1) == type(0.0):
            if type(func2) != type(0.0):
                return [func1, func2(func1)]
        elif type(func2) == type(0.0):
            if type(func1) != type(0.0):
                return [func2, func1(func2)]
        else:
            x0 = sco.brentq(lambda x: func1(x) - func2(x), xmin, xmax)
            return [x0, func1(x0)]
            
        
    def writeConstrainEquation(self, mu_X_axis, mu_Y_axis, const, chem_pot_dict):
        n_list = self.getStoechiometricRatios(self.synthesized, mu_X_axis, mu_Y_axis, const)
        if self.synth_population > 2:
            equation = "mu_" + const + "=-" + str(round(n_list[0]/float(n_list[4]), 3)) + "mu_" + mu_X_axis + "-" + str(round(n_list[2]/float(n_list[4]), 3)) + "mu_" + mu_Y_axis
        else:
            equation = "mu_" + const + "=-" + str(n_list[2]/float(n_list[4])) + "mu_" + mu_Y_axis
        constant = (self.synthesized.total_energy-self.calculateNiMuiSums(self.synthesized, chem_pot_dict)[0])/float(n_list[4])
        if constant >=0:
            equation = equation + "+" + str(round(constant, 3))
        else:
            equation = equation + str(round(constant, 3))
        return equation
        
                
    def getStoechiometricRatios(self, nonsynthesized, X, Y, const):
        """ex.: getStoechiometricRatios(CdIn2S4_cell, CdS, 'Cd', 'In', 'S') returns 1,2,4,1,0,1"""
        res = []
        for elt in [X, Y, const]:
            res.append(getVal(elt, self.synthesized.population))
            res.append(getVal(elt, nonsynthesized.population))
        return res
        
    
    def calculateNiMuiSums(self, nonsyncell, chem_pot_dict):
        if self.synth_population <= 3:
            return [0,0]
        else:
            sumSyn = 0
            sumNonSyn = 0
            for elt in chem_pot_dict.keys():
                sumSyn += getVal(elt, self.synthesized.population)*chem_pot_dict[elt]
                sumNonSyn += getVal(elt, nonsyncell.population)*chem_pot_dict[elt]
            return [sumSyn, sumNonSyn]
            
    
    def calculateInequationCoeffs(self, nonsyncell, n_list, chem_pot_dict):
        """Calculate the inequation coefficients given the non synthesized cell, the list of stoechiometric ratio of user-chosen elements 
        and a dictionary of fixed potentials for the remaining N - 3 elements of the material of interest"""
        a_X = float(n_list[1] * n_list[4] - n_list[0] * n_list[5])
        a_Y = float(n_list[3] * n_list[4]-n_list[2] * n_list[5])
        sumSyn, sumNonSyn = self.calculateNiMuiSums(nonsyncell, chem_pot_dict)
        
        try:
            C = float(n_list[4] * (get_formation_enthalpy(nonsyncell, chem_pot_dict) - sumSyn) - n_list[5] * (get_formation_enthalpy(self.synthesized, chem_pot_dict) - sumNonSyn))
        except TypeError, e:
            message = 'Warning! ' + nonsyncell.treetitle
            message += ' is not an energy calculation, it will not be included in the '
            message += 'Domain Stability plot. It is strongly advised to remove it from Chemical Potentials object'        
            print message
            return a_X, a_Y, 0
        
        return a_X, a_Y, C
        
        
    def defineDomain(self, mu_X_axis, mu_Y_axis, a_X, a_Y, C):
        """return the frontier as a function of mu_X (a single mu_X float value in case of a vertical frontier),
        True for forbidden domain above the stability domain of the material of interest
        and the inequation as a string"""
        if a_Y > 0:
            ineq = "mu_" + mu_Y_axis + "<=" + str(round(C/a_Y, 3)) 
            if a_X != 0:
                ineq = ineq + niceSub(a_X/a_Y) + "mu_" + mu_X_axis
            return lambda x: (C-a_X*x)/a_Y, True, ineq
        elif a_Y < 0:
            ineq = "mu_" + mu_Y_axis + ">=" + str(round(C/a_Y, 3))
            if a_X != 0:
                ineq = ineq + niceSub(a_X/a_Y) + "mu_" + mu_X_axis
            return lambda x: (C-a_X*x)/a_Y, False, ineq
        else:
            if(a_X > 0): 
                ineq = "mu_" + mu_X_axis + "<=" + str(round(C/a_X, 3))
                return C/a_X, True, ineq
            elif (a_X < 0):            
                ineq = "mu_" + mu_X_axis + ">=" + str(round(C/a_X, 3))
                return C/a_X, False, ineq
            else:
                print 'Warning! Division by zero avoided by ignoring one frontier!'
                return 0, False, ''


class PotentialsPlotParameters(pf.PlotParameters):
    """ Parameters for plotting the Stability Domain of a ChemicalPotentials object """

    def __init__(self, chem_pot):
        
        super(PotentialsPlotParameters, self).__init__()

        self.name = chem_pot.synthesized.rname + ' stability domain (' 
        self.chem_pot = chem_pot
        self.mu_X_axis = chem_pot.synthesized.atoms_types[0]
        if chem_pot.synth_population == 2:
            self.mu_Y_axis = chem_pot.synthesized.atoms_types[0]
            self.mu_X_axis = ''
            self.const = chem_pot.synthesized.atoms_types[1]
            self.name += self.mu_Y_axis + ')'
        else:
            self.mu_Y_axis = chem_pot.synthesized.atoms_types[1]
            self.const = chem_pot.synthesized.atoms_types[2]
            self.name += self.mu_X_axis + ', ' + self.mu_Y_axis + ')'
        
        self.domainSummits = [] 
        self.constrainEquation = ""
        self.domainInequationsList = []
        
        self.colorList = ['red', 'blue', 'green', 'yellow', 'orange', 'aqua', 'magenta', 'olive' ]
        
        self.colors = dict(zip([cell.rname for cell in chem_pot.non_synthesized.values()], self.colorList))
        
        self.title = 'Stability domain of $' +  chem_pot.synthesized.display_rname + '$' # Title of the plot
        self.hashed = True
        self.display_summits = True
        self.ymin = -5
        self.xmax = 0
        self.ymax = -2
        self.autoscale = True
        self.delta = False
        self.chem_pot_dict = {}
    
