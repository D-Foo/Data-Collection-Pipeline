# Data Collection Project

> An automated webscraping project to track prices of Magic the Gathering cards on www.cardmarket.com, could be applied to any other website to scrape data from. Makes us of Selenium, Geckodriver

## Creating a URL list and piloting an automated browser

- Creating a URL List

We can access data in .json format containing all the raw card details we need from https://mtgjson.com/. We can download json of a set of cards from https://mtgjson.com/downloads/all-sets/ (Sets are collections of cards released together ~300 cards contained in a set). By parsing the json of a set we can access and save the names of individual cards to a .txt file with the raw card names of the cards we want to find on cardmarket. We then format the raw names into the form they take on cardmarket's urls.


```python
#Convert name to url syntax
for name in card_namelist:
    name = name.replace(" // ", '-')  #Replace the " // " substring with a hyphen
    name = name.translate({ord(c):None for c in "',"}) #Remove any apostrophes or commas in the string
    name = name.replace(' ', '-')  #Replace any spaces with hyphens
    self.formatted_card_list.append(name)
```

- Controlling a browser with Selenium

We can initialise and pilot a firefox browser window using [Selenium](https://www.selenium.dev/documentation/webdriver/) and [Geckodriver](https://github.com/mozilla/geckodriver/releases). To start with we request the base url of the website www.cardmarket.com so we can accept cookies for the website. We wait until the cookies consent window appears, then find the accept cookies button using xpaths then click to accept cookies. 

We can find the xpath of the accept cookies button by inspecting it and examining where the button is contained in the HTML. The button is contained in the div with id="Cookies Consent" so we wait until it has loaded in the browser; then find the button with it's xpath then click it. 


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

After accepting cookies we can iterate through our url list and access each webpage associated with each card name in our list.

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

Before we start scraping we need a strcutre to store our data in. For this we project we're going to store our data in dictionaries, a data structure where each piece of data is mapped to a corresponding key, and easily exported to JSON format which is perfect for our needs. Each card in a magic set has a set number which suits as a user friendly unique ID for each set we scrape, a UUID is also added so we have access to a universally unique record ID for each individual card.

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

To find the data we need to scrape we make use of XPaths to find the elements on the page containing the data. The name is contained in the &lt;h1> (header) tag and the card image is contained in the &lt;img> tag. 

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

The rest of the data we need is contained in a &lt;dl> (description list), to efficiently scrape it we use a for loop to obtain every &lt;dt> (terms in the list) tag nested inside the dl and it's corresponding &lt;dd> (description) tag, each &lt;dd> tag is handled differently based on the &lt;dt> tag it belongs to.

![mtg_dl_blurred](https://user-images.githubusercontent.com/36233522/160681462-52cf134f-345d-4fde-b0e8-2b8676e6aed0.png)

- Save data and images locally

After scraping all the data we need the card data is exported to JSON format and saved with each card image saved in a separate folder.

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
