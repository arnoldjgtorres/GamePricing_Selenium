from bs4 import BeautifulSoup
#from incapsula import IncapSession
from selenium.webdriver.chrome.options import Options
from gsearch.googlesearch import search
from selenium import webdriver
import re
import json
import ast
#import six


'''Sell prices are held by a javascript dictionary variable. This
strips string and converts to python dict.'''
def text_to_dict(script):
    main_json_dict = script
    main_json_dict = main_json_dict[18:]
    main_json_dict = main_json_dict.rstrip()
    main_json_dict = main_json_dict[:-1]
    attr_dict = json.loads(main_json_dict)
    attr_dict = ast.literal_eval(json.dumps(attr_dict))
    return attr_dict



''' Found Github package that bypasses user privileges. 
    No longer a robot sending requests.'''
def incapsession_to_soup(url_string):

    '''
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    session = IncapSession()
    session.cookies.set('cookie-key', 'cookie-value')
    page = session.get(url_string, headers=headers, auth=('user', 'pass'))
    soup = BeautifulSoup(page.content, 'html.parser')
    '''
    WINDOW_SIZE = "1920, 1080"
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
    driver = webdriver.Chrome('C:\\Users\ArnoldGT\PycharmProjects\Selenium\chromedriver', chrome_options=chrome_options)
    driver.get(url_string)
    html = driver.page_source

    soup = BeautifulSoup(html, 'html.parser')
    return soup



'''Simple google search that returns url with the used query.'''
def get_url_string(query):
    url_string = ""
    results = search(query, num_results=3)
    for url_iter in results:
        if url_iter[1].startswith('https://www.gamestop.com'):
            url_string = url_iter[1]
            return url_string
    return url_string



'''Checks item condition for used/new, then google search for url.
Url html will be searched for prices then entered into cell.'''
def enter_buyback_price(c_flag, buyback_query):

    credit = 0
    cash = 0
    buyback_url_string = ""
    if c_flag == 1:
        # buyback_url_string = ''
        # print(buyback_query)

        buyback_url_string = get_url_string(buyback_query)
        '''
        try:
            buyback_url_string = get_url_string(buyback_query)
        except ValueError:
            buyback_url_string = "Url_Error"
            # print("BUY_STR_ERROR" + buyback_url_string + "VAL")
        '''


        if buyback_url_string is not "":
            print("BUYBACK_STR", buyback_url_string)
            credit, cash = find_buyback(buyback_url_string)
       
    return credit, cash, buyback_url_string


'''Searches soup for script tag that holds GetGameQuoteData js function. 
    Then search that function for buyback prices. 
    Uses incapsession_to_soup helper function.'''
def find_buyback(url_string):
    if url_string == '':
        return -1

    cash_str = 0
    credit_str = 0

    soup = incapsession_to_soup(url_string)
    script_tags = soup.find_all('script')

    for script in script_tags:
        pattern = 'GetGameQuoteData'
        if re.search(pattern, script.text):

            cash_pattern = re.compile('var cashAmount = (.*?);')
            credit_pattern = re.compile('var creditAmount = (.*?);')


            '''Below is just stripping string line for buyback price.'''
            if cash_pattern.search(str(script.text)):
                cash_amount = cash_pattern.search(script.text)
                cash_str = cash_amount.string[cash_amount.start():cash_amount.end()]
                cash_str = cash_str.split("=", 1)[1]
                cash_str = cash_str.replace(';', '')
                cash_str = cash_str.strip()

            if credit_pattern.search(str(script.text)):
                credit_amount = credit_pattern.search(script.string)
                credit_str = credit_amount.string[credit_amount.start():credit_amount.end()]
                credit_str = credit_str.split("=", 1)[1]
                credit_str = credit_str.replace(';', '')
                credit_str = credit_str.strip()
    print("Buyback Prices", credit_str, cash_str)
    return credit_str, cash_str



'''Searches soup for script tag that holds digitalData variable. That
    variable has a dict to convert and then searched for new/sell prices.
    Uses incapsession_to_soup and text_to_dict helper functions.'''
def find_prices(url_string, cond_flag):

    if url_string == '':
        return -1

    #check_search_flag(search_flag, url_string)
    print("Sell Url: ", url_string)
    soup = incapsession_to_soup(url_string)

    script_tags = soup.find_all('script')
    for script in script_tags:
        pattern = 'var digitalData'
        if re.search(pattern, script.text):
            attr_dict = text_to_dict(script.text)
            for key_attr_dict, value_attr_dict in attr_dict.items():
                if key_attr_dict == "product":
                    i = 0
                    while i < len(value_attr_dict):
                        for key, val_dict in value_attr_dict[i].items():
                            if key == "attributes":
                                # cond_flag: 0 = NEW, 1 = USED
                                if val_dict["condition"] == "New":
                                    if cond_flag == 0:
                                        return val_dict["price"]
                                if val_dict["condition"] == "Pre-Owned":
                                    if cond_flag == 1:
                                        return val_dict["price"]
                        i += 1

    return 0
