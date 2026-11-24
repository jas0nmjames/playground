# Medianville v2 hand-written records: the second reader's check

Written 2026-11-21 by a separate Claude agent that saw only the 300 record cards with their hand-written text (no code, no repository, no web), and checked the text against each card's own fields. Card numbers refer to the cards `tools/sample_records.py --ids sim/detail_parts/selection.json` writes. Kept as written; what was done with it is in [the close reading](medianville-v2-close-reading.md#the-hand-written-records). The cards showed the hand-written narrative only, so details carried over from the simulator's own narrative (a settlement in 21 days, $40 a month on a medical bill, an amount past due) read to this reader as unsupported.

Read from `handwritten_cards.md` only. Each card's Statement and Narrative were checked against the fields on the same card. One cross-card conflict (112 and 295, same resident) is included because a reader of the data would see both.

### 1. Must fix

5. R0002332: the statement says tax is withheld "every week", but she is paid biweekly; "every payday".
34. R0019951: the statement wants the check to land "before the mortgage draft", but the household owns its home free and clear; "before the bills draft".
46. R0031117: the narrative names the Earned Income Tax Credit for a household with $198,604 a year (58% from investments), far above the EITC income and investment-income limits, and $6,676.61 is also more than the refundable Child Tax Credit for two children. Flag the record, and until it is fixed say "refundable credits" without naming the EITC.
64. R0039856: the narrative puts her shift "at the nursing home", but she works at Medianville Regional Medical Center; "before her hospital shift". Also, "since his surgery" in the statement is not on the card.
69. R0045454: the narrative says the balance stays low "until SNAP and her check arrive". SNAP loads to the EBT card, not her Nimbus Bank account, and the household's only income is SSI, which was paid on Monday, March 1. Say "the balance was lower than that" and drop the arrival claim.
71. R0046332: "When my mom leaves for work" is wrong for this household, whose income is 100% Social Security with no wages; "When there is no time for breakfast at home".
79. R0058328: the narrative says "nobody could watch the kids", but a married household of 3 has one child; "nobody could watch his child". The statement's "my second job" is also wrong, since the card shows one job; "my job".
80. R0058968: the statement says "I want to drive him myself" for a woman with a vision disability (the narrative is careful to say she "went with her son by car"); "I want to get him there by car myself".
83. R0060420: "stay in my own apartment" doesn't fit: the notes say she rents a mobile home; "stay in my own home".
112/295. R0197700: this is the same resident (P003639) who paid a divorce filing fee at 9:54 a.m. in card 112, after "we have agreed to end the marriage". Paying a retainer that night for "my wife's green card case" contradicts that, and the household isn't flagged as an immigrant household. Make it a different immigration matter (a parent's or sibling's), or flag the pair of records.
150. R0098975: the statement and narrative make it a flat tire, but the record follows R0088002 (car_wont_start), and a flat doesn't stop a car from starting; "When my car will not start, I want to get it towed and fixed", and "a tow and a battery repair".
153. R0100146: the narrative says the money went by "a payment-app transfer", but the payment was ACH by phone; "a bank transfer she authorized over the phone".
159. R0103949: the narrative says he "drove 74.3 miles" although his disability is vision, and "walk without the cane" invents a mobility problem the card doesn't show. Say "made the 74.3-mile trip" and drop the cane. "Round trip" isn't on the card either, and 74.3 miles plus a therapy session can't fit in the 53-minute time field (record issue).
171. R0115051: the statement and narrative say he used a fuel card, but the payment field is debit. The fee is labelled fuel_card_fee, so one of the two fields is wrong: fix the record, or make the text say debit.
204. R0130107: "it covers most of the month's rent" is wrong because the $600.00 is more than the $422 rent; "it covers the month's rent with a little left over".
206. R0132556: "have them ready by three" is wrong because the stop starts at 3:06 p.m. and takes 14 minutes; "have them ready for afternoon snack".
210. R0133375: "he paid for the diagnosis only" contradicts paid by the person $0.00, and the $589 quote isn't on the card; "he left without the repair", or add the diagnosis charge to the record.
220. R0138383: "keep our food benefits" isn't supported: the card shows no SNAP or any other benefit for her or the household (no snap_monthly, uninsured); "keep our benefits", or fix the record.
223. R0139086: "When my parents pay me for watching their children" reads as his own mother and father; "When the parents pay me".
230. R0142920: "payday is two weeks off" is wrong because she is paid weekly; "payday is days away".
255. R0166157: "When I owe my brother" is wrong because the recipient is a 72-year-old woman; "my mother" (or "my grandmother", "a neighbor").
274. R0179952: the narrative calls her a "line cook", but the card says fast food worker at Sunny Dip Donuts; "fast food worker".
286. R0190210: "When the rent is short … pay the landlord" is wrong because he owns his home with a mortgage ($2,888 a month); "When the mortgage payment is short … pay the lender on time".

