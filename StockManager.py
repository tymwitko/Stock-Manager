#!/usr/bin/env python

from PyQt5 import QtWidgets, QtGui, QtCore, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLineEdit, QLabel, QCompleter, QRadioButton, QPushButton, QButtonGroup, QAbstractButton, QMessageBox, QWidget, QScrollArea, QVBoxLayout
from PyQt5.QtGui import QFont
import sys
# from Data import markets, PL, US, DE, HK, HU, JP, UK
# from Import import UserDatabase, NotEnoughSharesError, ShareNotFoundError, BelowZeroError, Stock
import requests
# import pandas as pd
import csv
# from datetime import datetime

from pandas_datareader import data as pdr
import pandas as pd
import datetime
from datetime import timedelta
from datetime import datetime as dt


class Stock:
	def __init__(self, market, instruction=''):
		self.inst = instruction
		self.market = market

	def importstock(self, stock):
		self.st = stock + '.'
		self.st += self.market
		self.df = pdr.DataReader(self.st, 'stooq')
		return self.df

	def datetostring(self, date):
		'''
		Converts given date to string for link purposes.
		'''
		return date.strftime("%Y") + '-' + date.strftime("%m") + '-' + date.strftime("%d")

	def stockprice(self, stock, market):
		'''
		Returns last noted price of given stock.
		(From the last closing of the market.)
		'''
		self.importstock(stock)
		for i in range(0, 365):
			try:
				return self.df.Close[self.datetostring(datetime.date.today() - timedelta(days=i))][0]
			except IndexError:
				pass
			# except AttributeError:
			#	 print(self.df)

	def compare_price(self, total_price, number, stock):
		'''
		Returns total income from given share.
		'''
		price = float(total_price)/number
		return number * (self.stockprice(stock, self.market)-price)


class NotEnoughSharesError(Exception):
	pass


class BelowZeroError(Exception):
	pass


class ShareNotFoundError(Exception):
	pass


class UserDatabase:
	'''
	Class UserDatabase
	Contains attributes:

	:param names_bought: list of names of stocks bought
	:type names_bought: str

	:param data: list of data regarding specific stocks: market, stock name, total price of bought stocks, number of bought stocks
	:type data: list

	:param ind_data: data regarding individual series of stocks bought
	:type ind_data:

	:param history: history of transactions (buying and selling)
	:type history: str

	:param currency: selected currency
	:type currency: str
	'''
	def __init__(self, history=[], divs={}, balance={"PL": 0, "US": 0, "HU": 0}): # "DE":  0, "HK": 0, "HU": 0, "JP": 0, "UK": 0}):  # data=[], ind_data=[], , names_bought=[], balance = [PL, US, DE, HK, HU, JP, UK] make a dict of balance
		self.balance = balance
		self.divs = divs
		self.currencies = {"PL": "PLN", "US": "USD", "HU": "HUF"} #, "JP": "JPY", "DE": "EUR", "UK": "GBP", "HK": "HKD"}
		self.names_bought = []
		self.ind_data = []
		self.history = history
		done = []
		for share in self.history:
			if share[1] not in done:
				self.names_bought.append(share[1])
				done.append(share[1])
		for line in self.history:
			if line[4] == "Bought":
				self.add_bought(line[0], line[1], float(line[2]), int(line[3]), 1)
			elif line[4] == "Sold":
				self.add_sold(line[0], line[1], float(line[2]), int(line[3]), 1)
		try:
			if self.ind_data[0][0] == 0:
				self.ind_data.remove(self.ind_data[0])  # removing 0 1 2 3 4
			self.history.remove(self.history[0])
		except Exception:
			pass

	def ret_divs(self):
		return self.divs

	def ret_ind_data(self):
		return self.ind_data

	def ret_names(self):
		return self.names_bought

	def ret_history(self):
		return self.history

	def ret_balance(self, market):
		return self.balance[market]

	def trans_history(self):
		temp = ''
		for line in self.history:
			temp += "[" + line[5] + "] " + line[4] + ' ' + str(line[3]) + ' ' + line[1] + ' stocks on the ' + line[0] + ' market for ' + str(line[2]) + ' ' + self.currency(line[0]) + ' each.\n'
		return temp

	def currency(self, market):
		return self.currencies[market]

	def export_new(self, x, csva):
		'''
		Writing sth in selected file (erases content if file already exists)
		'''
		if type(x) is str:
			myfile = open(csva, 'w')
			myfile.write(x)
			myfile.close()
		else:
			try:
				temp_df = pd.DataFrame(x)
				with open(csva, 'w', newline='') as myfile:
					temp_df.to_csv(myfile, sep=',', index=False)
			except ValueError:
				with open(csva, 'w') as myfile:
					myfile.write(str(x))

	def add_bought(self, market, name, price, number, sys):
		'''
		sys for stating whether it's the user or the system
		'''
		price = float(price)
		number = int(number)
		temp = [market, name, price*number, number, price]
		if price <= 0 or number <= 0 or price > 10000000000000 or number > 10000000000000:
			raise BelowZeroError
		else:
			self.ind_data.append(temp)
			temp2 = [market, name, price, number, "Bought", str(dt.now().date().strftime("%d-%m-%Y")) + " " + str(dt.now().time().strftime("%H-%M-%S"))]
			if not sys:
				self.history.append(temp2)
			self.balance[market] = float(self.balance[market])
			self.balance[market] -= float(price) * float(number)

	def add_sold(self, market, name, price, number, sys):  #TODO change how the substracting works - account for profits in the sum (substract buying price from summarized value, add selling price to balance)
		price = float(price)
		number = int(number)
		if float(price) <= 0 or float(number) <= 0 or float(price) > 10000000000000 or float(number) > 10000000000000:
			raise BelowZeroError
		else:
			num_init = number
			name_fits = []
			sump = 0
			for ind in self.ind_data:
				ind[3] = float(ind[3])
				ind[2] = float(ind[2])
				if ind[0] == market and ind[1] == name:
					name_fits.append(ind)
			i = 0
			for share in name_fits:
				sump += share[3]
			if sump < number:
				raise NotEnoughSharesError
			while number > 0 and i < len(name_fits):
				while name_fits[i][3] > 0 and number > 0:
					name_fits[i][3] -= 1
					number -= 1
				if name_fits[i][3] == 0:
					self.ind_data.remove(name_fits[i])
					i += 1
			temp2 = [market, name, price, num_init, "Sold", str(dt.now().date().strftime("%d-%m-%Y")) + " " + str(dt.now().time().strftime("%H-%M-%S"))]
			if not sys:
				self.history.append(temp2)
			self.balance[market] += float(num_init) * float(price)


# sys.setrecursionlimit(5000)

# swap Data.py for file import (market_XY.csv)
# open_dai() Daily Summary
# open_mys() My Stocks
# open_acc() My Account
# open_set() Setting


class ScrollLabel(QScrollArea):  # class for scrollable label
	def __init__(self, *args, **kwargs):  # constructor
		super(ScrollLabel, self).__init__()
		QMainWindow.__init__(self, *args, **kwargs)
		self.setWidgetResizable(True)  # making widget resizable
		content = QWidget(self)  # making qwidget object
		self.setWidget(content)
		lay = QVBoxLayout(content)  # vertical box layout
		self.label = QLabel(content)  # creating label
		# self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)  # setting alignment to the text
		self.label.setWordWrap(True)  # making label multi-line
		lay.addWidget(self.label)  # adding label to the layout
		self.label.setFont(QFont("Courier", 10))

	def setText(self, text):  # the setText method
		self.label.setText(text)  # setting text to the label

	def setStyle(self, text):
		self.label.setStyleSheet(text)


class ErrWindow(QMainWindow):
	def __init__(self, text):
		super(ErrWindow, self).__init__()
		self.resize(270, 100)
		self.setWindowTitle("ERROR")
		self.message = QLabel(text, self)
		self.message.resize(300, 50)
		self.message.move(10, 10)


class LoadingWindow(QMainWindow):
	def __init__(self):
		super(LoadingWindow, self).__init__()
		self.resize(300, 300)
		self.setWindowTitle("LOADING")
		self.message = QLabel("Connecting to stooq.com...", self)
		self.message.resize(300, 50)


class MainWindow(QMainWindow):
	'''
	Everything regarding the UI.
	'''
	def __init__(self, butt_theme='', back_theme='', profits="No data recorded."):
		super(MainWindow, self).__init__()
		self.resize(980, 520)
		self.setWindowTitle("Superduperstock")
		# self.setWindowIcon(QtGui.QIcon("dragon.gif"))
		self.button_theme = butt_theme
		self.back_theme = back_theme
		self.profits = profits
		self.UI()

	def UI(self):
		self.setStyleSheet(self.back_theme)
		self.welcome = QLabel("Welcome", self)
		self.welcome.move(10, 0)

		# self.dragbutt = PicButton(QtGui.QPixmap('dragon.gif'), self)
		# self.dragbutt.move(700, 700)
		# self.dragbutt.clicked.connect(self.changepic)
		# self.monbutt = PicButton(QtGui.QPixmap('mona.gif'), self)
		# self.monbutt.move(700, 700)
		# self.monbutt.clicked.connect(self.changepic)
		# self.monbutt.hide()

		self.stchoice = QLineEdit(self)
		self.stchoice.move(300, 100)
		self.stchoice.resize(280, 20)

		self.comboBox = QtWidgets.QComboBox(self)
		for market in markets:
			self.comboBox.addItem(market)
		self.comboBox.move(10, 50)
		self.refresh = QPushButton("REFRESH", self)
		self.refresh.move(110, 50)
		self.refresh.setStyleSheet(self.button_theme)
		self.refresh.clicked.connect(self.refresh_market)

		self.welcome = QLabel("Select your market", self)
		self.welcome.move(10, 20)

		self.titles = ['Add new stock', 'Sell stock', 'Daily summary', 'Transaction history', 'Price history', 'My stocks', 'My account', 'Settings']
		self.button_group = QButtonGroup()
		i = 100
		self.choice_list = []
		for title in self.titles:
			self.temp = QPushButton(title, self)
			# self.temp.setToolTip('This is an example button')
			self.temp.resize(100, 40)
			self.choice_list.append(self.temp)
			self.temp.move(50, i)
			i += 40
			self.button_group.addButton(self.temp)
			self.temp.setCheckable(True)
			self.temp.setStyleSheet(self.button_theme)

		self.refresh.setCheckable(True)
		self.refresh.setToolTip("Refresh to switch to selected market.")
		self.button_group.addButton(self.refresh)

		self.choice_list[0].clicked.connect(self.open_add)  # add new stock
		self.choice_list[0].setToolTip("Report buying new stocks.")
		self.inst_add1 = QLabel("Enter the name of new shares:", self)
		self.encount = QLineEdit(self)
		self.inst_add2 = QLabel(self)
		self.inst_add3 = QLabel("Enter the number of shares bought at that price:", self)
		self.numcount = QLineEdit(self)
		self.submit = QPushButton("SUBMIT", self)
		self.submit.clicked.connect(self.submit_add)
		self.submit.setStyleSheet(self.button_theme)
		self.completer = QCompleter(PL)
		self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
		# self.stchoice.setCompleter(self.completer)

		self.choice_list[1].clicked.connect(self.open_sell)  # sell stock
		self.choice_list[1].setToolTip("Report selling old stocks.")
		self.l = QLabel("Select the sold shares", self)
		self.inst_l2 = QLabel(self)
		self.inst_l3 = QLabel("Enter the number of shares sold at that price:", self)
		self.l_drop = QtWidgets.QComboBox(self)
		self.lpri = QLabel("Enter the selling price:", self)
		self.sell_conf = QPushButton("CONFIRM", self)
		self.sell_conf.clicked.connect(self.conf_sell)
		self.sell_conf.setStyleSheet(self.button_theme)

		self.choice_list[2].clicked.connect(self.open_dai)  # daily summary
		self.choice_list[2].setToolTip("Daily summary of income.")
		self.lege = QLabel("Stock	 	   Profit	   		   Buying price per share   		Number", self)
		# self.choice_list[2].setStyleSheet("background-color: yellow")
		self.loading = QLabel("Loading...", self)

		self.choice_list[3].clicked.connect(self.open_sum)  # transaction history
		self.choice_list[3].setToolTip("History of all transactions.")
		# self.j = QLabel("Total balance:", self)
		self.tran_his = QLabel("History of transactions:", self)
		# self.tran_his_list = QLabel(self)
		self.tran_his_list = ScrollLabel(self)
		self.export_butt = QPushButton("EXPORT TO .TXT", self)
		self.export_butt.clicked.connect(self.export)
		self.export_butt.setStyleSheet(self.button_theme)
		# self.bal = QLabel(self)

		self.choice_list[4].clicked.connect(self.open_his)  # price history
		self.choice_list[4].setToolTip("Look up the price history of any stock.")
		self.k = QLabel("Select the desired stock (from currently selected market)", self)
		self.price_his_list = ScrollLabel(self)
		self.price_his_list.setFont(QFont("Courier", 10))
		self.price_his_list.setStyleSheet("")
		self.search = QPushButton("SEARCH", self)
		self.search.clicked.connect(self.search_price)
		self.search.setStyleSheet(self.button_theme)

		self.choice_list[5].clicked.connect(self.open_mys)  # my stocks - summary of ind_data, sorted by stock name
		self.choice_list[5].setToolTip("All reported share packets.")
		# self.choice_list[5].setStyleSheet("background-color: yellow")
		self.legend = QLabel("Market	 	Name	   	Price per share	  Number", self)

		self.choice_list[6].clicked.connect(self.open_acc)  # account
		# self.choice_list[6].setStyleSheet("background-color: yellow")
		self.acclab = QLabel("My Account", self)
		self.choice_list[6].setToolTip("Balances in all currencies.")
		self.ballab = QLabel(self)

		self.choice_list[7].clicked.connect(self.open_set)  # settings
		# self.choice_list[7].setStyleSheet("background-color: red")
		self.choice_list[7].setToolTip("Change background theme.")
		self.set_label = QLabel("Theme:", self)
		self.theme1_button = QPushButton(self)
		self.theme1_button.setStyleSheet("background-color: lime")
		self.theme1_button.clicked.connect(self.theme1)
		self.theme2_button = QPushButton(self)
		self.theme2_button.setStyleSheet("background-color: magenta")
		self.theme2_button.clicked.connect(self.theme2)
		self.theme3_button = QPushButton(self)
		self.theme3_button.setStyleSheet("background-color: #a0a0ff")
		self.theme3_button.clicked.connect(self.theme3)
		self.theme4_button = QPushButton(self)
		self.theme4_button.setStyleSheet("background-color: yellow")
		self.theme4_button.clicked.connect(self.theme4)
		self.theme5_button = QPushButton(self)
		self.theme5_button.setStyleSheet("background-color: #e1e1e1")
		self.theme5_button.clicked.connect(self.theme5)

		# wrapping widgets into group for reset() to work on them
		self.menu_widgets = [self.l, self.l_drop, self.lpri, self.inst_l2,
							 self.inst_l3, self.tran_his, self.tran_his_list, self.export_butt,
							 self.sell_conf, self.k, self.price_his_list, self.search,
							 self.inst_add1, self.encount, self.stchoice, self.submit,
							 self.inst_add2, self.inst_add3, self.numcount, self.acclab, self.lege,
							 self.ballab, self.theme1_button, self.theme2_button, self.theme3_button, self.theme4_button, self.theme5_button, self.set_label, self.legend, self.loading]
		self.widgets = [self.l, self.l_drop, self.lpri, self.inst_l2,
						self.inst_l3, self.tran_his, self.tran_his_list, self.export_butt,
						self.sell_conf, self.k, self.price_his_list, self.search,
						self.inst_add1, self.encount, self.stchoice, self.submit,
						self.inst_add2, self.inst_add3, self.numcount, self.acclab, self.lege,
						self.ballab, self.theme1_button, self.theme2_button, self.theme3_button, self.theme4_button, self.theme5_button, self.set_label, self.legend, self.loading,
						self.choice_list[0], self.choice_list[1], self.choice_list[2], self.choice_list[3],
						self.choice_list[4], self.choice_list[5], self.choice_list[6], self.choice_list[7],
						self.comboBox, self.refresh]
		for widget in self.widgets:
			widget.show()
		self.reset()

	# def changepic(self):
	#	 self.dragbutt.hide()
	#	 self.monbutt.show()

	def open_add(self, market):
		self.reset()
		self.stchoice.show()
		self.encount.show()
		self.encount.move(300, 200)
		self.numcount.show()
		self.numcount.move(300, 300)
		self.inst_add1.show()
		self.inst_add1.resize(300, 20)
		self.inst_add1.move(300, 50)
		self.inst_add2.show()
		self.inst_add2.resize(310, 20)
		self.inst_add2.move(300, 150)
		self.inst_add2.setText("Enter the price of the moment of the purchase [" + self.ret_currency([self.comboBox.currentText()]) + "]:")
		self.inst_add3.show()
		self.inst_add3.resize(300, 20)
		self.inst_add3.move(300, 250)
		self.submit.show()
		self.submit.move(300, 350)
		market = PL
		if self.comboBox.currentText() == "PL":
			market = PL
		if self.comboBox.currentText() == "US":
			market = US
		# if self.comboBox.currentText() == "DE":
		# 	market = DE
		# if self.comboBox.currentText() == "HK":
		# 	market = HK
		if self.comboBox.currentText() == "HU":
			market = HU
		# if self.comboBox.currentText() == "JP":
		# 	market = JP
		# if self.comboBox.currentText() == "UK":
		# 	market = UK
		self.completer = QCompleter(market)
		self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self.stchoice.setCompleter(self.completer)
		# self.choice_list[0].hide()

	def submit_add(self):
		self.markets = {"PL": PL, "US": US, "HU": HU} #, "JP": JP, "DE": DE, "UK": UK, "HK": HK}
		# if self.comboBox.currentText() == "PL":
		#	 market = PL
		# if self.comboBox.currentText() == "US":
		#	 market = US
		# if self.comboBox.currentText() == "DE":
		#	 market = DE
		# if self.comboBox.currentText() == "HK":
		#	 market = HK
		# if self.comboBox.currentText() == "HU":
		#	 market = HU
		# if self.comboBox.currentText() == "JP":
		#	 market = JP
		# if self.comboBox.currentText() == "UK":
		#	 market = UK
		market = self.markets[self.comboBox.currentText()]
		try:
			price = float(self.encount.text())
			number = int(self.numcount.text())
			if self.stchoice.text().upper() not in market:
				# mess = self.stchoice.text() + ' not found.'
				# self.ErrBox("ERROR", mess)
				self.AddBox()
			else:
				dbase.add_bought(self.comboBox.currentText(), self.stchoice.text().upper(), price, number, 0)
				self.ErrBox("SUCCESS", "Shares added successfully.")
			# print(dbase.ret_data())
		except (ValueError, BelowZeroError):
			self.ErrBox("ERROR", "Invalid price and/or number of shares.")  # add option to update database?
		# print(float(self.encount.text()))

	def refresh_market(self):
		self.reset()
		# self.update_profit()

	def open_sell(self):
		self.reset()
		self.l_drop.clear()
		done = []
		for share in dbase.ret_ind_data():
			if share[0] == self.comboBox.currentText():
				if share[1] not in done:
					# self.l_drop.addItem(share[1])
					done.append(share[1])
		done.sort()
		for share in done:
			self.l_drop.addItem(share)
		self.l_drop.show()
		self.l_drop.move(300, 90)
		self.l.show()
		self.l.move(300, 50)
		self.l.resize(300, 20)
		self.inst_l2.show()
		self.inst_l2.move(300, 150)
		self.inst_l2.resize(300, 20)
		self.inst_l2.setText("Enter the price in the moment of selling [" + self.ret_currency([self.comboBox.currentText()]) + "]:")
		self.inst_l3.show()
		self.inst_l3.resize(300, 20)
		self.inst_l3.move(300, 250)
		self.encount.show()
		self.encount.move(300, 200)
		self.numcount.show()
		self.numcount.move(300, 300)
		self.sell_conf.show()
		self.sell_conf.move(300, 350)

	def conf_sell(self):
		'''
		Removing stocks from database after clicking the "CONFIRM" button.
		'''
		# if self.l_drop.currentText() not in dbase.ret_names():
		# 	mess = self.l_drop.currentText() + ' not found.'
		# 	self.ErrBox("ERROR", mess)
		# else:
		try:
			price = float(self.encount.text())
			number = int(self.numcount.text())
			dbase.add_sold(self.comboBox.currentText(), self.l_drop.currentText(), price, number, 0)
			self.ErrBox("SUCCESS", "Shares removed successfully.")
		except (ValueError, BelowZeroError):
			self.ErrBox("ERROR", "Invalid price and/or number of shares.")
		except NotEnoughSharesError:
			self.ErrBox("ERROR", "Not enough shares.")
		except ShareNotFoundError:
			self.ErrBox("ERROR", "Share not found.")  # not gonna need it once the program fully works

	def open_dai(self):
		'''
		Menu displayed after clicking the "Daily summary" button.
		'''
		self.reset()
		self.loading.show()
		self.loading.move(300, 300)
		try:
			self.lege.show()
			self.lege.move(300, 50)
			self.lege.resize(500, 30)
			self.price_his_list.show()
			self.price_his_list.resize(500, 350)
			self.price_his_list.move(300, 90)
			sort_it = sorted(dbase.ret_ind_data(), key=lambda x: x[1])
			tex = ''
			prof_ind = 0.0
			temp_ind = ''
			prev = ""
			prev_curr_price = 0
			# try:
			# raise AttributeError - test bez zuzywania prob
			counter = 0
			for ind in sort_it:
				temp = Stock(ind[0])
				# if ind[1]!=prev:
				# 	profit = str(round(temp.compare_price(float(ind[4])*float(ind[3]), float(ind[3]), ind[1]), 2))
				# else:
				# 	profit = prev_profit

				if ind[1]!=prev:
					number = float(ind[3])
					total_price = float(ind[4])*float(ind[3])
					price = float(total_price)/number
					curr_price = temp.stockprice(ind[1], ind[0])
					profit = number * (curr_price-price)
					profit = str(round(profit, 2))
				else:
					number = float(ind[3])
					total_price = float(ind[4])*float(ind[3])
					price = float(total_price)/number
					profit = number * (prev_curr_price-price)
					profit = str(round(profit, 2))
				prev_curr_price = curr_price
				prev = ind[1]

				prof_ind += float(profit)
				if ind[1] != temp_ind and temp_ind != '':
					prof_ind -= float(profit)
					tex += "Overall profit from " + temp_ind + ": " + str(round(float(prof_ind), 2)) + ' ' + self.ret_currency(ind) + '\n' + "Last dividend from that stock: "
					try:
						tex += str(dbase.ret_divs()[temp_ind]) + ' ' + self.ret_currency(ind) + ' per share.\n\n'
					except KeyError:
						tex += "[NO DATA]" + '\n\n'
					prof_ind = float(profit)
				# tex += "Profit from stock " + ind[1] + " (if sold at last closing) - " + profit + " " + self.ret_currency(ind) + " (bought for " + str(round(float(ind[4]), 2)) + self.ret_currency(ind) + ')\n'
				tex += ind[1] # + "	   " + profit + " " + self.ret_currency(ind) + "	 " + str(round(float(ind[4]), 2)) + " " + self.ret_currency(ind) + "	  " + str(int(ind[3])) + '\n'
				tex += ' '*(12-len(str(ind[1])))
				tex += profit + " " + self.ret_currency(ind)
				tex += ' '*(20-len(str(profit) + " " + self.ret_currency(ind)))
				tex += str(round(float(ind[4]), 2)) + " " + self.ret_currency(ind)
				tex += ' '*(20-len(str(round(float(ind[4]), 2)) + " " + self.ret_currency(ind)))
				tex += str(int(ind[3])) + '\n'
				# tex += ' '*(12-len(str(int(ind[3]))))
				temp_ind = ind[1]
				counter += 1
				if counter == len(sort_it):
					prof_ind -= float(profit)
					tex += "Overall profit from " + temp_ind + ": " + str(round(float(prof_ind), 2)) + '\n' + "Last dividend from that stock: "
					try:
						tex += str(dbase.ret_divs()[temp_ind]) + ' ' + self.ret_currency(ind) + ' per share.\n\n'
					except KeyError:
						tex += "[NO DATA]" + '\n\n'
					temp_ind = 0.0

			self.profits = tex
			self.price_his_list.setText(tex)
			# except AttributeError:
			# 	self.price_his_list.setText(self.profits)
			# 	self.ErrBox("ERROR", "Reached the daily limit of data extractions from stooq.com. Showing the last recorded data from current session.")
		except requests.exceptions.ConnectionError:
			self.ErrBox("ERROR", "Connection to stooq.com could not be established.\nCheck your connection and access to stooq.com\nand try again later.")

	def ret_currency(self, ind_line):
		if ind_line[0] == "PL":
			return "PLN"
		elif ind_line[0] == "US":
			return "USD"
		elif ind_line[0] == "HU":
			return "HUF"
		# elif ind_line[0] == "JP":
		# 	return "JPY"
		# elif ind_line[0] == "DE":
		# 	return "EUR"
		# elif ind_line[0] == "UK":
		# 	return "GBP"
		# elif ind_line[0] == "HK":
		# 	return "HKD"

	def open_sum(self):
		'''
		Menu displayed after clicking the "Transaction history" button.
		'''
		self.reset()
		# self.j.show()
		# self.j.move(300, 50)
		self.tran_his.show()
		self.tran_his.move(250, 50)
		self.tran_his.resize(150, 20)
		self.tran_his_list.move(250, 70)
		self.tran_his_list.resize(700, 380)
		self.tran_his_list.show()
		try:
			self.tran_his_list.setText(dbase.trans_history())
		except KeyError:
			pass
		self.export_butt.show()
		self.export_butt.move(250, 450)
		self.export_butt.resize(100, 40)
		# self.bal.setText(str(round(float(dbase.ret_balance(self.comboBox.currentText())), 2)))
		# self.bal.show()
		# self.bal.move(400, 50)

	def export(self):
		'''
		Exporting transaction history to readable .txt file after clicking the "EXPORT TO .TXT" BUTTON.
		'''
		temp_list = []
		try:
			temp_list.append(dbase.trans_history())
			dbase.export_new(temp_list, "stock_history_readable.txt")
			self.ErrBox("SUCCESS", 'History exported successfully to "stock_history_readable.txt" file')
		except KeyError:
			self.ErrBox("ERROR", "History empty. No file generated.")

	def open_his(self):
		self.reset()
		self.k.show()
		self.k.move(300, 50)
		self.k.resize(300, 20)
		self.search.show()
		self.search.move(600, 95)
		self.stchoice.show()
		market = PL
		if self.comboBox.currentText() == "PL":
			market = PL
		if self.comboBox.currentText() == "US":
			market = US
		# if self.comboBox.currentText() == "DE":
		# 	market = DE
		# if self.comboBox.currentText() == "HK":
		# 	market = HK
		if self.comboBox.currentText() == "HU":
			market = HU
		# if self.comboBox.currentText() == "JP":
		# 	market = JP
		# if self.comboBox.currentText() == "UK":
		# 	market = UK
		self.completer = QCompleter(market)
		self.completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
		self.stchoice.setCompleter(self.completer)

	def search_price(self):
		temp = Stock(self.comboBox.currentText())
		# self.price_his_list.setText((temp.importstock(self.stchoice.text())))
		temp_names = {"PL": PL,  "US": US, "HU": HU} #, "HK": HK, "JP": JP, "UK": UK, "DE": DE}
		if self.stchoice.text().upper() not in dbase.ret_names() and self.stchoice.text() not in temp_names[self.comboBox.currentText()]:
			self.ErrBox("ERROR", "Stock name not found.")
		else:
			self.price_his_list.setText(temp.importstock(self.stchoice.text()).to_string())
			self.price_his_list.show()
			self.price_his_list.resize(500, 350)
			self.price_his_list.move(300, 150)

	def open_mys(self):
		self.reset()
		self.legend.show()
		self.legend.resize(350, 30)
		self.legend.move(300, 50)
		temp = ''
		maxlast = 0
		templist = sorted(dbase.ret_ind_data(), key=lambda x: x[1])
		for ind in templist:
			counter = 0
			for element in ind:
				if counter != 4 and counter != 2:
					try:
						element = int(element)
					except ValueError:
						pass
					temp += str(element)
					temp += ' '*(12-len(str(element)))
				elif counter == 2:
					temp += str(round(float(ind[4]), 2))
					temp += ' '*(12-len(str(round(ind[4], 2))))
				else:
					if maxlast < len(str(element)):
						maxlast = len(str(element))
				counter += 1
			temp += '\n'
		self.price_his_list.setFont(QFont("Courier", 10))
		self.price_his_list.setText(temp)
		self.price_his_list.setStyle('')
		self.price_his_list.show()
		self.price_his_list.resize((350+(maxlast-3)*5), 350)
		self.price_his_list.move(300, 90)

	def open_acc(self):  # what else - maybe useless?
		self.reset()
		self.acclab.show()
		self.acclab.move(300, 50)
		self.acclab.setFont(QFont("Calibri", 14))
		self.ballab.show()
		self.ballab.resize(300, 100)
		# self.ballab.setText("Current balance:\n" + str(round(float(dbase.ret_balance("PL")), 2)) + " PLN\n" + str(round(float(dbase.ret_balance("US")), 2)) + " USD\n" + str(round(float(dbase.ret_balance("DE")), 2)) + " EUR\n" + str(round(float(dbase.ret_balance("HK")), 2)) + " HKD\n" + str(round(float(dbase.ret_balance("HU")), 2)) + " HUF\n" + str(round(float(dbase.ret_balance("JP")), 2)) + " JPY\n" + str(round(float(dbase.ret_balance("UK")), 2)) + " GBP")
		self.ballab.setText("Current balance:\n" + str(round(float(dbase.ret_balance("PL")), 2)) + " PLN\n" + str(round(float(dbase.ret_balance("US")), 2)) + " USD\n" + str(round(float(dbase.ret_balance("HU")), 2)) + " HUF")
		self.ballab.move(300, 100)

	def open_set(self):  # unfinished
		self.reset()
		self.set_label.show()
		self.set_label.move(300, 50)
		self.set_label.setFont(QFont("Calibri", 14))
		self.theme1_button.show()
		self.theme1_button.move(300, 100)
		self.theme2_button.show()
		self.theme2_button.move(400, 100)
		self.theme3_button.show()
		self.theme3_button.move(500, 100)
		self.theme4_button.show()
		self.theme4_button.move(600, 100)
		self.theme5_button.show()
		self.theme5_button.move(700, 100)
		# language?

	def theme1(self):
		self.button_theme = "background-color: lime"
		self.back_theme = "background-color: #a0ffa0"
		self.global_reset()
		self.open_set()
		self.price_his_list.setFont(QFont("Courier", 10))

	def theme2(self):
		self.button_theme = "background-color: magenta"
		self.back_theme = "background-color: pink"
		self.global_reset()
		self.open_set()
		self.price_his_list.setFont(QFont("Courier", 10))

	def theme3(self):
		self.button_theme = "background-color: #a0a0ff"
		self.back_theme = "background-color: #d0d0ff"
		self.global_reset()
		self.open_set()
		self.price_his_list.setFont(QFont("Courier", 10))

	def theme4(self):
		self.button_theme = "background-color: yellow"
		self.back_theme = "background-color: #ffffa0"
		self.global_reset()
		self.open_set()
		self.price_his_list.setFont(QFont("Courier", 10))

	def theme5(self):
		self.button_theme = ""
		self.back_theme = ""
		self.global_reset()
		self.open_set()

	def global_reset(self):
		for widget in self.widgets:
			widget.hide()
		self.UI()

	def reset(self):
		for widget in self.menu_widgets:
			widget.hide()

	def ErrBox(self, title, message):
		'''
		Displaying error box with message and title of choice.
		'''
		self.err = QtWidgets.QMessageBox()
		self.err.setWindowTitle(title)
		self.err.setText(message)
		if title == "ERROR":
			self.err.setIcon(QMessageBox.Critical)
		else:
			self.err.setIcon(QMessageBox.Information)
		# self.err.setWindowIcon(QtGui.QIcon("mona.gif"))
		self.err.exec_()

	def AddBox(self):
		'''
		Displayed after user tries to enter non-existent stock. Asks whether to ask the stock to database.
		'''
		self.addb = QtWidgets.QMessageBox()
		self.addb.setWindowTitle("ERROR")
		self.addb.setText("Stock not found on the market. Do you wish to add it to database?")
		self.addb.setIcon(QMessageBox.Warning)
		self.addb.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
		self.addb.setDefaultButton(QMessageBox.Yes)
		# self.addb.addButton(self.acc)
		# self.acc.clicked.connect(self.defnew)
		self.addb.buttonClicked.connect(self.defnew)
		self.addb.exec_()

	def defnew(self, button):
		if button.text() == "&Yes":
			if self.comboBox.currentText() == "PL":
				market = PL
			if self.comboBox.currentText() == "US":
				market = US
			# if self.comboBox.currentText() == "DE":
			# 	market = DE
			# if self.comboBox.currentText() == "HK":
			# 	market = HK
			if self.comboBox.currentText() == "HU":
				market = HU
			# if self.comboBox.currentText() == "JP":
			# 	market = JP
			# if self.comboBox.currentText() == "UK":
			# 	market = UK
			test = Stock(self.comboBox.currentText())
			if len(test.importstock(self.stchoice.text())):
				market.append(self.stchoice.text())
				self.ErrBox("SUCCESS", "Stocks added to database")
			else:
				self.ErrBox("ERROR", "Stock not found on stooq.com. Check your connection and try again later.")
		else:
			pass

	def ret_butt_theme(self):
		return str(self.button_theme)

	def ret_back_theme(self):
		return str(self.back_theme)

	def closeEvent(self, event):
		'''
		Save upon quitting.
		'''
		dbase.export_new(dbase.ret_history(), "stock_history.csv")
		dbase.export_new(self.ret_butt_theme(), "button_theme.txt")
		dbase.export_new(self.ret_back_theme(), "background_theme.txt")
		dbase.export_new(self.profits, "daily_summary.txt")
		dbase.export_new(dbase.ret_divs(), "finance_history.csv")
		# dbase.export_new(dbase.ret_data(), "stock_data.csv")
		# dbase.export_new(dbase.ret_ind_data(), "stock_ind_data.csv")
		# dbase.export_new("PL " + str(dbase.ret_balance("PL")) + '\nUS ' + str(dbase.ret_balance("US")) +
		# "\nDE " + str(dbase.ret_balance("DE")) + "\nHK " + str(dbase.ret_balance("HK")) + "\nHU " + str(dbase.ret_balance("HU")) +"\nJP " + str(dbase.ret_balance("JP")) + "\nUK " + str(dbase.ret_balance("UK")), "stock_balance.txt")
		# dbase.export_new(PL, "market_PL.csv") ??????? tf is that
		# dbase.export_new(US, "market_US.csv")
		# dbase.export_new(DE, "market_DE.csv")
		# dbase.export_new(HK, "market_HK.csv")
		# dbase.export_new(HU, "market_HU.csv")
		# dbase.export_new(JP, "market_JP.csv")
		# dbase.export_new(UK, "market_UK.csv")
		# reply = QMessageBox.question(
		#	 self, "Message",
		#	 "Are you sure you want to quit? Any unsaved work will be lost.",
		#	 QMessageBox.Save | QMessageBox.Close | QMessageBox.Cancel,
		#	 QMessageBox.Save)

		# if reply == QMessageBox.Close:
		#	 app.quit()
		# else:
		#	 pass

