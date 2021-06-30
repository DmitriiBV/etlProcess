import sqlite3, datetime, time, json, shutil, sys
import pandas as pd
import os, fnmatch

sys.path.append("sql_scripts/")
from sql_scripts_fill_to_tables_SCD1 import fillToTableCards, fillToTableAccounts, fillToTableClients
from sql_scripts_create_tables import createTableCards, createTableV_Cards, showTableCards
from sql_scripts_create_tables import createTableAccounts, createTableV_Accounts, showTableAccounts
from sql_scripts_create_tables import createTableClients, createTableV_Clients, showTableClients
from sql_scripts_create_tables import createTableTerminals, createTableV_Terminals
from sql_scripts_create_tables import createTablePassport_blacklist, createTableV_Passport_blacklist
from sql_scripts_create_tables import createTableTransactions, createTableV_Transactions, createTableReportingList
from sql_scripts_requests_to_report import request1, request2, request3, request4

# Сброс ограничений на количество выводимых рядов
pd.set_option('display.max_rows', None) 

# Сброс ограничений на число столбцов
#pd.set_option('display.max_columns', None) 

# Сброс ограничений на количество символов в записи
pd.set_option('display.max_colwidth', None)

def initTableSCD1(con):
	cursor = con.cursor()
	cursor.execute(createTableCards)
	cursor.execute(createTableV_Cards)
	cursor.execute(showTableCards)
	if len(cursor.fetchall()) == 0:
		cursor.executescript(fillToTableCards)
	con.commit()

	cursor.execute(createTableAccounts)
	cursor.execute(createTableV_Accounts)
	cursor.execute(showTableAccounts)
	if len(cursor.fetchall()) == 0:
		cursor.executescript(fillToTableAccounts)
	con.commit()

	cursor.execute(createTableClients)
	cursor.execute(createTableV_Clients)
	cursor.execute(showTableClients)
	if len(cursor.fetchall()) == 0:
		cursor.executescript(fillToTableClients)
	con.commit()

def initTableSCD2(con):
	cursor = con.cursor()
	cursor.execute(createTableTerminals)
	cursor.execute(createTableV_Terminals)
	cursor.execute(createTablePassport_blacklist)
	cursor.execute(createTableV_Passport_blacklist)
	cursor.execute(createTableTransactions)
	cursor.execute(createTableV_Transactions)
	cursor.execute(createTableReportingList)

#для копирования даты из названия файла
def cutDate(fileName):
	temp = ''
	if fileName.find('terminals_') != -1:
		temp = fileName.replace('terminals_','').replace('.xlsx','')
	elif fileName.find('transactions_') != -1:
		temp = fileName.replace('transactions_','').replace('.txt','')
	elif fileName.find('passport_blacklist_') != -1:
		temp = fileName.replace('passport_blacklist_','').replace('.xlsx','')
	else:
		return ''
	date = datetime.datetime.strptime(temp, '%d%m%Y')
	return date

#добавление данных в таблицу Terminals
def addTerminals(con, terminalData, fileName):
	cursor = con.cursor()
	date = cutDate(fileName)
	for item in terminalData:		
		cursor.execute(f'''
		UPDATE terminals
		SET effective_to = datetime('{date}', '-1 second')
		WHERE terminal_id = ? AND terminal_type = ? AND effective_to = datetime('9999-12-31 23:59:59')
		''', [item['terminal_id'], item['terminal_type']])		
		cursor.execute('INSERT INTO terminals(terminal_id, terminal_type, terminal_city, terminal_address, effective_from) VALUES(?, ?, ?, ?, ?)',
						[item['terminal_id'], item['terminal_type'], item['terminal_city'], item['terminal_address'], f'{date}'])
	con.commit()

