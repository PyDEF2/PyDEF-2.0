"""
    Optical indices
    author: Adrien Stoliaroff
    e-mail: adrien.stoliaroff@cnrs-imn.fr
"""

import numpy as np
import matplotlib.pyplot as plt
from  matplotlib.colors import rgb2hex as rgb2hex
from matplotlib.widgets import CheckButtons
import copy

import pydef_core.basic_functions as bf
import pydef_core.figure as pf


def shorten_quantity(quantity):
    if len(quantity) > 1:
        return 'e' + quantity.split()[1]
    else:
        return quantity


class OpticalIndices(object):

    def __init__(self, outcar_file):
        
        if type(outcar_file) == str:
            content = bf.read_file(outcar_file)
        elif type(outcar_file) == list:
            content = outcar_file
        
        self.components = ['XX', 'YY', 'ZZ', 'XY', 'YZ', 'ZX']
        self.quantities = ['epsilon 1', 'epsilon 2', 'n', 'k', 'R']
        self.quantities_labels = ('\epsilon_1', '\epsilon_2', 'n', 'k', 'R')
        self.components_labels = self.components

        algo = bf.grep(content, 'ALGO    =', 0, 'execute GW part')
        if algo == 'CHI':
            self._energy, self._eps1, self._eps2 = extract_rpa(content)
        elif algo is not None and algo.find('GW') > -1:
            self._energy, self._eps1, self._eps2 = extract_ipa_gw(content)
        else:
            self._energy, self._eps1, self._eps2 = extract_ipa(content)

        self._n, self._k, self._r = np.transpose([get_nkr(e1, e2) for e1, e2 in zip(self._eps1, self._eps2)], axes=(1, 0, 2))

        self.data = np.array([self._eps1, self._eps2, self._n, self._k, self._r])
        self.data_dict = dict(zip(self.quantities, self.data))
        self.data_dict_t = dict(zip(self.components, np.transpose(self.data, axes=(1, 0, 2))))
        self.quantities_dict = dict(zip(self.quantities, self.quantities_labels))
        self.components_dict = dict(zip(self.components, self.components_labels))
        self.lastopp = OpticalPlotParameters(self)

    @property
    def energy(self):
        return copy.deepcopy(self._energy)

    def get_data(self, data_id):

        if data_id in self.quantities:
            data = copy.deepcopy(self.data_dict[data_id])
            data_label = self.quantities_dict[data_id]
            return data, data_label, self.components, self.components_labels
        elif data_id in self.components:
            data = copy.deepcopy(self.data_dict_t[data_id])
            data_label = self.components_dict[data_id]
            return data, data_label, self.quantities, self.quantities_labels

    def export(self, filename, separator, data_id):
        
        data_ex = [self.energy]
        names_ex = ['E (eV)']
        for tensorid in self.quantities:
            data, data_label, names, labels = self.get_data(data_id)
            data_ex.append(data)
            names_ex.append(names)
        data_ex = np.transpose(data_ex)
        np.savetxt(filename, data, delimiter=separator, header=separator.join(names_ex), comments='')
        
        print 'Optical indices exported successfully!' 
    
    def plot_tensor(self, tensorid, pp=None, ax=None):
        
        print 'Printing Optical Index '  + tensorid + '...'
        
        if ax is None:
            ax, figure = pf.auto_ax(ax)
        else:
            figure = ax.get_figure()
        if pp is None:
            opp = self.lastopp
        else:
            opp = pp
        
        if tensorid in self.quantities:

            data, data_label, names, labels = self.get_data(tensorid)
            
            split = data_label.split('_')
            if len(split) == 2:
                i = split[1]
                temp_labels = [i + l for l in labels]
                data_label = split[0]

            data_dict = dict(zip(labels, data))
            length = len(labels)
            
            if len(split) == 2:
                key_init_list = [[k, '$' + data_label + '_{' + i + ' ' + k + '}$'] for k in data_dict.keys()]
            else:
                key_init_list = [[k, '$' + data_label + '_{' + k + '}$'] for k in data_dict.keys()]
                
            if opp.trace_only:
                label = r'$\frac{1}{3} tr(' + key_init_list[0][1].replace(key_init_list[0][0], '').replace('$','') + ')$'
                if opp.h_shift != 0:
                    tr = (data_dict['XX'] + data_dict['YY'] + data_dict['ZZ'])/3.
                    if tensorid.find('epsilon') > -1:
                        ax.plot(np.insert(opp.h_shift + self.energy, 0, 0), 
                        np.insert(tr,0,tr[0]), 
                        color=opp.colors[tensorid]['XX'], label=label, lw=3)
                    else:
                        # n,k,r
                        eps1, eps1_label, names1, labels1 = self.get_data('epsilon 1')
                        eps1 = dict(zip(labels1, eps1))
                        ep1 = (eps1['XX'][0] + eps1['YY'][0] + eps1['ZZ'][0])/3.
                        
                        eps2, eps2_label, names2, labels2 = self.get_data('epsilon 2')
                        eps2 = dict(zip(labels2, eps2))
                        ep2 = (eps2['XX'][0] + eps2['YY'][0] + eps2['ZZ'][0])/3.

                        n = np.sqrt(ep1 + np.sqrt(ep1**2 + ep2**2)) / np.sqrt(2)
                        k = np.sqrt(-ep1 + np.sqrt(ep1**2 + ep2**2)) / np.sqrt(2)
                        r = ((n-1)**2+k**2)/((n+1)**2+k**2)
                        val = {'n':n, 'k':k, 'R': r}
                        
                        ax.plot(np.insert(opp.h_shift + self.energy, 0, 0), 
                        np.insert(tr,0,val[tensorid]), 
                        color=opp.colors[tensorid]['XX'], label=label, lw=opp.lw)
                else:
                    ax.plot(self.energy, (data_dict['XX'] + data_dict['YY'] + data_dict['ZZ'])/3., 
                    color=opp.colors[tensorid]['XX'], label=label, lw=opp.lw)
            else:
                key_to_label = dict(key_init_list)
                for key1 in key_to_label.keys():
                    if key1 != 'XX':
                        try:
                            if bf.is_zero(data_dict[key1]):
                                data_dict.pop(key1)
                                print 'Removed ' + data_label + key1 + ' (zero)'
                            else:
                                for key2 in data_dict.keys():
                                    try:
                                        if key1 != key2 and bf.are_equal(data_dict[key1], data_dict[key2]):
                                            sortlist = [key1, key2]
                                            sortlist.sort()
                                            key_to_label[key1] = key_to_label[sortlist[0]] + ' = ' + key_to_label[sortlist[1]]  
                                            data_dict.pop(key2)
                                            print data_label.replace('\\', '') + ' ' + key1 + '==' + key2
                                        elif key1 != key2:
                                            data_label + ' ' + key1 + '!=' + key2
                                    except IndexError, e:
                                        # already popped out
                                        pass
                        except KeyError, e:
                            # already popped out
                            pass
                keylist = data_dict.keys()
                keylist.sort()
                if opp.h_shift != 0:
                    if tensorid.find('epsilon') > -1:
                        lines = [ax.plot(np.insert(opp.h_shift + self.energy, 0, 0), np.insert(data_dict[key],0,data_dict[key][0]), label=key_to_label[key], color=opp.colors[tensorid][key], lw=3) for key in key_to_label if key in keylist] 
                    else:
                        # n,k,r
                        eps1, eps1_label, names1, labels1 = self.get_data('epsilon 1')
                        eps1 = dict(zip(labels1, eps1))
                        
                        eps2, eps2_label, names2, labels2 = self.get_data('epsilon 2')
                        eps2 = dict(zip(labels2, eps2))
                        
                        def n(key):
                           return np.sqrt(eps1[key][0] + np.sqrt(eps1[key][0]**2 + eps2[key][0]**2)) / np.sqrt(2)
                        def k(key):
                            return np.sqrt(-eps1[key][0] + np.sqrt(eps1[key][0]**2 + eps2[key][0]**2)) / np.sqrt(2)
                        def r(key):
                            return ((n(key)-1)**2+k(key)**2)/((n(key)+1)**2+k(key)**2)
                            
                        val = {'n':n, 'k':k, 'R': r}
                        
                        lines = [ax.plot(np.insert(opp.h_shift + self.energy, 0, 0), np.insert(data_dict[key],0,val[tensorid](key)), label=key_to_label[key], color=opp.colors[tensorid][key], lw=3) for key in key_to_label if key in keylist] 
                else:
                    lines = [ax.plot(self.energy, data_dict[key], label=key_to_label[key], color=opp.colors[tensorid][key], lw=3) for key in key_to_label if key in keylist] 
                if len(split) == 2:
                    data_label = split[0] + '_' + i
                             
            pf.set_ax_parameters(ax, title=opp.title, xlabel=opp.x_label, ylabel=opp.y_label, xlim=[opp.xmin, opp.xmax], ylim=[opp.ymin, opp.ymax], legend=opp.display_legends, grid=opp.grid,
                             fontsize=opp.fontsize, l_fontsize=opp.fontsize, xticks=opp.xticks_var, xtick_labels=opp.xticklabels_var, yticks=opp.yticks_var,
                             ytick_label=opp.yticklabels_var, title_fontsize=opp.title_fontsize)
            
            return figure
        else:
            print 'Warning! ' + tensorid + ' is not a valid optical index name!'
        
    def plot(self, pp=None, ax=None):
        if pp is None:
            print 'Default Opp'
            self.lastopp = OpticalPlotParameters(self)
            tensors = self.lastopp.data_id
        
        tensors = pp.data_id
        ax, figure = pf.auto_ax(ax)
        for tensorid in tensors:
            self.plot_tensor(tensorid, pp=pp, ax=ax)
        return figure


