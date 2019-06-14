# gov_scan
Scrape public, government data into one easier-to-manage location!



Installation

    - python
		- python libraries (pip install -r requirements.txt)

    - chromedriver
        - GOAL: get the 'chromedriver' executable to be runnable when "browser = webdriver.Chrome()" executes
        - https://www.kenst.com/2015/03/installing-chromedriver-on-mac-osx/
		- https://www.kenst.com/2015/03/including-the-chromedriver-location-in-macos-system-path/

    - Connecting to the Google Sheet
        - TODO: do you need to turn on the API yourself?
            - hopefully we can just use link-sharing for the sheet instead...


Running it

    - TODO: set your Downloads directory path



What it does so far

    - Scrapes federal register (regs sheet)

    - Scrapes house bills (house sheet)

    - Scrapes senate bills (senate sheet)




What it doesnt do yet

    - scrapes the committee hearing pages (each committee has their own page/format)
		- I also plan to write an "update" script that makes sure committee pages have the witness lists & testimonies downloaded as well
		- note: this project will need to be updated AT LEAST every other yet (for each new Congress)

    - get more than 50 rows, so it doesnt yet get everything
		- Currently working on doing bulk inserts instead of individual inserts (which get throttled)
		- If you wanted to get the csv and import it into google sheets manually, we can do that

    - specify "only get the most recent N rows" or "get all rows from DATE to DATE"
