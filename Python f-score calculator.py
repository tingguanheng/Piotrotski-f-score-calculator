'''
My own attempt at creating Yahoo Finance API by adapting the codes from StackOverflow by 'QHarr'
https://stackoverflow.com/questions/58315274/r-web-scraping-yahoo-finance-after-2019-change
Adapting code because Python code provided does not work
'''

import requests as re
from bs4 import BeautifulSoup as bs
import pandas as pd

import os

os.chdir('D:/Random projects/Stock Market')

Ticker = 'AAPL'
company = Ticker.upper()

## Vital clue to fixing the problem, some form of authentication is required
header = {[insert own header]}
###############Income Statement################
income_statement = re.get('https://finance.yahoo.com/quote/'+company+'/financials?p='+company, headers=header)
soup = bs(income_statement.content, features = 'html.parser')

income_statement_results = []
## Within inspect, there is an element covering the entire table row that has "fi-row", use .fi-row
for row in soup.select('.fi-row'):
## Within the subelement, there are cells that can be identified with "title" (for breakdown) and "data-test=fin-col" (for values)
## .text only pulls out actual values in <span>
    income_statement_results.append([i.text for i in row.select('[title],[data-test="fin-col"]')])

income_statement_results = pd.DataFrame(income_statement_results)
for col in income_statement_results.columns[1:]:
    income_statement_results[col] = income_statement_results[col].apply(lambda x: float(x.replace(',','').replace('-','0')))

## No common identification in header
## At best use "BdB" to pull out dates, "Breakdown" must be hardcoded in
title = [i.text for i in soup.select('.BdB')][0:5]
title = pd.DataFrame([title])

title_row = pd.concat([pd.DataFrame(['Breakdown']),title],axis = 1)
title_row.columns = range(0,6)

Income_statement_table = pd.concat([title_row,income_statement_results], axis = 0, ignore_index = True)
Income_statement_table = Income_statement_table.transpose()
Income_statement_table.columns = Income_statement_table.iloc[0,:]
Income_statement_table = Income_statement_table[1:]


###############Balance Sheet################
balance_sheet = re.get('https://finance.yahoo.com/quote/'+company+'/balance-sheet?p='+company, headers=header)
soup = bs(balance_sheet.content, features = 'html.parser')

balance_sheet_results = []
for row in soup.select('.fi-row'):
        balance_sheet_results.append([i.text for i in row.select('[title],[data-test="fin-col"]')])

balance_sheet_results = pd.DataFrame(balance_sheet_results)
for col in balance_sheet_results.columns[1:]:
    balance_sheet_results[col] = balance_sheet_results[col].apply(lambda x: float(x.replace(',','').replace('-','0')))


title = [i.text for i in soup.select('.BdB')][0:5]
title = pd.DataFrame([title])

title_row = pd.concat([pd.DataFrame(['Breakdown']),title],axis = 1)
title_row.columns = range(0,6)

balance_sheet_table = pd.concat([title_row,balance_sheet_results], axis = 0, ignore_index = True)
balance_sheet_table = balance_sheet_table.transpose()
balance_sheet_table.columns = balance_sheet_table.iloc[0,:]
balance_sheet_table = balance_sheet_table[1:]

###############Cash Flow Statement################
cash_flow = re.get('https://finance.yahoo.com/quote/'+company+'/cash-flow?p='+company, headers=header)
soup = bs(cash_flow.content, features = 'html.parser')

cash_flow_results = []
for row in soup.select('.fi-row'):
        balance_sheet_results.append([i.text for i in row.select('[title],[data-test="fin-col"]')])

cash_flow_results = pd.DataFrame(cash_flow_results)
for col in cash_flow_results.columns[1:]:
    cash_flow_results[col] = cash_flow_results[col].apply(lambda x: float(x.replace(',','').replace('-','0')))


title = [i.text for i in soup.select('.BdB')][0:5]
title = pd.DataFrame([title])

title_row = pd.concat([pd.DataFrame(['Breakdown']),title],axis = 1)
title_row.columns = range(0,6)

cash_flow_table = pd.concat([title_row,cash_flow_results], axis = 0, ignore_index = True)
cash_flow_table = cash_flow_table.transpose()
cash_flow_table.columns = cash_flow_table.iloc[0,:]
cash_flow_table = cash_flow_table[1:]

################Full table###############
full_table = Income_statement_table.merge(
    balance_sheet_table, how = 'left', on = 'Breakdown').merge(
        cash_flow_table, how = 'left', on = 'Breakdown')

