"""Run with: streamlit run app.py"""
import json
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st
from metrics import METRICS, historical_rows, issue, metric_is_disputed, metrics, screen_rows

ROOT = Path(__file__).resolve().parent
SNAPSHOT = '6 November 2026'
st.set_page_config(page_title='Buying the dip? | Alamedin', page_icon='📉', layout='wide')

@st.cache_data
def load_data():
    records = json.loads((ROOT / 'data/balance_sheets.json').read_text())
    if len(records) != 100 or len({x['ticker'] for x in records}) != 100:
        raise ValueError('Expected 100 unique issuers in the bundled snapshot.')
    if any(x['scale'] != 'millions' for x in records):
        raise ValueError('This app expects source monetary amounts in millions.')
    return records

try:
    companies = load_data()
except (OSError, ValueError, KeyError) as exc:
    st.error(f'Could not load the bundled snapshot: {exc}')
    st.info('Include data/balance_sheets.json when deploying this repository.')
    st.stop()
by_ticker = {c['ticker']: c for c in companies}
frame = pd.DataFrame(screen_rows(companies))

def display_money(value, currency):
    return 'n.a.' if value is None or pd.isna(value) else f'{currency} {value / 1000:,.1f}B'

def chart_style(chart):
    return chart.configure_view(strokeWidth=0).configure_axis(
        labelColor='#A6B0BA', titleColor='#A6B0BA', gridColor='#252C34', labelFontSize=12
    ).configure_legend(labelColor='#DDE3E9', titleColor='#DDE3E9')

st.markdown('''<style>
.block-container{max-width:1450px;padding-top:2.4rem;padding-bottom:3rem}
.eyebrow{font-size:.78rem;letter-spacing:.16em;color:#a6b0ba;margin-bottom:1.1rem}
.hero{font-size:clamp(2.4rem,5vw,4.8rem);font-weight:800;line-height:1.05;letter-spacing:-.045em;margin:0 0 1.1rem}
.hero em{font-style:normal;color:#ccff55}
.deck{color:#a6b0ba;font-size:1.15rem;margin-bottom:1.7rem}
[data-testid="stMetricValue"]{font-size:1.65rem}
</style>
<div class="eyebrow">ALAMEDIN / LARP RESEARCH DEPARTMENT / REPORT 001</div>
<div class="hero">i guess we're buying the dip.<br><em>are we?</em></div>
<div class="deck">100 balance sheets. My conviction now has footnotes.</div>''', unsafe_allow_html=True)
st.caption(f'Static snapshot retrieved {SNAPSHOT}. Latest reporting dates vary from June to October 2026. No live prices or valuation model.')

with st.sidebar:
    st.subheader('The research desk')
    currency = st.selectbox('Reporting currency', ['USD', 'EUR', 'CNY'], key='currency')
    st.caption('One currency at a time. No pretend FX conversions.')
    search = st.text_input('Find a company', placeholder='Apple, MSFT, GOOG…', key='search')
    st.divider()
    st.markdown('**What this screen measures**')
    st.write('Cash and short-term investments, debt including leases, assets and liabilities.')
    st.caption('A negative liquidity surplus does not establish distress. A strong balance sheet does not establish a bargain.')
    st.link_button('Open the shared spreadsheet', 'https://docs.google.com/spreadsheets/d/1kctRRj5Sz-_Bvk0aiG10MZ9iUV1HdkD1/edit?usp=sharing')

filtered = frame[frame.currency == currency].copy()
if search.strip():
    needle = search.strip()
    filtered = filtered[filtered.ticker.str.contains(needle, case=False, regex=False) | filtered.company.str.contains(needle, case=False, regex=False)]
if filtered.empty:
    st.info('No companies match. Try another name or reporting currency.')
    st.stop()

top = st.columns(4)
top[0].metric('Companies in view', len(filtered))
top[1].metric('Reported periods each', 5)
top[2].metric('Currency', currency)
top[3].metric('Data exceptions in view', int((filtered.data_note != 'Provider data').sum()))
tabs = st.tabs(['The screen', 'Company receipts', 'Compare companies', 'Downloads & methodology'])

