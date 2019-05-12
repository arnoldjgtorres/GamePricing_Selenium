from bs4 import BeautifulSoup
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium import webdriver
from lxml.html import fromstring
from time import sleep
import re
import json
import ast
import bs4
import requests
import random
from selenium.webdriver.common.proxy import Proxy, ProxyType
from ReadSheet_Helpers import find_gecko


gecko_global = find_gecko('geckodriver.exe')


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


def get_proxies():
    sleep(1)
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies


def incapsession_to_soup(url_string):
    sleep(1)
    #proxies = get_proxies()

    '''
    if len(proxies) == 0:
        print("Proxies Empty", proxies)
        soup = vpn_to_soup(url_string)
    else:
        soup = proxy_to_soup(url_string, proxies)
    '''
    soup = vpn_to_soup(url_string)
    return soup


def proxy_to_soup(url_string, proxies):
    str_error = 0
    for i in range(0, 5):
        PROXY = random.sample(proxies, 1)
        print("Request #%d" % i)
        try:
            PORT = 8200
            str_proxy = str(PROXY) + ":" + str(PORT)
            driver_proxy = Proxy({
                'proxyType': ProxyType.MANUAL,
                'httpProxy': str_proxy,
                'ftpProxy': str_proxy,
                'sslProxy': str_proxy,
                'noProxy': ''  # set this value as desired
            })

            firefox_options = FirefoxOptions()
            firefox_options.add_argument("--headless")
            driver = webdriver.Firefox(executable_path=gecko_global, options=firefox_options, proxy=driver_proxy)                #driver = webdriver.Firefox(options=firefox_options)
            driver.get(url_string)
            html = driver.page_source
            driver.quit()
            str_error = None

        except Exception as error:
            print("Skipping. Connnection error")
            print(error)
            str_error = 0
            proxies = get_proxies()
            driver.quit()
            pass

        if str_error is not None:
            sleep(1)
        else:
            break

    soup = BeautifulSoup(html, 'lxml')
    return soup


def vpn_to_soup(url_string):
    soup = """<html><head><title>Null Page</title></head>"""
    try:
        firefox_options = FirefoxOptions()
        firefox_options.add_argument("--headless")
        driver = webdriver.Firefox(executable_path=gecko_global, options=firefox_options)
        driver.get(url_string)
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        driver.quit()
        return soup
    except Exception as error:
        driver.quit()
        print("VPN_to_Soup Error:", error)
    return soup


'''Simple google search that returns url with the used query.'''
def get_url_string(query, query_type):
    url_string = ""

    sleep(1)
    headers = {"User-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36"}

    try:
        res = requests.get('https://google.com/search?q=' + query, headers)
        soup = bs4.BeautifulSoup(res.text, 'lxml')
        links = soup.select('.r a')
    except Exception as error:
        print("Get Url String Exception", error)
        return url_string

    for link in links:
        link = link.get("href")
        link = link[7:]
        line, mid, end = link.partition('&sa')
        if query_type == "sell":
            if line.startswith('https://www.gamestop.com') or line.startswith('https://www.pricecharting.com'):
                print(line)
                return line
        elif query_type == "buyback":
            if line.startswith('https://www.gamestop.com/trade/quote'):
                print(line)
                return line

    print("Got Blank URL", url_string, "Suggest Switching VPN Location")
    return url_string


'''Checks item condition for used/new, then google search for url.
Url html will be searched for prices then entered into cell.'''
def enter_buyback_price(c_flag, buyback_query):
    credit = 0
    cash = 0
    buyback_url_string = ""

    if c_flag == 1:
        buyback_url_string = get_url_string(buyback_query, "buyback")
        if buyback_url_string is not "":
            credit, cash = find_buyback(buyback_url_string)

    return credit, cash, buyback_url_string


'''Searches soup for script tag that holds GetGameQuoteData js function. 
    Then search that function for buyback prices. Uses incapsession_to_soup helper
    function. If prices are not being entered in excel, it's the internet connection.'''
def find_buyback(url_string):

    cash_str = 0
    credit_str = 0
    #print("USED", url_string)
    try:
        soup = incapsession_to_soup(url_string)
        script_tags = soup.find_all('script')
    except Exception as error:
        print("Find BuyBack Exception", error)
        return credit_str, cash_str



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

    return credit_str, cash_str


'''Searches soup for script tag that holds digitalData variable. That
    variable has a dict to convert and then searched for new/sell prices.
    Uses incapsession_to_soup and text_to_dict helper functions.'''
def gamestop_find_prices(url_string, cond_flag):

    try:
        soup = incapsession_to_soup(url_string)
        script_tags = soup.find_all('script')
    except Exception as error:
        print("Find Prices Exception", error)
        return 0


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


def pricecharting_find_prices(url_string, cond_flag):

    soup = incapsession_to_soup(url_string)
    table = soup.find('table', id='price_data')

    if cond_flag == 0:
        new = table.find('td', id='new_price')
        new_text = new.find('span', {'class': 'price js-price'}).get_text()
        np = new_text.strip()
        np = np.replace("$", "")
        print("NEW:", np)
        return np

    if cond_flag == 1:
        loose = table.find('td', id='used_price')
        complete = table.find('td', id='complete_price')
        loose_text = loose.find('span', {'class': 'price js-price'}).get_text()
        comp_text = complete.find('span', {'class': 'price js-price'}).get_text()
        lp = loose_text.strip()
        cp = comp_text.strip()
        lp = lp.replace("$", "")
        cp = cp.replace("$", "")
        print("LOOSE:", lp)
        #print("COMPLETE:", cp)
        return lp

