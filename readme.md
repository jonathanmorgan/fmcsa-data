# USDOT web scraping challenge

## Overview System Design and Approach

This task calls for

- Getting `Cargo Carried` and `Vehicle Type Breakdown` from the Carrier Registration page for each carrier_id in **Motor Carrier Census Information** Dataset since the columns do not exist

--- 
1. I chose to use a database since it is more efficient compared to using one large .csv or many .csv files for reads/writes and joining to the larger census information later on. Two database tables are created (`cargo` and `vehicles`). `carrier_id` and `date_pulled` are included for reference and joining. Refer to the example csv files for output.
2. To obtain the latest FMCSA motor carrier IDs, I scrape the span with the `downloadLinks` class from [/SMS/Tools/Downloads.aspx](https://ai.fmcsa.dot.gov/SMS/Tools/Downloads.aspx).
3. FMCSA is downloaded, extracted, and read. The database is queried to see what carrier IDs already have data. The query can be modified later on to check if entries have a `date_pulled` less than a month ago. FMCSA is filtered down and saved as the variable `FMCSA_SUB`.
4. The Pandas `apply` function now goes through every row and scrapes the data using BeautifulSoup and Pandas' built-in `read_html` function for the vehicles table.
5. The data is cleaned up and appended to the database.
6. If the script fails, it can be rerun and will start from where it left off due to `FMCSA_SUB` containing only carrier IDs without scrapped data.
7. Everything can be run with docker-compose, making it easy to set up for use on the cloud or for someone else to run overnight. Alternatively, the `.env` file can be edited to connect to any Postgres database. (there is a bug where in the Dockerfile where it does not print any of python's messages but it is running ...)

### Next steps

- Split app.py into modules to provide a better experience finding database vs scraping code.
- Visit multi-threading / sub-processes to reduce the time it takes. Might need proxies to avoid rate limits. ie. `urllib.error.HTTPError: HTTP Error 502: Bad Gateway`
- Add Try and Except that write to a log file and contiune to avoid the whole program crashing when there are edge cases
- Uploading FMCSA csv to allow for joins and figure out a better schema to host different version of FMCSA and scapped data since it updates monthly.
- Better schema for `cargo` and `vehicles` tables?
- For some reason docker does not show any of the print message with docker-compose-wait
- Test more cases!! Only went through 5k entries. I am sure there are issues like the on mentioned.

### How to convert to this script so it run from csvs instead

Having a database might be "overkill". To convert the script to run from csvs `cargo` and `vehicles` rows can be written into `{carrier_id}_{date_pulled}.csv` using pd.to_csv instead of pd.to_sql. A list of file names can be pulled using glob.glob('*.csv') or pathlib to replace already_scraped dataframe.

## Run

### If you are using Docker

`docker-compose up` 

### If you are using python

- Have a postgres instance on port 5432 and edit the `.env` file with username, password, database name, and set `HOST` to localhost or ip your server
- Python 3 installed create a new enviormenet `conda create -n fmcsa python=3.8`  and `conda activate fmcsa`
- Run `pip install -r requirements.txt` or `pip install pandas beautifulsoup4 psycopg2 SQLAlchemy python-dotenv lxml`
- Run `python app.py`

## Interactive development

To see what each line of the script does use the jupyter notebook `playground.ipynb`.