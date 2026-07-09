import numpy as np
import pandas as pd

def calculate_wacc(data, market_risk_premium=0.075):
    cost_of_equity = data['risk_free_rate'] + (data['beta'] * market_risk_premium)
    cost_of_debt = data['risk_free_rate'] + 0.015 
    
    total_capital = data['market_cap'] + data['total_debt']
    weight_equity = data['market_cap'] / total_capital
    weight_debt = data['total_debt'] / total_capital
    
    wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt * (1 - data['tax_rate']))
    return wacc

import pandas as pd
import numpy as np

def build_base_forecast(data, wacc, forecast_years=5, terminal_growth=0.02):
    # GUARDRAIL: Prevent WACC from being <= terminal growth
    wacc = max(wacc, terminal_growth + 0.005) 
    
    years = range(1, forecast_years + 1)
    forecast = pd.DataFrame(index=years)
    
    # 1. Project Revenue (Smoothing applied in data_loader)
    forecast['Revenue'] = [data['total_revenue'] * (1 + data['historical_growth'])**yr for yr in years]
    
    # 2. Operating Margins & Taxes
    forecast['EBIT'] = forecast['Revenue'] * data['ebit_margin']
    forecast['NOPAT'] = forecast['EBIT'] * (1 - data['tax_rate'])
    
    # 3. Reinvestment Assumptions
    capex_pct = data['capex'] / data['total_revenue'] if data['total_revenue'] != 0 else 0.05
    da_pct = data['depreciation'] / data['total_revenue'] if data['total_revenue'] != 0 else 0.04
    nwc_pct = 0.03 
    
    forecast['D&A'] = forecast['Revenue'] * da_pct
    forecast['CapEx'] = forecast['Revenue'] * capex_pct
    
    # FIX: Calculate incremental Change in NWC, not total NWC
    nwc_balance = forecast['Revenue'] * nwc_pct
    historical_nwc = data['total_revenue'] * nwc_pct
    forecast['Change_NWC'] = nwc_balance.diff().fillna(nwc_balance.iloc[0] - historical_nwc)
    
    # 4. Free Cash Flow to Firm (FCFF)
    forecast['FCFF'] = forecast['NOPAT'] + forecast['D&A'] - forecast['CapEx'] - forecast['Change_NWC']
    
    # FIX: Mid-Year Discounting Convention (yr - 0.5)
    forecast['Discount_Factor'] = (1 + wacc) ** (forecast.index - 0.5)
    forecast['PV_FCFF'] = forecast['FCFF'] / forecast['Discount_Factor']
    
    # 5. Terminal Value Calculation
    final_fcff = forecast['FCFF'].iloc[-1]
    terminal_value = (final_fcff * (1 + terminal_growth)) / (wacc - terminal_growth)
    pv_tv = terminal_value / ((1 + wacc) ** (forecast_years - 0.5))
    
    # 6. Enterprise to Equity Bridge
    enterprise_value = forecast['PV_FCFF'].sum() + pv_tv
    equity_value = enterprise_value - data['total_debt'] + data['cash']
    implied_price = equity_value / data['shares_outstanding'] if data['shares_outstanding'] > 0 else 0
    
    return forecast, implied_price, enterprise_value, equity_value, terminal_value, pv_tv
