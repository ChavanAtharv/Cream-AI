# Evaluation results

| Config | Chunk words | Overlap | Top-k | Max distance | Chunks | Passed | Know/don't-know correct | Right source | Key fact present |
|---|---|---|---|---|---|---|---|---|---|
| A | 150 | 30 | 4 | 1.2 | 215 | 12/15 | 12/15 | 12/15 | 13/15 |
| B | 250 | 50 | 3 | 1.2 | 139 | 14/15 | 14/15 | 14/15 | 14/15 |

Winner: B

## Per question

| # | Question | Expected | Config A | Config B |
|---|---|---|---|---|
| 1 | I'm 25 years old. Can I enrol in Atal Pension Yojana? | answer | PASS (answered) | PASS (answered) |
| 2 | What insurance coverage does PMJJBY provide? | answer | PASS (answered) | PASS (answered) |
| 3 | I sell vegetables on a cart. Can I get a working capital loan without collateral? | answer | PASS (answered) | FAIL (I don't know) |
| 4 | What benefits does PM Vishwakarma provide to traditional artisans? | answer | PASS (answered) | PASS (answered) |
| 5 | Who is eligible for rural housing assistance under PMAY-G? | answer | PASS (answered) | PASS (answered) |
| 6 | What is the current application deadline for PM-KISAN? | I don't know | PASS (I don't know) | PASS (I don't know) |
| 7 | Can a farmer who pays income tax receive PM-KISAN benefits? | answer | PASS (answered) | PASS (answered) |
| 8 | What is the annual financial benefit provided under PM-KISAN? | answer | PASS (answered) | PASS (answered) |
| 9 | Who can apply for the DPIIT Internship Scheme? | answer | PASS (answered) | PASS (answered) |
| 10 | What is the next intake date for the DPIIT Internship Scheme? | answer | PASS (answered) | PASS (answered) |
| 11 | What monthly pension does PM-KMY provide? | answer | FAIL (I don't know) | PASS (answered) |
| 12 | At what age does the PM-KMY pension start? | answer | FAIL (I don't know) | PASS (answered) |
| 13 | Can a government employee get PM-KISAN? | answer | FAIL (I don't know) | PASS (answered) |
| 14 | What is the current interest rate on PPF? | I don't know | PASS (I don't know) | PASS (I don't know) |
| 15 | Which scheme gives free laptops to students? | I don't know | PASS (I don't know) | PASS (I don't know) |

## Details: config A

| # | Expected | Got | Closest distance | Cited files | Pass | Answer (start) |
|---|---|---|---|---|---|---|
| 1 | answer | answered | 0.8074 | apy_guidelines.pdf | PASS | Yes, you can enrol in Atal Pension Yojana because you are 25 years old, which is within th |
| 2 | answer | answered | 0.6438 | pmjjby_guidelines.pdf | PASS | PMJJBY offers a one‑year life insurance cover of Rs. 2 lakh for death due to any reason, w |
| 3 | answer | answered | 1.1938 | pm_svanidhi_guidelines.pdf | PASS | Yes, as a street vendor selling vegetables you appear to meet the conditions for the PM‑SV |
| 4 | answer | answered | 0.5979 | pm_vishwakarma_myscheme_tabs.pdf | PASS | PM Vishwakarma gives artisans recognition as Vishwakarma with a digital ID and certificate |
| 5 | answer | answered | 0.7499 | pmayg_myscheme_tabs.pdf | PASS | Eligible rural households are those that are houseless or live in zero, one or two‑room ku |
| 6 | I don't know | I don't know | 0.9904 | - | PASS | I don't know. The provided sources cover operational guidelines, portal details, and schem |
| 7 | answer | answered | 0.6474 | pm_kisan_operational_guidelines.pdf | PASS | No, a farmer who paid income tax in the last assessment year is excluded from receiving PM |
| 8 | answer | answered | 0.6433 | pm_kisan_faq.pdf, pm_kisan_operational_guidelines.pdf | PASS | The annual financial benefit under PM‑KISAN is Rs.6000 per year per eligible farmer family |
| 9 | answer | answered | 0.5133 | dpiit_guidelines.pdf | PASS | Students pursuing an undergraduate, postgraduate or research degree in Engineering, Manage |
| 10 | answer | answered | 0.5979 | dpiit_guidelines.pdf | PASS | The next intake for the DPIIT Internship Scheme opens on 1st March each year. |
| 11 | answer | I don't know | 0.7046 | - | FAIL | I don't know. The provided sources cover operational guidelines for PM-KMY and Atal Pensio |
| 12 | answer | I don't know | 0.7371 | - | FAIL | I don't know. The sources cover Atal Pension Yojana guidelines and PM-KMY operational guid |
| 13 | answer | I don't know | 0.9138 | - | FAIL | I don't know. The sources cover eligibility for landholding farmers and the operational de |
| 14 | I don't know | I don't know | 1.0787 | - | PASS | I don't know. The provided source does not cover the interest rate on PPF. |
| 15 | I don't know | I don't know | 1.2464 | - | PASS | I don't know. I could not find this in the documents I have. |

## Details: config B

| # | Expected | Got | Closest distance | Cited files | Pass | Answer (start) |
|---|---|---|---|---|---|---|
| 1 | answer | answered | 0.8057 | apy_guidelines.pdf | PASS | Yes, you appear to meet the age requirement for enrolling in the Atal Pension Yojana. The  |
| 2 | answer | answered | 0.8035 | pmjjby_guidelines.pdf | PASS | PMJJBY offers a one‑year life insurance cover for death due to any reason, which can be re |
| 3 | answer | I don't know | 1.2376 | - | FAIL | I don't know. I could not find this in the documents I have. |
| 4 | answer | answered | 0.8068 | pm_vishwakarma_myscheme_tabs.pdf | PASS | PM Vishwakarma gives artisans a range of benefits: recognition as a Vishwakarma with a cer |
| 5 | answer | answered | 0.7913 | pmayg_myscheme_tabs.pdf | PASS | Eligible beneficiaries are all houseless households living in zero, one, or two‑room house |
| 6 | I don't know | I don't know | 1.0073 | - | PASS | I don't know. The provided sources cover operational guidelines, portal details, and benef |
| 7 | answer | answered | 0.6361 | pm_kisan_operational_guidelines.pdf | PASS | No, a farmer who paid income tax in the last assessment year appears to be excluded from r |
| 8 | answer | answered | 0.6987 | pm_kisan_faq.pdf, pm_kisan_operational_guidelines.pdf | PASS | The annual financial benefit under PM‑KISAN is Rs.6000 per year per eligible farmer family |
| 9 | answer | answered | 0.5621 | dpiit_guidelines.pdf | PASS | Students pursuing Graduation/Post‑Graduation/Research in Engineering, Management, Law, Eco |
| 10 | answer | answered | 0.5925 | dpiit_guidelines.pdf | PASS | The next intake period for the DPIIT Internship Scheme is from 1st March to 30th April. |
| 11 | answer | answered | 0.7498 | pm_kmy_operational_guidelines.pdf | PASS | The PM‑KMY scheme provides an assured monthly pension of Rs. 3000 to eligible small and ma |
| 12 | answer | answered | 0.7656 | pm_kmy_operational_guidelines.pdf | PASS | The PM‑KMY pension starts when the farmer reaches 60 years of age. |
| 13 | answer | answered | 0.9727 | pm_kisan_operational_guidelines.pdf | PASS | No, government employees are excluded from the PM‑Kisan scheme. The operational guidelines |
| 14 | I don't know | I don't know | 1.2285 | - | PASS | I don't know. I could not find this in the documents I have. |
| 15 | I don't know | I don't know | 1.2433 | - | PASS | I don't know. I could not find this in the documents I have. |

## Failed answers in full: config A

**Q11** (expected an answer; cited: none)

> I don't know. The provided sources cover operational guidelines for PM-KMY and Atal Pension Yojana but do not state the monthly pension amount for PM-KMY.

**Q12** (expected an answer; cited: none)

> I don't know. The sources cover Atal Pension Yojana guidelines and PM-KMY operational guidelines but do not specify the age at which PM-KMY pension starts.

**Q13** (expected an answer; cited: none)

> I don't know. The sources cover eligibility for landholding farmers and the operational details of the PM-KISAN scheme, but they do not mention whether government employees are eligible.


## Failed answers in full: config B

**Q3** (expected an answer; cited: none)

> I don't know. I could not find this in the documents I have.


## What I noticed

Config B (250-word chunks, top 3) passed 14 of 15 questions and config A (150-word chunks, top 4) passed 12 of 15, so I am keeping config B. Both configs said "I don't know" correctly for the PM-KISAN deadline (Q6), the PPF rate (Q14) and the free laptops question (Q15). In config A, Q11, Q12 and Q13 failed because the model said "I don't know" even though the documents contain the answer; the small chunks seem to have separated the fact (the pension amount, the start age, the excluded groups) from its context, and the larger chunks in B kept them together. Config B's one failure was Q3: its closest chunk was at distance 1.2376, just over my 1.2 limit, so it was dropped before the model saw it, while the off-topic PPF question reached 1.2285 in the same run, so distance alone cannot separate relevant from irrelevant chunks. Q10 first looked like a failure, but the DPIIT guidelines do list two intake windows, so I corrected the expectation, and Q2 first failed only because my keyword check missed the non-breaking spaces the model writes. Answers vary a little between runs and there are only 15 questions, so a two-row gap is weak evidence, and the PM-KISAN guidelines date from 2020, so the documents may be out of date.