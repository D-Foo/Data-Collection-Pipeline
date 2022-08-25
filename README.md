# Data Collection Project

> An automated webscraping project to track prices of Magic the Gathering cards on www.cardmarket.com, could be applied to any other website to scrape data from. Makes us of Selenium, ChromeDriver

## Creating a URL list and piloting an automated browser

- Creating a URL List

Card data is accessed in .json format from https://mtgjson.com containing all the card details neededed to create the url list. Set JSONs are downloaded from https://mtgjson.com/downloads/all-sets/ (Sets are a collection of cards released together). 
By parsing a set's JSON the individual card names are accessed and saved to a .txt file creating a target list of card names to find on cardmarket; raw names are then formatted into the form they take on cardmarket's urls to create the url list.


```python
#Convert name to url syntax
for name in card_namelist:
    name = name.replace(" // ", '-')  #Replace the " // " substring with a hyphen
    name = name.translate({ord(c):None for c in "',"}) #Remove any apostrophes or commas in the string
    name = name.replace(' ', '-')  #Replace any spaces with hyphens
    self.formatted_card_list.append(name)
```

- Controlling a browser with Selenium

 A chrome browser is initialised and piloted with
 [Selenium](https://www.selenium.dev/documentation/webdriver/) and [ChromeDriver](https://chromedriver.chromium.org/downloads). To home page of the website (www.cardmarket.com) is requested so that cookies can be accepted for the website. The window waits until the cookies consent window appears, then finds and clicks on the accept cookies button using xpaths to locate and click on it. 

The xpath of the accept cookies button  is found by inspecting it and examining where the button is contained in the page's HTML. The button is contained in the div with id="Cookies Consent" so once it has loaded in the browser; the button with it's xpath is found then clicked. 


```python
try: 
    WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//div[@id="CookiesConsent"]')))
    accept_cookies_button = self.driver.find_element_by_xpath('//button[@aria-label="Accept All Cookies"]')
    accept_cookies_button.click()
except TimeoutException:
    print("Loading took much time (>" + string(self.delay) + "s)")

```

Cookies Pop Up | Accepted Cookies!
:-------------------------:|:-------------------------:
![automated_no_cookies_40](https://user-images.githubusercontent.com/36233522/159569096-bb9e6284-db9a-4178-99f8-81f380a2d7b7.png)  |  ![automated_cookies_40](https://user-images.githubusercontent.com/36233522/159569109-04fc6134-ec25-4c02-b6c6-ef2fc4e869c2.png)

After accepting cookies the url list is iterated through and each webpage associated with each card name in our list is accessed.

```python
  #Scrape rest of data from urls generated from target list data
  #Url
  self.url_base = target_url  #"https://www.cardmarket.com"
  self.url_mtg_section = "/en/Magic/Products/Singles/"
  self.url_set_name = set_name #"Kamigawa-Neon-Dynasty"
  url_head = self.url_base + self.url_mtg_section + self.url_set_name + "/"
  for c in self.formatted_card_list:
    final_url = url_head + c  #Example: https://www.cardmarket.com/en/Magic/Products/Singles/Kamigawa-Neon-Dynasty/Ancestral-Katana
    self.scrape(final_url)
```



## Scraping data from the website

- Create a dictionary to store data in 

Before scraping beings a strcutre is needed to store data in. For this project data will be storeed in dictionaries, a data structure where each piece of data is mapped to a corresponding key, and easily exported to JSON format which is well suited for the project's needs. Each card in a magic set has a set number which suits as a user friendly unique ID for each scraped set, a UUID is also added to have access to a universally unique record ID for each individual card in the case of scraping multiple sets that might include the same card.

```python
dict = {
        "card_name": string,
        "rarity": string,
        "available_count": int,
        "version_count": int,
        "set_number": int, #unique ID
        "lowest_price": float,
        "price_trend": float,
        "average_price_30_day": float,
        "average_price_7_day": float,
        "average_price_1_day": float,
        "image_url" : string,
        "uuid": string,}
```

- Getting data from the website

To find the data to scrape XPaths are used to locate the elements on the page containing the required data. The name is contained in the &lt;h1> (header) tag and the card image is contained in the &lt;img> tag. 

```python
#Get Name
if(debug):
    print("NAME -> " + self.driver.find_element_by_xpath('//h1').text)
name_string = self.driver.find_element_by_xpath('//h1').text
name_string = name_string[0 : name_string.find('\n')]
scraped_data.dict['card_name'] = name_string

#Get Image
card_image_url = self.driver.find_element_by_xpath('//img[@class="is-front"]').get_attribute("src")
if(debug):
    print("Card url: " + card_image_url)            
scraped_data.dict['image_url'] = card_image_url
```

The rest of the needed is contained in a &lt;dl> (description list), to efficiently scrape it a for loop is used to obtain every &lt;dt> (terms in the list) tag nested inside the dl and it's corresponding &lt;dd> (description) tag, each &lt;dd> tag is handled differently based on the &lt;dt> tag it belongs to.

![mtg_dl_blurred](https://user-images.githubusercontent.com/36233522/160681462-52cf134f-345d-4fde-b0e8-2b8676e6aed0.png)

- Save data and images locally

After scraping all the data needed the card data is exported to JSON format and saved with each card image saved in a separate folder.

```python
#Save .json
out_file = open(self.root_save_dir + '/' + self.json_filename, 'w')
json.dump(dict_list, out_file)
out_file.close()

#Save image if it does not already exist
for i in self.database:
    if(not exists(self.root_save_dir + '/' + self.image_dir + '/' + str(i.dict['set_number']) + '.jpg')):        
        with open(self.root_save_dir + '/' + self.image_dir + '/' + str(i.dict['set_number']) + '.jpg', 'wb') as image_out:
            img_data = requests.get(i.dict['image_url']).content
            image_out.write(img_data)
            image_out.close()
```

## Testing

To aid in testing the scraper python's built in unittest library is used to create a script which can be run to test our scraper. A test case is constructed by inheriting from unittest.TestCase, by doing so unittest will call each method that beings with "test".

A testing method is created for each public method in the scraper and an additional function is created to check the url logs of the scraper against requested urls to catch any redirections or erroneous urls being passed to the scraper. If an assertion in a test method fails then the test fails and the user is notified.

Example tests
```python
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
```
## Uploading

The data is uploaded to the cloud and stored with AWS S3 and RDS servers. A dataframe is made for each record by using pandas to convert the dictionaries in memory, which are then uploaded to the RDS server with SQL. The raw data is uploaded to S3 with boto3.

## Docker

Docker is used to containerise the application so it can be run scalably in the cloud

Changes are made to the code to allow the browser to run in "headless" mode as there is no display for the application to use when ran in a container.
Container

## Running in the cloud

An AWS EC2 instance is ran using an ubuntu image. Docker is installed on the machine and used to pull the containerised application.

To monitor the performance of docker and the EC2 instance a prometheus container is installed using docker along with a node exporter container. An endpoint is created which is accessed using grafana to pull and display metrics.

## Automation

A github workflow is created to automate containerising the application with docker. An is created so that on a push to main branch the application is automatically containerised and the container on dockerhub is updated

To automate the EC2 instance cronjobs are created that kill the previous container and pull and run the latest one from dockerhub everyday.
