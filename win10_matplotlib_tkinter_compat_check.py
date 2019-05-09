import tkinter as tk
import matplotlib.pyplot as plt


window = Tk()

frame = tk.Frame(window, bd = 2, bg = 'white', relief = RAISED)
frame.pack()

fig = plt.figure()
ax = fig.add_subplot(111)

ax.plot(list(range(0,10)), list(range(0,10)))

canvas = FigureCanvasTkAgg(fig, master=frame)
canvas.show()
canvas.get_tk_widget().pack(side=TOP, fill= BOTH, expand=1)
self.ctoolbar = NavigationToolbar2TkAgg(canvas, frame)
self.ctoolbar.update()
canvas._tkcanvas.pack(side=TOP, fill= BOTH, expand=True)

window.mainloop()
