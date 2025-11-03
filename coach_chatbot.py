import requests
import re
import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_wikipedia_intro(title):
    """Fetch Wikipedia intro paragraph for given title."""
    wiki_api_url = "https://en.wikipedia.org/w/api.php"
    params = {
        "format": "json",
        "action": "query",
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "titles": title
    }
    headers = {
        "User-Agent": "BundesligaCoachBot/1.0 (https://example.org/; contact@example.org)"
    }
    try:
        response = requests.get(wiki_api_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        page = next(iter(pages.values()))
        return page.get("extract", "No biography intro found on Wikipedia.")
    except requests.RequestException as e:
        logging.error(f"Wikipedia request failed: {e}")
        return "Wikipedia data not available."


def query_wikidata_for_names():
    """Retrieve German Bundesliga clubs and cities including aliases."""
    sparql_query = """
    SELECT DISTINCT ?club ?clubLabel ?altClubLabel ?city ?cityLabel ?altCityLabel WHERE {
      ?club wdt:P31 wd:Q476028;
            wdt:P118 wd:Q82595;
            wdt:P159 ?city.
      ?city wdt:P31/wdt:P279* wd:Q515.
      ?city wdt:P17 wd:Q183.

      ?club rdfs:label ?clubLabel.
      FILTER (LANG(?clubLabel) = "en")

      ?city rdfs:label ?cityLabel.
      FILTER (LANG(?cityLabel) = "en")

      OPTIONAL {
        ?club skos:altLabel ?altClubLabel.
        FILTER(LANG(?altClubLabel) = "en")
      }
      OPTIONAL {
        ?city skos:altLabel ?altCityLabel.
        FILTER(LANG(?altCityLabel) = "en")
      }
    }
    """
    url = "https://query.wikidata.org/sparql"
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "BundesligaCoachBot/1.0 (https://example.org/; contact@example.org)"
    }
    try:
        response = requests.get(url, params={'query': sparql_query}, headers=headers)
        response.raise_for_status()
        data = response.json()
        clubs = {}
        cities = {}
        for item in data.get("results", {}).get("bindings", []):
            club_label = item.get("clubLabel", {}).get("value")
            alt_club_label = item.get("altClubLabel", {}).get("value")
            city_label = item.get("cityLabel", {}).get("value")
            alt_city_label = item.get("altCityLabel", {}).get("value")

            if club_label:
                clubs[normalize_text(club_label)] = club_label
            if alt_club_label:
                clubs[normalize_text(alt_club_label)] = club_label
            if city_label:
                cities[normalize_text(city_label)] = city_label
            if alt_city_label:
                cities[normalize_text(alt_city_label)] = city_label

        return clubs, cities
    except requests.RequestException as e:
        logging.error(f"Wikidata request failed: {e}")
        return {}, {}


def normalize_text(text):
    """Normalize text (lowercase, strip possessives)."""
    text = text.lower().strip()
    text = re.sub(r"(?:'s|s)$", "", text)
    return text


def extract_entity_from_input(user_input, clubs, cities):
    """Extract the most appropriate club or city label from user input."""
    user_input_norm = normalize_text(user_input)

    # Handle special case "pauli" mapping to "st. pauli"
    if "pauli" in user_input_norm:
        for club_norm, official_name in clubs.items():
            if "st. pauli" in club_norm:
                return official_name, True

    for club_norm, official_name in clubs.items():
        if club_norm in user_input_norm:
            return official_name, True

    for city_norm, official_name in cities.items():
        if city_norm in user_input_norm:
            return official_name, False

    return None, None


def prepare_regex_for_sparql(text):
    """
    Correctly escape string for SPARQL regex including double escape of backslashes.
    """
    escaped = text.replace('\\', '\\\\').replace('"', '\\"')
    escaped = re.sub(r'\s+', r'\\\\s+', escaped)  # double escape for SPARQL compatibility
    return escaped



def query_wikidata_for_coach(entity_label, is_club):
    """Query Wikidata using safe regex for club or city label match."""
    regex_pattern = prepare_regex_for_sparql(entity_label)
    if is_club:
        filter_clause = f'FILTER(LANG(?clubLabel) = "en" && REGEX(?clubLabel, "{regex_pattern}", "i"))'
    else:
        filter_clause = f'FILTER(LANG(?cityLabel) = "en" && REGEX(?cityLabel, "{regex_pattern}", "i"))'

    sparql = f"""
    SELECT DISTINCT ?clubLabel ?coachLabel ?cityLabel WHERE {{
      ?club wdt:P31 wd:Q476028;
            wdt:P118 wd:Q82595;
            wdt:P159 ?city.
      ?city wdt:P31/wdt:P279* wd:Q515;
            rdfs:label ?cityLabel.
      ?club rdfs:label ?clubLabel.
      ?club wdt:P286 ?coach.
      {filter_clause}
      FILTER NOT EXISTS {{ ?coach wdt:P582 ?endTime }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" }}
    }}
    """

    url = "https://query.wikidata.org/sparql"
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "BundesligaCoachBot/1.0 (https://example.org/; contact@example.org)"
    }
    try:
        response = requests.get(url, params={'query': sparql}, headers=headers)
        response.raise_for_status()
        data = response.json()
        bindings = data.get("results", {}).get("bindings", [])
        if not bindings:
            logging.info(f"No results found for {'club' if is_club else 'city'} regex '{entity_label}'.")
            return None, None
        # Special case handling for 'St. Pauli'
        if is_club and entity_label.lower() in ["pauli", "st. pauli"]:
            for entry in bindings:
                if "st. pauli" in entry['clubLabel']['value'].lower():
                    return entry['clubLabel']['value'], entry['coachLabel']['value']
        return bindings[0]['clubLabel']['value'], bindings[0]['coachLabel']['value']
    except requests.RequestException as e:
        logging.error(f"Wikidata SPARQL request failed: {e}")
        return None, None


def main():
    clubs, cities = query_wikidata_for_names()
    if not clubs or not cities:
        print("Could not retrieve clubs and cities data. Exiting.")
        return

    print("Bundesliga Coach Info Bot\n")
    print("Ask about current Bundesliga club coaches.")
    print("Example questions:")
    print(" - Who is coaching Berlin?")
    print(" - Who is it for Pauli?")
    print(" - Who is Frankfurts manager?")
    print(" - Who is Bayerns coach?")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("Your question: ").strip()
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        entity_label, is_club = extract_entity_from_input(user_input, clubs, cities)
        if not entity_label:
            print("No club or city name recognized in your question. Please try again.")
            continue

        club, coach = query_wikidata_for_coach(entity_label, is_club)
        if not club or not coach:
            print(f"Could not find coach information for '{entity_label}'. Try another query.")
            continue

        intro = get_wikipedia_intro(coach)

        prompt = (
            "System: You are a helpful assistant answering questions about the current coach "
            "of football clubs in Germany's 1. Bundesliga.\n"
            f"User question: {user_input}\n\n"
            f"Information retrieved:\n"
            f"Club: {club}\n"
            f"Coach: {coach}\n"
            f"Biography: {intro}\n"
        )

        print("\n" + prompt)
        print("-" * 80)


if __name__ == "__main__":
    main()
