import numpy as np

data = np.arange(1.,11.,1)
logicalIndex = [data>5]
print(data)
print(logicalIndex)
data[tuple(np.where(logicalIndex))[1]] = np.nan
print(data)