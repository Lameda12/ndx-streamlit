"""Pure financial calculations. Amounts remain in reporting-currency millions."""
import math

METRICS = {
    'Cash + short-term investments': 'liquid',
    'Debt including leases': 'debt',
    'Liquidity surplus / deficit': 'surplus',
    'Total assets': 'assets',
    'Total liabilities': 'liabilities',
    'Shareholders equity': 'equity',
    'Current ratio': 'current_ratio',
}

def number(value):
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) else None

def source_value(company, name, period=0):
    values = company['values'].get(name, [])
    return number(values[period]) if period < len(values) else None

def difference(a, b):
    return a - b if a is not None and b is not None else None

def ratio(a, b):
    return a / b if a is not None and b is not None and b > 0 else None

def metrics(company, period=0):
    get = lambda key: source_value(company, key, period)
    cash, short = get('Cash & Equivalents'), get('Short-Term Investments')
    liquid = get('Cash & Short-Term Investments')
    if liquid is None and cash is not None and short is not None:
        liquid = cash + short
    debt, assets = get('Total Debt'), get('Total Assets')
    return {
        'cash': cash, 'short': short, 'liquid': liquid, 'debt': debt,
        'surplus': difference(liquid, debt), 'assets': assets,
        'liabilities': get('Total Liabilities'), 'equity': get("Shareholders' Equity"),
        'long_investments': get('Long-Term Investments'),
        'current_ratio': ratio(get('Total Current Assets'), get('Total Current Liabilities')),
        'debt_assets': ratio(debt, assets),
    }

def issue(company):
    if company['ticker'] == 'NVDA':
        return 'Investment mapping unresolved'
    if source_value(company, 'Total Debt') is None:
        return 'Debt unavailable'
    return 'Provider data'

def screen_rows(companies):
    return [dict(ticker=c['ticker'], company=c['name'], currency=c['currency'],
                 period=c['dates'][0], data_note=issue(c), **metrics(c)) for c in companies]

def historical_rows(companies, key):
    return [dict(ticker=c['ticker'], period=date, value=metrics(c, i)[key], currency=c['currency'])
            for c in companies for i, date in enumerate(c['dates'])]

def metric_is_disputed(ticker, key):
    return ticker == 'NVDA' and key in {'liquid', 'surplus'}
