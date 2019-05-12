import time
import datetime
from ReadSheet import program_start
from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showerror
import threading

start_time = time.time()
now = datetime.datetime.now()
print(now)

# path = filedialog.askopenfilename(initialdir="/", title="Select file",
#                                filetypes=(("xlsx files", "*.xlsx"), ("all files", "*.*")))

'''
path = 'C:\\Users\ArnoldGT\Desktop\ps4_01_08_15.xlsx'
# path = 'C:\\Users\ArnoldGT\Desktop\ns_price_change_8_10_18.xlsx'
# wb = openpyxl.load_workbook('C:\\Users\ArnoldGT\Desktop\ps4_01_08_15.xlsx')
wb = openpyxl.load_workbook(path)
sheet = wb.active
'''

class Application(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.pack()
        self.create_widgets()

    def create_widgets(self):
        self.file_display = Label(self, text="")
        self.file_display.pack()

        menubar = Menu(self.master)
        self.master.config(menu=menubar)
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.choose_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        system = ""
        file = ""
        retailer = ""

        platforms = ['Playstation 4', 'Playstation 3', 'Playstation 2', 'Playstation One', 'PS Vita', 'PSP',
                     'Nintendo Switch', 'Nintendo Wii U', 'Nintendo Wii', 'Nintendo Gamecube', 'Nintendo 64', 'SNES',
                     'NES', 'Nintendo 3DS',  'Nintendo DS', 'Nintendo Gameboy Advance', 'Nintendo Gameboy',
                     'Xbox One', 'Xbox 360', 'Xbox', 'Sega Genesis', 'Sega Saturn', 'Sega Dreamcast' ]

        retailers = ['Gamestop', 'Pricecharting']

        tkvar_platform = StringVar(self)
        tkvar_platform.set("None Selected")

        tkvar_retail = StringVar(self)
        tkvar_retail.set("None Selected")


        self.platform_label = Label(self, text='Choose a platform')
        self.platform_label.pack()

        game_dropdown = OptionMenu(self, tkvar_platform, *platforms, command=self.dropdown)
        game_dropdown.pack()

        self.retailer_label = Label(self, text='Choose a retailer')
        self.retailer_label.pack()

        retailer_dropdown = OptionMenu(self, tkvar_retail, *retailers, command=self.ret_dropdown)
        retailer_dropdown.pack()

        self.start_row_label = Label(self, text='Enter Start Row')
        self.start_row_label.pack()
        self.start_row = Entry(self)
        self.start_row.insert(END, "1")
        self.start_row.pack()

        self.end_row_label = Label(self, text='Enter End Row')
        self.end_row_label.pack()
        self.end_row = Entry(self)
        self.end_row.insert(END, "Max Row")
        self.end_row.pack()

        self.save_to_label = Label(self, text='Type name for save file')
        self.save_to_label.pack()

        self.save_name = Entry(self)
        self.save_name.pack()

        #self.run = Button(self, text="Run Program", fg="red", command=lambda: begin_read(self.system, self.file, self.save_name.get()))
        self.run = Button(self, text="Run Program", fg="red", command=self.start)
        self.run.pack()


    def dropdown(self, value):
        print(value)
        self.system = value
        return value

    def ret_dropdown(self, value):
        print(value)
        self.retailer = value
        return value

    def choose_file(self):
        file = askopenfilename(initialdir="/", title="Select file",
                               filetypes=(("xls files", "*.xls"), ("xlsx files", "*.xlsx"), ("all files", "*.*")))
        self.file_display.config(text=file)
        self.file = file

    def start(self):
        threads = []
        print(self.save_name.get())
        print("Start Row: " + self.start_row.get() + " End Row: " + self.end_row.get())
        t = threading.Thread(target=program_start, args=(self.system,
                self.file, self.save_name.get(), self.retailer, self.start_row.get(), self.end_row.get()))
        #begin_read(self.system, self.file, self.save_name.get())
        threads.append(t)
        t.start()

    def quit(self):
        sys.exit(0)


root = Tk()
root.geometry("450x350")
root.configure(background='black')

app = Application(master=root)
app.pack(fill=BOTH, expand=YES)
app.mainloop()

#begin_read('Playstation 4', 'C:\\Users\ArnoldGT\Desktop\ps4_01_08_15.xlsx', 'please')
print("--- %s seconds ---" % (time.time() - start_time))
