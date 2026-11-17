"""Template library: kind -> (action phrase, [job statements], [narratives])."""


def k(act, js, nar):
    return (act, [js] if isinstance(js, str) else list(js), [nar] if isinstance(nar, str) else list(nar))


def bill(what, so, extra=None):
    nar = ["%s paid to {org}." % what.capitalize(), "This month's %s to {org}." % what]
    if extra:
        nar.append(extra)
    return k("pay the %s" % what, ["When the %s comes due, I want to pay it on time, so I can %s." % (what, so),
                                    "When I am deciding which bills get paid first, I want the %s covered, so I can %s." % (what, so)], nar)


T = {}
# ------------------------------------------------------------------------------------------------ food
T["fast_food"] = k("buy a quick meal at {org}", ["When there is no time to cook between work and everything else, I want a quick hot meal, so I can keep the day moving.",
                                                "When everyone is hungry and we are still out, I want something cheap and fast, so I can get us fed without another stop.",
                                                "When my break is thirty minutes, I want food I can eat in the car, so I can be back on the clock on time."],
                   ["Drive-through order at {org}.", "Counter order at {org}, eaten in the car.", "Quick meal at {org} between stops.", "Lunch run to {org}."])
T["coffee"] = k("get a coffee at {org}", ["When the morning starts early, I want a coffee on the way, so I can be awake for work.",
                                         "When I have ten minutes between things, I want a small treat, so I can reset before the next one."],
                ["Coffee at {org}.", "Stopped at {org} on the way in.", "Coffee and a pastry at {org}."])
T["sit_down_restaurant"] = k("eat out at {org}", ["When we want a break from cooking midweek, I want a sit-down meal, so I can spend an hour with the people I came with.",
                                                 "When a friend is in town or there is something to mark, I want to eat out, so I can catch up without doing dishes."],
                             ["Meal at {org}, tip included.", "Table at {org}; the check includes the tip.", "Dinner out at {org}."])
T["fine_dining"] = k("have dinner at {org}", "When there is an anniversary or a client to host, I want a special dinner, so I can make the evening feel like an occasion.",
                     ["Dinner at {org} with wine and a tip.", "Reservation at {org}; tasting menu for the table."])
T["bar_tab"] = k("close out a tab at {org}", "When the shift is over and friends are meeting up, I want a couple of drinks, so I can unwind before going home.",
                 ["Tab closed at {org}.", "A couple of rounds at {org}."])
T["convenience_store"] = k("pick up a few things at {org}", ["When I need a drink, a snack or one missing item right now, I want the nearest counter, so I can keep going without a real shopping trip.",
                                                           "When the grocery store is too far for one thing, I want to grab it close to home, so I can skip the long trip."],
                           ["Snack and a drink at {org}.", "Quick stop at {org}.", "A few items from the cooler at {org}."])
T["tobacco"] = k("buy cigarettes at {org}", "When I am down to my last pack, I want to buy more on my usual stop, so I can get through the next couple of days.",
                 ["Pack bought at the counter at {org}.", "Cigarettes at {org}."])
T["lottery_ticket"] = k("buy lottery tickets at {org}", "When the jackpot is up or I have a few dollars in my pocket, I want to play my numbers, so I can have a small chance at something big.",
                        ["Scratch-offs and a draw ticket at {org}.", "Lottery tickets at {org} on the way out."])
T["dollar_store"] = k("shop at {org}", ["When money is tight and the big store is far, I want the basics in small sizes, so I can buy only what today's budget allows.",
                                       "When the house is out of soap, snacks and paper goods, I want one cheap stop, so I can cover them all."],
                      ["Household basics at {org}.", "Small-size groceries and cleaning supplies at {org}.", "A basket of basics at {org}."])
T["big_box_shopping"] = k("shop at {org}", ["When the household list gets long, I want one stop for everything, so I can save a trip and get the lower price.",
                                           "When the kids outgrow things and the pantry is low, I want to cover both in one cart, so I can be done for the week."],
                          ["Mixed cart at {org}: household goods and a few groceries.", "General shopping at {org}.", "One-stop trip to {org}."])
T["warehouse_club"] = k("buy in bulk at {org}", "When we have room to store it, I want to buy staples in bulk, so I can pay less per unit over the month.",
                        ["Bulk run at {org}.", "Cases of staples and paper goods at {org}."])
T["grocery_main_trip"] = k("buy the week's groceries at {org}", ["When the fridge is close to empty, I want to do the main grocery run, so I can feed my household for the week.",
                                                                "When the paycheck or benefits land, I want to stock up on staples, so I can stop making small expensive trips.",
                                                                "When I have a list and a budget, I want to get everything in one trip, so I can cook at home all week."],
                           ["Weekly shop at {org}.", "Full cart at {org}; watched the running total.", "Main grocery trip at {org}.", "Groceries for the week at {org}."])
T["grocery_fill_in"] = k("pick up a few groceries at {org}", ["When we run out of milk, bread or one dinner ingredient, I want a quick stop, so I can get through the next couple of days.",
                                                             "When dinner is missing one thing, I want to grab it on the way home, so I can cook what I planned."],
                         ["Top-up trip at {org}.", "A few things at {org} on the way home.", "Milk, bread and one or two extras at {org}."])
T["grocery_snap_purchase"] = k("buy groceries with SNAP at {org}", ["When my SNAP benefits are on the card, I want to buy the staples with them, so I can keep my cash for rent and bills.",
                                                                   "When the month's food money has to stretch, I want to use EBT for groceries, so I can make it to the next deposit."],
                               ["Paid with the EBT card at {org}; ${bal} left on it.", "SNAP purchase at {org}; balance after: ${bal}.", "Groceries on EBT at {org}."])
T["grocery_wic_purchase"] = k("pick up WIC foods at {org}", "When the WIC benefits are loaded, I want to pick up the approved items, so I can keep formula, milk and cereal in the house.",
                              ["WIC items rung up separately at {org}.", "WIC foods at {org}; matched each item to the approved list."])
T["wic_item_rejected_at_register"] = k("buy WIC foods at {org}", "When I am at the register with WIC foods, I want every item to scan as approved, so I can leave without holding up the line.",
                                       ["The register at {org} rejected {item}; it went back on the shelf.", "At {org}, {item} would not ring up as WIC-approved."])
T["grocery_item_out_of_stock"] = k("find {item} at {org}", "When I plan meals around one item, I want it to be on the shelf, so I can avoid a second trip.",
                                   ["{org} was out of {item}.", "No {item} on the shelf at {org}; settled for something else."])
T["snap_benefits_stolen"] = k("pay with SNAP at {org}", "When I swipe my EBT card, I want my benefits to be there, so I can feed my family this month.",
                              "The card showed a zero balance at {org}; the month's ${amt} had been drained by a skimmer.")
T["grocery_pickup_order"] = k("pick up an online grocery order at {org}", "When I can order groceries from my phone, I want them brought to the car, so I can skip an hour in the store.",
                              ["Curbside pickup at {org}.", "Online order loaded into the trunk at {org}."])
T["grocery_delivery_order"] = k("get groceries delivered", "When getting to the store is hard, I want groceries brought to the door, so I can spend the time on something else.",
                                ["Grocery delivery through {org}, tip included.", "App order through {org}; delivery, service fee and tip on top."])
T["farmers_market_purchase"] = k("buy produce at {org}", "When the midweek market is open, I want fresh produce from local growers, so I can cook something good this week.",
                                 ["Greens, eggs and bread at {org}.", "Produce from two stands at {org}."])
T["farmers_market_snap_tokens"] = k("use SNAP at {org}", "When the market takes EBT, I want to turn benefits into market tokens, so I can buy fresh produce.",
                                    "Swiped EBT for ${amt} in tokens at the market tent.")
T["farmers_market_match"] = k("get the market match", "When the market doubles SNAP dollars, I want the match, so I can take home twice the vegetables.",
                              "Market match added ${amt} in produce tokens.")
T["food_pantry_visit"] = k("pick up food at {org}", ["When the food budget runs out before the month does, I want a box from the pantry, so I can put dinner on the table this week.",
                                                    "When groceries cost more than I have, I want to use the Wednesday distribution, so I can keep what is left for rent."],
                           ["Box of groceries from {org} after a {wait}-minute line.", "Wednesday distribution at {org}; canned goods, produce and bread."])
T["restaurant_delivery_order"] = k("order delivery through {org}", ["When I am too tired to cook or go out, I want dinner brought to the door, so I can eat and rest.",
                                                                   "When the kids are asleep and I cannot leave, I want food delivered, so I can still have a meal."],
                                   ["Delivery from {rest} through {org}; ${tip} tip.", "Order from {rest} on {org}; fees and tip added to the food."])
T["workplace_cafeteria_or_vending"] = k("buy lunch at work", "When I did not pack a lunch, I want something from the cafeteria or the machines, so I can eat without leaving the building.",
                                        ["Cafeteria lunch at {org}.", "Vending machine snack at {org}.", "Sandwich from the break-room market at {org}."])
T["dining_hall_meal"] = k("eat in the dining hall", "When classes leave a gap, I want to use a meal swipe, so I can eat without spending cash.",
                          ["Meal swipe at the {org} dining hall.", "Dining hall meal on the semester plan."])
T["school_lunch"] = k("eat school lunch", ["When it is lunchtime at school, I want a hot meal, so I can get through afternoon classes.",
                                           "When my family counts on school for one meal a day, I want lunch in the cafeteria, so I can save food at home."],
                      ["Cafeteria lunch at {school} ({tier}).", "Lunch line at {school}; {tier} meal."])
T["school_breakfast"] = k("eat school breakfast", "When the bus gets in before the bell, I want breakfast at school, so I can start class fed.",
                          ["Breakfast at {school} ({tier}).", "Grab-and-go breakfast at {school}; {tier} meal."])