# note - I had no idea how to create a database back then
markets = ["PL", "US", "HU"]   #["PL", "US", "DE", "HK", "HU", "JP", "UK"]
PL = ['01C', '06N', '08N', '11B', '1AT', '2CP', '2IT', '4FM', '4MB', '4MS', '5AH', '7FT', '7LV', 'AAS', 'AAT', 'ABE', 'ABK', 'ABS', 'ACA', 'ACG', 'ACK', 'ACP', 'ACR', 'ACT',
      'ADV', 'ADX', 'AED', 'AER', 'AFC', 'AFH', 'AGL', 'AGO', 'AGP', 'AGT', 'AIN', 'AIT', 'ALD', 'ALI', 'ALL', 'ALR', 'ALS', 'ALU', 'AMB', 'AMC', 'AML', 'AOL', 'APA', 'APC', 'APE',
      'APL', 'APN', 'APR', 'APS', 'APT', 'AQA', 'AQT', 'AQU', 'ARA', 'ARC', 'ARE', 'ARG', 'ARH', 'ARI', 'ARK', 'ARR', 'ART', 'ARX', 'ASA', 'ASB', 'ASE', 'ASM', 'ASP', 'ASR', 'ASS',
      'AST', 'ATA', 'ATC', 'ATD', 'ATG', 'ATL', 'ATM', 'ATO', 'ATP', 'ATR', 'ATS', 'ATT', 'AUG', 'AUX', 'AVE', 'AWB', 'AWM', 'AZC', 'B24', 'BAH', 'BAL', 'BBA', 'BBD', 'BBT', 'BCI',
      'BCM', 'BDG', 'BDX', 'BDZ', 'BEP', 'BER', 'BGD', 'BHW', 'BHX', 'BIK', 'BIO', 'BIP', 'BKM', 'BLO', 'BLR', 'BLT', 'BLU', 'BMC', 'BML', 'BMX', 'BNP', 'BOS', 'BOW', 'BPC', 'BPN',
      'BPX', 'BRA', 'BRG', 'BRH', 'BRO', 'BRS', 'BRU', 'BSA', 'BST', 'BTC', 'BTG', 'BTK', 'BTX', 'BVT', 'CAI', 'CAM', 'CAR', 'CBD', 'CCC', 'CCE', 'CDA', 'CDL', 'CDR', 'CDT', 'CEZ',
      'CFG', 'CFI', 'CFS', 'CHP', 'CIE', 'CIG', 'CLC', 'CLD', 'CLE', 'CLN', 'CMC', 'CMI', 'CMP', 'CMR', 'CNT', 'COG', 'COR', 'CPA', 'CPD', 'CPG', 'CPL', 'CPS', 'CRB', 'CRC', 'CRJ',
      'CRM', 'CRS', 'CSY', 'CTE', 'CTF', 'CZK', 'CZT', 'DADA', 'DAM', 'DAT', 'DBC', 'DBE', 'DCR', 'DDI', 'DEG', 'DEK', 'DEL', 'DEV', 'DGA', 'DKR', 'DNP', 'DNS', 'DOK', 'DOM', 'DPL',
      'DRF', 'DRG', 'DTR', 'DTX', 'DUA', 'DVL', 'EAH', 'EAT', 'EBX', 'EC2', 'ECA', 'ECC', 'ECH', 'ECL', 'EDI', 'EDN', 'EEX', 'EFE', 'EFK', 'EGH', 'EHG', 'EKP', 'EKS', 'ELB', 'ELM',
      'ELQ', 'ELT', 'ELZ', 'EMA', 'EMC', 'ENA', 'ENE', 'ENG', 'ENI', 'ENP', 'ENT', 'EON', 'EPR', 'ERB', 'ERG', 'ERH', 'ETL', 'ETX', 'EUC', 'EUR', 'EXA', 'EXC', 'F51', 'FEE', 'FER',
      'FFI', 'FHD', 'FIG', 'FIV', 'FLG', 'FMF', 'FMG', 'FON', 'FOR', 'FOX', 'FPO', 'FRO', 'FSG', 'FTE', 'FTN', 'FVE', 'GAL', 'GCN', 'GEN', 'GIF', 'GIFA', 'GKI', 'GKS', 'GLC', 'GNB',
      'GNG', 'GOB', 'GOP', 'GOV', 'GPW', 'GRC', 'GRM', 'GRN', 'GTC', 'GTF', 'GTN', 'GTS', 'GX1', 'H4F', 'HDR', 'HEL', 'HMI', 'HMP', 'HOR', 'HPS', 'HRC', 'HRL', 'HRP', 'HRS', 'HUB',
      'I2D', 'ICA', 'ICD', 'ICE', 'IDA', 'IDH', 'IDM', 'IFA', 'IFC', 'IFI', 'IFR', 'IGN', 'IGS', 'IGT', 'IMC', 'IMG', 'IMP', 'IMS', 'INC', 'INF', 'ING', 'INK', 'INL', 'INM', 'INP',
      'INW', 'IOD', 'IPE', 'IPF', 'IPL', 'IPO', 'IRL', 'ISG', 'IST', 'ITB', 'ITL', 'ITM', 'IUS', 'IVE', 'IZB', 'IZO', 'IZS', 'JJB', 'JRH', 'JSW', 'JWA', 'JWC', 'JWW', 'K2I', 'KBD',
      'KBJ', 'KBT', 'KCH', 'KCI', 'KER', 'KGH', 'KGL', 'KGN', 'KKH', 'KLN', 'KME', 'KMP', 'KOM', 'KOR', 'KPC', 'KPL', 'KRC', 'KRI', 'KRK', 'KRU', 'KSG', 'KSW', 'KTY', 'KVT', 'LAB',
      'LBT', 'LBW', 'LEN', 'LET', 'LGT', 'LKD', 'LPP', 'LPS', 'LRQ', 'LSH', 'LSI', 'LTS', 'LTX', 'LUG', 'LUK', 'LVC', 'LWB', 'MAB', 'MAK', 'MBF', 'MBK', 'MBR', 'MBW', 'MCE', 'MCI',
      'MCP', 'MCR', 'MDA', 'MDG', 'MDI', 'MDN', 'MDP', 'MER', 'MEX', 'MFD', 'MFO', 'MGT', 'MIL', 'MIR', 'MLB', 'MLG', 'MLK', 'MLS', 'MLT', 'MMC', 'MMD', 'MNC', 'MND', 'MNS', 'MOE',
      'MOJ', 'MOL', 'MON', 'MOV', 'MPH', 'MPY', 'MRB', 'MRC', 'MRG', 'MRH', 'MSP', 'MSW', 'MSZ', 'MTN', 'MVP', 'MWT', 'MXC', 'MZA', 'NET', 'NEU', 'NGG', 'NNG', 'NRS', 'NST', 'NTT',
      'NTW', 'NVA', 'NVG', 'NVT', 'NVV', 'NWA', 'NWG', 'NXB', 'NXG', 'OAT', 'OBL', 'ODL', 'OEX', 'OML', 'OPF', 'OPL', 'OPM', 'OPN', 'OPT', 'ORG', 'ORL', 'OTM', 'OTS', 'OUT', 'OVI',
      'OVO', 'OXY', 'P24', 'P2B', 'P2C', 'PAS', 'PAT', 'PBG', 'PBT', 'PBX', 'PCE', 'PCF', 'PCFA', 'PCR', 'PCX', 'PDG', 'PDZ', 'PEM', 'PEN', 'PEO', 'PEP', 'PFD', 'PFG', 'PGE', 'PGM',
      'PGN', 'PGO', 'PHN', 'PHR', 'PIT', 'PIW', 'PJP', 'PKN', 'PKO', 'PKP', 'PLE', 'PLG', 'PLI', 'PLM', 'PLW', 'PLX', 'PLZ', 'PMA', 'PMP', 'PND', 'PNT', 'PNW', 'POZ', 'PPS', 'PRD',
      'PRF', 'PRL', 'PRM', 'PRN', 'PRO', 'PRS', 'PRT', 'PSH', 'PSW', 'PTE', 'PTH', 'PTN', 'PTW', 'PUE', 'PUN', 'PUR', 'PURA', 'PWX', 'PXM', 'PYL', 'PZU', 'QON', 'QRS', 'QUB', 'R22',
      'RAF', 'RBS', 'RBW', 'RDG', 'RDL', 'RDN', 'RDS', 'REM', 'RES', 'RFK', 'RHD', 'RLP', 'RMK', 'RNC', 'RNK', 'RON', 'RPC', 'RSP', 'RSY', 'RVU', 'RWL', 'S4E', 'SAN', 'SBE', 'SCP',
      'SCS', 'SEK', 'SEL', 'SEN', 'SES', 'SEV', 'SFD', 'SFG', 'SFN', 'SFS', 'SGN', 'SHD', 'SHG', 'SIM', 'SKA', 'SKH', 'SKL', 'SKT', 'SLV', 'SME', 'SMS', 'SNG', 'SNK', 'SNT', 'SNW',
      'SNX', 'SOK', 'SOL', 'SON', 'SPH', 'SPL', 'SPR', 'SSK', 'STA', 'STF', 'STP', 'STX', 'SUL', 'SUN', 'SUW', 'SVRS', 'SWD', 'SWG', 'SWK', 'SWT', 'SZR', 'T2P', 'TAR', 'TBL', 'TEN',
      'THD', 'TIG', 'TIM', 'TLG', 'TLS', 'TLT', 'TLV', 'TLX', 'TME', 'TMP', 'TOA', 'TOR', 'TOS', 'TOW', 'TPE', 'TRI', 'TRK', 'TRN', 'TRR', 'TSG', 'TXN', 'TYP', 'U2K', 'UCG', 'UFC',
      'ULG', 'ULM', 'UNI', 'UNT', 'URS', 'UTD', 'VAB', 'VAR', 'VDS', 'VEE', 'VER', 'VGO', 'VIN', 'VKT', 'VOT', 'VOX', 'VRB', 'VRG', 'VTI', 'VTL', 'VVD', 'WAS', 'WIK', 'WIS', 'WLT',
      'WOD', 'WOJ', 'WPL', 'WRE', 'WSE', 'WTN', 'WWL', 'WXF', 'XPL', 'XTB', 'XTP', 'YAN', 'YOL', 'ZAP', 'ZEP', 'ZMT', 'ZRE', 'ZST', 'ZUE', 'ZUK', 'ZWC']
