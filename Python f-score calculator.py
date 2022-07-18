'''
Fixed the previous problem of unable to scrape financial data hidden behind dropdowns.
Selenium was used to artificially interact with the web page by 'clicking' on the 'expand all' button to expand all dropdowns.
BeautifulSoup was then used to webscrape all financial data
'''

import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
from bs4 import BeautifulSoup as bs
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd
import numpy as np

import os
os.chdir('D:/Random projects/Stock Market')

np.set_printoptions(suppress=True)

Ticker = 'ASX'
company = Ticker.upper()

op = webdriver.ChromeOptions()
op.add_argument('headless')

driver_path = <insert driver path>
driver = webdriver.Chrome(service = Service(driver_path), options = op)
driver.get('https://finance.yahoo.com/quote/'+company+'/financials?p='+company)

#Script goes too fast, broswer needs time to load so let it wait
WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Col1-1-Financials-Proxy"]/section/div[2]/button'))).click()

html = driver.page_source
soup = bs(html, features = 'html.parser')

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
driver.get('https://finance.yahoo.com/quote/'+company+'/balance-sheet?p='+company)

WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Col1-1-Financials-Proxy"]/section/div[2]/button'))).click()

html = driver.page_source
soup = bs(html, features = 'html.parser')

balance_sheet_results = []
for row in soup.select('.fi-row'):
        balance_sheet_results.append([i.text for i in row.select('[title],[data-test="fin-col"]')])

balance_sheet_results = pd.DataFrame(balance_sheet_results)
for col in balance_sheet_results.columns[1:]:
    balance_sheet_results[col] = balance_sheet_results[col].apply(lambda x: float(x.replace(',','').replace('-','0')))


title = [i.text for i in soup.select('.BdB')][0:4]
title = pd.DataFrame([title])

title_row = pd.concat([pd.DataFrame(['Breakdown']),title],axis = 1)
title_row.columns = range(0,5)

balance_sheet_table = pd.concat([title_row,balance_sheet_results], axis = 0, ignore_index = True)
balance_sheet_table = balance_sheet_table.transpose()
balance_sheet_table.columns = balance_sheet_table.iloc[0,:]
balance_sheet_table = balance_sheet_table[1:]
balance_sheet_table_dup = pd.concat([pd.DataFrame(balance_sheet_table.iloc[0,:]).transpose(),balance_sheet_table], axis = 0, ignore_index = True)
balance_sheet_table_dup.iloc[0,0] = 'ttm'

###############Cash Flow Statement################
driver.get('https://finance.yahoo.com/quote/'+company+'/cash-flow?p='+company)

WebDriverWait(driver,20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="Col1-1-Financials-Proxy"]/section/div[2]/button'))).click()

html = driver.page_source
soup = bs(html, features = 'html.parser')

cash_flow_results = []
for row in soup.select('.fi-row'):
        cash_flow_results.append([i.text for i in row.select('[title],[data-test="fin-col"]')])

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
    balance_sheet_table_dup, how = 'left', on = 'Breakdown').merge(
        cash_flow_table, how = 'left', on = 'Breakdown')
        
##################Piotroski f-score #####################
f_score_analysis = pd.DataFrame(full_table['Breakdown'])

# Profitability
f_score_analysis['positive_profit'] = np.where(full_table['Net Income'] >= 0, 1, 0)
full_table['roa'] = full_table['Net Income']/full_table['Total Assets']
f_score_analysis['roa_change'] = np.where(full_table['roa'] >= 0, 1, 0)
f_score_analysis['operating_cf'] = np.where(full_table['Operating Cash Flow'] >= 0, 1, 0)
f_score_analysis['ocf_more_than_net_income'] = np.where(full_table['Operating Cash Flow'] >= full_table['Net Income'], 1, 0)

# Leverage, liquidity & source of funds
f_score_analysis['lower_ltd'] = np.where(full_table['Long Term Debt'] <= full_table['Long Term Debt'].shift(-1), 1, 0)
full_table['current_ratio'] = full_table['Current Assets']/full_table['Current Liabilities']
f_score_analysis['higher_cr'] = np.where(full_table['current_ratio'] >= full_table['current_ratio'].shift(-1), 1, 0)
f_score_analysis['dilution'] = np.where(full_table['Share Issued'] >= full_table['Share Issued'], 0, 1)

# Operating Efficiency
f_score_analysis['higher_margin'] = np.where(full_table['Gross Profit'] >= full_table['Gross Profit'].shift(-1), 1, 0)
full_table['asset_turnover'] = full_table['Total Revenue']/((full_table['Total Assets']+full_table['Total Assets'].shift(-1))/2)
f_score_analysis['higher_asset_turnover'] = np.where(full_table['asset_turnover'] >= full_table['asset_turnover'].shift(-1), 1, 0)

f_score_analysis['f_score'] = f_score_analysis['positive_profit'] + f_score_analysis['roa_change'] + f_score_analysis['operating_cf']+ f_score_analysis['ocf_more_than_net_income']+ f_score_analysis['lower_ltd'] + f_score_analysis['higher_cr']+ f_score_analysis['dilution'] + f_score_analysis['higher_margin'] + f_score_analysis['higher_asset_turnover'] 

f_score_analysis['quality'] = np.where(
    f_score_analysis['f_score'] >= 8, 'Good Investment',
    np.where((f_score_analysis['f_score'] >= 5) & 
             (f_score_analysis['f_score'] <= 8),
             'Risky Investment','Bad Investment'))
    
f_score_analysis['name'] = driver.find_element(By.XPATH, '//*[@id="quote-header-info"]/div[2]/div[1]/div[1]/h1').text

f_score_analysis = f_score_analysis.reindex(columns = ['name', 'f_score', 'quality']+ 
                            list(col for col in f_score_analysis.columns if col != ['name', 'f_score', 'quality']))
