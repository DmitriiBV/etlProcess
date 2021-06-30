createTableCards = '''
CREATE TABLE if not exists cards(
  card_num varchar(128), 
  account varchar(128), 
  create_dt date, 
  update_dt date
)
'''

createTableV_Cards = '''
CREATE VIEW if not exists v_cards AS 
SELECT 
  card_num, 
  account 
FROM 
  cards
'''

showTableCards = '''
SELECT 
  * 
FROM 
  cards
'''

createTableAccounts = '''
CREATE TABLE if not exists accounts(
  account varchar(128), 
  valid_to date, 
  client integer, 
  create_dt date, 
  update_dt date
)
'''

createTableV_Accounts = '''
CREATE VIEW if not exists v_accounts AS 
SELECT 
  account, 
  valid_to, 
  client 
FROM 
  accounts
'''

showTableAccounts = '''
SELECT 
  * 
FROM 
  accounts
'''

createTableClients = '''
CREATE TABLE if not exists clients(
  client_id integer, 
  last_name varchar(128), 
  first_name varchar(128), 
  patronymic varchar(128), 
  date_of_birth date, 
  passport_num varchar(128), 
  passport_valid_to date, 
  phone varchar(128), 
  create_dt date, 
  update_dt date
)
'''

createTableV_Clients = '''
CREATE VIEW if not exists v_clients AS 
SELECT 
  client_id, 
  last_name, 
  first_name, 
  patronymic, 
  date_of_birth, 
  passport_num, 
  passport_valid_to, 
  phone 
FROM 
  clients
'''

showTableClients = '''
SELECT 
  * 
FROM 
  clients
'''

createTableTerminals = '''
CREATE TABLE if not exists terminals(
  terminal_id varchar(128), 
  terminal_type varchar(128), 
  terminal_city varchar(128), 
  terminal_address varchar(128), 
  effective_from datetime default current_timestamp, 
  effective_to datetime default (
    datetime('9999-12-31 23:59:59')
  ), 
  deleted_flg integer default 0
)
'''

createTableV_Terminals = '''
CREATE VIEW if not exists v_terminals AS 
SELECT 
  terminal_id, 
  terminal_type, 
  terminal_city, 
  terminal_address 
FROM 
  terminals 
WHERE 
  deleted_flg = 0 
  AND current_timestamp BETWEEN effective_from 
  AND effective_to 
ORDER BY 
  terminal_id
'''

createTablePassport_blacklist = '''
CREATE TABLE if not exists passport_blacklist(
  passport_num varchar(128), 
  entry_dt date, 
  effective_from datetime default current_timestamp, 
  effective_to datetime default (
    datetime('9999-12-31 23:59:59')
  ), 
  deleted_flg integer default 0
)
'''

createTableV_Passport_blacklist = '''
CREATE VIEW if not exists v_passport_blacklist AS 
SELECT 
  passport_num, 
  entry_dt 
FROM 
  passport_blacklist 
WHERE 
  deleted_flg = 0 
  AND current_timestamp BETWEEN effective_from 
  AND effective_to
'''

createTableTransactions = '''
CREATE TABLE if not exists transactions(
  trans_id varchar(128), 
  trans_date datetime, 
  card_num varchar(128), 
  oper_type varchar(128), 
  amt decimal, 
  oper_result varchar(128), 
  terminal varchar(128)  
)
'''

createTableV_Transactions = '''
CREATE VIEW if not exists v_transactions AS 
SELECT 
  trans_id, 
  trans_date, 
  card_num, 
  oper_type, 
  amt, 
  oper_result, 
  terminal 
FROM 
  transactions
'''

createTableReportingList = '''
  CREATE TABLE if not exists reporting_list(
    event_dt varchar(128),
    passport varchar(128),
    fio varchar(128),
    phone varchar(128),
    event_type varchar(128),
    report_dt datetime
  )
''' 