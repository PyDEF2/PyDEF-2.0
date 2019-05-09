import matplotlib
import matplotlib.pyplot as plt
import matplotlib.text


def convert_string_to_pymath(strin):
    """ Convert a string to a 'math' format """

    if strin.strip() is not '':
        return '$' + strin.replace(' ', '\ ') + '$'
    else:
        return strin
        

def get_screen_size():
    """ Return the screen size in inches """
    import tkinter as tk
    root = tk.Tk()
    width = root.winfo_screenmmwidth() * 0.0393701
    height = root.winfo_screenmmheight() * 0.0393701
    root.destroy()
    return width, height


def delete_annotations(*annotations):
    """ Delete a set of matplotlib annotations """

    for element in annotations:
        try:
            element.remove()
        except AttributeError:
            pass


def auto_ax(ax=None):
    """ Return an ax and a figure if ax is None """

    if ax is None:
        figure = plt.figure()
        ax = figure.add_subplot(111)
    figure = ax.get_figure()

    return ax, figure


def set_ax_parameters(ax, title='', xlabel='', ylabel='', xlim=None, ylim=None, legend=True, grid=True, xticks=True,
                      yticks=True, xtick_labels=True, ytick_labels=True, fontsize=24, l_fontsize=24, title_fontsize=24,
                      xlog=False, ylog=False, tight=True, box=False):

    figure = ax.get_figure()

    # Title and labels
    if title.strip() != '':
        ax.set_title(title, y=1.02, fontsize=title_fontsize)
    if xlabel.strip() != '':
        ax.set_xlabel(xlabel, fontsize=fontsize)
    if ylabel.strip() != '':
        ax.set_ylabel(ylabel, fontsize=fontsize)

    # Ax limits
    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)

    # Ticks
    ax.tick_params(axis='both', length=4., width=1.5, pad=10)
    if xticks:
        x_alpha = 1.
    else:
        x_alpha = 0.
    [line.set_alpha(x_alpha) for line in ax.get_xticklines()]

    if yticks:
        y_alpha = 1.
    else:
        y_alpha = 0.
    [line.set_alpha(y_alpha) for line in ax.get_yticklines()]

    # Ticks labels
    if xtick_labels:
        ax.tick_params(labelbottom=True, labelsize=fontsize, length=10)
    else:
        ax.tick_params(labelbottom=False, labelsize=fontsize)

    if ytick_labels:
        ax.tick_params(labelleft=True, labelsize=fontsize, length=10)
    else:
        ax.tick_params(labelleft=False, labelsize=fontsize)

    # Grid
    if grid:
        ax.grid(True)
    else:
        ax.grid(False)

    # Legend
    if legend:
        try:
            ax.legend(fontsize=l_fontsize).set_draggable(True)
        except AttributeError:
            pass
    else:
        try:
            ax.get_legend().remove()
        except AttributeError:
            pass

    # Annotations fontsize
    for child in ax.get_children():
        if isinstance(child, matplotlib.text.Annotation):
            child.set_fontsize(fontsize)
    
    # log scale
    if xlog:
        plt.xscale('log')
    if ylog:
        plt.yscale('log')
        
    if tight:
        figure.tight_layout()
    
    try:
        if len(figure.axes)==1:
            plt.subplots_adjust(left=0.2, bottom=0.2, right=0.9, top=0.9, wspace=0.2, hspace=0.2)
    except ValueError as e:
        print('Sorry, did not manage to resize box...')
    
    if box is False:
        ax.spines['right'].set_color('none')
        ax.spines['top'].set_color('none')

def reorder_legend(ax, labels_order):
    """param labels_order: list of labels in the desired order
    Warning! all labels in labels_roder must be in the initial legend"""
    handles, labels = ax.get_legend_handles_labels()
    leg_dict = dict(list(zip(labels, handles)))

    handles = [leg_dict[label] for label in labels_order]
    ax.legend_.remove()
    ax.legend(handles, labels_order, fontsize=24).set_draggable(True)
    

class PlotParameters(object):

    def __init__(self):
        self.fontsize = 24  # size of the text displayed
        self.l_fontsize = 24  # fontsize of the legends
        self.title = 'Title'  # Title of the plot
        self.display_legends = True
        self.grid = False
        self.name = 'PP name'
        self.x_label = 'X'
        self.y_label = 'Y'
        self.xmin = -10
        self.xmax = 10
        self.ymin = -10
        self.ymax = 10
        self.axes_label_fontsize = 20
        self.title_fontsize = 25
        self.xticks_var = True
        self.xticklabels_var = True
        self.yticks_var = True
        self.yticklabels_var = True
