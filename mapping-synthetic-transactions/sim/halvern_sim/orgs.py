"""Organizations of Halvern. Every name here is invented."""
from .config import DISTRICTS, HOODS, SECNAME

DAYS = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

# Closed on a federal holiday (the observed date). Government offices, banks and credit unions close on all of them;
# many private offices and clinics close on the six major ones; most big retailers also close on Thanksgiving.
HOLIDAY_CLOSED = {"benefits_office", "city", "county", "community_college", "courthouse", "dmv", "federal_office", "health_dept",
                  "housing_authority", "library", "post_office", "probation", "school_district", "senior_center", "ssa", "usda",
                  "va_clinic", "workforce", "bank", "bank_hq", "credit_union", "head_start", "community_action", "legal_aid", "vita"}
MAJOR_CLOSED = {"prof_firm", "admin_firm", "law", "accounting", "insurer_office", "mgmt_hq", "software", "fqhc", "free_clinic",
                "after_school", "tax_prep", "check_casher", "payday", "title_loan", "pawn", "car_dealer", "bhph_dealer", "construction",
                "manufacturer", "wholesaler", "farm_supply", "ship_notary", "phone_store", "trade_school", "college_private",
                "private_school", "food_pantry", "food_bank", "thrift"}
THANKSGIVING_CLOSED = {"supercenter", "department", "home_center", "warehouse_club", "clothing", "electronics", "sporting",
                       "auto_parts", "tire", "oil_change", "car_wash", "luxury_boutique", "dollar"}


def closed_for_holiday(kind, cal):
    h = cal.get("holiday")
    if not h:
        return False
    return (kind in HOLIDAY_CLOSED or (cal["holiday_major"] and kind in MAJOR_CLOSED)
            or (h == "Thanksgiving Day" and kind in THANKSGIVING_CLOSED | MAJOR_CLOSED))


def parse_hours(hours, dow):
    """Return (open, close) minutes for the weekday, or (None, None) if closed that day."""
    if hours in ("24h", "always"):
        return 0, 1440
    parts = hours.split(" ")
    span = parts[-1]
    if len(parts) == 2:
        spec, ok = parts[0], False
        for piece in spec.split(","):
            if "-" in piece:
                a, b = piece.split("-")
                ia, ib = DAYS.index(a), DAYS.index(b)
                if ia <= dow <= ib:
                    ok = True
            elif DAYS.index(piece) == dow:
                ok = True
        if not ok:
            return None, None
    a, b = span.split("-")
    o = int(a[:2]) * 60 + int(a[3:])
    c = int(b[:2]) * 60 + int(b[3:])
    if c <= o:
        c = 1440
    return o, c


class Org:
    __slots__ = ("oid", "name", "kind", "otype", "sector", "district", "size", "accepts", "hours", "notes",
                 "open", "close", "emp", "cc", "dc", "csh", "ntx", "rev", "acc")

    def __init__(self, oid, name, kind, otype, sector, district, size, accepts, hours, notes):
        self.oid, self.name, self.kind, self.otype, self.sector = oid, name, kind, otype, sector
        self.district, self.size, self.accepts, self.hours, self.notes = district, size, accepts, hours, notes
        self.open = self.close = None
        self.emp = 0
        self.cc = self.dc = self.csh = self.rev = 0.0
        self.ntx = 0
        self.acc = set(accepts.split(";")) if accepts else set()


A_ALL = "cash;debit;credit;prepaid"
A_GROC = "cash;debit;credit;prepaid;ebt_snap;wic;check"
A_SNAP = "cash;debit;credit;prepaid;ebt_snap"
A_CARD = "debit;credit;prepaid"
A_ONLINE = "debit;credit;prepaid;bnpl"
A_BILL = "ach;debit;credit;check;money_order;cash"
A_BILLX = "ach;debit;credit;check"
A_GOV = "cash;check;money_order;debit;credit"
A_MED = "cash;debit;credit;check;insurance"
A_CASH = "cash"
A_B2B = "ach;check;credit"

SUR = ["Abernathy", "Okafor", "Nguyen", "Delgado", "Whitcomb", "Haddad", "Petrov", "Kowalczyk", "Brackett", "Yoon",
       "Castellano", "Mbeki", "Alvarez", "Thornbury", "Singh", "Fitzgerald", "Moreau", "Tanaka", "Ibarra", "Lindqvist",
       "Osei", "Rahimi", "Calloway", "Pruitt", "Villanueva", "Hargrove", "Zhou", "Dufresne", "Kessler", "Bautista",
       "Ferreira", "Novak", "Ellery", "Santangelo", "Girard", "Mwangi", "Trask", "Holloway", "Quintero", "Ashworth",
       "Baptiste", "Sorensen", "Cho", "Maldonado", "Pickering", "Adeyemi", "Lombardi", "Stroud", "Eze", "Varga",
       "Redcloud", "Halloran", "Nakamura", "Oyelaran", "Brennan", "Castillo", "Wojcik", "Amari", "Greer", "Tolbert"]
ADJ = ["Blue", "Copper", "Rusty", "Golden", "Little", "Lucky", "Painted", "Wandering", "Salty", "Sleepy", "Red", "Green",
       "Silver", "Crooked", "Honest", "Bright"]
NOUN = ["Heron", "Skillet", "Lantern", "Fig", "Anchor", "Biscuit", "Pepper", "Rooster", "Plow", "Magnolia", "Kettle",
        "Spoon", "Sparrow", "Barrel", "Acorn", "Thimble"]
CUIS = ["Kitchen", "Diner", "Grill", "Cantina", "Trattoria", "Noodle House", "Smokehouse", "Bistro", "Cafe", "Taqueria",
        "Pho & Grill", "Curry House", "Soul Food", "Family Restaurant", "Pizzeria", "Bar-B-Q", "Deli", "Tavern",
        "Pupuseria", "Dumpling House", "Fish Fry", "Gyro Spot"]


class Builder:
    def __init__(self, rng, cal, scale):
        self.rng, self.cal, self.scale = rng, cal, scale
        self.orgs, self.names, self.hood_i = [], set(), {d: 0 for d in DISTRICTS}

    def hood(self, d):
        if d not in HOODS:
            return "Halvern"
        h = HOODS[d][self.hood_i[d] % len(HOODS[d])]
        self.hood_i[d] += 1
        return h

    def uniq(self, name, d):
        base, k = name, 2
        if name in self.names and d in HOODS:
            name = "%s (%s)" % (base, self.rng.choice(HOODS[d]))
        while name in self.names:
            name = "%s %d" % (base, k)
            k += 1
        self.names.add(name)
        return name

    def add(self, kind, name, otype, sec, d, size, accepts, hours, notes=""):
        o = Org("O%04d" % (len(self.orgs) + 1), self.uniq(name, d), kind, otype, SECNAME.get(sec, sec), d,
                max(1, int(size)), accepts, hours, notes)
        o.open, o.close = parse_hours(hours, self.cal["dow"])
        if closed_for_holiday(kind, self.cal):
            o.open, o.close = None, None
        self.orgs.append(o)
        return o

    def n(self, x):
        """Scale an outlet count, keeping at least one where the full city has one."""
        if x <= 0:
            return 0
        return max(1, int(round(x * self.scale)))

    def chain(self, kind, base, otype, sec, counts, size, accepts, hours, notes=""):
        for d, c in zip(DISTRICTS, counts):
            for _ in range(self.n(c)):
                self.add(kind, "%s – %s" % (base, self.hood(d)), otype, sec, d, size, accepts, hours, notes)

    def indep(self, kind, gen, otype, sec, counts, size, accepts, hours, notes=""):
        for d, c in zip(DISTRICTS, counts):
            for _ in range(self.n(c)):
                sz = self.rng.randint(*size) if isinstance(size, tuple) else size
                self.add(kind, gen(d), otype, sec, d, sz, accepts, hours, notes)

    # name generators -----------------------------------------------------------------
    def g_sur(self, *suffixes):
        def f(d):
            return "%s %s" % (self.rng.choice(SUR), self.rng.choice(suffixes))
        return f

    def g_hood(self, *suffixes):
        def f(d):
            return "%s %s" % (self.rng.choice(HOODS[d]), self.rng.choice(suffixes))
        return f

    def g_rest(self, d):
        r = self.rng
        if r.random() < .55:
            return "%s's %s" % (r.choice(SUR), r.choice(CUIS))
        return "The %s %s" % (r.choice(ADJ), r.choice(NOUN))

    def g_bar(self, d):
        r = self.rng
        return r.choice(["The %s %s Taproom", "%s %s Pub", "The %s %s Lounge", "%s %s Bar & Billiards"]) % (r.choice(ADJ), r.choice(NOUN))

    def g_church(self, d):
        r = self.rng
        x = r.choice(["Grace", "Trinity", "Calvary", "Faith", "Hope", "Redeemer", "Cornerstone", "Living Water", "Bethel",
                      "Emmanuel", "Harvest", "Good Shepherd", "Peace", "Zion", "Covenant", "Resurrection"])
        y = r.choice(["Olive", "Pisgah", "Carmel", "Moriah", "Hebron", "Nebo"])
        h = r.choice(HOODS[d])
        return r.choice([
            "First Baptist Church of %s" % h, "%s Catholic Parish" % r.choice(["St. Brigid", "St. Anselm", "St. Kateri", "Our Lady of the Rivers", "St. Martin de Porres", "Holy Family"]),
            "%s United Methodist Church" % x, "Mt. %s Missionary Baptist Church" % y, "%s Lutheran Church" % x,
            "Iglesia %s" % r.choice(["Camino de Vida", "Roca Eterna", "Nueva Esperanza", "Casa de Oración", "Monte Sion"]),
            "%s Assembly" % x, "%s Church of Christ" % h, "%s Presbyterian Church" % x, "New %s AME Church" % y,
            "%s Community Church" % x, "%s Bible Fellowship" % x, "%s Pentecostal Tabernacle" % x, "%s Episcopal Church" % x])