T["home_delivered_meal"] = k("receive a delivered meal", "When cooking and shopping are hard to manage, I want a meal brought to my door, so I can stay in my own home.",
                             ["Hot lunch delivered by a volunteer driver.", "Home-delivered meal and a quick check-in at the door."])
T["senior_center_meal"] = k("have lunch at the senior center", "When eating alone gets old, I want lunch with other people, so I can have a good meal and some company.",
                            ["Congregate lunch at the senior center.", "Lunch and a card game at the senior center."])
T["liquor_store"] = k("buy beer or wine at {org}", "When friends are coming over or the week has been long, I want to pick up something to drink, so I can relax at home.",
                      ["Six-pack and a bottle at {org}.", "Wine for the week at {org}."])
# ------------------------------------------------------------------------------------------------ shopping and discretionary
T["online_shopping_order"] = k("place an online order with {org}", ["When I need something the local stores do not carry, I want to order it online, so I can have it at the door in a few days.",
                                                                  "When it is cheaper online, I want to order from my phone, so I can skip the drive."],
                               ["Order placed with {org}.", "Checked out a cart on {org}.", "Online order through {org}; arrives later this week."])
T["app_or_game_purchase"] = k("buy something in an app", "When I am playing or streaming on my phone, I want the add-on, so I can keep going.",
                              ["In-app purchase through {org}.", "Small digital purchase on {org}."])
T["travel_booking"] = k("book a trip through {org}", "When the dates are finally set, I want to book before prices rise, so I can stop checking fares.",
                        ["Flights booked through {org}.", "Hotel and airfare booked through {org}."])
T["online_wagering_deposit"] = k("add money to a betting account", "When there is a game on tonight, I want money in my betting account, so I can place a wager.",
                                 "Deposit to {org}.")
T["event_tickets"] = k("buy event tickets", "When a show I want to see goes on sale, I want tickets before they are gone, so I can plan the night.",
                       "Tickets through {org}; service fees added at checkout.")
T["clothing"] = k("buy clothes at {org}", ["When work clothes wear out or the kids outgrow theirs, I want replacements, so I can have what the week requires.",
                                         "When the season changes, I want a few new pieces, so I can stop making do."],
                  ["Clothes at {org}.", "Shoes and a few shirts at {org}."])
T["thrift_store"] = k("shop secondhand at {org}", "When we need clothes or housewares for less, I want to check the thrift racks, so I can stretch what I have.",
                      ["Secondhand finds at {org}.", "A coat and some kitchen things at {org}."])
T["electronics"] = k("buy electronics at {org}", "When a phone, charger or TV gives out, I want a replacement, so I can get back to normal.",
                     ["Replacement device at {org}.", "Electronics purchase at {org}."])
T["home_improvement"] = k("buy supplies at {org}", ["When something at home needs fixing, I want the parts and tools, so I can do the repair myself.",
                                                  "When a weekend project is planned, I want the materials on hand, so I can start on time."],
                          ["Hardware and repair supplies at {org}.", "Parts for a home repair at {org}."])
T["furniture"] = k("buy furniture at {org}", "When a bed or couch has to be replaced, I want something that will last, so I can stop patching the old one.",
                   "Furniture ordered at {org}; delivery next week.")
T["haircut"] = k("get a haircut at {org}", "When I am overdue for a cut, I want an hour in the chair, so I can look right for work.",
                 ["Cut at {org}, tip included.", "Haircut and tip at {org}."])
T["nail_salon"] = k("get nails done at {org}", "When I have an event or just need a break, I want my nails done, so I can feel put together.",
                    "Manicure at {org}, tip included.")
T["entertainment"] = k("go out to {org}", "When there is a free evening, I want to do something fun, so I can spend time with family or friends.",
                       ["Tickets and snacks at {org}.", "Evening out at {org}."])
T["hobby_and_gifts"] = k("shop at {org}", "When a hobby needs supplies or a birthday is coming, I want to pick something out in person, so I can get exactly the right thing.",
                         ["Purchase at {org}.", "Picked out a gift at {org}."])
T["pet_supplies"] = k("buy pet food at {org}", "When the pet food runs low, I want to restock, so I can keep our animals fed.",
                      ["Pet food and litter at {org}.", "Bag of feed at {org}."])
T["vet_visit"] = k("take the pet to {org}", "When our pet is sick or due for shots, I want it seen, so I can keep it healthy.",
                   ["Exam and vaccines at {org}.", "Vet visit at {org}."])
T["car_wash"] = k("wash the car at {org}", "When the car is covered in road salt and pollen, I want it washed, so I can protect the paint.", "Wash at {org}.")
T["auto_parts"] = k("buy car parts at {org}", "When the car needs a part I can put in myself, I want to buy it over the counter, so I can skip the shop's labor charge.",
                    ["Battery and wiper blades at {org}.", "Parts for a driveway repair at {org}."])
T["over_the_counter_medicine"] = k("buy medicine at {org}", "When someone at home has a cold or a headache, I want something from the shelf, so I can treat it without a doctor visit.",
                                   ["Cold medicine and pain reliever at {org}.", "Over-the-counter medicine at {org}."])
T["dry_cleaning"] = k("pick up dry cleaning at {org}", "When work clothes need pressing, I want them cleaned, so I can look sharp this week.", "Dry cleaning picked up at {org}.")
T["gift_for_family"] = k("buy a gift at {org}", "When a birthday or a new baby is coming up, I want to buy a gift, so I can show up with something.",
                         ["Gift bought at {org}.", "Card and a present at {org}."])
T["jewelry_purchase"] = k("buy jewelry at {org}", "When there is an engagement or an anniversary, I want a piece that marks it, so I can give something lasting.",
                          "Jewelry purchase at {org}.")
T["designer_handbag"] = k("buy a handbag at {org}", "When I have wanted one particular bag for a while, I want to buy it in person, so I can enjoy it.",
                          "Designer bag at {org}.")
T["golf_round"] = k("play a round at {org}", "When the weather breaks, I want a round with my usual group, so I can get outside.", "Greens fee and cart at {org}.")
T["store_return"] = k("return a purchase at {org}", "When something does not fit or does not work, I want my money back, so I can put it toward what I need.",
                      ["Returned an item at {org}; ${amt} back.", "Refund of ${amt} at the service desk at {org}."])
T["online_order_return_dropoff"] = k("send back an online order", "When an online order is wrong, I want to drop it off for return, so I can get refunded.",
                                     "Dropped a return at {org}; the ${amt} refund is pending.")
T["postage_and_shipping"] = k("mail a package at {org}", "When I have a package or forms to send, I want them mailed with tracking, so I can know they arrived.",
                              ["Package shipped at {org}.", "Stamps and one certified letter at {org}."])
T["streaming_subscription"] = k("pay for {org}", ["When the monthly charge comes around, I want the service to stay on, so I can keep watching what we follow.",
                                                 "When it renews on its own, I want to notice the charge, so I can decide whether it is still worth it."],
                                ["{org} monthly charge.", "{org} renewed on the card on file."])
T["other_subscription"] = k("pay a subscription to {org}", "When a subscription renews, I want it to go through quietly, so I can keep using it.",
                            ["Subscription renewal with {org}.", "Monthly charge from {org}."])
T["gym_membership"] = k("pay the gym membership", "When the gym draft comes out, I want to keep the membership, so I can work out when I get the chance.",
                        ["Monthly dues to {org}.", "{org} membership draft."])
T["pet_insurance"] = bill("pet insurance premium", "avoid a surprise vet bill")
T["boat_payment"] = bill("boat loan payment", "keep the boat for summer weekends")
T["country_club_bill"] = k("pay the club statement", "When the club statement arrives, I want it settled, so I can keep the membership in good standing.",
                           "Monthly dues and dining minimum at {org}.")
T["investment_contribution"] = k("move money into investments", "When the automatic transfer runs, I want it going into the account, so I can build savings for later.",
                                 ["Automatic contribution to {org}.", "Monthly transfer into the brokerage account."])
T["college_savings_contribution"] = k("add to college savings", "When the monthly transfer runs, I want it in the college fund, so I can cover part of tuition later.",
                                      "Automatic deposit to the {org}.")
T["retirement_contribution_payroll"] = k("save for retirement from pay", "When I get paid, I want a share set aside before I see it, so I can retire someday.",
                                         ["Retirement plan deferral from this paycheck.", "401(k) contribution taken out of pay."])
T["jail_commissary_purchase"] = k("buy from the commissary", "When money is on my account, I want soap, snacks and stamps, so I can get by inside.", "Commissary order at {org}.")
# ------------------------------------------------------------------------------------------------ transportation
T["gas_fill_up"] = k("buy gas at {org}", ["When the tank is near empty, I want to fill up, so I can get to work the rest of the week.",
                                        "When I only have a few dollars until payday, I want enough gas for the next trips, so I can keep driving.",
                                        "When I pass the cheapest station, I want to top off, so I can avoid paying more later."],
                     ["{gal} gallons at {org}, ${price} a gallon.", "Gas at {org}: {gal} gallons at ${price}.", "Filled up at {org}."])
T["ev_public_charging"] = k("charge the car", "When the battery is low away from home, I want a fast charge, so I can finish the day's driving.", "Fast-charging session at {org}.")
T["transit_ride"] = k("ride the bus", ["When I do not have a car for the trip, I want the bus to get me there, so I can keep my job and my appointments.",
                                       "When parking costs more than the fare, I want to ride transit, so I can save the money.",
                                       "When the bus is how I get around, I want it to come when the schedule says, so I can plan my day."],
                      ["Bus ride for {purpose}; fare ${fare}.", "Rode the bus for {purpose}.", "Took the bus for {purpose}; ${fare} at the farebox."])
