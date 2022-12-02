from . import database_functions
from .database_functions import *#get_prices_by_property_type, get_unique_values_of_column_from_table, get_features_by_property_type_by_district, get_lat_long_from_postcode
import matplotlib.pyplot as plt
import numpy as np
import mlai.plot as plot
import pandas as pd
import math

from fiona.env import ThreadEnv
from urllib.request import urlopen
import json
import plotly.express as px
from geojson_rewind import rewind
import ipywidgets as widgets
from ipywidgets import interact, fixed
from IPython.display import display

from matplotlib import axis
import proplot as pplt
import mlai
from mlai import plot
import geopandas as gpd

def plotlines_together_and_seperately(lines,x_label,y_label,graphname, labels):
    # plotting
  numdown = math.ceil(math.sqrt((len(lines)+1)))
  numacross = math.ceil(len(lines)/numdown)
  fig, axes = plt.subplots(
    nrows=numdown, ncols=numacross, sharex=True, sharey=True, figsize = (20,20)
  )
  #fig.xlabel(x)
  #fig.ylabel(y)
  fig.suptitle(graphname)
  
  for l in range(len(lines)):
    y = np.sort(lines[l])
    # get the cdf values of y
    x = np.arange(len(lines[l]))
    axes[0,0].plot(x,y,marker='o', markersize = 5, label =labels[l])
    axes[math.floor((l+1)/numacross),((l+1)%numacross)].plot(x,y,marker='o', markersize = 5, label =labels[l])
    axes[math.floor((l+1)/numacross),((l+1)%numacross)].legend()
  axes[0,0].legend()

  for ax in axes.flat:
    ax.set(xlabel=x_label, ylabel=y_label)

  # Hide x labels and tick labels for top plots and y ticks for right plots.
  for ax in axes.flat:
      ax.label_outer()

  #plt.figure(figsize=(40,20))
  plt.show()

def plot_graphs_subplots(graphs,linelabels,x_label,y_label,graphname, labels):
  numdown = math.ceil(math.sqrt((len(graphs))))
  numacross = math.ceil(len(graphs)/numdown)
  fig, axes = plt.subplots(
    nrows=numdown, ncols=numacross, sharex=True, sharey=False, figsize = (20,20)
  )
  fig.suptitle(graphname)

  for l in range(len(graphs)):
    ax = axes[math.floor((l)/numacross),((l)%numacross)]
    plotlines_on_ax(graphs[l], linelabels,ax)
    ax.title.set_text(labels[l])

  for ax in axes.flat:
    ax.set(xlabel=x_label, ylabel=y_label)
  plt.show()

def plotlines_on_ax(lines, labels,ax):
    # plotting
    for l in range(len(lines)):
      y = np.sort(lines[l])
      # get the cdf values of y
      x = np.arange(len(lines[l])) / float(len(lines[l]))
      ax.plot(x,y,marker='o', markersize = 5, label =labels[l])
    ax.legend()

def plot_cdfs_by_propertytype_locations(place,names,conn):
  propertytypes = get_unique_values_of_column_from_table("property_type","prices_coordinates_data",conn)
  allprices = [[get_prices_by_property_type_location(t,place,n,conn) for t in propertytypes] for n in names]
  print(len(allprices))
  plot_graphs_subplots(allprices,propertytypes,"Fraction of houses sold for less than that price","Price £", "CDF of prices by property type", names)


def plot_cdfs_by_propertytype():
  propertytypes = get_unique_values_of_column_from_table("property_type","prices_coordinates_data")
  allprices = [get_prices_by_property_type(t) for t in propertytypes]
  plotlines_together_and_seperately(allprices,"Number of houses sold less than that price","Price £", "CDF of prices by property type", propertytypes)

def fetch_uk_counties_geojson():
  with urlopen('https://raw.githubusercontent.com/thomasvalentine/Choropleth/main/Local_Authority_Districts_(December_2021)_GB_BFC.json') as response:
    Local_authorities = json.load(response)
    return Local_authorities

