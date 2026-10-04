# Price Alerts — Google Sheets + Apps Script

A Google Apps Script that monitors prices in an investment spreadsheet on Google Sheets and sends an email alert when an asset reaches a target price.

It currently covers **cryptocurrencies** (a sell alert when the price reaches the target). Stocks and Brazilian REITs (FIIs), which will get a buy alert when the price drops to the ceiling price, are in development.

## How it works

1. The spreadsheet fetches live quotes with `GOOGLEFINANCE`.
2. A time-driven trigger runs `crypto_prices_check()` periodically, even when the spreadsheet is closed.
3. For each row, the script compares the current price with the target price.
4. When the target is reached, it sends an HTML email and marks the row as `NOTIFIED`, so the same alert is not sent again.
5. If the price falls back below the target, the status is cleared and the alert is re-armed.

## Expected spreadsheet layout

Sheet `CRIPTO`, with data starting at row 3:

| Column | Content |
|---|---|
| B | Asset name |
| D | Purchase price |
| G | Target (sell) price |
| H | Current price (`=GOOGLEFINANCE("CURRENCY:BTCBRL")`) |
| I | Status (written by the script) |

The column numbers are defined as constants at the top of `crypto_prices_check()` and can be adjusted.

## Setup

1. In the spreadsheet, open **Extensions → Apps Script**.
2. Create the script files and paste in the code from this repository.
3. Run `crypto_prices_check` once manually and grant the requested permissions (spreadsheet access and sending email).
4. Under **Triggers**, add a trigger for `crypto_prices_check` with the event source **Time-driven**, set to run every 30 minutes.

Alerts are sent to the email address of the Google account that installed the script.

## Testing

Temporarily set a low target price in column G and run the function. You should receive the email, and column I should show `NOTIFIED`. Then restore the original value.

## Limitations

- `GOOGLEFINANCE` quotes can be delayed by up to about 20 minutes, so the alerts are not suitable for short-term trading.
- Free Gmail accounts can send about 100 emails per day through Apps Script.
- The shortest interval for a time-driven trigger is 1 minute.

## Roadmap

- [ ] Buy alerts for the stocks sheet (price ≤ ceiling price)
- [ ] Buy alerts for the REITs (FIIs) sheet
- [ ] Batch reads with `getValues()` for large sheets
- [ ] A single `check_all()` entry point with one trigger

## Tech stack

Google Apps Script (V8 JavaScript runtime), Google Sheets, `MailApp`, `GOOGLEFINANCE`.