with tabs[0]:
    st.subheader('the obligations also showed up.')
    metric_label = st.selectbox('Compare by', list(METRICS), index=2, key='screen_metric')
    key = METRICS[metric_label]
    show_disputed = st.checkbox('Include unresolved Nvidia investment figures', value=False, key='show_disputed') if key in {'liquid', 'surplus'} and 'NVDA' in filtered.ticker.values else False
    chart_df = filtered.copy()
    if not show_disputed:
        chart_df = chart_df[~chart_df.ticker.map(lambda t: metric_is_disputed(t, key))]
    if key in {'liquid', 'surplus'} and 'NVDA' in filtered.ticker.values:
        st.caption('Nvidia investment mapping is unresolved. Its affected figures are excluded from this chart by default, but remain in the source table.')
    if show_disputed:
        st.warning('Nvidia values below are provider figures with an unresolved issuer mismatch. They are not reconciled.')
    missing = int(chart_df[key].isna().sum())
    chart_df = chart_df.dropna(subset=[key])
    order = st.radio('Display order', ['Highest first', 'Lowest first'], horizontal=True, key='order')
    count = st.select_slider('Companies on chart', options=[5, 10, 20, 40, 100], value=10, key='chart_count')
    chart_df = chart_df.sort_values(key, ascending=order == 'Lowest first').head(count)
    unit = 'times' if key == 'current_ratio' else f'{currency} billions'
    chart_df['display_value'] = chart_df[key] if key == 'current_ratio' else chart_df[key] / 1000
    if missing:
        st.caption(f'{missing} company/companies omitted from this metric because inputs are unavailable, not zero.')
    if chart_df.empty:
        st.info('No comparable values for this selection.')
    else:
        chart = alt.Chart(chart_df).mark_bar(cornerRadiusEnd=3).encode(
            x=alt.X('display_value:Q', title=f'{metric_label} ({unit})'),
            y=alt.Y('ticker:N', sort=chart_df.ticker.tolist(), title=None),
            color=alt.condition(alt.datum.display_value >= 0, alt.value('#CCFF55'), alt.value('#FF607A')),
            tooltip=['ticker:N', 'company:N', 'period:N', alt.Tooltip('display_value:Q', title=unit, format=',.2f'), 'data_note:N'],
        ).properties(height=max(240, len(chart_df)*27))
        st.altair_chart(chart_style(chart), width='stretch')
    st.caption('Latest period per company, shown on hover. Companies have different fiscal calendars. Long-term investments are excluded from liquidity surplus.')
    st.markdown('#### All companies in your filter')
    table = filtered[['ticker','company','period','currency','liquid','debt','surplus','current_ratio','assets','liabilities','data_note']].rename(columns={
        'ticker':'Ticker','company':'Company','period':'Period end','currency':'Currency','liquid':'Cash + ST (millions)',
        'debt':'Debt incl. leases (millions)','surplus':'Liquidity surplus (millions)','current_ratio':'Current ratio',
        'assets':'Assets (millions)','liabilities':'Liabilities (millions)','data_note':'Data note'})
    st.dataframe(table, hide_index=True, width='stretch')
    st.download_button('Download filtered comparison CSV', table.to_csv(index=False).encode(), 'nasdaq100_filtered.csv', 'text/csv')

