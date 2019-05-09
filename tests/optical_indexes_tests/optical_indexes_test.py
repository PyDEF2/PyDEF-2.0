import pydef_core.optical_indices as oi


a = oi.OpticalIndices('./tests/test_files/Optical_indexes/OUTCAR')
b = oi.OpticalIndices('./tests/test_files/Optical_indexes/OUTCAR-1')
a.plot()
