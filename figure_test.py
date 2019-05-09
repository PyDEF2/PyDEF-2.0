
import pydef_core.cell as pc
import pydef_core.figure as pf
import figure_windows as fw
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.pyplot as plt

root = tk.Tk()

f = plt.figure(figsize=(15, 9), dpi=100)

canvas = FigureCanvasTkAgg(f, master=root)
canvas.show()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

toolbar = NavigationToolbar2TkAgg(canvas, root)
toolbar.update()
canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

figure = fw.Figure(f, 'my figure')
gga = pc.Cell('./tests/test_files/Functionals/CdIn2S4 - GGA/OUTCAR', './tests/test_files/Functionals/CdIn2S4 - GGA/DOSCAR')
pp = pc.DosPlotParameters(gga)
figure.add_subplot((1, 1, 1), gga, pp)


def open_window(event):
    if event.dblclick:
        fw.FigureWindow(root, figure, canvas)


canvas.mpl_connect('button_press_event', open_window)

tk.mainloop()
