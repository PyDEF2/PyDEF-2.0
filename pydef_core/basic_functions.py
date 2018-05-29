import numpy as np
import fractions
import copy
import os


# -------------------------------------------------- PYVALENCE EXCEPTIONS --------------------------------------------------

class PyVALENCEImportError(Exception):
    """ Error raised when there is an error when importing the data """
    pass


class PyVALENCEOutcarError(Exception):
    """ Error raised when the given OUTCAR file is not a valid OUTCAR file """
    pass


class PyVALENCEDoscarError(Exception):
    """ Error raised when the given DOSCAR file is not consistent with the OUTCAR file """
    pass

class PyVALENCEDefectCreationError(Exception):
    """ Error raised when the user has not specified the Defects parameters correctly (GUI)"""
    pass

class PyVALENCESolveError(Exception):
    """ Error raised when an iterative equation solving scheme fails"""
    pass

class PyVALENCEInputError(Exception):
    pass

# ------------------------------------------------------ FUNCTIONS -----------------------------------------------------


def read_file(filename):
    """ Return the content of a file as a list of strings, each corresponding to a line
    :param filename: string: location and name of the file
    :return: content of filename
    """
    with open(filename, 'r') as ofile:
        content = ofile.read().splitlines()
    return content


def grep(content, string1, line_nb=False, string2=False, data_type='str', nb_found=None, delimiter=''):
    """ Similar function to the bash grep
    :param content: list of strings
    :param string1: string after which the data is located. if the string is in a list, only locate this specific string
    :param line_nb: amongst the lines which contains 'thing', number of the line to be considered
    :param string2: string before which the data is located
    :param data_type: type of the data to be returned
    :param nb_found: exact number of 'string1' to be found
    :param delimiter: if different than empty string, it is used to separate the elements found in the string

    Examples:
    >>> content = ['my first line', 'my second line', 'this number is 3']
    >>> grep(content, 'first')
    [['my first line', 0]]
    >>> grep(content, 'first', 0)
    'line'
    >>> grep(content, 'my', 1, 'line', nb_found=2)
    'second'
    >>> grep(content, 'number is', 0, data_type='int', nb_found=1)
    3"""
    if type(string1) is list:
        found = [[f, g] for f, g in zip(content, range(len(content))) if string1[0] == f]
    else:
        found = [[f, g] for f, g in zip(content, range(len(content))) if string1 in f]

    if len(found) == 0:
        return None  # Return None if nothing was found

    if isinstance(nb_found, int):
        if len(found) != nb_found:
            # raise AssertionError()
            print 'Warning! Found ' + str(len(found)) + ' times \"' + string1 + '\" instead of ' + str(nb_found) + ' as expected'

    if line_nb is False:
        # print('%s elements found' % len(found))
        return found
    else:
        line = found[line_nb][0]

        if string2 is False:
            value = line[line.find(string1) + len(string1):]
        else:
            index_beg = line.find(string1) + len(string1)
            index_end = line[index_beg:].find(string2) + index_beg
            value = line[index_beg: index_end]

        if delimiter is not '':
            values = value.split(delimiter)
            if data_type == 'float':
                return [float(v) for v in values]
            elif data_type == 'int':
                return [int(float(v)) for v in values]
            else:
                return values
        else:
            if data_type == 'float':
                return float(value)
            elif data_type == 'int':
                return int(value)
            else:
                return value.strip()


def get_common_values(alist):
    """ Retrieve the common values of a set of list in 'alist' and sort them in increasing order
    :param alist: list of lists
    :return: list of common elements in the lists sorted in increasing order """

    common_values = copy.deepcopy(alist[0])
    for i in alist[1:]:
        common_values = list(set(common_values) & set(i))
    return list(np.sort(common_values))


def get_gcd(alist):
    """ Compute the GCD of the elements of a list

    :param alist: list of integers
    :return: GCD of the integers
    """

    gcd = fractions.gcd(alist[0], alist[1])
    for f in range(2, len(alist)):
        gcd = fractions.gcd(gcd, alist[f])
    return gcd


def plot_sphere(radius, center, ax, lstyle='-'):
    """
    :param radius: radius of the sphere (float or int)
    :param center: position of the center of the sphere in 3D space (list or array)
    :param ax: ax in which the sphere must be plotted (mpl_toolkits.mplot3d.axes3d.Axes3D)
    :param lstyle: style of the lines of the sphere (matplotlib.lines.lineStyles)
    :return: Draw a sphere using matplotlib
    """
    u = np.linspace(0, 2 * np.pi, 40)
    v = np.linspace(0, np.pi, 40)

    x = radius * np.outer(np.cos(u), np.sin(v)) + center[0]
    y = radius * np.outer(np.sin(u), np.sin(v)) + center[1]
    z = radius * np.outer(np.ones(np.size(u)), np.cos(v)) + center[2]

    ax.plot_surface(x, y, z, rstride=4, cstride=4, color='g', alpha=0.1, linestyle=lstyle)


