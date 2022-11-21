

"""
This file contains some useful sql query functions for the database

1. showallyears gives you the list of years that the price paid data contains

2. head prints the first 6 records from a table, and select_top returns the first n records from a table

3. 
"""

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