T["missed_bus"] = k("catch the bus", "When I am timing my day to the bus schedule, I want it to show up, so I can arrive on time.",
                    ["The bus never came; waited {wait} minutes for the next one.", "Watched the bus pull away and stood {wait} minutes for another."])
T["paratransit_ride"] = k("ride paratransit", "When I cannot drive or use a regular bus, I want a door-to-door ride, so I can get to treatment.", "Shared paratransit van to {org}.")
T["transit_pass_purchase"] = k("buy a monthly bus pass", "When a new month starts, I want a pass, so I can ride without counting fares.", "Monthly pass loaded in the transit app.")
T["parking_fee"] = k("pay for parking", "When I drive downtown, I want a legal place to leave the car, so I can avoid a ticket.",
                     ["Garage parking near work.", "Paid the meter by app.", "Parking at {where}."])
T["ride_hail_trip"] = k("book a ride", ["When there is no bus and no car, I want a ride I can book now, so I can get where I need to be.",
                                        "When I have been out and should not drive, I want a ride home, so I can get there safely."],
                        ["Ride booked through {org}.", "App ride across town with {org}."])
T["toll"] = k("pay the toll", "When the toll road saves twenty minutes, I want to use it, so I can make it to work on time.", ["Toll charged to the transponder.", "Toll on the commute."])
T["toll_account_reload"] = k("refill the toll account", "When the transponder balance runs low, I want it refilled automatically, so I can avoid pay-by-plate fees.", "Automatic $25 reload of the toll account.")
T["car_repair"] = k("get the car repaired at {org}", "When the car starts making a noise I cannot ignore, I want it fixed, so I can keep getting to work.",
                    ["Repair at {org}; estimate was ${est}.", "Shop visit at {org}."])
T["repair_estimate_too_high"] = k("get a repair estimate", "When the shop tells me what the repair costs, I want a price I can pay, so I can drive away fixed.",
                                  ["The estimate at {org} came to ${amt}; paid for the diagnosis only and drove home.", "Could not cover the ${amt} estimate at {org}; the repair waits."])
T["oil_change"] = k("get an oil change at {org}", "When the sticker says the oil is overdue, I want it changed, so I can avoid a bigger repair.", "Oil change at {org}.")
T["tires"] = k("buy tires at {org}", "When the tread is gone, I want tires I can afford, so I can pass inspection and drive safely in rain.",
               ["Tires mounted at {org}.", "Two tires at {org}."])
T["vehicle_registration_renewal"] = k("renew the car registration", "When the tag is about to expire, I want it renewed, so I can avoid a ticket.",
                                      ["Tag renewed with the county.", "Registration renewal and new decal."])
T["car_wont_start"] = k("start the car", "When I turn the key in the morning, I want the car to start, so I can get to where I am expected.",
                        ["The car would not start: {why}.", "Morning plans stopped by {why}."])
T["jump_start_from_neighbor"] = k("get the car running", "When the car is dead in the driveway, I want a jump from someone nearby, so I can still make it in.", "A neighbor brought over jumper cables.")
T["tow_and_roadside_repair"] = k("get a tow and a repair from {org}", "When the car will not move, I want a tow and a fix today, so I can drive tomorrow.", "Tow and repair by {org} after {why}.")
T["ride_search"] = k("find a ride to {where}", "When I have no car and no bus, I want someone to drive me, so I can get to {where}.",
                     ["Called around for a ride to {where}; {got} came through.", "Lined up a ride to {where} with {got}."])
T["bike_repair"] = k("fix the bike at {org}", "When my bike is how I get to work, I want it fixed fast, so I can ride tomorrow.", "Tube and brake pads at {org}.")
T["car_payment"] = bill("car payment", "keep the car I need for work")
T["bhph_car_payment"] = k("make the weekly car payment at {org}", "When the weekly payment is due at the lot, I want to pay in person, so I can keep them from disabling the car.",
                          ["Weekly payment handed over at {org}.", "Paid the lot in person at {org}."])
T["auto_insurance"] = bill("car insurance", "stay legal on the road")
T["used_car_private_sale"] = k("buy a used car", "When the old car is finished and the refund is in hand, I want to buy one outright, so I can get to work without a loan.",
                               "Cash for a used sedan from a private seller; ${amt}.")
T["used_car_buy_here_pay_here"] = k("buy a car at {org}", "When my credit rules out a bank loan, I want a car I can drive off today, so I can keep my job.",
                                    "Signed at {org}: ${down} down, {apr}% interest, ${wk} a week.")
T["used_car_dealer_purchase"] = k("buy a used car at {org}", "When repairs cost more than the car is worth, I want a newer used one, so I can stop missing work.",
                                  "Used car at {org}: ${down} down, the rest financed at {apr}% for {term} months.")
T["new_car_purchase"] = k("buy a new car at {org}", "When the lease is ending, I want a new car with a warranty, so I can stop thinking about repairs.",
                          "New car at {org}: ${down} down, financed at {apr}% for {term} months.")
# ------------------------------------------------------------------------------------------------ housing and utilities
T["rent"] = k("pay the rent", ["When rent is due, I want it paid in full, so I can keep my home.",
                               "When the grace period is about to end, I want the rent in before the late fee, so I can keep that money for food.",
                               "When my check lands after the first, I want to pay rent the same day, so I can stay on good terms with the landlord."],
              ["Rent to {org}.", "This month's rent paid to {org}.", "Rent for the month to {org}."])
T["lot_rent"] = bill("lot rent", "keep my home on the lot")
T["roommate_rent_share"] = k("send my share of the rent", "When rent is due, I want to send my share to the roommate who pays it, so I can do my part.",
                             ["Sent ${amt} for my share of the rent.", "Rent share handed to the leaseholder."])
T["mortgage"] = k("pay the mortgage", ["When the mortgage draft comes out, I want the money there, so I can keep the house.",
                                       "When the first of the month passes, I want the mortgage paid before the grace period ends, so I can avoid a late charge."],
                  ["Mortgage payment to {org}.", "Monthly principal and interest to {org}."])
T["property_tax_escrow"] = k("fund the escrow account", "When I pay the mortgage, I want the tax and insurance share set aside, so I can avoid a big bill later.",
                             "Escrow share of the house payment: about ${amt} toward county property tax.")
T["property_tax_payment"] = k("pay the property tax", "When the county tax bill is due, I want it paid, so I can keep the house clear of liens.", "Property tax installment to the county.")
T["hoa_dues"] = bill("homeowner association dues", "avoid a lien from the association")
T["renters_insurance"] = bill("renters insurance", "be covered if there is a fire or a break-in")
T["home_insurance"] = bill("homeowners insurance", "keep the house covered")
T["storage_unit"] = bill("storage unit rent", "keep my things from being auctioned")
T["security_system"] = bill("alarm monitoring", "keep the house watched")
T["cleaning_service"] = k("pay the house cleaner", "When the cleaner finishes, I want to pay right away, so I can keep a good worker coming back.", "Paid the house cleaner.")
T["assisted_living_fee"] = bill("assisted living fee", "stay where I get help every day")
T["laundromat"] = k("do laundry at {org}", ["When there is no washer at home, I want two hours at the laundromat, so I can have clean clothes for work and school.",
                                           "When the hamper is overflowing, I want to run every load at once, so I can be done for the week."],
                    ["Washers and dryers at {org}.", "Three loads at {org}, paid in quarters."])
T["home_repair_service"] = k("get {job} done", "When something breaks at home that I cannot fix, I want a contractor to come, so I can stop worrying about it.",
                             ["{org} came out for {job}.", "{job} by {org}."])
T["lawn_or_yard_service"] = k("pay for yard work", "When the yard gets ahead of me, I want someone to handle it, so I can keep the place up.", "Paid the yard crew.")
T["moving_truck_rental"] = k("rent a moving truck at {org}", "When the lease ends and the new place is ready, I want a truck for the day, so I can move everything in one trip.", "Truck rental at {org}.")
T["move_in_deposit_and_first_rent"] = k("pay the deposit and first month", "When I am approved for a new place, I want the deposit and first month paid, so I can get the keys.",
                                        "Deposit of ${dep} plus first month to {org}.")
T["rental_application_fee"] = k("apply for an apartment", "When I find a place I can afford, I want to apply before it is gone, so I can have a chance at it.",
                                "Application and screening fee to {org}; not refundable.")
T["repair_request_to_landlord"] = k("report a repair to {org}", "When something in the apartment breaks, I want the landlord to send someone, so I can live there safely.",
                                    ["Reported {issue} to {org}.", "Left a message with {org} about {issue}."])
T["eviction_notice_received"] = k("deal with an eviction notice", "When a court notice is taped to my door, I want to know my options, so I can keep my home.",
                                  "Notice filed by {org} for ${amt} in back rent; {days} days to answer.")
T["eviction_hearing"] = k("appear at the eviction hearing", "When my case is called, I want to be in the room, so I can ask for time to pay.",
                          "Hearing at {org}: {reason}.")
T["shelter_night"] = k("get a bed for the night", "When I have nowhere else to sleep, I want a bed and a meal, so I can be safe tonight.",
                       ["Checked in at {org} for the night.", "Bed, dinner and a shower at {org}."])
T["housing_case_management_meeting"] = k("meet with a housing case manager", "When I am working toward my own place, I want help with the applications, so I can get on a housing list.",
                                         ["Met a case manager at {org} about housing applications.", "Worked on ID and housing paperwork at {org}."])
T["electric_bill"] = k("pay the electric bill", ["When the power bill comes due, I want it paid, so I can keep the lights and heat on.",
                                                "When the bill is higher than last month, I want to cover it anyway, so I can stay off the shutoff list."],
                       ["Electric bill to {org}.", "Power bill paid to {org}."])
