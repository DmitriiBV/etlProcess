import sqlite3, sys, os, fnmatch

sys.path.append("py_scripts/")
from py_scripts_functions import initTableSCD1, initTableSCD2, uploadToDBase, showTable, createReport

if not os.path.exists('archive'):
	os.makedirs('archive')

#списки названий файлов
terminalsList = []
transactionsList = []
passportBlacklistList = []

listOfFiles = os.listdir('.')

for file in listOfFiles:
    if fnmatch.fnmatch(file, 'terminals_????????.xlsx'):
            terminalsList.append(file)
    if fnmatch.fnmatch(file, 'transactions_????????.txt'):
            transactionsList.append(file)
    if fnmatch.fnmatch(file, 'passport_blacklist_????????.xlsx'):
            passportBlacklistList.append(file)

con = sqlite3.connect('dataBase.db')

#создание таблиц (представлений) Cards, Accounts, Clients с их последующим заполнением
initTableSCD1(con)
#создание таблиц (представлений) Terminals, Passport_blacklist, Transactions, ReportingList
initTableSCD2(con)
#загрузка выгруженных данных в хранилище
uploadToDBase(con, terminalsList, transactionsList, passportBlacklistList)
#построение отчета с сохранением в файл
createReport(con)

con.close()