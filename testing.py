import scraper 
import unittest
import hypothesis
import os
import urllib3.exceptions
import json

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
        debug = True
        self.scraper = scraper.Scraper(target_url, set_name, target_list_filepath, debug)
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
        Check that the json file and images directory exist and validate the the .json file can be opened and parsed correctly
        """
        json_path = self.scraper.root_save_dir + '/' + self.scraper.json_filename
        self.assertTrue(os.path.isfile(json_path), json_path + ' (data .json) not found')  #Check data json
        #Open file and make sure it loads correctly 
        scraper_json = parse_json(json_path)
        self.assertIsNotNone(scraper_json, json_path + ' (data .json) is not a valid .json file')

        #Could be expanded to check specific entries/parts of the json

        image_path = self.scraper.root_save_dir + '/' + self.scraper.image_dir
        self.assertTrue(os.path.isdir(image_path), image_path + '(image folder) not found') #Check image dir was made
        #Could be expanded to check specific .jpgs exist

    def test_close(self) -> None:
        """
        Attempting to access scraper attributes after calling .quit() raises an exception which we can catch and use to check if quit() was called succesfully
        """
        self.assertTrue(self.scraper_quit_except, 'Driver session not closed successfully')   #Make sure the driver session == 'None'
        pass

if __name__ == '__main__':
    unittest.main()