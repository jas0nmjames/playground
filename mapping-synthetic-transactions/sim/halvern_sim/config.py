"""Halvern simulator: parameters, calendar logic and reference tables.

Everything a user is likely to edit lives in PARAMS. Tables below it encode the
calibration anchors from the prompt plus labeled estimates (see assumptions.csv).
"""
import datetime as dt

PARAMS = dict(
    SIM_DATE=dt.date(2027, 3, 3),
    WEATHER="ordinary",          # ordinary | storm | heat
    N_HOUSEHOLDS=41400,          # full city (about 100,000 residents); lower for test runs
    RANDOM_SEED=20270303,
    OUT_DIR="out",
    # scenario shocks (see README): multipliers and incident windows in minutes after midnight
    PURCHASE_FREQ=0.85,          # scales everyday purchase rates (calibrated to ~43 payments per adult per month)
    CASH_MULT=0.64,              # scales the propensity to pay cash (calibrated to ~14% of payments)
    GAS_PRICE=3.29,
    GROCERY_PRICE_MULT=1.0,
    BENEFITS_PORTAL_OUTAGE=(640, 805),      # 10:40-13:25 state benefits portal down
    CARD_READER_OUTAGE=(1025, 1070),        # 17:05-17:50 at one grocery store
    BUS_BREAKDOWN=(435, 500),               # 07:15-08:20 one trunk route short a bus
)

FULL_CITY_HOUSEHOLDS = 41400    # scale 1.0
SALES_TAX = 0.07           # combined state+local, estimate; groceries and Rx exempt
DISTRICTS = ["D1", "D2", "D3", "D4", "D5", "D6"]
DNAME = {"D1": "Downtown and core neighborhoods", "D2": "Inner suburbs", "D3": "Outer suburbs",
         "D4": "Satellite city", "D5": "Rural town", "D6": "Open country"}
DSHARE = {"D1": .31, "D2": .20, "D3": .22, "D4": .13, "D5": .08, "D6": .06}
INTRA = {"D1": 1.4, "D2": 2.8, "D3": 4.2, "D4": 2.3, "D5": 1.6, "D6": 8.5}
_D = {("D1", "D2"): 6, ("D1", "D3"): 13, ("D1", "D4"): 22, ("D1", "D5"): 38, ("D1", "D6"): 33,
      ("D2", "D3"): 9, ("D2", "D4"): 19, ("D2", "D5"): 35, ("D2", "D6"): 30,
      ("D3", "D4"): 17, ("D3", "D5"): 30, ("D3", "D6"): 24,
      ("D4", "D5"): 21, ("D4", "D6"): 15, ("D5", "D6"): 11}
DIST = {}
for (a, b), v in _D.items():
    DIST[(a, b)] = v
    DIST[(b, a)] = v
for d in DISTRICTS:
    DIST[(d, d)] = INTRA[d]
TRANSIT_SERVED = {"D1": 1.0, "D2": .8, "D3": .15, "D4": .35, "D5": 0.0, "D6": 0.0}
HOODS = {
    "D1": ["Downtown", "Courthouse Square", "Northside", "Foundry District", "Riverfront", "Old Depot", "Midtown", "College Hill"],
    "D2": ["Eastgate", "Airport Road", "Millrace", "Southgate", "Kettle Creek", "Garfield Park"],
    "D3": ["Stonebridge", "Fox Hollow", "Sycamore Ridge", "Prairie Crossing", "Lakeshore", "Highland Meadows", "Willow Bend"],
    "D4": ["Ashford Mills", "Mill Street", "Hospital Hill", "Ashford East"],
    "D5": ["Dunmore", "Dunmore Square"],
    "D6": ["Crossroads", "Route 9", "Tolliver Valley"],
}

# ---- sectors (shares of ~48,000 resident jobs; BLS Employment Projections mix given in the prompt)
SECTORS = [
    ("health", "Health care and social assistance", 13.7),
    ("gov", "State and local government (including public schools)", 12.1),
    ("retail", "Retail trade", 9.1),
    ("food", "Accommodation and food services", 8.3),
    ("mfg", "Manufacturing", 7.4),
    ("prof", "Professional, scientific and technical services", 6.3),
    ("self", "Self-employed", 5.8),
    ("admin", "Administrative and support services", 5.3),
    ("constr", "Construction", 4.9),
    ("fin", "Finance and insurance", 4.0),
    ("trans", "Transportation and warehousing", 3.9),
    ("other", "Other services (repair, salons, religious organizations)", 3.9),
    ("whole", "Wholesale trade", 3.6),
    ("pedu", "Private educational services", 2.4),
    ("fed", "Federal government", 1.7),
    ("info", "Information", 1.7),
    ("arts", "Arts, entertainment and recreation", 1.6),
    ("mgmt", "Management of companies", 1.5),
    ("re", "Real estate", 1.4),
    ("ag", "Agriculture, forestry and fishing", 0.9),
    ("util", "Utilities and mining", 0.7),
]
SECNAME = {c: n for c, n, _ in SECTORS}
SECSHARE = {c: s for c, _, s in SECTORS}

