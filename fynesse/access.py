from .config import *

"""These are the types of import we might expect in this file
import httplib2
import oauth2
import tables
import mongodb
import sqlite"""

# This file accesses the data

"""Place commands in this file to access the data electronically. Don't remove any missing values, or deal with outliers. Make sure you have legalities correct, both intellectual property and personal data privacy rights. Beyond the legal side also think about the ethical issues around this data. """

def data():
    """Read the data from the web or local file, returning structured format such as a data frame"""
    raise NotImplementedError


"""
DATABASE CONNECTION:
Create a connection to where the data to address will be stored.

First ask the user for the database address.

Then ask them to provide the username and password for the database so that it can be stored safely in a yaml file.

Then create a connection to that database and return that connection.

"""
# Code for requesting and storing credentials (username, password) here. 
import yaml
from ipywidgets import interact_manual, Text, Password
import pymysql
def write_credentials(username, password):
    with open("credentials.yaml", "w") as file:
        credentials_dict = {'username': username, 
                            'password': password}
        yaml.dump(credentials_dict, file)

def create_connection(user, password, host, database, port=3306):
    """ Create a database connection to the MariaDB database
        specified by the host url and database name.
    :param user: username
    :param password: password
    :param host: host url
    :param database: database
    :param port: port number
    :return: Connection object or None
    """
    conn = None
    try:
        conn = pymysql.connect(user=user,
                               passwd=password,
                               host=host,
                               port=port,
                               local_infile=1,
                               db=database
                               )
    except Exception as e:
        print(f"Error connecting to the MariaDB Server: {e}")
    return conn

#Code for connecting to a database given credentials
def create_database_connection(databaselocation):
    database_details = {"url": databaselocation, 
                    "port": 3306}
    with open("credentials.yaml") as file:
        credentials = yaml.safe_load(file)
    username = credentials["username"]
    password = credentials["password"]
    url = database_details["url"]
    conn = create_connection(user=credentials["username"], 
                         password=credentials["password"], 
                         host=database_details["url"],
                         database="uk_ppd")
    return conn

'''
DATABASE CREATION:
Create a database for handling the data we need for analysing UK houseprices.

This initially takes two parts:
Task B in the python notebook corresponds to the upload of price paid data of housing property sold for value between 1995-01-01 and the laast month 
(at time of writing this is 2022)

Task C in the python notebook corresponds to the upload of postcode data for the UK, this will allow us to give approximate latitudes and longitudes to each property.
This approximation of latitude and longitude can have an error of a few miles, as postcodes are calculated by the number of unique addresses (so a new housing development may cause a postcode to split) and the number of parcels delivered to a postcode per day. (Large postcodes receive more parcels than small postcodes)
Postcodes are added and deprecated frequently, so this data should be reviewed frequently.
Source: https://www.ons.gov.uk/methodology/geography/ukgeographies/postalgeography
One thing to consider is that postcodes do not necessarily align with other geographical boundaries, so they may not lie within one ward or constituency.

Task D joins the two tables created by joining them into a table where paid price data matches to the approximate latitude and longitude of the property.
'''