### 2. Should fix

1. R0001203: "two incomes in the house" isn't supported (only his wages are shown, and the withholding fits a single earner), and "federal and state tax" goes beyond a record paid to the IRS; "so I can avoid a bill in April".
8. R0003644: "from the school cafeteria" invents her work history, and "$442.03 was left after withholding" invents a 10% withholding the card doesn't show (default withholding on about $5,900 a year of pension would be about zero). Drop both, or put the withholding in the record.
10. R0007640: "building credit toward benefits" should be "earning Social Security work credits".
12. R0009281: "avoid owing with six people in the house" gets the logic backwards, since four children mean more credits and less tax owed; "so I can count on a refund".
13. R0010710: the statement mixes an equipment loan with "keep the line of credit open"; "so I can keep the bank willing to lend for the next repair".
18. R0012852: "payroll for 2 on staff" and "the two of us … my assistant" state a staff count that isn't on the card; keep them only if the record has the count.
20. R0013186: "and my aide" is unsupported because no disability or care need is listed; "and the rest of my bills".
25. R0014364: wanting health coverage "if I get hurt on the job" is wrong, since workers' compensation covers job injuries. "Keep the family covered" is also unclear for an adult child who may be on his own plan; "so I can see a doctor if I get sick or hurt".
45. R0030753: "blood sugar drops" implies a diabetes diagnosis for a 7-year-old that the card doesn't support, and "treated her … in 21 minutes" hides that 17 of those minutes were the wait. Use a neutral reason ("wakes up sick and we are scared") and say EMS arrived after 17 minutes.
55. R0034762: the narrative splits $14.91 into "$8.75 federal and $6.16 state", but the record is paid to the IRS, and federal withholding on $10,153 a year should be about zero. Drop the split or fix the record. Also, "so I can not owe anything" should be "so I won't owe anything".
57. R0035390: the same federal/state split ($13.14/$8.53) appears on an IRS record, and federal withholding is unlikely for a married couple on $14,060. Drop the split or fix the record.
59. R0036006: the text makes VaultBox a photo backup, but the job is streaming_subscription; call it a streaming service, or reclassify the record.
65. R0040918: "keep the loan from bouncing again" is off: the draft bounces, not the loan, and "again" implies an earlier bounce; "keep the draft from bouncing".
66. R0043380: "an early shift after school" doesn't explain eating breakfast at school at 7:11 a.m.; "When I worked late last night and had no time for breakfast".
70. R0045457: "on the account" suggests a trade account, but the payment was a credit card (as the narrative says); "on the company card".
77. R0052406: $1,247.04 is far too much for "the week's after-school care"; "the month's".
78. R0052645: "on my way home" at 7:39 a.m. doesn't fit a home child care provider whose day is just starting; "before the kids arrive".
91. R0073128: the statement has a tense clash ("When I moved …, I want"), and the narrative's "the call dropped" contradicts the abandoned outcome; "Now that I have moved in with my son", and "before he gave up".
95. R0075436: "get to class and my job" doesn't fit: the card shows a student with no job; drop "and my job".
98. R0076047: "picked and packed … deliver the load to the packer" doesn't work, because packing is the packer's job. The partial outcome isn't explained, and "the check will come in 21 days" isn't on the card. Use "picked and loaded", and say what was partial.
99. R0076179: the statement says "more hours" but the narrative says "a raise". "A $858.00" should be "an $858.00", and the text should give the period (only $858 a month would push $13,630 a year past the Medicaid limit).
102. R0077220: "my knee has been acting up since the service" invents a service-connected condition; "When my VA checkup is due".
105. R0078371: a housing "waiting list" doesn't fit a man earning $64,125 alone and saving for a deposit; "so I can rent a place before spring".
107. R0079040: the same "packed … deliver them to the packer" wording appears here; "payment comes in 21 days" isn't on the card, and the partial outcome isn't explained.
110. R0079573: "left work an hour early" reads oddly at 9:42 a.m.; "left work for an hour". The statement also stacks two clauses: "so I can be home so she is not alone".
116. R0080823: this is a record problem the text hides: Medicare's home health benefit is paying for a 42-year-old on a marketplace plan; flag the record.
119. R0081797: "the customer's accounts payable office" doesn't fit a customer from the general public; "the customer said the invoice never arrived".
125. R0084877: "the cash price would have been $16.57" isn't on the card; drop it.
129. R0085556: "so I can not start over" should be "so I don't have to start over".
135. R0087613: "$364.49 past due, with disconnection in 10 days" isn't on the card (gross $0.00); drop it, or add the figures to the record.
158. R0103104: the same packed-before-the-packer wording and unsupported "21 days" appear here.
178. R0117642: $300 is implausible for "my share of a ride home"; "for the weekend trip home".
180. R0117734: "leaving $5.12 on the card" isn't on the card, and "a little left" is a stretch two days after her $112 issuance (issue day 1); drop the balance.
181. R0118042: "after work" at 1:11 p.m. doesn't fit a full-time manager on a fixed schedule; "on my lunch break".
182. R0118215: "apply for passports" is plural, but the $165 fee covers one passport; "apply for my passport".
188. R0121488: "on the way home" at 1:33 p.m. falls while the children he watches would be in his care; "after the last pickup".
191. R0123685: "sold 7 head" and "raises cattle with her family" aren't on the card (she lives alone in a dorm); keep them only if the record has them.
200. R0128034: "When my grandmother lives in the nursing home" states a condition, not a trigger, and neither "nursing home" nor "round trip" is on the card; "When I visit my grandmother, I want to talk with the staff".
203. R0129472: "$513.58 past due, with disconnection in 5 days" isn't on the card; drop it, or add the figures to the record.
214. R0135404: "mistakes" appears twice in one statement; "so I can get the refund right the first time".
215. R0135490: "fill up on gas and trimmer line" should be "buy gas and trimmer line".
219. R0137997: "the approver is out until Monday" describes a business customer, but the customers here are the general public; "the customer is away until Monday".
229. R0140980: "my classes start next week" doesn't fit March 3, which is mid-semester; drop the timing or say "my next course".
235. R0147743: "$40 a month on the last medical bill" isn't on the card and is repeated word for word in 265; drop it, or take the figure from the record.
247. R0159462: "When my paper paycheck clears" is wrong, since FICA is withheld when the check is written; "When I get my paper paycheck".
253. R0162705: "since the accident" invents a cause; "When my husband cannot bathe on his own".
265. R0171932: the narrative ("$40 a month") and the statement are near copies of 235; vary or drop them.
267. R0174988: "save my cash for the bus" doesn't fit a record with no_transit in which she got a ride, and "round trip" isn't on the card; "save my cash for gas for my ride".
271. R0179307: sending "my share of the utilities" to a brother-in-law doesn't fit a two-person married household that owns its home; "pay my brother-in-law back".
277. R0184862: "my roommate" may be wrong. The recipient's ID (P077849) is far from hers (P048038), while household members elsewhere have neighboring IDs. Check, or say "a friend".
278. R0186231: "more than he had to spare after the house payment" is implausible for a $351,032 household with a $739 mortgage; "his account was short".
288. R0190524: "husband" may be wrong. The record follows a caregiving visit, and his ID (P091146) is far from hers (P075407), so he likely lives elsewhere and isn't her spouse in her two-person household; check.
289. R0190650: "wife" may be wrong for the same reason: the record follows a caregiving visit, and the IDs are P054157 and P066162; check.
300. R0201900: the statement is a relative's ("When my mother falls"), not the 77-year-old's own job; "When I fall and cannot get up, I want help getting up and checked, so I can know whether I am hurt".

