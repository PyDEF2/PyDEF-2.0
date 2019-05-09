
import pydef_core.cell as pc
import figure_windows as fw
import Tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import matplotlib.pyplot as plt

root = tk.Tk()

f = plt.figure(figsize=(15, 9), dpi=100)
ax1 = f.add_subplot(211)
ax2 = f.add_subplot(212)
cell = pc.Cell('./test_files/Bands/GGA/OUTCAR', './test_files/Bands/GGA/DOSCAR')
cell.plot_dos(ax1)
cell.plot_band_diagram(ax2)

canvas = FigureCanvasTkAgg(f, master=root)
canvas.show()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

toolbar = NavigationToolbar2TkAgg(canvas, root)
toolbar.update()
canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

def open_window(event):
    if event.dblclick:
        ax = event.inaxes
        fw.SubplotManager(root, ax, canvas)

canvas.mpl_connect('button_press_event', open_window)

tk.mainloop()
