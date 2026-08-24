"""Парсинг пользовательского ввода.

Поддерживаемые форматы (цифры и марка в любом порядке):
  123 Toyota      → plate=123, brand=Toyota
  toyota 123      → plate=123, brand=Toyota
  123тойота       → plate=123, brand=Toyota
  тойота123       → plate=123, brand=Toyota
  456 ТОЙОТА      → plate=456, brand=Toyota
"""
import re

# Словарь русских названий марок → нормальное написание
_RU_BRANDS: dict[str, str] = {
    "тойота": "Toyota",
    "хонда": "Honda",
    "мицубиси": "Mitsubishi",
    "мицубиши": "Mitsubishi",
    "митсубиси": "Mitsubishi",
    "ниссан": "Nissan",
    "мазда": "Mazda",
    "субару": "Subaru",
    "лексус": "Lexus",
    "инфинити": "Infiniti",
    "хюндай": "Hyundai",
    "хендай": "Hyundai",
    "хундай": "Hyundai",
    "киа": "Kia",
    "шкода": "Skoda",
    "фольксваген": "Volkswagen",
    "фольксваг": "Volkswagen",
    "мерседес": "Mercedes",
    "мерс": "Mercedes",
    "бмв": "BMW",
    "bmw": "BMW",
    "ауди": "Audi",
    "опель": "Opel",
    "форд": "Ford",
    "шевроле": "Chevrolet",
    "рено": "Renault",
    "пежо": "Peugeot",
    "ситроен": "Citroen",
    "вольво": "Volvo",
    "порше": "Porsche",
    "ягуар": "Jaguar",
    "джип": "Jeep",
    "лада": "Lada",
    "ваз": "ВАЗ",
    "газ": "ГАЗ",
    "уаз": "УАЗ",
    "нива": "Нива",
    "гранта": "Lada Granta",
    "веста": "Lada Vesta",
    "хавал": "Haval",
    "чери": "Chery",
    "джили": "Geely",
    "бид": "BYD",
}


def _normalize_brand(raw: str) -> str:
    """Нормализует название марки: RU→EN, красивое написание."""
    key = raw.lower().strip()
    # Точное совпадение
    if key in _RU_BRANDS:
        return _RU_BRANDS[key]
    # Частичное совпадение по первым 4 буквам
    if len(key) >= 4:
        for ru, en in _RU_BRANDS.items():
            if len(ru) >= 4 and key.startswith(ru[:4]):
                return en
    # Латинские аббревиатуры (3 буквы и меньше: BMW, KIA) — верхний регистр
    if re.fullmatch(r"[A-Za-z]{1,3}", key):
        return raw.strip().upper()
    # Латинское слово длиннее — Title Case
    if re.fullmatch(r"[A-Za-z0-9\- ]+", key):
        return raw.strip().title()
    # Ничего не нашли — вернуть с заглавной буквы
    return raw.strip().capitalize()


def parse_input(text: str) -> tuple[str, str] | None:
    """
    Разбирает строку, находит номер авто и марку.
    Поддерживает:
      - Смешанные токены: А322ВО77, A322BC777 → plate=А322ВО77
      - Только цифры: 322 toyota, toyota 322 → plate=322
    """
    text = text.strip()
    tokens = text.split()

    plate = None
    brand_tokens = []

    for token in tokens:
        # Смешанный токен (буквы + цифры) — кандидат на номер
        has_digits = bool(re.search(r"\d", token))
        has_letters = bool(re.search(r"[a-zA-Zа-яёА-ЯЁ]", token))
        if plate is None and has_digits and has_letters and len(token) >= 4:
            plate = token.upper()
        else:
            brand_tokens.append(token)

    # Если смешанного токена нет — ищем чистые цифры (3+)
    if plate is None:
        new_brand = []
        for token in brand_tokens:
            if plate is None and re.fullmatch(r"\d{3,}", token):
                plate = token
            else:
                new_brand.append(token)
        brand_tokens = new_brand

    if plate is None:
        return None

    brand_raw = " ".join(brand_tokens).strip()
    if not brand_raw:
        return None

    brand = _normalize_brand(brand_raw)
    return plate, brand
