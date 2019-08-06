import matplotlib.pyplot as plt
import numpy

font = {'family': 'serif',
        'color':  'darkred',
        'weight': 'normal',
        'size': 16,
        }
        
x = numpy.arange(1,11,1) # This syntax is idiotic
y = x


fig, ax = plt.subplots()
ax.plot(x, y, 'bo')
plt.xlabel('Timetag2', fontdict=font)
plt.ylabel('Data', fontdict=font)
plt.show()
