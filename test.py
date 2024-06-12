import locale
from datetime import datetime
from typing import Optional
import bs4
import requests
import sqlite3

locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")

def get_html(url) -> Optional[str]:
    response = requests.get(url)
    if response.status_code == 200:
        return response.text
    return None

def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%d.%m.%Y").date()

def parse_moon_landings(url: str) -> list[dict]:
    html = get_html(url)
    soup = bs4.BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="wikitable")
    rows = table.find_all("tr")

    data = []

    for row in rows[1:]:
        cells = row.find_all("td")
        if len(cells) >= 5:
            country_cell = cells[1]
            country_links = country_cell.find_all("a")
            countries = [link.text.strip() for link in country_links]
            landing_date = parse_date(cells[3].text.strip())
            data_dict = {
                "name": cells[0].text.strip(),
                "countries": countries,
                "location": cells[2].text.strip(),
                "landing_date": landing_date
            }
            data.append(data_dict)
    return data

URL = "https://ru.wikipedia.org/wiki/%D0%A1%D0%BF%D0%B8%D1%81%D0%BE%D0%BA_%D0%BF%D1%80%D0%B8%D0%BB%D1%83%D0%BD%D0%B5%D0%BD%D0%B8%D0%B9#%D0%A1%D0%BF%D0%B8%D1%81%D0%BE%D0%BA_%D0%BC%D1%8F%D0%B3%D0%BA%D0%B8%D1%85_%D0%BF%D0%BE%D1%81%D0%B0%D0%B4%D0%BE%D0%BA"

CREATE_COUNTRIES = """CREATE TABLE IF NOT EXISTS countries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);"""

CREATE_MOON_LANDINGS = """CREATE TABLE IF NOT EXISTS moon_landings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    landing_date DATE NOT NULL
);"""

CREATE_COUNTRY_LANDINGS = """CREATE TABLE IF NOT EXISTS country_landings (
    country_id INTEGER,
    landing_id INTEGER,
    FOREIGN KEY (country_id) REFERENCES countries(id),
    FOREIGN KEY (landing_id) REFERENCES moon_landings(id),
    PRIMARY KEY (country_id, landing_id)
);"""

INSERT_COUNTRY = """INSERT INTO countries (name) VALUES (?);"""

INSERT_LANDING = """INSERT INTO moon_landings (name, location, landing_date) VALUES (?, ?, ?);"""

INSERT_COUNTRY_LANDING = """INSERT INTO country_landings (country_id, landing_id) VALUES (?, ?);"""

if __name__ == "__main__":
    conn = sqlite3.connect("moon_landings.db")
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS countries;")
    cursor.execute("DROP TABLE IF EXISTS moon_landings;")
    cursor.execute("DROP TABLE IF EXISTS country_landings;")
    cursor.execute(CREATE_COUNTRIES)
    cursor.execute(CREATE_MOON_LANDINGS)
    cursor.execute(CREATE_COUNTRY_LANDINGS)

    data = parse_moon_landings(URL)

    for d in data:
        cursor.execute(INSERT_LANDING, (d["name"], d["location"], d["landing_date"]))
        landing_id = cursor.lastrowid

        for country in d["countries"]:
            cursor.execute(INSERT_COUNTRY, (country,))
            country_id = cursor.lastrowid

            cursor.execute(INSERT_COUNTRY_LANDING, (country_id, landing_id))

    conn.commit()


    N = 5
    top_countries_query = """
        SELECT countries.name, COUNT(country_landings.landing_id) AS landing_count
        FROM countries
        JOIN country_landings ON countries.id = country_landings.country_id
        GROUP BY countries.name
        ORDER BY landing_count DESC
        LIMIT ?;
    """
    top_countries_result = cursor.execute(top_countries_query, (N,))
    print(f"Топ {N} стран по числу прилунений:")
    for idx, (country, landing_count) in enumerate(top_countries_result, start=1):
        print(f"{idx}. {country}: {landing_count} прилунений")

    landings_by_country_query = """
        SELECT countries.name, moon_landings.name, moon_landings.location, moon_landings.landing_date
        FROM countries
        JOIN country_landings ON countries.id = country_landings.country_id
        JOIN moon_landings ON country_landings.landing_id = moon_landings.id
        ORDER BY countries.name;
    """
    landings_by_country_result = cursor.execute(landings_by_country_query)
    print("\nПрилунения с группировкой по странам:")
    for country, landing_name, location, landing_date in landings_by_country_result:
        print(f"Страна: {country}, Название прилунения: {landing_name}, Место: {location}, Дата: {landing_date}")

    landings_by_location_query = """
        SELECT moon_landings.location, COUNT(moon_landings.id) AS landing_count
        FROM moon_landings
        GROUP BY moon_landings.location
        ORDER BY landing_count DESC;
    """
    landings_by_location_result = cursor.execute(landings_by_location_query)
    print("\nПрилунения с группировкой по местам:")
    for idx, (location, landing_count) in enumerate(landings_by_location_result, start=1):
        print(f"{idx}. {location}: {landing_count} прилунений")