# sector affinities: education weights [<HS, HS, some college, associate, bachelor, graduate], female share
SEC_AFF = {
    "health": ([.5, .9, 1.2, 1.6, 1.1, 1.5], .77), "gov": ([.3, .7, .9, 1.0, 1.6, 1.9], .60),
    "retail": ([1.3, 1.4, 1.3, .9, .6, .25], .49), "food": ([1.9, 1.4, 1.2, .7, .4, .12], .53),
    "mfg": ([1.3, 1.5, 1.0, 1.0, .7, .45], .29), "prof": ([.05, .3, .6, .8, 2.0, 2.6], .44),
    "self": ([1.0, 1.0, 1.0, .9, 1.0, 1.1], .37), "admin": ([1.9, 1.4, 1.1, .8, .55, .25], .42),
    "constr": ([1.9, 1.6, 1.0, .8, .45, .18], .11), "fin": ([.05, .5, 1.0, 1.0, 1.9, 1.5], .55),
    "trans": ([1.3, 1.6, 1.2, .9, .45, .15], .26), "other": ([1.3, 1.3, 1.1, 1.0, .7, .5], .53),
    "whole": ([.9, 1.3, 1.1, 1.0, .9, .4], .30), "pedu": ([.15, .4, .8, .8, 1.6, 2.6], .66),
    "fed": ([.2, .9, 1.2, 1.2, 1.3, 1.3], .43), "info": ([.2, .6, 1.0, 1.0, 1.7, 1.4], .40),
    "arts": ([1.0, 1.1, 1.3, .9, 1.0, .6], .47), "mgmt": ([.05, .3, .6, .8, 2.0, 2.2], .52),
    "re": ([.5, 1.0, 1.1, 1.0, 1.2, .7], .49), "ag": ([3.0, 1.4, .7, .6, .4, .2], .26),
    "util": ([.5, 1.4, 1.2, 1.3, 1.0, .7], .22),
}
SEC_DIST = {  # district multipliers on sector choice by home district
    "ag": {"D1": .15, "D2": .5, "D3": .2, "D4": 1.5, "D5": 9, "D6": 28},
    "mfg": {"D4": 2.0, "D5": 1.6, "D6": 1.2, "D1": .8},
    "prof": {"D1": 1.3, "D3": 1.4, "D5": .5, "D6": .5},
    "fin": {"D1": 1.2, "D3": 1.4, "D5": .6, "D6": .5},
    "mgmt": {"D3": 1.5, "D1": 1.2, "D5": .4, "D6": .4},
    "trans": {"D2": 1.7, "D3": 1.1},
    "food": {"D1": 1.25, "D2": 1.15},
    "self": {"D6": 2.2, "D5": 1.3},
    "util": {"D6": 2.0, "D5": 1.5},
    "constr": {"D5": 1.3, "D6": 1.5, "D2": 1.2},
}
SEC_YOUNG = {"retail": 1.5, "food": 2.2, "arts": 1.8, "self": .35, "mgmt": .4, "gov": .6}
SEC_OLD = {"self": 1.6, "re": 1.3, "food": .6}
UNION = {"gov": .36, "util": .22, "trans": .15, "constr": .12, "mfg": .09, "pedu": .12, "info": .07,
         "health": .08, "fed": .28, "retail": .045}
CADENCE = {  # weekly, biweekly, semimonthly, monthly
    "default": (.27, .43, .19, .11), "constr": (.52, .40, .06, .02), "mfg": (.45, .45, .08, .02),
    "admin": (.50, .40, .08, .02), "ag": (.60, .34, .05, .01), "food": (.36, .52, .10, .02),
    "gov": (.04, .50, .21, .25), "prof": (.08, .45, .37, .10), "fin": (.06, .47, .37, .10),
    "mgmt": (.05, .45, .40, .10), "info": (.08, .50, .34, .08), "health": (.10, .72, .13, .05),
    "retail": (.30, .55, .12, .03), "fed": (0, 1, 0, 0),
}
PAY_WEEKDAY = [(.09, 0), (.06, 1), (.09, 2), (.14, 3), (.62, 4)]   # Mon..Fri payday weights (estimate)