US = ['A', 'AA', 'AAA', 'AAAU', 'AACG', 'AACQ', 'AACQU', 'AACQW', 'AAIC', 'AAIC_B', 'AAIC_C', 'AAL', 'AAMC', 'AAME', 'AAN', 'AAOI', 'AAON', 'AAP', 'AAPL', 'AAT', 'AAU', 'AAWW',
      'AAXN', 'AB', 'ABB', 'ABBV', 'ABC', 'ABCB', 'ABCL', 'ABCM', 'ABEO', 'ABEQ', 'ABEV', 'ABG', 'ABIO', 'ABM', 'ABMD', 'ABNB', 'ABR', 'ABR_A', 'ABR_B', 'ABR_C', 'ABST', 'ABT', 'ABTX',
      'ABUS', 'AC', 'ACA', 'ACAC', 'ACACU', 'ACACW', 'ACAD', 'ACAM', 'ACAMU', 'ACAMW', 'ACB', 'ACBI', 'ACC', 'ACCD', 'ACCO', 'ACEL', 'ACER', 'ACES', 'ACET', 'ACEV', 'ACEVU', 'ACEVW',
      'ACGL', 'ACGLO', 'ACGLP', 'ACH', 'ACHC', 'ACHV', 'ACI', 'ACIA', 'ACIC-U', 'ACIC-WS', 'ACIC', 'ACIO', 'ACIU', 'ACIW', 'ACKIU', 'ACLS', 'ACM', 'ACMR', 'ACN', 'ACNB', 'ACND-U', 'ACND-WS',
      'ACND', 'ACOR', 'ACP', 'ACRE', 'ACRS', 'ACRX', 'ACSG', 'ACSI', 'ACST', 'ACTC', 'ACTCU', 'ACTCW', 'ACTG', 'ACTV', 'ACU', 'ACV', 'ACVF', 'ACY', 'ADAP', 'ADBE', 'ADC', 'ADCT', 'ADES',
      'ADFI', 'ADI', 'ADIL', 'ADILW', 'ADM', 'ADMA', 'ADME', 'ADMP', 'ADMS', 'ADNT', 'ADOC', 'ADOCR', 'ADOCW', 'ADP', 'ADPT', 'ADS', 'ADSK', 'ADT', 'ADTN', 'ADTX', 'ADUS', 'ADV', 'ADVM',
      'ADVWW', 'ADX', 'ADXN', 'ADXS', 'AE', 'AEB', 'AEE', 'AEF', 'AEFC', 'AEG', 'AEGN', 'AEHL', 'AEHR', 'AEIS', 'AEL', 'AEL_A', 'AEL_B', 'AEM', 'AEMD', 'AENZ', 'AEO', 'AEP', 'AEPPL', 'AEPPZ',
      'AER', 'AERI', 'AES', 'AESE', 'AEY', 'AEYE', 'AEZS', 'AFB', 'AFC', 'AFG', 'AFGB', 'AFGC', 'AFGD', 'AFGE', 'AFI', 'AFIB', 'AFIF', 'AFIN', 'AFINO', 'AFINP', 'AFL', 'AFLG', 'AFMC', 'AFMD',
      'AFSM', 'AFT', 'AFTY', 'AFYA', 'AG', 'AGBA', 'AGBAR', 'AGBAU', 'AGBAW', 'AGC', 'AGCO', 'AGCUU', 'AGCWW', 'AGD', 'AGE', 'AGEN', 'AGFS', 'AGGP', 'AGGY', 'AGI', 'AGIO', 'AGLE', 'AGM-A',
      'AGM', 'AGMH', 'AGM_C', 'AGM_D', 'AGM_E', 'AGM_F', 'AGNC', 'AGNCM', 'AGNCN', 'AGNCO', 'AGNCP', 'AGO', 'AGO_B', 'AGO_E', 'AGO_F', 'AGR', 'AGRO', 'AGRX', 'AGS', 'AGT', 'AGTC', 'AGX', 'AGYS',
      'AHAC', 'AHACU', 'AHACW', 'AHC', 'AHCO', 'AHH', 'AHH_A', 'AHL_C', 'AHL_D', 'AHL_E', 'AHPI', 'AHT', 'AHT_D', 'AHT_F', 'AHT_G', 'AHT_H', 'AHT_I', 'AI', 'AIC', 'AIEQ', 'AIF', 'AIG-WS', 'AIG',
      'AIG_A', 'AIH', 'AIHS', 'AIIQ', 'AIKI', 'AIM', 'AIMC', 'AIN', 'AINC', 'AINV', 'AIO', 'AIQ', 'AIR', 'AIRC', 'AIRG', 'AIRI', 'AIRT', 'AIRTP', 'AIRTW', 'AIT', 'AIV', 'AIW', 'AIZ', 'AIZN', 'AIZP',
      'AJAX-U', 'AJAX-WS', 'AJAX', 'AJG', 'AJRD', 'AJX', 'AJXA', 'AKAM', 'AKBA', 'AKER', 'AKO-A', 'AKO-B', 'AKR', 'AKRO', 'AKTS', 'AKTX', 'AKU', 'AKUS', 'AL', 'ALAC', 'ALACR', 'ALACW', 'ALB',
      'ALBO', 'ALC', 'ALCO', 'ALDX', 'ALE', 'ALEC', 'ALEX', 'ALG', 'ALGM', 'ALGN', 'ALGS', 'ALGT', 'ALIM', 'ALIN_A', 'ALIN_B', 'ALIN_E', 'ALJJ', 'ALK', 'ALKS', 'ALL', 'ALLE', 'ALLK', 'ALLO',
      'ALLT', 'ALLY', 'ALLY_A', 'ALL_B', 'ALL_G', 'ALL_H', 'ALL_I', 'ALNA', 'ALNY', 'ALOT', 'ALPN', 'ALP_Q', 'ALRM', 'ALRN', 'ALRS', 'ALSK', 'ALSN', 'ALT', 'ALTA', 'ALTG-WS', 'ALTG', 'ALTL',
      'ALTM', 'ALTR', 'ALTUU', 'ALTY', 'ALUS-WS', 'ALUS', 'ALV', 'ALVR', 'ALX', 'ALXN', 'ALXO', 'ALYA', 'AL_A', 'AM', 'AMAL', 'AMAT', 'AMBA', 'AMBC-WS', 'AMBC', 'AMBO', 'AMC', 'AMCA', 'AMCI',
      'AMCIU', 'AMCIW', 'AMCR', 'AMCX', 'AMD', 'AME', 'AMED', 'AMEH', 'AMG', 'AMGN', 'AMH', 'AMHC', 'AMHCU', 'AMHCW', 'AMH_D', 'AMH_E', 'AMH_F', 'AMH_G', 'AMH_H', 'AMK', 'AMKR', 'AMN', 'AMNA',
      'AMNB', 'AMND', 'AMOM', 'AMOT', 'AMOV', 'AMP', 'AMPE', 'AMPH', 'AMPY', 'AMRB', 'AMRC', 'AMRK', 'AMRN', 'AMRS', 'AMRX', 'AMS', 'AMSC', 'AMSF', 'AMST', 'AMSWA', 'AMT', 'AMTB', 'AMTBB', 'AMTI',
      'AMTR', 'AMTX', 'AMUB', 'AMWD', 'AMWL', 'AMX', 'AMYT', 'AMZA', 'AMZN', 'AN', 'ANAB', 'ANAT', 'ANCN', 'ANDA', 'ANDAR', 'ANDAW', 'ANDE', 'ANET', 'ANEW', 'ANF', 'ANGI', 'ANGO', 'ANH', 'ANH_A',
      'ANH_B', 'ANH_C', 'ANIK', 'ANIP', 'ANIX', 'ANNX', 'ANPC', 'ANSS', 'ANTE', 'ANTM', 'ANVS', 'ANY', 'AOD', 'AON', 'AONE-U', 'AONE-WS', 'AONE', 'AOS', 'AOSL', 'AOUT', 'AP-WS', 'AP', 'APA',
      'APAM', 'APD', 'APDN', 'APEI', 'APEN', 'APG', 'APH', 'APHA', 'API', 'APLE', 'APLS', 'APLT', 'APM', 'APO', 'APOG', 'APOP', 'APOPW', 'APO_A', 'APO_B', 'APPF', 'APPN', 'APPS', 'APRE', 'APRN',
      'APSG-U', 'APSG-WS', 'APSG', 'APT', 'APTO', 'APTS', 'APTV', 'APTV_A', 'APTX', 'APVO', 'APWC', 'APXT', 'APXTU', 'APXTW', 'APYX', 'AQB', 'AQMS', 'AQN', 'AQNA', 'AQNB', 'AQST', 'AQUA', 'AR',
      'ARA', 'ARAV', 'ARAY', 'ARB', 'ARBGU', 'ARC', 'ARCB', 'ARCC', 'ARCE', 'ARCH', 'ARCM', 'ARCO', 'ARCT', 'ARD', 'ARDC', 'ARDS', 'ARDX', 'ARE', 'AREC', 'ARES', 'ARES_A', 'ARGD', 'ARGO', 'ARGO_A',
      'ARGX', 'ARI', 'ARKF', 'ARKG', 'ARKK', 'ARKO', 'ARKOW', 'ARKQ', 'ARKR', 'ARKW', 'ARL', 'ARLO', 'ARLP', 'ARMK', 'ARMP', 'ARMR', 'ARNA', 'ARNC', 'AROC', 'AROW', 'ARPO', 'ARQT', 'ARR', 'ARRY',
      'ARR_C', 'ARTL', 'ARTLW', 'ARTNA', 'ARTW', 'ARVN', 'ARW', 'ARWR', 'ARYA', 'ASA', 'ASAN', 'ASAQ-U', 'ASAQ-WS', 'ASAQ', 'ASB', 'ASB_C', 'ASB_D', 'ASB_E', 'ASB_F', 'ASC', 'ASET', 'ASG', 'ASGI',
      'ASGN', 'ASH', 'ASHX', 'ASIX', 'ASLE', 'ASLEW', 'ASLN', 'ASM', 'ASMB', 'ASML', 'ASND', 'ASO', 'ASPL-U', 'ASPL-WS', 'ASPL', 'ASPN', 'ASPS', 'ASPU', 'ASR', 'ASRT', 'ASRV', 'ASRVP', 'ASTC',
      'ASTE', 'ASUR', 'ASX', 'ASYS', 'AT', 'ATA-U', 'ATAC-U', 'ATAC-WS', 'ATAC', 'ATAX', 'ATCO', 'ATCO_D', 'ATCO_E', 'ATCO_G', 'ATCO_H', 'ATCO_I', 'ATCX', 'ATEC', 'ATEN', 'ATEX', 'ATGE', 'ATH',
      'ATHA', 'ATHE', 'ATHM', 'ATHX', 'ATH_A', 'ATH_B', 'ATH_C', 'ATH_D', 'ATI', 'ATIF', 'ATKR', 'ATLC', 'ATLO', 'ATNF', 'ATNFW', 'ATNI', 'ATNM', 'ATNX', 'ATO', 'ATOM', 'ATOS', 'ATR', 'ATRA',
      'ATRC', 'ATRI', 'ATRO', 'ATRS', 'ATSG', 'ATTO', 'ATUS', 'ATV', 'ATVI', 'ATXI', 'AU', 'AUB', 'AUBAP', 'AUBN', 'AUDC', 'AUGZ', 'AUMN', 'AUPH', 'AUSF', 'AUTL', 'AUTO', 'AUVI', 'AUY', 'AVA',
      'AVAL', 'AVAN-U', 'AVAN-WS', 'AVAN', 'AVAV', 'AVB', 'AVCO', 'AVCT', 'AVCTW', 'AVD', 'AVDE', 'AVDL', 'AVDV', 'AVEM', 'AVEO', 'AVGO', 'AVGOP', 'AVGR', 'AVID', 'AVIG', 'AVIR', 'AVK', 'AVLR',
      'AVMU', 'AVNS', 'AVNT', 'AVNW', 'AVO', 'AVRO', 'AVSF', 'AVT', 'AVTR', 'AVTR_A', 'AVUS', 'AVUV', 'AVXL', 'AVY', 'AVYA', 'AWAY', 'AWF', 'AWH', 'AWI', 'AWK', 'AWP', 'AWR', 'AWRE', 'AWTM', 'AWX',
      'AX', 'AXAS', 'AXDX', 'AXGN', 'AXL', 'AXLA', 'AXNX', 'AXO', 'AXP', 'AXR', 'AXS', 'AXSM', 'AXS_E', 'AXTA', 'AXTI', 'AXU', 'AY', 'AYI', 'AYLA', 'AYRO', 'AYTU', 'AYX', 'AZAA', 'AZAL', 'AZAO',
      'AZBA', 'AZBL', 'AZBO', 'AZEK', 'AZN', 'AZO', 'AZPN', 'AZRE', 'AZRX', 'AZUL', 'AZYO', 'AZZ', 'B', 'BA', 'BABA', 'BAC', 'BAC_A', 'BAC_B', 'BAC_C', 'BAC_E', 'BAC_K', 'BAC_L', 'BAC_M', 'BAC_N',
      'BAC_O', 'BAF', 'BAH', 'BAK', 'BAL', 'BALY', 'BAM', 'BAMH', 'BAMI', 'BANC', 'BANC_D', 'BANC_E', 'BAND', 'BANF', 'BANFP', 'BANR', 'BANX', 'BAP', 'BAR', 'BASI', 'BATL', 'BATRA', 'BATRK',
      'BATT', 'BAUG', 'BAX', 'BB', 'BBAR', 'BBAX', 'BBBY', 'BBC', 'BBCA', 'BBCP', 'BBD', 'BBDC', 'BBDO', 'BBEU', 'BBF', 'BBGI', 'BBI', 'BBIG', 'BBIN', 'BBIO', 'BBJP', 'BBK', 'BBL', 'BBMC', 'BBN',
      'BBP', 'BBQ', 'BBRE', 'BBSC', 'BBSI', 'BBU', 'BBVA', 'BBW', 'BBY', 'BC', 'BCAB', 'BCAT', 'BCBP', 'BCC', 'BCD', 'BCDA', 'BCDAW', 'BCE', 'BCEI', 'BCEL', 'BCH', 'BCI', 'BCLI', 'BCML', 'BCO',
      'BCOR', 'BCOV', 'BCOW', 'BCPC', 'BCRX', 'BCS', 'BCSF', 'BCTG', 'BCV', 'BCX', 'BCYC', 'BC_A', 'BC_B', 'BC_C', 'BDC', 'BDCX', 'BDCZ', 'BDGE', 'BDJ', 'BDL', 'BDN', 'BDR', 'BDRY', 'BDSI', 'BDSX',
      'BDTX', 'BDX', 'BDXB', 'BE', 'BEAM', 'BEAT', 'BECN', 'BEDU', 'BEEM', 'BEEMW', 'BEKE', 'BELFA', 'BELFB', 'BEN', 'BEP', 'BEPC', 'BEP_A', 'BERY', 'BEST', 'BETZ', 'BF-A', 'BF-B', 'BFAM', 'BFC',
      'BFEB', 'BFI', 'BFIIW', 'BFIN', 'BFIT', 'BFK', 'BFRA', 'BFS', 'BFST', 'BFS_D', 'BFS_E', 'BFT-U', 'BFT-WS', 'BFT', 'BFTR', 'BFY', 'BFZ', 'BG', 'BGB', 'BGCP', 'BGFV', 'BGH', 'BGI', 'BGIO',
      'BGNE', 'BGR', 'BGRN', 'BGS', 'BGSF', 'BGT', 'BGX', 'BGY', 'BH-A', 'BH', 'BHAT', 'BHB', 'BHC', 'BHE', 'BHF', 'BHFAL', 'BHFAN', 'BHFAO', 'BHFAP', 'BHK', 'BHLB', 'BHP', 'BHR', 'BHR_B', 'BHR_D',
      'BHSE', 'BHSEU', 'BHSEW', 'BHTG', 'BHV', 'BHVN', 'BIBL', 'BIDU', 'BIF', 'BIG', 'BIGC', 'BIIB', 'BILI', 'BILL', 'BILS', 'BIMI', 'BIO', 'BIOC', 'BIOL', 'BIOX', 'BIP', 'BIPC', 'BIP_A', 'BIT',
      'BIVI', 'BJ', 'BJAN', 'BJK', 'BJRI', 'BJUL', 'BK', 'BKAG', 'BKCC', 'BKD', 'BKE', 'BKEM', 'BKEP', 'BKEPP', 'BKH', 'BKHY', 'BKI', 'BKIE', 'BKLC', 'BKMC', 'BKN', 'BKNG', 'BKR', 'BKSB', 'BKSC',
      'BKSE', 'BKT', 'BKTI', 'BKU', 'BKYI', 'BL', 'BLBD', 'BLCM', 'BLCN', 'BLCT', 'BLD', 'BLDG', 'BLDP', 'BLDR', 'BLE', 'BLES', 'BLFS', 'BLHY', 'BLI', 'BLIN', 'BLK', 'BLKB', 'BLL', 'BLMN', 'BLNK',
      'BLNKW', 'BLOK', 'BLPH', 'BLRX', 'BLSA', 'BLU', 'BLUE', 'BLUWU', 'BLW', 'BLX', 'BMA', 'BMCH', 'BME', 'BMED', 'BMEZ', 'BMI', 'BMLP', 'BML_G', 'BML_H', 'BML_J', 'BML_L', 'BMO', 'BMRA', 'BMRC',
      'BMRN', 'BMTC', 'BMY-R', 'BMY', 'BNDC', 'BNDW', 'BNE', 'BNED', 'BNFT', 'BNGO', 'BNGOW', 'BNKD', 'BNKU', 'BNL', 'BNR', 'BNS', 'BNSO', 'BNTC', 'BNTX', 'BNY', 'BOAC-U', 'BOAC-WS', 'BOAC', 'BOCH',
      'BOCT', 'BOE', 'BOH', 'BOKF', 'BOKFL', 'BOMN', 'BOOM', 'BOOT', 'BORR', 'BOSC', 'BOSS', 'BOTJ', 'BOTZ', 'BOUT', 'BOWX', 'BOWXU', 'BOWXW', 'BOX', 'BOXL', 'BP', 'BPFH', 'BPMC', 'BPMP', 'BPOP',
      'BPOPM', 'BPOPN', 'BPRN', 'BPT', 'BPTH', 'BPY', 'BPYPN', 'BPYPO', 'BPYPP', 'BPYU', 'BPYUP', 'BQ', 'BR', 'BRBR', 'BRBS', 'BRC', 'BREZ', 'BREZR', 'BREZW', 'BRFS', 'BRG', 'BRG_A', 'BRG_C', 'BRID',
      'BRK-A', 'BRK-B', 'BRKL', 'BRKR', 'BRKS', 'BRLI', 'BRLIR', 'BRLIU', 'BRLIW', 'BRMK-WS', 'BRMK', 'BRN', 'BRO', 'BROG', 'BROGW', 'BRP', 'BRPA', 'BRPAR', 'BRPAW', 'BRQS', 'BRT', 'BRX', 'BRY',
      'BSA', 'BSAC', 'BSBK', 'BSBR', 'BSCR', 'BSCU', 'BSD', 'BSE', 'BSET', 'BSGM', 'BSIG', 'BSJS', 'BSL', 'BSM', 'BSML', 'BSMM', 'BSMN', 'BSMO', 'BSMP', 'BSMQ', 'BSMR', 'BSMS', 'BSMT', 'BSMU',
      'BSMX', 'BSN-U', 'BSN-WS', 'BSN', 'BSQR', 'BSRR', 'BST', 'BSTZ', 'BSVN', 'BSX', 'BSX_A', 'BSY', 'BTA', 'BTAI', 'BTAQ', 'BTAQU', 'BTAQW', 'BTBT', 'BTEC', 'BTEK', 'BTG', 'BTI', 'BTN', 'BTO',
      'BTT', 'BTU', 'BTWN', 'BTWNU', 'BTWNW', 'BTZ', 'BUD', 'BUFF', 'BUFR', 'BUG', 'BUI', 'BUL', 'BUR', 'BURL', 'BUSE', 'BV', 'BVH', 'BVN', 'BVXV', 'BW', 'BWA', 'BWAC', 'BWACU', 'BWACW', 'BWAY',
      'BWB', 'BWEN', 'BWFG', 'BWG', 'BWL-A', 'BWMX', 'BWXT', 'BX', 'BXC', 'BXG', 'BXMT', 'BXMX', 'BXP', 'BXP_B', 'BXRX', 'BXS', 'BXS_A', 'BY', 'BYD', 'BYFC', 'BYM', 'BYND', 'BYSI', 'BZH', 'BZM',
      'BZUN', 'C', 'CAAP', 'CAAS', 'CABA', 'CABO', 'CAC', 'CACC', 'CACG', 'CACI', 'CADE', 'CAE', 'CAF', 'CAG', 'CAH', 'CAI', 'CAI_A', 'CAI_B', 'CAJ', 'CAKE', 'CAL', 'CALA', 'CALB', 'CALF', 'CALM',
      'CALT', 'CALX', 'CAMP', 'CAMT', 'CAN', 'CANF', 'CANG', 'CAP-U', 'CAPAU', 'CAPAW', 'CAPL', 'CAPR', 'CAR', 'CARA', 'CARE', 'CARG', 'CARR', 'CARS', 'CARV', 'CAS-U', 'CASA', 'CASH', 'CASI', 'CASS',
      'CASY', 'CAT', 'CATB', 'CATC', 'CATH', 'CATM', 'CATO', 'CATY', 'CB', 'CBAH-U', 'CBAN', 'CBAT', 'CBAY', 'CBB', 'CBB_B', 'CBD', 'CBFV', 'CBH', 'CBIO', 'CBLI', 'CBLS', 'CBMB', 'CBMG', 'CBNK',
      'CBOE', 'CBPO', 'CBRE', 'CBRL', 'CBSE', 'CBSH', 'CBT', 'CBTX', 'CBU', 'CBZ', 'CC', 'CCAC-U', 'CCAC-WS', 'CCAC', 'CCAP', 'CCB', 'CCBG', 'CCC', 'CCCC', 'CCD', 'CCEP', 'CCF', 'CCI', 'CCIV-U',
      'CCIV-WS', 'CCIV', 'CCJ', 'CCK', 'CCL', 'CCLP', 'CCM', 'CCMP', 'CCNC', 'CCNE', 'CCNEP', 'CCO', 'CCOI', 'CCON', 'CCOR', 'CCRC', 'CCRN', 'CCRV', 'CCS', 'CCU', 'CCV-U', 'CCX-U', 'CCX-WS', 'CCX',
      'CCXI', 'CD', 'CDAK', 'CDAY', 'CDC', 'CDE', 'CDEV', 'CDK', 'CDL', 'CDLX', 'CDMO', 'CDMOP', 'CDNA', 'CDNS', 'CDOR', 'CDR', 'CDR_B', 'CDR_C', 'CDTX', 'CDW', 'CDXC', 'CDXS', 'CDZI', 'CE', 'CEA',
      'CECE', 'CEE', 'CEF', 'CEFA', 'CEFD', 'CEFS', 'CEI', 'CEIX', 'CEL', 'CELC', 'CELG-R', 'CELH', 'CELP', 'CEM', 'CEMB', 'CEMI', 'CEN', 'CENT', 'CENTA', 'CENX', 'CEO', 'CEPU', 'CEQP', 'CEQP_',
      'CERC', 'CERE', 'CEREW', 'CERN', 'CERS', 'CERT', 'CET', 'CETX', 'CETXW', 'CEV', 'CEVA', 'CEY', 'CF', 'CFA', 'CFACU', 'CFB', 'CFBI', 'CFBK', 'CFCV', 'CFFI', 'CFFN', 'CFG', 'CFG_D', 'CFG_E',
      'CFII', 'CFIIU', 'CFIIW', 'CFIVU', 'CFMS', 'CFO', 'CFR', 'CFRX', 'CFR_B', 'CFX', 'CFXA', 'CG', 'CGA', 'CGBD', 'CGC', 'CGEN', 'CGIX', 'CGNX', 'CGO', 'CGRO', 'CGROU', 'CGROW', 'CHA', 'CHAD',
      'CHAQ-U', 'CHAQ-WS', 'CHAQ', 'CHB', 'CHCI', 'CHCO', 'CHCT', 'CHD', 'CHDN', 'CHE', 'CHEF', 'CHEK', 'CHEKZ', 'CHFS', 'CHFW-U', 'CHGG', 'CHGX', 'CHH', 'CHI', 'CHIC', 'CHIH', 'CHIK', 'CHIL',
      'CHIR', 'CHIS', 'CHIU', 'CHKP', 'CHL', 'CHMA', 'CHMG', 'CHMI', 'CHMI_A', 'CHMI_B', 'CHN', 'CHNA', 'CHNG', 'CHNGU', 'CHNR', 'CHPM', 'CHPMW', 'CHRA', 'CHRS', 'CHRW', 'CHS', 'CHSCL', 'CHSCM',
      'CHSCN', 'CHSCO', 'CHSCP', 'CHT', 'CHTR', 'CHU', 'CHUY', 'CHW', 'CHWY', 'CHX', 'CHY', 'CI', 'CIA', 'CIB', 'CIBR', 'CID', 'CIDM', 'CIEN', 'CIF', 'CIG-C', 'CIG', 'CIGI', 'CIH', 'CII', 'CIIC',
      'CIICU', 'CIICW', 'CIK', 'CIL', 'CIM', 'CIM_A', 'CIM_B', 'CIM_C', 'CIM_D', 'CINF', 'CINR', 'CIO', 'CIO_A', 'CIR', 'CIT', 'CIT_B', 'CIVB', 'CIX', 'CIXX', 'CIZ', 'CIZN', 'CJJD', 'CKH', 'CKPT',
      'CKX', 'CL', 'CLA-U', 'CLA-WS', 'CLA', 'CLAR', 'CLB', 'CLBK', 'CLBS', 'CLCT', 'CLDB', 'CLDR', 'CLDT', 'CLDX', 'CLEU', 'CLF', 'CLFD', 'CLGN', 'CLGX', 'CLH', 'CLI', 'CLII-U', 'CLII-WS', 'CLII',
      'CLIR', 'CLIX', 'CLLS', 'CLM', 'CLMT', 'CLNC', 'CLNE', 'CLNY', 'CLNY_G', 'CLNY_H', 'CLNY_I', 'CLNY_J', 'CLOU', 'CLPR', 'CLPS', 'CLPT', 'CLR', 'CLRB', 'CLRBZ', 'CLRG', 'CLRO', 'CLS', 'CLSD',
      'CLSK', 'CLSN', 'CLTL', 'CLVR', 'CLVRW', 'CLVS', 'CLW', 'CLWT', 'CLX', 'CLXT', 'CM', 'CMA', 'CMBM', 'CMC', 'CMCL', 'CMCM', 'CMCO', 'CMCSA', 'CMCT', 'CMD', 'CMDY', 'CME', 'CMFNL', 'CMG', 'CMI',
      'CMLF', 'CMLFU', 'CMLFW', 'CMLS', 'CMO', 'CMO_E', 'CMP', 'CMPI', 'CMPR', 'CMPS', 'CMRE', 'CMRE_B', 'CMRE_C', 'CMRE_D', 'CMRE_E', 'CMRX', 'CMS', 'CMSA', 'CMSC', 'CMSD', 'CMS_B', 'CMT', 'CMTL',
      'CMU', 'CNA', 'CNBKA', 'CNBS', 'CNC', 'CNCE', 'CNCR', 'CND-U', 'CNDT', 'CNET', 'CNF', 'CNFR', 'CNFRL', 'CNHI', 'CNI', 'CNK', 'CNMD', 'CNNB', 'CNNE', 'CNO', 'CNOB', 'CNO_A', 'CNP', 'CNP_B',
      'CNQ', 'CNR', 'CNRG', 'CNS', 'CNSL', 'CNSP', 'CNST', 'CNTG', 'CNTY', 'CNX', 'CNXC', 'CNXN', 'CNYA', 'CO', 'COCP', 'CODA', 'CODI', 'CODI_A', 'CODI_B', 'CODI_C', 'CODX', 'COE', 'COF', 'COFS',
      'COF_G', 'COF_H', 'COF_I', 'COF_J', 'COF_K', 'COG', 'COGT', 'COHN', 'COHR', 'COHU', 'COKE', 'COLB', 'COLD', 'COLL', 'COLM', 'COM', 'COMB', 'COMM', 'CONE', 'CONN', 'CONX', 'CONXU', 'CONXW',
      'COO', 'COOLU', 'COOP', 'COP', 'COR', 'CORE', 'CORR', 'CORR_A', 'CORT', 'COST', 'COTY', 'COUP', 'COWN', 'COWNL', 'COWNZ', 'COWZ', 'CP', 'CPA', 'CPAH', 'CPB', 'CPE', 'CPF', 'CPG', 'CPHI',
      'CPIX', 'CPK', 'CPLG', 'CPLP', 'CPRI', 'CPRT', 'CPRX', 'CPS', 'CPSH', 'CPSI', 'CPSR-U', 'CPSR-WS', 'CPSR', 'CPSS', 'CPST', 'CPT', 'CPTA', 'CPTAG', 'CPTAL', 'CPZ', 'CQP', 'CR', 'CRAI', 'CRAK',
      'CRBP', 'CRC', 'CRD-A', 'CRD-B', 'CRDF', 'CREE', 'CREG', 'CRESY', 'CREX', 'CREXW', 'CRF', 'CRH', 'CRHC-U', 'CRHC-WS', 'CRHC', 'CRHM', 'CRI', 'CRIS', 'CRK', 'CRL', 'CRM', 'CRMD', 'CRMT', 'CRNC',
      'CRNT', 'CRNX', 'CRON', 'CROX', 'CRS', 'CRSA', 'CRSAW', 'CRSP', 'CRSR', 'CRT', 'CRTD', 'CRTDW', 'CRTO', 'CRTX', 'CRUS', 'CRVL', 'CRVS', 'CRWD', 'CRWS', 'CRY', 'CS', 'CSB', 'CSBR', 'CSCO',
      'CSCW', 'CSF', 'CSGP', 'CSGS', 'CSII', 'CSIQ', 'CSL', 'CSLT', 'CSML', 'CSOD', 'CSPI', 'CSPR', 'CSQ', 'CSR', 'CSR_C', 'CSSE', 'CSSEN', 'CSSEP', 'CSTE', 'CSTL', 'CSTM', 'CSTR', 'CSU', 'CSV',
      'CSWC', 'CSWCL', 'CSWI', 'CSX', 'CTAA', 'CTAC-U', 'CTAC-WS', 'CTAC', 'CTAQU', 'CTAS', 'CTA_A', 'CTA_B', 'CTB', 'CTBB', 'CTBI', 'CTDD', 'CTEC', 'CTEK', 'CTG', 'CTHR', 'CTIB', 'CTIC', 'CTK',
      'CTLT', 'CTMX', 'CTO', 'CTR', 'CTRA', 'CTRE', 'CTRM', 'CTRN', 'CTS', 'CTSH', 'CTSO', 'CTT', 'CTVA', 'CTXR', 'CTXRW', 'CTXS', 'CUB', 'CUBA', 'CUBB', 'CUBE', 'CUBI', 'CUBI_C', 'CUBI_D', 'CUBI_E',
      'CUBI_F', 'CUE', 'CUK', 'CULP', 'CURI', 'CURIW', 'CURO', 'CUTR', 'CUZ', 'CVA', 'CVAC', 'CVBF', 'CVCO', 'CVCY', 'CVE', 'CVEO', 'CVET', 'CVGI', 'CVGW', 'CVI', 'CVLB', 'CVLG', 'CVLT', 'CVLY',
      'CVM', 'CVNA', 'CVR', 'CVS', 'CVU', 'CVV', 'CVX', 'CW', 'CWBC', 'CWBR', 'CWCO', 'CWEB', 'CWEN-A', 'CWEN', 'CWH', 'CWK', 'CWS', 'CWST', 'CWT', 'CX', 'CXDC', 'CXDO', 'CXE', 'CXH', 'CXO', 'CXP',
      'CXSE', 'CXW', 'CYAD', 'CYAN', 'CYBE', 'CYBR', 'CYCC', 'CYCCP', 'CYCN', 'CYD', 'CYH', 'CYRN', 'CYRX', 'CYTH', 'CYTHW', 'CYTK', 'CZNC', 'CZR', 'CZWI', 'CZZ', 'C_J', 'C_K', 'C_N', 'C_S', 'D',
      'DAC', 'DADA', 'DAIO', 'DAKT', 'DAL', 'DALI', 'DALT', 'DAN', 'DAO', 'DAR', 'DARE', 'DASH', 'DAVA', 'DAX', 'DB', 'DBD', 'DBDR', 'DBDRU', 'DBDRW', 'DBEH', 'DBI', 'DBL', 'DBLV', 'DBMF', 'DBOC',
      'DBVT', 'DBX', 'DCBO', 'DCF', 'DCI', 'DCO', 'DCOM', 'DCOMP', 'DCP', 'DCPH', 'DCP_B', 'DCP_C', 'DCRB', 'DCRBU', 'DCRBW', 'DCT', 'DCTH', 'DCUE', 'DD', 'DDD', 'DDF', 'DDIV', 'DDLS', 'DDMXU',
      'DDOG', 'DDS', 'DDT', 'DDWM', 'DE', 'DEA', 'DECK', 'DEED', 'DEEF', 'DEEP', 'DEFA', 'DEH-U', 'DEH-WS', 'DEH', 'DEI', 'DELL', 'DEMZ', 'DEN', 'DENN', 'DEO', 'DESP', 'DEUS', 'DEX', 'DFAE', 'DFAI',
      'DFAU', 'DFEN', 'DFFN', 'DFHT', 'DFHTU', 'DFHTW', 'DFIN', 'DFND', 'DFNL', 'DFNS-WS', 'DFNS', 'DFP', 'DFPH', 'DFPHW', 'DFS', 'DG', 'DGICA', 'DGICB', 'DGII', 'DGLY', 'DGNR-U', 'DGNR-WS', 'DGNR',
      'DGNS', 'DGX', 'DHC', 'DHCNI', 'DHCNL', 'DHF', 'DHI', 'DHIL', 'DHR', 'DHR_A', 'DHR_B', 'DHT', 'DHX', 'DHY', 'DIAL', 'DIAX', 'DIN', 'DINT', 'DIOD', 'DIS', 'DISCA', 'DISCB', 'DISCK', 'DISH',
      'DIT', 'DIVA', 'DIVB', 'DIVO', 'DJCB', 'DJCO', 'DJD', 'DJUL', 'DJUN', 'DK', 'DKL', 'DKNG', 'DKS', 'DL', 'DLA', 'DLB', 'DLHC', 'DLNG', 'DLNG_A', 'DLNG_B', 'DLPN', 'DLR', 'DLR_C', 'DLR_J',
      'DLR_K', 'DLR_L', 'DLTH', 'DLTR', 'DLX', 'DLY', 'DM-WS', 'DM', 'DMAC', 'DMB', 'DMDV', 'DMF', 'DMLP', 'DMO', 'DMRC', 'DMRE', 'DMRI', 'DMRL', 'DMRM', 'DMRS', 'DMS-WS', 'DMS', 'DMTK', 'DMXF',
      'DMYD-U', 'DMYD-WS', 'DMYD', 'DMYI-U', 'DNB', 'DNK', 'DNLI', 'DNMR-WS', 'DNMR', 'DNN', 'DNOW', 'DNP', 'DOC', 'DOCT', 'DOCU', 'DOGZ', 'DOMO', 'DOOO', 'DOOR', 'DORM', 'DOV', 'DOW', 'DOX', 'DOYU',
      'DPG', 'DPST', 'DPW', 'DPZ', 'DQ', 'DRAD', 'DRADP', 'DRD', 'DRE', 'DRH', 'DRH_A', 'DRI', 'DRIO', 'DRIOW', 'DRIV', 'DRNA', 'DRQ', 'DRRX', 'DRSK', 'DRTT', 'DRUA', 'DS', 'DSAC', 'DSACU', 'DSACW',
      'DSE', 'DSEP', 'DSGX', 'DSKE', 'DSKEW', 'DSL', 'DSM', 'DSOC', 'DSPG', 'DSS', 'DSSI', 'DSTL', 'DSTX', 'DSU', 'DSWL', 'DSX', 'DSX_B', 'DS_B', 'DS_C', 'DS_D', 'DT', 'DTB', 'DTE', 'DTEA', 'DTEC',
      'DTF', 'DTIL', 'DTJ', 'DTLA_', 'DTP', 'DTSS', 'DTW', 'DTY', 'DUC', 'DUDE', 'DUK', 'DUKB', 'DUKH', 'DUK_A', 'DUNEU', 'DUO', 'DUOT', 'DURA', 'DUSA', 'DUSL', 'DVA', 'DVAX', 'DVD', 'DVLU', 'DVN',
      'DVOL', 'DWAS', 'DWAW', 'DWEQ', 'DWFI', 'DWIN-U', 'DWLD', 'DWMF', 'DWPP', 'DWSH', 'DWSN', 'DWUS', 'DX', 'DXC', 'DXCM', 'DXF', 'DXPE', 'DXR', 'DXYN', 'DX_B', 'DX_C', 'DY', 'DYAI', 'DYFN',
      'DYHG', 'DYN', 'DYNF', 'DYNT', 'DZSI', 'E', 'EA', 'EAD', 'EAF', 'EAGG', 'EAI', 'EAOA', 'EAOK', 'EAOM', 'EAOR', 'EAR', 'EARN', 'EARS', 'EASG', 'EAST', 'EAT', 'EB', 'EBAY', 'EBAYL', 'EBC', 'EBF',
      'EBIX', 'EBIZ', 'EBLU', 'EBMT', 'EBON', 'EBR', 'EBS', 'EBSB', 'EBTC', 'EC', 'ECC', 'ECCB', 'ECCX', 'ECCY', 'ECF', 'ECF_A', 'ECHO', 'ECL', 'ECLN', 'ECOL', 'ECOM', 'ECOR', 'ECOW', 'ECOZ', 'ECPG',
      'ED', 'EDAP', 'EDD', 'EDF', 'EDI', 'EDIT', 'EDN', 'EDOC', 'EDOW', 'EDRY', 'EDSA', 'EDTK', 'EDTXU', 'EDU', 'EDUC', 'EDUT', 'EEA', 'EEFT', 'EEMD', 'EEMO', 'EEMX', 'EEX', 'EFAS', 'EFAX', 'EFC',
      'EFC_A', 'EFF', 'EFIV', 'EFL', 'EFNL', 'EFOI', 'EFR', 'EFSC', 'EFT', 'EFX', 'EGAN', 'EGBN', 'EGF', 'EGHT', 'EGIS', 'EGLE', 'EGO', 'EGOV', 'EGP', 'EGRX', 'EGY', 'EH', 'EHC', 'EHI', 'EHT',
      'EHTH', 'EIC', 'EIDX', 'EIG', 'EIGI', 'EIGR', 'EIM', 'EINC', 'EIX', 'EJAN', 'EKAR', 'EKSO', 'EL', 'ELA', 'ELAN', 'ELAT', 'ELC', 'ELF', 'ELMD', 'ELOX', 'ELP', 'ELS', 'ELSE', 'ELTK', 'ELVT',
      'ELY', 'ELYS', 'EMAN', 'EMBH', 'EMCF', 'EMD', 'EMDV', 'EME', 'EMF', 'EMGF', 'EMHY', 'EMKR', 'EML', 'EMMF', 'EMN', 'EMNT', 'EMO', 'EMP', 'EMPW-U', 'EMPW-WS', 'EMPW', 'EMQQ', 'EMR', 'EMSG',
      'EMTL', 'EMTY', 'EMX', 'EMXC', 'EMXF', 'ENB', 'ENBA', 'ENBL', 'ENDP', 'ENG', 'ENIA', 'ENIC', 'ENJ', 'ENLC', 'ENLV', 'ENO', 'ENOB', 'ENOR', 'ENPC-U', 'ENPC-WS', 'ENPC', 'ENPH', 'ENR', 'ENR_A',
      'ENS', 'ENSG', 'ENSV', 'ENTA', 'ENTG', 'ENTR', 'ENTX', 'ENTXW', 'ENV', 'ENVA', 'ENX', 'ENZ', 'EOD', 'EOG', 'EOI', 'EOLS', 'EOS', 'EOSE', 'EOSEW', 'EOT', 'EPAC', 'EPAM', 'EPAY', 'EPC', 'EPD',
      'EPIX', 'EPM', 'EPR', 'EPRF', 'EPRT', 'EPR_C', 'EPR_E', 'EPR_G', 'EPSN', 'EPZM', 'EP_C', 'EQ', 'EQBK', 'EQC', 'EQC_D', 'EQD-U', 'EQD-WS', 'EQD', 'EQH', 'EQH_A', 'EQIX', 'EQNR', 'EQOS', 'EQOSW',
      'EQR', 'EQRR', 'EQS', 'EQT', 'EQX', 'ERC', 'ERES', 'ERESU', 'ERESW', 'ERF', 'ERH', 'ERIC', 'ERIE', 'ERII', 'ERJ', 'ERM', 'ERSX', 'ERYP', 'ES', 'ESBA', 'ESBK', 'ESCA', 'ESCR', 'ESE', 'ESEA',
      'ESEB', 'ESGA', 'ESGC', 'ESGD', 'ESGE', 'ESGN', 'ESGR', 'ESGRO', 'ESGRP', 'ESGS', 'ESGU', 'ESGV', 'ESHY', 'ESI', 'ESLT', 'ESML', 'ESNG', 'ESNT', 'ESP', 'ESPO', 'ESPR', 'ESQ', 'ESRT', 'ESS',
      'ESSA', 'ESSC', 'ESSCR', 'ESSCU', 'ESSCW', 'ESTA', 'ESTC', 'ESTE', 'ESXB', 'ET', 'ETAC', 'ETACU', 'ETACW', 'ETB', 'ETG', 'ETH', 'ETHO', 'ETI_', 'ETJ', 'ETM', 'ETN', 'ETNB', 'ETO', 'ETON',
      'ETP_C', 'ETP_D', 'ETP_E', 'ETR', 'ETRN', 'ETSY', 'ETTX', 'ETV', 'ETW', 'ETX', 'ETY', 'EUCR', 'EUCRU', 'EUDV', 'EURN', 'EURZ', 'EUSB', 'EV', 'EVA', 'EVBG', 'EVBN', 'EVC', 'EVER', 'EVF', 'EVFM',
      'EVG', 'EVGN', 'EVH', 'EVI', 'EVK', 'EVLO', 'EVM', 'EVN', 'EVOK', 'EVOL', 'EVOP', 'EVR', 'EVRG', 'EVRI', 'EVT', 'EVTC', 'EVV', 'EVY', 'EW', 'EWBC', 'EWCO', 'EWEB', 'EWGS', 'EWJE', 'EWJV',
      'EWMC', 'EWRE', 'EWSC', 'EWUS', 'EXAS', 'EXC', 'EXD', 'EXEL', 'EXFO', 'EXG', 'EXK', 'EXLS', 'EXN', 'EXP', 'EXPC', 'EXPCU', 'EXPCW', 'EXPD', 'EXPE', 'EXPI', 'EXPO', 'EXPR', 'EXR', 'EXTN',
      'EXTR', 'EYE', 'EYEG', 'EYEN', 'EYES', 'EYESW', 'EYLD', 'EYPT', 'EZPW', 'F', 'FAAR', 'FAF', 'FAII-U', 'FAII-WS', 'FAII', 'FALN', 'FAMI', 'FANG', 'FANH', 'FARM', 'FARO', 'FAST', 'FAT', 'FATBP',
      'FATBW', 'FATE', 'FAX', 'FB', 'FBC', 'FBHS', 'FBIO', 'FBIOP', 'FBIZ', 'FBK', 'FBM', 'FBMS', 'FBNC', 'FBP', 'FBRX', 'FBSS', 'FC', 'FCAC', 'FCACU', 'FCACW', 'FCAL', 'FCAP', 'FCAU', 'FCBC',
      'FCBP', 'FCCO', 'FCCY', 'FCEF', 'FCEL', 'FCF', 'FCFS', 'FCN', 'FCNCA', 'FCNCP', 'FCO', 'FCPT', 'FCRD', 'FCRW', 'FCRZ', 'FCTR', 'FCVT', 'FCX', 'FDBC', 'FDEM', 'FDEU', 'FDEV', 'FDHY', 'FDLO',
      'FDMO', 'FDMT', 'FDNI', 'FDP', 'FDRR', 'FDS', 'FDUS', 'FDUSG', 'FDUSL', 'FDUSZ', 'FDVV', 'FDX', 'FE', 'FEDU', 'FEIM', 'FELE', 'FEN', 'FENC', 'FENG', 'FET', 'FEUL', 'FEVR', 'FEYE', 'FF', 'FFBC',
      'FFBW', 'FFC', 'FFG', 'FFHG', 'FFHL', 'FFIC', 'FFIN', 'FFIU', 'FFIV', 'FFNW', 'FFSG', 'FFTG', 'FFTI', 'FFTY', 'FFWM', 'FGBI', 'FGEN', 'FGF', 'FGFPP', 'FGNA-U', 'FGNA-WS', 'FGNA', 'FHB', 'FHI',
      'FHN', 'FHN_A', 'FHN_B', 'FHN_C', 'FHN_D', 'FHN_E', 'FHTX', 'FI', 'FIBK', 'FIBR', 'FICO', 'FICS', 'FID', 'FIDI', 'FIEE', 'FIHD', 'FIII', 'FIIIU', 'FIIIW', 'FINS', 'FINV', 'FINX', 'FIS', 'FISI',
      'FISK', 'FISR', 'FISV', 'FIT', 'FITB', 'FITBI', 'FITBO', 'FITBP', 'FITE', 'FIV', 'FIVA', 'FIVE', 'FIVG', 'FIVN', 'FIX', 'FIXD', 'FIXX', 'FIZZ', 'FJNK', 'FJUL', 'FJUN', 'FL', 'FLACU', 'FLAU',
      'FLAX', 'FLBL', 'FLBR', 'FLC', 'FLCA', 'FLCB', 'FLCH', 'FLCO', 'FLDM', 'FLDR', 'FLEE', 'FLEH', 'FLEX', 'FLFR', 'FLGB', 'FLGR', 'FLGT', 'FLGV', 'FLHK', 'FLHY', 'FLIA', 'FLIC', 'FLIN', 'FLIR',
      'FLIY', 'FLJH', 'FLJP', 'FLKR', 'FLL', 'FLLA', 'FLLV', 'FLMB', 'FLMI', 'FLMN', 'FLMNW', 'FLMX', 'FLNG', 'FLNT', 'FLO', 'FLOW', 'FLQD', 'FLQE', 'FLQG', 'FLQH', 'FLQL', 'FLQM', 'FLQS', 'FLR',
      'FLRG', 'FLRU', 'FLS', 'FLSA', 'FLSP', 'FLSW', 'FLT', 'FLTW', 'FLUX', 'FLWS', 'FLXN', 'FLXS', 'FLY', 'FLYT', 'FLZA', 'FMAC-U', 'FMAC-WS', 'FMAC', 'FMAO', 'FMBH', 'FMBI', 'FMBIO', 'FMBIP',
      'FMC', 'FMHI', 'FMN', 'FMNB', 'FMO', 'FMS', 'FMTX', 'FMX', 'FN', 'FNB', 'FNB_E', 'FNCB', 'FND', 'FNF', 'FNGD', 'FNGO', 'FNGS', 'FNGU', 'FNGZ', 'FNHC', 'FNKO', 'FNLC', 'FNOV', 'FNV', 'FNWB',
      'FOCS', 'FOCT', 'FOE', 'FOF', 'FOLD', 'FONR', 'FOR', 'FORD', 'FORM', 'FORR', 'FORTY', 'FOSL', 'FOUR', 'FOVL', 'FOX', 'FOXA', 'FOXF', 'FPAC-U', 'FPAY', 'FPEI', 'FPH', 'FPI', 'FPI_B', 'FPRX',
      'FPXE', 'FQAL', 'FR', 'FRA', 'FRAF', 'FRBA', 'FRBK', 'FRC', 'FRC_G', 'FRC_H', 'FRC_I', 'FRC_J', 'FRC_K', 'FRD', 'FRDM', 'FREE', 'FREEW', 'FREQ', 'FRG', 'FRGAP', 'FRGI', 'FRHC', 'FRLG', 'FRLN',
      'FRME', 'FRO', 'FROG', 'FRPH', 'FRPT', 'FRSX', 'FRT', 'FRTA', 'FRT_C', 'FRX-U', 'FSBW', 'FSDC', 'FSEA', 'FSEP', 'FSFG', 'FSI', 'FSK', 'FSKR', 'FSLF', 'FSLR', 'FSLY', 'FSM', 'FSMB', 'FSMD',
      'FSP', 'FSR-WS', 'FSR', 'FSRV', 'FSRVU', 'FSRVW', 'FSS', 'FST-U', 'FST-WS', 'FST', 'FSTR', 'FSTX', 'FSV', 'FT', 'FTAG', 'FTAI', 'FTAI_A', 'FTAI_B', 'FTCH', 'FTCVU', 'FTDR', 'FTEK', 'FTF',
      'FTFT', 'FTHM', 'FTHY', 'FTI', 'FTIV', 'FTIVU', 'FTIVW', 'FTK', 'FTNT', 'FTOC', 'FTOCU', 'FTOCW', 'FTRI', 'FTS', 'FTSI', 'FTV', 'FTV_A', 'FTXD', 'FTXG', 'FTXH', 'FTXL', 'FTXN', 'FTXO', 'FTXR',
      'FUBO', 'FUL', 'FULC', 'FULT', 'FULTP', 'FUMB', 'FUN', 'FUNC', 'FUND', 'FUNL', 'FURY', 'FUSB', 'FUSE-U', 'FUSE-WS', 'FUSE', 'FUSN', 'FUT', 'FUTU', 'FUV', 'FVAL', 'FVAM', 'FVC', 'FVCB', 'FVE',
      'FVRR', 'FWONA', 'FWONK', 'FWP', 'FWRD', 'FXNC', 'F_B', 'F_C', 'G', 'GAB', 'GABC', 'GAB_G', 'GAB_H', 'GAB_J', 'GAB_K', 'GAIA', 'GAIN', 'GAINL', 'GAINM', 'GALT', 'GAM', 'GAMR', 'GAM_B', 'GAN',
      'GASS', 'GATO', 'GATX', 'GAU', 'GB-WS', 'GB', 'GBAB', 'GBCI', 'GBDC', 'GBDV', 'GBGR', 'GBIL', 'GBIO', 'GBL', 'GBLI', 'GBLIL', 'GBLO', 'GBR', 'GBS', 'GBT', 'GBUG', 'GBX', 'GCBC', 'GCI', 'GCMG',
      'GCMGW', 'GCO', 'GCOR', 'GCOW', 'GCP', 'GCV', 'GD', 'GDDY', 'GDEN', 'GDL', 'GDL_C', 'GDMA', 'GDO', 'GDOT', 'GDP', 'GDRX', 'GDS', 'GDV', 'GDVD', 'GDV_G', 'GDV_H', 'GDXD', 'GDXU', 'GDYN',
      'GDYNW', 'GE', 'GECC', 'GECCL', 'GECCM', 'GECCN', 'GEF-B', 'GEF', 'GEG', 'GEL', 'GEM', 'GEN', 'GENC', 'GENE', 'GENY', 'GEO', 'GEOS', 'GER', 'GERM', 'GERN', 'GES', 'GEVO', 'GF', 'GFED', 'GFF',
      'GFI', 'GFL', 'GFLU', 'GFN', 'GFNCP', 'GFNSL', 'GFNSZ', 'GFX-U', 'GGAL', 'GGB', 'GGG', 'GGM', 'GGN', 'GGN_B', 'GGO', 'GGO_A', 'GGT', 'GGT_E', 'GGT_G', 'GGZ', 'GGZ_A', 'GH', 'GHC', 'GHG',
      'GHIV', 'GHIVU', 'GHIVW', 'GHL', 'GHLD', 'GHM', 'GHSI', 'GHVIU', 'GHY', 'GHYB', 'GHYG', 'GIB', 'GIFI', 'GIGB', 'GIGE', 'GIGM', 'GIII', 'GIK-U', 'GIK-WS', 'GIK', 'GIL', 'GILD', 'GILT', 'GIM',
      'GIS', 'GIX-R', 'GIX-U', 'GIX-WS', 'GIX', 'GJH', 'GJO', 'GJP', 'GJT', 'GKOS', 'GL', 'GLAD', 'GLADD', 'GLADL', 'GLAQU', 'GLBS', 'GLBZ', 'GLCN', 'GLDD', 'GLDG', 'GLDM', 'GLEO-U', 'GLEO-WS',
      'GLEO', 'GLG', 'GLIF', 'GLIN', 'GLMD', 'GLNG', 'GLO', 'GLOB', 'GLOG', 'GLOG_A', 'GLOP', 'GLOP_A', 'GLOP_B', 'GLOP_C', 'GLP', 'GLPG', 'GLPI', 'GLP_A', 'GLQ', 'GLRE', 'GLRY', 'GLSI', 'GLT',
      'GLTO', 'GLU', 'GLUU', 'GLU_A', 'GLV', 'GLW', 'GLYC', 'GL_C', 'GM', 'GMAB', 'GMBL', 'GMBLW', 'GMDA', 'GME', 'GMED', 'GMLP', 'GMLPP', 'GMRE', 'GMRE_A', 'GMS', 'GMTA', 'GNAF', 'GNCA', 'GNE',
      'GNE_A', 'GNFT', 'GNK', 'GNL', 'GNLN', 'GNL_A', 'GNL_B', 'GNMK', 'GNOG', 'GNOGW', 'GNOM', 'GNPK-U', 'GNPX', 'GNRC', 'GNRS', 'GNRSU', 'GNRSW', 'GNSS', 'GNT', 'GNTX', 'GNTY', 'GNT_A', 'GNUS',
      'GNW', 'GO', 'GOAC-U', 'GOAC-WS', 'GOAC', 'GOAT', 'GOAU', 'GOCO', 'GOED', 'GOEV', 'GOEVW', 'GOEX', 'GOF', 'GOGL', 'GOGO', 'GOL', 'GOLD', 'GOLF', 'GOOD', 'GOODM', 'GOODN', 'GOOG', 'GOOGL',
      'GOOS', 'GORO', 'GOSS', 'GOVX', 'GOVXW', 'GP', 'GPC', 'GPI', 'GPJA', 'GPK', 'GPL', 'GPM', 'GPMT', 'GPN', 'GPP', 'GPRE', 'GPRK', 'GPRO', 'GPS', 'GPX', 'GRA', 'GRAY', 'GRBK', 'GRC', 'GRCY',
      'GRCYW', 'GRF', 'GRFS', 'GRIF', 'GRIL', 'GRIN', 'GRMN', 'GRN', 'GRNB', 'GRNQ', 'GRNV', 'GRNVR', 'GRNVW', 'GROW', 'GRP-U', 'GRPN', 'GRSV', 'GRSVU', 'GRSVW', 'GRTS', 'GRTX', 'GRUB', 'GRVY',
      'GRWG', 'GRX', 'GS', 'GSAH-U', 'GSAH-WS', 'GSAH', 'GSAT', 'GSBC', 'GSBD', 'GSEU', 'GSEW', 'GSHD', 'GSIE', 'GSIG', 'GSIT', 'GSJY', 'GSK', 'GSKY', 'GSL', 'GSLC', 'GSLD', 'GSL_B', 'GSM', 'GSMG',
      'GSMGW', 'GSPY', 'GSS', 'GSSC', 'GSUM', 'GSV', 'GSX', 'GS_A', 'GS_C', 'GS_D', 'GS_J', 'GS_K', 'GS_N', 'GT', 'GTE', 'GTEC', 'GTES', 'GTH', 'GTHX', 'GTIM', 'GTIP', 'GTLS', 'GTN-A', 'GTN', 'GTO',
      'GTS', 'GTT', 'GTY', 'GTYH', 'GURE', 'GUT', 'GUT_A', 'GUT_C', 'GVA', 'GVIP', 'GVP', 'GWAC', 'GWACW', 'GWB', 'GWGH', 'GWPH', 'GWRE', 'GWRS', 'GWW', 'GXGX', 'GXGXW', 'GXTG', 'GYC', 'H', 'HA',
      'HAACU', 'HACK', 'HAE', 'HAFC', 'HAIL', 'HAIN', 'HAL', 'HALL', 'HALO', 'HAPP', 'HARP', 'HAS', 'HASI', 'HAUZ', 'HAWX', 'HAYN', 'HBAN', 'HBANN', 'HBANO', 'HBB', 'HBCP', 'HBI', 'HBIO', 'HBM',
      'HBMD', 'HBNC', 'HBP', 'HBT', 'HCA', 'HCAP', 'HCAPZ', 'HCARU', 'HCAT', 'HCC', 'HCCI', 'HCDI', 'HCHC', 'HCI', 'HCKT', 'HCM', 'HCSG', 'HCXZ', 'HD', 'HDAW', 'HDB', 'HDEF', 'HDIV', 'HDLB', 'HDMV',
      'HDSN', 'HE', 'HEAR', 'HEC', 'HECCU', 'HECCW', 'HEES', 'HEI-A', 'HEI', 'HELE', 'HEP', 'HEPA', 'HEQ', 'HERD', 'HERO', 'HES', 'HESM', 'HEWC', 'HEWU', 'HEWW', 'HEXO', 'HFC', 'HFEN', 'HFFG',
      'HFRO', 'HFRO_A', 'HFWA', 'HFXI', 'HGBL', 'HGEN', 'HGH', 'HGLB', 'HGSH', 'HGV', 'HHC', 'HHR', 'HI', 'HIBB', 'HIBL', 'HIBS', 'HIE', 'HIFS', 'HIG', 'HIGA-U', 'HIGA-WS', 'HIGA', 'HIG_G', 'HIHO',
      'HII', 'HIL', 'HIMX', 'HIO', 'HIPR', 'HIPS', 'HIW', 'HIX', 'HJLI', 'HJLIW', 'HJPX', 'HKIB', 'HL', 'HLAL', 'HLF', 'HLG', 'HLI', 'HLIO', 'HLIT', 'HLM_', 'HLNE', 'HLT', 'HLX', 'HLXA', 'HMC',
      'HMCOU', 'HMG', 'HMHC', 'HMI', 'HMLP', 'HMLP_A', 'HMN', 'HMNF', 'HMOP', 'HMST', 'HMSY', 'HMTV', 'HMY', 'HNDL', 'HNGR', 'HNI', 'HNNA', 'HNP', 'HNRG', 'HNW', 'HOFT', 'HOFV', 'HOFVW', 'HOG',
      'HOL', 'HOLI', 'HOLUU', 'HOLUW', 'HOLX', 'HOMB', 'HOME', 'HOMZ', 'HON', 'HONE', 'HOOK', 'HOPE', 'HOTH', 'HOV', 'HOVNP', 'HP', 'HPE', 'HPF', 'HPI', 'HPK', 'HPKEW', 'HPP', 'HPQ', 'HPR', 'HPS',
      'HPX-U', 'HPX-WS', 'HPX', 'HQH', 'HQI', 'HQL', 'HQY', 'HR', 'HRB', 'HRC', 'HRI', 'HRL', 'HRMY', 'HROW', 'HRTG', 'HRTX', 'HRZN', 'HSAQ', 'HSBC', 'HSBC_A', 'HSC', 'HSCZ', 'HSDT', 'HSIC', 'HSII',
      'HSKA', 'HSMV', 'HSON', 'HSRT', 'HST', 'HSTM', 'HSTO', 'HSY', 'HT', 'HTA', 'HTAB', 'HTBI', 'HTBK', 'HTBX', 'HTD', 'HTEC', 'HTFA', 'HTGC', 'HTGM', 'HTH', 'HTHT', 'HTIA', 'HTLD', 'HTLF', 'HTLFP',
      'HTOO', 'HTOOW', 'HTPA-U', 'HTRB', 'HTUS', 'HTY', 'HT_C', 'HT_D', 'HT_E', 'HUBB', 'HUBG', 'HUBS', 'HUGE', 'HUIZ', 'HUM', 'HUN', 'HURC', 'HURN', 'HUSA', 'HUSN', 'HUSV', 'HUYA', 'HVBC', 'HVT',
      'HWBK', 'HWC', 'HWCC', 'HWCPL', 'HWCPZ', 'HWKN', 'HWM', 'HX', 'HXL', 'HY', 'HYB', 'HYBB', 'HYDB', 'HYDW', 'HYFM', 'HYGV', 'HYHG', 'HYI', 'HYLB', 'HYLN', 'HYLV', 'HYMC', 'HYMCW', 'HYMCZ',
      'HYRE', 'HYT', 'HYTR', 'HYUP', 'HYXF', 'HYXU', 'HZAC-U', 'HZAC-WS', 'HZAC', 'HZN', 'HZNP', 'HZO', 'HZON-U', 'HZON-WS', 'HZON', 'IAA', 'IAC', 'IACA-U', 'IACA-WS', 'IACA', 'IAE', 'IAF', 'IAG',
      'IAGG', 'IART', 'IAUF', 'IBA', 'IBBJ', 'IBCP', 'IBD', 'IBDR', 'IBDS', 'IBDT', 'IBDU', 'IBDV', 'IBEX', 'IBHA', 'IBHB', 'IBHC', 'IBHD', 'IBHE', 'IBHF', 'IBIO', 'IBKR', 'IBM', 'IBMJ', 'IBMK',
      'IBML', 'IBMM', 'IBMO', 'IBMP', 'IBN', 'IBO', 'IBOC', 'IBP', 'IBTA', 'IBTB', 'IBTD', 'IBTE', 'IBTF', 'IBTG', 'IBTH', 'IBTI', 'IBTJ', 'IBTX', 'ICAD', 'ICBK', 'ICCC', 'ICCH', 'ICD', 'ICE',
      'ICFI', 'ICHR', 'ICL', 'ICLK', 'ICLR', 'ICMB', 'ICON', 'ICOW', 'ICPT', 'ICSH', 'ICUI', 'ICVT', 'ID', 'IDA', 'IDCC', 'IDE', 'IDEV', 'IDEX', 'IDHD', 'IDIV', 'IDLB', 'IDMO', 'IDN', 'IDNA', 'IDRA',
      'IDRV', 'IDT', 'IDXG', 'IDXX', 'IDYA', 'IEA', 'IEAWW', 'IEC', 'IECS', 'IEDI', 'IEFN', 'IEHS', 'IEIH', 'IEME', 'IEP', 'IESC', 'IETC', 'IEX', 'IFF', 'IFFT', 'IFMK', 'IFN', 'IFRA', 'IFRX', 'IFS',
      'IG', 'IGA', 'IGAC', 'IGACU', 'IGACW', 'IGBH', 'IGC', 'IGD', 'IGEB', 'IGHG', 'IGI', 'IGIB', 'IGIC', 'IGICW', 'IGLB', 'IGMS', 'IGR', 'IGRO', 'IGSB', 'IGT', 'IH', 'IHAK', 'IHC', 'IHD', 'IHG',
      'IHIT', 'IHRT', 'IHT', 'IHTA', 'IIAC-U', 'IID', 'IIF', 'IIGD', 'IIGV', 'III', 'IIIIU', 'IIIN', 'IIIV', 'IIM', 'IIN', 'IIPR', 'IIPR_A', 'IIVI', 'IIVIP', 'IJAN', 'IKNX', 'IKT', 'ILMN', 'ILPT',
      'IMAB', 'IMAC', 'IMACW', 'IMAX', 'IMBI', 'IMGN', 'IMH', 'IMKTA', 'IMMP', 'IMMR', 'IMNM', 'IMO', 'IMOM', 'IMOS', 'IMPX-U', 'IMPX-WS', 'IMPX', 'IMRA', 'IMRN', 'IMRNW', 'IMTB', 'IMTE', 'IMTX',
      'IMTXW', 'IMUX', 'IMV', 'IMVT', 'IMXI', 'INAQ', 'INAQU', 'INAQW', 'INBK', 'INBKL', 'INBKZ', 'INBX', 'INCY', 'INDB', 'INDF', 'INDO', 'INDS', 'INFI', 'INFN', 'INFO', 'INFU', 'INFY', 'ING',
      'INGN', 'INGR', 'INM', 'INMB', 'INMD', 'INN', 'INN_D', 'INN_E', 'INO', 'INOD', 'INOV', 'INPX', 'INS', 'INSE', 'INSG', 'INSI', 'INSM', 'INSP', 'INSW', 'INSW_A', 'INT', 'INTC', 'INTG', 'INTT',
      'INTU', 'INTZ', 'INUV', 'INVA', 'INVE', 'INVH', 'INVO', 'INZY', 'IO', 'IONS', 'IOSP', 'IOVA', 'IP', 'IPA', 'IPAR', 'IPAY', 'IPB', 'IPDN', 'IPG', 'IPGP', 'IPHA', 'IPHI', 'IPI', 'IPLDP',
      'IPOC-U', 'IPOC-WS', 'IPOC', 'IPOD-U', 'IPOD-WS', 'IPOD', 'IPOE-U', 'IPOE-WS', 'IPOE', 'IPOF-U', 'IPOF-WS', 'IPOF', 'IPOS', 'IPV-U', 'IPV-WS', 'IPV', 'IPWR', 'IQ', 'IQDG', 'IQI', 'IQIN',
      'IQSI', 'IQSU', 'IQV', 'IR', 'IRBO', 'IRBT', 'IRCP', 'IRDM', 'IRIX', 'IRL', 'IRM', 'IRMD', 'IROQ', 'IRR', 'IRS', 'IRT', 'IRTC', 'IRWD', 'ISBC', 'ISD', 'ISDR', 'ISDX', 'ISEE', 'ISEM', 'ISIG',
      'ISMD', 'ISNS', 'ISR', 'ISRG', 'ISSC', 'ISTR', 'ISZE', 'IT', 'ITAC', 'ITACU', 'ITACW', 'ITCB', 'ITCI', 'ITEQ', 'ITGR', 'ITI', 'ITIC', 'ITMR', 'ITOS', 'ITP', 'ITRG', 'ITRI', 'ITRM', 'ITRN',
      'ITT', 'ITUB', 'ITW', 'IUS', 'IUSS', 'IVA', 'IVAC', 'IVAL', 'IVC', 'IVDG', 'IVES', 'IVH', 'IVLC', 'IVLU', 'IVOL', 'IVR', 'IVRA', 'IVR_A', 'IVR_B', 'IVR_C', 'IVSG', 'IVZ', 'IWFH', 'IX', 'IXSE',
      'IYLD', 'IZEA', 'IZRL', 'J', 'JAAA', 'JACK', 'JAGG', 'JAGX', 'JAKK', 'JAMF', 'JAN', 'JAX', 'JAZZ', 'JBGS', 'JBHT', 'JBK', 'JBL', 'JBLU', 'JBSS', 'JBT', 'JCE', 'JCI', 'JCO', 'JCOM', 'JCPB',
      'JCS', 'JCTCF', 'JCTR', 'JD', 'JDD', 'JDIV', 'JE', 'JEF', 'JELD', 'JEMD', 'JEPI', 'JEQ', 'JETS', 'JFIN', 'JFR', 'JFU', 'JG', 'JGH', 'JGLD', 'JHAA', 'JHB', 'JHCS', 'JHEM', 'JHG', 'JHI', 'JHMA',
      'JHMC', 'JHMD', 'JHME', 'JHMF', 'JHMH', 'JHMI', 'JHML', 'JHMM', 'JHMS', 'JHMT', 'JHMU', 'JHS', 'JHSC', 'JHX', 'JIG', 'JIGB', 'JIH-U', 'JIH-WS', 'JIH', 'JILL', 'JJA', 'JJC', 'JJG', 'JJM', 'JJN',
      'JJP', 'JJS', 'JJSF', 'JJT', 'JJU', 'JKHY', 'JKS', 'JLL', 'JLS', 'JMBS', 'JMIA', 'JMIN', 'JMM', 'JMOM', 'JMP', 'JMPNL', 'JMPNZ', 'JMST', 'JMUB', 'JNCE', 'JNJ', 'JNPR', 'JO', 'JOB', 'JOBS',
      'JOE', 'JOET', 'JOF', 'JOUT', 'JOYY', 'JP', 'JPC', 'JPEM', 'JPHY', 'JPI', 'JPIB', 'JPIN', 'JPM', 'JPMB', 'JPME', 'JPM_C', 'JPM_D', 'JPM_G', 'JPM_H', 'JPM_J', 'JPN', 'JPS', 'JPSE', 'JPST',
      'JPT', 'JPUS', 'JPXN', 'JQC', 'JQUA', 'JRI', 'JRJC', 'JRO', 'JRS', 'JRSH', 'JRVR', 'JSD', 'JSM', 'JSMD', 'JSML', 'JSTC', 'JT', 'JTA', 'JTD', 'JULZ', 'JUPW', 'JUPWW', 'JUST', 'JVA', 'JVAL',
      'JW-A', 'JWN', 'JWS-U', 'JWS-WS', 'JWS', 'JYAC', 'JYNT', 'K', 'KAI', 'KALA', 'KALL', 'KALU', 'KALV', 'KAMN', 'KAPR', 'KAR', 'KARS', 'KB', 'KBAL', 'KBH', 'KBNT', 'KBNTW', 'KBR', 'KBSF', 'KBUY',
      'KBWB', 'KBWD', 'KBWR', 'KBWY', 'KC', 'KCAPL', 'KCCB', 'KCNY', 'KDFI', 'KDMN', 'KDNY', 'KDP', 'KE', 'KELYA', 'KELYB', 'KEMQ', 'KEMX', 'KEN', 'KEP', 'KEQU', 'KERN', 'KERNW', 'KESG', 'KEX',
      'KEY', 'KEYS', 'KEY_I', 'KEY_J', 'KEY_K', 'KF', 'KFRC', 'KFS', 'KFVG', 'KFY', 'KGC', 'KGRN', 'KHC', 'KIDS', 'KIM', 'KIM_L', 'KIM_M', 'KIN', 'KINS', 'KINZU', 'KIO', 'KIQ', 'KIRK', 'KJAN',
      'KJUL', 'KKR', 'KKR_A', 'KKR_B', 'KKR_C', 'KL', 'KLAC', 'KLCD', 'KLDO', 'KLDW', 'KLIC', 'KLR-WS', 'KLR', 'KLXE', 'KMB', 'KMDA', 'KMED', 'KMF', 'KMI', 'KMLM', 'KMPR', 'KMT', 'KMX', 'KN', 'KNDI',
      'KNG', 'KNGS', 'KNL', 'KNOP', 'KNSA', 'KNSL', 'KNTE', 'KNX', 'KO', 'KOCT', 'KOD', 'KODK', 'KOF', 'KOIN', 'KOKU', 'KOMP', 'KOP', 'KOPN', 'KOR', 'KORP', 'KOS', 'KOSS', 'KPTI', 'KR', 'KRA',
      'KRBN', 'KRBP', 'KRC', 'KREF', 'KRG', 'KRKR', 'KRMA', 'KRMD', 'KRNT', 'KRNY', 'KRO', 'KRON', 'KROS', 'KRP', 'KRTX', 'KRUS', 'KRYS', 'KSA', 'KSCD', 'KSM', 'KSMT', 'KSMTU', 'KSMTW', 'KSPN',
      'KSS', 'KSU', 'KSU_', 'KT', 'KTB', 'KTCC', 'KTF', 'KTH', 'KTN', 'KTOS', 'KTRA', 'KURA', 'KURE', 'KVHI', 'KVLE', 'KW', 'KWAC-U', 'KWEB', 'KWR', 'KXIN', 'KYMR', 'KYN', 'KZIA', 'KZR', 'L', 'LAC',
      'LACQ', 'LACQU', 'LACQW', 'LAD', 'LADR', 'LAIX', 'LAKE', 'LAMR', 'LANC', 'LAND', 'LANDO', 'LANDP', 'LARK', 'LASR', 'LATN', 'LATNW', 'LAUR', 'LAWS', 'LAZ', 'LAZR', 'LAZRW', 'LAZY', 'LB', 'LBAI',
      'LBAY', 'LBC', 'LBRDA', 'LBRDK', 'LBRDP', 'LBRT', 'LBTYA', 'LBTYB', 'LBTYK', 'LC', 'LCAP', 'LCAPU', 'LCAPW', 'LCG', 'LCI', 'LCII', 'LCNB', 'LCR', 'LCTX', 'LCUT', 'LCY', 'LCYAU', 'LCYAW',
      'LDEM', 'LDL', 'LDOS', 'LDP', 'LDRS', 'LDSF', 'LE', 'LEA', 'LEAD', 'LEAF', 'LEAP-U', 'LEAP-WS', 'LEAP', 'LECO', 'LEDS', 'LEE', 'LEG', 'LEGH', 'LEGN', 'LEGR', 'LEJU', 'LEN-B', 'LEN', 'LEND',
      'LEO', 'LESL', 'LEU', 'LEVI', 'LEVL', 'LEVLP', 'LFAC', 'LFACW', 'LFC', 'LFEQ', 'LFT', 'LFTR', 'LFTRU', 'LFTRW', 'LFUS', 'LFVN', 'LGF-A', 'LGF-B', 'LGH', 'LGHL', 'LGHLW', 'LGI', 'LGIH',
      'LGL-WS', 'LGL', 'LGND', 'LGOV', 'LGVW-U', 'LGVW-WS', 'LGVW', 'LH', 'LHCG', 'LHX', 'LI', 'LIFE', 'LII', 'LILA', 'LILAK', 'LIN', 'LINC', 'LIND', 'LINX', 'LIQT', 'LITB', 'LITE', 'LIVE', 'LIVK',
      'LIVKW', 'LIVN', 'LIVX', 'LIXT', 'LIXTW', 'LIZI', 'LJPC', 'LKCO', 'LKFN', 'LKQ', 'LL', 'LLIT', 'LLNW', 'LLY', 'LMAT', 'LMB', 'LMFA', 'LMND', 'LMNL', 'LMNR', 'LMNX', 'LMPX', 'LMRK', 'LMRKN',
      'LMRKO', 'LMRKP', 'LMST', 'LMT', 'LNC', 'LND', 'LNDC', 'LNFA-U', 'LNG', 'LNGR', 'LNN', 'LNSR', 'LNT', 'LNTH', 'LOAC', 'LOACR', 'LOACU', 'LOACW', 'LOAN', 'LOB', 'LOCO', 'LODE', 'LOGC', 'LOGI',
      'LOKB-U', 'LOMA', 'LOOP', 'LOPE', 'LORL', 'LOUP', 'LOV', 'LOVE', 'LOW', 'LPCN', 'LPG', 'LPI', 'LPL', 'LPLA', 'LPRO', 'LPSN', 'LPTH', 'LPTX', 'LPX', 'LQDA', 'LQDI', 'LQDT', 'LRCX', 'LRGE',
      'LRMR', 'LRN', 'LRNZ', 'LSAF', 'LSAQ', 'LSAT', 'LSBK', 'LSCC', 'LSF', 'LSI', 'LSLT', 'LSPD', 'LSST', 'LSTR', 'LSXMA', 'LSXMB', 'LSXMK', 'LTBR', 'LTC', 'LTHM', 'LTRN', 'LTRPA', 'LTRPB', 'LTRX',
      'LU', 'LUB', 'LULU', 'LUMN', 'LUMO', 'LUNA', 'LUNG', 'LUV', 'LUXA', 'LUXAU', 'LUXAW', 'LVHD', 'LVHI', 'LVS', 'LW', 'LWAY', 'LX', 'LXEH', 'LXFR', 'LXP', 'LXP_C', 'LXRX', 'LXU', 'LYB', 'LYFE',
      'LYFT', 'LYG', 'LYL', 'LYRA', 'LYTS', 'LYV', 'LZB', 'M', 'MA', 'MAA', 'MAAC', 'MAACU', 'MAACW', 'MAAX', 'MAA_I', 'MAC', 'MACK', 'MACU', 'MACUW', 'MAG', 'MAGA', 'MAGS', 'MAIN', 'MAN', 'MANH',
      'MANT', 'MANU', 'MAR', 'MARA', 'MARK', 'MARPS', 'MAS', 'MASI', 'MASS', 'MAT', 'MATW', 'MATX', 'MAV', 'MAX', 'MAXN', 'MAXR', 'MBBB', 'MBCN', 'MBI', 'MBII', 'MBIN', 'MBINO', 'MBINP', 'MBIO',
      'MBNKP', 'MBOT', 'MBRX', 'MBSD', 'MBT', 'MBUU', 'MBWM', 'MC', 'MCA', 'MCAC', 'MCACR', 'MCACU', 'MCB', 'MCBC', 'MCBS', 'MCC', 'MCD', 'MCEF', 'MCEP', 'MCF', 'MCFE', 'MCFT', 'MCHP', 'MCHX', 'MCI',
      'MCK', 'MCMJ', 'MCMJW', 'MCN', 'MCO', 'MCR', 'MCRB', 'MCRI', 'MCS', 'MCV', 'MCY', 'MD', 'MDB', 'MDC', 'MDCA', 'MDGL', 'MDGS', 'MDGSW', 'MDIA', 'MDJH', 'MDLA', 'MDLQ', 'MDLX', 'MDLY', 'MDLZ',
      'MDNA', 'MDP', 'MDRR', 'MDRRP', 'MDRX', 'MDT', 'MDU', 'MDVL', 'MDWD', 'MDWT', 'MDXG', 'MEAR', 'MEC', 'MED', 'MEDP', 'MEDS', 'MEG', 'MEI', 'MEIP', 'MELI', 'MEN', 'MEOH', 'MERC', 'MER_K', 'MESA',
      'MESO', 'MET', 'METC', 'METX', 'METXW', 'MET_A', 'MET_E', 'MET_F', 'MEXX', 'MFA', 'MFAC-WS', 'MFAC', 'MFA_B', 'MFA_C', 'MFC', 'MFDX', 'MFEM', 'MFG', 'MFGP', 'MFH', 'MFIN', 'MFINL', 'MFL',
      'MFM', 'MFMS', 'MFNC', 'MFO', 'MFT', 'MFUS', 'MFV', 'MG', 'MGA', 'MGEE', 'MGEN', 'MGF', 'MGI', 'MGIC', 'MGLN', 'MGM', 'MGMT', 'MGNI', 'MGNX', 'MGP', 'MGPI', 'MGR', 'MGRB', 'MGRC', 'MGTA',
      'MGTX', 'MGU', 'MGY', 'MGYR', 'MHD', 'MHE', 'MHF', 'MHH', 'MHI', 'MHK', 'MHLA', 'MHLD', 'MHN', 'MHNC', 'MHO', 'MH_A', 'MH_C', 'MH_D', 'MIC', 'MICT', 'MID', 'MIDD', 'MIDF', 'MIE', 'MIG', 'MIK',
      'MILN', 'MIME', 'MIN', 'MIND', 'MINDP', 'MIRM', 'MIST', 'MITK', 'MITO', 'MITT', 'MITT_A', 'MITT_B', 'MITT_C', 'MIXT', 'MIY', 'MJ', 'MJJ', 'MJO', 'MKC-V', 'MKC', 'MKD', 'MKGI', 'MKL', 'MKSI',
      'MKTX', 'MLAB', 'MLAC', 'MLACU', 'MLACW', 'MLCO', 'MLHR', 'MLI', 'MLM', 'MLND', 'MLP', 'MLPB', 'MLPO', 'MLPR', 'MLR', 'MLSS', 'MLVF', 'MMAC', 'MMC', 'MMD', 'MMI', 'MMIN', 'MMIT', 'MMLG',
      'MMLP', 'MMM', 'MMP', 'MMS', 'MMSI', 'MMT', 'MMU', 'MMX', 'MMYT', 'MN', 'MNDO', 'MNKD', 'MNOV', 'MNP', 'MNPR', 'MNR', 'MNRL', 'MNRO', 'MNR_C', 'MNSB', 'MNSO', 'MNST', 'MNTX', 'MO', 'MOD',
      'MODN', 'MOFG', 'MOG-A', 'MOGO', 'MOGU', 'MOH', 'MOHO', 'MOMO', 'MOON', 'MOR', 'MORF', 'MORN', 'MOS', 'MOSY', 'MOTI', 'MOTN', 'MOTNU', 'MOTNW', 'MOTO', 'MOTS', 'MOTV-U', 'MOV', 'MOXC', 'MP-WS',
      'MP', 'MPA', 'MPAA', 'MPB', 'MPC', 'MPLN-WS', 'MPLN', 'MPLX', 'MPV', 'MPW', 'MPWR', 'MPX', 'MQT', 'MQY', 'MRACU', 'MRAM', 'MRBK', 'MRC', 'MRCC', 'MRCCL', 'MRCY', 'MREO', 'MRIN', 'MRK', 'MRKR',
      'MRLN', 'MRM', 'MRNA', 'MRNS', 'MRO', 'MRSN', 'MRTN', 'MRTX', 'MRUS', 'MRVI', 'MRVL', 'MS', 'MSA', 'MSB', 'MSBI', 'MSC', 'MSCI', 'MSD', 'MSEX', 'MSFT', 'MSGE', 'MSGN', 'MSGS', 'MSI', 'MSM',
      'MSN', 'MSON', 'MSOS', 'MSP', 'MSTB', 'MSTR', 'MSVB', 'MSVX', 'MS_A', 'MS_E', 'MS_F', 'MS_I', 'MS_K', 'MS_L', 'MT', 'MTA', 'MTACU', 'MTB', 'MTBC', 'MTBCP', 'MTC', 'MTCH', 'MTCN', 'MTCR', 'MTD',
      'MTDR', 'MTEM', 'MTEX', 'MTG', 'MTGP', 'MTH', 'MTL', 'MTLS', 'MTL_', 'MTN', 'MTNB', 'MTOR', 'MTP', 'MTR', 'MTRN', 'MTRX', 'MTSC', 'MTSI', 'MTSL', 'MTT', 'MTW', 'MTX', 'MTZ', 'MU', 'MUA', 'MUC',
      'MUDSU', 'MUE', 'MUFG', 'MUH', 'MUI', 'MUJ', 'MUR', 'MUS', 'MUSA', 'MUST', 'MUX', 'MVBF', 'MVF', 'MVIS', 'MVO', 'MVRL', 'MVT', 'MWA', 'MWK', 'MX', 'MXC', 'MXDU', 'MXE', 'MXF', 'MXIM', 'MXL',
      'MYC', 'MYD', 'MYE', 'MYF', 'MYFW', 'MYGN', 'MYI', 'MYJ', 'MYN', 'MYO', 'MYOV', 'MYRG', 'MYSZ', 'MYT', 'MZA', 'NAC', 'NACP', 'NAD', 'NAII', 'NAIL', 'NAK', 'NAKD', 'NAN', 'NANR', 'NAOV', 'NAPR',
      'NARI', 'NAT', 'NATH', 'NATI', 'NATR', 'NAV', 'NAVB', 'NAVI', 'NAV_D', 'NAZ', 'NBA-U', 'NBA-WS', 'NBA', 'NBAC', 'NBACR', 'NBACU', 'NBACW', 'NBB', 'NBEV', 'NBH', 'NBHC', 'NBIX', 'NBLX', 'NBN',
      'NBO', 'NBR', 'NBRV', 'NBR_A', 'NBSE', 'NBTB', 'NBTX', 'NBW', 'NBY', 'NC', 'NCA', 'NCB', 'NCBS', 'NCLH', 'NCMI', 'NCNA', 'NCNO', 'NCR', 'NCSM', 'NCTY', 'NCV', 'NCV_A', 'NCZ', 'NCZ_A', 'NDAQ',
      'NDLS', 'NDMO', 'NDP', 'NDRA', 'NDRAW', 'NDSN', 'NEA', 'NEBCU', 'NEE', 'NEE_K', 'NEE_N', 'NEE_O', 'NEE_P', 'NEE_Q', 'NEM', 'NEN', 'NEO', 'NEOG', 'NEON', 'NEOS', 'NEP', 'NEPH', 'NEPT', 'NERD',
      'NERV', 'NES', 'NESR', 'NET', 'NETE', 'NETL', 'NEU', 'NEV', 'NEW', 'NEWA', 'NEWR', 'NEWT', 'NEWTI', 'NEWTL', 'NEX', 'NEXA', 'NEXT', 'NFBK', 'NFE', 'NFG', 'NFH-WS', 'NFH', 'NFJ', 'NFLT', 'NFLX',
      'NG', 'NGA-U', 'NGA-WS', 'NGA', 'NGAC', 'NGACU', 'NGACW', 'NGD', 'NGG', 'NGHC', 'NGHCN', 'NGHCO', 'NGHCP', 'NGHCZ', 'NGL', 'NGL_B', 'NGL_C', 'NGM', 'NGMS', 'NGS', 'NGVC', 'NGVT', 'NH', 'NHA',
      'NHC', 'NHF', 'NHI', 'NHIC', 'NHICU', 'NHICW', 'NHLD', 'NHLDW', 'NHS', 'NHTC', 'NI', 'NICE', 'NICK', 'NID', 'NIE', 'NIFE', 'NIM', 'NINE', 'NIO', 'NIQ', 'NISN', 'NIU', 'NI_B', 'NJAN', 'NJR',
      'NJUL', 'NJV', 'NK', 'NKE', 'NKG', 'NKLA', 'NKSH', 'NKTR', 'NKTX', 'NKX', 'NL', 'NLOK', 'NLS', 'NLSN', 'NLTX', 'NLY', 'NLY_F', 'NLY_G', 'NLY_I', 'NM', 'NMCI', 'NMCO', 'NMFC', 'NMFCL', 'NMI',
      'NMIH', 'NMK_B', 'NMK_C', 'NML', 'NMM', 'NMMC', 'NMMCU', 'NMMCW', 'NMR', 'NMRD', 'NMRK', 'NMS', 'NMT', 'NMTR', 'NMY', 'NMZ', 'NM_G', 'NM_H', 'NNA', 'NNBR', 'NNDM', 'NNI', 'NNN', 'NNN_F',
      'NNOX', 'NNVC', 'NNY', 'NOA', 'NOACU', 'NOAH', 'NOC', 'NOCT', 'NODK', 'NOG', 'NOK', 'NOM', 'NOMD', 'NOV', 'NOVA', 'NOVN', 'NOVS', 'NOVSW', 'NOVT', 'NOW', 'NP', 'NPA', 'NPAUU', 'NPAWW', 'NPK',
      'NPN', 'NPO', 'NPTN', 'NPV', 'NQP', 'NR', 'NRBO', 'NRC', 'NREF', 'NREF_A', 'NRG', 'NRGD', 'NRGU', 'NRGX', 'NRIM', 'NRIX', 'NRK', 'NRO', 'NRP', 'NRT', 'NRUC', 'NRZ', 'NRZ_A', 'NRZ_B', 'NRZ_C',
      'NS', 'NSA', 'NSA_A', 'NSC', 'NSCO-WS', 'NSCO', 'NSH-U', 'NSH-WS', 'NSH', 'NSIT', 'NSL', 'NSP', 'NSPR-WS-B', 'NSPR-WS', 'NSPR', 'NSS', 'NSSC', 'NSTG', 'NSYS', 'NS_A', 'NS_B', 'NS_C', 'NTAP',
      'NTB', 'NTCO', 'NTCT', 'NTEC', 'NTES', 'NTG', 'NTGR', 'NTIC', 'NTIP', 'NTLA', 'NTN', 'NTNX', 'NTP', 'NTR', 'NTRA', 'NTRS', 'NTRSO', 'NTST', 'NTSX', 'NTUS', 'NTWK', 'NTZ', 'NUAG', 'NUAN',
      'NUBD', 'NUDM', 'NUE', 'NUEM', 'NUHY', 'NULC', 'NULG', 'NULV', 'NUM', 'NUMG', 'NUMV', 'NUO', 'NURE', 'NURO', 'NUS', 'NUSA', 'NUSC', 'NUSI', 'NUV', 'NUVA', 'NUW', 'NUZE', 'NVAX', 'NVCN', 'NVCR',
      'NVDA', 'NVEC', 'NVEE', 'NVFY', 'NVG', 'NVGS', 'NVIV', 'NVMI', 'NVO', 'NVQ', 'NVR', 'NVRO', 'NVS', 'NVST', 'NVT', 'NVTA', 'NVUS', 'NWBI', 'NWE', 'NWFL', 'NWG', 'NWHM', 'NWL', 'NWLI', 'NWN',
      'NWPX', 'NWS', 'NWSA', 'NX', 'NXC', 'NXE', 'NXGN', 'NXJ', 'NXN', 'NXP', 'NXPI', 'NXQ', 'NXR', 'NXRT', 'NXST', 'NXTC', 'NXTD', 'NXTG', 'NYC', 'NYCB', 'NYCB_A', 'NYCB_U', 'NYMT', 'NYMTM',
      'NYMTN', 'NYMTO', 'NYMTP', 'NYMX', 'NYT', 'NYV', 'NZF', 'O', 'OAC-U', 'OAC-WS', 'OAC', 'OACB-U', 'OACB-WS', 'OACB', 'OAK_A', 'OAK_B', 'OAS', 'OBCI', 'OBLG', 'OBLN', 'OBNK', 'OBOR', 'OBSV',
      'OC', 'OCA-U', 'OCC', 'OCCI', 'OCFC', 'OCFCP', 'OCFT', 'OCG', 'OCGN', 'OCIO', 'OCN', 'OCSI', 'OCSL', 'OCTZ', 'OCUL', 'OCUP', 'OCX', 'ODC', 'ODFL', 'ODP', 'ODT', 'OEC', 'OEG', 'OESX', 'OEUR',
      'OFC', 'OFED', 'OFG', 'OFG_A', 'OFG_B', 'OFG_D', 'OFIX', 'OFLX', 'OFS', 'OFSSG', 'OFSSI', 'OFSSL', 'OGE', 'OGEN', 'OGI', 'OGIG', 'OGS', 'OHI', 'OI', 'OIA', 'OIBR-C', 'OII', 'OIIM', 'OIL',
      'OILK', 'OIS', 'OKE', 'OKTA', 'OLB', 'OLD', 'OLED', 'OLLI', 'OLMA', 'OLN', 'OLP', 'OM', 'OMAB', 'OMC', 'OMCL', 'OMER', 'OMEX', 'OMF', 'OMFL', 'OMFS', 'OMI', 'OMP', 'ON', 'ONB', 'ONCR', 'ONCS',
      'ONCT', 'ONCY', 'ONDS', 'ONE', 'ONEM', 'ONEO', 'ONEV', 'ONEW', 'ONEY', 'ONLN', 'ONTO', 'ONTX', 'ONTXW', 'ONVO', 'OOMA', 'OPBK', 'OPCH', 'OPEN', 'OPENW', 'OPER', 'OPGN', 'OPHC', 'OPI', 'OPINI',
      'OPINL', 'OPK', 'OPNT', 'OPOF', 'OPP', 'OPP_A', 'OPRA', 'OPRT', 'OPRX', 'OPT', 'OPTN', 'OPTT', 'OPY', 'OR', 'ORA', 'ORAN', 'ORBC', 'ORC', 'ORCC', 'ORCL', 'ORGO', 'ORGS', 'ORI', 'ORIC', 'ORLA',
      'ORLY', 'ORMP', 'ORN', 'ORPH', 'ORRF', 'ORTX', 'OSB', 'OSBC', 'OSCV', 'OSG', 'OSH', 'OSIS', 'OSK', 'OSMT', 'OSN', 'OSPN', 'OSS', 'OSTK', 'OSUR', 'OSW', 'OTEL', 'OTEX', 'OTIC', 'OTIS', 'OTLK',
      'OTLKW', 'OTRA', 'OTRAU', 'OTRAW', 'OTRK', 'OTRKP', 'OTTR', 'OUSA', 'OUSM', 'OUT', 'OVB', 'OVBC', 'OVF', 'OVID', 'OVL', 'OVLY', 'OVM', 'OVS', 'OVV', 'OXBR', 'OXBRW', 'OXFD', 'OXLC', 'OXLCM',
      'OXLCO', 'OXLCP', 'OXM', 'OXSQ', 'OXSQL', 'OXSQZ', 'OXY-WS', 'OXY', 'OYST', 'OZK', 'OZON', 'PAA', 'PAAS', 'PAC', 'PACB', 'PACE-U', 'PACE-WS', 'PACE', 'PACK', 'PACW', 'PAE', 'PAEWW', 'PAG',
      'PAGP', 'PAGS', 'PAHC', 'PAI', 'PAIC', 'PAICU', 'PAICW', 'PALC', 'PAM', 'PAMC', 'PANA-U', 'PANA-WS', 'PANA', 'PAND', 'PANL', 'PANW', 'PAR', 'PARR', 'PASG', 'PATI', 'PATK', 'PAUG', 'PAVE',
      'PAVM', 'PAVMW', 'PAVMZ', 'PAWZ', 'PAYA', 'PAYAW', 'PAYC', 'PAYS', 'PAYX', 'PB', 'PBA', 'PBB', 'PBC', 'PBCT', 'PBCTP', 'PBDM', 'PBEE', 'PBF', 'PBFS', 'PBFX', 'PBH', 'PBHC', 'PBI', 'PBIP',
      'PBI_B', 'PBLA', 'PBND', 'PBPB', 'PBR-A', 'PBR', 'PBSM', 'PBT', 'PBTP', 'PBTS', 'PBUS', 'PBY', 'PBYI', 'PCAR', 'PCB', 'PCF', 'PCG', 'PCGU', 'PCG_A', 'PCG_D', 'PCG_H', 'PCG_I', 'PCH', 'PCI',
      'PCK', 'PCM', 'PCN', 'PCOM', 'PCPC-U', 'PCPL-U', 'PCPL-WS', 'PCPL', 'PCQ', 'PCRX', 'PCSA', 'PCSB', 'PCTI', 'PCTY', 'PCVX', 'PCYG', 'PCYO', 'PD', 'PDAC-U', 'PDAC-WS', 'PDAC', 'PDCE', 'PDCO', 'PDD', 'PDEV', 'PDEX', 'PDFS', 'PDI', 'PDLB', 'PDM', 'PDP', 'PDS', 'PDSB', 'PDT', 'PE', 'PEAK', 'PEB', 'PEBK', 'PEBO', 'PEB_C', 'PEB_D', 'PEB_E', 'PEB_F', 'PECK', 'PED', 'PEG', 'PEGA', 'PEI', 'PEIX', 'PEI_B', 'PEI_C', 'PEI_D', 'PEN', 'PENN', 'PEO', 'PEP', 'PERI', 'PESI', 'PETQ', 'PETS', 'PETZ', 'PEXL', 'PEY', 'PEZ', 'PFBC', 'PFBI', 'PFC', 'PFD', 'PFE', 'PFEB', 'PFFA', 'PFFD', 'PFFL', 'PFFR', 'PFFV', 'PFG', 'PFGC', 'PFH', 'PFHD', 'PFI', 'PFIE', 'PFIN', 'PFIS', 'PFL', 'PFLD', 'PFLT', 'PFM', 'PFMT', 'PFN', 'PFO', 'PFPT', 'PFS', 'PFSI', 'PFSW', 'PG', 'PGC', 'PGEN', 'PGJ', 'PGM', 'PGNY', 'PGP', 'PGR', 'PGRE', 'PGTI', 'PGZ', 'PH', 'PHAR', 'PHAS', 'PHAT', 'PHCF', 'PHD', 'PHG', 'PHGE-U', 'PHGE-WS', 'PHGE', 'PHI', 'PHICU', 'PHIO', 'PHIOW', 'PHK', 'PHM', 'PHO', 'PHR', 'PHT', 'PHUN', 'PHUNW', 'PHX', 'PHYL', 'PHYS', 'PI', 'PIAI-U', 'PIAI-WS', 'PIAI', 'PICO', 'PID', 'PIE', 'PIFI', 'PII', 'PILL', 'PIM', 'PINC', 'PINE', 'PING', 'PINS', 'PIPP-U', 'PIPR', 'PIRS', 'PIXY', 'PIZ', 'PJAN', 'PJT', 'PJUL', 'PK', 'PKBK', 'PKE', 'PKG', 'PKI', 'PKO', 'PKOH', 'PKW', 'PKX', 'PLAB', 'PLAG', 'PLAN', 'PLAT', 'PLAY', 'PLBC', 'PLCE', 'PLD', 'PLG', 'PLIN', 'PLL', 'PLM', 'PLMR', 'PLNT', 'PLOW', 'PLPC', 'PLRX', 'PLSE', 'PLT', 'PLTM', 'PLTR', 'PLUG', 'PLUS', 'PLW', 'PLX', 'PLXP', 'PLXS', 'PLYA', 'PLYM', 'PLYM_A', 'PM', 'PMBC', 'PMD', 'PME', 'PMF', 'PML', 'PMM', 'PMO', 'PMT', 'PMT_A', 'PMT_B', 'PMVC-U', 'PMVC-WS', 'PMVC', 'PMVP', 'PMX', 'PNBK', 'PNC', 'PNC_P', 'PNF', 'PNFP', 'PNFPP', 'PNI', 'PNM', 'PNNT', 'PNNTG', 'PNR', 'PNRG', 'PNTG', 'PNW', 'POAI', 'POCT', 'PODD', 'POLA', 'POOL', 'POR', 'POST', 'POTX', 'POWI', 'POWL', 'POWW', 'PPBI', 'PPBT', 'PPC', 'PPD', 'PPG', 'PPIH', 'PPL', 'PPR', 'PPSI', 'PPT', 'PPTY', 'PPX', 'PQDI', 'PQG', 'PQIN', 'PQLC', 'PQSG', 'PQSV', 'PRA', 'PRAA', 'PRAH', 'PRAX', 'PRCH', 'PRCHW', 'PRDO', 'PREF', 'PRE_G', 'PRE_H', 'PRE_I', 'PRFT', 'PRFX', 'PRG', 'PRGO', 'PRGS', 'PRGX', 'PRI', 'PRIF_A', 'PRIF_B', 'PRIF_C', 'PRIF_D', 'PRIF_E', 'PRIF_F', 'PRIM', 'PRK', 'PRLB', 'PRLD', 'PRMW', 'PRN', 'PRNT', 'PRO', 'PROF', 'PROG', 'PROS', 'PROV', 'PRPB-U', 'PRPB-WS', 'PRPB', 'PRPH', 'PRPL', 'PRPO', 'PRQR', 'PRS', 'PRSC', 'PRSP', 'PRT', 'PRTA', 'PRTH', 'PRTK', 'PRTS', 'PRTY', 'PRU', 'PRVB', 'PRVL', 'PS', 'PSA', 'PSAC', 'PSACU', 'PSACW', 'PSA_B', 'PSA_C', 'PSA_D', 'PSA_E', 'PSA_F', 'PSA_G', 'PSA_H', 'PSA_I', 'PSA_J', 'PSA_K', 'PSA_L', 'PSA_M', 'PSA_N', 'PSA_O', 'PSB', 'PSB_W', 'PSB_X', 'PSB_Y', 'PSB_Z', 'PSC', 'PSEC', 'PSET', 'PSF', 'PSHG', 'PSL', 'PSLV', 'PSMB', 'PSMC', 'PSMG', 'PSMM', 'PSMT', 'PSN', 'PSNL', 'PSO', 'PSTG', 'PSTH-WS', 'PSTH', 'PSTI', 'PSTL', 'PSTV', 'PSTX', 'PSX', 'PSXP', 'PT', 'PTA', 'PTBD', 'PTC', 'PTCT', 'PTE', 'PTEN', 'PTEU', 'PTF', 'PTGX', 'PTH', 'PTICU', 'PTIN', 'PTK-U', 'PTK-WS', 'PTK', 'PTLC', 'PTMC', 'PTMN', 'PTN', 'PTNQ', 'PTNR', 'PTON', 'PTPI', 'PTR', 'PTRS', 'PTSI', 'PTVCA', 'PTVCB', 'PTVE', 'PTY', 'PUBM', 'PUI', 'PUK', 'PUK_', 'PUK_A', 'PULM', 'PULS', 'PUMP', 'PUTW', 'PVAC', 'PVBC', 'PVG', 'PVH', 'PVL', 'PW', 'PWFL', 'PWOD', 'PWR', 'PWS', 'PW_A', 'PXD', 'PXI', 'PXLW', 'PXS', 'PXSAP', 'PXSAW', 'PYN', 'PYPD', 'PYPE', 'PYPL', 'PYS', 'PYZ', 'PZC', 'PZG', 'PZN', 'PZZA', 'QADA', 'QARP', 'QCOM', 'QCRH', 'QD', 'QDEL', 'QDIV', 'QELL', 'QELLU', 'QELLW', 'QEP', 'QFIN', 'QGEN', 'QGRO', 'QH', 'QINT', 'QIWI', 'QK', 'QLGN', 'QLV', 'QLVD', 'QLVE', 'QLYS', 'QMCO', 'QMJ', 'QMOM', 'QNST', 'QPT', 'QPX', 'QQC', 'QQD', 'QQH', 'QQQJ', 'QQQM', 'QQQN', 'QQQX', 'QRFT', 'QRHC', 'QRTEA', 'QRTEB', 'QRTEP', 'QRVO', 'QS-WS', 'QS', 'QSR', 'QSY', 'QTNT', 'QTRX', 'QTS', 'QTS_A', 'QTS_B', 'QTT', 'QTUM', 'QTWO', 'QUAD', 'QUIK', 'QUMU', 'QUOT', 'QURE', 'QVAL', 'QVCC', 'QVCD', 'QYLG', 'R', 'RA', 'RAACU', 'RAAX', 'RACA', 'RACE', 'RAD', 'RADA', 'RADI', 'RAFE', 'RAIL', 'RAMP', 'RAND', 'RAPT', 'RARE', 'RAVE', 'RAVN', 'RBA', 'RBAC-U', 'RBAC-WS', 'RBAC', 'RBB', 'RBBN', 'RBC', 'RBCAA', 'RBCN', 'RBIN', 'RBKB', 'RBNC', 'RBND', 'RBUS', 'RC', 'RCA', 'RCB', 'RCEL', 'RCG', 'RCHG', 'RCHGU', 'RCHGW', 'RCI', 'RCII', 'RCKT', 'RCKY', 'RCL', 'RCM', 'RCMT', 'RCON', 'RCP', 'RCS', 'RCUS', 'RDCM', 'RDFI', 'RDFN', 'RDHL', 'RDI', 'RDN', 'RDNT', 'RDOG', 'RDS-A', 'RDS-B', 'RDUS', 'RDVT', 'RDWR', 'RDY', 'RE', 'REAL', 'RECS', 'REDU', 'REED', 'REFR', 'REG', 'REGI', 'REGN', 'REI', 'REKR', 'RELL', 'RELX', 'REML', 'RENN', 'REPH', 'REPL', 'RES', 'RESD', 'RESE', 'RESI', 'RESN', 'RESP', 'RETA', 'RETO', 'REV', 'REVG', 'REVS', 'REX', 'REXR', 'REXR_A', 'REXR_B', 'REXR_C', 'REYN', 'REZI', 'RF', 'RFAP', 'RFCI', 'RFDA', 'RFDI', 'RFEM', 'RFEU', 'RFFC', 'RFI', 'RFIL', 'RFL', 'RFM', 'RFP', 'RFUN', 'RF_A', 'RF_B', 'RF_C', 'RGA', 'RGCO', 'RGEN', 'RGLD', 'RGLS', 'RGNX', 'RGP', 'RGR', 'RGS', 'RGT', 'RH', 'RHE', 'RHE_A', 'RHI', 'RHP', 'RIBT', 'RICE-U', 'RICE-WS', 'RICE', 'RICK', 'RIDE', 'RIDEW', 'RIG', 'RIGL', 'RILY', 'RILYG', 'RILYH', 'RILYI', 'RILYL', 'RILYM', 'RILYN', 'RILYO', 'RILYP', 'RILYZ', 'RIO', 'RIOT', 'RISN', 'RIV', 'RIVE', 'RJF', 'RKDA', 'RKT', 'RL', 'RLAY', 'RLGT', 'RLGY', 'RLH', 'RLI', 'RLJ', 'RLJ_A', 'RLMD', 'RM', 'RMAX', 'RMBI', 'RMBL', 'RMBS', 'RMCF', 'RMD', 'RMED', 'RMGBU', 'RMI', 'RMM', 'RMNI', 'RMO-WS', 'RMO', 'RMPL_', 'RMR', 'RMRM', 'RMT', 'RMTI', 'RNA', 'RNDB', 'RNDM', 'RNDV', 'RNEM', 'RNET', 'RNG', 'RNGR', 'RNLC', 'RNLX', 'RNMC', 'RNP', 'RNR', 'RNR_E', 'RNR_F', 'RNSC', 'RNST', 'RNWK', 'ROAD', 'ROAM', 'ROBO', 'ROBT', 'ROCCU', 'ROCH', 'ROCHW', 'ROCK', 'RODE', 'RODI', 'RODM', 'ROG', 'ROIC', 'ROK', 'ROKT', 'ROKU', 'ROL', 'ROLL', 'ROOT', 'ROP', 'RORO', 'ROSC', 'ROST', 'ROUS', 'RP', 'RPAI', 'RPAR', 'RPAY', 'RPD', 'RPLA-U', 'RPLA-WS', 'RPLA', 'RPM', 'RPRX', 'RPT', 'RPTX', 'RPT_D', 'RQI', 'RRBI', 'RRC', 'RRD', 'RRGB', 'RRR', 'RS', 'RSF', 'RSG', 'RSI-WS', 'RSI', 'RSSS', 'RSVAU', 'RTAI', 'RTH', 'RTLR', 'RTP-U', 'RTP-WS', 'RTP', 'RTPZ-U', 'RTX', 'RUBY', 'RUHN', 'RUN', 'RUSHA', 'RUSHB', 'RUTH', 'RVI', 'RVLV', 'RVMD', 'RVNC', 'RVP', 'RVPH', 'RVPHW', 'RVRS', 'RVSB', 'RVT', 'RWGV', 'RWLK', 'RWT', 'RWVG', 'RXN', 'RXT', 'RY', 'RYAAY', 'RYAM', 'RYB', 'RYI', 'RYN', 'RYTM', 'RY_T', 'RZA', 'RZB', 'RZLT', 'SA', 'SABR', 'SABRP', 'SACC', 'SACH', 'SAF', 'SAFE', 'SAFM', 'SAFT', 'SAGE', 'SAH', 'SAIA', 'SAIC', 'SAII', 'SAIIU', 'SAIIW', 'SAIL', 'SAK', 'SAL', 'SALM', 'SALT', 'SAM', 'SAMG', 'SAN', 'SAND', 'SANM', 'SANW', 'SAP', 'SAR', 'SASR', 'SATS', 'SAVA', 'SAVE', 'SB', 'SBAC', 'SBBA', 'SBBP', 'SBCF', 'SBE-U', 'SBE-WS', 'SBE', 'SBFG', 'SBG-U', 'SBG-WS', 'SBG', 'SBGI', 'SBH', 'SBI', 'SBLK', 'SBLKZ', 'SBNY', 'SBNYP', 'SBOW', 'SBR', 'SBRA', 'SBS', 'SBSI', 'SBSW', 'SBT', 'SBTX', 'SBUG', 'SBUX', 'SB_C', 'SB_D', 'SC', 'SCCB', 'SCCC', 'SCCO', 'SCD', 'SCE_G', 'SCE_H', 'SCE_J', 'SCE_K', 'SCE_L', 'SCHI', 'SCHJ', 'SCHK', 'SCHL', 'SCHN', 'SCHQ', 'SCHW', 'SCHW_C', 'SCHW_D', 'SCI', 'SCKT', 'SCL', 'SCM', 'SCOAU', 'SCOR', 'SCPE-WS', 'SCPE', 'SCPH', 'SCPL', 'SCPS', 'SCS', 'SCSC', 'SCU', 'SCVL', 'SCVX-WS', 'SCVX', 'SCWX', 'SCX', 'SCYX', 'SD', 'SDC', 'SDCI', 'SDG', 'SDGA', 'SDGR', 'SDHY', 'SDPI', 'SDVY', 'SE', 'SEAC', 'SEAH-U', 'SEAH-WS', 'SEAH', 'SEAS', 'SEB', 'SECO', 'SECT', 'SEDG', 'SEE', 'SEED', 'SEEL', 'SEER', 'SEIC', 'SEIX', 'SELB', 'SELF', 'SEM', 'SENEA', 'SENS', 'SEPZ', 'SESN', 'SF', 'SFB', 'SFBC', 'SFBS', 'SFE', 'SFET', 'SFHY', 'SFIG', 'SFIX', 'SFL', 'SFM', 'SFNC', 'SFST', 'SFT', 'SFTTW', 'SFTW-U', 'SFTW-WS', 'SFTW', 'SFUN', 'SFY', 'SFYF', 'SFYX', 'SF_A', 'SF_B', 'SF_C', 'SG', 'SGA', 'SGAM', 'SGAMU', 'SGAMW', 'SGBX', 'SGC', 'SGEN', 'SGG', 'SGH', 'SGLB', 'SGLBW', 'SGMA', 'SGMO', 'SGMS', 'SGOC', 'SGOV', 'SGRP', 'SGRY', 'SGTX', 'SGU', 'SHAG', 'SHAK', 'SHBI', 'SHC', 'SHE', 'SHEN', 'SHG', 'SHI', 'SHIP', 'SHIPW', 'SHIPZ', 'SHLD', 'SHLX', 'SHO', 'SHOO', 'SHOP', 'SHO_E', 'SHO_F', 'SHSP', 'SHW', 'SHYF', 'SHYL', 'SI', 'SIBN', 'SIC', 'SID', 'SIEB', 'SIEN', 'SIF', 'SIFY', 'SIG', 'SIGA', 'SIGI', 'SIGIP', 'SII', 'SILC', 'SILK', 'SILV', 'SIM', 'SIMO', 'SIMS', 'SINA', 'SINO', 'SINT', 'SIOX', 'SIRI', 'SITC', 'SITC_A', 'SITC_K', 'SITE', 'SITM', 'SIVB', 'SIVBP', 'SIX', 'SIXA', 'SIXH', 'SIXL', 'SIXS', 'SJ', 'SJI', 'SJIJ', 'SJIU', 'SJM', 'SJR', 'SJT', 'SJW', 'SKLZ-WS', 'SKLZ', 'SKM', 'SKT', 'SKX', 'SKY', 'SKYW', 'SLAB', 'SLB', 'SLCA', 'SLCT', 'SLDB', 'SLF', 'SLG', 'SLGG', 'SLGL', 'SLGN', 'SLG_I', 'SLM', 'SLMBP', 'SLN', 'SLNO', 'SLP', 'SLQT', 'SLRC', 'SLRX', 'SLS', 'SLT', 'SM', 'SMAR', 'SMBC', 'SMBK', 'SMCI', 'SMCP', 'SMDY', 'SMED', 'SMFG', 'SMG', 'SMHB', 'SMHI', 'SMID', 'SMIN', 'SMIT', 'SMLP', 'SMM', 'SMMC', 'SMMCU', 'SMMCW', 'SMMD', 'SMMF', 'SMMT', 'SMMV', 'SMOG', 'SMP', 'SMPL', 'SMSI', 'SMTC', 'SMTI', 'SMTS', 'SMTX', 'SNA', 'SNAP', 'SNBR', 'SNCA', 'SNCR', 'SND', 'SNDE', 'SNDL', 'SNDR', 'SNDX', 'SNE', 'SNES', 'SNEX', 'SNFCA', 'SNGX', 'SNGXW', 'SNMP', 'SNN', 'SNOA', 'SNOW', 'SNP', 'SNPE', 'SNPR-U', 'SNPR-WS', 'SNPR', 'SNPS', 'SNR', 'SNRHU', 'SNSR', 'SNSS', 'SNUG', 'SNV', 'SNV_D', 'SNV_E', 'SNX', 'SNY', 'SO', 'SOAC-U', 'SOAC-WS', 'SOAC', 'SOGO', 'SOHO', 'SOHOB', 'SOHON', 'SOHOO', 'SOHU', 'SOI', 'SOJB', 'SOJC', 'SOJD', 'SOJE', 'SOL', 'SOLN', 'SOLO', 'SOLOW', 'SOLY', 'SON', 'SONA', 'SONM', 'SONN', 'SONO', 'SOR', 'SOS', 'SOVB', 'SP', 'SPAB', 'SPAK', 'SPB', 'SPBO', 'SPCB', 'SPCE', 'SPCX', 'SPD', 'SPDN', 'SPDV', 'SPDW', 'SPE', 'SPEM', 'SPEU', 'SPE_B', 'SPFI', 'SPFR-U', 'SPG', 'SPGI', 'SPGM', 'SPGP', 'SPG_J', 'SPH', 'SPHY', 'SPI', 'SPIB', 'SPIP', 'SPKE', 'SPKEP', 'SPLB', 'SPLG', 'SPLK', 'SPLP', 'SPLP_A', 'SPMB', 'SPMD', 'SPMO', 'SPMV', 'SPNE', 'SPNS', 'SPNV-U', 'SPNV-WS', 'SPNV', 'SPOK', 'SPOT', 'SPPI', 'SPPP', 'SPR', 'SPRB', 'SPRO', 'SPRQ-U', 'SPRT', 'SPSB', 'SPSC', 'SPSK', 'SPSM', 'SPT', 'SPTI', 'SPTL', 'SPTM', 'SPTN', 'SPTS', 'SPUC', 'SPUS', 'SPVM', 'SPVU', 'SPWH', 'SPWR', 'SPXB', 'SPXC', 'SPXE', 'SPXN', 'SPXT', 'SPXV', 'SPXX', 'SPYC', 'SPYD', 'SPYX', 'SQ', 'SQBG', 'SQEW', 'SQFT', 'SQM', 'SQNS', 'SQZ', 'SR', 'SRAC', 'SRACU', 'SRACW', 'SRAX', 'SRC', 'SRCE', 'SRCL', 'SRC_A', 'SRDX', 'SRE', 'SREA', 'SREV', 'SRE_A', 'SRE_B', 'SRG', 'SRGA', 'SRG_A', 'SRI', 'SRL', 'SRLP', 'SRNE', 'SRPT', 'SRRA', 'SRRK', 'SRSA', 'SRSAU', 'SRSAW', 'SRT', 'SRTS', 'SRV', 'SRVR', 'SR_A', 'SSB', 'SSBI', 'SSD', 'SSKN', 'SSL', 'SSLY', 'SSNC', 'SSNT', 'SSP', 'SSPK', 'SSPKU', 'SSPKW', 'SSPY', 'SSRM', 'SSSS', 'SSTI', 'SSTK', 'SSUS', 'SSY', 'SSYS', 'ST', 'STAA', 'STAF', 'STAG', 'STAG_C', 'STAR', 'STAR_D', 'STAR_G', 'STAR_I', 'STAY', 'STBA', 'STC', 'STCN', 'STE', 'STEP', 'STFC', 'STG', 'STIC-U', 'STIC-WS', 'STIC', 'STIM', 'STK', 'STKL', 'STKS', 'STL', 'STLC', 'STLD', 'STLG', 'STLV', 'STL_A', 'STM', 'STMB', 'STMP', 'STN', 'STND', 'STNE', 'STNG', 'STOK', 'STON', 'STOR', 'STOT', 'STPK-U', 'STPK-WS', 'STPK', 'STRA', 'STRL', 'STRM', 'STRO', 'STRS', 'STRT', 'STSA', 'STSB', 'STT', 'STTK', 'STT_D', 'STT_G', 'STWD', 'STWO', 'STWOU', 'STWOW', 'STX', 'STXB', 'STXS', 'STZ-B', 'STZ', 'SU', 'SUI', 'SULR', 'SUM', 'SUMO', 'SUMR', 'SUN', 'SUNS', 'SUNW', 'SUP', 'SUPN', 'SUPV', 'SURF', 'SUSA', 'SUSB', 'SUSC', 'SUSL', 'SUZ', 'SV', 'SVAC', 'SVACU', 'SVACW', 'SVAL', 'SVBI', 'SVC', 'SVM', 'SVMK', 'SVOKU', 'SVRA', 'SVSVU', 'SVSVW', 'SVT', 'SVVC', 'SWAN', 'SWAV', 'SWBI', 'SWCH', 'SWI', 'SWIR', 'SWK', 'SWKH', 'SWKS', 'SWM', 'SWN', 'SWT', 'SWTX', 'SWX', 'SWZ', 'SXC', 'SXI', 'SXT', 'SXTC', 'SY', 'SYBT', 'SYBX', 'SYF', 'SYF_A', 'SYK', 'SYKE', 'SYN', 'SYNA', 'SYNC', 'SYNH', 'SYNL', 'SYPR', 'SYRS', 'SYTA', 'SYTAW', 'SYX', 'SYY', 'SZC', 'SZNE', 'T', 'TA', 'TAAG', 'TAC', 'TACA-U', 'TACE', 'TACO', 'TACT', 'TADS', 'TAIL', 'TAIT', 'TAK', 'TAL', 'TALO-WS', 'TALO', 'TANH', 'TANNI', 'TANNL', 'TANNZ', 'TAOP', 'TAP-A', 'TAP', 'TARA', 'TARO', 'TARS', 'TAST', 'TATT', 'TAXF', 'TAYD', 'TBB', 'TBBK', 'TBC', 'TBI', 'TBIO', 'TBJL', 'TBK', 'TBKCP', 'TBLT', 'TBLTW', 'TBNK', 'TBPH', 'TC', 'TCBI', 'TCBIL', 'TCBIP', 'TCBK', 'TCCO', 'TCDA', 'TCF', 'TCFC', 'TCFCP', 'TCHP', 'TCI', 'TCMD', 'TCOM', 'TCON', 'TCP', 'TCPC', 'TCRR', 'TCS', 'TCTL', 'TCX', 'TD', 'TDA', 'TDAC', 'TDACU', 'TDACW', 'TDC', 'TDE', 'TDF', 'TDG', 'TDI', 'TDJ', 'TDOC', 'TDS', 'TDSC', 'TDSE', 'TDVG', 'TDW-WS-A', 'TDW-WS-B', 'TDW-WS', 'TDW', 'TDY', 'TEAF', 'TEAM', 'TECB', 'TECH', 'TECK', 'TECTP', 'TEDU', 'TEF', 'TEI', 'TEKK', 'TEKKU', 'TEKKW', 'TEL', 'TELA', 'TELL', 'TEN', 'TENB', 'TENX', 'TEO', 'TEQI', 'TER', 'TERM', 'TESS', 'TEVA', 'TEX', 'TFC', 'TFC_F', 'TFC_G', 'TFC_H', 'TFC_I', 'TFC_O', 'TFC_R', 'TFFP', 'TFII', 'TFIV', 'TFJL', 'TFLT', 'TFSL', 'TFX', 'TG', 'TGA', 'TGB', 'TGC', 'TGH', 'TGI', 'TGIF', 'TGLS', 'TGNA', 'TGP', 'TGP_A', 'TGP_B', 'TGRW', 'TGS', 'TGT', 'TGTX', 'TH', 'THBR', 'THBRU', 'THBRW', 'THC', 'THCA', 'THCAU', 'THCAW', 'THCB', 'THCBU', 'THCBW', 'THCX', 'THFF', 'THG', 'THM', 'THMO', 'THNQ', 'THO', 'THQ', 'THR', 'THRM', 'THRY', 'THS', 'THTX', 'THW', 'THWWW', 'TIF', 'TIG', 'TIGO', 'TIGR', 'TILE', 'TIMB', 'TINV-U', 'TIPT', 'TISI', 'TITN', 'TJX', 'TK', 'TKAT', 'TKC', 'TKR', 'TLC', 'TLDH', 'TLEH', 'TLGT', 'TLK', 'TLMD', 'TLMDW', 'TLND', 'TLRY', 'TLS', 'TLSA', 'TLYS', 'TM', 'TMBR', 'TMDI', 'TMDX', 'TME', 'TMFC', 'TMHC', 'TMO', 'TMP', 'TMPM', 'TMPMU', 'TMQ', 'TMST', 'TMTS', 'TMTSU', 'TMTSW', 'TMUS', 'TMX', 'TNAV', 'TNC', 'TNDM', 'TNET', 'TNK', 'TNP', 'TNP_D', 'TNP_E', 'TNP_F', 'TNXP', 'TOL', 'TOMZ', 'TOPS', 'TOT', 'TOUR', 'TOWN', 'TPAY', 'TPB', 'TPC', 'TPCO', 'TPGY-U', 'TPGY-WS', 'TPGY', 'TPH', 'TPHD', 'TPHS', 'TPIC', 'TPIF', 'TPL', 'TPLC', 'TPOR', 'TPR', 'TPRE', 'TPSC', 'TPTX', 'TPVG', 'TPVY', 'TPX', 'TPYP', 'TPZ', 'TR', 'TRC', 'TRCH', 'TREB-U', 'TREB-WS', 'TREB', 'TREC', 'TREE', 'TREX', 'TRGP', 'TRHC', 'TRI', 'TRIB', 'TRIL', 'TRIP', 'TRIT', 'TRITW', 'TRMB', 'TRMD', 'TRMK', 'TRMT', 'TRN', 'TRNO', 'TRNS', 'TROW', 'TROX', 'TRP', 'TRQ', 'TRS', 'TRST', 'TRT', 'TRTN', 'TRTN_A', 'TRTN_B', 'TRTN_C', 'TRTN_D', 'TRTX', 'TRTY', 'TRU', 'TRUE', 'TRUP', 'TRV', 'TRVG', 'TRVI', 'TRVN', 'TRX', 'TRXC', 'TS', 'TSBK', 'TSC', 'TSCAP', 'TSCBP', 'TSCO', 'TSE', 'TSEM', 'TSHA', 'TSI', 'TSIAU', 'TSLA', 'TSLX', 'TSM', 'TSN', 'TSOC', 'TSQ', 'TSRI', 'TT', 'TTAC', 'TTAI', 'TTC', 'TTCF', 'TTCFW', 'TTD', 'TTEC', 'TTEK', 'TTGT', 'TTI', 'TTM', 'TTMI', 'TTNP', 'TTOO', 'TTP', 'TTWO', 'TU', 'TUFN', 'TUP', 'TURN', 'TUSK', 'TV', 'TVACU', 'TVC', 'TVE', 'TVTX', 'TVTY', 'TW', 'TWCT', 'TWCTU', 'TWCTW', 'TWI', 'TWIN', 'TWLO', 'TWN', 'TWND-U', 'TWND-WS', 'TWND', 'TWNK', 'TWNKW', 'TWO', 'TWOU', 'TWO_A', 'TWO_B', 'TWO_C', 'TWO_D', 'TWO_E', 'TWST', 'TWTR', 'TX', 'TXG', 'TXMD', 'TXN', 'TXRH', 'TXT', 'TY', 'TYG', 'TYHT', 'TYL', 'TYME', 'TZOO', 'T_A', 'T_C', 'U', 'UA', 'UAA', 'UAL', 'UAMY', 'UAN', 'UAUG', 'UAVS', 'UBA', 'UBCP', 'UBER', 'UBFO', 'UBOH', 'UBOT', 'UBP', 'UBP_H', 'UBP_K', 'UBS', 'UBSI', 'UBX', 'UCBI', 'UCBIO', 'UCIB', 'UCL', 'UCON', 'UCTT', 'UDR', 'UE', 'UEC', 'UEIC', 'UEPS', 'UEVM', 'UFAB', 'UFCS', 'UFEB', 'UFI', 'UFO', 'UFPI', 'UFPT', 'UFS', 'UG', 'UGI', 'UGP', 'UHAL', 'UHS', 'UHT', 'UI', 'UIHC', 'UIS', 'UITB', 'UIVM', 'UJAN', 'UJUL', 'UK', 'UKOMW', 'UL', 'ULBI', 'ULH', 'ULTA', 'ULTR', 'ULVM', 'UMBF', 'UMC', 'UMH', 'UMH_C', 'UMH_D', 'UMPQ', 'UNAM', 'UNB', 'UNF', 'UNFI', 'UNH', 'UNIT', 'UNM', 'UNMA', 'UNP', 'UNTY', 'UNVR', 'UOCT', 'UONE', 'UONEK', 'UPLD', 'UPS', 'UPST', 'UPWK', 'URBN', 'URG', 'URGN', 'URI', 'URNM', 'UROV', 'USA', 'USAC', 'USAI', 'USAK', 'USAP', 'USAS', 'USAT', 'USAU', 'USB', 'USB_A', 'USB_H', 'USB_M', 'USB_O', 'USB_P', 'USB_Q', 'USCR', 'USDP', 'USEG', 'USEQ', 'USFD', 'USHG', 'USHY', 'USI', 'USIG', 'USIO', 'USLB', 'USLM', 'USM', 'USMC', 'USMF', 'USNA', 'USOI', 'USPH', 'USRT', 'USSG', 'USTB', 'USVM', 'USWS', 'USWSW', 'USX', 'USXF', 'UTES', 'UTF', 'UTG', 'UTHR', 'UTI', 'UTL', 'UTMD', 'UTRN', 'UTSI', 'UTSL', 'UTZ-WS', 'UTZ', 'UUU', 'UUUU-WS', 'UUUU', 'UVE', 'UVSP', 'UVV', 'UXIN', 'UZA', 'UZB', 'UZC', 'UZD', 'UZE', 'V', 'VAC', 'VACQ', 'VACQU', 'VACQW', 'VALE', 'VALQ', 'VALT', 'VALU', 'VAMO', 'VAPO', 'VAR', 'VBF', 'VBIV', 'VBLT', 'VBTX', 'VC', 'VCAR', 'VCEB', 'VCEL', 'VCF', 'VCIF', 'VCLO', 'VCNX', 'VCRA', 'VCTR', 'VCV', 'VCVCU', 'VCYT', 'VEC', 'VECO', 'VEDL', 'VEEV', 'VEGN', 'VEL', 'VEON', 'VER', 'VERB', 'VERBW', 'VERI', 'VERO', 'VERU', 'VERX', 'VERY', 'VER_F', 'VET', 'VETS', 'VFC', 'VFF', 'VFIN', 'VFL', 'VFLQ', 'VFMF', 'VFMO', 'VFMV', 'VFQY', 'VFVA', 'VG', 'VGAC-U', 'VGAC-WS', 'VGAC', 'VGI', 'VGM', 'VGR', 'VGZ', 'VHAQ-U', 'VHC', 'VHI', 'VIAC', 'VIACA', 'VIAO', 'VIAV', 'VICE', 'VICI', 'VICR', 'VIE', 'VIGI', 'VIH', 'VIHAU', 'VIHAW', 'VIIAU', 'VINC', 'VINCW', 'VIOT', 'VIPS', 'VIR', 'VIRC', 'VIRI', 'VIRT', 'VISL', 'VIST', 'VITL', 'VIV', 'VIVE', 'VIVO', 'VJET', 'VKI', 'VKQ', 'VKTX', 'VKTXW', 'VLDR', 'VLDRW', 'VLGEA', 'VLO', 'VLRS', 'VLT', 'VLY', 'VLYPO', 'VLYPP', 'VMAC', 'VMACU', 'VMACW', 'VMAR', 'VMC', 'VMD', 'VMI', 'VMM', 'VMO', 'VMOT', 'VMW', 'VNCE', 'VNDA', 'VNE', 'VNET', 'VNLA', 'VNO', 'VNOM', 'VNO_K', 'VNO_L', 'VNO_M', 'VNO_N', 'VNRX', 'VNT', 'VNTR', 'VOC', 'VOD', 'VOLT', 'VOXX', 'VOYA', 'VOYA_B', 'VPC', 'VPG', 'VPN', 'VPOP', 'VPV', 'VRA', 'VRAI', 'VRAY', 'VRCA', 'VREX', 'VRIG', 'VRM', 'VRME', 'VRMEW', 'VRNA', 'VRNS', 'VRNT', 'VRRM', 'VRS', 'VRSK', 'VRSN', 'VRT-WS', 'VRT', 'VRTS', 'VRTU', 'VRTV', 'VRTX', 'VSAT', 'VSDA', 'VSEC', 'VSGX', 'VSH', 'VSL', 'VSMV', 'VSPR', 'VSPRU', 'VSPRW', 'VST-WS-A', 'VST', 'VSTA', 'VSTM', 'VSTO', 'VTA', 'VTAQU', 'VTC', 'VTEB', 'VTGN', 'VTN', 'VTNR', 'VTOL', 'VTR', 'VTRN', 'VTRS', 'VTRU', 'VTSI', 'VTVT', 'VUZI', 'VVI', 'VVNT-WS', 'VVNT', 'VVOS', 'VVPR', 'VVR', 'VVV', 'VWID', 'VXRT', 'VYGG-U', 'VYGG-WS', 'VYGG', 'VYGR', 'VYMI', 'VYNE', 'VZ', 'W', 'WAB', 'WABC', 'WAFD', 'WAFU', 'WAL', 'WALA', 'WANT', 'WASH', 'WAT', 'WATT', 'WB', 'WBA', 'WBAI', 'WBIE', 'WBIF', 'WBIG', 'WBII', 'WBIL', 'WBIN', 'WBIT', 'WBIY', 'WBK', 'WBND', 'WBS', 'WBS_F', 'WBT', 'WCC', 'WCC_A', 'WCLD', 'WCN', 'WD', 'WDAY', 'WDC', 'WDFC', 'WDR', 'WEA', 'WEBL', 'WEBS', 'WEC', 'WEI', 'WELL', 'WEN', 'WERN', 'WES', 'WETF', 'WEX', 'WEYS', 'WF', 'WFC', 'WFC_A', 'WFC_L', 'WFC_N', 'WFC_O', 'WFC_P', 'WFC_Q', 'WFC_R', 'WFC_W', 'WFC_X', 'WFC_Y', 'WFC_Z', 'WFH', 'WFHY', 'WFIG', 'WGO', 'WH', 'WHD', 'WHF', 'WHFBZ', 'WHG', 'WHLM', 'WHLR', 'WHLRD', 'WHLRP', 'WHR', 'WIA', 'WIFI', 'WIL', 'WILC', 'WIMI', 'WINA', 'WINC', 'WING', 'WINT', 'WIRE', 'WISA', 'WISH', 'WIT', 'WIW', 'WIX', 'WIZ', 'WK', 'WKEY', 'WKHS', 'WLDN', 'WLDR', 'WLFC', 'WLK', 'WLKP', 'WLL', 'WLTW', 'WM', 'WMB', 'WMC', 'WMG', 'WMK', 'WMS', 'WMT', 'WNC', 'WNEB', 'WNS', 'WNW', 'WOMN', 'WOR', 'WORK', 'WORX', 'WOW', 'WPC', 'WPF-U', 'WPF-WS', 'WPF', 'WPG', 'WPG_H', 'WPG_I', 'WPM', 'WPP', 'WPRT', 'WPX', 'WRAP', 'WRB', 'WRB_C', 'WRB_D', 'WRB_E', 'WRB_F', 'WRB_G', 'WRE', 'WRI', 'WRK', 'WRLD', 'WRN', 'WSBC', 'WSBCP', 'WSBF', 'WSC', 'WSFS', 'WSG', 'WSM', 'WSO', 'WSR', 'WST', 'WSTG', 'WTBA', 'WTER', 'WTFC', 'WTFCM', 'WTFCP', 'WTI', 'WTM', 'WTMF', 'WTRE', 'WTREP', 'WTRG', 'WTRH', 'WTRU', 'WTS', 'WTT', 'WTTR', 'WU', 'WVE', 'WVFC', 'WVVI', 'WVVIP', 'WW', 'WWD', 'WWE', 'WWJD', 'WWOW', 'WWR', 'WWW', 'WY', 'WYND', 'WYNN', 'WYY', 'X', 'XAIR', 'XAN', 'XAN_C', 'XBIO', 'XBIT', 'XBUY', 'XCEM', 'XCUR', 'XDIV', 'XEC', 'XEL', 'XELA', 'XELB', 'XENE', 'XENT', 'XERS', 'XFLT', 'XFOR', 'XGN', 'XHR', 'XIN', 'XITK', 'XL-WS', 'XL', 'XLNX', 'XLRE', 'XLRN', 'XLSR', 'XMHQ', 'XMMO', 'XMVM', 'XNCR', 'XNET', 'XNTK', 'XOM', 'XOMA', 'XOMAP', 'XONE', 'XOUT', 'XP', 'XPEL', 'XPER', 'XPEV', 'XPL', 'XPO', 'XPOA-U', 'XPOA-WS', 'XPOA', 'XRAY', 'XRX', 'XSHD', 'XSHQ', 'XSMO', 'XSPA', 'XSVM', 'XTLB', 'XTNT', 'XWEB', 'XXII', 'XYF', 'XYL', 'XYLD', 'XYLG', 'Y', 'YAC-U', 'YAC-WS', 'YAC', 'YALA', 'YCBD', 'YCBD_A', 'YELP', 'YETI', 'YEXT', 'YGMZ', 'YI', 'YJ', 'YLD', 'YLDE', 'YMAB', 'YMTX', 'YNDX', 'YOLO', 'YORW', 'YPF', 'YQ', 'YRCW', 'YRD', 'YSAC', 'YSACU', 'YSACW', 'YSG', 'YTEN', 'YTRA', 'YUM', 'YUMC', 'YVR', 'YY', 'Z', 'ZAGG', 'ZBH', 'ZBRA', 'ZCAN', 'ZCMD', 'ZDEU', 'ZDGE', 'ZEAL', 'ZEN', 'ZEUS', 'ZEXIT', 'ZG', 'ZGBR', 'ZGNX', 'ZGYH', 'ZGYHR', 'ZGYHU', 'ZGYHW', 'ZHOK', 'ZI', 'ZIEXT', 'ZIG', 'ZION', 'ZIONL', 'ZIONN', 'ZIONO', 'ZIONP', 'ZIOP', 'ZIXI', 'ZJPN', 'ZKIN', 'ZLAB', 'ZM', 'ZNGA', 'ZNH', 'ZNTEU', 'ZNTL', 'ZOM', 'ZS', 'ZSAN', 'ZTO', 'ZTR', 'ZTS', 'ZUMZ', 'ZUO', 'ZVO', 'ZXIET', 'ZYME', 'ZYNE', 'ZYXI']
