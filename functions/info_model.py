from typing import List

OUTGOING_INFORMATION_MODEL = {
    "*": {
        "HUIS": {
            "INTERNET": [],
            "HUUR": [],
            "WATER": [],
            "ENERGIE & WARMTE": [],
            "MOBIEL": [],
            "GOOGLE": [],
        },
        "SPAREN": [],
        "ZORG": {
            "ZORGVERZEKERING": [],
            "MEDICIJNEN": [],
            "COSMETISCH": [],
            "HYGIENE": [],
            "BEHANDELING": [],
            "KAPPER": [],
        },
        "AANKOPEN": {
            "KEUKEN": [],
            "MEUBILAIR": [],
            "KLEDING": [],
            "PLANTEN": [],
            "CADEAU": [],
            "TECHNIEK": [],
        },
        "REIS": {
            "AUTO": {
                "BENZINE": [],
                "AUTOONDERHOUD": [],
                "WEGENBELASTING": [],
                "AUTOVERZEKERING": [],
                "PARKEREN": [],
            },
            "FIETS": [],
            "OV": {"VLIEGTUIG": [], "TREIN/BUS/TRAM": []},
            "REISVERZEKERING": [],
        },
        "ETEN": {
            "BOODSCHAPPEN": {
                "AH": [],
                "JUMBO": [],
                "ALDI": [],
                "PLUS": [],
                "HEMA": [],
                "ANDERE WINKELS": [],
            },
            "SPECIAALZAKEN": {
                "BAKKER": [],
                "SLAGER": [],
                "KAAS": [],
                "VIS": [],
                "KOFFIE": [],
                "SLIJTERIJ": [],
            },
            "TO GO": [],
            "LUNCH": [],
        },
        "ONTSPANNING": {
            "STREAMEN": [],
            "SPORT & SPEL": {
                "SCOUTING": [],
                "SPEL": [],
                "HENGELVERENIGING": [],
                "SPORTCITY": [],
                "PADEL": [],
            },
            "UITJES": {"UIT ETEN": [], "ATTRACTIES": [], "KROEG/CAFE": []},
            "VAKANTIE": [],
            "WELLNESS": [],
        },
        "ONDERWIJS": {"TAAL": []},
        "BELASTINGEN": {
            "INKOMSTENBELASTING": [],
            "GEMEENTEBELASTING": [],
        },
        "DUO": [],
        "WERK": [],
        "OVERIG": [],
    }
}
INCOME_INFORMATION_MODEL = {
    "*": {"SALARIS": [], "VERGOEDING": [], "RENTE": []},
}

SPECIAL_CATEGORIES = [
    "IGNORE"
]


def generate_list_of_categories(
    obj: dict = None, categories_list: list = None
) -> List[str]:
    for key in obj:
        if isinstance(obj[key], list):
            categories_list.append(key)
        elif isinstance(obj[key], dict):
            categories_list = generate_list_of_categories(obj[key], categories_list)
        else:
            raise ValueError("Only use dict and list as values in information models.")
    return categories_list


# class InfoModel(BaseModel):
