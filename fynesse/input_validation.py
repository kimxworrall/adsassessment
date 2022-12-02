from .config import *
from shapely.geometry import Point
import geopandas
from global_land_mask import globe
import datetime
def check_nearby_postcode(latitude,longitude,conn):
  '''
    This function is to check if there is a postcode within an aproximately 10km radius of the given point
  '''
  cur = conn.cursor()
  north,south,east,west = latitude+0.1,latitude-0.1,longitude+0.1,longitude-0.1
  cur.execute(f"SELECT postcode FROM postcode_data WHERE lattitude < {north} AND lattitude > {south} AND longitude < {east} AND longitude > {west} LIMIT 1;")
  num = cur.fetchall()
  return len(num) > 0

def check_coordinates_valid(latitude,longitude,conn):
  '''
  This function checks that the given point is on land, and is also believably in the UK (it is within 10km of a UK postcode)
  '''
  if (check_nearby_postcode(latitude,longitude,conn)):
    if globe.is_land(latitude, longitude):
      return True
    else:
      print("that point is in the sea")
  else:
    print("No nearby uk postcodes")
  return False

def validate_date(date):
  '''
  This function checks whether the date
  '''
  if date < 1995:
    print("Price data for this year does not exist, the model may not be accurate")
  if date >  datetime.date.today().year:
    print("This date is in the future, the model may not be accurate")

def validate_property_type(pt):
  return pt in ['F','T','S','D','O']

def clean_prices_dataframe(df):
  mean = np.mean(df['price'])
  standarddeviation = np.std(df['price'])
  return df[df['price']<(mean+(2*standarddeviation))][df['price']>(mean-(2*standarddeviation))]