def extract_ipa(content):

    tensor_headers = bf.grep(content, "frequency dependent")
    if tensor_headers is not None:
        if len(tensor_headers) == 2:
            index1 = bf.grep(content, "frequency dependent IMAGINARY DIELECTRIC FUNCTION")[0][1]
            index2 = bf.grep(content, "frequency dependent      REAL DIELECTRIC FUNCTION")[0][1]
            index3 = bf.grep(content, "The outermost node ")[0][1]
        elif len(tensor_headers) == 4:
            index1 = tensor_headers[0][1]
            index2 = tensor_headers[1][1]
            index3 = tensor_headers[2][1]
        else:
            print 'Warning! Case not programmed! Are you sure your file is ok?'
        eps2 = bf.fast_stringcolumn_to_array(content[index1 + 3: index2 - 1])
        eps1 = bf.fast_stringcolumn_to_array(content[index2 + 3: index3 - 1])
        return eps1[0], eps1[1:], eps2[1:]
    else:
        print 'Warning! Could not find tensor header in OUTCAR file'

def read_block(block):
        energy_ = float(block[0].split()[1])
        block_data = bf.fast_stringcolumn_to_array(block[1:], False)
        # XX, YY, ZZ, XY, YZ, ZX
        eps1_ = np.array([block_data[0, 0], block_data[1, 2], block_data[2, 4], block_data[1, 0], block_data[2, 2], block_data[0, 4]])
        eps2_ = np.array([block_data[0, 1], block_data[1, 3], block_data[2, 5], block_data[1, 1], block_data[2, 3], block_data[0, 5]])
        return energy_, eps1_, eps2_
        
        