# occupation tuples: (title, base full-time annual wage in 2027 dollars, weight, minimum education 0-5, schedule key, tipped)
OCC = {
    "health": [("registered nurse", 98000, .13, 3, "shift12", 0), ("nursing assistant", 41000, .10, 1, "shift3", 0),
               ("home health aide", 36500, .16, 0, "var", 0), ("medical assistant", 46000, .08, 1, "day", 0),
               ("physician", 262000, .03, 5, "day", 0), ("nurse practitioner", 134000, .02, 5, "day", 0),
               ("licensed practical nurse", 64000, .04, 2, "shift3", 0), ("medical billing clerk", 50000, .07, 1, "day", 0),
               ("physical therapist", 104000, .02, 5, "day", 0), ("dental hygienist", 93000, .02, 3, "day", 0),
               ("dental assistant", 49000, .03, 1, "day", 0), ("social worker", 63000, .05, 4, "day", 0),
               ("child care worker", 34000, .08, 1, "day", 0), ("hospital housekeeper", 36000, .05, 0, "shift3", 0),
               ("lab technician", 60000, .04, 3, "shift3", 0), ("medical receptionist", 42000, .06, 1, "day", 0),
               ("health services manager", 118000, .02, 4, "day", 0)],
    "gov": [("public school teacher", 68000, .25, 4, "school", 0), ("teaching assistant", 36000, .08, 1, "school", 0),
            ("school bus driver", 43000, .03, 1, "split", 0), ("school custodian", 38000, .03, 0, "eve", 0),
            ("school cafeteria worker", 33000, .03, 0, "school", 0), ("school counselor", 72000, .02, 5, "school", 0),
            ("school principal", 112000, .01, 5, "school", 0), ("police officer", 79000, .05, 2, "shift12", 0),
            ("firefighter", 63000, .03, 1, "shift12", 0), ("corrections officer", 58000, .02, 1, "shift3", 0),
            ("municipal clerk", 50000, .09, 1, "day", 0), ("public works maintenance worker", 50000, .07, 0, "early", 0),
            ("benefits caseworker", 56000, .04, 4, "day", 0), ("library assistant", 38000, .02, 2, "day", 0),
            ("transit bus operator", 57000, .02, 1, "split", 0), ("community college instructor", 82000, .04, 5, "day", 0),
            ("public civil engineer", 98000, .02, 4, "day", 0), ("court clerk", 52000, .02, 2, "day", 0),
            ("water treatment operator", 59000, .02, 1, "shift3", 0), ("911 dispatcher", 53000, .01, 1, "shift12", 0),
            ("parks and recreation worker", 38000, .03, 0, "var", 0), ("state office clerk", 49000, .05, 1, "day", 0),
            ("public health nurse", 82000, .01, 4, "day", 0), ("paramedic", 55000, .02, 2, "shift12", 0),
            ("city administrator", 124000, .01, 5, "day", 0)],
    "retail": [("cashier", 31000, .21, 0, "var", 0), ("retail salesperson", 35500, .24, 0, "var", 0),
               ("stock clerk", 37500, .16, 0, "var", 0), ("retail supervisor", 50000, .10, 1, "var", 0),
               ("store manager", 74000, .04, 2, "day", 0), ("pharmacist", 138000, .02, 5, "day", 0),
               ("pharmacy technician", 43500, .04, 1, "var", 0), ("car salesperson", 64000, .04, 1, "day", 0),
               ("customer service associate", 40000, .06, 1, "var", 0), ("grocery deli worker", 36000, .05, 0, "var", 0),
               ("overnight stocker", 39000, .04, 0, "night", 0)],
    "food": [("fast food worker", 30500, .30, 0, "var", 0), ("line cook", 37000, .18, 0, "var", 0),
             ("server", 33000, .19, 0, "var", 1), ("bartender", 36000, .04, 1, "late", 1),
             ("dishwasher", 30500, .06, 0, "var", 0), ("restaurant manager", 68000, .05, 2, "var", 0),
             ("host", 29500, .04, 0, "var", 1), ("hotel desk clerk", 33000, .03, 1, "shift3", 0),
             ("hotel housekeeper", 33500, .06, 0, "day", 1), ("shift supervisor", 40000, .05, 1, "var", 0)],
    "mfg": [("assembler", 43500, .27, 1, "shift3", 0), ("machine operator", 46500, .18, 1, "shift3", 0),
            ("welder", 54000, .05, 1, "shift3", 0), ("machinist", 57000, .04, 2, "shift3", 0),
            ("quality inspector", 49500, .05, 1, "shift3", 0), ("maintenance mechanic", 67000, .06, 2, "shift3", 0),
            ("production supervisor", 73000, .06, 2, "shift3", 0), ("industrial engineer", 104000, .05, 4, "day", 0),
            ("forklift operator", 43000, .10, 0, "shift3", 0), ("packaging operator", 38500, .08, 0, "shift3", 0),
            ("plant office administrator", 56000, .04, 2, "day", 0), ("plant manager", 142000, .02, 4, "day", 0)],
    "prof": [("software developer", 136000, .15, 4, "day", 0), ("accountant", 87000, .12, 4, "day", 0),
             ("attorney", 158000, .07, 5, "day", 0), ("paralegal", 64000, .05, 3, "day", 0),
             ("engineer", 105000, .10, 4, "day", 0), ("drafter", 66000, .04, 3, "day", 0),
             ("management consultant", 108000, .07, 4, "day", 0), ("marketing specialist", 78000, .07, 4, "day", 0),
             ("IT support specialist", 63000, .08, 2, "day", 0), ("graphic designer", 63000, .04, 3, "day", 0),
             ("veterinary technician", 44000, .05, 2, "day", 0), ("administrative assistant", 48000, .11, 1, "day", 0),
             ("veterinarian", 128000, .01, 5, "day", 0), ("research analyst", 88000, .04, 4, "day", 0)],
    "self": [("general contractor", 64000, .12, 1, "early", 0), ("landscaper", 45000, .08, 0, "early", 0),
             ("hair stylist", 40000, .08, 1, "var", 1), ("home child care provider", 31000, .06, 1, "day", 0),
             ("rideshare and delivery driver", 34000, .10, 0, "gig", 0), ("freelance designer", 56000, .07, 3, "day", 0),
             ("independent consultant", 112000, .08, 4, "day", 0), ("farmer", 60000, .08, 1, "farm", 0),
             ("truck owner-operator", 79000, .05, 1, "early", 0), ("house cleaner", 33000, .07, 0, "day", 0),
             ("real estate agent", 67000, .06, 2, "var", 0), ("food vendor", 43000, .04, 0, "var", 0),
             ("music and tutoring teacher", 37000, .03, 3, "eve", 0), ("shop owner", 62000, .05, 1, "day", 0),
             ("solo practitioner", 185000, .03, 5, "day", 0)],
    "admin": [("janitor", 36500, .22, 0, "eve", 0), ("security guard", 39500, .12, 1, "shift3", 0),
              ("landscaping worker", 39500, .14, 0, "early", 0), ("call center representative", 42000, .15, 1, "day", 0),
              ("temp laborer", 37000, .14, 0, "var", 0), ("office clerk", 43500, .11, 1, "day", 0),
              ("collections agent", 46000, .04, 1, "day", 0), ("pest control technician", 45000, .03, 1, "day", 0),
              ("crew supervisor", 58000, .05, 1, "early", 0)],
    "constr": [("construction laborer", 46500, .22, 0, "early", 0), ("carpenter", 60000, .16, 1, "early", 0),
               ("electrician", 68000, .12, 2, "early", 0), ("plumber", 67000, .09, 2, "early", 0),
               ("equipment operator", 61000, .07, 1, "early", 0), ("roofer", 52000, .05, 0, "early", 0),
               ("painter", 50000, .06, 0, "early", 0), ("HVAC technician", 63000, .07, 2, "early", 0),
               ("site foreman", 81000, .08, 1, "early", 0), ("project estimator", 104000, .05, 4, "day", 0),
               ("construction office manager", 52000, .03, 2, "day", 0)],
    "fin": [("bank teller", 40000, .12, 1, "day", 0), ("loan officer", 77000, .10, 4, "day", 0),
            ("personal banker", 47000, .13, 2, "day", 0), ("insurance agent", 63000, .12, 2, "day", 0),
            ("claims adjuster", 77000, .11, 4, "day", 0), ("financial advisor", 108000, .08, 4, "day", 0),
            ("underwriter", 83000, .06, 4, "day", 0), ("financial analyst", 92000, .12, 4, "day", 0),
            ("branch manager", 102000, .05, 4, "day", 0), ("insurance call center rep", 46000, .11, 1, "day", 0)],
    "trans": [("warehouse picker", 41500, .30, 0, "shift3", 0), ("truck driver", 61000, .20, 1, "early", 0),
              ("parcel delivery driver", 46000, .16, 1, "early", 0), ("forklift operator", 44500, .08, 0, "shift3", 0),
              ("dispatcher", 51000, .04, 1, "shift3", 0), ("airport ground crew", 44500, .06, 1, "shift3", 0),
              ("warehouse supervisor", 65000, .06, 2, "shift3", 0), ("diesel mechanic", 63000, .05, 2, "day", 0),
              ("logistics coordinator", 55000, .05, 3, "day", 0)],
    "other": [("auto mechanic", 53000, .20, 1, "day", 0), ("hairdresser", 36500, .13, 1, "var", 1),
              ("nail technician", 34500, .06, 0, "var", 1), ("clergy", 61000, .06, 4, "day", 0),
              ("church administrator", 41000, .06, 2, "day", 0), ("laundry worker", 31500, .06, 0, "day", 0),
              ("nonprofit program coordinator", 53000, .11, 4, "day", 0), ("funeral attendant", 47000, .02, 1, "day", 0),
              ("pet groomer", 36500, .04, 0, "day", 1), ("appliance repair technician", 51000, .06, 1, "day", 0),
              ("car wash attendant", 31000, .06, 0, "var", 1), ("nanny", 37000, .08, 0, "day", 0),
              ("parking attendant", 31500, .03, 0, "var", 0), ("membership organization staff", 58000, .03, 4, "day", 0)],
    "whole": [("wholesale sales representative", 77000, .24, 2, "day", 0), ("warehouse worker", 42500, .25, 0, "early", 0),
              ("delivery truck driver", 57000, .18, 1, "early", 0), ("order clerk", 44500, .10, 1, "day", 0),
              ("purchasing agent", 73000, .07, 4, "day", 0), ("distribution manager", 112000, .05, 4, "day", 0),
              ("forklift operator", 44500, .11, 0, "early", 0)],
    "pedu": [("private school teacher", 56000, .24, 4, "school", 0), ("college professor", 93000, .15, 5, "day", 0),
             ("college staff member", 58000, .20, 4, "day", 0), ("tutor", 40000, .08, 2, "eve", 0),
             ("trade school instructor", 67000, .07, 3, "day", 0), ("teaching assistant", 34500, .10, 1, "school", 0),
             ("campus food service worker", 36000, .10, 0, "var", 0), ("fitness and dance instructor", 44500, .06, 1, "eve", 0)],
    "fed": [("mail carrier", 62500, .38, 1, "early", 0), ("postal clerk", 60000, .08, 1, "day", 0),
            ("VA nurse", 96000, .07, 4, "day", 0), ("VA clinic clerk", 52000, .07, 1, "day", 0),
            ("airport security officer", 55000, .08, 1, "shift3", 0), ("Social Security claims specialist", 63000, .07, 4, "day", 0),
            ("active-duty service member", 54000, .08, 1, "day", 0), ("federal program specialist", 86000, .14, 4, "day", 0),
            ("federal law enforcement officer", 92000, .03, 4, "shift12", 0)],
    "info": [("telecom installer", 67000, .20, 1, "early", 0), ("web developer", 118000, .14, 4, "day", 0),
             ("reporter", 57000, .07, 4, "day", 0), ("cable customer service rep", 44500, .18, 1, "day", 0),
             ("broadcast technician", 55000, .06, 3, "shift3", 0), ("data center technician", 73000, .08, 3, "shift3", 0),
             ("telecom sales rep", 66000, .10, 2, "var", 0), ("editor", 71000, .06, 4, "day", 0),
             ("cinema worker", 29500, .11, 0, "late", 0)],
    "arts": [("fitness trainer", 46500, .20, 1, "var", 1), ("recreation attendant", 30500, .27, 0, "var", 0),
             ("coach", 42500, .08, 2, "eve", 0), ("musician", 41000, .06, 1, "late", 1),
             ("museum educator", 46500, .05, 4, "day", 0), ("golf course groundskeeper", 38500, .11, 0, "early", 0),
             ("bowling and gaming attendant", 34000, .10, 0, "late", 1), ("lifeguard", 30500, .05, 0, "var", 0),
             ("venue manager", 69000, .08, 4, "day", 0)],
    "mgmt": [("regional manager", 136000, .20, 4, "day", 0), ("corporate financial analyst", 97000, .20, 4, "day", 0),
             ("HR specialist", 71000, .15, 4, "day", 0), ("executive assistant", 62000, .18, 2, "day", 0),
             ("executive", 235000, .06, 4, "day", 0), ("corporate accountant", 87000, .21, 4, "day", 0)],
    "re": [("property manager", 63000, .25, 2, "day", 0), ("leasing agent", 44500, .20, 1, "day", 0),
           ("apartment maintenance technician", 46500, .26, 1, "day", 0), ("real estate broker", 70000, .19, 2, "var", 0),
           ("appraiser", 67000, .05, 4, "day", 0), ("real estate office assistant", 42500, .05, 1, "day", 0)],
    "ag": [("crop farmworker", 33500, .44, 0, "farm", 0), ("packing shed worker", 33000, .20, 0, "early", 0),
           ("farm equipment operator", 42500, .10, 0, "farm", 0), ("dairy and livestock worker", 37500, .13, 0, "farm", 0),
           ("farm manager", 77000, .05, 2, "farm", 0), ("logging worker", 50500, .05, 0, "early", 0),
           ("crew leader", 48500, .03, 0, "farm", 0)],
    "util": [("electrical lineworker", 89000, .24, 1, "early", 0), ("plant operator", 85000, .14, 2, "shift3", 0),
             ("utility field technician", 61000, .16, 1, "early", 0), ("utility customer service rep", 46500, .15, 1, "day", 0),
             ("quarry equipment operator", 58500, .21, 0, "early", 0), ("utility engineer", 109000, .10, 4, "day", 0)],
}
# WAGE_SCALE: read this before using any one person's pay.
# The OCC table above is close to the national median pay for each occupation (OEWS May 2025; registered nurse $98,000
# against OEWS's $97,550). Every wage is then multiplied by WAGE_SCALE, so a typical full-time worker in Halvern earns
# 1.23 times the table. Wage growth from May 2025 to 2027 would justify only about 1.08, so each worker is paid about 14%
# more than a real worker in the same job (a Halvern nurse about $120,000 against roughly $105,000).
# Why: Halvern's households are smaller than real ones (2.36 people against about 2.58 nationally, 1.14 earners each), so
# fewer paychecks reach each home. v1 set the boost to make up for that (and to put 41.5% of households under the ALICE
# budget). Even with it, median household income is about $78,000, against about $86,700 implied by SCF 2025 in 2027
# dollars; at 1.08 it would fall to roughly $70,000 and Halvern would look poorer than the country.
# So household money (balances, bills, overdrafts, who can cover $400) is closer to right with the boost, and pay for a
# single job is not. Compare households, not occupations.
# Decided 2026-11-20: keep 1.23 for v2 (same people as v1). v3 rebuilds households at their real size from ACS PUMS;
# it should then set this to wage growth alone (about 1.08) and re-check household income against SCF.
WAGE_SCALE = 1.23

