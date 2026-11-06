"""Day 2 scheme records.

The first nine records contain details assembled during prior myScheme research.
The remaining eleven are shortlist candidates with details deliberately left
blank until verified against the live Central filter and official scheme pages.
"""

schemes = [
    {
        "id": "APY", "scheme_name": "Atal Pension Yojana (APY)",
        "category": "Banking, Financial Services and Insurance",
        "ministry": "Ministry of Finance",
        "benefit": "Guaranteed minimum monthly pension of ₹1,000 to ₹5,000 from age 60, based on contribution and joining age.",
        "eligibility": "Indian citizens aged 18–40 with a savings bank or post-office account; income-tax payers are excluded from new enrolment under the applicable rule.",
        "documents": ["Savings bank or post-office account details", "Aadhaar details/authentication", "Enrolment and consent form", "Nominee details"],
        "source_url": "https://www.myscheme.gov.in/schemes/apy",
        "verification_status": "details_from_prior_research"
    },
    {
        "id": "PMJJBY", "scheme_name": "Pradhan Mantri Jeevan Jyoti Bima Yojana (PMJJBY)",
        "category": "Banking, Financial Services and Insurance",
        "ministry": "Ministry of Finance",
        "benefit": "Life insurance cover of ₹2 lakh for death due to any cause, subject to scheme terms.",
        "eligibility": "Savings bank or participating post-office account holders aged 18–50 who consent to premium deduction.",
        "documents": ["Enrolment and consent form", "Account details", "KYC identity proof", "Nominee details"],
        "source_url": "https://www.myscheme.gov.in/schemes/pmjjby",
        "verification_status": "details_from_prior_research"
    },
    {
        "id": "PM_SVANIDHI", "scheme_name": "PM Street Vendor's AtmaNirbhar Nidhi (PM SVANidhi)",
        "category": "Business & Entrepreneurship",
        "ministry": "Ministry of Housing and Urban Affairs",
        "benefit": "Progressive collateral-free working-capital loan tranches, interest subsidy and digital-transaction incentives under scheme rules.",
        "eligibility": "Eligible street vendors identified by the Urban Local Body or holding the applicable vendor certificate, identity card or Letter of Recommendation.",
        "documents": ["Certificate of Vending/vendor identity card or eligible Letter of Recommendation", "Aadhaar", "KYC details", "Bank account details"],
        "source_url": "https://www.myscheme.gov.in/schemes/pm-svanidhi",
        "verification_status": "details_from_prior_research"
    },
    {
        "id": "PM_VISHWAKARMA", "scheme_name": "PM Vishwakarma",
        "category": "Business & Entrepreneurship",
        "ministry": "Ministry of Micro, Small and Medium Enterprises",
        "benefit": "Recognition, skill training, toolkit incentive, concessional collateral-free enterprise loans and other support under scheme rules.",
        "eligibility": "Artisans and craftspeople aged 18 or above working in one of the 18 notified traditional trades, subject to scheme exclusions.",
        "documents": ["Aadhaar", "Aadhaar-linked mobile number", "Bank account details", "Ration card or family Aadhaar details where applicable", "Trade details"],
        "source_url": "https://www.myscheme.gov.in/schemes/pm-vishwakarma",
        "verification_status": "details_from_prior_research"
    },
    {
        "id": "PMAY_G", "scheme_name": "Pradhan Mantri Awaas Yojana - Gramin (PMAY-G)",
        "category": "Housing & Shelter",
        "ministry": "Ministry of Rural Development",
        "benefit": "Housing assistance for eligible rural households, with applicable toilet and wage-employment convergence.",
        "eligibility": "Eligible rural houseless households and households in qualifying kutcha houses, identified through applicable beneficiary lists and verification.",
        "documents": ["Beneficiary identity and household details", "Bank or post-office account details", "Additional information requested during local verification"],
        "source_url": "https://www.myscheme.gov.in/schemes/pradhan-mantri-awaas-yojana-gramin",
        "verification_status": "details_from_prior_research"
    },
    {
        "id": "PMAY_U", "scheme_name": "Pradhan Mantri Awas Yojana - Urban (PMAY-U)",
        "category": "Housing & Shelter",
        "ministry": "Ministry of Housing and Urban Affairs",
        "benefit": "Urban housing support through applicable construction, partnership, rental-housing and interest-subsidy components.",
        "eligibility": "Eligible urban households in applicable income groups, subject to house-ownership, prior-benefit and component-specific conditions.",
        "documents": ["Aadhaar details", "Income proof/self-declaration", "Identity and address proof", "Bank details", "Land/property documents where applicable"],
        "source_url": "https://www.myscheme.gov.in/schemes/pmay-u",
        "verification_status": "details_from_prior_research"
    },
    {
        "id": "DPIIT_INTERNSHIP", "scheme_name": "DPIIT Internship Scheme",
        "category": "Education & Learning",
        "ministry": "Ministry of Commerce and Industry - DPIIT",
        "benefit": "Internship exposure within DPIIT, stipend and experience certificate subject to the current scheme notice.",
        "eligibility": "Students in eligible undergraduate, postgraduate or research programmes and disciplines, subject to the current DPIIT notice.",
        "documents": ["Online application details", "Educational and personal information requested by the portal", "Any supporting documents specified in the current notice"],
        "source_url": "https://www.myscheme.gov.in/schemes/dpiit-is",
        "verification_status": "details_from_prior_research"
    },
    {
        "id": "PM_KISAN", "scheme_name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "category": "Agriculture, Rural & Environment",
        "ministry": "Ministry of Agriculture and Farmers Welfare",
        "benefit": "₹6,000 per year to eligible landholding farmer families in three equal instalments through direct benefit transfer.",
        "eligibility": "Eligible landholding farmer families, subject to institutional-landholder and specified category-based exclusions.",
        "documents": ["Aadhaar", "Landholding records", "Bank account details", "Farmer/family details", "Registration information"],
        "source_url": "https://www.myscheme.gov.in/schemes/pm-kisan",
        "verification_status": "details_from_prior_research"
    },
    {
        "id": "KCC", "scheme_name": "Kisan Credit Card (KCC)",
        "category": "Agriculture, Rural & Environment",
        "ministry": "Ministry of Agriculture and Farmers Welfare",
        "benefit": "Credit access for eligible crop cultivation and specified agriculture and allied requirements.",
        "eligibility": "Eligible owner cultivators, tenant farmers, oral lessees, sharecroppers and qualifying farmer groups.",
        "documents": ["Application form", "Identity/address proof", "Landholding or cultivation proof", "Cropping and acreage details", "Bank-required documents"],
        "source_url": "https://www.myscheme.gov.in/schemes/kcc",
        "verification_status": "central_filter_status_pending"
    },
    {
        "id": "PMFBY", "scheme_name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "category": "Agriculture, Rural & Environment", "ministry": None, "benefit": None,
        "eligibility": None, "documents": [], "source_url": "https://www.myscheme.gov.in/search",
        "verification_status": "candidate_details_and_central_filter_pending"
    },
    {
        "id": "PMJAY", "scheme_name": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (AB PM-JAY)",
        "category": "Health & Wellness", "ministry": None, "benefit": None,
        "eligibility": None, "documents": [], "source_url": "https://www.myscheme.gov.in/search",
        "verification_status": "candidate_details_and_central_filter_pending"
    },
    {
        "id": "MUDRA", "scheme_name": "Pradhan Mantri MUDRA Yojana (PMMY)",
        "category": "Business & Entrepreneurship", "ministry": None, "benefit": None,
        "eligibility": None, "documents": [], "source_url": "https://www.myscheme.gov.in/search",
        "verification_status": "candidate_details_and_central_filter_pending"
    },
    {
        "id": "PMUY", "scheme_name": "Pradhan Mantri Ujjwala Yojana (PMUY)",
        "category": "Utility & Sanitation", "ministry": None, "benefit": None,
        "eligibility": None, "documents": [], "source_url": "https://www.myscheme.gov.in/search",
        "verification_status": "candidate_details_and_central_filter_pending"
    },
    {
        "id": "PMJDY", "scheme_name": "Pradhan Mantri Jan Dhan Yojana (PMJDY)",
        "category": "Banking, Financial Services and Insurance", "ministry": None, "benefit": None,
        "eligibility": None, "documents": [], "source_url": "https://www.myscheme.gov.in/search",
        "verification_status": "candidate_details_and_central_filter_pending"
    },
    {
        "id": "PMSBY", "scheme_name": "Pradhan Mantri Suraksha Bima Yojana (PMSBY)",
        "category": "Banking, Financial Services and Insurance", "ministry": None, "benefit": None,
        "eligibility": None, "documents": [], "source_url": "https://www.myscheme.gov.in/search",
        "verification_status": "candidate_details_and_central_filter_pending"
    },
    {
        "id": "SSY", "scheme_name": "Sukanya Samriddhi Account Scheme",
        "category": "Women & Child", "ministry": None, "benefit": None,
        "eligibility": None, "documents": [], "source_url": "https://www.myscheme.gov.in/search",
        "verification_status": "candidate_details_and_central_filter_pending"
    },
    {
        "id": "NSS", "scheme_name": "National Scholarship Scheme",
        "category": "Education & Learning", "ministry": None, "benefit": None,
        "eligibility": None, "documents": [], "source_url": "https://www.myscheme.gov.in/search",
        "verification_status": "candidate_details_and_central_filter_pending"
    },
    {
        "id": "PM_SYM", "scheme_name": "Pradhan Mantri Shram Yogi Maandhan (PM-SYM)",
        "category": "Social Welfare & Empowerment", "ministry": None, "benefit": None,
        "eligibility": None, "documents": [], "source_url": "https://www.myscheme.gov.in/search",
        "verification_status": "candidate_details_and_central_filter_pending"
    },
    {
        "id": "PM_KMY", "scheme_name": "Pradhan Mantri Kisan Maandhan Yojana (PM-KMY)",
        "category": "Agriculture, Rural & Environment", "ministry": None, "benefit": None,
        "eligibility": None, "documents": [], "source_url": "https://www.myscheme.gov.in/search",
        "verification_status": "candidate_details_and_central_filter_pending"
    },
    {
        "id": "PMGSY", "scheme_name": "Pradhan Mantri Gram Sadak Yojana (PMGSY)",
        "category": "Agriculture, Rural & Environment", "ministry": None, "benefit": None,
        "eligibility": None, "documents": [], "source_url": "https://www.myscheme.gov.in/search",
        "verification_status": "candidate_details_and_central_filter_pending"
    },
]
