#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Creates a csv file with text scraped from reviews and other business info.

"""

#Marjolein Spronk
#Date last modified: 1/21/2019


# Import packages
import os, random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import glob


# Functions for scraping
def setOptions():
    options = webdriver.ChromeOptions();
    #options.add_argument('--/usr/lib/chromium-browser/chromedriver');
    options.add_argument('--disable-infobars');
    options.add_argument('--disable-dev-shm-usage');
    options.add_argument('--disable-extensions');
    options.add_argument('--headless');
    options.add_argument('--disable-gpu');
    options.add_argument('--no-sandbox');
    options.add_argument('--no-proxy-server')
    options.add_experimental_option("excludeSwitches", ["ignore-certificate-errors"]);
    return options

#webdriver.Chrome('/usr/lib/chromium-browser/chromedriver')
def getNextPage(driver, wait):
    nextURL = driver.find_element_by_xpath("//a[@class='u-decoration-none next pagination-links_anchor']").get_attribute('href')
    soup = finishLoadGrabSource(nextURL, driver, wait)
    return soup

def finishLoadGrabSource(url, driver, wait):
    # This overlay with class='throbber-overlay' disappears when Yelp loads
    loadingCondition = EC.invisibility_of_element_located((By.CLASS_NAME,'throbber'))
    try:
        driver.get(url)
        pageLoaded = wait.until(loadingCondition);
        soup = BeautifulSoup(driver.page_source, 'lxml')
        return soup
    except:
        print('Page failed to load, or browser time out')
        pass;

def getBusinessDetails(s):
    return [s.at['biz_url']]

def startDriver():
    options = setOptions()
    driver = webdriver.Chrome(chrome_options=options);
    #need implicit wait or else some pages timeout
    #driver.implicitly_wait(10)
    wait = WebDriverWait(driver, 30);
    return driver, wait

def quitDriver(driver):
    driver.close();
    driver.quit();

def startThread(city):
    # This block is using the saved business csv
    filepath = glob.glob('scraped_data/'+city+'_businesses_v*.csv');
#    if len(filepath)==0:
#        path doesnt exist
#        df = scrapeBusinesses(city)
#    elif len(filepath==1):
    if(len(filepath)==1):
        path = filepath[0]
        df = pd.read_csv(path)
    elif (len(filepath)>1):
        print('WARNING: more than 1 city file for city')
        return False

    driver, wait = startDriver()
    listOverall=[];
    # Using the dataframe of scraped businesses, going through them one by one to get the review and other data
    totalPages = df.index.size
    for i in df.index:
        business=i+1
        print('Scraping Reviews for: ',city,' Business: ',business)


        url='https://www.yelp.com'+df.at[i,'biz_url']
        bizList = getBusinessDetails(df.loc[i])


        # This if statement shuts down and restarts the webdriver
        # every 50 pages to prevent slow down over time
        if( (i>0) & (i % 20 == 0)):
            quitDriver(driver)
            driver, wait = startDriver()

        # Open the page, wait for it to load
        # Then pass the source to BS as lxml (faster than html.parser)
        soup = finishLoadGrabSource(url, driver, wait)

        # Input for findAll function will depend on specific search/needs: view the webpage source code
        for div in soup.find_all("div", class_ = "content-container js-biz-details"):
            try:
                biz_name = div.find("meta", itemprop = "name")
                biz_name = biz_name['content']
            except:
                biz_name="NA"
            try:
                biz_phone = div.find("span", itemprop = "telephone").get_text()
            except:
                biz_phone="NA"
            try:
                biz_rating = div.find("meta", itemprop = "ratingValue")
                biz_rating = biz_rating['content']
            except:
                biz_rating="NA"
        # Initialize list to hold all the info for each business
        # This list has every review+business-details as each element
        currentBizList = []
        bizList = [bizList[0], biz_rating,biz_name,biz_phone]

        while(True):

            # Iterate over all review blocks
            for rev in soup.find_all("div", itemprop = "review"):

                try:
                    review_name = rev.find("meta", itemprop = "author")
                    review_name = review_name['content']
                except:
                    review_name="NA"
                try:
                    review_rating = rev.find("meta",  itemprop = "ratingValue")
                    review_rating = review_rating['content']
                except:
                    review_rating = "NA"
                try:
                    review_date = rev.find("meta",  itemprop = "datePublished")
                    review_date = review_date['content']
                except:
                    review_date = "NA"
                try:
                    review_text = rev.find('p', attrs={'itemprop': 'description'}).get_text()
                except:
                    #review text doesn't exits so skipping
                    review_text="";
                    continue
                reviewList = [review_name,review_rating,review_date,review_text]
                currentBizList.append(reviewList+bizList)

# When the for loop above finishes, see if there is a
# "Next Page" link that's clickable. If so, keep going
            try:
                soup = getNextPage(driver, wait)

            except:
# The following gets called if the try command fails with an error, and can't
# find a next page link, meaning that there are no more reviews.
# Save the lists, +sign means add to the end & not nest the lists with append.
                listOverall=listOverall+currentBizList
                break

    driver.quit()
    return listOverall



# Get the reviews and save in a csv file
columns = ['biz_url']
import time
city = 'New%20York%2C%20NY&attrs'

dir_path = 'scraped_data/'
extension = '.csv'
# The columns of the final dataframe output
columns = ['review-name','review-rating','review-date','review-text','biz_url','biz_rating','biz_name','biz_phone']
city_name = city

#for city in listCities:   #uncheck if using a loop for multiple cities
listOverall = startThread(city)
output = pd.DataFrame.from_records(listOverall, columns=columns)

now = time.strftime("%Y%m%d-%H%M%S")

output_csv = dir_path+city_name+now+extension
output.to_csv(output_csv)