# ---- federal program parameters for 2027 (see assumptions.csv for sources)
SS_AVG_RETIRED = 2170.0        # SSA: average retired-worker benefit, Jan 2027 after 3.6% COLA
SS_AVG_DISABLED = 1694.0       # $1,635 x 1.036
SS_AVG_WIDOW = 2005.0
SSI_FBR = 1029.0               # individual federal benefit rate 2027
SSI_FBR_COUPLE = 1544.0
PART_B_PREMIUM = 209.50        # Trustees projection for 2027; CMS final not yet published
PART_B_DEDUCTIBLE = 292.0
PART_D_OOP_CAP = 2400.0
SNAP_MAX = {1: 306, 2: 562, 3: 808, 4: 1023, 5: 1217, 6: 1463, 7: 1616, 8: 1841}   # FY2027, 48 states
POVERTY_BASE, POVERTY_STEP = 16400.0, 5750.0   # estimated 2027 HHS guideline
# Day of the month SNAP loads: eight states' rules weighted by their SNAP households (FY2024 QC), from
# sources/derived/snap_load_days.csv (sources/tools/snap_load_days.py). 87 percent load by the 10th; Georgia and Missouri run later.
SNAP_LOAD_DAYS = [(1, 0.0826), (2, 0.0783), (3, 0.0783), (4, 0.0846), (5, 0.0964), (6, 0.0846), (7, 0.0987), (8, 0.0846), (9, 0.0964), (10, 0.0846), (11, 0.0204), (12, 0.0086), (13, 0.0204), (14, 0.0023), (15, 0.0141), (16, 0.0023), (17, 0.0141), (18, 0.0023), (19, 0.0141), (20, 0.0023), (21, 0.0141), (22, 0.0046), (23, 0.0118)]
# Hourly preference weights for shopping trips and gas fill-ups (hour of day: weight), weekday and weekend/holiday.
# Fitted (7 rounds, 12,000-household runs of 2027-03-03 and 2027-10-09) so the realized start hours of grocery, big-box,
# clothing and dollar-store trips (60/40 grocery to other shopping) and of gas fill-ups match ATUS 2023-25
# (sources/derived/atus_start_hours.csv). Distance from ATUS (total variation): weekday shopping 0.27 -> 0.08, weekend
# shopping 0.23 -> 0.04, gas about 0.2 -> 0.03. Evening weights are low because workers are only free then anyway.
SHOP_HOURS = {
    "weekday": {7: .05, 8: .263, 9: .791, 10: 1.0, 11: .964, 12: .973, 13: .923, 14: .904, 15: .663, 16: .381, 17: .129,
                18: .029, 19: .019, 20: .019, 21: .019},
    "weekend": {7: .121, 8: .307, 9: .445, 10: .876, 11: .874, 12: .955, 13: 1.0, 14: .693, 15: .432, 16: .398, 17: .144,
                18: .037, 19: .019, 20: .019, 21: .019}}
