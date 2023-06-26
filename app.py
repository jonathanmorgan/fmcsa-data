import pandas as pd
from bs4 import BeautifulSoup

from pathlib import Path 
import shutil
import os
import urllib.request
import re
from dotenv import load_dotenv

import sqlalchemy as sa
from sqlalchemy import text

from time import sleep

load_dotenv()
DBNAME = os.environ["POSTGRES_DB"]
USER = os.environ["POSTGRES_USER"]
PASS = os.environ["POSTGRES_PASSWORD"]
HOST = os.environ["HOST"]

def main():
    ENGINE = sa.create_engine(f"postgresql://{USER}:{PASS}@{HOST}:5432/{DBNAME}")

    # create database for data , it they don't exist
    # todo - come up with a better schema
    query = """
        CREATE TABLE IF NOT EXISTS cargo (
            carrier_id integer NOT NULL,
            date_pulled text,
            cargo_carried text ARRAY
        );


        CREATE TABLE IF NOT EXISTS vehicles (
            carrier_id integer NOT NULL,
            type text,
            date_pulled text,
            owned integer,
            term_leased integer,
            trip_leased integer
        );

        SELECT COUNT(DISTINCT carrier_id) FROM cargo;
    """
    #create table if details
    with ENGINE.connect() as con:
        result = con.execute(text(query))
        #print(result.fetchall())
        con.commit()

    #get the latest download link for the zip
    def getHTMLContent(url):
        res = urllib.request.urlopen(url)
        return res.read().decode("utf-8")
    def getSoup(url):
        return BeautifulSoup(getHTMLContent(url), "html.parser")

    soup = getSoup('https://ai.fmcsa.dot.gov/SMS/Tools/Downloads.aspx')
    link = soup.find("ul", class_="downloadLinks").find("a")["href"]

    DOWNLOAD_URL = 'https://ai.fmcsa.dot.gov' + link
    ZIP_NAME = Path(link).name

    print('pulling data from', DOWNLOAD_URL, ZIP_NAME)

    #setup raw folder and download the latest Motor Carrier Census Information
    RAW_DATA_FOLDER = Path('./raw')
    if not RAW_DATA_FOLDER.exists():
        os.mkdir(RAW_DATA_FOLDER)
        
    ZIP_FILE = RAW_DATA_FOLDER / ZIP_NAME
    if not ZIP_FILE.exists():
        print(f'DOWNLOADING {ZIP_NAME}')
        urllib.request.urlretrieve(DOWNLOAD_URL, ZIP_FILE)
        print(f'EXTRACTING')
        shutil.unpack_archive(ZIP_FILE, RAW_DATA_FOLDER)

    # --- Step 2 - Read and filter entries ---

    #read the latest spreadsheet to get carrier ids
    FMCSA_DF = pd.read_csv(RAW_DATA_FOLDER / ZIP_NAME.replace('.zip','.txt'), encoding = 'latin-1')

    #check entires that already exist in the database
    query = f"""
        SELECT carrier_id, date_pulled from cargo 
    """
    already_scraped = pd.read_sql(text(query), con = ENGINE)

    #create a subselection, not scraped already
    FMCSA_SUB = FMCSA_DF[~FMCSA_DF['DOT_NUMBER'].isin(already_scraped['carrier_id'])].reset_index()
    print(len(FMCSA_DF) - len(FMCSA_SUB), 'already scraped')


    # --- Step 3 - Scrape ---

    def scrapeDataAndAppendToDB(carrier_id):
        url = f'https://ai.fmcsa.dot.gov/SMS/Carrier/{carrier_id}/CarrierRegistration.aspx'
        html_content = getHTMLContent(url)
        soup = getSoup(url)
        
        #get date
        date = re.search('(\d*\/\d*\/\d*)',soup.find("span", class_="asOf").text)
        if date:
            date = date.group()
        else:
            date = 'Unknown'
            
        
        # --- vehicle_type
        vehicle_type_df = pd.read_html(html_content)[0]
        #filter out those without any value s in Owned, Term Leased, Trip Leased
        filt_df = vehicle_type_df[(vehicle_type_df[['Owned', 'Term Leased', 'Trip Leased']] > 0).any(axis=1)].copy()
        #rename columns to match sql
        filt_df.columns = ['type','owned','term_leased','trip_leased']
        #add identifiers
        filt_df['date_pulled'] = date
        filt_df['carrier_id'] = carrier_id
        filt_df.to_sql('vehicles', con=ENGINE, if_exists= 'append', index = False)
        
        
        # --- cargo
        cargo_ul = soup.find("ul", class_="cargo")
        cargo_li_checked = cargo_ul.find_all("li", class_="checked")

        # clean up list items and convert to postgres array 
        cargo_carried = '{'+ ','.join([li.text.lstrip('X').rstrip(',') for li in cargo_li_checked]) + '}'

        cargo_df = pd.DataFrame([{'cargo_carried': cargo_carried, 'carrier_id': carrier_id, 'date_pulled': date}])
        cargo_df.to_sql('cargo', con=ENGINE, if_exists= 'append', index = False)
        
        # avoid rate limits, maybe?
        sleep(0.01)
        
        # return basic stats for debuging
        return pd.Series([url, cargo_carried, 
                        filt_df[['type','owned','term_leased','trip_leased']].to_dict(orient = 'records')])


    def run(row):
        #print once in a while
        if row.name % 25 == 0:
            print('on row', row.name, 'of', len(FMCSA_SUB))
        return scrapeDataAndAppendToDB(row['DOT_NUMBER'])


    #FMCSA_SUB[:].apply(run, axis = 1)
    FMCSA_SUB[:1000].apply(run, axis = 1)

if __name__ == "__main__":
    print('Running Script')
    main()
    print('Done!')