**# USDOT web scraping challenge**

**## Overview System Design and Approach**

This task calls for

- Getting `Cargo Carried` and `Vehicle Type Breakdown` from the Carrier Registration page for each carrier_id in **Motor Carrier Census Information** Dataset since the columns do not exist

--- 
1. I chose to use a database since it is more efficient compared to using one large .csv or many .csv files for reads/writes and joining to the larger census information later on. Two database tables are created (`cargo` and `vehicles`). `carrier_id` and `date_pulled` are included for reference and joining. Refer to the example csv files.
2. To obtain the latest FMCSA motor carrier IDs, I scrape the `downloadLinks` URL from [/SMS/Tools/Downloads.aspx](https://ai.fmcsa.dot.gov/SMS/Tools/Downloads.aspx).
3. FMCSA is downloaded, extracted, and read. The database is queried to see what carrier IDs already have data. The query can be modified later on to check if entries have a `date_pulled` less than a month ago. FMCSA is filtered down and saved as the variable `FMCSA_SUB`.
4. The Pandas `apply` function now goes through every row and scrapes the data using BeautifulSoup and Pandas' built-in `read_html` function for tables.
5. The data is cleaned up and appended to the database tables.
6. If the script fails, it can be rerun and will start from where it left off due to `FMCSA_SUB` containing only carrier IDs without scrapped data.
7. Everything can be run with docker-compose, making it easy to set up for use on the cloud or for someone else to run overnight. Alternatively, the `.env` file can be edited to connect to any Postgres database.

### Next steps

- Split app.py into modules to provide a better experience finding database vs scraping code.
- Visit multi-threading / sub-processes to reduce the time it takes. Might need proxies to avoid rate limits. ie. `urllib.error.HTTPError: HTTP Error 502: Bad Gateway`
- Add Try and Except that write to a log file and contiune to avoid the whole program crashing when there are edge cases
- Uploading FMCSA csv to allow for joins and figure out a better schema to host different version of FMCSA and scapped data since it updates monthly.
- Better schema for `cargo` and `vehicles` tables.
- For some reason docker does not show any of the print message with docker-compose-wait. It is running.

## Run

Either use `docker-compose up` or

- have a postgres instance on port 5432 instance and edit the `.env` file with login, password, db name, and set `HOST` to localhost or your server
- python 3 installed and run `pip install -r requirements.txt` or have the following packages (pandas beautifulsoup4 psycopg2 SQLAlchemy python-dotenv lxml)