def extract_ipa_gw(content):
    index_beg = bf.grep(content, 'HEAD OF MICROSCOPIC DIELECTRIC TENSOR (INDEPENDENT PARTICLE)')[0][1] + 2
    index_end = bf.grep(content, 'XI_LOCAL:  cpu time')[0][1] - 4
    
    blocks_indices = range(index_beg, index_end, 7)
    data = [read_block(content[index: index+4]) for index in blocks_indices]
    energy = np.array([d[0] for d in data])
    eps1, eps2 = np.transpose([d[1:] for d in data], axes=(1, 2, 0))
    return energy, eps1, eps2
    
    
def extract_rpa(content):
    index_beg = bf.grep(content, 'INVERSE MACROSCOPIC DIELECTRIC TENSOR')[0][1] + 2
    index_end = bf.grep(content, 'screened Coulomb potential')[0][1] - 4

    blocks_indices = range(index_beg, index_end, 7)
    data = [read_block(content[index: index+4]) for index in blocks_indices]
    energy = np.array([d[0] for d in data])
    eps1, eps2 = np.transpose([d[1:] for d in data], axes=(1, 2, 0))
    return energy, eps1, eps2


def get_nkr(eps1, eps2):
    """ Calculate n, k and r from epsilon 1 & 2 """

    n = np.sqrt(eps1 + np.sqrt(eps1**2 + eps2**2)) / np.sqrt(2)
    k = np.sqrt(-eps1 + np.sqrt(eps1**2 + eps2**2)) / np.sqrt(2)
    r = ((n-1)**2+k**2)/((n+1)**2+k**2)

    return n, k, r


class OpticalPlotParameters(pf.PlotParameters):

    def __init__(self, optical_indices):
        
        super(OpticalPlotParameters, self).__init__()
        
        self.components = optical_indices.components
        self.name = 'Default optical plot properties'
        self.data_id = ['epsilon 1', 'epsilon 2', 'n', 'k', 'R']
        self.title = 'Optical indices'
        self.x_label = 'E (eV)'
        self.y_label = 'Optical indices'
        self.lw = 3
        self.xmin = np.min(optical_indices.energy)
        self.xmax = np.max(optical_indices.energy)
        temp = [optical_indices.get_data(tensorid)[0] for tensorid in self.data_id]
        lengthi = len(temp)
        lengthj = len(self.data_id)
        minlist = [min(temp[j][i]) for i in range(0, lengthi) for j in range(0, lengthj)]
        maxlist = [max(temp[j][i]) for i in range(0, lengthi) for j in range(0, lengthj)]
        self.ymin = min(minlist)
        self.ymax = max(maxlist)
        self.colors = {}
        self.trace_only = False # Display only trace of tensors
        self.h_shift = 0
        
        colormaps = ['Reds', 'Blues', 'Greens', 'Oranges', 'Purples', 'Greys']
        
        p = -1
        for q in optical_indices.quantities:
            p += 1
            customcmap = plt.get_cmap(colormaps[p-1])
            self.colors[q] = dict(zip(optical_indices.components, [rgb2hex(customcmap(120+18*i)) for i in range(0, 7)])) 
