"""
City mappings for Uzbekistan train stations.
"""

CITIES = [
    {
        "ru": "Ташкент",
        "uz": "Toshkent",
        "en": "Tashkent",
        "code": "2900000"
    },
    {
        "ru": "Самарканд",
        "uz": "Samarqand",
        "en": "Samarkand",
        "code": "2900700"
    },
    {
        "ru": "Бухара",
        "uz": "Buxoro",
        "en": "Bukhara",
        "code": "2900800"
    },
    {
        "ru": "Хива",
        "uz": "Xiva",
        "en": "Khiva",
        "code": "2900172"
    },
    {
        "ru": "Ургенч",
        "uz": "Urganch",
        "en": "Urgench",
        "code": "2900790"
    },
    {
        "ru": "Нукус",
        "uz": "Nukus",
        "en": "Nukus",
        "code": "2900970"
    },
    {
        "ru": "Навои",
        "uz": "Navoiy",
        "en": "Navoi",
        "code": "2900930"
    },
    {
        "ru": "Андижан",
        "uz": "Andijon",
        "en": "Andijan",
        "code": "2900680"
    },
    {
        "ru": "Карши",
        "uz": "Qarshi",
        "en": "Karshi",
        "code": "2900750"
    },
    {
        "ru": "Джизак",
        "uz": "Jizzax",
        "en": "Jizzakh",
        "code": "2900720"
    },
    {
        "ru": "Термез",
        "uz": "Termiz",
        "en": "Termez",
        "code": "2900255"
    },
    {
        "ru": "Гулистан",
        "uz": "Guliston",
        "en": "Gulistan",
        "code": "2900850"
    },
    {
        "ru": "Коканд",
        "uz": "Qo'qon",
        "en": "Qo'qon",
        "code": "2900880"
    },
    {
        "ru": "Маргилан",
        "uz": "Margilon",
        "en": "Margilon",
        "code": "2900920"
    },
    {
        "ru": "Пап",
        "uz": "Pop",
        "en": "Pop",
        "code": "2900693"
    },
    {
        "ru": "Наманган",
        "uz": "Namangan",
        "en": "Namangan",
        "code": "2900940"
    }
]


def get_city_by_code(code: str) -> dict | None:
    """Get city data by station code."""
    for city in CITIES:
        if city["code"] == code:
            return city
    return None


def get_city_name_uz(code: str) -> str:
    """Get Uzbek city name by code."""
    city = get_city_by_code(code)
    return city["uz"] if city else code


def get_city_name_ru(code: str) -> str:
    """Get Russian city name by code."""
    city = get_city_by_code(code)
    return city["ru"] if city else code
