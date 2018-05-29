import ttk
import tkMessageBox as mb
import Tkinter as tk
import tkColorChooser as tcc
from Tkinter import RAISED, END, VERTICAL, RIGHT, LEFT


def centre_window(window):
    """ Centre the window 'window' """

    window.update_idletasks()

    # Screen
    sw = window.winfo_screenwidth()
    sh = window.winfo_screenheight()

    # Window
    ww = window.winfo_width()
    wh = window.winfo_height()

    window.geometry('%dx%d%+d%+d' % (ww, wh, (sw - ww)/2, (wh - sh)/2))


def disable_frame(frame):
    """ Disable all child widgets of frame and all child widgets of its subframes """
    for child in frame.winfo_children():
        if type(child) is ttk.Frame:
            disable_frame(child)
        else:
            child.configure(state='disable')


def enable_frame(frame):
    """ Enable all child widgets of frame and all child widgets of its subframes """
    for child in frame.winfo_children():
        if type(child) is ttk.Frame:
            enable_frame(child)
        else:
            child.configure(state='enable')


class DisplayParametersFrame(tk.Toplevel):

    def __init__(self, parent, X, Y, pp):
        
        cb_kwargs = dict(onvalue=True, offvalue=False)
        frame_kwargs = dict(padx=2, pady=2)

        self.frame = ttk.Frame(parent)
        self.frame.pack(expand=True, fill='both')
        
        display_param_label = tk.Label(self.frame, text='Display parameters', font=('', '16', 'bold'))
        self.main_frame = ttk.LabelFrame(self.frame, labelwidget=display_param_label)
        self.main_frame.pack(expand=True, fill='both')
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.X = X
        self.Y = Y
        
        self.pp = pp
        
        # ---------------------------------------------------- TITLE ---------------------------------------------------

        title_frame = ttk.Frame(self.main_frame)
        title_frame.pack(expand=True, fill='x', **frame_kwargs)
        title_frame.grid_columnconfigure(0, weight=1)

        self.title_var = tk.StringVar(value=pp.title)
        ttk.Label(title_frame, text='Title ').pack(side='left')
        ttk.Entry(title_frame, textvariable=self.title_var, width=50).pack(side='left', expand=True, fill='x')

        # -------------------------------------------------- FONTSIZE --------------------------------------------------
        
        # Title fontsize

        fontsize_frame = ttk.Frame(self.main_frame)
        fontsize_frame.pack(**frame_kwargs)
        fontsize_frame.grid_columnconfigure(0, weight=1)

        self.fontsize_var = tk.IntVar(value=pp.fontsize)
        self.title_fontsize_var = tk.IntVar(value=pp.title_fontsize)
        
        ttk.Label(fontsize_frame, text='Title fontsize ').grid(row=0, column=0)
        tk.Spinbox(fontsize_frame, textvariable=self.title_fontsize_var, width=3, from_=10, to=100).grid(row=0, column=1)
        
        ttk.Label(fontsize_frame, text='General fontsize ').grid(row=0, column=2)
        tk.Spinbox(fontsize_frame, textvariable=self.fontsize_var, width=3, from_=10, to=100).grid(row=0, column=3)
        
        # --------------------------------------------------- LEGEND ---------------------------------------------------

        legend_frame = ttk.Frame(self.main_frame)
        legend_frame.pack(**frame_kwargs)
        legend_frame.grid_columnconfigure(0, weight=1)

        self.legend_var = tk.BooleanVar(value=pp.display_legends)
        self.lfontsize_var = tk.IntVar(value=pp.l_fontsize)

        ttk.Checkbutton(legend_frame, text='Display legend   ', variable=self.legend_var, **cb_kwargs).pack(side='left')
        ttk.Label(legend_frame, text='Legend fontsize').pack(side='left')
        tk.Spinbox(legend_frame, textvariable=self.lfontsize_var, width=3, from_=10, to=100).pack(side='left')

        # ---------------------------------------------------- GRID ----------------------------------------------------

        self.grid_var = tk.BooleanVar(value=pp.grid)
        ttk.Checkbutton(self.main_frame, text='Show grid ', variable=self.grid_var).pack()

        # --------------------------------------------------- X-AXIS ---------------------------------------------------

        x_frame_label = ttk.Label(self.frame, text=X+' axis', font='-weight bold')
        x_frame = ttk.LabelFrame(self.main_frame, labelwidget=x_frame_label)
        x_frame.pack(expand=True, fill='x', **frame_kwargs)
        x_frame.grid_columnconfigure(1, weight=1)

        # xlabel
        self.xlabel_var = tk.StringVar(value=pp.x_label)
        ttk.Label(x_frame, text=X + ' axis label ').grid(row=0, column=0)
        ttk.Entry(x_frame, textvariable=self.xlabel_var).grid(row=0, column=1, sticky='we')

        # X limits
        self.xlim_frame = RangeFrame(x_frame, pp.xmin, pp.xmax, X + ' range', width=5)
        self.xlim_frame.grid(row=1, column=0, columnspan=2)

        # X-ticks
        self.xticks_var = tk.BooleanVar(value=pp.xticks_var)
        ttk.Checkbutton(x_frame, text='Display ' + X + ' axis ticks', variable=self.xticks_var, **cb_kwargs).grid(row=2, column=0, columnspan=2, sticky='w')

        # X-ticks labels
        self.xticklabels_var = tk.BooleanVar(value=pp.xticklabels_var)
        ttk.Checkbutton(x_frame, text='Display ' + X + ' ticks labels', variable=self.xticklabels_var, **cb_kwargs).grid(row=3, column=0, columnspan=2, sticky='w')

        # --------------------------------------------------- Y-AXIS ---------------------------------------------------

        y_frame_label = ttk.Label(self.frame, text=Y+' axis', font='-weight bold')
        y_frame = ttk.LabelFrame(self.main_frame, labelwidget=y_frame_label)
        y_frame.pack(expand=True, fill='x', **frame_kwargs)
        y_frame.grid_columnconfigure(1, weight=1)

        # ylabel
        self.ylabel_var = tk.StringVar(value=pp.y_label)
        ttk.Label(y_frame, text=Y + ' axis label ').grid(row=0, column=0)
        ttk.Entry(y_frame, textvariable=self.ylabel_var).grid(row=0, column=1, sticky='we')

        # Y limits
        self.ylim_frame = RangeFrame(y_frame, pp.ymin, pp.ymax, Y + ' range', width=5)
        self.ylim_frame.grid(row=1, column=0, columnspan=2)

        # Y-ticks
        self.yticks_var = tk.BooleanVar(value=pp.yticks_var)
        ttk.Checkbutton(y_frame, text='Display ' + Y + ' ticks', variable=self.yticks_var, **cb_kwargs).grid(row=2, column=0, columnspan=2, sticky='w')

        # Y-ticks labels
        self.yticklabels_var = tk.BooleanVar(value=pp.yticks_var)
        ttk.Checkbutton(y_frame, text='Display ' + Y + ' ticks labels', variable=self.yticklabels_var, **cb_kwargs).grid(row=3, column=0, columnspan=2, sticky='w')
        
        
    def update_frame(self, pp):
        self.fontsize_var.set(self.pp.fontsize)  # size of the text displayed
        self.lfontsize_var.set(self.pp.l_fontsize)  # fontsize of the legends
        self.title_var.set(self.pp.title)  # Title of the plot
        self.legend_var.set(self.pp.display_legends)
        self.grid_var.set(self.pp.grid)
        self.xlabel_var.set(self.pp.x_label)
        self.ylabel_var.set(self.pp.y_label)
        self.fontsize_var.set(self.pp.axes_label_fontsize)
        self.title_fontsize_var.set(self.pp.title_fontsize)
        self.xticks_var.set(self.pp.xticks_var)
        self.xticklabels_var.set(self.pp.xticklabels_var)
        self.yticks_var.set(self.pp.yticks_var)
        self.yticklabels_var.set(self.pp.yticklabels_var)
        
    
    def write_in_pp(self, pp):
        pp.fontsize = self.fontsize_var.get()  # size of the text displayed
        pp.l_fontsize = self.lfontsize_var.get()  # fontsize of the legends
        pp.title = self.title_var.get()  # Title of the plot
        pp.display_legends = self.legend_var.get()
        pp.grid = self.grid_var.get()
        pp.x_label = self.xlabel_var.get()
        pp.y_label = self.ylabel_var.get()
        pp.axes_label_fontsize = self.fontsize_var.get()
        pp.title_fontsize = self.title_fontsize_var.get()
        pp.xticks_var = self.xticks_var.get()
        pp.xticklabels_var = self.xticklabels_var.get()
        pp.yticks_var = self.yticks_var.get()
        pp.yticklabels_var = self.yticklabels_var.get()
        pp.xmin = self.xlim_frame.low_var.get()
        pp.xmax = self.xlim_frame.high_var.get()
        pp.ymin = self.ylim_frame.low_var.get()
        pp.ymax = self.ylim_frame.high_var.get()


