import pandas
import dateutil.parser
import datetime
import matplotlib.pyplot as plt

from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

start = dateutil.parser.parse("2018-05-17 19:00:00").replace(tzinfo=datetime.timezone.utc)
end = dateutil.parser.parse("2018-05-17 20:00:00").replace(tzinfo=datetime.timezone.utc)
df = pandas.DataFrame(data=[start, end], index=[0,1], columns=['x'])
# *** HACK: CONVERT datetime column to string and back again - who knows why this works? ***
df['x'] = pandas.to_datetime(df['x'].astype(str))
print(df)
print(df.dtypes)

plt.plot(df['x'], [0,1], '--o')
plt.show()