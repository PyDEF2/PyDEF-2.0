"""
    12/12/17
	Simple script to follow convergence from OSZICAR file
    author: Adrien Stoliaroff
    email: adrien.stoliaroff@cnrs-imn.fr
"""
import matplotlib.pyplot as plt

def isInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

#Read OSZICAR content        
infile = open("OSZICAR","r")
eList, dEList, dEpsList, rmsList, eSCF, dESCF = [], [], [], [], [], []

for line in infile:
	content = line.replace('d eps','deps').split()
	#line inside SCF cycle
	if(isInt(content[1])):
		eList.append(float(content[2]))
		dEList.append(float(content[3]))
		dEpsList.append(float(content[4]))
		rmsList.append(float(content[6].split('-0.')[0]))
	#end of SCF cycle
	if(isInt(content[0])):
		eSCF.append(float(line.split()[4]))
		dESCF.append(float(line.split()[7].replace('=','')))
#plot result
legend = ['E', 'dE', 'd eps', 'RMS', 'E_SCF', 'd E_SCF']
colors = ['r', 'b', 'g', 'c', 'm', 'y']
i = 0
plt.subplot(311)

for curve in [eList, dEList]:
	plt.plot(range(len(curve)), curve, label = legend[i], color = colors[i])
	i += 1

plt.xlabel('Iteration')
plt.ylabel('Energies (eV)')
plt.title('Convergence follow up from OSZICAR')
plt.legend()

plt.subplot(312)
 
for curve in [dEpsList, rmsList]:
	plt.plot(range(len(curve)), curve, label = legend[i], color = colors[i])
	i += 1
	
plt.xlabel('Iteration')
plt.ylabel('Convergence')
plt.legend()

plt.subplot(313)
 
for curve in [eSCF, dESCF]:
	plt.plot(range(len(curve)), curve, label = legend[i], marker = 'o', linestyle = '--', color = colors[i])
	i += 1
	
plt.xlabel('SCF cycle')
plt.ylabel('Energies (eV)')
plt.legend()

fig=plt.gcf()
fig.show()