def plot_district_withdata(data):
  Local_authorities = fetch_uk_counties_geojson()
  la_data = []
  # Iterative over JSON
  for i in range(len(Local_authorities["features"])):
      # Extract local authority name
      la = Local_authorities["features"][i]['properties']['LAD21NM']
      # Assign the local authority name to a new 'id' property for later linking to dataframe
      Local_authorities["features"][i]['id'] = la
      # append local authority name to a list with the item of data to plot
      if "," in la:
        a = la.split(', ')
        if (a[1] == "County of"):
          f = data.get((a[0]).upper(),0)
        else:
          f = data.get((a[1]+" "+a[0]).upper(),0)
        la_data.append([la,int(f)])
      else:
        la_data.append([la,int(data.get(la.upper(), 0))])

  df = pd.DataFrame(la_data)

      # update column names
  df.columns = ['LA','Val']


  fig = px.choropleth_mapbox(df,
                                geojson=Local_authorities,
                                locations='LA',
                                color='Val',
                                featureidkey="properties.LAD21NM",
                                color_continuous_scale="Viridis",
                                mapbox_style="carto-positron",
                                center={"lat": 55.09621, "lon": -4.0286298},
                                zoom=4.2,
                                labels={'val':'value'})

  fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
  fig.show()

def filter_and_plotdistricts(dataframe,groupby, column=None, item="all"):
    """This helper function displays a DataFrame, filtering a given column on a particular item"""
    if column is None:
        column = dataframe.columns[0]
    if item=="all": 
        plot_district_withdata((dict(zip(dataframe["district"],dataframe[column]))))
    plot_district_withdata((dict(zip(dataframe[dataframe[groupby]==item]["district"],dataframe[dataframe[groupby]==item][column]))))

def plot_counties_features_groupby(year, groupby,conn,features= ['AVG(price) as average_price', 'COUNT(db_id) as num_sold', 'MAX(price) as Maxprice', 'MIN(price) as Minprice', 'MAX(price) - MIN(price) as pricerange']):
  #print(get_keys(conn,'pp_data'))
  data_interact = get_features_by_property_type_by_district(features, year, groupby,conn)
  
  column = groupby
  columns = data_interact.keys()[1:-1]
  column_select = widgets.Select(options=columns)
  options = data_interact[groupby].unique()
  options  =np.append(options,'all')
  item_select = widgets.Select(options=options)
  #number_slider = widgets.FloatSlider(min=0, max=500, step=1, value=5)

  selection = interact(filter_and_plotdistricts,
              dataframe=fixed(data_interact),
              groupby = fixed(groupby), 
              column=column_select,
              item = item_select)

def get_bounding_box(latitude,longitude,radius):
  north,south,east,west = latitude+radius, latitude-radius, longitude+radius, longitude-radius
  return north,south,east,west

def get_points_of_interest(latitude,longitude,radius,tags): #Please enter tags in dictionary form with {tag_name:True/False/'value',....}
  pois = ox.geometries_from_bbox(latitude+radius, latitude-radius, longitude+radius, longitude-radius, tags)
  return pois


def plot_pois(pois,ax):
  pois.plot(ax=ax, color="blue", alpha=0.7, markersize=10)

def plot_map(lat,lon,radius,ax):
  north,south,east,west = radius+float(lat), -radius + float(lat) , radius+float(lon), -radius+float(lon)
  graph = ox.graph_from_bbox(north, south, east, west)

  # Retrieve nodes and edges
  nodes, edges = ox.graph_to_gdfs(graph)
  

  # Plot street edges
  edges.plot(ax=ax, linewidth=1, edgecolor="dimgray")

  ax.set_xlim([west, east])
  ax.set_ylim([south, north])
  ax.set_xlabel("longitude")
  ax.set_ylabel("latitude")

def plot_pois_around_point(latitude,longitude,radius,tags):
  pois = (get_points_of_interest(float(latitude),float(longitude),radius,tags))
  fix,ax = pplt.subplots(figsize=plot.big_figsize)
  plot_map(float(latitude),float(longitude),radius,ax)
  plot_pois(pois, ax)