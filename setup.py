import sys
from cx_Freeze import setup, Executable
import os
import sys
path=sys.prefix.replace('\\','/')

pathbin= path +'/Library/bin/'

os.environ['TCL_LIBRARY'] = path + '/tcl/tcl8.6'
os.environ['TK_LIBRARY'] = path + '/tcl/tk8.6'

base = None
if sys.platform == 'win32':
    base = 'Console'
    icon="Pictures/icon.ico"

includes=[ ]   
include_files = ["Pictures/icon.ico","Pictures",('vide','Save-Projects')]

packages = ['mpl_toolkits',"PIL", "numpy", "scipy", "tkinter", "matplotlib"]

if sys.platform == 'win32':
	executables = [
        Executable('main.py', base=base, targetName='PyDEF3.exe', icon="Pictures/icon.ico") 
        ]
	exclude = ['scipy.spatial.cKDTree','sqlite3']
	f=open('couilles.txt','r')
	for line in f:
		file = line[:-1]
		try :
			open(pathbin+file)
			include_files.append(pathbin + file)
		except:
			pass

	include_files = include_files+[path+'/Library/bin/libiomp5md.dll',path+'/Library/bin/mkl_intel_thread.dll']
else:
	exclude = []
	executables = [
        Executable('main.py', base=base, targetName='PyDEF3.exe') 
        ] 

setup(
name = "PyDEF3",
version = "2.1",
description = "A Post-Treatment Software for VASP",
options = {'build_exe':{"packages":packages, "include_files":include_files,'excludes':exclude,'includes':includes}},
executables = executables
)