T["gas_bill"] = k("pay the gas bill", "When the heating bill arrives, I want it paid, so I can keep the furnace running through March.", ["Gas bill to {org}.", "Heating bill paid to {org}."])
T["water_bill"] = bill("water and sewer bill", "keep the water on")
T["trash_bill"] = bill("trash pickup bill", "keep the cans getting emptied")
T["propane_budget_plan"] = bill("propane budget payment", "have a full tank for heat")
T["internet_bill"] = k("pay the internet bill", ["When the internet bill is due, I want it paid, so I can keep the kids' homework and my work online.",
                                                "When the promotional price ends, I want to keep service anyway, so I can stay connected."],
                       ["Internet bill to {org}.", "Home internet paid to {org}."])
T["phone_bill"] = k("pay the phone bill", ["When the phone bill is due, I want it paid, so I can keep the one number everyone has for me.",
                                          "When my plan is about to run out, I want another month, so I can stay reachable for work."],
                    ["Phone service paid to {org}.", "Another month of service with {org}."])
T["prepaid_phone_top_up"] = k("add minutes to the phone", "When the prepaid plan runs dry mid-month, I want a top-up card, so I can take calls about work.", "Top-up card bought at {org}.")
T["shutoff_notice_received"] = k("deal with a shutoff notice", "When a shutoff notice comes in the mail, I want to find the money or a payment plan, so I can keep the {what} on.",
                                 "{org} notice: ${amt} past due on the {what} account, disconnection in {days} days.")
T["service_disconnected_for_nonpayment"] = k("keep the {what} on", "When I wake up to no {what}, I want service back the same day, so I can cook and stay warm.",
                                             "{org} disconnected the {what}.")
T["reconnection_payment"] = k("get the {what} turned back on", "When service has been cut, I want to pay what it takes, so I can have the {what} back tonight.",
                              "Paid {org} by phone to restore the {what}.")
T["sought_emergency_utility_help"] = k("ask {org} for emergency help", "When I cannot pay to get service back, I want an agency to pledge the difference, so I can get reconnected.",
                                       "Called {org} about emergency help with the {what} bill.")
T["utility_connection_deposit"] = k("put down a utility deposit", "When I open an account at a new address, I want the deposit paid, so I can have power on move-in day.",
                                    "Deposit to {org} to start service.")
T["energy_assistance_application"] = k("apply for energy assistance at {org}", "When the heating bills pile up, I want to apply for help, so I can keep the heat on.",
                                       "Energy assistance application at {org}.")
T["energy_assistance_pledge"] = k("receive an energy assistance pledge", "When my application is approved, I want the pledge sent to the utility, so I can stop the shutoff.",
                                  "Pledge of ${amt} sent to {org} on the household's behalf.")
T["utility_billing_phone_call"] = k("sort out {matter} with {org} by phone", "When the bill does not look right, I want a person on the phone, so I can get it corrected.",
                                    "Call to {org} about {matter}.")
T["jail_phone_call"] = k("call home", "When I get phone time, I want to call my family, so I can hear how the kids are.", "{mins}-minute call through {org}.")
T["power_outage"] = k("keep the power on", "When the power goes out, I want it back before the food spoils, so I can keep the house running.", "Power was out for about {hrs} hours.")
# ------------------------------------------------------------------------------------------------ health
T["doctor_visit"] = k("see the doctor at {org}", ["When something has been bothering {who} for a while, I want it checked, so I can know what it is.",
                                                "When a checkup or a refill visit is due, I want to get it done, so I can keep prescriptions current."],
                      ["Office visit for {who} at {org}.", "Primary care visit at {org}."])
T["community_health_center_visit"] = k("be seen at {org}", "When I have no regular doctor, I want a clinic that charges by income, so I can be seen anyway.",
                                       ["Sliding-fee visit for {who} at {org}.", "Clinic visit at {org}."])
T["va_clinic_visit"] = k("be seen at {org}", "When I am due at the VA, I want my appointment, so I can keep my care in one place.", "Appointment at {org}.")
T["specialist_visit"] = k("see a specialist at {org}", "When my doctor refers me on, I want the specialist's opinion, so I can decide what to do next.",
                          ["Specialist appointment for {who} at {org}.", "Follow-up with a specialist at {org}."])
T["lab_or_imaging"] = k("get tests done at {org}", "When the doctor orders labs or a scan, I want them done, so I can get answers.", ["Bloodwork and imaging at {org}.", "Ordered tests at {org}."])
T["telehealth_visit"] = k("have a video visit with {org}", "When it is hard to get to the office, I want to see the doctor by video, so I can skip the trip.", "Video visit with {org}.")
T["urgent_care_visit"] = k("be seen at {org}", "When it cannot wait for an appointment but is not the emergency room, I want a walk-in clinic, so I can be treated today.",
                           "Walk-in visit for {who} at {org}.")
T["emergency_department_visit"] = k("be treated in the emergency department", "When it is serious or after hours, I want the emergency room, so I can be treated right away.",
                                    "{hrs} hours in the emergency department at {org} for {who}.")
T["emergency_visit_uncompensated"] = k("be treated in the emergency department", "When I am sick and uninsured, I want the one door that cannot turn me away, so I can be treated.",
                                       "{hrs} hours in the emergency department at {org}; no insurance on file.")
T["ems_ambulance_transport"] = k("get to the hospital by ambulance", "When it is an emergency, I want an ambulance, so I can get to the hospital alive.", "Ambulance to {org} for {who}.")
T["ems_response_no_transport"] = k("get help from paramedics", "When something goes wrong at home, I want paramedics to check, so I can know whether it is serious.", "Paramedics responded: {why}.")
T["hospital_admission"] = k("be admitted to {org}", "When the doctors say I need to stay, I want a bed, so I can get the treatment I need.", "Admitted to {org} {via}.")
T["hospital_admission_uncompensated"] = k("be admitted to {org}", "When I need a hospital bed and have no insurance, I want to be treated, so I can recover.",
                                          "Admitted to {org} {via}; financial counselor to follow.")
T["childbirth_hospital_stay"] = k("give birth at {org}", "When labor starts, I want to be at the hospital, so I can deliver safely.", "Admitted to labor and delivery at {org}.")
T["hospice_care_day"] = k("receive hospice care", "When treatment is over, I want comfort and my family near, so I can be at peace.", "Hospice nurse visit from {org}.")
T["prescription_pickup"] = k("pick up a prescription at {org}", ["When my refill is ready, I want to pick it up, so I can keep taking it without a gap.",
                                                               "When the doctor calls in something new, I want it filled today, so I can start treatment."],
                             ["{brand} prescription at {org}: cash price ${cash}, copay ${cp}.", "Picked up a {brand} refill at {org}; copay ${cp}.", "Filled {who} prescription at {org}."])
T["prescription_mail_order"] = k("get a mail-order refill", "When I take the same medicine every day, I want ninety days mailed, so I can skip the pharmacy line.",
                                 "{brand} refill shipped by {org}; copay ${cp}.")
T["dental_visit"] = k("go to the dentist at {org}", "When a cleaning is due or a tooth hurts, I want to be seen, so I can stop it from getting worse.",
                      ["Dental visit for {who} at {org}: {svc}.", "{svc} at {org}."])
T["vision_exam_and_glasses"] = k("get an eye exam at {org}", "When my glasses stop working, I want an exam and new lenses, so I can see to drive and read.", "Eye exam and glasses at {org}.")
T["therapy_session"] = k("see a therapist at {org}", "When my weekly session comes around, I want to keep it, so I can stay steady.", "Counseling session with {org}.")
T["therapy_session_self_pay"] = k("see a therapist at {org}", "When my therapist does not take insurance, I want to keep going anyway, so I can stay well.", "Self-pay counseling session with {org}.")
T["physical_therapy_visit"] = k("go to physical therapy at {org}", "When I am recovering from an injury, I want my therapy sessions, so I can get back to work.", "Physical therapy session at {org}.")
T["dialysis_treatment"] = k("get dialysis at {org}", "When it is my treatment day, I want my four hours in the chair, so I can stay alive.", "Dialysis session at {org}.")
T["personal_care_aide_visit"] = k("have my aide come", "When I need help bathing and dressing, I want my aide to come, so I can stay in my own home.", "{hrs}-hour visit from an aide with {org}.")
T["home_health_nurse_visit"] = k("have the nurse visit", "When I am just home from the hospital, I want the nurse to check on me, so I can avoid going back.", "Nurse visit from {org}.")
T["nursing_home_day"] = k("live in the nursing home", "When I need care around the clock, I want a bed and staff, so I can be looked after.", "Resident day at {org}.")
T["skilled_nursing_rehab_day"] = k("do rehab at {org}", "When I am recovering after surgery, I want daily therapy, so I can go home.", "Rehab day at {org}.")
T["group_home_residential_services"] = k("live in the group home", "When I need support each day, I want staff I know, so I can live in the community.", "Residential support day.")
T["residential_treatment_day"] = k("stay in treatment", "When I am working on recovery, I want a full day of the program, so I can stay on track.", "Day of residential treatment.")
T["nursing_home_patient_liability"] = k("pay my share to the nursing home", "When my Social Security arrives, I want my share sent to the home, so I can keep my bed and my ${keep} allowance.",
                                        "Patient share to {org}; ${keep} kept for personal needs.")
T["nursing_home_private_pay"] = bill("nursing home bill", "keep my room")
T["health_premium"] = k("pay the health insurance premium", "When the premium is due, I want it paid, so I can keep my coverage.", ["Monthly premium to {org}.", "Health plan premium to {org}."])
T["health_premium_payroll"] = k("pay for health insurance from my check", "When I get paid, I want my share of the premium taken out, so I can keep my family covered.",
                                ["Health premium deducted from pay.", "Employee share of the health plan, taken from this check."])
