import cPickle as pickle


def load_mem():
    try:
        with open("./Save-Projects/PyDEF_memory.pyd", "rb") as f:
            return pickle.load(f)
    except EOFError, e :
        print 'Warning! PyDEF memory file found but is empty. '
        return {}
    except IOError, e:
        print 'Warning! No PyDEF memory found. '
        return {}


def load_project(pid):
        try:
            projectpath = projects_mem[pid]['path']
            if projectpath.split('.')[-1] != 'pyd':
                print 'Warning! Are you sure this project was saved correctly? The file\'s extension is not *.pyd.'
            with open(projectpath, "rb") as f:
                projects[pid] = pickle.load(f)
                # projects[pid].mainwindow = self
                projects[pid].pid = pid
            print 'Project ' + projects[pid].name + ' loaded successfully!\n'
        except IOError:
            print 'No *.pyd file found for Project %s!' %pid
            if pid in projects.keys():
                projects.pop(pid)
                print 'Project %s deleted.' %pid
        except KeyError:
            printerror('Sorry! I do not remember any path to a *.pyd save file for this project.')
        except EOFError:
            if init:
                printerror('Error while reading saved *.pyd file.')
            else:
                print '!!!Error!!! Error while reading saved *.pyd file.'
            
projects_mem = load_mem()
projects = {}
for pid in projects_mem.keys():
    if pid not in ['last_import_dir', 'last_export_dir']:
        name = projects_mem[pid]['name']
        path = projects_mem[pid]['path']
        load_project(pid)
        print name + ' ' + path
        try:
            print 'project.hostcellid ' + str(projects[pid].hostcellid)
            print '\n\n\n'
        except KeyError:
            pass
        
print 'Done'

try:
    last_import_dir = projects_mem['last_import_dir']
    last_export_dir = projects_mem['last_export_dir']
except KeyError:
    pass
    
for project in projects.values():
    print '\n'
    try:
        print project.name + ' host : ' + str(project.cells[project.hostcellid])
    except KeyError:
        print project.name + ' hostcellid : ' + project.hostcellid
        
# with open("./Save-Projects/PyDEF_memory.pyd", "wb") as f:
#    pickle.dump(projects_mem, f, pickle.HIGHEST_PROTOCOL)