def build_orgs(rng, cal, scale=1.0):
    B = Builder(rng, cal, scale)
    add, chain, indep = B.add, B.chain, B.indep

    # ---------------- retail: food
    chain("grocery_full", "Marlow's Market", "business", "retail", [2, 2, 3, 1, 0, 0], 110, A_GROC, "06:00-23:00", "full-service grocery chain with pharmacy counter")
    chain("grocery_full", "Tillbrook Foods", "business", "retail", [1, 1, 2, 1, 1, 0], 85, A_GROC, "06:00-22:00", "regional grocery chain")
    chain("grocery_discount", "Pennywell Discount Grocery", "business", "retail", [1, 2, 0, 1, 0, 0], 32, A_SNAP, "08:00-21:00", "limited-assortment discount grocer; bring your own bags")
    for d, nm in [("D1", "Mercado La Palma"), ("D1", "Sunrise Halal Market"), ("D1", "Corner Pantry Bodega"), ("D1", "Halvern Food Co-op"),
                  ("D1", "Northside Fresh Mart"), ("D1", "Old Depot Grocery"), ("D2", "Golden Lotus Asian Grocery"), ("D2", "Carnicería El Rodeo"),
                  ("D2", "Eastgate International Foods"), ("D2", "Millrace Market"), ("D2", "Tienda Mi Pueblo"), ("D2", "Addis Market & Spice"),
                  ("D3", "Stonebridge Natural Grocer"), ("D3", "Fox Hollow Butcher & Provisions"), ("D4", "Mill Street Market"),
                  ("D4", "La Cosecha Tienda"), ("D4", "Ashford Corner Grocery"), ("D5", "Dunmore Hometown Grocery"), ("D6", "Crossroads General Store")]:
        add("grocery_indep", nm, "business", "retail", d, rng.randint(6, 24), A_GROC if rng.random() < .8 else "cash;debit;ebt_snap", "07:00-21:00", "independent grocer")
    chain("dollar", "Penny Pine Dollar", "business", "retail", [3, 3, 2, 2, 2, 1], 9, A_SNAP, "08:00-21:00", "dollar store chain; limited fresh food")
    chain("dollar", "Buckwise Variety", "business", "retail", [2, 2, 0, 1, 1, 0], 8, A_SNAP, "09:00-20:00", "dollar and variety store")
    chain("supercenter", "Oxbow Supercenter", "business", "retail", [0, 1, 2, 1, 0, 0], 300, A_GROC, "06:00-23:00", "big-box general merchandise and grocery")
    chain("warehouse_club", "Stackhouse Wholesale Club", "business", "retail", [0, 0, 1, 0, 0, 0], 220, A_SNAP, "09:00-20:30", "membership warehouse club")
    chain("home_center", "Kettleman Home Center", "business", "retail", [0, 1, 1, 1, 0, 0], 150, A_ALL + ";check", "06:00-21:00", "home improvement big-box with contractor desk")
    chain("electronics", "Circuit Barn", "business", "retail", [0, 0, 1, 0, 0, 0], 60, A_ALL + ";bnpl", "10:00-21:00", "electronics and appliances")
    chain("farm_supply", "Tallgrass Farm & Ranch Supply", "business", "retail", [0, 0, 0, 1, 1, 0], 28, A_ALL + ";check", "07:30-18:30", "feed, fencing, workwear")
    chain("department", "Marchetti & Lane", "business", "retail", [0, 0, 1, 0, 0, 0], 120, A_ALL + ";bnpl", "10:00-21:00", "department store at Stonebridge Commons")
    chain("clothing", "Threadline Outlet", "business", "retail", [1, 1, 1, 1, 0, 0], 22, A_ALL + ";bnpl", "10:00-20:00", "discount apparel")
    chain("thrift", "Second Go Thrift", "nonprofit", "retail", [1, 1, 0, 1, 1, 0], 12, A_ALL, "09:00-18:00", "thrift store funding job training")
    chain("sporting", "Trailhead Sporting Goods", "business", "retail", [0, 0, 1, 0, 0, 0], 40, A_ALL, "09:00-21:00")
    chain("pharmacy", "Wellspring Pharmacy", "business", "retail", [3, 2, 3, 2, 1, 0], 22, A_GROC.replace(";wic", "") + ";insurance", "08:00-21:00", "chain pharmacy and convenience")
    add("pharmacy", "Main Street Apothecary", "business", "retail", "D4", 7, A_ALL + ";insurance", "Mo-Fr 09:00-18:00", "independent pharmacy")
    add("pharmacy", "Dunmore Drug", "business", "retail", "D5", 6, A_ALL + ";insurance;check", "Mo-Fr 09:00-17:30", "independent pharmacy; counter closes 13:00-13:30 for lunch")
    chain("auto_parts", "PartsPost Auto Parts", "business", "retail", [1, 1, 1, 1, 1, 0], 11, A_ALL, "07:30-21:00")
    chain("liquor", "Barrelhouse Wine & Spirits", "business", "retail", [2, 2, 2, 1, 1, 0], 6, A_ALL, "10:00-22:00")
    chain("phone_store", "Vireo Wireless Store", "business", "retail", [1, 1, 1, 1, 0, 0], 8, A_ALL, "10:00-20:00", "postpaid carrier store")
    chain("phone_store", "Pocket Prepaid Wireless", "business", "retail", [1, 2, 0, 1, 1, 0], 4, A_ALL, "10:00-19:00", "prepaid phone refills and bill pay")
    indep("jewelry", B.g_sur("Jewelers", "Fine Jewelry", "Diamonds & Watches"), "business", "retail", [1, 0, 2, 1, 0, 0], (4, 9), A_ALL + ";bnpl", "10:00-18:00")
    add("luxury_boutique", "Atelier Corvane", "business", "retail", "D3", 9, A_CARD, "10:00-19:00", "designer handbags and accessories at Stonebridge Commons")
    indep("furniture", B.g_sur("Furniture", "Home Furnishings", "Mattress & Furniture"), "business", "retail", [1, 1, 2, 1, 0, 0], (6, 18), A_ALL + ";bnpl", "10:00-19:00")
    indep("rent_to_own", lambda d: "EasyKeep Rent-to-Own", "business", "retail", [1, 1, 0, 1, 1, 0], 6, A_ALL, "10:00-19:00", "weekly-payment furniture and electronics")
    indep("pet_store", B.g_hood("Pet Supply", "Feed & Pet"), "business", "retail", [1, 1, 2, 1, 1, 0], (5, 14), A_ALL, "09:00-20:00")
    indep("bookstore", lambda d: rng.choice(["Dog-Eared Books", "The Reading Lamp", "Inkwell Books & Games", "Paper Lantern Books"]), "business", "retail", [2, 0, 1, 1, 0, 0], (3, 8), A_ALL, "10:00-19:00")
    indep("bike_shop", lambda d: rng.choice(["Spoke & Sprocket Cyclery", "Riverfront Bike Works", "Chainline Bicycles"]), "business", "retail", [2, 0, 1, 0, 0, 0], (3, 6), A_ALL, "10:00-18:00")
    indep("tobacco", B.g_hood("Smoke & Vape", "Tobacco Outlet"), "business", "retail", [3, 3, 1, 2, 1, 0], (2, 4), A_ALL, "09:00-22:00")
    indep("florist", B.g_sur("Flowers", "Floral Design"), "business", "retail", [2, 1, 2, 1, 1, 0], (2, 6), A_ALL, "09:00-17:30")
    indep("hardware", B.g_sur("Hardware", "Hardware & Supply"), "business", "retail", [2, 1, 0, 1, 1, 1], (4, 10), A_ALL + ";check", "07:30-18:00")
    # gas and convenience
    chain("gas", "Lantern Fuel & Go", "business", "retail", [4, 5, 6, 3, 2, 1], 9, A_SNAP, "24h", "gas station and convenience chain; ATM inside")
    chain("gas", "Bison Travel Stop", "business", "retail", [0, 0, 1, 0, 0, 1], 26, A_SNAP, "24h", "highway truck stop with diesel and showers")
    indep("gas", B.g_hood("Gas & Grocery", "Quick Stop", "Fuel Mart"), "business", "retail", [3, 3, 0, 2, 1, 2], (3, 6), A_SNAP, "05:00-23:00", "independent station; some pumps require pay-inside")
    add("ev_charging", "VoltWay Fast Charging", "business", "retail", "D3", 1, A_CARD, "24h", "public DC fast chargers at Stonebridge Commons and downtown garage")
    # car dealers
    add("car_dealer", "Castellan Auto Group", "business", "retail", "D3", 140, A_BILLX, "09:00-20:00", "new-car dealerships and service")
    add("car_dealer", "Bridgeview Motors", "business", "retail", "D2", 24, A_BILLX + ";cash", "09:00-19:00", "used cars")
    for d in ("D2", "D5"):
        add("bhph_dealer", "Drive Today Auto Sales", "business", "retail", d, 7, "cash;debit;money_order", "09:00-18:00", "buy-here-pay-here lot; weekly payments in person")

    # ---------------- food service and lodging
    for nm, cnt in [("Burger Depot", [2, 2, 3, 1, 1, 0]), ("Cluck & Biscuit", [1, 2, 2, 1, 1, 0]), ("Taco Rancho", [2, 2, 2, 1, 0, 0]),
                    ("Slice Wagon Pizza", [2, 1, 2, 1, 1, 0]), ("Hoagie Junction", [2, 1, 2, 1, 1, 0]), ("Sunny Dip Donuts", [2, 2, 2, 1, 0, 0]),
                    ("Wokabout Express", [1, 1, 1, 0, 0, 0])]:
        chain("fastfood", nm, "business", "food", cnt, 22, A_ALL, "06:00-23:00", "quick-service chain")
    chain("coffee", "Copper Kettle Coffee", "business", "food", [4, 1, 3, 1, 0, 0], 14, A_ALL, "05:30-19:00", "coffee chain with drive-through")
    for d, nm in [("D1", "Wren & Rye Coffee"), ("D1", "Second Street Roasters"), ("D4", "Mill Race Coffee"), ("D5", "Main Street Perk"), ("D2", "Café Jacaranda")]:
        add("coffee", nm, "business", "food", d, rng.randint(4, 9), A_ALL, "06:30-17:00", "independent cafe")
    indep("restaurant", B.g_rest, "business", "food", [38, 22, 22, 16, 6, 1], (9, 30), A_ALL, "11:00-22:00", "independent sit-down restaurant")
    for d, nm in [("D1", "The Gilded Finch"), ("D1", "Ember & Oak"), ("D3", "Larkspur Table"), ("D4", "Vintner's Hall")]:
        add("fine_dining", nm, "business", "food", d, rng.randint(22, 38), A_CARD + ";cash", "We-Su 17:00-22:00", "fine dining; reservations")
    indep("bar", B.g_bar, "business", "food", [13, 6, 5, 6, 2, 1], (4, 12), A_ALL, "15:00-01:00")
    indep("food_truck", lambda d: rng.choice(["Tacos El Gallo Truck", "Seoul Wheels", "Smoke Signal BBQ Truck", "Arepa Parade", "Biscuit Wagon", "Curry Up Truck", "Halal Cart on Fifth", "Elote Loco Cart"]), "business", "food", [6, 4, 1, 1, 0, 0], (2, 3), "cash;debit;credit", "10:30-15:00", "food truck or cart")
    chain("hotel", "Wayfarer Inn & Suites", "business", "food", [1, 2, 2, 1, 0, 0], 28, A_CARD, "24h", "hotel")
    add("hotel", "Hotel Aurelia", "business", "food", "D1", 70, A_CARD, "24h", "downtown boutique hotel")
    add("hotel", "Dunmore Motor Lodge", "business", "food", "D5", 6, A_ALL, "24h", "motel; weekly rates")
    add("caterer", "Marigold Catering Co.", "business", "food", "D1", 26, A_B2B, "07:00-19:00", "office and event catering")
    add("caterer", "Box & Platter Lunch Catering", "business", "food", "D3", 14, A_B2B, "07:00-15:00", "office lunch catering")

    # ---------------- health care and social assistance
    add("hospital", "Halvern Regional Medical Center", "nonprofit", "health", "D4", 2500, A_MED, "24h", "regional hospital, trauma level III, 310 beds")
    add("hospital", "Halvern Regional – Downtown Campus", "nonprofit", "health", "D1", 900, A_MED, "24h", "emergency department, outpatient surgery, clinics")
    for d in ("D1", "D2", "D5"):
        add("fqhc", "Riverbend Community Health Center – %s" % B.hood(d), "nonprofit", "health", d, 45, A_MED, "Mo-Fr 08:00-18:00", "federally qualified health center; sliding fee scale; medical, dental, behavioral")
    chain("urgent_care", "PromptCare Urgent Care", "business", "health", [0, 1, 1, 1, 0, 0], 18, A_MED, "08:00-20:00")
    indep("physician", B.g_hood("Family Medicine", "Internal Medicine Associates", "Pediatrics", "Women's Health", "Cardiology Group", "Orthopedics", "Primary Care"), "business", "health", [9, 5, 9, 7, 1, 0], (8, 40), A_MED, "Mo-Fr 08:00-17:00", "physician practice")
    indep("dental", B.g_sur("Family Dentistry", "Dental Care", "Orthodontics", "Dental Group"), "business", "health", [12, 8, 12, 7, 2, 0], (5, 14), A_MED + ";bnpl", "Mo-Fr 08:00-17:00", "dental office")
    indep("vision", B.g_sur("Eye Care", "Vision Center", "Optical"), "business", "health", [3, 2, 4, 2, 1, 0], (4, 10), A_MED, "Mo-Sa 09:00-18:00")
    indep("behavioral", lambda d: rng.choice(["Compass Counseling", "Stillwater Behavioral Health", "Open Sky Therapy Group", "Hearth & Mind Counseling", "Bridgeway Recovery Services", "Lantern Family Therapy"]), "business", "health", [7, 3, 5, 3, 1, 0], (3, 16), A_MED, "Mo-Fr 08:00-20:00", "outpatient therapy; some telehealth")
    indep("pt_clinic", B.g_hood("Physical Therapy", "Rehab & Sports Therapy"), "business", "health", [3, 2, 3, 2, 0, 0], (6, 14), A_MED, "Mo-Fr 07:00-19:00")
    add("dialysis", "Clearwater Dialysis Center – Downtown", "business", "health", "D1", 38, "insurance", "Mo-Sa 05:30-18:30", "in-center hemodialysis")
    add("dialysis", "Clearwater Dialysis Center – Ashford Mills", "business", "health", "D4", 30, "insurance", "Mo-Sa 05:30-18:30", "in-center hemodialysis")
    indep("home_health", lambda d: rng.choice(["Hearthside Home Care", "Evergreen Home Health", "Helping Hands Personal Care", "Tri-County Visiting Nurses", "Comfort Keel Home Care", "Amistad Home Care"]), "business", "health", [2, 2, 1, 1, 1, 0], (60, 180), A_MED, "24h", "home health and personal care agency")
    add("nursing_home", "Maple Glen Nursing & Rehabilitation", "business", "health", "D2", 190, A_MED, "24h", "skilled nursing facility, 180 beds")
    add("nursing_home", "Cedar Hollow Care Center", "nonprofit", "health", "D4", 135, A_MED, "24h", "skilled nursing facility, 130 beds")
    add("nursing_home", "Prairie View Manor", "government", "health", "D5", 70, A_MED, "24h", "county-owned nursing home, 60 beds")
    add("assisted_living", "Wexford Commons Senior Living", "business", "health", "D3", 85, A_BILLX, "24h", "assisted living and memory care; private pay")
    add("hospice", "Gentle Harbor Hospice", "nonprofit", "health", "D4", 60, "insurance", "24h")
    add("free_clinic", "Good Neighbor Free Clinic", "nonprofit", "health", "D1", 6, "none", "Tu,Th 17:00-20:30", "volunteer-run clinic for uninsured adults")
    indep("child_care", lambda d: rng.choice(["Little Sprouts Learning Center", "Bright Beginnings Child Care", "Tiny Explorers Academy", "Sunflower Early Learning", "Kiddie Junction", "Stepping Stones Child Development", "Rainbow Bridge Daycare", "Mi Casita Bilingual Preschool", "Acorn Hollow Preschool", "ABC Clubhouse"]), "business", "health", [11, 9, 12, 6, 2, 1], (6, 30), "ach;debit;credit;check;cash;money_order", "Mo-Fr 06:30-18:00", "licensed child care center or home")
    add("head_start", "Halvern Community Action Head Start", "nonprofit", "health", "D1", 95, "none", "Mo-Fr 07:30-15:30", "Head Start and Early Head Start, five classroom sites")
    add("after_school", "Northside Youth Club", "nonprofit", "health", "D1", 30, A_ALL, "Mo-Fr 14:30-19:00", "after-school programs; sliding fees")
    add("after_school", "Halvern Community Rec Association", "nonprofit", "arts", "D3", 120, A_ALL + ";ach", "05:00-22:00", "family fitness, swim lessons, after-school care")
    add("food_bank", "Three Rivers Food Bank", "nonprofit", "health", "D2", 48, "none", "Mo-Fr 08:00-17:00", "regional food bank supplying pantries")
    for d, nm in [("D1", "Loaves & Fishes Pantry at St. Brigid"), ("D2", "Eastgate Community Pantry"), ("D4", "Ashford Mills Food Shelf"), ("D5", "Dunmore Ministerial Pantry")]:
        add("food_pantry", nm, "nonprofit", "health", d, 2, "none", "We 10:00-18:00", "volunteer food pantry; Wednesday distribution")
    add("community_action", "Halvern Community Action Agency", "nonprofit", "health", "D1", 70, "none", "Mo-Fr 08:30-16:30", "energy assistance, weatherization, emergency rent help")
    add("legal_aid", "Legal Aid of the Three Rivers", "nonprofit", "prof", "D1", 22, "none", "Mo-Fr 09:00-17:00", "free civil legal help")
    add("shelter", "Harbor House Shelter", "nonprofit", "health", "D1", 34, "none", "24h", "emergency shelter and day center")
    add("vita", "Halvern Free Tax Help", "nonprofit", "other", "D1", 4, "none", "Mo-Sa 10:00-18:00", "volunteer income tax assistance at Central Library and the community college")
    add("senior_center", "Halvern County Senior Services", "government", "gov", "D1", 46, "cash;check", "Mo-Fr 08:00-16:30", "senior centers in D1, D4, D5; congregate and home-delivered meals")

    # ---------------- vets (professional services)
    indep("vet", B.g_hood("Animal Hospital", "Veterinary Clinic", "Pet Clinic"), "business", "prof", [3, 2, 4, 2, 1, 0], (8, 22), A_ALL + ";bnpl", "Mo-Sa 08:00-18:00")
    add("vet", "Tolliver Large Animal Veterinary", "business", "prof", "D6", 7, A_ALL + ";check", "Mo-Fr 07:00-17:00")

    # ---------------- finance
    chain("bank", "First Halvern Bank", "financial", "fin", [3, 1, 2, 1, 1, 0], 16, A_BILL, "Mo-Fr 09:00-17:00", "community bank; overdraft fee $28; ATM at each branch")
    chain("bank", "Corbel National Bank", "financial", "fin", [2, 1, 2, 1, 0, 0], 18, A_BILL, "Mo-Fr 09:00-17:00", "large national bank branch; overdraft fee $34; $12 monthly fee under $1,500")
    chain("credit_union", "Three Forks Credit Union", "financial", "fin", [1, 1, 1, 1, 0, 0], 20, A_BILL, "Mo-Fr 09:00-17:30", "credit union; overdraft fee $25; payday-alternative loans")
    chain("check_casher", "Greenleaf Check Cashing", "financial", "fin", [2, 2, 0, 0, 0, 0], 4, A_CASH, "08:00-20:00", "check cashing, money orders, bill pay, prepaid reloads")
    chain("payday", "Stopgap Cash Advance", "financial", "fin", [1, 1, 0, 0, 1, 0], 3, "cash;debit;ach", "Mo-Sa 09:00-18:00", "payday lender; $15 per $100 for two weeks")
    chain("title_loan", "TitleWorks Loans", "financial", "fin", [0, 1, 0, 0, 1, 0], 3, "cash;debit", "Mo-Sa 09:00-18:00", "auto title lender")
    add("plasma", "BioBridge Plasma Center", "business", "health", "D2", 24, "prepaid", "07:00-19:00", "paid plasma donation; pays on a reloadable card")
    chain("pawn", "Silver Anvil Pawn", "business", "retail", [1, 1, 0, 1, 1, 0], 5, A_ALL, "09:00-18:00", "pawn loans and resale")
    chain("tax_prep", "Ledgerline Tax Service", "business", "prof", [1, 1, 1, 1, 1, 0], 9, A_ALL, "09:00-20:00", "storefront tax preparation; refund-transfer products")
    add("tax_prep", "Reyes Tax & Multiservicios", "business", "prof", "D2", 4, "cash;debit;money_order", "10:00-19:00", "tax prep, notary, money transfers, translations")
    indep("insurance_agency", B.g_sur("Insurance Agency", "Insurance Group"), "business", "fin", [7, 5, 8, 4, 2, 0], (3, 9), A_BILLX + ";cash", "Mo-Fr 09:00-17:00", "local insurance agency")
    indep("advisor", B.g_sur("Wealth Advisors", "Financial Planning", "Capital Partners"), "business", "fin", [6, 1, 7, 2, 0, 0], (3, 12), A_BILLX, "Mo-Fr 08:30-17:00")
    add("insurer_office", "Granite Shield Insurance – Regional Claims Center", "business", "fin", "D3", 420, A_BILLX, "Mo-Fr 08:00-18:00", "auto and home insurer; regional claims and service center")
    add("bank_hq", "First Halvern Bank – Operations Center", "financial", "fin", "D1", 210, A_BILLX, "Mo-Fr 08:00-17:00", "loan servicing and back office")

    # ---------------- other services
    indep("auto_repair", B.g_sur("Auto Repair", "Automotive", "Garage", "Transmission & Brake", "Collision Center"), "business", "other", [9, 10, 9, 7, 3, 2], (3, 12), A_ALL + ";check", "Mo-Fr 07:30-17:30")
    chain("tire", "Tread Depot", "business", "other", [0, 1, 1, 1, 1, 0], 9, A_ALL + ";bnpl", "Mo-Sa 07:30-18:00", "tires and alignment; lease-to-own financing")
    chain("oil_change", "LubeLane Quick Oil", "business", "other", [1, 1, 2, 1, 0, 0], 7, A_ALL, "08:00-18:00")
    chain("car_wash", "SudsRunner Car Wash", "business", "other", [1, 1, 2, 1, 0, 0], 8, A_ALL, "07:00-20:00")
    add("towing", "Ironhook Towing & Roadside", "business", "trans", "D2", 14, A_ALL, "24h")
    add("towing", "Tolliver Wrecker Service", "business", "trans", "D5", 4, "cash;debit;credit;check", "24h")
    indep("salon", lambda d: rng.choice(["%s Hair Studio", "%s Barbershop", "%s Cuts & Color", "Shear %s Salon", "%s Braids & Beauty", "%s Barber Lounge"]) % rng.choice(SUR + ["Northside", "Eastgate", "Classic", "Crown", "Velvet", "Main Street"]), "business", "other", [22, 15, 16, 10, 4, 1], (2, 9), "cash;debit;credit;p2p_app", "09:00-19:00", "salon or barbershop")
    indep("nail", lambda d: rng.choice(["Lotus Nails & Spa", "Polished Nail Bar", "Diamond Nails", "Lavender Nail Lounge", "Happy Nails & Spa"]), "business", "other", [6, 6, 7, 3, 1, 0], (3, 8), A_ALL, "09:30-19:30")
    indep("laundromat", lambda d: rng.choice(["Suds & Bubbles Laundromat", "Spin Cycle Coin Laundry", "Lavandería La Burbuja", "Wash Day Laundromat", "Clean Getaway Laundry"]), "business", "other", [5, 5, 0, 2, 1, 0], (1, 3), "cash;debit;credit;prepaid", "06:00-22:00", "coin and card laundromat")
    indep("dry_cleaner", B.g_sur("Cleaners", "Dry Cleaning & Tailoring"), "business", "other", [3, 2, 3, 1, 0, 0], (2, 6), A_ALL, "Mo-Sa 07:00-18:30")
    for d, nm in [("D1", "Whitcomb & Sons Funeral Home"), ("D2", "Serenity Memorial Chapel"), ("D3", "Hargrove Family Funeral & Cremation"),
                  ("D4", "Ashford Mills Mortuary"), ("D5", "Pruitt-Tolbert Funeral Home"), ("D1", "Baptiste Cremation Society")]:
        add("funeral", nm, "business", "other", d, rng.randint(4, 11), A_BILLX + ";cash;insurance", "08:00-18:00")
    indep("pet_groom", lambda d: rng.choice(["Wag & Wash Grooming", "Fluff & Buff Pet Salon", "Muddy Paws Grooming"]), "business", "other", [2, 2, 3, 1, 1, 0], (2, 5), A_ALL, "08:00-17:00")
    chain("ship_notary", "PakPost Shipping & Notary", "business", "other", [1, 1, 1, 1, 0, 0], 4, A_ALL, "Mo-Sa 09:00-18:30", "shipping, mailboxes, notary, fingerprinting")
    indep("repair_shop", B.g_sur("Appliance Repair", "Phone & Computer Repair", "Small Engine Repair", "Shoe & Leather Repair"), "business", "other", [4, 4, 3, 3, 2, 1], (1, 5), A_ALL, "Mo-Sa 09:00-18:00")
    indep("church", B.g_church, "religious", "other", [34, 22, 20, 16, 10, 8], (1, 12), "cash;check;ach;debit;credit", "Su,We 08:00-21:00", "congregation; midweek service Wednesday evening")
    for d, nm in [("D1", "Masjid Al-Salam of Halvern"), ("D2", "An-Noor Islamic Center"), ("D1", "Temple Beth Shalom"), ("D3", "Halvern Hindu Temple & Cultural Center"),
                  ("D2", "Three Rivers Sikh Gurdwara"), ("D1", "Lotus Path Buddhist Center"), ("D1", "Halvern Unitarian Fellowship"), ("D6", "Tolliver Valley Mennonite Church")]:
        add("church", nm, "religious", "other", d, rng.randint(1, 6), "cash;check;ach;debit;credit", "08:00-21:00", "congregation")
    for d, nm in [("D1", "United Fund of Greater Halvern"), ("D1", "Homefront Builders"), ("D1", "Halvern Literacy Council"), ("D4", "Ashford Mills Historical Society"),
                  ("D1", "Halvern Area Labor Council"), ("D3", "Stonebridge Service Club Foundation"), ("D5", "Tolliver County Growers Association"), ("D2", "Centro Comunitario Las Américas"),
                  ("D1", "New Arrivals Welcome Center"), ("D1", "Halvern Animal Rescue League")]:
        add("nonprofit", nm, "nonprofit", "other", d, rng.randint(3, 24), "ach;check;credit;debit;cash", "Mo-Fr 09:00-17:00")

    # ---------------- arts, entertainment, recreation, information
    chain("gym", "IronRoot Gym", "business", "arts", [1, 1, 1, 0, 0, 0], 16, "ach;debit;credit", "05:00-23:00", "gym; monthly dues by autopay")
    chain("gym", "Pulse24 Fitness", "business", "arts", [0, 0, 1, 1, 0, 0], 12, "ach;debit;credit", "24h", "24-hour gym")
    add("bowling", "Kingpin Lanes & Arcade", "business", "arts", "D2", 22, A_ALL, "11:00-23:00")
    add("country_club", "Stonebridge Country Club", "nonprofit", "arts", "D3", 110, "ach;check;credit", "07:00-22:00", "private golf and tennis club; monthly dues plus dining minimum")
    add("golf", "Ashford Mills Municipal Golf Course", "government", "arts", "D4", 14, A_ALL, "07:00-18:00")
    add("museum", "Halvern Children's Museum", "nonprofit", "arts", "D1", 24, A_ALL + ";ebt_snap", "We-Su 10:00-17:00", "museum; $3 admission with an EBT card")
    add("theater", "Bellamy Theatre", "nonprofit", "arts", "D4", 12, A_ALL, "We-Su 12:00-22:00", "restored downtown theater")
    add("trampoline", "SkyBounce Family Fun Park", "business", "arts", "D3", 30, A_ALL, "10:00-21:00")
    add("cinema", "Starlite Cinemas 14", "business", "info", "D3", 55, A_ALL, "11:00-23:30")
    add("cinema", "Starlite Cinemas Ashford 6", "business", "info", "D4", 22, A_ALL, "15:00-23:00")
    indep("studio", lambda d: rng.choice(["Tempo Dance Academy", "Halvern School of Music", "Tiger Crane Martial Arts", "Little Kickers Tae Kwon Do", "Brushstrokes Art Studio", "Stonebridge Gymnastics"]), "business", "pedu", [2, 2, 4, 2, 0, 0], (3, 12), "ach;debit;credit;check;cash", "Mo-Sa 14:00-20:30", "youth lessons; monthly tuition")
    add("youth_sports", "Halvern Youth Soccer League", "nonprofit", "arts", "D3", 3, "debit;credit;check;cash", "Mo-Fr 16:00-20:00", "volunteer league; spring registration open")
    add("youth_sports", "Ashford Mills Little Diamond Baseball", "nonprofit", "arts", "D4", 2, "debit;credit;check;cash", "Mo-Fr 16:00-20:00", "volunteer league; spring registration open")
    add("isp", "Corvid Broadband", "business", "info", "D2", 180, A_BILL, "Mo-Sa 09:00-18:00", "cable internet and TV provider for D1-D4; payment counter at Eastgate")
    add("isp", "PrairieLink Fiber Cooperative", "nonprofit", "info", "D5", 34, A_BILL, "Mo-Fr 08:00-17:00", "member-owned fiber and phone for Dunmore and parts of the county")
    add("newspaper", "The Halvern Ledger", "business", "info", "D1", 45, A_BILLX, "Mo-Fr 08:00-17:00", "daily newspaper")
    add("broadcast", "Channel 9 Halvern", "business", "info", "D1", 62, A_B2B, "24h", "local TV station")
    add("software", "Lumen Analytics", "business", "info", "D1", 190, A_B2B, "Mo-Fr 08:00-18:00", "software firm; hybrid schedules")
    add("data_center", "Granary Data Center", "business", "info", "D3", 45, A_B2B, "24h")

    # ---------------- education
    for nm, d, sz in [("Halvern Unified School District", "D1", 2550), ("Ashford Mills City Schools", "D4", 640), ("Tolliver County Schools", "D5", 560)]:
        add("school_district", nm, "government", "gov", d, sz, "ach;debit;credit;check;cash", "Mo-Fr 07:00-16:30", "public school district; employer of record for school staff")
    for kind, label, counts in [("school_elem", "Elementary School", [5, 4, 5, 3, 1, 1]), ("school_mid", "Middle School", [2, 1, 2, 1, 1, 0]), ("school_high", "High School", [1, 1, 1, 1, 1, 0])]:
        for d, c in zip(DISTRICTS, counts):
            for i in range(c):
                nm = "%s %s" % (rng.choice(["Linden Heights", "Riverbend", "Cesar Estrada", "Maple Grove", "Kettle Creek", "Stonebridge", "Fox Hollow", "Harriet Greene", "Sycamore", "Ashford", "Mill Street", "Dunmore", "Tolliver Valley", "Northside", "Eastgate", "Prairie Crossing", "Willow Bend", "Foundry", "Garfield", "Lakeshore"]), label)
                add(kind, nm, "government", "gov", d, 1, "none", "Mo-Fr 07:15-15:45", "public school" + ("; community eligibility: all meals free" if d in ("D1", "D2", "D5", "D6") else ""))
    add("private_school", "St. Anselm Catholic School", "religious", "pedu", "D1", 38, A_BILLX + ";cash", "Mo-Fr 07:30-15:30", "K-8 parochial school")
    add("private_school", "Halvern Christian Academy", "religious", "pedu", "D3", 62, A_BILLX, "Mo-Fr 07:30-15:30", "K-12")
    add("private_school", "Briarwood Country Day School", "nonprofit", "pedu", "D3", 85, A_BILLX, "Mo-Fr 07:45-15:45", "independent K-12; highest tuition in the area")
    add("private_school", "Ashford Montessori School", "nonprofit", "pedu", "D4", 18, A_BILLX, "Mo-Fr 08:00-15:00", "preschool through grade 6")
    add("college_private", "Wexley College", "nonprofit", "pedu", "D4", 330, A_BILLX, "Mo-Fr 08:00-17:00", "residential liberal arts college; about 1,100 students in dorms")
    add("community_college", "Three Rivers Community College", "government", "gov", "D2", 480, A_BILLX + ";cash", "Mo-Fr 07:30-21:00", "main campus Eastgate; center in Ashford Mills")
    add("trade_school", "Halvern Technical Institute", "business", "pedu", "D2", 44, A_BILLX, "Mo-Fr 08:00-21:00", "for-profit trade school: welding, HVAC, medical assisting")
    indep("tutoring", lambda d: rng.choice(["Bright Path Learning Center", "Summit Tutoring & Test Prep", "Mathways Tutoring"]), "business", "pedu", [1, 1, 2, 1, 0, 0], (4, 12), "ach;debit;credit", "Mo-Sa 14:00-20:00")

    # ---------------- government
    add("city", "City of Halvern", "government", "gov", "D1", 820, A_GOV, "Mo-Fr 08:30-16:30", "city hall, police, fire, public works, permits")
    add("city", "City of Ashford Mills", "government", "gov", "D4", 210, A_GOV, "Mo-Fr 08:30-16:30", "city hall, police, fire, utilities")
    add("city", "Town of Dunmore", "government", "gov", "D5", 38, A_GOV, "Mo-Fr 08:30-16:00", "town hall, water, two police officers")
    add("county", "Halvern County Government", "government", "gov", "D4", 640, A_GOV, "Mo-Fr 08:30-16:30", "county seat in Ashford Mills; annex downtown; tax office, clerk, elections")
    add("county", "Tolliver County Government", "government", "gov", "D5", 120, A_GOV, "Mo-Fr 08:30-16:30", "rural county seat in Dunmore")
    add("courthouse", "Halvern County Courthouse", "government", "gov", "D4", 95, A_GOV, "Mo-Fr 08:30-16:30", "state trial courts, clerk of court; online payments carry a 3% card fee")
    add("courthouse", "Halvern Municipal Court", "government", "gov", "D1", 30, A_GOV, "Mo-Fr 08:30-16:30", "traffic and ordinance cases")
    add("courthouse", "Tolliver County Courthouse", "government", "gov", "D5", 18, "cash;check;money_order", "Mo-Fr 08:30-16:00", "court clerk takes cash, check or money order only")
    add("jail", "Halvern County Detention Center", "government", "gov", "D4", 110, "cash;debit;credit", "24h", "county jail, about 240 people held; commissary and phone deposits carry vendor fees")
    add("health_dept", "Halvern County Health Department", "government", "gov", "D1", 85, A_GOV, "Mo-Fr 08:00-16:30", "immunizations, WIC clinic, vital records; satellite in Ashford Mills")
    add("ems", "Halvern County EMS", "government", "gov", "D4", 120, "insurance;check;credit", "24h", "county ambulance service")
    add("library", "Halvern Public Library – Central", "government", "gov", "D1", 44, "cash;debit;credit", "Mo-Sa 09:00-20:00", "main library; 60 public computers; fine-free")
    add("library", "Halvern Public Library – Eastgate Branch", "government", "gov", "D2", 12, "cash;debit;credit", "Mo-Sa 10:00-19:00")
    add("library", "Halvern Public Library – Stonebridge Branch", "government", "gov", "D3", 12, "cash;debit;credit", "Mo-Sa 10:00-19:00")
    add("library", "Ashford Mills Public Library", "government", "gov", "D4", 10, "cash;debit;credit", "Mo-Sa 10:00-18:00")
    add("library", "Tolliver County Library", "government", "gov", "D5", 4, "cash", "Tu-Sa 12:00-18:00", "one-room library; bookmobile visits open country on Thursdays")
    add("parks", "Halvern Parks & Recreation", "government", "gov", "D1", 95, A_ALL, "06:00-21:00", "rec centers, pools, youth leagues, senior fitness")
    add("transit", "Halvern Area Transit", "government", "gov", "D1", 210, "cash;prepaid;debit;credit", "05:00-23:00", "bus system serving D1-D2 with limited D3 and D4 routes; fare $1.75")
    add("paratransit", "HAT Access Paratransit", "government", "gov", "D1", 40, "cash;prepaid", "06:00-20:00", "ADA paratransit; book a day ahead; fare $3.50")
    add("rural_transit", "Tolliver County Rides", "government", "gov", "D5", 9, "cash", "Mo-Fr 07:00-17:00", "demand-response van; 48-hour notice; fare $3")
    add("parking", "Halvern Parking Authority", "government", "gov", "D1", 18, "debit;credit;cash", "24h", "meters, garages, citations")
    add("housing_authority", "Halvern Housing Authority", "government", "gov", "D1", 55, "ach;money_order;check", "Mo-Fr 08:30-16:30", "public housing and vouchers")
    add("airport", "Halvern Regional Airport Authority", "government", "trans", "D2", 90, A_CARD, "04:30-23:30", "regional airport")
    add("dmv", "State Driver Services Center – Eastgate", "government", "gov", "D2", 28, A_GOV, "Mo-Fr 08:00-16:30", "driver licenses, IDs, voter registration; appointments recommended")
    add("dmv", "State Driver Services – Dunmore Office", "government", "gov", "D5", 3, "cash;check;money_order", "Tu,Th 09:00-15:30", "part-time rural office: Tuesdays and Thursdays only")
    add("benefits_office", "State Department of Family & Economic Services – Halvern Office", "government", "gov", "D1", 110, "none", "Mo-Fr 08:00-16:30", "SNAP, Medicaid, TANF, child care assistance; online portal 'MyBenefits'")
    add("benefits_office", "State Department of Family & Economic Services – Ashford Mills Office", "government", "gov", "D4", 26, "none", "Mo-Fr 08:00-16:30", "also serves Tolliver County on Mondays in Dunmore")
    add("workforce", "State Workforce Commission Career Center", "government", "gov", "D1", 32, "none", "Mo-Fr 08:00-16:30", "unemployment claims help, job search, training grants")
    add("probation", "State Probation & Parole Office", "government", "gov", "D1", 24, "money_order;debit;credit", "Mo-Fr 08:00-16:30", "supervision fees payable by money order or card")
    add("tollway", "Three Rivers Tollway Authority", "government", "gov", "D3", 40, "ach;debit;credit", "24h", "toll road between the outer suburbs and downtown; transponder or pay-by-plate")
    add("ssa", "Social Security field office – Halvern", "government", "fed", "D1", 34, "none", "Mo-Fr 09:00-16:00", "federal office; appointments required for most services")
    add("va_clinic", "VA Community Clinic – Halvern", "government", "fed", "D1", 70, "insurance", "Mo-Fr 07:30-16:30", "veterans outpatient clinic")
    for d, nm in [("D1", "U.S. Post Office – Halvern Main"), ("D1", "U.S. Post Office – Northside Station"), ("D2", "U.S. Post Office – Eastgate"), ("D3", "U.S. Post Office – Stonebridge"),
                  ("D4", "U.S. Post Office – Ashford Mills"), ("D5", "U.S. Post Office – Dunmore"), ("D6", "U.S. Post Office – Crossroads (contract unit)")]:
        add("post_office", nm, "government", "fed", d, 40 if d != "D6" else 2, "cash;debit;credit", "Mo-Fr 08:30-17:00", "postal counter; money orders sold for cash or debit only")
    add("federal_office", "Federal Building – Halvern", "government", "fed", "D1", 140, "none", "Mo-Fr 08:00-17:00", "federal court, airport security staff base, other agencies")
    add("usda", "USDA Service Center – Dunmore", "government", "fed", "D5", 12, "none", "Mo-Fr 08:00-16:30", "farm programs and conservation offices")
    add("armory", "National Guard Armory – Halvern", "government", "fed", "D2", 30, "none", "Mo-Fr 08:00-16:30")

    # ---------------- utilities
    add("electric", "Halvern Power & Light", "business", "util", "D1", 190, A_BILL, "Mo-Fr 08:00-17:00", "investor-owned electric utility for D1-D4; walk-in payment center downtown")
    add("electric_coop", "Prairie Rivers Electric Cooperative", "nonprofit", "util", "D5", 46, A_BILL, "Mo-Fr 08:00-16:30", "member-owned electric co-op for Dunmore and open country")
    add("gas_util", "Tri-County Natural Gas", "business", "util", "D2", 62, A_BILL, "Mo-Fr 08:00-17:00")
    add("water", "City of Halvern Water & Sewer", "government", "gov", "D1", 130, A_BILL, "Mo-Fr 08:30-16:30", "city water utility; $40 reconnection fee")
    add("water", "Ashford Mills Utilities", "government", "gov", "D4", 44, A_BILL, "Mo-Fr 08:30-16:30")
    add("water", "Dunmore Municipal Water", "government", "gov", "D5", 6, "cash;check;money_order", "Mo-Fr 08:30-16:00", "pay at town hall; no online payments")
    add("trash", "GreenBin Waste Services", "business", "admin", "D3", 85, A_BILLX, "Mo-Fr 07:00-17:00", "private hauler for D3-D6")
    add("propane", "Tolliver Propane & Oil", "business", "retail", "D5", 14, "cash;check;debit;credit", "Mo-Fr 07:30-17:00", "bulk propane delivery; minimum fill 150 gallons unless on budget plan")
    add("quarry", "Redstone Quarry", "business", "util", "D6", 55, A_B2B, "Mo-Fr 06:00-16:00", "crushed stone and gravel")

    # ---------------- real estate and housing
    for d, nm in [("D1", "Cornerstone Residential Management"), ("D1", "Foundry Lofts Leasing Office"), ("D1", "Riverfront Towers Apartments"), ("D1", "Midtown Flats"),
                  ("D2", "Maplewood Property Group"), ("D2", "Eastgate Village Apartments"), ("D2", "Kettle Creek Mobile Home Community"), ("D3", "The Preserve at Stonebridge"),
                  ("D3", "Fox Hollow Townhomes"), ("D4", "Mill Street Property Management"), ("D4", "Ashford Arms Apartments"), ("D5", "Dunmore Square Rentals"),
                  ("D6", "Route 9 Mobile Home Park"), ("D1", "Pelham Street Rentals LLC"), ("D2", "Garfield Park Duplexes LLC"), ("D4", "Hospital Hill Rentals LLC")]:
        add("landlord", nm, "business", "re", d, rng.randint(3, 22), "ach;debit;credit;check;money_order;cash", "Mo-Fr 09:00-17:00", "rental housing; online portal adds 2.95% for cards")
    indep("brokerage", B.g_sur("Realty", "Real Estate Group", "& Associates Realtors"), "business", "re", [4, 2, 6, 3, 1, 0], (4, 26), A_BILLX, "09:00-18:00")
    add("hoa_mgmt", "Community Association Partners", "business", "re", "D3", 22, "ach;check;credit", "Mo-Fr 09:00-17:00", "manages homeowner associations in the outer suburbs")
    add("storage", "LockTight Self Storage", "business", "re", "D2", 5, "ach;debit;credit;cash", "06:00-22:00")

    # ---------------- employers that mostly sell outside the household day
    for nm, d, sz, note in [("Vandermeer Axle & Driveline", "D4", 1150, "auto parts plant, three shifts"), ("Halvern Packaging Works", "D2", 420, "corrugated packaging"),
                            ("Corliss Food Products", "D4", 380, "food processing, two shifts"), ("Tolliver Wood Products", "D5", 140, "trusses and pallets"),
                            ("Stratum Precision Machining", "D3", 160, "contract machining")]:
        add("manufacturer", nm, "business", "mfg", d, sz, A_B2B, "24h", note)
    indep("manufacturer", B.g_sur("Fabrication", "Tool & Die", "Plastics", "Sign & Print Works", "Cabinet Works", "Metal Finishing", "Bakery Commissary"), "business", "mfg", [4, 8, 4, 6, 2, 1], (8, 60), A_B2B, "Mo-Fr 06:00-16:30", "small manufacturer")
    for nm, d, sz, note in [("Bazaaro Fulfillment Center HV2", "D3", 760, "e-commerce fulfillment, 24-hour shifts"), ("Crosswind Logistics Distribution Center", "D2", 380, "third-party warehouse"),
                            ("ParcelPoint Delivery Hub", "D2", 260, "parcel sort and delivery"), ("Airline Ground Services at HRA", "D2", 90, "airport ground handling")]:
        add("warehouse", nm, "business", "trans", d, sz, A_B2B, "24h", note)
    indep("trucking", B.g_sur("Trucking", "Freight Lines", "Hauling", "Moving & Storage"), "business", "trans", [1, 4, 2, 2, 1, 1], (6, 40), A_B2B, "Mo-Sa 05:00-18:00")
    for nm, d, sz, note in [("Three Rivers Foodservice Distributors", "D2", 240, "broadline food distributor to restaurants and schools"), ("Halvern Building Supply", "D2", 90, "lumber and drywall wholesale"),
                            ("Bellweather Beverage Distributing", "D2", 130, "beverage wholesaler"), ("Prairie Ag Supply", "D5", 40, "seed, fertilizer, fuel"),
                            ("Halvern Medical Supply", "D4", 55, "medical supply wholesaler"), ("Dunmore Farmers Cooperative Elevator", "D5", 36, "grain elevator and agronomy")]:
        add("wholesaler", nm, "business", "whole", d, sz, A_B2B, "Mo-Fr 05:00-17:00", note)
    indep("wholesaler", B.g_sur("Produce Wholesale", "Restaurant Supply", "Electrical Supply", "Plumbing Supply", "Paper & Janitorial Supply", "Auto Parts Wholesale", "Import Foods Wholesale"), "business", "whole", [5, 12, 5, 5, 1, 0], (6, 45), A_B2B, "Mo-Fr 06:00-16:30")
    add("construction", "Brackett Construction Group", "business", "constr", "D3", 220, A_B2B, "Mo-Fr 06:30-17:00", "commercial general contractor")
    add("construction", "Halvern Paving & Site", "business", "constr", "D2", 110, A_B2B, "Mo-Fr 06:00-16:30")
    indep("construction", B.g_sur("Plumbing & Heating", "Electric", "Roofing", "Builders", "Remodeling", "Concrete", "Drywall & Paint", "Heating & Air", "Homes", "Excavating", "Fence & Deck"), "business", "constr", [26, 34, 40, 24, 12, 10], (2, 22), "check;ach;credit;debit;cash", "Mo-Fr 07:00-16:30", "trade contractor")
    indep("law", B.g_sur("Law Office", "& Partners LLP", "Legal Group", "Immigration Law"), "business", "prof", [18, 3, 8, 6, 2, 0], (2, 28), A_BILLX, "Mo-Fr 08:30-17:30")
    indep("accounting", B.g_sur("CPAs", "Accounting & Tax", "Bookkeeping"), "business", "prof", [8, 3, 8, 4, 2, 0], (2, 22), A_BILLX, "Mo-Sa 08:00-18:00")
    indep("prof_firm", B.g_sur("Engineering", "Architects", "Design Studio", "IT Solutions", "Marketing", "Consulting Group", "Surveying", "Environmental"), "business", "prof", [16, 4, 14, 5, 1, 0], (3, 55), A_B2B, "Mo-Fr 08:00-17:30")
    for nm, d, sz, note in [("StaffRight Staffing", "D2", 420, "temp agency; weekly pay, paycards"), ("ClearPane Janitorial", "D2", 300, "contract cleaning, evening shifts"),
                            ("Sentinel Guard Services", "D1", 150, "contract security"), ("GreenEdge Landscaping", "D3", 120, "commercial landscaping"),
                            ("Halvern Customer Care Center", "D3", 450, "outsourced call center")]:
        add("admin_firm", nm, "business", "admin", d, sz, A_B2B, "24h", note)
    indep("admin_firm", B.g_sur("Cleaning Services", "Lawn & Landscape", "Pest Control", "Office Services", "Security"), "business", "admin", [8, 10, 10, 6, 2, 1], (3, 30), "check;ach;credit;debit;cash", "Mo-Fr 07:00-17:00")
    for nm, d, sz in [("Marlow's Market Headquarters", "D3", 300), ("Vandermeer North America Offices", "D4", 180), ("Oxbow Stores Regional Office", "D3", 110), ("Granite Shield Holdings", "D3", 130)]:
        add("mgmt_hq", nm, "business", "mgmt", d, sz, A_B2B, "Mo-Fr 08:00-17:30", "corporate office")
    # farms and packing
    for nm, d, sz, note in [("Hollis Family Farms", "D6", 9, "corn, soybeans, wheat"), ("Rivera Produce Farm", "D6", 60, "vegetables; seasonal crews"),
                            ("Tolliver Valley Orchards", "D6", 45, "apples and peaches; pruning in March"), ("Dunmore Dairy", "D6", 20, "350-cow dairy"),
                            ("Bittersweet Greenhouse & Nursery", "D6", 35, "bedding plants; spring ramp-up"), ("Double T Cattle Company", "D6", 6, "cow-calf ranch"),
                            ("Sweetgrass Egg Farm", "D6", 25, "cage-free eggs"), ("Okafor Pastured Poultry", "D6", 5, "direct-market farm"),
                            ("Kettle Creek Mushroom Farm", "D5", 30, "year-round mushrooms"), ("Three Sisters Vegetable Farm", "D6", 8, "CSA and market farm")]:
        add("farm", nm, "business", "ag", d, sz, "check;ach;cash", "05:30-18:30", note)
    add("packing", "Tolliver Valley Packing Co.", "business", "ag", "D5", 90, A_B2B, "Mo-Sa 06:00-16:00", "packing shed and cold storage; buys from area growers")
    add("sale_barn", "Tolliver Sale Barn", "business", "whole", "D5", 12, "check;cash", "We 08:00-17:00", "livestock auction every Wednesday")
    add("farmers_market", "Halvern Winter Farmers Market", "nonprofit", "retail", "D1", 2, "cash;debit;credit;ebt_snap", "We 14:00-18:00", "Wednesday indoor market; SNAP tokens matched dollar-for-dollar up to $20")

    # ---------------- outside-Halvern counterparties (district EXT)
    ext = [
        ("x_treasury", "U.S. Treasury (federal payments)", "government", "fed", "pays Social Security, SSI, VA, tax refunds; receives federal taxes"),
        ("x_ssa", "Social Security Administration", "government", "fed", "benefit programs"),
        ("x_cms", "Medicare (CMS)", "government", "fed", "Medicare Parts A, B and D"),
        ("x_medicaid", "State Medicaid Program", "government", "gov", "Medicaid and CHIP; managed care through Arbor Community Care"),
        ("x_va", "U.S. Department of Veterans Affairs", "government", "fed", "VA health care and benefits"),
        ("x_irs", "Internal Revenue Service", "government", "fed", "federal income tax and payroll tax deposits"),
        ("x_staterev", "State Department of Revenue", "government", "gov", "state income and sales tax"),
        ("x_snap", "State EBT (SNAP, WIC, TANF)", "government", "gov", "state EBT processor; federal benefit dollars"),
        ("x_ui", "State Unemployment Insurance Fund", "government", "gov", "weekly unemployment benefits"),
        ("x_csdu", "State Child Support Disbursement Unit", "government", "gov", "passes child support from payer to custodial parent"),
        ("x_uscis", "U.S. Citizenship and Immigration Services", "government", "fed", "immigration filing fees; electronic payment only"),
        ("x_ed", "Federal student loan servicer EdPath", "financial", "fin", "services federal student loans"),
        ("x_ins_a", "Northlight Health Insurance", "financial", "fin", "employer and marketplace health plans"),
        ("x_ins_b", "Arbor Health Plan", "financial", "fin", "employer plans; Medicare Advantage; Medicaid managed care as Arbor Community Care"),
        ("x_tricare", "Military health plan (TRICARE)", "government", "fed", "military health coverage"),
        ("x_cc1", "Summit Ridge Card Services", "financial", "fin", "credit card issuer"),
        ("x_cc2", "Harborline Card", "financial", "fin", "credit card issuer; store cards"),
        ("x_acq", "TillStream Merchant Services", "financial", "fin", "card processor for local merchants"),
        ("x_mort1", "Homestead Loan Servicing", "financial", "fin", "mortgage servicer"),
        ("x_mort2", "Juniper Mortgage", "financial", "fin", "mortgage servicer"),
        ("x_auto1", "DriveLine Credit", "financial", "fin", "subprime auto lender"),
        ("x_auto2", "Corbel Auto Finance", "financial", "fin", "auto lender"),
        ("x_autoins", "Granite Shield Insurance", "financial", "fin", "auto, home and renters insurance"),
        ("x_farmins", "Farmstead Mutual Insurance", "financial", "fin", "rural auto and farm insurance"),
        ("x_life", "Sentinel Life Assurance", "financial", "fin", "life insurance"),
        ("x_collect", "Alder Creek Recovery Services", "financial", "fin", "medical debt collector"),
        ("x_bnpl1", "LaterLeaf", "financial", "fin", "buy-now-pay-later; four payments every two weeks"),
        ("x_bnpl2", "FourFold Pay", "financial", "fin", "buy-now-pay-later"),
        ("x_p2p1", "Palmo", "financial", "fin", "person-to-person payment app; 1.75% instant cash-out fee"),
        ("x_p2p2", "Tandem Pay", "financial", "fin", "bank-linked person-to-person transfers"),
        ("x_prepaid", "Kestrel Prepaid Card", "financial", "fin", "general-purpose reloadable prepaid card; $5.95 monthly fee; $3.95 cash reload"),
        ("x_paycard", "PayRoute Paycard", "financial", "fin", "employer payroll card"),
        ("x_ewa", "PaySooner", "financial", "fin", "earned-wage access app; $3.49 instant fee"),
        ("x_onlinebank", "Nimbus Bank (online)", "financial", "fin", "online bank; no overdraft fees, declines instead"),
        ("x_remit", "EnvíoPronto Money Transfer", "financial", "fin", "international money transfers through grocery and check-cashing agents"),
        ("x_market", "Bazaaro (online marketplace)", "business", "retail", "largest online retailer"),
        ("x_shop2", "Shelfline.com", "business", "retail", "online general merchandise"),
        ("x_shop3", "Nestwell Home (online)", "business", "retail", "online furniture and decor"),
        ("x_alarm", "Hearthguard Monitoring", "business", "admin", "home alarm monitoring by subscription"),
        ("x_union_ed", "Halvern Educators Association", "nonprofit", "other", "union local for school employees; dues by payroll deduction"),
        ("x_union_pub", "Public Workers of Halvern, Local 77", "nonprofit", "other", "union local for city, county and transit employees"),
        ("x_union_trades", "Allied Trades & Service Workers, Local 418", "nonprofit", "other", "union local for trades, plant, warehouse, grocery and health care workers"),
        ("x_shop4", "PetParcel (online)", "business", "retail", "pet supplies by subscription"),
        ("x_rxmail", "ScriptPost Mail Pharmacy", "business", "retail", "mail-order pharmacy"),
        ("x_stream1", "StreamHollow", "business", "info", "video streaming"),
        ("x_stream2", "Kinora+", "business", "info", "video streaming"),
        ("x_stream3", "TuneRiver", "business", "info", "music streaming"),
        ("x_stream4", "PlayOrbit", "business", "info", "games and app store"),
        ("x_cloud", "VaultBox", "business", "info", "cloud storage"),
        ("x_mobile1", "Vireo Wireless", "business", "info", "postpaid mobile carrier"),
        ("x_mobile2", "Tallgrass Mobile", "business", "info", "postpaid mobile carrier with rural coverage"),
        ("x_mobile3", "Pocket Prepaid", "business", "info", "prepaid mobile brand"),
        ("x_sat", "SkyHop Satellite Internet", "business", "info", "satellite internet for open country"),
        ("x_ride1", "Rydeline", "business", "trans", "ride-hailing app"),
        ("x_ride2", "Vamos Ride", "business", "trans", "ride-hailing app"),
        ("x_deliv1", "Forkly", "business", "trans", "restaurant delivery app"),
        ("x_deliv2", "Zipmeal", "business", "trans", "restaurant and grocery delivery app"),
        ("x_travel", "Farefinder Travel", "business", "trans", "online travel agency"),
        ("x_air", "SkyBridge Air", "business", "trans", "airline serving Halvern Regional"),
        ("x_tix", "TixGate", "business", "arts", "event ticketing with service fees"),
        ("x_bet", "LuckyLine Sportsbook", "business", "arts", "licensed online sports wagering"),
        ("x_crowd", "KindlyFund", "business", "other", "crowdfunding platform"),
        ("x_taxsoft", "TaxTrail (online tax software)", "business", "prof", "do-it-yourself tax filing"),
        ("x_broker", "Northgate Brokerage", "financial", "fin", "brokerage and retirement accounts"),
        ("x_529", "State College Savings Plan", "government", "gov", "529 plan"),
        ("x_tuition", "TuitionBridge", "financial", "fin", "tuition payment-plan processor used by local schools"),
        ("x_mealpay", "LunchLedger", "business", "info", "school meal account portal; $2.75 fee per online deposit"),
        ("x_jailpay", "ConnectInside", "business", "info", "jail phone and commissary deposit vendor; fees $3.95-$7.95"),
        ("x_medcard", "SmileLine Credit", "financial", "fin", "health care financing card with deferred interest"),
        ("x_customers", "Customers (general public)", "business", "other", "pseudo-party for receipts from many unnamed customers"),
        ("x_outemp", "Out-of-area employers", "business", "other", "employers outside Halvern for residents who commute out"),
        ("x_abroad", "Family abroad", "business", "other", "pseudo-party for international remittance recipients and senders"),
        ("x_outfam", "Family and friends outside Halvern", "business", "other", "pseudo-party for transfers to and from people elsewhere"),
        ("x_stateuniv", "State University (out of area)", "government", "gov", "public university attended by some residents"),
        ("x_scam", "Unknown party (suspected scam)", "business", "other", "pseudo-party for scam attempts"),
        ("x_pension", "Pension and annuity payers", "financial", "fin", "public and private pension funds"),
        ("x_charity", "National charities (online)", "nonprofit", "other", "pseudo-party for online donations"),
        ("x_suppliers", "Out-of-area suppliers", "business", "whole", "pseudo-party for business purchases from outside Halvern"),
    ]
    for kind, nm, otype, sec, note in ext:
        o = add(kind, nm, otype, sec, "EXT", 1, "ach;debit;credit;check" if otype != "government" else "ach;check;debit;credit", "24h", note)
    return B.orgs