T["medigap_premium"] = bill("Medicare supplement premium", "avoid the twenty percent Medicare leaves")
T["medicare_part_b_premium"] = k("pay the Medicare premium", "When my Social Security is deposited, I want the Medicare premium taken out first, so I can keep my doctor coverage.",
                                 ["Part B premium withheld: ${gross} gross became ${net}.", "Medicare Part B premium deducted from Social Security."])
T["medicare_drug_plan_premium"] = k("pay the drug plan premium", "When my benefit is deposited, I want the drug plan premium withheld, so I can keep prescription coverage.", "Part D premium withheld from Social Security.")
T["medicare_part_b_state_buy_in"] = k("have the state pay my Medicare premium", "When my income is too low for the premium, I want the state to pay it, so I can keep my whole check.",
                                      "State Medicaid paid the ${amt} Part B premium.")
T["medical_payment_plan"] = bill("medical bill installment", "keep the account out of collections")
T["appointment_rescheduled_no_free_time"] = k("fit in an appointment", "When the clinic is only open during my shift, I want an appointment I can get to, so I can be seen without losing pay.",
                                              "Called {org} to move the appointment; nothing fit around work.")
T["appointment_scheduling_call"] = k("book an appointment with {org}", "When I need to be seen, I want the first open slot, so I can stop waiting.", "Booked with {org}; first opening is {weeks} weeks out.")
T["insurance_phone_call"] = k("sort out {matter} with the insurer", "When the insurance does not do what I expected, I want a person to explain it, so I can get the bill fixed.",
                              "Call about {matter}.")
T["public_health_clinic_visit"] = k("be seen at {org}", "When I need shots or a test and money is short, I want the health department clinic, so I can get it done for little or nothing.",
                                    "{svc} at {org}.")
T["wic_clinic_appointment"] = k("keep the WIC appointment", "When my WIC certification is due, I want to keep the appointment, so I can stay on the program.", "Weigh-in and nutrition visit at {org}.")
# ------------------------------------------------------------------------------------------------ income and benefits
T["paycheck_direct_deposit"] = k("get paid", ["When payday comes, I want my check in my account, so I can pay what is due.",
                                             "When I have been watching the balance all week, I want my pay to land, so I can stop juggling."],
                                 ["{cadence} pay from {org}: ${gross} gross, ${net} after deductions.", "Direct deposit from {org}; ${net} net.", "Pay as a {occ} at {org}."])
T["paycheck_paycard"] = k("get paid on the paycard", "When payday comes and I have no bank account, I want my pay on the card, so I can spend it today.",
                          "{cadence} pay from {org} loaded to a paycard: ${net} net.")
T["paycheck_paper_check"] = k("get my paycheck", "When the boss hands out checks, I want mine, so I can cash it before the weekend.", "Paper check from {org}: ${net} net.")
T["payroll_income_tax_withholding"] = k("have income tax withheld", "When I get paid, I want the tax taken out as I go, so I can avoid owing in April.",
                                        ["Federal ${fed} and state ${st} withheld.", "Income tax withholding on this check."])
T["payroll_fica"] = k("pay Social Security and Medicare tax", "When I get paid, I want my payroll taxes credited, so I can count on benefits later.",
                      ["Social Security and Medicare tax, 7.65% of gross.", "Payroll tax on this check."])
T["union_dues"] = k("pay union dues", "When I get paid, I want my dues sent, so I can keep the contract's protection.", "Union dues deducted from pay.")
T["wage_garnishment"] = k("have wages garnished", "When a court order sits on my paycheck, I want to know what is left, so I can plan the two weeks.", "Court-ordered garnishment taken from this check.")
T["cash_tips"] = k("take home tips", "When the shift ends, I want my tips counted out, so I can buy gas and groceries tonight.", ["Cash tips from the shift at {org}.", "Tips as a {occ}."])
T["gig_payout_instant"] = k("cash out today's earnings", "When I finish driving, I want today's earnings now, so I can fill the tank for tomorrow.", "Instant cash-out of the day's app earnings.")
T["gig_payout_weekly"] = k("get the weekly gig payout", "When the week's trips are totaled, I want the deposit, so I can cover my bills.", "Weekly payout for app-based driving and delivery work.")
T["self_employment_receipts"] = k("get paid by customers", ["When a job is finished, I want to be paid the same day, so I can cover materials and my own bills.",
                                                          "When I work for myself, I want money coming in most days, so I can keep the business going."],
                                  ["Customer payments for work as a {occ}.", "Day's receipts as a {occ}."])
T["social_security_deposit"] = k("receive Social Security", ["When my payment date arrives, I want the deposit there in the morning, so I can pay rent and fill prescriptions.",
                                                            "When I live on one check a month, I want it to arrive on schedule, so I can plan every dollar."],
                                 ["Monthly {kind} benefit: ${gross} gross, ${net} deposited.", "Social Security deposit of ${net}."])
T["ssi_deposit"] = k("receive SSI", "When the first of the month comes, I want my SSI, so I can pay rent.", "Monthly SSI payment.")
T["pension_payment"] = k("receive my pension", "When the pension is paid, I want it in my account, so I can cover the month.", "Pension deposit; ${net} after withholding.")
T["va_compensation_deposit"] = k("receive VA compensation", "When the VA pays, I want the deposit, so I can cover my bills.", "Monthly VA disability compensation.")
T["unemployment_benefit"] = k("receive unemployment", "When I am out of work, I want my weekly benefit, so I can cover basics while I look.", "Weekly unemployment payment.")
T["snap_issuance"] = k("receive SNAP benefits", "When my issuance day comes, I want the benefits on the card, so I can do the month's big shop.", "Monthly SNAP loaded for a household of {n}.")
T["wic_benefit_load"] = k("receive WIC benefits", "When the new month of WIC starts, I want the foods loaded, so I can pick up formula and milk.", "Month of WIC foods loaded.")
T["tanf_cash_issuance"] = k("receive cash assistance", "When my assistance is issued, I want it on the card, so I can pay for what food benefits do not cover.", "Monthly cash assistance issued to the EBT card.")
T["child_support_received"] = k("receive child support", "When the other parent's payment clears the state, I want it deposited, so I can cover the kids' costs.", "Child support passed through the state unit.")
T["federal_tax_refund"] = k("receive my tax refund", ["When the refund finally arrives, I want it in my account, so I can catch up on what has been waiting.",
                                                    "When I filed in January, I want the refund I have been tracking, so I can pay down bills."],
                            ["Federal refund of ${refund} by {via}.", "Refund deposited: ${amt} in all."])
T["refundable_tax_credit"] = k("receive my tax credits", "When I work and raise kids on a small income, I want the credits I qualify for, so I can get ahead for a month or two.",
                               "Earned Income and Child Tax Credit portion of the refund: ${credit}.")
T["state_tax_refund"] = k("receive the state refund", "When the state return is processed, I want the refund, so I can put it toward bills.", "State income tax refund.")
T["juror_pay"] = k("get paid for jury service", "When I give the court my day, I want the juror payment, so I can at least cover parking.", "Juror check for the day: $30.")
T["plasma_donation_payment"] = k("get paid for donating plasma", "When I need cash before payday, I want to donate plasma, so I can cover gas and groceries.", "Donation at {org}; ${amt} loaded to the center's card.")
T["sold_item_to_pawn_shop"] = k("sell something for cash", "When I need money today, I want to sell something I own, so I can cover a bill.", "Sold {item} at {org} for ${amt}.")
T["remittance_received"] = k("receive money from family", "When family abroad sends help, I want to pick it up, so I can use it here.", "Transfer received from family abroad.")
# ------------------------------------------------------------------------------------------------ children and education
T["public_school_day"] = k("go to school", ["When it is a school day, I want to be in class, so I can learn and see my friends.",
                                            "When my parents are at work, I want a safe place to spend the day, so I can learn while they earn."],
                           ["A day of {grade} at {school}.", "School day at {school}, {grade}.", "In class at {school} ({grade})."])
T["head_start_day"] = k("go to Head Start", "When my parents are working or looking for work, I want a classroom and two meals, so I can be ready for kindergarten.", "Day at {org}.")
T["public_prek_day"] = k("go to pre-K", "When I am four, I want a classroom of my own, so I can be ready for kindergarten.", "State pre-K day.")
T["after_school_club_day"] = k("go to the after-school club", "When school lets out before my mom's shift ends, I want somewhere to go, so I can do homework and play.", "Afternoon at {org}.")
T["school_meal_account_reload"] = k("add money to the lunch account", "When the lunch balance runs low, I want to reload it, so I can keep my child from being told there is no money.",
                                    "Reloaded the school meal account through {org}.")
T["field_trip_fee"] = k("pay for the field trip", "When the permission slip comes home, I want the fee paid, so I can keep my child from being left behind.", "Field trip fee for the class outing.")
T["school_activity_fee"] = k("pay a school activity fee", "When the team or the yearbook costs extra, I want it paid, so I can let my teenager take part.", "Activity fee paid through {org}.")
T["youth_sports_registration"] = k("sign my child up for spring sports", "When spring sign-ups open, I want a spot on a team, so I can give my child something to look forward to.",
                                   "Spring season registration with {org}.")
T["school_supplies"] = k("buy school supplies at {org}", "When the teacher's list comes home, I want the supplies, so I can send my child prepared.", "Poster board, pencils and a folder at {org}.")
T["college_textbooks"] = k("buy textbooks", "When the syllabus lists a book I must have, I want it ordered, so I can keep up in class.", "Textbook order from {org}.")
T["child_care_payment"] = k("pay for child care", ["When the week's child care is due, I want it paid, so I can keep my spot and keep working.",
                                                  "When child care costs as much as rent, I want the bill covered, so I can stay employed."],
                            ["Child care tuition to {org}.", "Week of care paid to {org}."])
