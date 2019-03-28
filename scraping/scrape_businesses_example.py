#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Creates a csv file with Yelp url's for all businesses in your Yelp search result.

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
    listOverall = []
    driver, wait = startDriver()

    # Use url to the Yelp page with search results
    url = 'https://www.yelp.com/search?find_desc=coffee%20shop&find_loc=New%20York%2C%20NY&attrs=WiFi.free'

    driver.get(url)

    pageLoaded = wait.until(EC.visibility_of_element_located((By.ID,"wrap")));
    soup = BeautifulSoup(driver.page_source, 'lxml')
    currentPage = []
    page = 0

    while(True):
        print('Searching: ',city,' on page: ',page)

        # View the source code of the web results page in a browser to find the input for findAll()
        for link in soup.findAll('a', class_="lemon--a__373c0__1_OnJ link__373c0__29943 link-color--blue-dark__373c0__1mhJo link-size--inherit__373c0__2JXk5"):
            biz_url = link.get('href')
            currentItem = [biz_url]
            currentPage.append(currentItem)

        try:
            # Again, look at the source code of the web page, input will depend on what you're looking for, in this case a business url.
            nextURL = soup.find("a", class_="lemon--a__373c0__1_OnJ link__373c0__29943 next-link navigation-button__373c0__1D3Ug link-color--blue-dark__373c0__1mhJo link-size--default__373c0__1skgq")["href"]
            nextURL = "https://www.yelp.com" + nextURL

            #nextURL = driver.findElement(By.linkText("next")).getAttribute("href");
            #nextURL = driver.find_element_by_xpath("//a[@class='u-decoration-none next pagination-links_anchor']").get_attribute('href')
            driver.get(nextURL)
            page = page + 1
            pageLoaded = wait.until(EC.visibility_of_element_located((By.ID,"wrap")));
            soup = BeautifulSoup(driver.page_source, 'lxml')
        except:
            listOverall=listOverall+currentPage
            break
    driver.quit()
    return listOverall


# Yelp code of the city you're searching in
listCities = ['New%20York%2C%20NY&attrs']


columns = ['biz_url']
import time


for city in listCities:
    listOverall = startThread(city)
    output = pd.DataFrame.from_records(listOverall, columns=columns)
    output2 = [x for x in output['biz_url'] if x.startswith('/biz')]
    B = ['hrid=']
    blacklist = re.compile('|'.join([re.escape(word) for word in B]))
    output3 = [word for word in output2 if not blacklist.search(word)]
    output3 = pd.DataFrame(output3)
    output3.columns=["biz_url"]
    now = time.strftime("%Y%m%d-%H%M%S")
    output_csv = 'scraped_data/'+city+'_businesses_v'+now+'.csv'   # change path to your data directory
    output3.to_csv(output_csv)
