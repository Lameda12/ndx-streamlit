# i guess we're buying the dip. are we?

A Streamlit research app for Alamedin's LARP Research Department. It includes the **6 November 2026 static Nasdaq-100 snapshot** used in the accompanying report: 100 unique issuers, five reported periods each, source URLs and known data exceptions.

## Publish on Streamlit Community Cloud

1. Unzip this project. Create a GitHub repository, for example `buying-the-dip`.
2. Upload the **contents** of `ndx_streamlit` to the repository root. Include `app.py`, `metrics.py`, `requirements.txt`, the entire `data` and `reports` directories, and `.streamlit/config.toml`. If your uploader hides dotfiles, enable hidden files or create `.streamlit/config.toml` using GitHub's file editor.
3. Open [Streamlit Community Cloud](https://share.streamlit.io/), connect GitHub, and select **Create app** / deploy from GitHub.
4. Select your repository and branch. Set the main file path to **`app.py`**. Use **Python 3.12** under Advanced settings. No secrets or API keys are needed.
5. Deploy. Choose a URL such as `alamedin-buying-the-dip.streamlit.app` if available.

If you upload the parent folder instead, set the entry point to `ndx_streamlit/app.py`. Prefer the repository-root layout above.

Official instructions: [Deploy an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [dependencies](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies).

## Run locally

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

On Windows activate with `.venv\Scripts\activate`.

## Included

- `app.py`: dark dashboard, screener, company histories, comparison charts, CSV exports and report downloads.
- `metrics.py`: calculations with explicit missing-value handling.
- `data/balance_sheets.json`: all 100 companies, native currencies, latest five source periods, numeric values, original source strings and URLs.
- `reports/`: Excel workbook, editable presentation and PDF. Downloads always return the original full report, not the active filtered view.
- `.streamlit/config.toml`: dark theme with lime accents.
- `test_app.py`: financial calculation and Streamlit interaction tests.

## Data contract and limitations

The app is **not live**. It makes no API or scraping requests. The Google Sheets button opens the user's shared workbook, but does not synchronize with it. Quotes, prices and valuation scores are intentionally absent.

Monetary values are in **reporting-currency millions** in JSON and tables. Charts explicitly convert to billions. Comparisons never mix USD, EUR and CNY. Reporting dates remain visible and are not normalized to calendar quarters. Alphabet is represented by GOOGL once, covering both share classes.

Liquidity surplus = cash and short-term investments minus provider total debt, including classified leases. Long-term investments are excluded. A deficit is not a bankruptcy signal. Current ratio = current assets / current liabilities. Source dashes are missing, not zero. Debt for ISRG and MNST is unavailable in this snapshot.

**Nvidia:** provider cash + ST investments is USD 62,469 million, whereas issuer cash + marketable debt securities is USD 56,586 million; issuer equity securities form another line. The mapping remains unresolved. The app retains the raw provider values with warnings and excludes Nvidia from affected screening charts by default and investment-dependent comparison charts entirely. Other metrics remain available. Selected issuer checks do not constitute a full audit.

## Update the data

Replace `data/balance_sheets.json` only with a reviewed extract of the same schema. Each issuer record contains `ticker`, `name`, `currency`, `scale` (`millions`), `dates` (five ISO period-end dates, latest first), `values` (line-item arrays of numbers or null), `raw` (original display strings), and `url`. Optional `quarters` is preserved. Keep raw and numeric values consistent.

Update the visible snapshot date and methodology in `app.py`, recheck membership and known exceptions in `metrics.py`, and replace the report downloads with matching new editions. Clear the Streamlit cache or reboot after deployment. There is no automatic weekly refresh or connection to a ChatGPT scheduled task.

## Test

```bash
python -m unittest test_app -v
```

The tests cover missing debt versus actual zero, utility fallback, currency isolation, reporting dates, Nvidia exclusion, company selection, search/empty states and app startup. They do not certify the accuracy of every third-party financial value or a deployment on Community Cloud.

Source figures and URLs retain their provider attribution; this package grants no rights over third-party financial data. The editable code is provided for your app.