GAS_HOURS = {
    "weekday": {5: .27, 6: .286, 7: .21, 8: .315, 9: .316, 10: .35, 11: .777, 12: 1.0, 13: .453, 14: .585, 15: .566, 16: .435,
                17: .66, 18: .463, 19: .242, 20: .16, 21: .043, 22: .069},
    "weekend": {6: .421, 7: .235, 8: .314, 9: .331, 10: .399, 11: .598, 12: 1.0, 13: .568, 14: .661, 15: .517, 16: .612,
                17: .84, 18: .826, 19: .37, 20: .133, 21: .159, 22: .11}}
# Day-of-week factor on everyday purchase rates (Mon=0; holidays use their own weekday). Fitted (4 rounds, 12,000-household
# runs of Oct 18-24, 2027) so purchases per resident by weekday match DCPC 2025 (transactions with payment=1 and bill=0,
# weighted by daily_weight): Sun 1.06, Mon .89, Tue .92, Wed 1.03, Thu 1.01, Fri 1.07, Sat 1.02 of the weekly mean.
# The factors average 1, so the weekly total (calibrated by PURCHASE_FREQ) is unchanged.
DOW_PURCHASE = {0: .827, 1: .872, 2: 1.012, 3: 1.002, 4: 1.079, 5: 1.057, 6: 1.15}
FED_MIN_WAGE = 7.25
STATE_INCOME_TAX = 0.035       # stand-in for a national-average state