### 3. Patterns

- **Stock statement endings.** "so I can keep …" ends 86 of 300 statements (35 "keep the", 19 "keep my", 6 "keep him", 4 "keep her"). "I want to have …" appears in 73. "so I can avoid" appears in 11.
- **Stock narrative opening.** 217 of 300 narratives open "A/An N-year-old …".
- **One template per record type.** Within a record type the statements are near copies:
  - school lunch, "When it is lunchtime at school" (6);
  - school day, "When it is a school day" (4);
  - child care subsidy, "When we care for children whose families get state help" (4);
  - employer payroll tax, "When payroll runs for the …" (4);
  - overdue invoice, "When a customer is 60/45 days late, I want to chase the payment" (4);
  - midweek offering, "… service begins, I want to give what I can, so I can support my church" (5);
  - renewals, "fix the form and send it again" (5);
  - put-off care, "a doctor/dentist I can afford" (4), with "before it gets worse" (3);
  - declined app transfers, "send it through the app, so I can settle up today" (3);
  - caregiver errands, "keep him/her stocked without another trip" (3).
- **Exact and near-duplicate statements.** Two pairs are word-for-word duplicates: 186/198 (prescription) and 250/274 (free filing). Near duplicates: 91/199, 118/179, 140/231, 132/262, 270/292, 160/164, 162/190, 134/243, 93/284, 235/265 and 81/151/215 (trimmer line).
- **Repeated narrative details.**
  - "disputing two line items" (184, 217);
  - "because a signature page was missing" (149, 216, word for word);
  - "one application went back for a missing …" (105, 196);
  - "payment comes in 21 days" (98, 107, 158);
  - "the linked account did not have enough to cover it" (255, 277, 290, plus 263);
  - "the balance was lower than that" (69, 178, 276);
  - "not enough on hand or on any card" (95, 160);
  - "a tube and brake pads" (138, 239);
  - "Medicaid pays/covers her Part B premium" (2, 7, 30, 41).
