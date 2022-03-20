class Scraper:

    def __init__(self, target_url, target_list, debug) -> None:
        self.target_url = target_url
        self.target_list = target_list
        self.debug = debug
        self.url_list = []  #0 base website url, 1-X data 

        self.startup()

        pass
    
    def startup(self):
        if(self.debug):
            print("Startup")
        pass

    def handle_cookies(self, url):
        if(self.debug):
            print("Handle_Cookies")
        pass

    def create_url_list(self):
        if(self.debug):
            print("Create_Url_List")

        pass

    def scrape(self, url):
        
        pass

    def run(self):
        self.create_url_list()
        #Load base website url and handle cookies
        self.handle_cookies()

        #Scrape rest of data from urls generated from tareet list data
        for url in self.url_list:
            self.scrape(url)


        pass

if __name__ == "__main__":
    #example url https://www.cardmarket.com/en/Magic/Products/Singles/Kamigawa-Neon-Dynasty/Ancestral-Katana
    target_url = "https://www.cardmarket.com"
    target_list = [] # Get from kamigawa_neon_dynasty.json -> name list
    debug = True

    scraper = Scraper(target_url, target_list, debug)
    pass