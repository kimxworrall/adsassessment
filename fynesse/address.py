# This file contains code for suporting addressing questions in the data

"""# Here are some of the imports we might expect 
import sklearn.model_selection  as ms
import sklearn.linear_model as lm
import sklearn.svm as svm
import sklearn.naive_bayes as naive_bayes
import sklearn.tree as tree

import GPy
import torch
import tensorflow as tf

# Or if it's a statistical analysis
import scipy.stats"""
import shapely
import math
from geopandas import GeoSeries
import numpy as np
import pandas as pd
from .input_validation import *
from .data_visualisation import *
"""Address a particular question that arises from the data"""

def validate_inputs(latitude, longitude, date, property_type,conn):
  #Check that the given inputs are valid and return any warnings associated with them
  if check_coordinates_valid(latitude, longitude,conn):
     validate_date(date)
     return validate_property_type(property_type)

def select_year_range(year):
  #Select the two year range of the year, and the year before it (where possible)
  if year < 1999:
    return (1995,1996)
  if year > 2022:
    return (2021,2022)
  return(year,year-1)

def get_training_pricesdata(latitude,longitude,date,radius,conn):
  #Join the postcode data and the paid price data for transactions that are in the date range, and in the bounding box
  date_range = select_year_range(date)
  cur = conn.cursor()
   
  rows = pd.read_sql(f"""
                        SELECT ft.price, ft.date_of_transfer, ct.postcode, ft.property_type, ft.new_build_flag, ft.tenure_type, ft.primary_addressable_object_name, ft.street, ft.locality, ft.town_city, ft.district, ft.county, ct.country, ct.lattitude, ct.longitude, ft.db_id
                                        FROM
                                            (SELECT `postcode`,`db_id`,`price`, `date_of_transfer`, `property_type`,`new_build_flag`, `tenure_type`,`primary_addressable_object_name`, `street`, `locality`, `town_city`, `district`, `county`   FROM pp_data) ft
                                        INNER JOIN 
                                            (SELECT `postcode`, `lattitude`, `longitude`, `country` FROM postcode_data ) ct
                                        ON
                                            ft.`postcode` = ct.`postcode`
                                        WHERE 
                                            lattitude < {radius+latitude} AND lattitude > {-radius+latitude} AND longitude < {radius+longitude} AND longitude > {-radius+longitude} AND date_of_transfer BETWEEN '{date_range[1]}-01-01' AND '{date_range[0]}-12-31'

                        ;""",con = conn)
  return rows

def validate_training_data(data,latitude,longitude,radius,ptype):
  #Given a dataframe of prices data, remove datapoints where the price might be anomalous, and look at how many datapoints there are, if we dont have many, let the user know
  df = clean_prices_dataframe(data)
  if len(df['price'])<100:
    print("Not many houses were sold in this area, we only found "+str(len(df['price'])) +", this data might not be very accurate")
  if len(df['price']) == 0:
    print("We've found no houses near here, checking osmnx data")
    profile_osmdata(latitude,longitude,radius)
  if len(df[df['property_type']==ptype]) < 20:
    print("There aren't many properties of that type near here, this prediction may not be accurate")
  
  return df

'''
Below are the four functions for getting the training parameters from the data, they could easily be added to or edited if necessart
'''

def get_avg_prices_in_radius_df(df,radius):
  avgs = [np.mean(df[sqrt(pow(abs(df.lattitude - df['lattitude'][i]),2) + pow(abs(df.longitude - df['longitude'][i]),2)) < radius ]['price']) for i in df['price'].index]
  return avgs

def get_avg_prices_propertytype_in_radius_df(df,radius):
  avgs = [np.mean(df[df['property_type']==df['property_type'][i]][sqrt(pow(abs(df[df['property_type']==df['property_type'][i]]['lattitude'] - df['lattitude'][i]),2) + pow(abs(df[df['property_type']==df['property_type'][i]].longitude - df['longitude'][i]),2)) < radius ]['price']) for i in df['price'].index]
  return avgs

