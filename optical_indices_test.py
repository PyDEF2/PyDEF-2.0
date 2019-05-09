import pydef_core.optical_indices as oi
import pydef_core.cell as cc

a = oi.OpticalIndices('./tests/test_files/Optical_indices/OUTCAR')
b = oi.OpticalIndices('./tests/test_files/Optical_indices/OUTCAR-1')
c = cc.Cell('D:/OUTCAR.LOPTICS')

eps1, eps2, n, k, r = a.plot()
"""eps1.show()
eps2.show() 
n.show()
k.show()"""

a.lastopp.plot_energy = True
"""eps11, eps21, n1, k1 = a.plot()
eps11.show()
eps21.show() 
n1.show()
k1.show()"""

c = oi.OpticalIndices('D:/OUTCAR.LOPTICS')
eps1, eps2, n, k, r = c.plot()
# eps1.show()
n.show() 
k.show() 
r.show()

c = cc.Cell('D:/OUTCAR.LOPTICS')

import sys
sys.exit()

import pydef_core.basic_functions as bf

content = bf.read_file('D:/OUTCAR.LOPTICS')
test0 = bf.grep(content, "frequency dependent IMAGINARY DIELECTRIC FUNCTION")
index1 = bf.grep(content, "frequency dependent IMAGINARY DIELECTRIC FUNCTION")[0][1]
index2 = bf.grep(content, "frequency dependent      REAL DIELECTRIC FUNCTION")[0][1]
index3 = bf.grep(content, "The outermost node ")[0][1] # This can be a problem sometime! 
test1 = content[index1 + 4: index2 - 1]
test2 = content[index2 + 4: index3 - 1]

def check(arg, index):
    i = index -1 
    for elt in arg:
        i += 1
        j = -1
        try:
            for e in elt.split():
                float(e)
        except ValueError as err:
            print(str(err) + '\n')
            print('i ' + str(i) + ' ' + str(e))
            
print('index1 ' + str(index1))
print('index2 ' + str(index3))
print('index3 ' + str(index3))
# check(test1)
# check(test2, index2 + 4)

import sys
sys.exit()

eps2 = bf.fast_stringcolumn_to_array(test1)
eps1 = bf.fast_stringcolumn_to_array(test2)


c = oi.OpticalIndices('D:/OUTCAR.LOPTICS')
eps1, eps2, n, k = c.plot()
eps1.show()
c.lastopp.plot_energy = True
eps11, eps21, n1, k1 = c.plot()
eps11.show()