T["after_school_fee"] = bill("after-school program fee", "work until five without worrying")
T["private_school_tuition"] = bill("tuition installment", "keep my child enrolled")
T["college_payment_plan"] = bill("college payment plan installment", "stay registered for the term")
T["lessons_tuition"] = bill("lesson tuition", "keep my child in the class")
T["student_loan_payment"] = k("pay the student loan", "When the loan payment is due, I want it made, so I can stay out of default.", ["Monthly payment to {org}.", "Student loan draft to {org}."])
T["school_dropoff"] = k("drop the kids at school", "When the bell is about to ring, I want the kids at the door, so I can get to work.",
                        ["Car line at {school}.", "Dropped {n} at {school} on the way to work."])
T["school_pickup"] = k("pick the kids up from school", "When school lets out, I want to be in the pickup line, so I can get the kids home.",
                       ["Pickup line at {school}.", "Collected {n} from {school}."])
T["pickup_arranged_with_someone_else"] = k("arrange a school pickup", "When my shift runs past dismissal, I want someone I trust at the school door, so I can keep working.",
                                           "Called around until someone could pick up at {school}.")
T["stayed_home_with_sick_child"] = k("stay home with a sick child", "When my child wakes up sick, I want to be home with them, so I can look after them.", "Home with a sick {age}-year-old; used leave.")
T["school_closure_child_care_scramble"] = k("find child care for a closed school day", "When school closes with little notice, I want someone to watch the kids, so I can still work.",
                                            "School closed; spent the early morning finding someone to take the kids.")
# ------------------------------------------------------------------------------------------------ money services
T["atm_withdrawal"] = k("get cash from the ATM", ["When I need cash for the week, I want to pull it from my account, so I can pay the places that do not take cards.",
                                                 "When my wallet is empty, I want forty dollars out, so I can cover small things."],
                        ["Withdrew ${amt} at an ATM ({org}).", "${amt} cash from the machine at {org}."])
T["transfer_from_savings"] = k("move money from savings", "When checking is nearly empty, I want to pull from savings, so I can avoid an overdraft.", "Moved ${amt} from savings to checking.")
T["transfer_to_savings"] = k("move money to savings", "When there is a little extra, I want it out of checking, so I can keep from spending it.", "Moved ${amt} to savings.")
T["mobile_check_deposit"] = k("deposit a check by phone", "When I am handed a check, I want it deposited from my phone, so I can skip the branch.", "Mobile deposit of a {what}; ${avail} available now.")
T["branch_check_deposit"] = k("deposit a check at the branch", "When I have a check, I want it in my account today, so I can count on the money.", "Deposited a {what} with a teller at {org}.")
T["check_cashing"] = k("cash a check at {org}", "When I am paid by check and have no bank, I want cash today, so I can pay my bills.", "Cashed a {what} at {org}; fee ${fee}.")
T["check_not_cashed_yet"] = k("cash a check", "When I am handed a check after hours, I want somewhere open, so I can turn it into money.", "A {what} is still in hand; nowhere was open after work.")
T["money_order_purchase"] = k("buy a money order", "When my landlord will not take cash, I want a money order, so I can prove I paid.", "Money order for the {bill} bought at {org}.")
T["prepaid_card_cash_reload"] = k("load cash onto my card", "When I need to pay something online, I want my cash on a card, so I can make the payment.", "Loaded ${amt} at the register at {org}.")
T["prepaid_card_monthly_fee"] = k("pay the card's monthly fee", "When I use a prepaid card as my account, I want to keep it open, so I can receive deposits.", "Monthly fee taken from the prepaid card.")
T["bank_monthly_maintenance_fee"] = k("pay the account fee", "When my balance falls under the minimum, I want to know what the bank charges, so I can decide whether to keep the account.",
                                      "Monthly maintenance fee from {org} for a low balance.")
T["credit_card_payment"] = k("pay the credit card", ["When the card statement is due, I want at least the minimum paid, so I can avoid a late fee.",
                                                    "When I can clear the balance, I want it paid in full, so I can avoid interest."],
                             ["Payment to {org}.", "Card payment to {org}."])
T["credit_card_interest_charge"] = k("carry a card balance", "When I cannot pay the card in full, I want to know what carrying it costs, so I can plan to pay it down.",
                                     ["Interest posted at {apr}% APR on a ${bal} balance.", "Monthly interest charge on the card."])
T["credit_card_late_fee"] = k("pay the card on time", "When the due date slips past, I want to catch up, so I can stop the fees.", "Late fee added to the card balance.")
T["bnpl_installment"] = k("pay an installment", "When a pay-in-four payment comes due, I want it to clear, so I can avoid a late charge.", ["Installment to {org}.", "Scheduled pay-later installment to {org}."])
T["rent_to_own_payment"] = k("make the rent-to-own payment", "When the weekly payment is due, I want it made, so I can keep the furniture.", "Weekly payment to {org}.")
T["personal_loan_payment"] = bill("loan payment", "keep the loan current")
T["life_insurance"] = bill("life insurance premium", "leave my family something")
T["p2p_transfer"] = k("send money through an app", ["When I owe someone a few dollars, I want to send it from my phone, so I can settle up now.",
                                                   "When someone I know needs money today, I want to send it instantly, so I can help without a trip."],
                      ["Sent through {org}: {why}.", "App transfer for {why}.", "{why}, sent by phone."])
T["p2p_instant_cash_out"] = k("move app money to my bank now", "When money lands in the app, I want it in my bank today, so I can spend it.", "Instant transfer out of {org}; fee ${fee}.")
T["earned_wage_advance"] = k("get part of my pay early", "When payday is days away and the tank is empty, I want wages I have already earned, so I can get to work.", "Advance of ${amt} through {org}.")
T["payday_loan_disbursed"] = k("take out a payday loan", "When a bill cannot wait and I have nothing left, I want cash today, so I can keep the lights on.", "Borrowed ${amt} at {org}; ${due} due next payday.")
T["online_installment_loan_disbursed"] = k("take out an online loan", "When I am short and the storefront is closed, I want an online loan, so I can cover the gap.", "Online loan of ${amt} funded to checking.")
T["payday_loan_repayment"] = k("repay the payday loan", "When payday comes, I want the loan cleared, so I can stop paying fees.", "Loan paid off to {org}.")
T["payday_loan_rollover"] = k("repay the payday loan", "When I cannot repay the loan and eat, I want two more weeks, so I can keep the full amount from coming out.",
                              "Paid only the ${fee} fee to {org}; the loan rolls over.")
T["title_loan_disbursed"] = k("borrow against my car", "When I need more than a payday loan gives, I want cash against my title, so I can cover an emergency.", "Borrowed ${amt} at {org} against the car title.")
T["pawn_loan"] = k("pawn something for cash", "When I need cash for a few weeks, I want a loan on something I own, so I can get it back later.", "Pawned {item} at {org} for ${amt}.")
T["pawn_redemption"] = k("get my item out of pawn", "When I have the money again, I want my item back, so I can stop paying storage on it.", "Redeemed {item} at {org}.")
T["remittance_sent"] = k("send money to family abroad", "When my family back home is counting on me, I want to send part of my pay, so I can help with their rent and food.",
                         ["Transfer sent through {org}.", "Money sent home through {org}."])
T["ebt_cash_withdrawal"] = k("withdraw cash assistance", "When my cash benefits post, I want them out as cash, so I can pay rent and the phone.", "Withdrew ${amt} of cash assistance at an ATM.")
T["paid_tax_preparation"] = k("have my taxes done at {org}", "When my W-2s are all in, I want a preparer to file, so I can get my refund without a mistake.", "Return prepared at {org}.")
T["tax_software_filing"] = k("file my taxes online", "When I sit down with my tax forms, I want software to walk me through, so I can file tonight.", "Filed through {org}; the state return cost extra.")
T["tax_return_filed_free"] = k("file my taxes for free", "When my return is simple, I want to file without paying, so I can keep the whole refund.", "Filed a free federal return online.")
T["free_tax_preparation"] = k("get free tax help at {org}", "When paid preparers charge hundreds, I want a volunteer to file for me, so I can keep my refund.", "Return prepared by a volunteer at {org}.")
T["federal_tax_balance_due_payment"] = k("pay the tax I owe", "When my return shows a balance due, I want it paid, so I can avoid penalties.", "Balance due paid to the IRS from checking.")
T["card_charge_dispute"] = k("dispute a charge", "When a charge I do not recognize hits my card, I want it reversed, so I can get my money back.", "Disputed ${amt} for {what}; credit pending.")
T["bank_phone_call"] = k("sort out {matter} with {org}", "When my card or account is not working, I want the bank on the phone, so I can use my own money.", "Call to {org} about {matter}.")
T["scam_attempt_handled"] = k("deal with a scam attempt", "When a stranger contacts me about money, I want to tell real from fake, so I can protect my account.",
                              ["Got {how}; did not respond.", "Ignored {how} and blocked the number."])
T["scam_loss"] = k("protect my money from a scam", "When someone convincing says my money is in danger, I want to do the right thing, so I can keep it safe.", "Lost ${amt} after {how}, paid by {via}.")
# ------------------------------------------------------------------------------------------------ giving and faith
T["church_offering"] = k("give at the midweek service", "When the plate comes around, I want to give what I can, so I can support my church.", ["Offering at {org}.", "Midweek service offering at {org}."])
T["recurring_tithe"] = k("give my tithe", "When my income arrives, I want my tithe sent first, so I can keep my commitment.", "Recurring gift to {org}.")
T["recurring_donation"] = k("make my monthly donation", "When my monthly gift is charged, I want it to go through, so I can keep supporting the cause.", "Monthly donation to {org}.")
T["one_time_online_donation"] = k("donate online", "When a cause I care about asks, I want to give, so I can help.", "One-time gift to {org}.")
T["crowdfunding_contribution"] = k("chip in to a fundraiser", "When someone I know is in trouble, I want to chip in, so I can help them through it.", "Gave toward {cause} on {org}.")
T["crowdfunding_campaign_started"] = k("start a fundraiser", "When the funeral costs more than we have, I want to ask friends for help, so I can bury my relative properly.",
                                       "Started a {org} page to raise ${amt}.")
