# Medianville v2 close reading: the second reader's report

Written 2026-11-21 by a separate Claude agent that saw only the 200 record cards (no code, no repository, no web); see [the close reading](medianville-v2-close-reading.md) for the sample and what was done with it. Card numbers refer to the cards `tools/sample_records.py` draws with salt 700 from the v2 baseline day and five typed days. Kept as written.

Read from the cards alone. All 200 read.

### 1. Patterns (most serious first)

**P1. Housing costs that equal or exceed household income.** Five cards have a mortgage payment larger than the household's whole income: 12 ($2,903/mo on $25,900, 134%), 17 ($1,349 on $14,451, 112%), 40 ($2,319 on $14,497, 192%), 93 ($2,873 on $26,042, 132%), 135 ($1,807 on $16,695, 130%). Another eight put housing at 57-90% of gross: 52, 53, 63, 80, 101, 107 ($8,357/mo for a construction laborer household), 134, 148. "Owner free and clear" households show monthly costs of $2,000-2,500: 11 ($2,214), 15 ($2,500 on $14,959), 36 ($2,500 on $13,313), 78 ($2,476 on $16,648), 106 ($2,275), 143 ($2,081). The same $2,500 shows up twice, which looks like a cap. Why it breaks: lenders cap debt-to-income at about 43-50%, so a poverty household cannot carry a mortgage bigger than its income. A paid-off house costs only property tax plus insurance, usually $250-700 a month in a median county. This is the most frequent "that can't be right" in the sample. About 19 cards.

**P2. Health-claim money does not add up.** In 53, 124, 125 and 129 the insurer pays exactly 45% of gross (9.83/21.84, 13.97/31.04, 2.70/5.99, 81.72/181.59), the patient pays $0, and the rest is unexplained. In 24, $418.28 + $1,254.85 = $1,673.13 against a $2,040.40 gross, leaving $367 unaccounted for. In 165, $5.00 + $0.68 against $12.63. In 172, a $12 copay with no plan payment against $24.66. Card 81 has Medicare paying $68.67 of $262.90, with "$194.23 more will be billed later". Medicare assignment does not work that way: Part B pays 80% of the allowed amount, the patient owes 20%, and the rest is written off. Card 53 bills a 6.9-hour ER stay at $181.59 (real charges run $1,500-3,000+). It then says "About $182 more will be billed later", which is the whole gross even though $81.72 was already paid. Why it breaks: a reader expects gross = plan paid + patient paid + contractual adjustment. A fixed 45% with a $0 copay reads as a formula. 8 cards.

**P3. SSI paid where the income and deeming rules forbid it, and SSI recipients missing Medicaid.** Spouse's or parents' income is deemed to the SSI claimant and would wipe out the benefit in 29 (about $1,007/mo SSI next to a spouse earning about $63k), 53 (SSI next to $34k of spouse wages), 75 (a married couple with $39k income plus investment draws), 107 (SSI in a household with $151k of wages), 175 (SSI next to $65k of parent income) and 183 (SSI for a full-time regional manager in a $227k household). In 27 and 53 the SSI recipient is Medicare-only or uninsured and pays his own Part B. In most states SSI brings Medicaid automatically, and with it the state Part B buy-in. In 70 a 93-year-old lives on $705/mo of Social Security with no SSI, though she plainly qualifies for the roughly $1,029 federal benefit rate. 9 cards.