class ItemsChoiceFrame(tk.Toplevel):
    """ Window consisting of two listbox. The listbox on the rights contains elements which are returned
     The list on the left contains elements which are not returned"""

    def grid(self, row=None, column=None, padx=None, pady=None):
        self.main_frame.grid(row=row, column=column, padx=padx, pady=pady)

    def pack(self,expand=None, fill=None, padx=None, pady=None):
        self.main_frame.pack(expand=expand, fill=fill, padx=padx, pady=pady)
    
    def get_choice(self):
        return self.list_on.get(0, END)

    def __init__(self, parent, items, items_on, label_on, label_off, labeltitle):
        """
        :param parent: parent window
        :param items: list of all items
        :param items_on: list of items which are used
        :param label_on: label for the list of used items
        :param label_off: label for the list of non used items
        :param labeltitle: label of the Frame"""

        self.parent = parent
        self.items = items

        self.main_frame = ttk.LabelFrame(parent, labelwidget=labeltitle)

        items_off = list(set(items) - set(items_on))

        # -------------------------------------------------- ITEMS OFF -------------------------------------------------

        self.frame_off = ttk.LabelFrame(self.main_frame, text=label_off)

        self.list_off = tk.Listbox(self.frame_off)  # list containing element not plotted
        self.list_off.config(height=5)
        self.list_off.pack(side='right')
        if (len(items_off) or len(items_on))>5:
            self.yscrollbar_off = ttk.Scrollbar(self.frame_off, orient='vertical')
            self.list_off.pack(side='left', fill='both')
            self.yscrollbar_off.pack(side='right', fill='y')
            self.list_off.config(yscrollcommand=self.yscrollbar_off.set)
            self.yscrollbar_off.config(command=self.list_off.yview)
        for i in items_off:
            self.list_off.insert('end', i)

        self.frame_off.grid(row=0, column=0)

        # ------------------------------------------------- ITEMS ON ---------------------------------------------------

        self.on_frame = ttk.LabelFrame(self.main_frame, text=label_on)

        self.list_on = tk.Listbox(self.on_frame)
        self.list_on.config(height=5)
        self.yscrollbar_on = ttk.Scrollbar(self.on_frame, orient='vertical')
        self.list_on.pack(side='left')
        if (len(items_off) or len(items_on))>5:
            self.yscrollbar_on.pack(side='right', fill='y')
            self.list_on.config(yscrollcommand=self.yscrollbar_on.set)
            self.yscrollbar_on.config(command=self.list_on.yview)
        for i in items_on:
            self.list_on.insert('end', i)

        self.on_frame.grid(row=0, column=2)

        # --------------------------------------------------- BUTTONS --------------------------------------------------

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=0, column=1, padx=5)

        tk.Button(self.button_frame, text='>', command=self.add_selection, bg='grey').pack(side='top', expand='True', fill='both')
        tk.Button(self.button_frame, text='>>', command=self.add_all, bg='grey').pack(side='top', expand='True', fill='both')
        tk.Button(self.button_frame, text='<', command=self.remove_selection, bg='grey').pack(side='top', expand='True', fill='both')
        tk.Button(self.button_frame, text='<<', command=self.remove_all, bg='grey').pack(side='top', expand='True', fill='both')

        self.list_on.bind('<Double-Button-1>', self.remove_selected)  # remove element when double-clicked
        self.list_off.bind('<Double-Button-1>', self.add_selected)  # add item when double-clicked

    def add_selection(self):
        """ Add selected elements to the 'on' list and remove them from the 'off' list """
        selection = self.list_off.curselection()
        if len(selection) != 0:
            for selected in selection:
                items_ids = self.list_off.get(selected)
                self.list_on.insert(0, items_ids)
                self.list_off.delete(selected)

    def remove_selection(self):
        """ Remove selected elements in the 'on' list and add them to the 'off' list """
        selection = self.list_on.curselection()
        if len(selection) != 0:
            for selected in selection:
                items_ids = self.list_on.get(selected)
                self.list_off.insert(0, items_ids)
                self.list_on.delete(selected)

    def add_all(self):
        """ Add all items to the 'on' list and remove them from the 'off' list """
        self.list_off.delete(0, 'end')
        self.list_on.delete(0, 'end')
        [self.list_on.insert(0, f) for f in self.items]

    def remove_all(self):
        """ Remove all items from the 'on' list and add them to the 'off' list """
        self.list_on.delete(0, 'end')
        self.list_off.delete(0, 'end')
        [self.list_off.insert(0, f) for f in self.items]

    def add_selected(self, event):
        """ Add the selected item to the 'on' list and remove it from the 'off' list when "event" happens """
        widget = event.widget
        widget.curselection()
        self.add_selection()

    def remove_selected(self, event):
        """ Add the selected item to the 'off' list and remove it from the 'on' list when "event" happens """
        widget = event.widget
        widget.curselection()
        self.remove_selection()


