from __future__ import unicode_literals
from collections import OrderedDict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import bs4
import json
import re
import boto3
import time
import os

s3 = boto3.client('s3')
db = boto3.resource('dynamodb')
waitTime = 3

def lambda_handler(event, context):
    print('Event : ', event)

    searchPages = os.environ['searchPages']

    amazon_job( int(searchPages ) )

def saveDataInDynamoDB( data ):

    tableName = os.environ['tableName']
    print("Table Name : ", tableName)

    table = db.Table( tableName )

    item = {
        'job_id': data['job_id'],
        'job_post_date': data['job_post_date'],
        'job_title': data['job_title'],
        'job_location': data['job_location'],
        'job_link': data['job_link'],
        'job_description': data['job_description'],
        'job_qualification': data['job_qualification']
    }

    print("Item : ", item)

    table.put_item(Item=item)

def amazon_job(number_page=10):

    print("---start---")
    result = []

    for i in range(number_page):

        print( "PAGE NO ::: {} ::: ".format( i ) )

        # Currently 10 jobs per page
        # Sorting recent/relevant
        # &category[]=solutions-architect

        URL = "https://www.amazon.jobs/en/search?offset={}&result_limit=10&sort=recent&category[]=&country[]=USA&distanceType=Mi&radius=24km&latitude=&longitude=&loc_group_id=&loc_query=&base_query=&city=&country=&region=&county=&query_options=&".format(
            str(10 * i))

        options = Options()
        options.binary_location = '/opt/headless-chromium'
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--single-process')
        options.add_argument('--disable-dev-shm-usage')

        driver = webdriver.Chrome('/opt/chromedriver', chrome_options=options)
        # driver.get('https://www.google.com/')

        # driver = webdriver.PhantomJS()
        print( "URL : ", URL )

        time.sleep( waitTime )
        driver.get(URL)
        time.sleep( waitTime )

        job_title = []
        job_ids = []
        location = []
        posting_date = []
        job_link = []

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        print( "Main Soup : ", soup )
        print( soup.findAll("div", {"class": "job-tile"}) )

        for td in soup.findAll("div", {"class": "job-tile"}):

            jobLink = 'https://www.amazon.jobs' + td.find('a').get('href')
            print( "Job Link : ", jobLink )

            job_link.append(jobLink)

            jobLocTemp = td.find("p", {"class": "location-and-id"}).text
            jobLoc = jobLocTemp.split('|', 1)[0]
            location.append(jobLoc)

            jobId = jobLocTemp.split('|', 1)[1]
            jobId = re.sub('Job ID: ', '', jobId )
            jobId = jobId.strip()

            print( "Job ID >>> ", jobId )

            job_ids.append( jobId )

            jobTitle = td.find('h3').text
            job_title.append(jobTitle)

        for td in soup.findAll("h2", {"class": "posting-date"}):
            jobPostDate = re.sub('Posted ', '', td.text)
            posting_date.append(jobPostDate)


        print( job_link )
        print( location )
        print( job_title )
        print( posting_date )
        print( job_ids )

        driver.close()
        driver.quit()

        # Collecting Job Description...
        cnt = 0
        for link in job_link:
            data = {}

            # driver = webdriver.PhantomJS()
            options = Options()
            options.binary_location = '/opt/headless-chromium'
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--single-process')
            options.add_argument('--disable-dev-shm-usage')

            driver = webdriver.Chrome('/opt/chromedriver', chrome_options=options)

            time.sleep( waitTime )
            driver.get(link)
            time.sleep( waitTime )
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            driver.close()
            driver.quit()

            jobDesc = soup.find("div", {"class": "section description"}).text
            jobDesc = re.sub('DESCRIPTION', '', jobDesc)

            jobQual = soup.findAll("div", {"class": "section"})[1].text
            jobQual = re.sub('BASIC QUALIFICATIONS', '', jobQual)

            data['job_title']           = job_title[cnt]
            data['job_location']        = location[cnt]
            data['job_post_date']       = posting_date[cnt]
            data['job_id']              = job_ids[cnt]
            data['job_link']            = link
            data['job_description']     = jobDesc
            data['job_qualification']   = jobQual
            cnt = cnt + 1

            result.append(data)

            saveDataInDynamoDB( data )

            # print( result )

    #         print( "-----------------------------" )
    #         print( jobTitle )
    #         print( jobLoc )
    #         print( jobPostDate )
    #         print( jobLink )
    #         print( jobDesc )
    #         print( jobQual )

    json_file_data = json.dumps(result, indent=None, separators=(',', ':'))
    json_file_data = str(json_file_data)[1:-1]
    json_file_data = (json_file_data.replace("},", "}\n"))

    print(json_file_data)