**P4. Statement and narrative templates that contradict the person.** Work talk from people who don't work, or don't work days: 29 (NILF, "so I can still get to work"), 45 (night-shift bartender at 7 a.m., "so I can get to work"), 50 (NILF TANF father, "on the way to work"), 131 (student, "look right for work"), 196 (retiree, "between work and everything else"). Job framing that doesn't fit: 51 (self-employed stylist, "without losing my job"), 67 (food vendor, "before the customer paid"). Legal and civic framing that doesn't fit: 59 (probation review, "avoid a default"), 110 (parking ticket, "avoid a warrant"), 80 (an electric utility's "promotional rate that expired"), 140 (a Hindu temple, "when the plate comes around... my church"). Gas talk from people with no car: 134 and 190 ("buy gas" with 0 vehicles). Money talk from people with no income: 184 ($0 income, "when my check lands"). Statement says new, narrative says refill: 124, 125, 165 ("calls in something new" against "generic refill"). Narrative errors: 88 ("Helped my child (5) with sorting pills and paying bills"), 57 (follows a failed nurse visit but says the aide missed; "1 hours"), 150 ("When I am building a water heater swap"), 161 ("a appraiser"). Statement and narrative disagree: 143 and 199. About 23 cards. Why it breaks: an outside reader catches these on first read, and each one exposes the template.

**P5. Coverage that does not match eligibility.** The sample shows many poverty adults on Medicaid (17, 18, 19, 22, 46's peers), which implies an expansion state. Yet adults with $0 or near-$0 income are uninsured in 15, 46, 62, 88, 96, 102, 104 and 109. Card 86 has marketplace coverage at $0 income, where there are no subsidies below 100% FPL. Card 35 has a family-of-4 marketplace premium of $220/mo at $458k income; unsubsidized family premiums run $1,500+. Card 3 puts a full-time manufacturing mechanic on the marketplace. Card 71 is a long-stay nursing home resident on Medicare Advantage only, with $18.6k income. Medicare does not pay custodial care, so she would be on Medicaid. Card 76 is a veteran drawing about $3,900/mo in VA compensation (about a 100% rating), listed as uninsured. Cards 75 and 141 are full duals at about 137% FPL and above. Card 81 sends a 69-year-old to "Foundry District Pediatrics". About 17 cards.

**P6. Placeholder counterparties and reversed invoices.** "Out-of-area employers" is printed as the employer name in 18, 151 and 152. "Customers (general public)" is coded as "Other services (repair, salons, religious organizations), Outside Medianville". It pays a $33k fabrication invoice (47), a $1.19M axle invoice (128), cash tips (134, 190) and a local shop's day of card sales (136). It also stands in for a private used-car seller (91) and for a contractor's overdue client (198). In 47 and 128 the "outbound shipment invoiced" runs From the customer To the manufacturer, which is backwards. Card 138's scammer is coded as a salon/religious-services business. 12 cards. Why it breaks: these are the database's seams showing, and the sector code is absurd for the role.

**P7. Distances and times that a 100k-person county cannot produce.** Several trips cover 60-80 miles one way inside "Medianville": 61 (59.6 mi), 62 (77.8), 84 (76), 105 (79.1), 122 (70). Meanwhile card 70 puts Open country 1.4 miles from a Satellite city fuel mart. The time field often ignores travel. In 61, a 119-mile round trip takes 12 minutes in total. In 105, 158 miles take 11 minutes. Card 62 does 156 miles in 45 non-wait minutes. Cards 59, 60, 115, 118, 131 and 181 have the same problem at smaller scale. Waits are longer than the total time in 110 (60 in 27), 111 (13 in 7), 124 (18 in 10), 129 (19 in 10) and 196 (8 in 6). Cards 59 and 60 carry identical times (143 min, 98 waited). About 17 cards. Why it breaks: a county of 100k is typically 20-40 miles across, and nobody drives 79 miles each way to roll over a title loan when the same chain has a branch nearby (96).

**P8. $0-income households all paying exactly $380 rent with no cash aid.** Cards 62, 65, 66, 86, 102, 104, 109, 127, 140, 160 and 181 all show $0 income and $380 rent. Several also run 1-2 vehicles (65, 127). Only 88 and 184 show subsidized rent ($50) for $0-income families. No one draws TANF, and the disabled adults in 88 and 104 have no SSI. Why it breaks: the identical rent is a visible default, and a family with no income for a year is either on housing assistance, TANF or SSI, or doubled up. 11 cards.

**P9. Job, employer, wage and education mismatches.** Odd employers: a software developer at a pet clinic (142), an engineer at a law firm (73), an appraiser on an apartment complex's payroll (161), a drafter at a marketing firm (125), a janitor at a security firm (72), a "crew supervisor" at a call center in a $458k household (35). Odd institutions: a local post office running its own payroll (8), a "City Schools" payroll covering 13 staff (25). Odd wages: a school cafeteria worker paid $975/week, weekly (11; typical is $25-32k on a school-year schedule), and a full-time campus food worker in a $20k household, about $9.70/hr (132). Card 89 is a home health aide whose household earns $160k all from wages and whose other member is 77, which implies a 77-year-old earning about $125k with no Social Security. Graduate degrees show up often in low-wage jobs (3, 4, 89, 106, 168). About 14 cards.

**P10. "Could not cover $400" applied without regard to income, and contradicted by savings.** The note appears on households at $94k-$355k: 23, 31, 106, 107, 122 ($355k), 139, 154, 157, 197, and on about a third of the $90k+ households overall. The Fed's survey puts that rate at roughly 10-15% at those incomes. Cards 63 and 178 move $500 from savings while carrying the same note.

**P11. Program, banking and calendar rules misapplied (smaller, scattered).**
- Free school meals for households above the reduced-price line: 74 ($88k for 3), 175 ($77k for 4), 69 ($54k for 5, over 130% FPL). Community eligibility would explain them, but nothing says so.
- WIC listed for a 48-year-old (40).
- A college student on SNAP with no exemption (109). A "some college" student receiving free school meals (127).
- SSDI paid alongside earnings above the substantial-gainful-activity level (34, 157).
- Nursing-home Medicaid paying the full $274 with no resident share (1, 169). The resident's income goes to patient liability. The same $274 rate also appears at two different facilities.
- Mortgage escrow posted to the county monthly (12, 183). The servicer holds escrow and pays the county once or twice a year.
- Federal withholding taken from married filers at $14-15k (15, 17), where the W-4 math gives $0.
- Lottery bought on a credit card (68), which most states bar at retail.
- ACH and check runs on Independence Day observed (177, 179, 183) and an ACH debit at 11 p.m. Saturday (200).
- Child care subsidy paid from "State EBT (SNAP, WIC, TANF)" (162, 170, 177).
- The same courthouse charges $62 and $76 for a marriage license (65, 115).
- "55 days after invoice" on three vendor payments (166, 174, 179). "$135 owed in all" on two different fines (110, 123).

**P12. Narrative amounts or channels that disagree with the fields.**
- Card 10's refund field reads $924.64 while the narrative says "$9083.80 in all".
- Card 160's narrative charges a $0.43 fee that the money fields don't show. The cash-out also goes from an unbanked person "to my bank".
- Card 138's narrative says a wire from the branch; the payment field says ach/phone.
- Card 62 failed, yet LIHEAP is recorded as paying $42.

A related label problem: "paid by the person" appears on business and government payers (6, 8, 25, 28, 77, 174 and others) and on income records, where it holds the fee.

### 2. Card by card

1. Medicaid pays the full $274 day with $0 from a resident who has $12,384/yr of Social Security; patient liability should take most of it.
3. Full-time manufacturing mechanic on marketplace coverage; FICA of $292.64 implies about $99k/yr; a "roommates" household with $398k, a mortgage and 4 vehicles.
5. $113/week federal withholding is too high for a married household at $51.5k in total; part-time car sales on a fixed weekly schedule.
7. SSI near the federal maximum while the listed veteran's household draws VA compensation, which offsets SSI dollar for dollar.
8. A local post office does not run payroll or remit employer taxes; USPS payroll is national.
10. Refund field $924.64 against a narrative of $9,083.80; a NILF single parent in a household where wages are 98% of income.
11. School cafeteria worker at $975/week paid weekly; a free-and-clear owner paying $2,214/mo.
12. Mortgage $2,903/mo on $25,900; escrow does not go to the county monthly.
13. SNAP $538 for 2 on $1,331/mo income is near the maximum allotment.
15. Free-and-clear housing at $2,500/mo on $14,959; federal withholding at an income that owes nothing.
17. Mortgage of $16,188/yr against income of $14,451; withholding at that income.
18. Employer printed as "Out-of-area employers"; his part-time pay ($27k/yr) exceeds the household's $22,143.
24. $418.28 + $1,254.85 does not reach the $2,040.40 gross.
25. A school district payroll "covering 13 on staff".
27. SSI recipient on Medicare only, paying his own Part B; "payroll_deduction" for a Social Security deduction.
29. SSI next to a spouse earning about $63k; NILF but the statement says "get to work".
34. SSDI recipient earning about $1,800/mo, above the substantial-gainful-activity level.
35. Family marketplace premium of $220/mo at $458k; call-center "crew supervisor".
36. Free-and-clear housing at $2,500/mo on $13,313.
37. Fast food withholding of $168 biweekly implies pay well above fast-food wages.
40. WIC for a 48-year-old; mortgage $2,319/mo on $14,497; a poverty household living only on investment draws.
44. "Fuel card fee" on a debit purchase.
45. Night bartender's 7 a.m. dropoff "so I can get to work".
46. Uninsured at poverty income in an apparent expansion state.
47. $33k fabrication invoice paid by "Customers (general public)" coded as salons/religious services; direction reversed; "partial" outcome unexplained.
49. Unbanked 28-year-old owns free and clear at $150/mo; commutes across districts with 0 vehicles.
50. NILF TANF parent "on the way to work".
51. Self-employed stylist "without losing my job".
52. Rent is 71% of income.
53. ER stay of 6.9 hours billed $181.59; "$182 more" contradicts the $81.72 already paid; SSI recipient uninsured; SSI next to spouse wages; mortgage at 69% of income.
57. Follows a nurse visit but the narrative names an aide; "1 hours".
59. Probation review framed as "avoid a default"; 55 miles plus the hearing in 45 non-wait minutes; times identical to 60.
60. Same 143/98 minutes as 59; 40.5 miles between two districts.
61. 59.6 miles each way to hand over $75, in 12 minutes total.
62. Uninsured at $0 income; 77.8 miles each way in 45 non-wait minutes; a failed application with $42 of LIHEAP recorded as paid.
63. Moves $500 from savings while flagged as unable to cover $400; mortgage at 62% of income.
65. A $0-income two-person household with 2 vehicles; license $62 here and $76 on card 115.
67. Food vendor's narrative uses the contractor line "before the customer paid".
68. Lottery tickets on credit; narrative fragment "on the way out".
69. "Prairie Crossing Elementary" filed under Tolliver County Schools; free meals at $54k for 5.
70. Lives on $705/mo with no SSI; Open country 1.4 miles from Satellite city.
71. Long-stay nursing home resident with no Medicaid on $18.6k.
72. Janitor employed by a security company.
73. Part-time engineer at a law firm.
74. Free school meals at $88k for 3.
75. SSI and full dual status for a couple at $39k with investment income.
76. Roughly 100%-rated veteran listed uninsured; first driver's license at 58.
77. Pest control firm paying $8,327/mo commercial rent to a townhome community.
78. Free-and-clear housing at $2,476/mo on $16,648.
80. "Promotional rate" at a regulated electric utility; mortgage at 62% of income.
81. 69-year-old at a pediatrics office; Medicare pays 26% and the patient is billed the rest.
84. Cattle farmer renting downtown; 76 miles to the county sale barn.
86. Marketplace coverage at $0 income.
88. A 5-year-old "sorting pills and paying bills"; uninsured disabled adult in a $0-income family of 6.
89. Household income of $160k all from wages, with a 77-year-old spouse and a home health aide.
90. Assisted living at $6,332/mo on $2,430/mo income, with no assets shown.
91. Private car seller recorded as "Customers (general public)"; household still shows 2 vehicles.
93. Mortgage $2,873/mo on $26,042.
99. Concrete contractor paid for "unit repair".
102. Uninsured at $0 income.
104. $0-income couple, disabled 29-year-old spouse with no SSI; a "caregiving visit" to a spouse in the same home.
105. 79 miles each way to a title lender that has a nearer branch, in 11 minutes.
106. Free-and-clear housing at $2,275/mo.
107. $8,357/mo mortgage for a laborer household; SSI next to $151k of wages.
108. First license at 52 in a 4-vehicle household; proof of insurance is not the usual missing document for a first license.
109. College student on SNAP with no exemption; $0 income paying rent.
110. Parking ticket "avoid a warrant"; a 60-minute wait inside a 27-minute total; $135 again.
111. Wait longer than the total time.
114. "When the lease is ending" for a man with 0 vehicles who walked to the dealer.
115. License price differs from card 65 at the same courthouse; 42 miles in 17 non-wait minutes.
118. 17.6 miles each way for $36 at a variety store.
122. $355k household flagged as unable to cover $400; an inner-suburbs farmer 70 miles from the sale barn.
123. Same $135 as card 110.
124. $12 of the gross unaccounted for; wait longer than the total time; statement says "new", narrative says refill.
125. Same 45% plan share and $0 copay; drafter at a marketing firm.
127. "Some college" student on free school meals.
128. $1.19M axle shipment billed to "Customers (general public)", direction reversed.
129. Plan pays $2.70 of $5.99, copay $0; wait longer than the total time.
131. Student "look right for work"; 46 miles round trip for a haircut in 30 non-wait minutes.
132. Full-time campus food worker household at $20k.
134. Tips from "Customers (general public)"; "buy gas" with 0 vehicles; mortgage at 69% of income.
135. Mortgage $1,807/mo on $16,695.
136. Local shop's sales coded as coming from Outside Medianville.
138. Narrative says wire at the branch, field says ach/phone; underbanked at $217k.
140. Hindu temple offering framed as the plate at "my church".
141. Full dual at about 137% FPL.
142. Software developer at a pet clinic.
143. Statement says "owe a few dollars", narrative says "sending money to family".
148. Mortgage at 90% of income.
150. "When I am building a water heater swap".
151. "Out-of-area employers".
152. "Out-of-area employers".
154. A credit-card issuer funding an online installment loan.
157. SSDI next to substantial self-employment.
158. Rural-town franchise depositing cash at a downtown branch about 78 miles away at night.
160. Fee in the narrative only; unbanked person cashing out "to my bank".
161. Appraiser on an apartment complex payroll at $66k part time; "a appraiser".
162. Child care subsidy paid by "State EBT".
164. Rural-town clerk with 0 vehicles working in Satellite city.
165. $5.00 + $0.68 does not make $12.63; "new" against "refill".
166. "55 days after invoice" (also 174, 179).
169. Same $274 rate as card 1 at another facility; no patient liability on $27k.
170. Child care subsidy paid by "State EBT".
172. Medicare-only member with a $12 copay and no plan payment; half the gross unaccounted for.
174. "ach, in_person"; "55 days" again.
175. Free meals at $77k for 4; SSI next to $65k of household income.
177. ACH settles on a federal holiday.
178. Savings transfer contradicts the $400 note.
179. City check run on July 5, the observed holiday.
181. 59 miles round trip plus shopping in 49 minutes.
183. SSI for a full-time regional manager in a $227k household; escrow posted on a holiday.
184. "When my check lands" at $0 income.
187. Wholesale distributor renting from a duplex LLC.
190. "Buy gas" for a dorm resident with 0 vehicles; tips from "Customers (general public)".
196. Retiree "between work and everything else".
198. "Customers (general public)" as the client; "the answer was that nobody picked up" is garbled.
199. Statement says "help someone", narrative says splitting a tab.
200. Merchant cash advance ACH debit at 11 p.m. Saturday; "fee" friction with no fee amount.

The 8 storm-day cards (161-168) show no sign of the storm (no closures, outages or delays), which a reader would expect at least once.

### 3. What reads true

The transaction mechanics are often right, and right in a way only someone who knows the field would write. Payday loans cost $15 per $100 (34, 41, 117). The title loan rolls over at 25% (105). P2P instant cash-out costs 1.75% (92, 157, 176). An out-of-network ATM costs $4 (70), card processing 2.9% (136), and the merchant cash advance holds back 10% (200). The livestock card deducts commission, yardage and checkoff and sells at "Wednesday's sale" (84, 122). Mailing the October tax bill costs $0.78 in postage (194). LIHEAP funds are gone by March (62). Social Security lands on the 3rd for "pay:3rd" beneficiaries on a Wednesday, and the EITC refund wave arrives March 2. SNAP amounts track the maximum allotments by household size ($306, $562, $1,023, $1,463). SSI-only households sit at the federal benefit rate, and the SSDI+SSI arithmetic on card 55 works out. The Medicaid personal care aide is paid $27.50/hr (100). Free lunch is reimbursed at $4.95. The gas pump math works (107). Withholding splits into federal and state (23, 31). New-car financing carries 7% sales tax and a doc fee (114). The buy-here-pay-here lot takes weekly payments with a starter-interrupt threat (61). Smaller touches also land: the chip won't read and the terminal times out (192, 196), a Wednesday-night church offering (141), the roommate pair on 55 and 68 lines up, a missed aide visit cascades into family members covering it or leaving work (98, 113), and a refund-season cash car purchase (91).

### 4. Overall

Single transactions are believable: fees, benefit amounts, timing and paydays mostly match how American money actually moves. The household profiles behind them often are not. Mortgages exceed income, SSI and Medicaid ignore income and deeming, and coverage contradicts eligibility. On top of that, the templated statements regularly put work, gas or church words in the mouths of people they don't fit. The three fixes that would matter most:
1. Tie housing cost to income: keep debt-to-income at about 50% or less, and cap free-and-clear costs at property tax plus insurance.
2. Run benefit and coverage eligibility off the household's actual income: SSI deeming, SSI→Medicaid, dual and MSP limits, free-meal thresholds, the marketplace floor. Also make every claim close: gross = plan + patient + adjustment.
3. Make statement and narrative text conditional on the person (work status, schedule, vehicles, age, faith, job type), and replace the "Customers (general public)" and "Out-of-area employers" placeholders with real-looking counterparties and correct invoice direction.