class ItemsChoiceWindow(tk.Toplevel):
    """ Window consisting of two listbox. The listbox on the rights contains elements which are returned
     The list on the left contains elements which are not returned"""

    def __init__(self, parent, items, items_on, output, label_on, label_off):
        """
        :param parent: parent window
        :param items: list of all items
        :param items_on: list of items which are used
        :param output: string
        :param label_on: label for the list of used items
        :param label_off: label for the list of non used items """

        tk.Toplevel.__init__(self, parent)
        self.resizable(False, False)
        parent.attributes('-topmost', False)
        self.attributes('-topmost', True)

        self.parent = parent
        self.output = output
        self.items = items

        self.main_frame = ttk.LabelFrame(self)
        self.main_frame.pack(expand=True, fill='both')

        items_off = list(set(items) - set(items_on))

        # ------------------------------------------------- ITEMS ON ---------------------------------------------------

        self.on_frame = ttk.LabelFrame(self.main_frame, text=label_on)
        self.on_frame.grid(row=0, column=0)

        self.list_on = tk.Listbox(self.on_frame, width=20)
        self.yscrollbar_on = ttk.Scrollbar(self.on_frame, orient='vertical')
        self.list_on.pack(side='left', fill='both', expand=True)
        self.yscrollbar_on.pack(side='right', fill='y')
        self.list_on.config(yscrollcommand=self.yscrollbar_on.set)
        self.yscrollbar_on.config(command=self.list_on.yview)
        for i in items_on:
            self.list_on.insert('end', i)

        # -------------------------------------------------- ITEMS OFF -------------------------------------------------

        self.frame_off = ttk.LabelFrame(self.main_frame, text=label_off)
        self.frame_off.grid(row=0, column=2)

        self.list_off = tk.Listbox(self.frame_off, width=20)  # list containing element non plotted
        self.yscrollbar_off = ttk.Scrollbar(self.frame_off, orient='vertical')
        self.list_off.pack(side='left', fill='both', expand=True)
        self.yscrollbar_off.pack(side='right', fill='y')
        self.list_off.config(yscrollcommand=self.yscrollbar_off.set)
        self.yscrollbar_off.config(command=self.list_off.yview)
        for i in items_off:
            self.list_off.insert('end', i)

        # --------------------------------------------------- BUTTONS --------------------------------------------------

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=0, column=1, padx=5)

        ttk.Button(self.button_frame, text='>', command=self.remove_selection).pack(side='top')
        ttk.Button(self.button_frame, text='>>', command=self.remove_all).pack(side='top')
        ttk.Button(self.button_frame, text='<', command=self.add_selection).pack(side='top')
        ttk.Button(self.button_frame, text='<<', command=self.add_all).pack(side='top')

        self.list_on.bind('<Double-Button-1>', self.remove_selected)  # remove element when double-clicked
        self.list_off.bind('<Double-Button-1>', self.add_selected)  # add item when double-clicked

        # ------------------------------------------------ MAIN BUTTONS ------------------------------------------------

        self.main_button_frame = ttk.Frame(self.main_frame)
        self.main_button_frame.grid(row=1, column=0, columnspan=3)

        ttk.Button(self.main_button_frame, text='OK', command=self.save).pack(side='left')
        ttk.Button(self.main_button_frame, text='Cancel', command=self.cancel).pack(side='right')

    def add_selection(self):
        """ Add selected elements to the 'on' list and remove them from the 'off' list """
        selection = self.list_off.curselection()
        if len(selection) != 0:
            for selected in selection:
                items_ids = self.list_off.get(selected)
                self.list_on.insert(0, items_ids)
                self.list_off.delete(selected)

    def remove_selection(self):
        """ Remove selected elements in the 'on' list and add them to the 'off' list """
        selection = self.list_on.curselection()
        if len(selection) != 0:
            for selected in selection:
                items_ids = self.list_on.get(selected)
                self.list_off.insert(0, items_ids)
                self.list_on.delete(selected)

    def add_all(self):
        """ Add all items to the 'on' list and remove them from the 'off' list """
        self.list_off.delete(0, 'end')
        self.list_on.delete(0, 'end')
        [self.list_on.insert(0, f) for f in self.items]

    def remove_all(self):
        """ Remove all items from the 'on' list and add them to the 'off' list """
        self.list_on.delete(0, 'end')
        self.list_off.delete(0, 'end')
        [self.list_off.insert(0, f) for f in self.items]

    def add_selected(self, event):
        """ Add the selected item to the 'on' list and remove it from the 'off' list when "event" happens """
        widget = event.widget
        widget.curselection()
        self.add_selection()

    def remove_selected(self, event):
        """ Add the selected item to the 'off' list and remove it from the 'on' list when "event" happens """
        widget = event.widget
        widget.curselection()
        self.remove_selection()

    def save(self):
        """ Save the choice and close the window """
        choice = list(self.list_on.get(0, 'end'))
        if len(choice) == 0:
            mb.showerror('Error', 'You must select at least one item', parent=self)
            return None
        else:
            setattr(self.parent, self.output, choice)
        self.parent.attributes('-topmost', True)
        self.destroy()

    def cancel(self):
        """ Save the initial items on and close the window """
        self.destroy()