# ------------------------------------------------------------------------------------------------ care, household, work
T["caregiving_at_home"] = k("care for a family member", ["When someone in my home cannot manage alone, I want to help with the day's needs, so I can keep them safe at home.",
                                                       "When care falls to me, I want to fit it around work, so I can do both."],
                            ["Helped my {rel} ({age}) with {tasks}.", "Unpaid care at home: {tasks}."])
T["caregiving_visit"] = k("check on a relative", ["When my relative lives alone and needs help, I want to stop by, so I can make sure they are all right.",
                                                "When I am the one family member nearby, I want to visit after work, so I can handle what they cannot."],
                          ["Drove over to help my relative ({age}) with {tasks}.", "Visit for {tasks}."])
T["escort_to_appointment"] = k("take a family member to an appointment", "When my relative cannot get to the doctor alone, I want to take them, so I can hear what the doctor says.",
                               ["Took my {rel} to {org}.", "Drove and waited at {org}."])
T["hospital_bedside_time"] = k("be at the hospital with family", "When someone I love is admitted, I want to be at the bedside, so I can speak for them.", "At {org} with my {rel}.")
T["hospital_visit_to_relative"] = k("visit a relative in the hospital", "When my relative is in the hospital, I want to visit, so I can keep their spirits up.", "Visiting hours at {org}.")
T["at_hospital_for_a_birth"] = k("be there for the birth", "When the baby is coming, I want to be in the room, so I can support my partner.", "At {org} for the birth.")
T["job_applications_online"] = k("apply for jobs", "When I am out of work, I want applications in every day, so I can get an interview.", ["Sent {n} applications online.", "Evening of job applications; {n} submitted."])
T["job_search_in_person"] = k("look for work in person", "When I have no internet at home, I want to ask for work in person, so I can find something.", "Stopped at {n} employers to ask about openings.")
T["job_interview"] = k("go to a job interview", "When I finally get an interview, I want to be there on time, so I can make my case.", ["Interview for a new position.", "Job interview across town."])
T["weekly_unemployment_certification"] = k("certify for unemployment", "When the claim week closes, I want to certify, so I can be paid.", "Weekly certification filed.")
T["career_center_visit"] = k("get help at {org}", "When my search is going nowhere, I want someone to look at my résumé, so I can find work sooner.", "Résumé help and job leads at {org}.")
T["sent_home_early"] = k("work my full shift", "When I am scheduled for a full shift, I want to work all of it, so I can earn what I planned on.",
                         ["Sent home {hrs} hours early from {org}; about ${lost} in pay gone.", "{org} cut the shift short by {hrs} hours."])
T["shift_cancelled_short_notice"] = k("work my scheduled shift", "When I arrange my week around a shift, I want it to happen, so I can earn the pay I counted on.",
                                      ["{org} cancelled the shift with {notice} notice; about ${lost} in pay gone.", "Shift at {org} dropped {notice}."])
T["turned_down_extra_hours"] = k("pick up extra hours", "When my manager offers more hours, I want to say yes, so I can earn more without losing the help that keeps us afloat.",
                                 "Turned down {hrs} extra hours at {org} (about ${extra}) to stay under the limit for {prog}.")
T["ride_to_work_fee"] = k("pay for the ride to work", "When the fields are miles from town and I have no car, I want a seat in the crew van, so I can get to work.",
                          ["Paid the driver for the ride out to {org}.", "Cash to the crew driver for the trip to the fields."])
T["missed_shift_for_sick_child"] = k("go to work", "When my child is sick and there is no one else, I want to stay home without losing my job, so I can take care of them.",
                                     "Missed {hrs} hours of work to stay with a sick {age}-year-old; about ${lost} unpaid.")
T["late_or_missed_shift"] = k("get to work on time", "When my ride fails, I want to make my shift anyway, so I can keep my hours.", "Lost {hrs} hours and about ${lost} because {why}.")
# ------------------------------------------------------------------------------------------------ civic and legal
T["driver_license_renewal"] = k("renew my driver's license", "When my license is about to expire, I want it renewed, so I can keep driving to work.", ["License renewed at {org}.", "Renewal processed by {org}."])
T["first_driver_license"] = k("get my first license", "When I pass the test, I want my license, so I can drive myself.", "First license issued at {org}.")
T["state_id_card"] = k("get a state ID", "When I need ID for a job or benefits, I want a state card, so I can prove who I am.", "State ID issued at {org}.")
T["real_id_upgrade"] = k("upgrade to a REAL ID", "When I need to fly, I want the starred license, so I can get through security.", "REAL ID processed at {org}.")
T["title_transfer"] = k("transfer a car title", "When I buy a used car, I want the title in my name, so I can register it.", "Title transfer at {org}.")
T["court_fine_payment"] = k("pay a court fine", "When I owe on {what}, I want it paid, so I can keep my license from being suspended.", "Paid the fine for {what}.")
T["court_fine_payment_plan"] = k("set up a payment plan with the court", "When I cannot pay the whole fine, I want a plan, so I can avoid a warrant.", "Payment plan for {what}; ${total} owed in all.")
T["court_appearance"] = k("appear in court", "When I have a court date, I want to be there, so I can avoid a default.", "Appeared at {org} for {matter}.")
T["jury_duty"] = k("serve jury duty", "When I am summoned, I want to serve and be done, so I can get back to work.", ["Reported for jury duty at {org}.", "Day in the jury pool at {org}."])
T["probation_supervision_fee"] = k("pay the supervision fee", "When my monthly check-in comes, I want the fee paid, so I can stay in compliance.", "Supervision fee paid at {org}.")
T["cash_bond_posted"] = k("post bond", "When someone in my family is in jail, I want them out before their shift, so I can keep them from losing the job.", "Bond posted at {org}.")
T["jail_day"] = k("get through a day in jail", "When I cannot make bail, I want my court date to come, so I can go home.", "Day in custody at {org}.")
T["jail_account_deposit"] = k("put money on a jail account", "When my relative is inside, I want money on their account, so I can let them call home.", "Deposit through {org}.")
T["building_permit"] = k("get a building permit", "When I am building {what}, I want the permit, so I can pass inspection.", "Permit for {what}.")
T["pet_license"] = k("license the dog", "When the city requires a tag, I want it done, so I can avoid a fine.", "Pet license renewed online.")
T["yard_sale_permit"] = k("get a yard sale permit", "When I am clearing out the garage, I want the permit, so I can hold the sale.", "Yard sale permit.")
T["residential_parking_permit"] = k("get a parking permit", "When my street is permit-only, I want a sticker, so I can park near home.", "Residential parking permit.")
T["business_license_renewal"] = k("renew the business license", "When my license comes up, I want it renewed, so I can keep operating.", "Business license renewed with the city.")
T["fishing_or_hunting_license"] = k("buy a fishing license", "When the season opens, I want my license, so I can fish legally.", "License bought online from the state.")
T["passport_application"] = k("apply for a passport", "When a trip is planned, I want my passport application in, so I can travel.", "Passport application accepted at {org}.")
T["immigration_filing_fee"] = k("file immigration paperwork", "When my status depends on a form and a fee, I want both sent, so I can keep working here.", "Filed {form}.")
T["immigration_attorney_consultation"] = k("consult an immigration attorney", "When the forms are confusing, I want a lawyer to check them, so I can avoid a mistake.", "Consultation at {org} about {form}.")
T["attorney_retainer"] = k("retain a lawyer", "When I am filing for divorce, I want a lawyer, so I can protect my share.", "Retainer paid to {org}.")
T["marriage_license"] = k("get a marriage license", "When we decide to marry, I want the license, so I can make it official.", "Marriage license issued at {org}.")
T["divorce_filing_fee"] = k("file for divorce", "When the marriage is over, I want to file, so I can move on.", "Petition filed at {org}.")
T["notary_service"] = k("get a document notarized", "When a form needs a notary, I want it stamped, so I can send it in.", "Notarized {doc} at {org}.")
T["voter_registration_update"] = k("update my voter registration", "When my details change, I want my registration updated, so I can vote.", "Updated registration after {why}.")
T["change_of_address"] = k("file a change of address", "When I move, I want my mail forwarded, so I can keep getting my bills.", "Change of address filed.")
T["social_security_office_visit"] = k("get help at the Social Security office", "When I have a problem with my benefits, I want to see someone, so I can fix it.", "Visit to {org} about {matter}.")
T["social_security_phone_call"] = k("reach Social Security by phone about {matter}", "When a letter about my benefits confuses me, I want to reach a person, so I can understand it.", "Call about {matter}.")
T["irs_phone_call"] = k("reach the IRS about {matter}", "When my refund is stuck, I want a person at the IRS, so I can find out why.", "Call about {matter}.")
T["medicaid_renewal"] = k("renew Medicaid", "When my renewal packet arrives, I want it filed before the deadline, so I can keep my coverage.", ["Medicaid renewal submitted to {org}.", "Renewal packet completed."])
T["snap_recertification"] = k("recertify for SNAP", "When my certification period ends, I want my paperwork in, so I can keep food benefits.", ["SNAP recertification submitted to {org}.", "Recertification completed."])
T["renewal_resubmitted"] = k("resubmit a benefits renewal", "When my renewal comes back, I want to fix it and send it again, so I can keep my benefits.", "Renewal corrected and sent back to {org}.")
T["benefits_renewal_returned"] = k("renew my benefits", "When I mail my renewal, I want it accepted, so I can keep my benefits.", "Renewal came back in the mail: {reason}.")
T["medicaid_work_hours_report"] = k("report my work hours for Medicaid", "When the state wants proof of my hours every month, I want to report them, so I can keep my coverage.",
                                    ["Monthly work-hours report filed.", "Uploaded pay stubs for the monthly hours report."])
