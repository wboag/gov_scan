import pandas as pd
import requests
import io
import re
import time
import tqdm
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# cache due dates (to avoid repeatedly querying in notebook)
dates_due = {}


# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

sheet_url = 'https://docs.google.com/spreadsheets/d/1_E4mfSaYOHRv4cvq8ob6krQ1jxId4S9pH0W0D8aCbC4/edit?usp=sharing'
page = client.open_by_url(sheet_url)



regs_sheet = page.worksheet('regs')

# Get existing data (to avoid inserting a row that is already scraped)
records = regs_sheet.get_all_records()
seen_document_numbers = set([row['DOCUMENT_NUMBER'] for row in records])
print(len(seen_document_numbers ))



# Access the federal register via the following link: https://www.federalregister.gov
# Navigate to the search button at the top of the page and click on "advanced search"
# Narrow the search to "proposed rules" and click "search"
query_url = 'https://www.federalregister.gov/documents/search.csv?conditions%5Btype%5D%5B%5D=PRORULE'
response = requests.get(query_url)
text = response.text
text = '\n'.join(text.split('\n')[:-1]) # for some reason, the final line isnt full. skip it

regs_df = pd.read_csv(io.BytesIO(text.encode()))
regs_df.head()

recent_document_numbers = reversed(regs_df.document_number.values[:50])

# index regs by document number
regs = {}
for _,row in regs_df.iterrows():
    regs[row['document_number']] = row[['publication_date','title','agency_names','abstract','document_number','html_url']]

regs_df[['publication_date','title','agency_names','abstract','document_number','html_url']]




columns = regs_sheet.row_values(1)
print(columns)

inserted_count = 0
for document_number in tqdm.tqdm(recent_document_numbers):
    # todo: should probably go in actual order cuz then could quickly break
    if document_number in seen_document_numbers or type(document_number)==type(0.0): continue

    reg = regs[document_number]

    title = reg['title'].replace(',', ' -- ')
    date_introduced = reg['publication_date']
    date_due = 'UNK'
    agency = reg['agency_names'].replace(',', ';')
    url = reg['html_url']
    abstract = reg['abstract']
    if type(abstract) == type(''):
        abstract = abstract.replace(',', ' -- ')
    else:
        abstract = ''

    # read due date from the page
    if document_number not in dates_due:
        response = requests.get(reg.html_url)
        text = response.text
        match = re.search('Comments Close:.*?(\d+/\d+/\d+)</dd>', text, re.DOTALL)
        if match:
            date_due = match.groups()[0]
        dates_due[document_number] = date_due
    else:
        date_due = dates_due[document_number]

    # NAME	DATE INTRODUCED	DATE COMMENTS DUE	RELATED RESEARCH
    out = [title, agency, date_introduced, date_due, '', abstract, document_number, url]

    # insert row
    try:
        regs_sheet.insert_row(out, 2)
    except Exception:
        time.sleep(60)
        regs_sheet.insert_row(out, 2)

    seen_document_numbers.add(document_number)
    inserted_count += 1

print('inserted %d rows' % inserted_count)

