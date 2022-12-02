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
import osmnx as ox
from scipy.stats.morestats import sqrt

def plotlines_together_and_seperately(lines,x_label,y_label,graphname, labels):
  #This functions plots lines both all on the same graph, and on one graph each
  numdown = math.ceil(math.sqrt((len(lines)+1)))
  numacross = math.ceil(len(lines)/numdown)
  fig, axes = plt.subplots(
    nrows=numdown, ncols=numacross, sharex=True, sharey=True, figsize = (20,20)
  )

  fig.suptitle(graphname)
  
  for l in range(len(lines)):
    y = np.sort(lines[l])
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

  plt.figure(figsize=(40,20))
  plt.show()

def plot_graphs_subplots(graphs,linelabels,x_label,y_label,graphname, labels):
  #This function takes a number of graphs and plots them in a rectangle
  numdown = math.ceil(math.sqrt((len(graphs))))
  numacross = math.ceil(len(graphs)/numdown)
  fig, axes = plt.subplots(
    nrows=numdown, ncols=numacross, sharex=True, sharey=False, figsize = plot.big_figsize
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
    # This function plots a set of sets of points on a given axis
    for l in range(len(lines)):
      y = np.sort(lines[l])
      # get the cdf values of y
      x = np.arange(len(lines[l])) / float(len(lines[l]))
      ax.plot(x,y,marker='o', markersize = 5, label =labels[l])
    ax.legend()

def plot_cdfs_by_propertytype_locations(place,names,conn):
  #This function plots the functions comparing what fraction of properties have sold for which price for each place name
  propertytypes = get_unique_values_of_column_from_table("property_type","prices_coordinates_data",conn)
  allprices = [[get_prices_by_property_type_location(t,place,n,conn) for t in propertytypes] for n in names]
  print(len(allprices))
  plot_graphs_subplots(allprices,propertytypes,"Fraction of houses sold for less than that price","Price £", "CDF of prices by property type", names)


def plot_cdfs_by_propertytype(conn):
  #This function just plots cdfs per property type for all of the data in prices_coordinates_data
  propertytypes = get_unique_values_of_column_from_table("property_type","prices_coordinates_data",conn)
  allprices = [get_prices_by_property_type(t,conn) for t in propertytypes]
  plotlines_together_and_seperately(allprices,"Number of houses sold less than that price","Price £", "CDF of prices by property type", propertytypes)

def fetch_uk_district_geojson():
  #This line fetches the districts geojson
  with urlopen('https://raw.githubusercontent.com/thomasvalentine/Choropleth/main/Local_Authority_Districts_(December_2021)_GB_BFC.json') as response:
    Local_authorities = json.load(response)
    return Local_authorities

def plot_district_withdata(data):
  #This function plots an interactive map using the dataframe provided of local_authorities and values for them
  Local_authorities = fetch_uk_district_geojson()
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
        if (a[1] == "County of"): #This is to match discrepencies in how the districts are listed in the different data sources
          f = data.get((a[0]).upper(),0)
        elif ((a[1] == "City of") and (a[0] == "Westiminster")):
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
    """This helper function plots the DataFrame, filtering a given column on a particular item"""
    if column is None:
        column = dataframe.columns[0]
    if item=="all": 
        plot_district_withdata((dict(zip(dataframe["district"],dataframe[column]))))
    plot_district_withdata((dict(zip(dataframe[dataframe[groupby]==item]["district"],dataframe[dataframe[groupby]==item][column]))))

def plot_counties_features_groupby(year, groupby,conn,features= ['AVG(price) as average_price', 'COUNT(db_id) as num_sold', 'MAX(price) as Maxprice', 'MIN(price) as Minprice', 'MAX(price) - MIN(price) as pricerange']):
  #This function produces the interacts that help the user choose different features of the data to look at
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
  fix,ax = plt.subplots(figsize=plot.big_figsize)
  plot_map(float(latitude),float(longitude),radius,ax)
  plot_pois(pois, ax)

def plot_houses(houses,ax,fig):
    # plotting
  markeroptions = {'F':'o','T':'^','S':'s','D':'D','O':'*'}
  housetypes = houses['property_type'].unique()
  ax.title.set_text("Houses sold in area")

  min,max = houses['price'].min(), houses['price'].max()
  for t in housetypes:
    y = houses[houses['property_type']==t]['lattitude']
    # get the cdf values of y
    x = houses[houses['property_type']==t]['longitude']#[:-20]
    z = houses[houses['property_type']==t]['price']

    points = pd.DataFrame(x,y)
    geometry=gpd.points_from_xy(x, y)
    points_gdf = gpd.GeoDataFrame(z, 
                            geometry=geometry)
    points_gdf.crs = "EPSG:4326"
    if (t == 'S'):
      points_gdf.plot('price', ax=ax, marker = markeroptions[t], label=t, c= z,cmap = "Plasma",  vmin = min, vmax = max, legend=True)
    else:
      points_gdf.plot('price', ax=ax, marker = markeroptions[t], label=t, c= z,cmap = "Plasma",  vmin = min, vmax = max)

  ax.legend(loc='best')

  plt.figure(figsize=(9, 9))
  plt.show()

def plot_around_postcode(postcode,radius,conn):
  loc,rows = select_houses_in_radius_around_postcode(postcode,radius,conn)
  fig,ax = plt.subplots(figsize=plot.big_figsize)
  plot_map(loc[0],loc[1],radius,ax)
  plot_houses(rows,ax,fig)

def plot_pois_houses_around_point(latitude,longitude,radius,conn,tags,fig,ax):
  rows = select_houses_in_radius_around_point(latitude,longitude,radius,conn)
  plot_map(float(latitude),float(longitude),radius,ax)
  pois = (get_points_of_interest(float(latitude),float(longitude),radius,tags))
  plot_pois(pois, ax)
  plot_houses(rows,ax,fig)
  return pois,rows

def plot_pois_houses_around_postcode(postcode,radius,conn,tags):
  loc = get_lat_long_from_postcode(postcode,conn)
  latitude,longitude = loc[0],loc[1]
  fig,ax = plt.subplots(figsize=plot.big_figsize)
  plot_pois_houses_around_point(latitude,longitude,radius,conn,tags,fig,ax)

def plotscatter_on_ax(pairs, marker, colour, label,ax):
    # plotting
    ax.plot(x=pairs[0],y=pairs[1],marker=marker, markersize = 5, label =label, color =  colour)
    ax.legend()

def plot_price_distance_to_osmnxpoint(latitude,longitude,radius,tags,conn):
  fig,ax = pplt.subplots(figsize=plot.big_figsize)
  pois,houses = plot_pois_houses_around_point(latitude,longitude,radius,conn,tags,fig,ax)
  #avgs = [np.mean(pois[pois.geometry.distance(Point(houses['lattitude'][i],houses['longitude'][i])) < radius]['size']) for i in houses['price'].index]
  colours = {'F':'r','T':'y','S':'b','D':'g','O':'o'}
  markeroptions = {'F':'o','T':'^','S':'s','D':'D','O':'*'}
  housetypes = houses['property_type'].unique()
  '''for t in housetypes:
    subset = houses[houses['property_type'] == t]
    dists = [min(pois.geometry.distance(Point(subset['lattitude'][i],subset['longitude'][i]))) for i in subset['price'].index]
    pairs = [subset['price'],dists]
  
    pairs = pairs[pairs[1]!=np.NaN]
    print(pairs)
    plotscatter_on_ax(pairs, markeroptions[t], colours[t], t,axs[0,1])'''
  
  latitudes = [x for x in pois.geometry.centroid.y]
  #latitudes.extend([x for x in pois.geometry.way.centroid.y])
  longitudes = [x for x in pois.geometry.centroid.x]
  #longitudes.extend([x for x in pois.geometry.way.centroid.x])

  pois['latitude'] = latitudes
  pois['longitude'] = longitudes
  fig2,ax2 = plt.subplots(figsize=plot.big_figsize)
  colours = {'F':'r','T':'y','S':'b','D':'g','O':'c'}
  markeroptions = {'F':'o','T':'^','S':'s','D':'D','O':'*'}
  for i in range(len(houses['price'])):
    lat,lon = houses['lattitude'][i],houses['longitude'][i]
    dists = sqrt(pow(abs(pois.latitude - lat),2) + pow(abs(pois.longitude - lon),2))
    dist = radius
    if len(dists)>0:
      dist = min(dists)
    if ((dist != np.NaN) and (dist > 0)):
      ax2.scatter(x=dist,y=houses['price'][i],marker =markeroptions[houses['property_type'][i]], color = colours[houses['property_type'][i]])

  plt.show()


def get_houses_sizes(latitude,longitude,radius,conn,tag="building",keys= ['residential','semidetached_house','apartments','house','detached','terrace']):
  houses = select_houses_in_radius_around_point(latitude,longitude,radius,conn)
  tags = {tag: True}
  pois = ox.geometries_from_bbox(latitude+radius, latitude-radius, longitude+radius, longitude-radius, tags)
  pois = (pois[pois.building.isin(keys)])
  #print(pois[pois['house']=='terraced'])
  
  pois.geometry.crs = "EPSG:4326"
  pois['size'] = pois.geometry.area



  latitudes = [x for x in pois.geometry.node.y]
  latitudes.extend([x for x in pois.geometry.way.centroid.y])
  longitudes = [x for x in pois.geometry.node.x]
  longitudes.extend([x for x in pois.geometry.way.centroid.x])

  pois['latitude'] = latitudes
  pois['longitude'] = longitudes
  return houses,pois

def plot_price_to_sizeIn_radius(latitude,longitude,radius,conn):
  houses,pois = get_houses_sizes(latitude,longitude,radius,conn)
  fig,ax = plt.subplots(figsize=plot.big_figsize)
  plot_map(latitude,longitude,radius,ax)
  pois.plot(ax=ax, color="blue", alpha=0.7, markersize=10)
  plot_houses(houses,ax,fig)
  markeroptions = {'F':'o','T':'^','S':'s','D':'D','O':'*'}
  colours = {'F':'r','T':'b','S':'y','D':'p','O':'g'}
  fig,ax = plt.subplots(figsize=plot.big_figsize)
  for i in range(len(houses['price'])):
    lat,lon = houses['lattitude'][i],houses['longitude'][i]
    #print(pois)
    #print(pois[sqrt(pow(abs(pois.latitude - lat),2) + pow(abs(pois.longitude - lon),2))<radius])
    close_pois_avg = np.mean(pois[sqrt(pow(abs(pois.latitude - lat),2) + pow(abs(pois.longitude - lon),2)) < radius ]['size'])
    #print( max(close_pois_avg,0),houses['price'][i])
    if (close_pois_avg != np.NaN and close_pois_avg < radius):
      ax.scatter(x = max(close_pois_avg,0), y = houses['price'][i], marker =markeroptions[houses['property_type'][i]], color = colours[houses['property_type'][i]])

def profile_osmdata(latitude,longitude,radius):
  tag="building"
  keys= ['residential','semidetached_house','apartments','house','detached','terrace']
  tags = {"building": 'residential',"building":'semidetached_house',"building":'apartments',"building":'house',"building":'detached',"building":'terrace', "building":True, "landuse":True, }
  pois = ox.geometries_from_bbox(latitude+radius, latitude-radius, longitude+radius, longitude-radius, tags)
  #pois = (pois[pois.building.isin(keys)])
  
  if ("residential" in list(pois['building'])):
    print("There are this many residential buildings in this area:")
    print(len(pois[pois['building']=="residential"]))
    print("Maybe try a larger bounding box")
  print("This is the landuses of this area:")
  display(pois['landuse'].unique())
  if ("farmland" in list(pois['landuse'])):
    print("This area contains a lot of farmland, it is possible there aren't many houses here")