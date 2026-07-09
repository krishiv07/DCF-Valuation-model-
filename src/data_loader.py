import yfinance as yf

import yfinance as yf
import numpy as np

def fetch_financial_data(ticker):
    stock = yf.Ticker(ticker)
    income_stmt = stock.financials
    balance_sheet = stock.balance_sheet
    cash_flow = stock.cashflow
    info = stock.info
    
    data = {}
    
    # Extract Base Metrics
    try:
        data['total_revenue'] = income_stmt.loc['Total Revenue'].iloc[0]
        data['ebit'] = income_stmt.loc['EBIT'].iloc[0]
        data['ebit_margin'] = data['ebit'] / data['total_revenue']
        
        # FIX: Bound the tax rate between 0% and 35% to prevent one-off distortions
        raw_tax_rate = income_stmt.loc['Tax Provision'].iloc[0] / income_stmt.loc['Pretax Income'].iloc[0]
        data['tax_rate'] = max(0.0, min(raw_tax_rate, 0.35))
        
        # FIX: Multi-Year Smoothing for Historical Growth (3-Year CAGR)
        if len(income_stmt.columns) >= 4:
            revenue_yr3 = income_stmt.loc['Total Revenue'].iloc[3]
            data['historical_growth'] = (data['total_revenue'] / revenue_yr3)**(1/3) - 1
        else:
            revenue_yr1 = income_stmt.loc['Total Revenue'].iloc[1]
            data['historical_growth'] = (data['total_revenue'] / revenue_yr1) - 1

        data['total_debt'] = balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index else 0
        data['cash'] = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in balance_sheet.index else 0
        data['shares_outstanding'] = info.get('sharesOutstanding', 1)
        
        # FIX: Dynamic Cost of Debt (Interest Expense / Total Debt)
        if 'Interest Expense' in income_stmt.index and data['total_debt'] > 0:
            interest_expense = abs(income_stmt.loc['Interest Expense'].iloc[0])
            data['cost_of_debt'] = interest_expense / data['total_debt']
        else:
            data['cost_of_debt'] = 0.085 # Standard fallback proxy

        data['beta'] = info.get('beta', 1.0)
        data['capex'] = abs(cash_flow.loc['Capital Expenditure'].iloc[0]) if 'Capital Expenditure' in cash_flow.index else data['total_revenue'] * 0.05
        data['depreciation'] = cash_flow.loc['Depreciation And Amortization'].iloc[0] if 'Depreciation And Amortization' in cash_flow.index else data['total_revenue'] * 0.04
        
        # Risk Free Rate handling (Fallback to 7.1% for India if ticker fails)
        try:
            bond = yf.Ticker("^IN10YT=RR")
            data['risk_free_rate'] = bond.history(period="1d")['Close'].iloc[-1] / 100
        except:
            data['risk_free_rate'] = 0.071
            
    except Exception as e:
        print(f"Data parsing error for {ticker}: {e}")
        
    return data
