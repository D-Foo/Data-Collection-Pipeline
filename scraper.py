from distutils.command.upload import upload
from genericpath import exists
from uuid import uuid4
from xmlrpc.client import Boolean
from numpy import bool_, equal, number
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
import string

import urllib3.exceptions
from mtg_card_data import MTGCardData
import random
import json
import os
import requests

import boto3
from botocore.exceptions import NoCredentialsError
from botocore.exceptions import ClientError

import pandas as pd
from sqlalchemy import create_engine
from zipfile import ZipFile
import glob

class Scraper:
    """
    Webscraper targeting cardmarket.com
    
    Parameters
    ----------
    target_url : str
        URL of the website to scrape from
    set_url : str
        MTG set name in url format for cardmarket
    set_code : str
        MTG three letter expansion code of the set
    target_list_filepath : str
        Filepath of the names of cards to scrape
    to_upload : bool
        Whether or not to upload after scraping
    upload_file_name : str
        The name of the file to upload to s3
    bucket_name : str
        Name of the s3 bucket to upload to
    rds_endpoint : str
        URL of the endpoint of the RDS instance to upload to 
    debug : bool
        Whether or not to enable debugging
    

    Attributes
    ----------
    debug : bool
        Controls outputting of print statements for debugging
    url_mtg_section : str
        Part of the url that leads to the magic section of the cardmarket website
    url_set_name : str
        MTG set name in url format for cardmarket
    set_code : str
        MTG thre letter expansion code of a set, used to name data subfolders
    target_list_filepath : str
        Filepath of the names of cards to scrape
    formatted_card_list : list[str]
        Contains card urls formatted for cardmarket
    driver : webdriver
        Selenium webdriver
    delay : int
        Maximum time in seconds to wait for website to load
    root_save_dir : str
        Directory to save scraped data to
    json_filename : str
        Name of the file to save to in JSON format
    image_dir : str
        Directory to save images to
    database : list[MTGCardData]
        Contains class to store scraped data
    successfully_handled_cookies : bool 
        Tracks whether or not the driver handled the cookies prompt
    get_url_log : list[str]
        History of webpages that were attempted to visit
    real_url_log : list[str]
        History of webpages that were visited by the driver
    zip_filename : str
        Name of the zip file
    """
    
    def __init__(self, target_url, set_url, set_code, target_list_filepath, to_upload, upload_file_name, bucket_name, rds_endpoint, debug) -> None:
        
        #Control
        self.debug = debug
        self.to_upload = to_upload

        #Url
        self.url_base = target_url
        self.url_mtg_section = "/en/Magic/Products/Singles/"
        self.url_set_name = set_url
        self.target_list_filepath = target_list_filepath
        self.formatted_card_list = []
        
        #Webdriver
        self.driver = webdriver.Firefox()
        self.delay = 10

        #Data
        self.root_save_dir = "raw_data" 
        self.json_filename = "data.json"
        self.image_dir = "images"
        self.database = []
        self.set_code = set_code
        self.zip_filename = "raw_data.zip"

        #Error Checking
        self.successfully_handled_cookies = False
        self.get_url_log = []   
        self.driver_url_log = []   

        #Uploading
        self.upload_file_name = upload_file_name
        self.bucket_name = bucket_name
        self.rds_endpoint = rds_endpoint
        self.dataframe = pd.DataFrame

    
    def _geturl(self, url) -> None:
        """
        Commands the driver to load the given url, waits for the page to load and logs the desired url and visited url
        Parameters
        ----------
        url : str
            The URL to load 
        """
        self.driver.get(url)
        self.get_url_log.append(url)
        time.sleep(2) # Wait a couple of seconds, so the website doesn't suspect we're a bot
        self.driver_url_log.append(self.driver.current_url)

    def _startup(self) -> None:
        """
        Opens the browser window and gets the base url       
        """
        if(self.debug):
            print("Startup")
        self._geturl(self.url_base + '/en')

    def close(self) -> None:
        """
        Closes all windows and exits the driver
        """
        
        if(self.debug):
            print('PreQuit ID: ' + self.driver.session_id)
            print('PreQuit Profile: ' + str(self.driver.profile))
            print('PreQuit Handle Count: ' + str(len(self.driver.window_handles)))
            print('PreQuit None:')
            if self.driver == None:
                print('Driver None')


        self.driver.close()
        time.sleep(1)
        self.driver.quit()
        
        if(self.debug):
            print('PostQuit None:')
            if self.driver == None:
                print('Driver None')

            print('PostQuit ID: ' + self.driver.session_id)
            try:
                hasattr(self.driver, 'window_handles')
            #print('PostQuit Handle Count: ' + str(len(self.driver.window_handles)))
           
            except urllib3.exceptions.MaxRetryError:
                print('Error caught successfully')


    def _handle_cookies(self) -> None:
        """
        Finds and commands the driver to click on the accept cookies button
        """
        if(self.debug):
            print("Handle_Cookies")
        try: 
            WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//div[@id="CookiesConsent"]')))
            accept_cookies_button = self.driver.find_element_by_xpath('//button[@aria-label="Accept All Cookies"]')
            accept_cookies_button.click()
        except TimeoutException:
            print("Loading took much time (>" + string(self.delay) + "s)")
        except BaseException as err:
            print(f"Unexpected {err=}, {type(err)=}")
            raise
        else:
            self.successfully_handled_cookies = True

    def _create_url_list(self) -> None:
        """
        Loads the cardlist txt file and generates a list of urls to scrape from
        """
        if(self.debug):
            print("Create_Url_List")

        #load NEO_cardlist.txt
        cardlist_filename = self.target_list_filepath
        card_namelist = []
        scraped_namelist = []
        try:
            with open(cardlist_filename, 'r') as f:
                card_namelist = f.readlines()
        except BaseException as err:
            print("Could not open " + cardlist_filename + " for reading.")
            print(f"Unexpected {err=}, {type(err)=}")   
            raise

        #Remove previously scraped elements
        #Open each XXX.json and get card name
        for filename in glob.glob(os.path.join(self.root_save_dir + '/', '*.json')):
            if filename != f'{self.root_save_dir}/{self.json_filename}':
                try:
                    with open(os.path.join(os.getcwd(), filename), 'r') as f:
                        scraped_dict = json.load(f)
                        scraped_namelist.append(scraped_dict['card_name'])
                except BaseException as err:
                    print("Could not open " + cardlist_filename + " for reading.")
                    print(f"Unexpected {err=}, {type(err)=}")   
                    raise
        #Get diff of entire set namelist and scraped namelist
        card_namelist = card_namelist - scraped_namelist

        #Convert name to url syntax
        for name in card_namelist:
            name = name.replace(" // ", '-')  #Replace the " // " substring with a hyphen
            name = name.translate({ord(c):None for c in "',"}) #Remove any apostrophes or commas in the string
            name = name.replace(' ', '-')  #Replace any spaces with hyphens
            name = name.replace('\n', '')  #Remove \n at end of name
            self.formatted_card_list.append(name)
        
    def _scrape(self, url) -> None:
        """
        Scrapes data from the given url
        
        Parameters
        ----------
        url : str
            The URL to scrape data from 
        """
        self._geturl(url)
        scraped_data = MTGCardData()
        scraped_data.dict['version_count'] = 0

        #Wait until tabel containing the data we want to scrape is loaded in
        WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//dl[@class="labeled row no-gutters mx-auto"]'))) 

        #Get each table description and corresponding value
        for dt in self.driver.find_element_by_xpath('//dl[@class="labeled row no-gutters mx-auto"]').find_elements_by_xpath('.//dt'):
            
            dd = dt.find_element_by_xpath('.//following-sibling::dd')

            #Rarity
            if(dt.text == "Rarity"):
                if(self.debug):
                    print("RARITY -> " + dd.find_element_by_xpath('.//span').get_attribute("data-original-title"))
                scraped_data.dict['rarity'] = dd.find_element_by_xpath('.//span').get_attribute("data-original-title")

            #Reprints
            elif(dt.text == "Reprints"):
                version_count = 0
                number_str = dd.find_element_by_xpath('.//a').text  #Get string of the number between parentheses
                if(number_str.find('(') == -1):
                    version_count = 1   #If no number in parenthses found then there is only one reprint of that card on cardmarket
                else:
                    if(self.debug):
                        print("REPRINTS -> " + dd.find_element_by_xpath('.//a').text)
                    number_str = number_str[number_str.find('(') + 1 : number_str.find(')')]
                    version_count = int(number_str)
                scraped_data.dict['version_count'] = version_count

            #Printed in
            elif(dt.text == "Printed in"):
                if(self.debug):
                    print("Printed in")
                pass    #Expected input but we won't do anything with it

            #Availble items
            elif(dt.text == "Available items"):
                if(self.debug):
                    print(dt.text + " -> " + dd.text)
                scraped_data.dict['available_count'] = int(dd.text)

            #Set Number
            elif(dt.text == "Number"):
                if(self.debug):
                    print(dt.text + " -> " + dd.text)
                scraped_data.dict['set_number'] = int(dd.text)


            #Prices
            elif(dt.text == "From" or "Price Trend" or "30-days average price" or "7-days average price" or "1-day average price"):
                if(self.debug):
                    print(dt.text + " -> " + dd.text)

                #Clip € from end of string and convert to floating point 
                price_str = dd.text
                price_str = price_str.replace(',', '.')
                price_str = price_str.replace(' ', '')
                price_str = price_str.replace('€', '')
                price = float(price_str)

                if(dt.text == "From"):
                    scraped_data.dict['lowest_price'] = price
                elif(dt.text == "Price Trend"):
                    scraped_data.dict['price_trend'] = price
                elif(dt.text == "30-days average price"):
                    scraped_data.dict['average_price_30_day'] = price
                elif(dt.text == "7-days average price"):
                    scraped_data.dict['average_price_7_day'] = price
                else:
                    scraped_data.dict['average_price_1_day'] = price

            else:
                print("Unexpected input: " + dt.text)
        
        #Get Name
        name_string = self.driver.find_element_by_xpath('//h1').text
        name_string = name_string[0 : name_string.find('\n')]
        if(self.debug):
            print("NAME -> " + name_string)
        scraped_data.dict['card_name'] = name_string

        #Get Image
        card_image_url = self.driver.find_element_by_xpath('//img[@class="is-front"]').get_attribute("src")
        if(self.debug):
            print("Card url: " + card_image_url)            
        scraped_data.dict['image_url'] = card_image_url
        scraped_data.dict['image_key'] = f'{self.set_code}_{scraped_data.dict["set_number"]:03d}'

        #UUID
        scraped_data.dict['uuid'] = str(uuid4())

        self.database.append(scraped_data)

    def save(self) -> None:
        """
        Saves data to raw_data.json and images to the images directory
        """
        #Create directories if they don't already exist
        if(not os.path.isdir(self.root_save_dir)):
            os.mkdir(self.root_save_dir)
        if(not os.path.isdir(self.root_save_dir + '/' + self.set_code)):
            os.mkdir(self.root_save_dir + '/' + self.set_code)
        if(not os.path.isdir(self.root_save_dir  + '/' + self.set_code + '/' + self.image_dir)):
            os.mkdir(self.root_save_dir + '/' + self.set_code + '/' + self.image_dir)
        
        #Save .json of all records
        out_file = open(self.root_save_dir + '/' + self.set_code + '/' + self.json_filename, 'w')

        #TODO: UPDATE JSON SAVING TO OPEN AND UPDATE/FILL IN MISSING RECORDS
        dict_list = []  #List of dictionaries
        for i in self.database:
            dict_list.append(i.dict)

        dict_list = sorted(dict_list, key=lambda k: k['set_number'])

        json.dump(dict_list, out_file)
        out_file.close()

        #Save .json for individual records 
        for dict in dict_list:
            record_file_name = f'{dict["set_number"]:03d}.json' #Create the filename based on the set number with leading zeroes e.g. 001.json
            out_file = open(self.root_save_dir + '/' + self.set_code + '/' + record_file_name , 'w')
            json.dump(dict, out_file)
            out_file.close()
        
        #Save image if it does not already exist
        for i in self.database:
            if(not exists(self.root_save_dir + '/' + self.set_code + '/' + self.image_dir + '/' + f'{i.dict["set_number"]:03d}.jpg')):        
                with open(self.root_save_dir + '/' + self.set_code + '/' + self.image_dir + '/' + f'{i.dict["set_number"]:03d}.jpg', 'wb') as image_out:
                    img_data = requests.get(i.dict['image_url']).content
                    image_out.write(img_data)
                    image_out.close()

        #Create a zip of the raw_data folder
        with ZipFile(self.zip_filename, 'w') as zip:
            for path, directories, files in os.walk(self.root_save_dir):
                for self.zip_filename in files:
                    file_name = os.path.join(path, self.zip_filename)
                    zip.write(file_name)

    def run(self) -> None:
        """
        Starts the driver, and scrapes data for each card in cardlist txt      
        """
        self._startup()

        #Flow Control
        parse_only_one = False
        parse_first_x = 3
        random_parse = False

        self._create_url_list()

        #Load base website url and handle cookies
        self._handle_cookies()

        #Scrape rest of data from urls generated from target list data
        url_head = self.url_base + self.url_mtg_section + self.url_set_name + "/"

        if parse_only_one:
            if random_parse:
                self._scrape(url_head + random.choice(self.formatted_card_list))
            else:
                self._scrape(url_head + self.formatted_card_list[247])
        elif parse_first_x:
            if random_parse:
                for i in range(parse_first_x):
                    self._scrape(url_head + random.choice(self.formatted_card_list))
            else:
                for i in range(parse_first_x):
                    self._scrape(url_head + self.formatted_card_list[i])   
        else:
            for c in self.formatted_card_list:
                final_url = url_head + c      
                if(debug):
                    print("Scraping: " + final_url)      
                self._scrape(final_url)        

    def upload(self) -> None:
        """
        Uploads the raw_data folder(zipped) to AWS S3 and creates a dataframe for each record and then uploads to AWS RDS
        """

        #Create S3 connection
        self._upload_s3()

        #Create RDS connection
        self._create_dataframe()
        self._upload_rds()

    def _upload_s3(self) -> bool:
        """
        Upload the raw_data.zip to S3
        """
        s3_client = boto3.client('s3')
        try:
            for root,dirs,files in os.walk(self.root_save_dir):
                for file in files:
                    s3_client.upload_file(os.path.join(root,file),self.bucket_name,file)

            response = s3_client.upload_file(self.upload_file_name, self.bucket_name, self.upload_file_name)
            print("Uploaded to S3 successfully")
        except FileNotFoundError:
            if(debug):
                print("The file was not found")
            return False
        except NoCredentialsError:
            if(debug):
                print("Credentials not available")
            return False
        except ClientError as e:
            if(debug):
                print(f"Client Error: {e=}, {type(e)=}")
            return False
        return True


    def _upload_rds(self) -> bool:
        """
        Upload the tabulated data to the RDS instance
        """
        DATABASE_TYPE = '${env:DATABASE_TYPE}'
        DBAPI = '${env:DBAPI}'
        USER = '${env:USER}'
        PASSWORD = '${env:PASSWORD}'
        PORT = '${env:PORT}'
        DATABASE = '${env:DATABASE}'
      
        engine = create_engine(f"{DATABASE_TYPE}+{DBAPI}://{USER}:{PASSWORD}@{self.rds_endpoint}:{PORT}/{DATABASE}")
        engine.connect()

        self.dataframe.to_sql('mtgscraper_dataset', engine, if_exists='replace')

        engine.dispose()
        pass

    def _create_dataframe(self) -> None:
        """
        Create dataframe with pandas
        """
        self.dataframe = pd.read_json(self.root_save_dir + '/' + self.set_code + '/' + self.json_filename)
        if(self.debug):
            print(self.dataframe.head)

        pass

    
        

if __name__ == "__main__":
    #example url https://www.cardmarket.com/en/Magic/Products/Singles/Kamigawa-Neon-Dynasty/Ancestral-Katana
    target_url = "https://www.cardmarket.com"
    target_list_filepath = "NEO_cardlist.txt"
    set_name = "Kamigawa-Neon-Dynasty"
    set_code = "NEO"
    debug = True
    to_upload = False
    upload_file_name = "raw_data.zip"
    bucket_name = "mtgscraperbucket"
    rds_endpoint = "testaidb.czu22ftu6upt.eu-west-2.rds.amazonaws.com"
    

    scraper = Scraper(target_url, set_name, set_code, target_list_filepath, to_upload, upload_file_name, bucket_name, rds_endpoint, debug)
    scraper.run()
    scraper.save()
    scraper.close()
    #scraper.upload()
    #scraper._create_dataframe()
    #scraper._upload_rds()