class ColoursChoiceWindow(tk.Toplevel):
    """ Window for choosing the color of each item of the plot """

    def __init__(self, parent, items, colors, output):

        tk.Toplevel.__init__(self, parent)
        self.resizable(False, False)
        self.attributes('-topmost', True)

        self.title('Colours selector')
        self.attributes('-topmost', True)
        self.parent = parent
        self.output = output

        self.main_frame = ttk.Frame(self)  # Main ttk frame
        self.main_frame.pack(expand=True, fill='both')

        # dictionary for storing the colors with their associated item
        self.color_dict = dict(zip(items, colors * len(items)))
        self.items = items

        self.combobox = ttk.Combobox(self.main_frame, values=items, state='readonly')
        self.combobox.grid(row=0, column=0, padx=5, pady=3)
        self.combobox.bind('<<ComboboxSelected>>', self.get_color)

        tk.Label(self.main_frame, text='    ').grid(row=0, column=1)
        ttk.Button(self.main_frame, text='color', command=self.set_color).grid(row=0, column=2, padx=5, pady=3)

        # ---------------------------------------------------- BUTTONS -------------------------------------------------

        self.main_button_frame = ttk.Frame(self.main_frame)
        self.main_button_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=3)

        ttk.Button(self.main_button_frame, text='OK', command=self.validate).pack(side='left', padx=5, pady=3)
        ttk.Button(self.main_button_frame, text='Cancel', command=self.destroy).pack(side='right', padx=5, pady=3)

    def get_color(self, event):
        """ Retrieve the color associated with the selected item and display it in a label """
        widget = event.widget
        selected = widget.get()
        color = self.color_dict[selected]
        tk.Label(self.main_frame, text='    ', background=color).grid(row=0, column=1)

    def set_color(self):
        """ Ask for a color and set it to the current item selected and display it"""
        selected = self.combobox.get()
        if selected == '':
            mb.showwarning('Error', 'Select an item first', parent=self)
        else:
            self.attributes('-topmost', False)
            color = tcc.askcolor(self.color_dict[selected])
            self.attributes('-topmost', True)
            if color[1] is not None:
                self.color_dict[selected] = color[1]
                tk.Label(self.main_frame, text='    ', background=color[1]).grid(row=0, column=1)

    def validate(self):
        """ Save the data in the parent window object and close the window """
        choice = [self.color_dict[k] for k in self.items]
        setattr(self.parent, self.output, choice)
        self.parent.attributes('-topmost', True)
        self.destroy()