- **Past event in the "When" clause.** 12 statements put a past event before a present "I want": 40, 91, 117, 118, 173, 176, 179, 199, 238, 243, 269, 279. "Now that …" reads better.
- **Static conditions in place of triggers.** About 7 statements open with a standing condition rather than a trigger: 3, 6, 31, 41, 200, 250, 274 ("When the household lives on about $18,000 a year", "When my taxes are simple this year").
- **Invented precise figures.** These figures are not on the cards: 8, 125, 135, 165 (14.6 gallons), 180, 191, 203, 210, 235, 265, 297 ("4 card sales"), and 98/107/158 (21 days). The net pay in 34 and 48 and the premium deductions in 14, 20 and 35 may come from linked records; if so, they are fine.
- **Invented medical reasons.** 45 (low blood sugar), 64 (surgery), 102 (knee since the service), 253 (accident), 159 (cane), plus lighter ones in 108, 125, 161 (blood pressure) and 241 (knee).
- **Distance.** Six narratives add "round trip" (159, 190, 200, 226, 267, 268), while others treat the same field as one way (50, 112, 123, 173, 176, 182). Several time and distance pairs are impossible: 123 has 65.5 mi in 8 min, 159 has 74.3 mi plus therapy in 53 min, and 190 has 70.1 mi in 16 min. Decide what the distance field means before writing about it.
- **Income-tax withholding records.** Three cards treat these as federal plus state although the payee is the IRS (1, 55, 57). The record type seems to lump state tax in with the IRS.
- **Mandatory taxes framed as wants.** 15 payroll-tax statements say "I want to have … taken out". That is acceptable for the job-statement form, but the wording is the same every time.
- **kept_availability_open, partial outcome.** Both cards (76, 100) say the call never came. Confirm that this is what "partial" means.
- **Record problems the writer worked around.** These are not text faults, but worth a look:
  - 46 (EITC at $198,604);
  - 116 (Medicare for a 42-year-old);
  - 67 (a dishwasher's 6-hour shift at $33.94 an hour);
  - 128 (SSI in a $100,565 household);
  - 74, 89, 147 (free school meals in high-income households);
  - 281 (Medicaid for a single man at $39,073).

### 4. Overall

The hand-written text is mostly faithful. Nearly every sum, fee and difference I could compute checks out, and the voice is plain and human. 23 cards contradict their own fields or state a wrong rule. Most of these are household, work or relationship facts (rent versus mortgage, weekly versus biweekly pay, a "brother" who is a 72-year-old woman, a woman with a vision disability who drives, a nursing home that is a hospital), plus one real-rule error (the EITC at $198,604). The larger quality problem is sameness: within a record type the statements are near copies, more than a quarter end "so I can keep", and a few invented specifics ("$40 a month", "21 days", "two line items", "signature page") repeat from card to card.