#добавление данных в таблицу PassportBlacklist
def addPassportBlacklist(con, passportBlacklistData, fileName):
	cursor = con.cursor()
	date = cutDate(fileName)
	for item in passportBlacklistData:
		cursor.execute(f'''
		SELECT
			*
		FROM passport_blacklist
		WHERE passport_num = ?
		AND entry_dt = ?;''', [item['passport'], datetime.date.fromtimestamp(item['date']/1000)])
		if len(cursor.fetchall()) == 0:
			cursor.execute('''
			INSERT INTO passport_blacklist (passport_num, entry_dt, effective_from)
						VALUES(?, ?, ?);
			''', [item['passport'], datetime.date.fromtimestamp(item['date']/1000), f'{date}'])
	con.commit()

#добавление данных в таблицу Transactions
def addTransactions(con, transactionsData):
	cursor = con.cursor()
	for item in transactionsData:		
		cursor.execute('''
		INSERT INTO transactions (trans_id, trans_date, card_num, oper_type, amt, oper_result, terminal)
					VALUES(?, ?, ?, ?, ?, ?, ?);
		''', [item['transaction_id'], item['transaction_date'], 
			item['card_num'], item['oper_type'], item['amount'].replace(',','.'), item['oper_result'], 
			item['terminal']])
	con.commit()

#добавление данных в таблицу ReportList (витрина отчетности)
def addReportList(con, reportListData):
	cursor = con.cursor()
	for item in reportListData:		
		cursor.execute('''
		INSERT INTO reporting_list (event_dt, passport, fio, phone, event_type, report_dt)
					VALUES(?, ?, ?, ?, ?, ?);
		''', [item['event_dt'], item['passport'], item['fio'], 
		item['phone'], item['event_type'], item['report_dt']])
	con.commit()

#вспомогательная функция для показа таблицы в консоли
def showTable(con, tableName):
	print('-_'*20+'\n'+tableName+'\n'+'-_'*20)
	df = pd.read_sql_query(f'select * from {tableName}', con=con)
	if not df.empty:
		print(df)

#вспомогательная функция для переименования файла
def renameFile(fileName):
	return f'{fileName}'+'.backup'

#загрузка данных в хранилище
def uploadToDBase(con, terminalsList, transactionsList, passportBlacklistList):
	for item in terminalsList:
		excel_data_df = pd.read_excel(item, sheet_name='terminals').to_json(orient='records', force_ascii = False)
		decoded_hand = json.loads(excel_data_df)
		addTerminals(con, decoded_hand, item)
		shutil.move(item, f'archive\\{renameFile(item)}')

	for item in transactionsList:
		txt_data_df = pd.read_table(item, sep=';').to_json(orient='records',  force_ascii = False)
		decoded_hand = json.loads(txt_data_df)
		addTransactions(con, decoded_hand)
		shutil.move(item, f'archive\\{renameFile(item)}')

	for item in passportBlacklistList:
		excel_data_df = pd.read_excel(item, sheet_name='blacklist').to_json(orient='records', date_format = 'epoch', force_ascii = False)
		decoded_hand = json.loads(excel_data_df)
		addPassportBlacklist(con, decoded_hand, item)
		shutil.move(item, f'archive\\{renameFile(item)}')

#построение отчета и сохранение его в файл excel
def createReport(con):
	requestList = []
	requestList.append(request1)
	requestList.append(request2)
	requestList.append(request3)
	requestList.append(request4)
	for item in requestList:	
		df = pd.read_sql_query(item, con=con)
		if not df.empty:
			data_df = df.to_json(orient='records', force_ascii = False)
			decoded_data_df = json.loads(data_df)
			addReportList(con, decoded_data_df)

	curDate = datetime.date.today()
	tempDate = str(curDate).replace('-','')
	tempDate = f'{tempDate[6]}' + f'{tempDate[7]}' \
			 + f'{tempDate[4]}' + f'{tempDate[5]}' \
			 + f'{tempDate[0]}' + f'{tempDate[1]}' + f'{tempDate[2]}' + f'{tempDate[3]}'

	df = pd.read_sql_query(f'''
			SELECT * 
			FROM reporting_list
			WHERE report_dt = '{curDate}'
		''', con=con)
	if not df.empty:
		writer = pd.ExcelWriter(f'report_{tempDate}.xlsx')
		df.to_excel(writer, index = False)
		writer.save()