class RangeFrame(ttk.Frame):

    def __init__(self, parent, low, high, label, unit='', step=None, **kwargs):

        ttk.Frame.__init__(self, parent)

        self.low_var = tk.DoubleVar(value=low)
        self.high_var = tk.DoubleVar(value=high)

        ttk.Label(self, text=label + ': from').pack(side='left')
        ttk.Entry(self, textvariable=self.low_var, **kwargs).pack(side='left')
        ttk.Label(self, text=unit + ' to ').pack(side='left')
        ttk.Entry(self, textvariable=self.high_var, **kwargs).pack(side='left')
        ttk.Label(self, text=unit).pack(side='left')
        if step is not None:
            self.step_var = tk.DoubleVar(value=step)
            ttk.Label(self, text='  Step: ').pack(side='left')
            ttk.Entry(self, textvariable=self.step_var, **kwargs).pack(side='left')
            ttk.Label(self, text=unit).pack(side='left')


class GapInputFrame(tk.Toplevel):
    """ Window for experimental and theoretical gaps input """

    def pack(self, expand=None, fill=None, padx=None, pady=None):
        self.main_frame.pack(expand=expand, fill=fill, padx=padx, pady=pady)
    
    def get_gaps(self):
        outlist = self.listbox.get(0, END)
        def  format_gap(gapentry):
            return float(gapentry.split(' (')[1].replace(' eV)','')), gapentry.split(' (')[0]
        return [format_gap(gapentry) for gapentry in outlist]

    def __init__(self, parent, gap_input_var, labeltitle):

        # tk.Toplevel.__init__(self, parent)
        # self.title('Gaps')
        # self.resizable(False, False)

        self.main_frame = ttk.LabelFrame(parent, labelwidget=labeltitle)
        # self.main_frame.pack(expand=True, fill='both')
        self.main_frame.grid_columnconfigure(0, weight=1)

        # ----------------------------------------------------- INPUT --------------------------------------------------

        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.grid(row=0, column=0, sticky='nswe', padx=3, pady=3)
        self.input_frame.grid_columnconfigure(1, weight=1)

        self.name_var = tk.StringVar()
        self.value_var = tk.DoubleVar()
        self.name_var.set('Experimental gap')

        ttk.Label(self.input_frame, text='Gap Name').grid(row=0, column=0)
        ttk.Entry(self.input_frame, textvariable=self.name_var).grid(row=0, column=1, sticky='we')

        ttk.Label(self.input_frame, text='Value (eV)').grid(row=1, column=0)
        ttk.Entry(self.input_frame, textvariable=self.value_var).grid(row=1, column=1, sticky='we')

        # ---------------------------------------------------- BUTTONS -------------------------------------------------

        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=1, column=0, padx=3, pady=3)

        def add_gap():
            """ Add the gap to the listbox """
            gap_name = self.name_var.get()
            if ';' in gap_name:
                mb.showwarning('Warning', 'The name of the gap cannnot contain the character \';\'')
            else:
                try:
                    gap_value = self.value_var.get()
                except ValueError:
                    raise ValueError('Gap values must be floats!')
                    return None
                gap_id = gap_name + ' (' + str(gap_value) + ' eV)'
                if gap_id not in self.list_content.get():
                    self.listbox.insert('end', gap_id)

        def remove_gap():
            """ Remove the selected gap from the listbox """
            selection = self.listbox.curselection()
            if len(selection) != 0:
                self.listbox.delete(selection[0])

        ttk.Button(self.button_frame, text='Add gap', command=add_gap).grid(row=0, column=0)
        ttk.Button(self.button_frame, text='Remove gap', command=remove_gap).grid(row=0, column=1)

        # ------------------------------------------------------ LIST --------------------------------------------------

        self.list_frame = ttk.Frame(self.main_frame)
        self.list_frame.grid(row=2, column=0, sticky='nswe')

        self.list_content = tk.StringVar()

        self.listbox = tk.Listbox(self.list_frame, listvariable=self.list_content)
        self.listbox.config(height=0)
        if gap_input_var.get().split(';') != ['']:
            [self.listbox.insert(0, f) for f in gap_input_var.get().split(';') if len(f)>0]

        self.yscrollbar = ttk.Scrollbar(self.list_frame, orient='vertical', command=self.listbox.yview)
        self.yscrollbar.pack(side='right', fill='y')

        self.listbox.configure(yscrollcommand=self.yscrollbar.set)
        self.listbox.pack(side='left', fill='both', expand=True)

        # ------------------------------------------------- MAIN BUTTONS -----------------------------------------------

        self.main_button_frame = ttk.Frame(self.main_frame)
        self.main_button_frame.grid(row=3, column=0, padx=3, pady=3)


