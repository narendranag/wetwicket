"""Hand-built map from Cricsheet city (or venue, where city is missing) to host country.

UK/Ireland follow cricket's own boundaries: England & Wales (ECB), Scotland, and Ireland (all-island).
"""

EW, SCO, IRE = "England & Wales", "Scotland", "Ireland"
AUS, IND, NZ, SA, SL = "Australia", "India", "New Zealand", "South Africa", "Sri Lanka"
PAK, BAN, ZIM, UAE, NL = "Pakistan", "Bangladesh", "Zimbabwe", "United Arab Emirates", "Netherlands"
HK, USA, NEP, MAS, DEN = "Hong Kong", "United States", "Nepal", "Malaysia", "Denmark"

_BY_COUNTRY = {  # "|"-separated
    EW: "Arundel | Beckenham | Birmingham | Bishop's Stortford | Blackpool | Brighton | Bristol | "
        "Cambridge | Canterbury | Cardiff | Chelmsford | Cheltenham | Chester | Chester-le-Street | "
        "Chesterfield | Coggeshall | Colchester | Colwyn Bay | Darlington | Derby | Eastbourne | Exmouth | "
        "Farington | Frinton-on-Sea | Gosforth | Grantham | Guildford | Halstead | Horsham | Hove | "
        "Kibworth | Kidderminster | Leeds | Leicester | Liverpool | London | Loughborough | "
        "Louth Cricket Club | Manchester | Market Warsop | Milton Keynes | Milverton | Neath | "
        "Nettleworth | Newbury | Newport | Northampton | Northwood | Nottingham | Oakham | Radlett | "
        "Repton | Richmond | Rugby | Sale | Scarborough | Sedbergh | Solihull | Sookholme | Southampton | "
        "Southend-on-Sea | Southport | Street | Swansea | Taunton | Tunbridge Wells | Uxbridge | Welbeck | "
        "West Mersea Cricket Club | Worcester | Wormsley | York",
    SCO: "Aberdeen | Arbroath | Ayr | Dundee | Edinburgh | Glasgow | Stirling",
    IRE: "Belfast | Bready | Comber | Cork | Derry | Dublin | Eglinton | Lisburn | Londonderry | Strabane | "
        "Waringstown | Wicklow",
    AUS: "Adelaide | Adelaide Oval No. 2 | Albury | Alice Springs | Ballarat | Bendigo | Bowral | "
        "Brisbane | Burnie | Cairns | Canberra | Carrara | Coffs Harbour | Darwin | Geelong | Gold Coast | "
        "Hobart | Kennards Hire Community Oval | Latrobe | Launceston | Mackay | Melbourne | Moe | "
        "Nuriootpa | Perth | Sydney | Townsville | Victoria | Wollongong",
    NZ: "Alexandra | Auckland | Cello Basin Reserve | Christchurch | Cobham Oval | Colin Maiden Park | "
        "Dunedin | Fitzherbert Park | Gisborne | Invercargill | Mount Maunganui | Napier | Nelson | "
        "Nelson Park | New Plymouth | Palmerston North | Queenstown | Rangiora | "
        "University of Otago Oval | Wellington | Whangarei",
    SA: "Benoni | Bloemfontein | Cape Town | Centurion | Durban | East London | Gqeberha | Johannesburg | "
        "Kimberley | Paarl | Pietermaritzburg | Port Elizabeth | Potchefstroom | Pretoria | "
        "Stellenbosch University 1 | Stellenbosch University 2",
    IND: "Ahmedabad | Alembic 1 Cricket Ground | Alembic 2  Cricket Ground | Alur Cricket Stadium | "
        "Alur Cricket Stadium II | Alur Cricket Stadium III | BKC Ground | Bangalore | Barsapara | "
        "Bengaluru | Bharat Ratna Shri Atal Bihari Vajpayee Ekana Cricket Stadium B | C B Patel Ground | "
        "Chandigarh | Chaudhry Bansi Lal Cricket Stadium | Chennai | Cuttack | DRIEMS Ground | Dehra Dun | "
        "Delhi | Dharamsala | Dharmasala | Dr P.V.G. Raju ACA Sports Complex | "
        "Dr. Y.S. Rajasekhara Reddy ACA VDCA Cricket Stadium | "
        "Emerald Heights International School Ground | F B Colony Ground | Faridabad | "
        "Gokaraju Liala Gangaaraju ACA Cricket Ground | Greenfield Stadium | "
        "Gurugram Cricket Ground (SRNCC) | Guwahati | Gwalior | Holkar Stadium | Hyderabad | "
        "IC-Gurunanak College Ground | Indore | Jadavpur University Campus | Jaipur | Jamshedpur | "
        "Jawaharlal Nehru Stadium | Kanpur | Kochi | Kolkata | Lalbhai Contractor Stadium | Lucknow | "
        "Mangalagiri | Margao | Mohali | Motera | Motibaug Cricket Ground | Mulapadu | Mumbai | Nagpur | "
        "Navi Mumbai | New Chandigarh | Palam | Palam II | Pune | Raipur | Rajkot | Ranchi | "
        "Reliance Cricket Stadium | SSN College Ground | Salt Lake | Sector 26 | Sector-16 | "
        "Sharad Pawar Cricket Academy BKC | Sri Ramachandra Medical College | "
        "St  Pauls college ground  Kalamassery | St'Xavier's KCA Cricket Ground | Surat | "
        "T I Murugappa Ground | Thiruvananthapuram | VCA Ground | Vadodara | Visakhapatnam",
    SL: "Colombo | Dambulla | Galle | Hambantota | Kaluthara | Kandy | Katunayake | Kurunegala | Maggona | "
        "Moratuwa | Pallekele | Panadura | Panagoda | Welisara",
    PAK: "Faisalabad | Karachi | Lahore | Multan | Peshawar | Rawalpindi | Sheikhupura Stadium | Sind",
    BAN: "Bogra | Chattogram | Chittagong | Chittagong Divisional Stadium | Cox's Bazar | Dhaka | "
        "Fatullah | Khulna | Mirpur | Rajshahi | Sylhet",
    ZIM: "Bulawayo | Harare | Kwekwe",
    UAE: "Abu Dhabi | Ajman | Al Dhaid Cricket Village | Dubai | Dubai Sports City Cricket Stadium | "
        "Sharjah",
    NL: "Amstelveen | Deventer | Rotterdam | Schiedam | The Hague | Utrecht | Voorburg",
    HK: "Hong Kong | Kowloon | Mong Kok | Wong Nai Chung Gap",
    USA: "Dallas | Grand Prairie | Houston | Lauderhill | Los Angeles | Morrisville | New York | Oakland | "
        "Pearland | Pomona",
    NEP: "Kathmandu | Kirtipur | Pokhara",
    MAS: "Bandar Kinrara | Bangi | Johor | Kuala Lumpur | Mantin",
    DEN: "Brondby | Copenhagen | Ishoj | Koge",
    "Italy": "Medicina | Navile | Pianoro | Rome | Spinaceto",
    "Austria": "Graz | Latschach | Lower Austria",
    "Germany": "Gelsenkirchen | Karlsruhe | Krefeld",
    "Canada": "King City | Toronto",
    "Uganda": "Entebbe | Jinja | Kampala",
    "Kenya": "Mombasa Sports Club Ground | Nairobi",
    "Nigeria": "Abuja | Lagos | Tafawa Balewa Square (TBS) Cricket Oval",
    "Argentina": "Buenos Aires | San Albano | St Georges Quilmes",
    "Guernsey": "Castel | Port  Soif | St Martin | St Peter Port",
    "Jersey": "St Clement | St Saviour",
    "Romania": "Ilfov County | Moara Vlasiei Cricket Ground",
    "Thailand": "Bangkok | Chiang Mai",
    "Spain": "Almeria | Murcia",
    "Mexico": "Mexico City | Naucalpan",
    "Japan": "Nisshin | Osaka | Sano",
    "China": "Guanggong International Cricket Stadium | Hangzhou",
    "Singapore": "Padang | Singapore",
    "Trinidad and Tobago": "Port of Spain | Tarouba | Trinidad",
    "Barbados": "Barbados | Bridgetown | Cave Hill",
    "Antigua and Barbuda": "Antigua | Coolidge | North Sound | St John's",
    "Jamaica": "Jamaica | Kingston",
    "Guyana": "Guyana | Providence",
    "Saint Lucia": "Gros Islet | St Lucia",
    "Saint Kitts and Nevis": "Basseterre | St Kitts",
    "Saint Vincent and the Grenadines": "Kingstown | St Vincent",
    "Grenada": "Grenada | St George's",
    "Dominica": "Dominica | Roseau",
}
# Single-city countries, where the name is unambiguous.
_SINGLES = {
    "Accra": "Ghana", "Al Amarat": "Oman", "Albergaria": "Portugal", "Apia": "Samoa", "Bali": "Indonesia",
    "Belgrade": "Serbia", "Bermuda": "Bermuda", "Blantyre": "Malawi", "Bogota": "Colombia",
    "Corfu": "Greece", "Dar-es-Salaam": "Tanzania", "Dasmarinas": "Philippines", "Doha": "Qatar",
    "Dreux": "France", "Episkopi": "Cyprus", "FTZ Sports Complex": SL, "Gaborone": "Botswana", "Gelephu": "Bhutan",
    "George Town": "Cayman Islands", "Ghent": "Belgium", "Gibraltar": "Gibraltar", "Guacima": "Costa Rica",
    "Incheon": "South Korea", "Kerava": "Finland", "Kigali City": "Rwanda", "Kolsva": "Sweden",
    "Kuwait City": "Kuwait", "Malkerns": "Eswatini", "Marsa": "Malta", "Noumea": "New Caledonia",
    "Oslo": "Norway", "Panama City": "Panama", "Phnom Penh": "Cambodia", "Port Moresby": "Papua New Guinea",
    "Port Vila": "Vanuatu", "Prague": "Czech Republic", "Seropedica": "Brazil", "Sofia": "Bulgaria",
    "Stockholm": "Sweden", "Suva": "Fiji", "Szodliget": "Hungary", "Tallinn": "Estonia", "Vantaa": "Finland",
    "Walferdange": "Luxembourg", "Waterloo": "Belgium", "Windhoek": "Namibia", "Zagreb": "Croatia",
    "Zemst": "Belgium",
}

CITY_COUNTRY = dict(_SINGLES)
for _country, _names in _BY_COUNTRY.items():
    CITY_COUNTRY.update({n.strip(): _country for n in _names.split("|")})

# Same city name in two countries: resolve by venue.
VENUE_COUNTRY = {
    "White Hill Field, Sandys Parish": "Bermuda",
    "National Stadium, Hamilton": "Bermuda",
    "Bert Sutcliffe Oval, Lincoln": NZ,
}
_AMBIGUOUS = {"Hamilton": NZ, "Lincoln": EW}


def country_for(city, venue):
    if venue in VENUE_COUNTRY:
        return VENUE_COUNTRY[venue]
    return CITY_COUNTRY.get(city) or _AMBIGUOUS.get(city)
