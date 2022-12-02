from .config import *

from . import access
from .data_visualisation import *
from .database_functions import *
"""These are the types of import we might expect in this file
import pandas
import bokeh
import seaborn
import matplotlib.pyplot as plt
import sklearn.decomposition as decomposition
import sklearn.feature_extraction"""

"""Place commands in this file to assess the data you have downloaded. How are missing values encoded, how are outliers encoded? What do columns represent, makes rure they are correctly labeled. How is the data indexed. Crete visualisation routines to assess the data (e.g. in bokeh). Ensure that date formats are correct and correctly timezoned."""
"""Please refer to data_visualisation for code referring to that and to database_functions for database functions"""
def select_properties_typet_prices_overx(conn,x,t):
  cur = conn.cursor()
  cur.execute(f"SELECT * FROM prices_coordinates_data WHERE property_type = '{t}' and price > {x};")
  rows = cur.fetchall()
  return rows

def select_properties_typet_prices_underx(conn,x,t):
  cur = conn.cursor()
  cur.execute(f"SELECT * FROM prices_coordinates_data WHERE property_type = '{t}' and price < {x};")
  rows = cur.fetchall()
  return rows

def select_properties_typet_prices_overx_outsidelondon(conn,x,t):
  cur = conn.cursor()
  cur.execute(f"SELECT * FROM prices_coordinates_data WHERE property_type = '{t}' and price > {x} and town_city != 'LONDON' and county != 'GREATER LONDON';")
  rows = cur.fetchall()
  return rows