GENERATIONS = [(2013, "gen_alpha"), (1997, "gen_z"), (1981, "millennial"), (1965, "gen_x"),
               (1946, "baby_boomer"), (1928, "silent"), (0, "greatest")]


# Federal holidays (5 U.S.C. 6103). A Saturday holiday is observed the Friday before, a Sunday one the Monday after.
# Banks and the ACH network close on the observed date, so pay and benefits due that day move to the business day before
# and ACH autopays post the business day after. "Major" holidays are the six nearly every employer with paid holidays gives
# (NCS March 2026: 81% of private-industry workers have paid holidays, 8 a year on average; state and local government 11).
MAJOR_HOLIDAYS = {"New Year's Day", "Memorial Day", "Independence Day", "Labor Day", "Thanksgiving Day", "Christmas Day"}
SCHOOL_OPEN_HOLIDAYS = {"Columbus Day", "Veterans Day"}   # most school districts hold classes (estimate)


def side_rng(seed, *key):
    """A random stream of its own for a v2 attribute, keyed by the run seed and (say) a household id. v2 draws new
    population attributes from these so the main stream, and with it v1's people, stay exactly as they were."""
    import random
    return random.Random("%s|%s" % (seed, "|".join(str(k) for k in key)))


def draw_table(r, table):
    """Pick a value from [(value, share), ...] with a uniform draw r in [0, 1)."""
    acc = 0.0
    for v, w in table:
        acc += w
        if r < acc:
            return v
    return table[-1][0]


