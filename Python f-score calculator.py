''' Python Piotrotski f-score calculator'''
'''
Note:
I've checked the table values of YahooFinancials module with
Yahoo Finance website itself and found out that many values
are wrong. 

This added with the fact that webscraping with Python is far
beyond my skill level as of now means the webscrape codes
should be taken with a pinch of salt.

This CANNOT be used as an actual product but should be viewed 
as a display of Python data manipulation skillset.

Check out my R script for the usable product that I actually use
'''

import pandas as pd
import json
import numpy as np
from yahoofinancials import YahooFinancials

ticker = 'AAPL'
rawdata = YahooFinancials(ticker)

'''Income Statement'''

income_Statement_data_qt = rawdata.get_financial_stmts('annual', 'income')
latest_is = pd.DataFrame(income_Statement_data_qt['incomeStatementHistory'][ticker][0])
last_year_is = pd.DataFrame(income_Statement_data_qt['incomeStatementHistory'][ticker][1])
two_years_ago_is = pd.DataFrame(income_Statement_data_qt['incomeStatementHistory'][ticker][2])
income_statement = pd.concat([latest_is,last_year_is,two_years_ago_is], axis = 1).transpose()
income_statement['netIncome_is'] = income_statement['netIncome']
income_statement = income_statement.drop(columns = 'netIncome')

'''Balance Sheet'''

balance_Sheet_data_qt = rawdata.get_financial_stmts('annual','balance')
latest_bs = pd.DataFrame(balance_Sheet_data_qt['balanceSheetHistory'][ticker][0])
last_year_bs = pd.DataFrame(balance_Sheet_data_qt['balanceSheetHistory'][ticker][1])
two_years_ago_bs = pd.DataFrame(balance_Sheet_data_qt['balanceSheetHistory'][ticker][2])
bs = pd.concat([latest_bs,last_year_bs,two_years_ago_bs], axis = 1).transpose()

'''Statement of Cash Flow'''

cash_flow_data_qt = rawdata.get_financial_stmts('annual','cash')
latest_cf = pd.DataFrame(cash_flow_data_qt['cashflowStatementHistory'][ticker][0])
last_year_cf = pd.DataFrame(cash_flow_data_qt['cashflowStatementHistory'][ticker][1])
two_years_ago_cf = pd.DataFrame(cash_flow_data_qt['cashflowStatementHistory'][ticker][2])
cf = pd.concat([latest_cf,last_year_cf,two_years_ago_cf], axis = 1).transpose()
cf['netIncome_cf'] = cf['netIncome']
cf = cf.drop(columns = ['netIncome'])

df = pd.concat([income_statement,bs,cf], axis = 1)
df['positive_net_income'] = np.where(df['netIncome_is'] > 0, 1, 0)
df['positive_roa'] = np.where((df['netIncome_is']/df['totalAssets']) > 0, 1, 0)
df['positive_ocf'] = np.where(df['totalCashFromOperatingActivities'] > 0, 1, 0)
df['ocf_more_than_net_income'] = np.where((df['totalCashFromOperatingActivities'] > df['netIncome_is']), 1, 0)
df['long_term_debt_ratio_improvement'] = np.where((df['longTermDebt']/df['totalAssets']) < (df['longTermDebt'].shift(-1)/df['totalAssets'].shift(-1)), 1, 0)
df['current_ratio_improvement'] = np.where(((df['totalCurrentAssets']/df['totalCurrentLiabilities']) > df['totalCurrentAssets'].shift(-1)/df['totalCurrentLiabilities'].shift(-1)), 1, 0)
df['shareissuance'] = np.where(df['issuanceOfStock'] > 0, 0, 1)
df['gross_margin_improvement'] = np.where(((df['grossProfit']/df['totalRevenue']) > (df['grossProfit'].shift(-1))/df['totalRevenue'].shift(-1)),1,0)
df['asset_turnover_improvement'] = np.where((df['totalRevenue']/((df['totalAssets']+df['totalAssets'].shift(-1))/2)) > (df['totalRevenue'].shift(-1)/((df['totalAssets'].shift(-1)+df['totalAssets'].shift(-2))/2)),1,0)
f_score = df[['positive_net_income',
                        'positive_roa',
                        'positive_ocf',
                        'ocf_more_than_net_income',
                        'long_term_debt_ratio_improvement',
                        'current_ratio_improvement',
                        'shareissuance',
                        'gross_margin_improvement',
                        'asset_turnover_improvement'
    ]].head(1)
f_score['score'] = f_score.sum(axis = 1)
f_score['comment'] = np.where(f_score['score'] >= 8, 'Good Investment', 'Bad Investment')
front_labels = ['comment','score']
f_score = f_score[front_labels + [col for col in f_score.columns if col not in front_labels]]