class CustomNotebook(ttk.Notebook):
    """A ttk Notebook with close buttons on each tab
    From: https://stackoverflow.com/questions/39458337/is-there-a-way-to-add-close-buttons-to-tabs-in-tkinter-ttk-notebook """

    __initialized = False

    def __init__(self, indexes=None, *args, **kwargs):

        if not self.__initialized:
            self.__initialize_custom_style()
            self.__inititialized = True

        kwargs["style"] = "CustomNotebook"
        ttk.Notebook.__init__(self, *args, **kwargs)

        self._active = None
        self.last_closed = None

        if indexes is None:
            self.indexes = []
        else:
            self.indexes = indexes

        self.bind("<ButtonPress-1>", self.on_close_press, True)
        self.bind("<ButtonRelease-1>", self.on_close_release)

    def on_close_press(self, event):
        """Called when the button is pressed over the close button """

        element = self.identify(event.x, event.y)

        if "close" in element:
            index = self.index("@%d,%d" % (event.x, event.y))
            self.state(['pressed'])
            self._active = index

    def on_close_release(self, event):
        """Called when the button is released over the close button """

        if not self.instate(['pressed']):
            return

        element = self.identify(event.x, event.y)
        index = self.index("@%d,%d" % (event.x, event.y))
        if index in self.indexes:
            return

        if "close" in element and self._active == index:
            self.last_closed = self.tab(index, 'text')
            self.forget(index)
            self.event_generate("<<NotebookTabClosed>>")

        self.state(["!pressed"])
        self._active = None

    def __initialize_custom_style(self):

        style = ttk.Style()
        self.images = (
            tk.PhotoImage("img_close", data='''
                R0lGODlhCAAIAMIBAAAAADs7O4+Pj9nZ2Ts7Ozs7Ozs7Ozs7OyH+EUNyZWF0ZWQg
                d2l0aCBHSU1QACH5BAEKAAQALAAAAAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU
                5kEJADs='''),
            tk.PhotoImage("img_closeactive", data='''
                R0lGODlhCAAIAMIEAAAAAP/SAP/bNNnZ2cbGxsbGxsbGxsbGxiH5BAEKAAQALAAA
                AAAIAAgAAAMVGDBEA0qNJyGw7AmxmuaZhWEU5kEJADs='''),)

        style.element_create("close", "image", self.images[0],
                             ("active", "!disabled", self.images[1]), border=8, sticky='')

        style.layout("CustomNotebook", [("CustomNotebook.client", {"sticky": "nswe"})])
        style.map('CustomNotebook.Tab', foreground=[('selected', 'blue')])
        style.layout("CustomNotebook.Tab", [
            ("CustomNotebook.tab", {
                "sticky": "nswe",
                "children": [
                    ("CustomNotebook.padding", {
                        "side": "top",
                        "sticky": "nswe",
                        "children": [
                            ("CustomNotebook.focus", {
                                "side": "top",
                                "sticky": "nswe",
                                "children": [
                                    ("CustomNotebook.label", {"side": "left", "sticky": ''}),
                                    ("CustomNotebook.close", {"side": "left", "sticky": ''}),
                                ]
                            })
                        ]
                    })
                ]
            })
        ])


