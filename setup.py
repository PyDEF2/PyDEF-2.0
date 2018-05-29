import sys
from cx_Freeze import setup, Executable
import mpl_toolkits.mplot3d

base = None
if sys.platform == 'win32':
    base = 'Win32GUI'
    
include_files = [(mpl_toolkits.mplot3d.__file__,"mpl_toolkits.mplot3d")]

packages = ["PIL", "numpy", "scipy", "tkFileDialog", "Tkinter", "matplotlib"]

executables = [
    Executable('main.py', base=base, targetName='PyDEF2.exe') 
    ] 
    
setup(
    name = "PyDEF2",
    version = "2.0",
    description = "A Post-Treatment Software for VASP",
    options = {'build_exe':{"packages":packages, "include_files":include_files, "includes": ["mpl_toolkits.mplot3d"]}},
    executables = executables
)