def _nth_weekday(year, month, weekday, n):
    d = dt.date(year, month, 1)
    d += dt.timedelta(days=(weekday - d.weekday()) % 7)
    if n > 0:
        return d + dt.timedelta(weeks=n - 1)
    last = dt.date(year + (month == 12), month % 12 + 1, 1) - dt.timedelta(days=1)   # n == -1: last such weekday
    return last - dt.timedelta(days=(last.weekday() - weekday) % 7)


def federal_holidays(year):
    """{observed date: name} for the holidays of `year` (New Year's Day of year+1 can be observed on Dec 31)."""
    fixed = [("New Year's Day", dt.date(year, 1, 1)), ("Juneteenth National Independence Day", dt.date(year, 6, 19)),
             ("Independence Day", dt.date(year, 7, 4)), ("Veterans Day", dt.date(year, 11, 11)),
             ("Christmas Day", dt.date(year, 12, 25)), ("New Year's Day", dt.date(year + 1, 1, 1))]
    out = {}
    for name, d in fixed:
        if d.weekday() == 5:
            d -= dt.timedelta(days=1)
        elif d.weekday() == 6:
            d += dt.timedelta(days=1)
        if d.year == year:
            out[d] = name
    for name, m, wd, n in (("Birthday of Martin Luther King, Jr.", 1, 0, 3), ("Washington's Birthday", 2, 0, 3),
                           ("Memorial Day", 5, 0, -1), ("Labor Day", 9, 0, 1), ("Columbus Day", 10, 0, 2),
                           ("Thanksgiving Day", 11, 3, 4)):
        out[_nth_weekday(year, m, wd, n)] = name
    return out