with tabs[1]:
    options = filtered.ticker.tolist()
    ticker = st.selectbox('Company', options, format_func=lambda t:f'{t} · {by_ticker[t]["name"]}', key='company')
    c = by_ticker[ticker]
    m = metrics(c)
    st.subheader(c['name'])
    st.caption(f'{ticker} · reported {c["dates"][0]} · {currency} · Alphabet share classes are consolidated once.')
    if ticker == 'NVDA':
        st.warning('Provider cash + ST investments: USD 62,469m. Issuer cash + marketable debt securities: USD 56,586m. The USD 5,883m mapping difference is unresolved. Issuer equity securities are a separate line. Provider values are retained below.')
    elif issue(c) == 'Debt unavailable':
        st.warning('The provider reports debt as a dash. Debt and liquidity surplus remain unavailable; a dash is not treated as zero.')
    cards = st.columns(3)
    cards[0].metric('Cash + short-term investments', display_money(m['liquid'],currency))
    cards[1].metric('Debt including leases', display_money(m['debt'],currency))
    cards[2].metric('Liquidity surplus / deficit', display_money(m['surplus'],currency))
    if ticker == 'AAPL':
        st.info(f'Apple also reports {display_money(m["long_investments"],currency)} in long-term investments, excluded from the surplus above. The footnotes would like a word.')
    if ticker == 'MSTR':
        st.info('Strategy requires separate analysis of Bitcoin exposure and preferred capital. This liquidity screen is incomplete for its capital structure.')
    hist_label = st.selectbox('Historical metric', list(METRICS), index=3, key='history_metric')
    hk = METRICS[hist_label]
    if metric_is_disputed(ticker,hk):
        st.warning('This metric includes unresolved provider investment mapping. Historical values are not independently reconciled.')
    hist = pd.DataFrame(historical_rows([c],hk))
    hist['period'] = pd.to_datetime(hist.period)
    hist['display_value'] = hist.value if hk=='current_ratio' else hist.value/1000
    hu = 'times' if hk=='current_ratio' else f'{currency} billions'
    if hist.value.notna().any():
        line = alt.Chart(hist.sort_values('period')).mark_line(point=True,color='#CCFF55').encode(
            x=alt.X('period:T',title='Period end',axis=alt.Axis(format='%b %Y')),
            y=alt.Y('display_value:Q',title=f'{hist_label} ({hu})', scale=alt.Scale(zero=False)),
            tooltip=[alt.Tooltip('period:T',format='%Y-%m-%d'),alt.Tooltip('display_value:Q',format=',.2f',title=hu)],
        ).properties(height=300)
        st.altair_chart(chart_style(line),width='stretch')
    else:
        st.info('This metric is unavailable for these source periods.')
    st.markdown('#### Full source line items')
    records=[]
    for name,values in c['raw'].items():
        if name in {'Fiscal Quarter','Period Ending'}: continue
        records.append({'Source line item':name,**{date:values[i] if i<len(values) else '—' for i,date in enumerate(c['dates'])}})
    detail=pd.DataFrame(records)
    st.caption(f'Amounts in {currency} millions, except source percentage and per-share measures. Shares outstanding are in millions. Source dashes remain dashes.')
    st.dataframe(detail,hide_index=True,width='stretch',height=460)
    st.download_button('Download company source CSV',detail.to_csv(index=False).encode(),f'{ticker}_balance_sheet.csv','text/csv')
    st.link_button('Open company source',c['url'])

with tabs[2]:
    st.subheader('conviction, meet comparison.')
    available = filtered.ticker.tolist()
    defaults=[t for t in ['AAPL','MSFT','GOOGL','AMZN'] if t in available] or available[:3]
    chosen=st.multiselect('Pick up to six companies',available,default=defaults,max_selections=6,key='compare_tickers')
    label=st.selectbox('Comparison metric',list(METRICS),index=3,key='compare_metric')
    ck=METRICS[label]
    if not chosen:
        st.info('Choose at least one company to draw a comparison.')
    else:
        selected=[by_ticker[t] for t in chosen]
        if any(metric_is_disputed(t,ck) for t in chosen):
            st.warning('Nvidia is excluded from this investment-dependent comparison while its mapping remains unresolved.')
            selected=[c for c in selected if not metric_is_disputed(c['ticker'],ck)]
        if selected:
            history=pd.DataFrame(historical_rows(selected,ck))
            history['period']=pd.to_datetime(history.period)
            history['display_value']=history.value if ck=='current_ratio' else history.value/1000
            unit='times' if ck=='current_ratio' else f'{currency} billions'
            if history.value.notna().any():
                plot=alt.Chart(history.sort_values('period')).mark_line(point=True).encode(
                    x=alt.X('period:T',title='Actual period end',axis=alt.Axis(format='%b %Y')),
                    y=alt.Y('display_value:Q',title=f'{label} ({unit})',scale=alt.Scale(zero=False)),
                    color=alt.Color('ticker:N',title=None,scale=alt.Scale(range=['#CCFF55','#65C7FF','#FF607A','#BB9AFF','#FFBE70','#70E0C4'])),
                    tooltip=['ticker:N',alt.Tooltip('period:T',format='%Y-%m-%d'),alt.Tooltip('display_value:Q',format=',.2f',title=unit)],
                ).properties(height=420)
                st.altair_chart(chart_style(plot),width='stretch')
            else: st.info('No numeric data for this comparison.')
        st.caption('Actual reporting dates, not synchronized calendar quarters. Lines connect available observations, not daily estimates. Missing inputs are not zero.')

