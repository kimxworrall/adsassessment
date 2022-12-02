

"""
This file contains some useful sql query functions for the database

1. showallyears gives you the list of years that the price paid data contains

2. head prints the first 6 records from a table, and select_top returns the first n records from a table

3. 
"""
import pandas as pd
import numpy as np

def show_all_years(conn):
    cur = conn.cursor()
    cur.execute(f"""SELECT DISTINCT YEAR(date_of_transfer) FROM pp_data ORDER BY ASC;""")
    rows = cur.fetchall()
    return rows

def select_top(conn, table,  n):
    """
    Query n first rows of the table
    :param conn: the Connection object
    :param table: The table to query
    :param n: Number of rows to query
    """
    cur = conn.cursor()
    cur.execute(f'SELECT * FROM {table} LIMIT {n}')

    rows = cur.fetchall()
    return rows
def head(conn, table, n=6):
  rows = select_top(conn, table, n)
  for r in rows:
      print(r)

def select_from_pricecoordinatedata_by_place_and_year(place, placetype,year, conn):
    if placetype == "Country":
        cur = conn.cursor()
        cur.execute(f"""SELECT * FROM prices_coordinates_data WHERE (date_of_transfer BETWEEN '{year}-01-01' AND '{year}-12-31') AND country = {place}""")
    elif placetype == "County":
        cur.execute(f"""SELECT * FROM prices_coordinates_data WHERE (date_of_transfer BETWEEN '{year}-01-01' AND '{year}-12-31') AND county = {place}""")
    else:
        return NotImplementedError


def get_prices_by_property_type(type,conn):
    cur = conn.cursor()
    cur.execute(f"SELECT price FROM prices_coordinates_data WHERE property_type = '{type}' ;")
    rows = cur.fetchall()
    return [i[0] for i in rows]

def get_unique_values_of_column_from_table(column,table,conn):
    rows = pd.read_sql(f"SELECT DISTINCT {column} FROM {table};",con = conn)
    return list(rows[column])



def get_features_by_property_type_by_district(features,year,groupby,conn):
    fselect = ', '.join(features)
    cur = conn.cursor()
    rows = pd.read_sql(f"SELECT {groupby}, {fselect}, district FROM prices_coordinates_data WHERE date_of_transfer BETWEEN '{year}-01-01' AND '{year}-12-31' GROUP BY {groupby}, district;",con = conn)
    return rows


def get_keys(conn,table):
  cur = conn.cursor()
  cur.execute(f"SHOW COLUMNS FROM {table};")
  return [i[0] for i in cur.fetchall()]

def get_lat_long_from_postcode(postcode,conn):
  cur = conn.cursor()
  cur.execute(f"SELECT lattitude, longitude FROM postcode_data WHERE postcode = '{postcode}';")
  loc = cur.fetchall()[0]
  return loc

def get_prices_by_property_type_location(type,place,c,conn):
    cur = conn.cursor()
    cur.execute(f"SELECT price FROM prices_coordinates_data WHERE property_type = '{type}' AND {place} = '{c}' ;")
    rows = cur.fetchall()
    return [i[0] for i in rows]

def select_houses_in_radius_around_postcode(postcode,radius,conn):
  cur = conn.cursor()
  cur.execute(f"SELECT lattitude, longitude FROM postcode_data WHERE postcode = '{postcode}';")
  loc = cur.fetchall()[0]
  rows = pd.read_sql(f"SELECT price, property_type, lattitude, longitude FROM prices_coordinates_data WHERE lattitude < {radius+float(loc[0])} AND lattitude > {-radius+float(loc[0])} AND longitude < {radius+float(loc[1])} AND longitude > {-radius+float(loc[1])};",con = conn)
  return (loc,rows)



def select_houses_in_radius_around_point(latitude,longitude,radius,conn):
  cur = conn.cursor()
  rows = pd.read_sql(f"SELECT price, property_type, lattitude, longitude FROM prices_coordinates_data WHERE lattitude < {radius+float(latitude)} AND lattitude > {-radius+float(latitude)} AND longitude < {radius+float(longitude)} AND longitude > {-radius+float(longitude)};",con = conn)
  return rows

