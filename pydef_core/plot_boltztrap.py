import pickle
import matplotlib.pyplot as plt
import numpy as np

import pydef_core.figure as pf

labels = {'seebeck':'S ($\mu V.K^{-1}$)', 
'sigma': r"$\sigma/ \tau (1.10^{20}\Omega^{-1}.m^{-1}.s^{-1})$", 
'kappa': r"$\kappa^{elec}/\tau (1.10^{15}W.m^{-1}.K^{-1}.s^{-1})$", 
'ZT': 'ZT', 'mu': r'$\mu$ (eV)', 'T': 'T (K)', 
'eta': r'$\eta$ $(cm^{-3})$'}

factors = {'seebeck': 1e6, 'sigma': 1e-20, 'kappa': 1e-15, 'ZT':1}
components_slice = {'xx': '[0, :, 0, 0]', 
'yy': '[0, :, 1, 1]', 'zz': '[0, :, 2, 2]',
'xy': '[0, :, 0, 1]', 'xz': '[0, :, 0, 2]',
'yz': '[0, :, 1, 2]'}
    
def plot_boltztrap(boltztrap_data, x_axis, y_axis, temperature, pp, trace_only=True, components=[], ax=None, label=None, volume=None):
#        """ Plot the selected transport properties
#        :param ax: matplotlib ax object
#        :param x_axis: 'mu' (chemical potential of the rigid band model), 'n' (charge carrier concentration) 
#        :param y_axis: 'seebeck', 'sigma', 'kappa', 'ZT', 'n'
#		:param pp: plot_parameters"""
		
		
		ax, figure = pf.auto_ax(ax)
		x = boltztrap_data[temperature][x_axis]
        # convert x from (1/unit cell) into (1/cm3) if necessary
		if volume is not None and x_axis == 'n':
			x = boltztrap_data[temperature][x_axis]/volume*1e24
		if trace_only:
			y = eval('(boltztrap_data[temperature][y_axis][0, :, 0, 0] + boltztrap_data[temperature][y_axis][0, :, 1, 1] + boltztrap_data[temperature][y_axis][0, :, 2, 2])/3')
			line = ax.plot(x, y*factors[y_axis])[0] #, linestyle=pp.linestyle, lw=pp.lw)
			if label is not None:
				line.set_label(label)
		else:
			for component in components:
				line = ax.plot(x, 
				boltztrap_data[temperature][components_slice[component]]*factors[y_axis], 
				linestyle=linestyle, lw=lw)[0]
				if label is not None:
					line.set_label(label)
		pf.set_ax_parameters(ax, title='', xlabel=labels[x_axis], ylabel=labels[y_axis], tight=False, grid=False, box=False)     
                
# aggregate by T ?        
# def plot_boltztrap_vs_T(boltztrap_data, y_axis, components, trace_only=False, ax=None, label=None, linestyle=None, volume=None, legend=True, xlog=False):