def index_orgs(orgs):
    by_kind, by_kd = {}, {}
    for o in orgs:
        by_kind.setdefault(o.kind, []).append(o)
        by_kd.setdefault((o.kind, o.district), []).append(o)
    return by_kind, by_kd


# Storefronts Halvern had far fewer of than the country, per 100,000 residents, from County Business Patterns 2023
# (sources/derived/cbp_establishments_per_100k.csv, sources/tools/cbp_outlets.py; employer establishments only). Where
# v1 had under 60% of the CBP rate, outlets are added after the city is built, copied from an existing outlet of the
# kind, so v1's people, employers and accounts stay as they were; the new outlets have no Halvern staff on the roster.
# Kinds v1 has too many of (groceries, bars, salons, laundromats, churches) are left as they are: removing them would
# redraw the population. Nursing homes and assisted living are left too: their residents are part of the population.
CBP_PER_100K = {("fastfood",): 80.65, ("coffee",): 25.42, ("bank", "credit_union"): 30.63, ("physician",): 61.10, ("home_health",): 12.17,
                ("car_dealer",): 14.05 - 1.5, ("hotel",): 16.69, ("gym",): 12.41, ("auto_parts",): 11.52, ("clothing",): 24.87}


def add_cbp_outlets(sim):
    from .config import DSHARE, side_rng
    srng = side_rng(sim.cfg["RANDOM_SEED"], "cbp_outlets")
    names = {o.name for o in sim.orgs}
    pop = len(sim.persons)
    added = 0
    for kinds, per in CBP_PER_100K.items():
        have = [o for o in sim.orgs if o.kind in kinds and o.district != "EXT"]
        if not have:
            continue
        for _ in range(max(0, int(round(per * pop / 1e5)) - len(have))):
            t = srng.choice(have)
            d = srng.choices(list(DSHARE), list(DSHARE.values()))[0]
            base = t.name.split(" – ")[0].split(" (")[0]
            name = "%s – %s" % (base, srng.choice(HOODS.get(d, ["Halvern"])))
            k = 2
            while name in names:
                name, k = "%s – %s %d" % (base, srng.choice(HOODS.get(d, ["Halvern"])), k), k + 1
            names.add(name)
            o = Org("O%04d" % (len(sim.orgs) + 1), name, t.kind, t.otype, t.sector, d, t.size, ";".join(sorted(t.acc)), t.hours, t.notes)
            o.open, o.close = parse_hours(o.hours, sim.cal["dow"])
            if closed_for_holiday(o.kind, sim.cal):
                o.open, o.close = None, None
            sim.orgs.append(o)
            added += 1
    # A dialysis clinic in the rural town. CMS's facility list (sources/raw/cms_dialysis, October 2026) against the 2023
    # rural-urban codes: 72% of nonmetro residents have a clinic in their own county (27.6% do not). v1 had both of
    # Halvern's clinics in the city and suburbs, so every rural patient drove 15-21 miles each way three times a week.
    t = next((o for o in sim.orgs if o.kind == "dialysis"), None)
    if t is not None and not any(o.kind == "dialysis" and o.district == "D5" for o in sim.orgs):
        o = Org("O%04d" % (len(sim.orgs) + 1), "%s – %s" % (t.name.split(" – ")[0], (HOODS.get("D5") or ["Halvern"])[0]), "dialysis", t.otype, t.sector,
                "D5", 12, ";".join(sorted(t.acc)), t.hours, "in-center hemodialysis, 12 stations")
        o.open, o.close = parse_hours(o.hours, sim.cal["dow"])
        sim.orgs.append(o)
        added += 1
    sim.by_kind, sim.by_kd = index_orgs(sim.orgs)
    sim.by_name = {o.name: o for o in sim.orgs}
    return added