def get_avg_prices_newbuild_in_radius_df(df,radius):
  avgs = [np.mean(df[df['new_build_flag']==df['new_build_flag'][i]][sqrt(pow(abs(df[df['new_build_flag']==df['new_build_flag'][i]]['lattitude'] - df['lattitude'][i]),2) + pow(abs(df[df['new_build_flag']==df['new_build_flag'][i]].longitude - df['longitude'][i]),2)) < radius ]['price']) for i in df['price'].index]
  return avgs

def get_sizeIn_radius(houses,pois,radius):
  avgs = [np.mean(pois[pois.geometry.distance(Point(houses['lattitude'][i],houses['longitude'][i])) < radius]['size']) for i in houses['price'].index]
  return avgs  

def make_proper_training_data(df,latitude,longitude,conn):
  
  newdf = df[['lattitude','longitude']]
  newdf['mean_close_price'] = get_avg_prices_in_radius_df(df,0.005)
  newdf['mean_price_of_propertytype_close'] = get_avg_prices_propertytype_in_radius_df(df,0.005)
  newdf['mean_price_of_isnewbuild_close'] = get_avg_prices_newbuild_in_radius_df(df,0.01)
  newdf['avg_size_of_ptype'] = get_sizeIn_radius(df,get_houses_sizes(latitude,longitude,0.01,conn),0.001)
  return newdf
  

def get_predictionparams(latitude,longitude,date,property_type,newbuild_flag,pois,df):
    pp = [latitude,longitude,
          np.mean(df[sqrt(pow(abs(df.lattitude - latitude),2) + pow(abs(df.longitude - longitude),2)) < 0.005 ]['price']),
          np.mean(df[df['property_type']==property_type][sqrt(pow(abs(df[df['property_type']==property_type]['lattitude'] - latitude),2) + pow(abs(df[df['property_type']==property_type].longitude - longitude),2)) < 0.005 ]['price']),
          np.mean(df[df['new_build_flag']==newbuild_flag][sqrt(pow(abs(df[df['new_build_flag']==newbuild_flag]['lattitude'] - latitude),2) + pow(abs(df[df['new_build_flag']==newbuild_flag].longitude - longitude),2)) < 0.05 ]['price']),
          np.mean(pois[pois.geometry.distance(Point(latitude,longitude)) < 0.001]['size'])
          ]
    return pp

def validate_prediction(p):
  if p < 0:
    print("This prediction is negative and is therefore very unlikely to be accurate, please check your data")
  
def predict_price(latitude,longitude,date,property_type,conn):
    """Price??prediction??for??UK??housing."""
    if validate_inputs(latitude, longitude, date, property_type,conn):
      data = get_training_pricesdata(latitude,longitude,date,0.01,conn)
      data = validate_training_data(data,latitude,longitude,0.01,property_type)
      params = make_proper_training_data(data,latitude,longitude,conn)
      params = params.fillna(0)
      design = params.to_numpy()
      Y = data['price'].to_numpy()
      m_linear_basis = sm.OLS(Y,design)
      results_basis = m_linear_basis.fit()
      design_pred = get_predictionparams(latitude,longitude,date,property_type,'N',get_houses_sizes(latitude,longitude,0.01,conn),data)
      design_pred = np.where(np.isnan(design_pred), 0, design_pred)
      y_pred_linear_basis = results_basis.get_prediction(design_pred).summary_frame(alpha=0.05)
      prediction = results_basis.predict(design_pred)
      print("I predict ??:")
      print(prediction)
      print("This is the variance of our model "+ str(results_basis.scale))
      print("Standard deviation = " + str(math.sqrt(results_basis.scale)))
      print("These are the prediction parameters ")
      print(str(y_pred_linear_basis))
      validate_prediction(prediction)
    pass