def create_ppd_table(conn):
    cur = conn.cursor()
    cur.execute(
        """
        DROP TABLE IF EXISTS `pp_data`;
        """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS `pp_data` (
            `transaction_unique_identifier` tinytext COLLATE utf8_bin NOT NULL,
            `price` int(10) unsigned NOT NULL,
            `date_of_transfer` date NOT NULL,
            `postcode` varchar(8) COLLATE utf8_bin NOT NULL,
            `property_type` varchar(1) COLLATE utf8_bin NOT NULL,
            `new_build_flag` varchar(1) COLLATE utf8_bin NOT NULL,
            `tenure_type` varchar(1) COLLATE utf8_bin NOT NULL,
            `primary_addressable_object_name` tinytext COLLATE utf8_bin NOT NULL,
            `secondary_addressable_object_name` tinytext COLLATE utf8_bin NOT NULL,
            `street` tinytext COLLATE utf8_bin NOT NULL,
            `locality` tinytext COLLATE utf8_bin NOT NULL,
            `town_city` tinytext COLLATE utf8_bin NOT NULL,
            `district` tinytext COLLATE utf8_bin NOT NULL,
            `county` tinytext COLLATE utf8_bin NOT NULL,
            `ppd_category_type` varchar(2) COLLATE utf8_bin NOT NULL,
            `record_status` varchar(2) COLLATE utf8_bin NOT NULL,
            `db_id` bigint(20) unsigned NOT NULL
        ) DEFAULT CHARSET=utf8 COLLATE=utf8_bin AUTO_INCREMENT=1 ;
        """)
    cur.execute(
        """
        ALTER TABLE `pp_data`
        ADD PRIMARY KEY (`db_id`);
        """
        )
    cur.execute(
        """
        ALTER TABLE `pp_data`
        MODIFY `db_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=1;
        """
    )
    cur.execute("""
    CREATE INDEX `pp.postcode` USING HASH
        ON `pp_data`
            (postcode);
        """)
    cur.execute("""
    CREATE INDEX `pp.date` USING HASH
        ON `pp_data` 
            (date_of_transfer);
        """)
    conn.commit()
    print("Paid price data table created with table name `pp_data`")
    
def create_postcode_data_table(conn):
    cur = conn.cursor()
    '''
    --
    -- Table structure for table `postcode_data`
    --
    '''
    cur.execute(
        """
            DROP TABLE IF EXISTS `postcode_data`;
        """
    )
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS `postcode_data` (
        `postcode` varchar(8) COLLATE utf8_bin NOT NULL,
        `status` enum('live','terminated') NOT NULL,
        `usertype` enum('small', 'large') NOT NULL,
        `easting` int unsigned,
        `northing` int unsigned,
        `positional_quality_indicator` int NOT NULL,
        `country` enum('England', 'Wales', 'Scotland', 'Northern Ireland', 'Channel Islands', 'Isle of Man') NOT NULL,
        `lattitude` decimal(11,8) NOT NULL,
        `longitude` decimal(10,8) NOT NULL,
        `postcode_no_space` tinytext COLLATE utf8_bin NOT NULL,
        `postcode_fixed_width_seven` varchar(7) COLLATE utf8_bin NOT NULL,
        `postcode_fixed_width_eight` varchar(8) COLLATE utf8_bin NOT NULL,
        `postcode_area` varchar(2) COLLATE utf8_bin NOT NULL,
        `postcode_district` varchar(4) COLLATE utf8_bin NOT NULL,
        `postcode_sector` varchar(6) COLLATE utf8_bin NOT NULL,
        `outcode` varchar(4) COLLATE utf8_bin NOT NULL,
        `incode` varchar(3)  COLLATE utf8_bin NOT NULL,
        `db_id` bigint(20) unsigned NOT NULL
    ) DEFAULT CHARSET=utf8 COLLATE=utf8_bin AUTO_INCREMENT=1 ;
        """
    )
    cur.execute(
        """
        ALTER TABLE `postcode_data`
        ADD PRIMARY KEY (`db_id`);
        """
        )
    cur.execute(
        """
        ALTER TABLE `postcode_data`
        MODIFY `db_id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,AUTO_INCREMENT=1;
        """
    )
    cur.execute(
        """
        CREATE INDEX `po.postcode` USING HASH
            ON `postcode_data`
                (postcode);
        """
    )
    conn.commit()
    print("postcode data table created with table name `postcode_data`")
    
def create_postcode_prices_data(conn):
    return NotImplementedError

"""
Now fill the databases with the existing data from the websites
"""

import urllib
import pandas as pd
import os

def load_files_to_table(filename,conn,table):
    cur = conn.cursor()
    cur.execute(f"""LOAD DATA LOCAL INFILE '{filename}' INTO TABLE {table}
    FIELDS TERMINATED BY ',' 
    OPTIONALLY ENCLOSED BY '"'
    LINES STARTING BY '' TERMINATED BY '\n';""")
    conn.commit()
    print(filename)

def upload_ppd_by_year_2parts(year,conn):
  filename = f" http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-{year}-part1.csv"
  urllib.request.urlretrieve(filename,f"pp_{year}_p1.csv")
  load_files_to_table(f"pp_{year}_p1.csv",conn,"pp_data")
  os.remove(f"pp_{year}_p1.csv") 
  filename = f" http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-{year}-part2.csv"
  urllib.request.urlretrieve(filename,f"pp_{year}_p2.csv")
  load_files_to_table(f"pp_{year}_p2.csv",conn,"pp_data")
  os.remove(f"pp_{year}_p2.csv") 

import datetime

def load_price_paid_data_to_year(startyear,year,conn):
    for i in range(startyear,year-1):
        upload_ppd_by_year_2parts(i,conn)
    if year ==  datetime.date.today().year: #the current year of paid price data is always just one file, as it is updated monthly
        filename = f" http://prod.publicdata.landregistry.gov.uk.s3-website-eu-west-1.amazonaws.com/pp-{year}.csv"
        urllib.request.urlretrieve(filename,f"pp_{year}.csv")
        load_files_to_table(f"pp_{year}.csv",conn,"pp_data")
        os.remove(f"pp_{year}.csv") 
    else:
        upload_ppd_by_year_2parts(year,conn)

import zipfile

def load_postcode_data(conn):
    postcode_data_url = ' https://www.getthedata.com/downloads/open_postcode_geo.csv.zip'
    _,msg=urllib.request.urlretrieve(postcode_data_url,'open_postcode_geo.csv.zip')
    with zipfile.ZipFile('/content/open_postcode_geo.csv.zip','r') as zip_ref:
        zip_ref.extractall('/content/nopen_postcode_geo.csv.zip')
    load_files_to_table("open_postcode_geo.csv",conn,"postcode_data")
    
