import pandas as pd
import urllib
import io
from collections import Counter, defaultdict
import re
import time
import numpy as np
import tqdm
import os, glob
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium import webdriver



# TODO: argparse to identify most recent N or from DATE til DATE
pass


# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

sheet_url = 'https://docs.google.com/spreadsheets/d/1_E4mfSaYOHRv4cvq8ob6krQ1jxId4S9pH0W0D8aCbC4/edit?usp=sharing'
page = client.open_by_url(sheet_url)

house_sheet = page.worksheet('house')



# Get existing data (to avoid inserting a row that is already scraped)
records = house_sheet.get_all_records()
seen_document_numbers = set([row['LEGISLATION_NUMBER'] for row in records])
print len(seen_document_numbers )




# TODO: do we have an up-to-date csv already? (no need to spam the website if re-running this)
pass


house_url = 'https://www.congress.gov/advanced-search/legislation?congresses%5B0%5D=116&legislationNumbers=&restrictionType=field&restrictionFields%5B0%5D=allBillTitles&restrictionFields%5B1%5D=summary&summaryField=billSummary&enterTerms=&wordVariants=true&legislationTypes%5B0%5D=hr&legislationTypes%5B1%5D=s&public=true&private=true&chamber=all&actionTerms=&legislativeActionWordVariants=true&dateOfActionOperator=equal&dateOfActionStartDate=&dateOfActionEndDate=&dateOfActionIsOptions=yesterday&dateOfActionToggle=multi&legislativeAction=Any&sponsorState=One&member=&sponsorTypes%5B0%5D=sponsor&sponsorTypes%5B1%5D=sponsor&sponsorTypeBool=OR&committeeActivity%5B0%5D=any&committeeActivity%5B1%5D=referred+to&committeeActivity%5B2%5D=hearings+by&committeeActivity%5B3%5D=markup+by&committeeActivity%5B4%5D=reported+by&committeeActivity%5B5%5D=reported+original+measure&committeeActivity%5B6%5D=discharged+from&committeeActivity%5B7%5D=legislative+interest&satellite=%5B%5D&search=&submitted=Submitted&searchResultViewType=expanded&q=%7B%22chamber%22%3A%22House%22%7D'

# Open selenium browser
browser = webdriver.Chrome()
browser.get(house_url)

# click the 'Download Results' button
download_button = browser.find_element_by_link_text('Download Results')
download_button.click()

# confirm the download by clicking 'OK'
dialog = browser.find_element_by_id('download-csv-dialog')
buttons = dialog.find_elements_by_class_name('button')
ok_button = [b for b in buttons if b.text=='OK'][0]
ok_button.click()

# close the browser (hopefully 5 seconds is enough time to download in general)
# idk how to check download action was successful before closing
time.sleep(5)
browser.close()




# note: point to your own download folder
download_folder = '/Users/wboag/Downloads'
house_downloads = glob.glob('%s/search_results_*.csv' % download_folder)
most_recent_download = sorted(house_downloads)[-1]

# todo: make sure the date matches
match = re.search('search_results_(\d+)-(\d+)-(\d+)_(\d+)(\w+).csv', most_recent_download)
year,month,day,time_of_day,is_am = match.groups()
pass # this is where one would do the time comparison (e.g. within 5 min)

# for some reason, the first three lines of the file are not csv format (its download metadata)
with open(most_recent_download, 'r') as f:
    text = f.read()
text = text[text.index('"Legislation Number"'):]
with open(most_recent_download, 'w') as f:
    f.write(text)




house_df = pd.read_csv(most_recent_download)
assert all(house_df.Committees.str.startswith('House')), 'error: read wrong csv. please clear ~/Downloads/search_results* just to be safe'





# insert into sheet

columns = house_sheet.row_values(1)
print columns

inserted_count = 0
for _,row in house_df.head(n=50)[::-1].iterrows():

    legislation_number = row['Legislation Number']
    if legislation_number in seen_document_numbers: continue

    name = row['Title']
    date = row['Date of Introduction']
    policy_topic = ''
    status = ''
    committee = row['Committees']
    sponsor = row['Sponsor']
    url = row['URL']

    # determine the status
    'Date of Introduction	Date Offered	Date Submitted	Date Proposed'
    if not np.isnan(row['Date Proposed']):
        status = 'Proposed'
    elif not np.isnan(row['Date Submitted']):
        status = 'Submitted'
    elif not np.isnan(row['Date Offered']):
        status = 'Offered'
    else:
        status = 'Introduced'

    # 'NAME, u'DATE','POLICY TOPIC', 'STATUS','COMMITTEE','SPONSOR','LEGISLATION_NUMBER','URL'
    out = [name, date, '', status, committee, sponsor, legislation_number, url]

    # insert row
    house_sheet.insert_row(out, 2)

    seen_document_numbers.add(legislation_number)
    inserted_count += 1

    #break

print 'inserted %d rows' % inserted_count