class ModifiableLabel(ttk.Frame):

    def __init__(self, parent, var, funcs=(None, None), **kwargs):
        """
        :param parent: parent frame or window
        :param var: variable stocking the string
        :param funcs: tuple of two functions called
        :param kwargs: passed to entry and label widgets """

        ttk.Frame.__init__(self, parent)
        self.parent = parent
        self.var = var
        self.funcs = funcs
        self.kwargs = kwargs

        self.label = ttk.Label(self, textvariable=self.var, **self.kwargs)
        self.entry = ttk.Entry(self, textvariable=self.var, **self.kwargs)
        self.label.bind('<Double-Button-1>', self.show_entry)
        self.entry.bind('<Return>', self.show_label)
        self.entry.bind('<FocusOut>', self.show_label)

        self.show_label(None)

    def show_label(self, event):
        """ Display the label """
        self.entry.pack_forget()
        self.label.pack()
        if self.funcs[0] is not None:
            self.funcs[0]()

    def show_entry(self, event):
        """ Display the entry """
        self.label.pack_forget()
        self.entry.pack()
        self.entry.focus()
        if self.funcs[1] is not None:
            self.funcs[1]()

class ScrollableTableFrame(object):
    
    def __init__(self, main_frame, header, summary):
        self.main_frame = tk.Frame(main_frame)
        # create a canvas object and a vertical scrollbar for scrolling it
        vscrollbar = ttk.Scrollbar(self.main_frame, orient=VERTICAL)
        # vscrollbar.pack(fill='y', side=RIGHT, expand=False)
        vscrollbar.grid(row=0, column=1, sticky = 'nse')
        canvas = tk.Canvas(self.main_frame, bd=0, highlightthickness=0,
                        yscrollcommand=vscrollbar.set)
        # canvas.pack(side=LEFT, fill='both', expand=True)
        canvas.grid(row=0, column=0, sticky = 'nsew')
        vscrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor='nw')

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
        canvas.bind('<Configure>', _configure_canvas)
        
        def display(tablecell):
            if type(tablecell) == float:
                return '%.3f' %tablecell
            else:
                return tablecell
        
        j=0        
        for tablecell in header:
            tk.Label(self.interior, text=display(tablecell), relief="ridge", bg='grey', padx=2, font = ('', 16, '')).grid(row=0, column=j, sticky ='nsew')        
            j += 1
        
        nrows = len(summary)
        if nrows >0:
            i = 0 
            for line in summary:
                i += 1
                j = -1
                for tablecell in line:
                    j += 1
                    tk.Label(self.interior, text=display(tablecell), relief="ridge", bg='white', padx=2, font = ('', 16, '')).grid(row=i, column=j, sticky ='nsew')
        self.main_frame.grid(sticky='nsew')


class QuantityEntry(ttk.Frame):

    def __init__(self, parent, quantity, initial_value, unit='', **kwargs):

        ttk.Frame.__init__(self, parent)

        if isinstance(initial_value, float):
            self.var = tk.DoubleVar(value=initial_value)
        elif isinstance(initial_value, int):
            self.var = tk.IntVar(value=initial_value)
        else:
            self.var = tk.StringVar()

        ttk.Label(self, text=quantity).pack(side='left')
        ttk.Entry(self, textvariable=self.var, **kwargs).pack(side='left', padx=1)
        ttk.Label(self, text=unit).pack(side='left')