T["legal_aid_consultation"] = k("get legal help at {org}", "When I cannot afford a lawyer, I want legal aid, so I can understand my rights.", "Met with {org} about {matter}.")
T["funeral_arrangements"] = k("arrange the funeral at {org}", "When someone in my family dies, I want a proper {kind}, so I can say goodbye.", "Arrangements at {org} for my {rel}: {kind}.")
T["death_certificates"] = k("order death certificates", "When I have to close accounts, I want certified copies, so I can settle the estate.", "{n} certified copies ordered from the county.")
T["death_recorded"] = k("record a death", "When a relative dies, I want it recorded, so I can begin what comes next.", "Death at {where}, age {age}.")
T["birth_registered"] = k("register the birth", "When our baby is born, I want the birth registered, so I can get the certificate.", "Birth registered with the county.")
# ------------------------------------------------------------------------------------------------ public services
T["library_visit"] = k("use the library", ["When I want books without buying them, I want the library, so I can read for free.",
                                           "When the kids need something to do, I want an hour at the library, so I can get them reading."],
                       ["Checked out {items} items at {org}.", "Browsed and borrowed at {org}."])
T["library_computer_session"] = k("use a library computer", "When I have no internet at home, I want a computer and a printer, so I can finish {purpose}.", "Computer session at {org} for {purpose}.")
T["library_story_time"] = k("take my child to story time", "When my toddler needs other kids, I want story time, so I can get us out of the house.", "Story time at {org}.")
T["rec_league_practice"] = k("go to practice", "When the season starts, I want to be at practice, so I can play with my team.", "Rec league practice at the city fields.")
T["senior_fitness_class"] = k("go to my exercise class", "When I want to stay on my feet, I want my class, so I can keep my balance.", "Fitness class at {org}.")
# ------------------------------------------------------------------------------------------------ business
T["card_settlement_batch"] = k("settle the day's card sales", "When the business day closes, I want card sales deposited, so I can pay suppliers and staff.",
                               ["Batch of {n} card sales for {org}; fees took {pct}%.", "Card settlement to {org}: ${net} net."])
T["cash_deposit"] = k("deposit the day's cash", "When the drawer is counted, I want the cash in the bank, so I can keep it safe.", "Cash from {org} dropped at the bank.")
T["merchant_cash_advance_daily_remittance"] = k("repay the cash advance", "When I took an advance on future sales, I want the daily cut to come out, so I can finish paying it off.",
                                                "Advance provider took {pct}% of {org}'s card sales.")
T["delivery_platform_payout"] = k("get paid for delivery orders", "When delivery orders come through the app, I want my share, so I can cover food costs.", "Payout to {org} for {n} orders; commission {pct}%.")
T["payroll_run"] = k("run payroll", "When payday comes, I want every employee paid correctly, so I can keep my staff.", "Payroll run at {org} covering {n} on staff.")
T["employer_payroll_taxes"] = k("pay employer payroll taxes", "When I run payroll, I want the employer taxes set aside, so I can stay square with the government.", "Employer share of payroll taxes for {org}.")
T["federal_payroll_tax_deposit"] = k("deposit payroll taxes", "When the deposit deadline falls today, I want withheld taxes sent, so I can avoid penalties.", "Semiweekly federal tax deposit by {org}.")
T["foodservice_delivery"] = k("receive the food delivery", "When the truck arrives before open, I want the full order, so I can serve the whole menu.", "Delivery from {org} to {buyer}; terms: {terms}.")
T["store_replenishment_delivery"] = k("restock the shelves", "When the truck backs in overnight, I want the order complete, so I can open with full shelves.", "Overnight truck for {org}.")
T["pharmacy_wholesaler_order"] = k("restock the pharmacy", "When the daily order arrives, I want every drug in it, so I can fill today's prescriptions.", "Daily wholesaler tote for {org}.")
T["fuel_delivery"] = k("refill the tanks", "When the tanks run low, I want a tanker drop, so I can keep the pumps on.", "{gal} gallons delivered to {org} at ${rack} rack.")
T["contractor_materials_purchase"] = k("buy materials for the job", "When a job starts in the morning, I want materials loaded early, so I can keep the crew working.", "{buyer} picked up materials at {org}; terms: {terms}.")
T["shop_parts_order"] = k("order parts for a repair", "When a car is on the lift, I want the part by noon, so I can return it today.", "{buyer} ordered parts from {org}.")
T["shop_supplies_order"] = k("order shop supplies", "When supplies run low, I want them delivered, so I can keep serving customers.", "{buyer} ordered supplies from {org}.")
T["raw_materials_delivery"] = k("receive raw materials", "When the line is scheduled, I want materials on the dock, so I can keep it running.", "Inbound materials for {org}; {terms}.")
T["customer_shipment_invoiced"] = k("ship and invoice an order", "When an order ships, I want it invoiced, so I can be paid in forty-five days.", "Outbound shipment invoiced by {org}; {terms}.")
T["medical_supply_delivery"] = k("receive medical supplies", "When the units restock, I want the supply order in, so I can treat patients.", "Supply delivery from {org} to {buyer}.")
T["school_food_service_delivery"] = k("receive the cafeteria food order", "When schools serve thousands of meals, I want the food delivered, so I can feed students.", "Food service delivery from {org}.")
T["milk_pickup"] = k("ship the day's milk", "When the tanker comes, I want the milk picked up, so I can be paid on the next settlement.", "{lb} pounds of milk picked up at {org}.")
T["farm_load_delivered_to_packer"] = k("deliver a load to the packer", "When the crop is picked, I want it at the shed cold, so I can get the best grade.", "Load from {farm} to {org}; {terms}.")
T["packer_settlement_check"] = k("get paid by the packer", "When the packer settles, I want the check, so I can pay the crew and the bank.", "Settlement to {farm}: ${net} after packing charges.")
T["grain_sold_to_elevator"] = k("sell grain to the elevator", "When the bid looks decent, I want to sell stored grain, so I can pay for seed.", "{bu} bushels from {farm} at ${px}.")
T["farm_inputs_purchase"] = k("buy inputs for planting", "When planting is weeks away, I want inputs bought, so I can be ready.", "{farm} bought {what} at {org} on the operating line.")
T["livestock_sold_at_auction"] = k("sell cattle at the sale barn", "When the calves are ready, I want them sold at Wednesday's sale, so I can pay the bank.", "{head} head sold at {org}; ${net} after commission.")
T["farm_program_payment"] = k("receive a farm program payment", "When the program pays, I want the deposit, so I can cover operating costs.", "Federal farm program payment to {farm}.")
T["commercial_rent_payment"] = k("pay the business rent", "When the lease payment is due, I want it paid, so I can keep the location.", "Monthly rent for {org}.")
T["business_utility_bill"] = k("pay the business power bill", "When the utility bill comes, I want it paid, so I can keep the doors open.", "Electric bill for {org}.")
T["business_insurance_premium"] = k("pay the business insurance", "When the premium is due, I want coverage in force, so I can operate.", "Insurance premium for {org}.")
T["business_loan_payment"] = k("pay the business loan", "When the loan draft hits, I want it covered, so I can keep my credit line.", "Loan payment from {org}.")
T["software_subscription"] = k("pay for business software", "When the register software renews, I want it paid, so I can ring up sales.", "Software subscription for {org}.")
T["route_service_invoice"] = k("get the weekly service", "When the route truck comes, I want the service done, so I can pass inspection.", "{what} for {buyer} by {org}.")
T["accounting_fees"] = k("pay the accountant", "When the books are closed for the year, I want the accountant paid, so I can file on time.", "{buyer} paid {org} for tax work.")
T["local_advertising"] = k("buy local advertising", "When business is slow, I want an ad, so I can bring customers in.", "{buyer} bought advertising from {org}.")
T["property_maintenance_invoice"] = k("pay for building repairs", "When a unit needs repair, I want the contractor paid, so I can keep tenants.", "{buyer} paid {org} for maintenance.")
T["overdue_invoice_follow_up"] = k("collect an overdue invoice", "When a customer is weeks late, I want to be paid, so I can make my own payroll.",
                                   ["Invoice for ${amt} is {days} days old; the answer was that {said}.", "Chased ${amt} owed for {days} days: {said}."])
T["late_invoice_paid"] = k("get paid on a late invoice", "When an old invoice is finally paid, I want it deposited, so I can catch up.", "Payment for ${amt} arrived {days} days after the invoice.")
T["government_vendor_payment"] = k("pay a vendor", "When the check run goes out, I want vendors paid, so I can keep services running.", "{org} paid {vendor} {days} days after invoice.")
T["child_care_subsidy_payment_to_provider"] = k("get paid for subsidized care", "When I care for children on assistance, I want the state's payment, so I can pay my teachers.", "State subsidy payment to {org}.")
T["grant_disbursement"] = k("receive a grant", "When the campaign distributes funds, I want our grant, so I can keep the program open.", "Grant payment to {org}.")
T["office_catering_order"] = k("order lunch for the office", "When there is a working lunch, I want food delivered, so I can keep the meeting going.", "{buyer} ordered lunch for {n} from {org}.")
T["self_employed_supplies"] = k("buy what the job needs at {org}", "When tomorrow's job needs supplies, I want them bought, so I can do the work.", "Bought {what} at {org} for work as a {occ}.")
T["eviction_filing_fee"] = k("file an eviction", "When a tenant is months behind, I want to file, so I can recover the unit.", "{org} filed an eviction case.")
