# Bundesliga Coach Info Bot

## Overview
This Python command-line tool provides live information about the current coaches of German Bundesliga football clubs.  
It dynamically retrieves data from Wikidata and Wikipedia APIs based on user queries about cities or clubs.

## Features
- Understands natural, colloquial questions like "Who is Bayerns coach?" or "Who is it for Pauli?"
- Retrieves club and city data including aliases using SPARQL queries on Wikidata
- Matches queries flexibly, handling possessives and partial names
- Retrieves current coach data from Wikidata with language and regex filtering
- Fetches English introductory paragraphs about coaches from Wikipedia
- Handles special cases for clubs like FC St. Pauli
- Provides prompt strings suitable for use with language models

## Requirements
- Python 3.8 or higher
- `requests` library (install via `pip install requests`)

## Usage
Run the chatbot from your terminal/command prompt:

python coach_chatbot.py


## Prompt questions
Enter your questions about Bundesliga club coaches, for example:
- Who is coaching Berlin?
- Who is Bayerns coach?
- Who is it for Pauli?
- Who is Frankfurts manager?

Type `exit` to quit.

## Design and Implementation
- Uses SPARQL queries to dynamically fetch clubs, cities, and coaching staff from Wikidata, including handling alternative labels.
- Implements text normalization and regex pattern preparation for flexible and reliable matching.
- Fetches Wikipedia extracts to enrich coach descriptions.
- Logs errors and handles missing data gracefully.





---

Thank you for reviewing this project!
