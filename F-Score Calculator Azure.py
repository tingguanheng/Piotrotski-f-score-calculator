# This is the calculator script made by pulling data from Financial Modelling Prep API and automating the analysis on Azure Automate.

import requests
from datetime import date
import automationassets

stock_screener_url = "https://financialmodelingprep.com/api/v3/stock-screener"

stock_parameters = {
    "marketCapMoreThan":1000000,
    "priceLowerThan":20,
    "volumeMoreThan":2500000,
    "priceMoreThan ":5,
    "isActivelyTrading":"true",
    "sector":"Technology",
    "Country":"US,JP",
    "exchange":"nyse,nasdaq",
    "apikey":automationassets.get_automation_variable("FMP_API_KEY")
}

response = requests.get(url=stock_screener_url,params=stock_parameters)
response.raise_for_status()
company_data = response.json()
company_list = []
for stock in company_data:
    name = stock["symbol"]
    company_list.append(name)

print(company_list)

good_stocks = []

for stock in company_list:
    is_endpoint = f"https://financialmodelingprep.com/api/v3/income-statement/{stock}"
    bs_endpoint = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{stock}"
    cf_endpoint = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{stock}"

    fmp_parameters = {
        "apikey":automationassets.get_automation_variable("FMP_API_KEY")
    }


    is_response = requests.get(url=is_endpoint,params=fmp_parameters)
    is_response.raise_for_status()
    is_data = is_response.json()[:3]

    bs_response = requests.get(url=bs_endpoint,params=fmp_parameters)
    bs_response.raise_for_status()
    bs_data = bs_response.json()[:3]

    cf_response = requests.get(url=cf_endpoint,params=fmp_parameters)
    cf_response.raise_for_status()
    cf_data = cf_response.json()[:3]

    ## Piotrotski F-Score Analysis ('m)
    ## Net Income score
    try:
        net_income = is_data[0]["netIncome"]/1000000
    except:
        print("Net Income not found.")
        net_income = 0

    if net_income>0:
        net_income_score = 1
    else: 
        net_income_score = 0

    ## Return on Assets score
    try:
        return_on_assets = net_income/(bs_data[0]["totalAssets"]/1000000)
    except:
        print("Total Assets not found.")
        return_on_assets = 0

    if return_on_assets>0:
        roa_score = 1
    else:
        roa_score = 0

    ## Operating Cash Flow score
    try:
        operating_cash_flow = cf_data[0]["netCashProvidedByOperatingActivities"]/1000000
    except IndexError:
        print("Positive cash flow not found.")
        try:
            operating_cash_flow = cf_data[0]["netCashUsedByOperatingActivities"]/1000000
        except:
            print("Cash flow not found.")
            operating_cash_flow = 0

    if operating_cash_flow >0:
        ocf_score = 1
    else:
        ocf_score = 0

    ## Operating Cash Flow > Net Income score
    if operating_cash_flow > net_income:
        ocf_ni_score = 1
    else:
        ocf_ni_score = 0

    ## Long Term Debt score
    try:
        long_term_debt = (bs_data[0]["longTermDebt"]/1000000)/(bs_data[0]["totalAssets"]/1000000)
    except:
        print("Long Term Debt not found.")
        long_term_debt = 0
    try:
        long_term_debt_prev = (bs_data[1]["longTermDebt"]/1000000)/(bs_data[1]["totalAssets"]/1000000)
    except:
        print("No long term debt in prior year.")
        long_term_debt_prev = 0

    if long_term_debt<long_term_debt_prev:
        long_term_debt_score = 1
    else:
        long_term_debt_score = 0

    ## Quick Ratio score
    try:
        current_assets = bs_data[0]["totalCurrentAssets"]/1000000
    except:
        print("Current asset not found.")
        current_assets = 0
    try:
        inventory = bs_data[0]["inventory"]/1000000
    except:
        print("Inventory not found.")
        inventory = 0
    
    current_asset_less_inventory = current_assets-inventory
    

    try:
        current_liabilities = bs_data[0]["totalCurrentLiabilities"]/1000000
        quick_ratio = current_asset_less_inventory/current_liabilities
    except:
        print("Current liabilities not found.")
        current_liabilities = 0
        quick_ratio = 0

    try:
        current_assets_prev = bs_data[1]["totalCurrentAssets"]/1000000
    except:
        print("No current assets in prior year.")
        current_assets_prev = 0
    try:
        inventory_prev = bs_data[1]["inventory"]/1000000
    except:
        print("No inventory in prior year.")
        inventory_prev = 0

    current_asset_less_inventory_prev = current_assets_prev-inventory_prev

    try:
        current_liabilities_prev = bs_data[1]["totalCurrentLiabilities"]/1000000
        quick_ratio_prev = current_asset_less_inventory_prev/current_liabilities_prev
    except:
        print("No current liabilities in prior year.")
        current_liabilities_prev = 0
        quick_ratio_prev = 0

    if quick_ratio > quick_ratio_prev:
        quick_ratio_score = 1
    else:
        quick_ratio_score = 0

    ## Shares issued score
    try:
        common_stock_issued = (cf_data[0]["commonStockIssued"]-cf_data[0]["commonStockRepurchased"])/1000000
    except:
        try:
            common_stock_issued = cf_data[0]["commonStockIssued"]
            print("Common stock repurchase not found.")
        except:
            print("Common stock movement not found.")
            common_stock_issued = 0
    try :
        preferred_stock_issued = (cf_data[0]["preferredStockIssued"]-cf_data[0]["preferredStockRepurchased"])/1000000
    except:
        try:
            preferred_stock_issued = cf_data[0]["preferredStockIssued"]
            print("Preferred stock repurchase not found.")
        except:
            preferred_stock_issued = 0

    if common_stock_issued + preferred_stock_issued <= 0:
        shares_issued_score = 1
    else:
        shares_issued_score = 0

    ## Profit Margin Score
    try:
        profit_margin = is_data[0]["grossProfitRatio"]
    except:
        try:
            profit_margin = (is_data[0]["revenue"]-is_data[0]["costOfRevenue"])/is_data[0]["revenue"]
        except:
            try: 
                revenue = is_data[0]["revenue"]
            except:
                print("Revenue not found.")
                revenue = 0
            try:
                cogs = is_data[0]["costOfRevenue"]
            except:
                print("COGS not found.")
                print("Profit margin not found.")
                profit_margin = 0
    try:
        profit_margin_prev = is_data[1]["grossProfitRatio"]
    except:
        try:
            profit_margin_prev = (is_data[1]["revenue"]-is_data[1]["costOfRevenue"])/is_data[1]["revenue"]
        except:
            try: 
                revenue = is_data[1]["revenue"]
            except:
                print("No revenue found in prior year.")
                revenue = 0
            try:
                cogs = is_data[1]["costOfRevenue"]
            except:
                print("No COGS found in prior year.")
                print("No profit margin found in prior year.")
                profit_margin_prev = 0    


    if profit_margin > profit_margin_prev:
        profit_margin_score = 1
    else:
        profit_margin_score = 0

    ## Asset Turnover Score
    try:
        revenue = is_data[0]["revenue"]/1000000
    except:
        print("Revenue not found.")
        revenue = 0
    try:
        average_asset = ((bs_data[0]["totalAssets"]/1000000)+(bs_data[1]["totalAssets"]/1000000))/2
        asset_turnover = revenue/average_asset
    except:
        print("Total asset not found in current or prior year.")
        average_asset = 0
        asset_turnover = 0
    
    try:
        revenue_prev = is_data[1]["revenue"]/1000000
    except:
        print("No revenue found in prior year.")
        revenue_prev = 0
    try:
        average_asset_prev = ((bs_data[1]["totalAssets"]/1000000)+(bs_data[2]["totalAssets"]/1000000))/2
        asset_turnover_prev = revenue_prev/average_asset_prev
    except:
        print("Total asset not found either last year or the year before.")
        average_asset_prev = 0
        asset_turnover_prev = 0

    if asset_turnover > asset_turnover_prev:
        asset_turnover_score = 1
    else:
        asset_turnover_score = 0

    total_score = ocf_score+roa_score+ocf_ni_score+net_income_score + quick_ratio_score + profit_margin_score + asset_turnover_score + long_term_debt_score + shares_issued_score


    price_endpoint= f"https://financialmodelingprep.com/api/v3/quote/{stock}"

    price_response = requests.get(url=price_endpoint,params=fmp_parameters)
    price_response.raise_for_status()
    price_data = price_response.json()

    current_price = price_data[0]["price"]
    company_name = price_data[0]["name"]

    print(f"Stock name: {stock}")
    print(f"Company name: {company_name}")
    print(f"Current price: {current_price}")

    f_score = {
        "ocf_score":ocf_score,
        "roa_score":roa_score,
        "ocf_ni_score":ocf_ni_score,
        "net_income_score":net_income_score,
        "quick_ratio_score":quick_ratio_score,
        "profit_margin_score":profit_margin_score,
        "asset_turnover_score":asset_turnover_score,
        "long_term_debt_score":long_term_debt_score,
        "shares_issued":shares_issued_score
    }

    if total_score == 7 or total_score == 8:
        f_list = f_score.items()
        shortfalls = []
        for i in f_list:
            if i[1] == 0:
                shortfalls.append(i)
        statement = "   ".join(x[0]+":"+str(x[1]) for x in shortfalls)
        print(f"Total score: {total_score}  {statement}")
    else:
        print(f"Total score: {total_score}")

    if total_score >= 7 and total_score <= 9:
        good_stocks.append(f"{company_name}: {total_score}")

today_date = date.today()
today_date = today_date.strftime("%d %B %Y")

print(f"Good stocks as at {today_date}:\n{good_stocks}")
