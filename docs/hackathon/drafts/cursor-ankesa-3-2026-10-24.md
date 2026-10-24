To: hi@cursor.com
Subject: Third formal request - 76,153,304 tokens billed while the client was closed (ticket T-I12995, account arifi.arber@gmail.com)

Hello,

Ticket T-I12995 has still not received a substantive reply. I am writing a third time because I now have evidence that is not about pricing, not about the Ultra plan, and not about usage volume.

It is about a single invoice that was generated for usage that no client of mine could have produced.

THE FACTS

1. Invoice ALdOoWbp for USD 100.09 was issued on 21 October 2026 at 15:13 (Europe/Belgrade).

2. The Cursor desktop application on my only machine last wrote to its log files at 18 October 2026, 16:59. It was next launched on 22 October 2026, 08:02. Between those two timestamps the application was not running.

3. The application's local database contains 553 chat sessions. Between 19 and 21 October 2026 it contains zero. I checked the 74 per-workspace databases as well: zero sessions in that window.

4. I develop against a remote host over SSH. That host has no Cursor session store and no session in that window.

5. The Cursor CLI directory on the machine shows no activity in that window.

6. Your own usage export, however, records 76,153,304 On-Demand tokens between 18 October 2026 16:59 and 21 October 2026 15:13 - precisely the window that produced the USD 100.09 invoice, and precisely the window in which the client was closed.

For comparison, in the 4 hours and 23 minutes when the application WAS open on 18 October, the account recorded 5,691,233 On-Demand tokens. In the 70 hours when it was closed, it recorded 76,153,304.

WHAT I AM ASKING

a) Identify the client, device and IP address that generated those 76,153,304 tokens, with request-level identifiers and timestamps.

b) If no such client can be identified, reverse invoice ALdOoWbp and the corresponding usage.

c) A human audit of the account from 1 July 2026 to today, with per-invoice itemisation (dates, models, token counts, amounts) sufficient to reconcile each charge.

d) Written confirmation that no service action will be taken against the account while the audit is open.

I am not asking for goodwill or a discount. I am asking which machine made those requests. If the answer is none of mine, then this is not a billing question.

Attached: a full reconstruction, 12 months of usage data, 100 invoices, 99 invoice-to-invoice intervals, and the local session evidence.

Regards,
Arber Arifi
arifi.arber@gmail.com
Ticket: T-I12995 - Account: arifi.arber@gmail.com