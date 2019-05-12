import os
import time
from collections import defaultdict
from GetSoup import gamestop_find_prices, pricecharting_find_prices, get_url_string, enter_buyback_price
from ReadSheet_Helpers import divide_sheet, find_last_cell
from ConvertXLS import open_xls_as_xlsx
import threading

max_threads = 1
data_dict = defaultdict(list)
read_count = 0

sheet_lock = threading.Lock()

'''Will read excel sheet for game titles and new/used condition.'''
def read_game(r, sheet):
    sheet_lock.acquire()
    item_number = sheet.cell(row=r, column=1).value

    if item_number.find("*") == -1:
        c_flag = 0
        g_title = sheet.cell(row=r, column=9).value
    else:
        c_flag = 1
        g_title = sheet.cell(row=r, column=9).value
    sheet_lock.release()
    return c_flag, g_title


def gs_collect_to_sheet(row, retailer, cond_flag, price_url_string, game_system, game_title, sheet, wb, to_file):

    sell_price = gamestop_find_prices(price_url_string, cond_flag)
    sheet_lock.acquire()
    if sell_price == 0:

        original_price = sheet.cell(row=row, column=2).value
        sell_price = original_price
    else:
        sell_price = sell_price

    credit_cash = "Null"
    bb_str = "Null"

    if cond_flag == 0:
        try:
            price = int(round(float(sell_price)))
            buyback_price = price / 2
            credit_cash = str(buyback_price)
        except ValueError:
            print("Value Error, Detected Program")
            done_and_save(sheet, wb, to_file)

    if cond_flag == 1:
        trade_in_str = " Trade In Value "
        buyback_query = retailer + game_title + " " + game_system + trade_in_str
        credit, cash, bb_str = enter_buyback_price(cond_flag, buyback_query)
        credit_cash = str(credit) + ", " + str(cash)

    item_list = [row, sell_price, credit_cash, price_url_string, bb_str]
    global data_dict
    data_dict[sheet.cell(row=row, column=1).value] = item_list
    sheet_lock.release()

    global read_count
    read_count = read_count + 1
    print("Count:", read_count)


def pc_collect_to_sheet(row, cond_flag, price_url_string, sheet, wb, to_file):

    sell_price = pricecharting_find_prices(price_url_string, cond_flag)
    sheet_lock.acquire()

    if sell_price == 0:
        original_price = sheet.cell(row=row, column=4).value
        sell_price = original_price
    else:
        sell_price = sell_price

    credit_cash = "Null"

    try:
        if sell_price is not None:
            price = int(round(float(sell_price)))
        else:
            price = 1

        print("PRICE:", price)

        if   45 < price:
            buyback_price = int(round(price / 2))
        elif 27 < price <= 45:
            buyback_price = int(round(price / 3))
        elif 14 < price <= 27:
            buyback_price = int(round(price / 4))
        elif 8 < price <= 14:
            buyback_price = int(round(price / 5))
        elif 4 < price <= 8:
            buyback_price = int(round(price / 6))
        else:
            buyback_price = .25

        print("Buyback price:", buyback_price)
        credit_cash = str(buyback_price)

    except ValueError:
        print("Value Error, Detected this Program")
        done_and_save(sheet, wb, to_file)

    item_list = [row, sell_price, credit_cash, price_url_string, "Null"]
    global data_dict
    data_dict[sheet.cell(row=row, column=1).value] = item_list
    sheet_lock.release()
    global read_count
    read_count = read_count + 1
    print("Count:", read_count)


def write_to_sheet(sheet):
    for key, value in data_dict.items():
        r = value[0]
        sheet.cell(row=r, column=6).value = value[1]
        sheet.cell(row=r, column=7).value = value[2]
        sheet.cell(row=r, column=10).value = value[3]
        sheet.cell(row=r, column=11).value = value[4]


'''Loop through all excel sheet rows to enter sell and buyback prices.'''
def begin_read(game_system, sheet, bounds, retailer, wb, to_file):
    for row in range(bounds[0], bounds[1]+1):
        #start_time = time.time()
        cond_flag, game_title = read_game(row, sheet)
        query = str(retailer) + " " + str(game_title) + " " + str(game_system)

        price_url_string = get_url_string(query, "sell")

        if not (price_url_string.startswith('https://www.gamestop.com') or price_url_string.startswith('https://www.pricecharting.com')):
            print("Doesnt Start With GS or PC:", price_url_string)
            continue

        if retailer == "Gamestop":
            gs_collect_to_sheet(row, retailer, cond_flag, price_url_string, game_system, game_title, sheet, wb, to_file)
        elif retailer == "Pricecharting":
            pc_collect_to_sheet(row, cond_flag, price_url_string, sheet, wb, to_file)
        #print("--- One item: %s seconds ---" % (time.time() - start_time))

def done_and_save(sheet, wb, to_file):
    write_to_sheet(sheet)
    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    save_path = desktop + '\\' + to_file + '.xlsx'
    wb.save(save_path)


'''Program start here, called in GUI_Start'''
def program_start(system, open_file, to_file, retailer, start, end):
    st1 = time.time()
    wb_file = open_file.replace('/', '\\')

    wb = open_xls_as_xlsx(wb_file)
    #wb = openpyxl.load_workbook(wb_file)
    sheet = wb.active
    max_row = find_last_cell(sheet)
    bounds = divide_sheet(max_row, max_threads, int(start), end)

    if max_threads is not 1:
        threads = []

        for bound in bounds:
            t = threading.Thread(target=begin_read, args=(system, sheet, bound, retailer, wb, to_file))
            threads.append(t)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    else:
        for bound in bounds:
            begin_read(system, sheet, bound, retailer, wb, to_file)

    done_and_save(sheet, wb, to_file)

    print("*** %s secs ***" % (time.time() - st1))