def _holidays_near(d):
    h = {}
    for y in (d.year - 1, d.year, d.year + 1):
        h.update(federal_holidays(y))
    return h


def bank_day(d, hol=None):
    hol = _holidays_near(d) if hol is None else hol
    return d.weekday() < 5 and d not in hol


def _mini(d):
    """The few calendar fields that decide paydays and bill dates, for a day other than SIM_DATE."""
    return dict(date=d, dow=d.weekday(), dom=d.day, week_parity=(d.isocalendar()[1] % 2))


def calendar(sim_date):
    """Everything the simulator needs to know about SIM_DATE."""
    dow = sim_date.weekday()                      # Mon=0
    dom = sim_date.day
    first = sim_date.replace(day=1)
    hol = _holidays_near(sim_date)
    holiday = hol.get(sim_date) if dow < 5 else None
    is_bank = bank_day(sim_date, hol)
    nth_wed = None
    if dow == 2:
        nth_wed = (dom - 1) // 7 + 1

    def biz_on_or_before(d):
        while not bank_day(d, hol):
            d -= dt.timedelta(days=1)
        return d
    nxt = (first + dt.timedelta(days=32)).replace(day=1)
    # Social Security: the 3rd, or the 2nd, 3rd and 4th Wednesdays; SSI and VA: the 1st. Each moves to the business day
    # before when it falls on a weekend or holiday, which can pull next month's payment into this month.
    cohorts = set()
    for m1 in (first, nxt):
        if biz_on_or_before(m1.replace(day=3)) == sim_date:
            cohorts.add("3rd")
        for n in (2, 3, 4):
            if biz_on_or_before(_nth_weekday(m1.year, m1.month, 2, n)) == sim_date:
                cohorts.add("wed%d" % n)
    ssi_day = biz_on_or_before(first)
    ssi_today = sim_date in (ssi_day, biz_on_or_before(nxt))
    # Paydays and ACH autopays that fall on days the banks are closed
    pay_ahead, ach_catchup = [], []
    if is_bank:
        d = sim_date + dt.timedelta(days=1)
        while not bank_day(d, hol):
            pay_ahead.append(_mini(d))
            d += dt.timedelta(days=1)
        d = sim_date - dt.timedelta(days=1)
        while not bank_day(d, hol):
            ach_catchup.append(_mini(d))
            d -= dt.timedelta(days=1)
    month = sim_date.month
    school = dow < 5 and month not in (6, 7) and not (month == 8 and dom < 10)
    if holiday and holiday not in SCHOOL_OPEN_HOLIDAYS:
        school = False
    c = dict(date=sim_date, dow=dow, dom=dom, weekday=dow < 5, nth_wed=nth_wed, ss_cohorts=cohorts,
             ssi_today=ssi_today, days_since_first=(sim_date - ssi_day).days,
             holiday=holiday, holiday_major=holiday in MAJOR_HOLIDAYS, bank_day=is_bank,
             pay_ahead=pay_ahead, ach_catchup=ach_catchup,
             tax_season=(dt.date(sim_date.year, 1, 25) <= sim_date <= dt.date(sim_date.year, 4, 20)),
             eitc_wave=(dt.date(sim_date.year, 2, 26) <= sim_date <= dt.date(sim_date.year, 3, 5)),
             school_day=school,
             heating=(month in (11, 12, 1, 2, 3)), cooling=(month in (6, 7, 8, 9)),
             growing=(month in (4, 5, 6, 7, 8, 9, 10)), month=month,
             snap_day=(dom if dom <= 10 else None), week_parity=(sim_date.isocalendar()[1] % 2),
             early_month=(dom <= 5), iso=sim_date.isoformat(),
             dayname=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][dow])
    return c


def weather_mult(weather):
    """Shock multipliers. 'ordinary' is all ones; see README for scenarios."""
    base = dict(trips=1.0, delivery=1.0, outage=1.0, missed_bus=1.0, car_fail=1.0, school_open=True,
                ed=1.0, noshow=1.0, power_outage=0.0)
    if weather == "storm":
        base.update(trips=.55, delivery=1.5, outage=5.0, missed_bus=4.0, car_fail=2.2, school_open=False,
                    ed=1.25, noshow=3.0, power_outage=.08)
    elif weather == "heat":
        base.update(trips=.85, delivery=1.25, outage=2.0, missed_bus=1.5, car_fail=1.6, ed=1.15, power_outage=.01)
    return base
