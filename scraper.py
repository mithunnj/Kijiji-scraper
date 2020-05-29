import requests
from bs4 import BeautifulSoup
import sys
import json
from twilio.rest import Client
import os
from datetime import datetime
import time


# Base URL to perform Kijiji webscraping on - provide the URL from the first page (not any of the numbered pages)
BASE_URL = "https://www.kijiji.ca/b-bikes/ottawa/bike/k0c644l1700185?radius=104.0&gpTopAds=y&address=Ottawa%2C+ON&ll=45.421530,-75.697193"

# Print terminal colours
CRED = '\033[91m'
CGREEN  = '\33[32m'
CEND = '\033[0m'

# List of bike companies to do a keyword search for - NOTE: keep it lowercase.
BIKE_LIST = [
    "specialized",
    "giant", 
    "cervelo"
    "cannondale"
    "norco"
    "trek"
    "ridley"
    "opus"
    "cube"
    "bianci"
    "canyon"
    "pinnacle"
    "brodie"
    "salsa"
    "scott"
    "ultegra"
    "dura ace"
    "zipp"
    "look"
    "fuji"
]

OLD_LISTINGS = dict() # Store of all the listings that we have already be notified about

# Twilio API credentials
ACCOUNT_SID = os.environ.get('KIJIJI_TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.environ.get('KIJIJI_TWILIO_AUTH_TOKEN')
HOST_NUMBER = os.environ.get('KIJIJI_TWILIO_NUMBER')
NUMBERS = [
	"+16138831157",
	"+16138644591"
]

# Helper functions

def site_content(url):
    """
    param: url <str> : Kijiji website URL from the first page
    return: requests.content <request obj> : These are the HTML contents of the requests module
    """

    # Fetch URL content using requests module. The return will be an HTML Status code as described here: 
    # https://www.restapitutorial.com/httpstatuscodes.html
    result = requests.get(url)

    if result.status_code == 200: # Successfully fetched contents
        return result.content
    else:
        print("Failed to load content from the following URL: {}".format(url))
        sys.exit(1)

def listing_IO(content=False):
    """
    param: content <bool> : Default is set to false so that we don't overwrite our OLD_LISTINGS information
        True means that we have OLD_LISTINGS to write to the backup listings.json file. This will overwrite the file. 
    return: None
    """

    global OLD_LISTINGS # I know it's bad form, but we want to refer to the global OLD_LISTINGS variable.

    # If there is content to write, overwrite the contents of the listings.json backup file.
    if content:
        with open('listings.json', 'w') as f:
            json.dump(OLD_LISTINGS, f)
            print('Successfully printed searched listings history to listings.json file.')
        f.close()
    else:
        with open('listings.json') as f:
            OLD_LISTINGS = json.load(f)
            print('Successfully loaded previously processed listings from the listings.json file.')
        f.close()

    return

def parse_site(site_content):
    """
    param: site_content <request.content obj>
    return:
        index <int> : This is the index that contains the first Kijiji listing from the a-href site content list.
        links <list> : List of all the a-href HTML tags from the site.
    """
    
    soup = BeautifulSoup(site_content, 'lxml') # Parse contents of the site using BeautifulSoup
    links = soup.find_all("a") # Find all the ahref tags

    index = 0 # Store the index of the ahref search as we find the first listing

    for link in links:
        if "Sign Up" in link.getText():
            index += 1
            return index, links
        else:
            index += 1


def send_text(number, message):
	"""
	param: number <str> : This is the outbound verified Twilio number that the message will be sent to.
	param: message <str> : This is the message to send to the Twilio number from above.
	"""
	client = Client(ACCOUNT_SID, AUTH_TOKEN)

	message = client.messages \
                .create(
                     body=message,
                     from_=HOST_NUMBER,
                     to=number
                 )

	return

def listing_notifier(index, content):
    """
    param: index <int> : This is the starting index from the site data with the listing information, skipping over all the unecessary site contents.
    param: content <bs4.element.ResultSet> (Beautiful soup content object) : This is the HTML content of the site that is parseable through BeautifulSoup object.
    return: None

    Grab the contents of the BeautifulSoup parseable content, and then loop through each listing searching for specific bike names. If there is a matching listing,
    it will notifier the admins through SMS message, and store the information locally.
    """

    # Loop through the listings and find title match to the bike models specified above
    for listing in range(index, len(content)):
        listing_title = content[listing].getText().strip()
        listing_href = content[listing]['href'].strip()

        if any(bike in listing_title.lower() for bike in BIKE_LIST) and listing_title not in OLD_LISTINGS.keys():

            print('POSITIVE: ', listing_title)
            message_url = "https://www.kijiji.ca" + listing_href

            for number in NUMBERS:
                send_text(number, "BIKE NOTIFIER for: \n - Listing title: {} \n - URL: {}".format(listing_title, message_url))
            print(CGREEN + 'Notified admins about the following listing: \n - Listing title: {} \n, - URL: {}'.format(listing_title, message_url) + CEND)
            
            # Store the listing information with Title, URL and Date metadata
            OLD_LISTINGS[listing_title] = {
                "URL": listing_href,
                "Date": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
        else:
            continue

    return

def gen_url(url):
    """
    param: url <str> : This is the base url (the first page) of the search query.
    return: url_list <arr> : List containing pre-structured url's for subsequent pages of the base query.
    """
    url_list = list()
    url_list.append(url) # Store the base URL of search query

    for i in range(2,5):
        url_split = url.split('/')
        url_split.insert(6, "page-{}".format(i))
        url_list.append(("/".join(url_split)))

    return url_list
    
def main():
    """
    Main program execution.
    """

    # Init for the Kijiji scrapping process
    listing_IO(False) # Initialize the OLD_LISTINGS global store

    # Gen all the subpages of the search query
    url_list = gen_url(BASE_URL)

    # Loop through each page on the site
    for url in url_list:
        data = site_content(url) # Load the data from our Kijiji listing URL
        print("Loaded site content for the following url: {}".format(url))

        # Parse contents of the site
        start_ind, content = parse_site(data)

        # Loop through the listings and find title match to the bike models specified above
        listing_notifier(start_ind, content)

    # Write contents of processed listings to file as backup
    listing_IO(True)
    

while True:
    print(CGREEN + 'Starting Kijiji scraper for the following search query: {} \n'.format(BASE_URL) + CEND)

    main()
    sleep_time = 60*5

    print(CRED + "Finished program execution, sleeping for: {} \n".format(str(sleep_time)) + CEND)

    time.sleep(sleep_time) # Sleep for 5 min intervals