with tabs[3]:
    st.subheader('receipts, including the awkward ones.')
    st.write('Download the original report package. These documents cover the full snapshot, not your current filters.')
    files=[('Excel workbook','Nasdaq100_Balance_Sheets.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),('Editable slides','Buying_The_Dip_Are_We.pptx','application/vnd.openxmlformats-officedocument.presentationml.presentation'),('PDF report','Buying_The_Dip_Are_We.pdf','application/pdf')]
    for column,(label,name,mime) in zip(st.columns(3),files):
        path=ROOT/'reports'/name
        if path.exists(): column.download_button(label,path.read_bytes(),name,mime,width='stretch')
        else: column.caption(f'{label} not included in this deployment.')
    st.markdown('''
#### How to read this
- **Universe:** 100 issuers / 101 securities. Alphabet's GOOG and GOOGL share one balance sheet.
- **Source:** Stock Analysis standardized financials, retrieved 6 November 2026. Five reported periods per company. This app makes no live data requests.
- **Currency:** 96 USD, 3 EUR and 1 CNY reporters. Monetary comparisons stay within one reporting currency.
- **Liquidity surplus:** cash + short-term investments minus provider total debt, including classified leases. Long-term investments are excluded. Investments can fluctuate or be restricted.
- **Current ratio:** current assets divided by current liabilities. No universal safe threshold applies across all industries.
- **Missing data:** source dashes stay unavailable. ISRG and MNST debt is not assumed zero. Utilities missing a combined cash/ST line use both components only if both are numeric.
- **Nvidia exception:** provider cash/ST mapping differs from issuer components. Retained and flagged in source tables; excluded by default from affected screening charts.
- **Membership:** the current list includes Moderna and excludes Warner Bros. Discovery and Kraft Heinz; the older Nasdaq education page had not reflected those changes.
- **Limits:** selected issuer spot checks, not a filing-by-filing audit. No stock prices, earnings model, target returns or buy/sell recommendations. A static balance sheet cannot tell you whether a stock is cheap.

#### Primary references
[Current constituent list](https://stockanalysis.com/list/nasdaq-100-stocks/) ·
[Moderna membership notice](https://ir.nasdaq.com/node/111076) ·
[Kraft Heinz exchange transfer](https://www.nasdaq.com/press-release/kraft-heinz-transfer-stock-exchange-listing-nyse-2026-08-26)

[Apple filing](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm) ·
[Alphabet filing](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000084/goog-20260930.htm) ·
[Nvidia filing and mapping exception](https://investor.nvidia.com/files/doc_financials/2027/NVDA-2027-Q2-10Q-Final-including-exhibits.pdf)
''')
    sources=pd.DataFrame([{'Ticker':c['ticker'],'Company':c['name'],'Period end':c['dates'][0],'Source':c['url']} for c in companies])
    with st.expander('All 100 company source links'):
        st.dataframe(sources,column_config={'Source':st.column_config.LinkColumn('Source')},hide_index=True,width='stretch')

st.divider()
st.caption('Alamedin · LARP Research Department · ambition: high. spreadsheet: allowed to disagree.')
