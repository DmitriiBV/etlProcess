#Совершение операции при просроченном или заблокированном паспорте
request1 = '''
	SELECT t4.trans_date AS event_dt,
	       t1.passport_num AS passport,
	       t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic AS fio,
	       t1.phone AS phone,
	       'Совершение операции при просроченном или заблокированном паспорте' AS event_type,
	       date('now') AS report_dt
	FROM v_clients t1
	INNER JOIN v_accounts t2 ON t1.client_id = t2.client
	INNER JOIN v_cards t3 ON t2.account = t3.account
	INNER JOIN v_transactions t4 ON t3.card_num = t4.card_num
	LEFT JOIN v_passport_blacklist t5 ON t5.passport_num = t1.passport_num
	WHERE (t5.entry_dt <= t4.trans_date
	       OR t1.passport_valid_to <= t4.trans_date)
	  AND t4.oper_result = 'SUCCESS'
	ORDER BY t4.trans_date
'''
#Совершение операции при недействующем договоре
request2 = '''
	SELECT t4.trans_date AS event_dt,
	       t1.passport_num AS passport,
	       t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic AS fio,
	       t1.phone AS phone,
	       'Совершение операции при недействующем договоре' AS event_type,
	       date('now') AS report_dt
	FROM v_clients t1
	INNER JOIN v_accounts t2 ON t1.client_id = t2.client
	INNER JOIN v_cards t3 ON t2.account = t3.account
	INNER JOIN v_transactions t4 ON t3.card_num = t4.card_num
	WHERE (t2.valid_to <= t4.trans_date)
	  AND t4.oper_result = 'SUCCESS'
	ORDER BY t4.trans_date
'''
#Совершение операций в разных городах в течение одного часа
request3 = '''
	SELECT table1.dt AS event_dt,
	       table1.passport AS passport,
	       table1.fio AS fio,
	       table1.phone AS phone,
	       'Совершение операций в разных городах в течение одного часа' AS event_type,
	       date('now') AS report_dt
	FROM
	  (SELECT t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic AS fio,
	          t4.trans_date AS dt,
	          t1.passport_num AS passport,
	          t1.phone AS phone,
	          t5.terminal_city AS city,
	          lag(t4.trans_date, 1, 0) OVER() AS p_dt,
	          lag(t5.terminal_city, 1, 0) OVER() AS p_city,
	          lag(t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic, 1, 0) OVER(
	                                                                                       ORDER BY t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic) AS p_fio,
	          lead(t4.trans_date, 1, 0) OVER() AS f_dt,
	          lead(t5.terminal_city, 1, 0) OVER() AS f_city,
	          lead(t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic, 1, 0) OVER(
	                                                                                        ORDER BY t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic) AS f_fio
	   FROM v_clients t1
	   INNER JOIN v_accounts t2 ON t1.client_id = t2.client
	   INNER JOIN v_cards t3 ON t2.account = t3.account
	   INNER JOIN v_transactions t4 ON t3.card_num = t4.card_num
	   INNER JOIN v_terminals t5 ON t4.terminal = t5.terminal_id
	   WHERE t4.oper_result = 'SUCCESS'
	     AND fio IN
	       (SELECT table1.fio
	        FROM
	          (SELECT t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic AS fio,
	                  t5.terminal_city AS city
	           FROM v_clients t1
	           INNER JOIN v_accounts t2 ON t1.client_id = t2.client
	           INNER JOIN v_cards t3 ON t2.account = t3.account
	           INNER JOIN v_transactions t4 ON t3.card_num = t4.card_num
	           INNER JOIN v_terminals t5 ON t4.terminal = t5.terminal_id
	           WHERE t4.oper_result = 'SUCCESS'
	           GROUP BY fio,
	                    city
	           ORDER BY fio,
	                    city,
	                    t4.trans_date) table1
	        GROUP BY table1.fio
	        HAVING count(table1.city) > 1)
	   ORDER BY fio,
	            city,
	            dt) table1
	WHERE (table1.city <> table1.p_city
	       AND table1.fio == table1.p_fio
	       AND abs(strftime('%s', table1.dt) - strftime('%s', table1.p_dt)) <= 3600)
	  OR (table1.city <> table1.f_city
	      AND table1.fio == table1.f_fio
	      AND abs(strftime('%s', table1.dt) - strftime('%s', table1.f_dt)) <= 3600)
	ORDER BY table1.dt
'''
#Попытка подбора суммы. В течение 20 минут проходит более 3х операций
#со следующим шаблоном – каждая последующая меньше предыдущей, при этом
#отклонены все кроме последней. Последняя операция (успешная) в такой цепочке
#считается мошеннической
request4 = '''
	SELECT t1.dt AS event_dt,
	       t1.passport AS passport,
	       t1.fio AS fio,
	       t1.phne AS phone,
	       'Попытка подбора суммы' AS event_type,
	       date('now') AS report_dt
	FROM
	  (SELECT t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic AS fio,
	          t1.passport_num AS passport,
	          t1.phone AS phne,
	          t3.card_num AS c_num,
	          t4.trans_date AS dt,
	          t4.oper_result AS op_r,
	          t4.amt AS amt,
	          lag(t3.card_num, 1, 0) OVER(
	                                      ORDER BY t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic, t3.card_num) AS c_num_1,
	          lag(t4.trans_date, 1, 0) OVER(
	                                        ORDER BY t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic, t3.card_num, t4.trans_date) AS dt_1,
	          lag(t4.oper_result, 1, 0) OVER(
	                                         ORDER BY t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic, t3.card_num, t4.trans_date) AS op_r_1,
	          lag(t4.amt, 1, 0) OVER(
	                                 ORDER BY t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic, t3.card_num, t4.trans_date) AS amt_1,
	          lag(t3.card_num, 2, 0) OVER(
	                                      ORDER BY t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic, t3.card_num) AS c_num_2,
	          lag(t4.trans_date, 2, 0) OVER(
	                                        ORDER BY t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic, t3.card_num, t4.trans_date) AS dt_2,
	          lag(t4.oper_result, 2, 0) OVER(
	                                         ORDER BY t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic, t3.card_num, t4.trans_date) AS op_r_2,
	          lag(t4.amt, 2, 0) OVER(
	                                 ORDER BY t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic, t3.card_num, t4.trans_date) AS amt_2,
	          lag(t3.card_num, 3, 0) OVER(
	                                      ORDER BY t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic, t3.card_num) AS c_num_3,
	          lag(t4.trans_date, 3, 0) OVER(
	                                        ORDER BY t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic, t3.card_num, t4.trans_date) AS dt_3,
	          lag(t4.oper_result, 3, 0) OVER(
	                                         ORDER BY t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic, t3.card_num, t4.trans_date) AS op_r_3,
	          lag(t4.amt, 3, 0) OVER(
	                                 ORDER BY t1.last_name || ' ' || t1.first_name || ' ' || t1.patronymic, t3.card_num, t4.trans_date) AS amt_3
	   FROM v_clients t1
	   INNER JOIN v_accounts t2 ON t1.client_id = t2.client
	   INNER JOIN v_cards t3 ON t2.account = t3.account
	   INNER JOIN v_transactions t4 ON t3.card_num = t4.card_num
	   INNER JOIN v_terminals t5 ON t4.terminal = t5.terminal_id
	   WHERE c_num IN
	       (SELECT card_num
	        FROM v_cards
	        GROUP BY card_num)
	     AND (t4.oper_type = 'WITHDRAW'
	          OR t4.oper_type = 'PAYMENT')
	   ORDER BY fio,
	            c_num,
	            dt) t1
	WHERE t1.op_r = 'SUCCESS'
	  AND t1.op_r_1 = 'REJECT'
	  AND t1.op_r_2 = 'REJECT'
	  AND t1.op_r_3 = 'REJECT'
	  AND (t1.amt < t1.amt_1)
	  AND (t1.amt_1 < t1.amt_2)
	  AND (t1.amt_2 < t1.amt_3)
	  AND abs(strftime('%s', t1.dt) - strftime('%s', t1.dt_3)) <= 1200
'''