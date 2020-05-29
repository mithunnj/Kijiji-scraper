# Kijiji-scraper

This tool was made to scrape listings given a Kijiji query, and notify the user to listings that are relevant based on user-defined brands. This was implemented to track new bike listings in the Ottawa area. 

## Dev setup on local system

The script has dependencies that need to be addressed to enable this system.You need to define the following environment variables:

1. TWILIO_ACCOUNT_SID: This can be retrieved from the Twilio console. 
2. TWILIO_AUTH_TOKEN: This can be retrieved from the Twilio console.
3. TWILIO_NUMBER: This is the Twilio generated number that will be used to send messages to authorized numbers. 

## Things to fix:
- Construct a vaild URL (need to include https://www.kijiji.com... + page info) in the text message that is sent.
- Write a docstring for listing_notifier function.
- Loop through multiple pages and ensure that nothing breaks. Note all pages after page 2 have an additional parameter in the URL.
- Make the program sleep to limit the number of times it scrapes.
