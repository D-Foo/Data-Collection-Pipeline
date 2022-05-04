import scraper 
import unittest
import hypothesis
import os
import urllib3.exceptions
import json
from sqlalchemy import create_engine
from sqlalchemy import inspect
import boto3
from botocore.exceptions import NoCredentialsError
from botocore.exceptions import ClientError


def parse_json(filename):
        try: 
            with open(filename) as f: 
                return json.load(f) 
        except ValueError as e: 
            print('invalid json: %s' % e) 
            return None

class ScraperTestCase(unittest.TestCase):

    """
    Webscraper Tester 

    Attributes
    ----------
    scraper : Scraper
        Webscraper to test
    running_id : str
        Scraper session id
    scraper_quit_except : bool
        Records whethere or not an expection was raised when attempting to access scraper attributes
    """
    @classmethod
    def setUpClass(self) -> None:
        """
        Initialise the webscraper for testing and record any variables we will use to validate performance later
        """
        target_url = "https://www.cardmarket.com"
        target_list_filepath = "NEO_cardlist.txt"
        set_name = "Kamigawa-Neon-Dynasty"
        set_code = "NEO"
        debug = True
        to_upload = False
        upload_file_name = "raw_data.zip"
        bucket_name = "mtgscraperbucket"
        rds_endpoint = "testaidb.czu22ftu6upt.eu-west-2.rds.amazonaws.com"
    

        self.scraper = scraper.Scraper(target_url, set_name, set_code, target_list_filepath, to_upload, upload_file_name, bucket_name, rds_endpoint, debug)
        self.scraper.run()
        self.running_id = self.scraper.driver.session_id
        self.scraper.save()
        self.scraper.close()
        self.scraper_quit_except = False
        try:
            hasattr(self.scraper.driver, 'window_handles')
        except urllib3.exceptions.MaxRetryError:
            self.scraper_quit_except = True

    @classmethod
    def tearDownClass(self) -> None:
        """
        Delete the scraper
        """
        del self.scraper

    def test_run(self) -> None:
        """
        Check if a session ID was generated to validate that the driver was created succesfully
        """
        self.assertNotEqual(self.running_id, None, 'Driver session not created successfully')   #Make sure the driver session != 'None'

    def test_url_logs(self) -> None:
        """
        Check for any discrepancies between the urls the driver was told to request and those that it visited
        """
        self.assertListEqual(self.scraper.get_url_log, self.scraper.driver_url_log, 'URL Log discrepancy') #Check the urls the driver accessed are the same as the target urls

    def test_save(self) -> None:
        """
        Check that the json and image directories exist and validate that the .json files can be opened and parsed correctly
        """
        #Open json files and make sure it loads correctly 
        for path, directories, files in os.walk(self.scraper.root_save_dir + self.scraper.set_code):
                for file in files:
                    if(file.endswith('.json')):
                        scraper_json = parse_json(file)
                        self.assertIsNotNone(scraper_json, file + 'is not a valid .json file')

        #Could be expanded to check specific entries/parts of the json
        image_path = self.scraper.root_save_dir + '/' + self.scraper.set_code + '/' + self.scraper.image_dir
        self.assertTrue(os.path.isdir(image_path), image_path + '(image folder) not found') #Check image dir was made
        #Could be expanded to check specific .jpgs exist

        #Check zip
        zip_path = self.scraper.zip_filename
        self.assertTrue(os.path.isfile(zip_path), zip_path + ' (data .zip) not found')  #Check zip

    def test_close(self) -> None:
        """
        Attempting to access scraper attributes after calling .quit() raises an exception which we can catch and use to check if quit() was called succesfully
        """
        self.assertTrue(self.scraper_quit_except, 'Driver session not closed successfully')   #Make sure the driver session == 'None'
        pass

    def test_upload(self) -> None:
        """
        Connect to the S3 and RDS servers and verify that files/dataframes exist there
        """
        #S3
        s3 = boto3.resource('s3')

        try:
            s3.Object(self.scraper.bucket_name, self.scraper.zip_filename).load()     
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                #File does not exist
                self.fail('Error 404: File does not exist')
            else:
                self.fail(f'Client Error: {e=}, {type(e)=}')
        except NoCredentialsError:
            self.fail('Incorrect Credentials for S3')


        #RDS
        DATABASE_TYPE = os.environ.get('DATABASE_TYPE')
        DBAPI = os.environ.get('DBAPI')
        USER = os.environ.get('USER')
        PASSWORD = os.environ.get('PASSWORD')
        PORT = os.environ.get('PORT')
        DATABASE = os.environ.get('DATABASE')

        engine = create_engine(f"{DATABASE_TYPE}+{DBAPI}://{USER}:{PASSWORD}@{self.scraper.rds_endpoint}:{PORT}/{DATABASE}")
        engine.connect()

        insp = inspect(engine)
        self.assertTrue(insp.has_table('mtgscraper_dataset'))
        engine.dispose()

        pass

if __name__ == '__main__':
    unittest.main()