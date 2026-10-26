# New DOT numbers weekly: free sample of new motor carrier registrations

Every week about 1,800 trucking companies get a USDOT number from FMCSA (the Federal Motor Carrier Safety Administration). Our weekly file of new DOT leads is built every Monday: it has every carrier registered in the last 21 days that was not in an earlier file, so each carrier appears in one file only. This repository holds a free 100-row sample of that file, with every column the paid file has.

<!--SAMPLE-->Current sample: 100 of the 3,970 carriers registered 2026-10-05 to 2026-10-23.<!--/SAMPLE-->

File: [`sample/new-usdot-carriers-sample.csv`](sample/new-usdot-carriers-sample.csv). It opens in Excel or Google Sheets.

## What is in each row

USDOT Number, Legal Name, DBA Name, Company Officer, Street Address, City, State, ZIP, Country, Mailing City, Mailing State, Phone, Cell Phone, Email, Operation (interstate or intrastate), Hazmat, Carries Passengers, Trucks, Drivers, Date Registered, Cargo Carried, Operating Type, and a link to the carrier's FMCSA record.

From the file for the week ending 2026-10-25, each row also has **Insurance On File** (Yes / No / Unknown: whether FMCSA has the carrier's liability insurance filing yet; "No" means the carrier needs one and has no insurance filing on file with FMCSA yet), plus Authority Status, MC Number and Insurance Checked (UTC), read from FMCSA's daily operating-authority and insurance data on the morning the file is built.

In this free sample a few personal fields are partly hidden: the company officer is shown as initials, the email as its domain, house numbers as `***` and the last 4 digits of the cell phone as `****`. The paid file has them in full.

## Who buys this list

- **Truck insurance agents**: new carriers must bind liability and cargo cover before they can haul.
- **Factoring companies**: new carriers have no credit history and wait 30 to 60 days to be paid.
- **ELD, fuel-card, dash-cam and dispatch vendors**: every new interstate carrier needs an ELD and fuel.
- **Compliance filers**: UCR, BOC-3, IFTA and MC authority services sell in a carrier's first weeks.

## Get the full week

The full file (every carrier in this week's file, all columns unmasked, as a CSV plus JSON) is **$29/month** at **https://rasengan.win/new-dot-leads/**. The first week is free: a card is required, you pay $0 today, and your card is charged $29 on day 8, then monthly, unless you cancel. One download link always serves the newest week. Cancel any time by emailing rasengan.win@gmail.com from the address you used at checkout.

## Source and terms

Source: the FMCSA Motor Carrier Census (dataset az4n-8mr2 on data.transportation.gov), a US federal public record. Contact details are as filed by each carrier and are not verified by FMCSA. If you contact these businesses, follow the TCPA, do-not-call, CAN-SPAM and state rules that apply to you.

**Rasengan Data is not affiliated with FMCSA or the US Department of Transportation.**

## Licence

The sample file and `update_sample.py` are released under the MIT licence (see [LICENSE](LICENSE)). The underlying government records are public.

`update_sample.py` rebuilds the sample from the newest weekly zip: `python3 update_sample.py [folder-with-weekly-zips]`.

Rasengan Data, https://rasengan.win