# DE = [""]
# HK = [""]
HU = ['4IG', 'AKKO', 'ALTEO', 'ANY', 'APPENINN', 'AUTOWALLIS', 'BIF', 'CIGPANNONIA', 'CYBERG', 'DELTA', 'DMKER', 'DUNAHOUSE', 'EHEP', 'ENEFI', 'FORRAS_OE', 'FORRAS_T', 'FUTURAQUA', 'GLOSTER', 'GSPARK', 'KARPOT', 'KULCSSOFT', 'MASTERPLAST', 'MEGAKRAN', 'MKBBANK', 'MOL', 'MTELEKOM', 'NORDTELEKOM', 'NUTEX', 'OPUS', 'ORMESTER', 'OTP', 'OTT1', 'PANNERGY', 'PENSUM', 'RABA', 'RICHTER', 'SET', 'SUNDELL', 'TAKAREKJZB', 'UBM', 'WABERERS', 'ZWACK']
# JP = [""]
# UK = [""]

if __name__ == "__main__":
	try:
		# print(str(datetime.now().date().strftime("%d-%m-%Y")) + str(datetime.now().time().strftime("%H-%M-%S")))
		# with open('stock_data.csv', newline='') as d, open('stock_ind_data.csv', newline='') as i, open('stock_history.csv', newline='') as h, open('stock_balance.txt') as b:
			# with open('stock_ind_data.csv', newline='') as i:
				# with open('stock_history.csv', newline='') as h:
				#	 with open('stock_balance.txt') as b:
			# da = csv.reader(d)
			# ind = csv.reader(i)
			# hi = csv.reader(h)
			# ba = b.read()
			# print(ba)
			# bala = {"PL": 0, "US": 0, "DE":  0, "HK": 0, "HU": 0, "JP": 0, "UK": 0}
			# for line in ba:
			#	 print(line)
			# ba = {}
			# for line in b:
			#	 (key, val) = line.split()
			#	 ba[key] = val
			# print(ba)
		butt = open('button_theme.txt', "r")
		back = open('background_theme.txt', 'r')
		summary = open('daily_summary.txt', 'r')
		with open('stock_history.csv', newline='') as h, open('finance_history.csv', newline='') as f:
			# butt = open('button_theme.txt', "r")
			# back = open('background_theme.txt', 'r')
			hi = csv.reader(h)
			fi = csv.reader(f)
			divs = {}
			for line in fi:
				try:
					if line[2] == "Dywidendy" and float(line[4]) >= 0 and line[7] is not None and line[7] != '':
						divs[line[3]] = float(line[7])
				except IndexError:
					pass
			# print(divs)
			summ = summary.read()
			but = butt.read()
			backg = back.read()
			dbase = UserDatabase(list(hi), divs) # list(da), list(ind), ba
			app = QApplication(sys.argv)
			load = LoadingWindow()
			load.show()
			# TESTOWANIE - DO ODKOMENTOWANIA
			try:
				test = Stock('test connection', 'PL')
				test.importstock("PKN")
				load.hide()
				i = MainWindow(but, backg, summ)
				i.show()
			except requests.exceptions.ConnectionError:
				load.hide()
				j = ErrWindow("Connection to stooq.com could not be established.\nCheck your connection and access to stooq.com\nand try again later.")
				j.show()
			sys.exit(app.exec_())
	except (FileNotFoundError, AttributeError):  # , pd.errors.EmptyDataError): # indexerror usunac
		dbase = UserDatabase()
		app = QApplication(sys.argv)
		load = LoadingWindow()
		load.show()
		try:
			test = Stock('test connection', 'PL')
			test.importstock("PKN")
			load.hide()
			i = MainWindow()
			i.show()
		except requests.exceptions.ConnectionError:
			load.hide()
			j = ErrWindow("Connection to stooq.com could not be established.\nCheck your connection and access to stooq.com\nand try again later.")
			j.show()
		sys.exit(app.exec_())
	# except (UnboundLocalError, ValueError, IndexError): # file corrupted
	#	 app = QApplication(sys.argv)
	#	 j = ErrWindow("File corrupted! Check the stock_history.csv file for typos.")
	#	 j.show()
	#	 j.resize(300, 70)
	#	 sys.exit(app.exec())