def distance(point1, point2):
    """ Return the distance between 2 points in space
    :param point1: list or array of float
    :param point2: list or array of float
    :return: distance between point1 and point2
    """
    return np.sqrt(np.sum([(f - g)**2 for f, g in zip(point1, point2)]))


def heaviside(x):
    """ Heaviside function
    :param x: float or int
    :return: 0 if x < 0, 0.5 if x = 0 and 1.0 if x > 0
    """
    return 0.5 * np.sign(x) + 0.5


def float_to_str(number):
    """
    :param number: any number
    :return:
    """
    if number > 0:
        integer_str = '+' + str(int(number))
    else:
        integer_str = str(int(number))
    return integer_str


def split_into_chunks(alist, sizes):
    """ Split a list into chunks which size correspond to the value in indices
     :param alist: list or ndarray
     :param sizes: list object containing the size of the chunks """

    indices = np.cumsum(sizes)
    return np.split(alist, indices[:-1])


def choose_in(keys, values, choices):
    """" Return the values corresponding to the choices
    :param keys: list of keys
    :param values: list of values
    :param choices: list of choices """

    dictionary = dict(zip(keys, values))
    return [dictionary[key] for key in choices]


def fast_stringcolumn_to_array(raw_data, transpose=True):
    """ Quickly convert a list of strings where data are separated by one or few white spaces

    Example
    >>> raw_data = ['1 2', '3 4']
    >>> fast_stringcolumn_to_array(raw_data)
    array([[ 1.,  3.],
           [ 2.,  4.]])"""

    nb_lines = len([x for x in raw_data if x != ' '])
    string = '\r\n'.join(raw_data)
    data_str = np.array([x for x in string.split() if x != ' '], dtype=float)
    data = data_str.reshape((nb_lines, -1))
    if transpose:
        return np.transpose(data)
    else:
        return data


def handle_same_string(str1, alist):
    """ if a string already exist in a list, add a number to it """

    if str1 in alist:
        for i in range(1, 1000):
            str1_ = str1 + ' (%i)' % i
            if str1_ not in alist:
                return str1_
    else:
        return str1


def add_object_to_dict(obj, container):
    """ Add a pydef object to a dictionary
    :param obj: any pydef object
    :param container: dictionary """

    obj.ID = handle_same_string(obj.ID, container.keys())
    container[obj.ID] = obj


def get_name_file(file_location):
    """ Return the name of the file """

    return os.path.splitext(os.path.basename(file_location))[0]


def find_file(filename, string1, string2):
    """ Find a filename containing string2 and the same extension as filename in the same directory """

    name = get_name_file(filename)
    if string1 in name:
        index = name.find(string1)
        rest = name[index + len(string1):]
    else:
        return ''

    directory = os.path.dirname(filename)
    try:
        return [os.path.abspath(directory + '/' + f) for f in os.listdir(directory) if string2 + rest in f][0]
    except IndexError:
        return ''


def check_cells_consistency(cell1, cell2):
    """ Check that the cell parameters of two cells are close enough """

    c1 = cell1.cell_parameters
    c2 = cell2.cell_parameters
    c_diff = c1 - c2
    if any(np.concatenate(c_diff) > np.ones(9) * 0.001):
        print('Warning! Significant difference between the host cell and the defect cell parameters: %s' % c_diff)
        
        
def moving_avg(arglist, n):
    cumsum, moving_aves = [0], []
    for i, x in enumerate(arglist, 1):
        cumsum.append(cumsum[i-1] + x)
        if i>=n:
            moving_ave = (cumsum[i] - cumsum[i-n])/n
            moving_aves.append(moving_ave)
    return moving_aves
    

def normalize_list(arglist):
    m = max(arglist)
    if type(arglist) == np.ndarray:
        return arglist/m
    else:
        return [x/m for x in arglist]


def is_zero(arglist):
    for i in arglist:
        if np.abs(i) > 0.001:
            return False
            break
    return True
    
def are_equal(a, b):
    """compare the values of two arrays"""
    length = len(a)
    if length != len(b):
        raise ValueError('Compared arrays should have same length!')
    if sum([(a[k]-b[k])**2 for k in range(0,length)]) > 1:
        return False
    else:
        return True
