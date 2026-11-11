
import re

# Keywords used to identify customer requests
INTENTS = {
    "study": ["study", "laptop", "wifi", "wi-fi", "quiet", "seating", "work"],
    "drivethru": ["drive thru", "drive-thru", "quick", "fast", "on the go"],
    "craft": ["craft", "pour over", "roast", "espresso", "artisanal", "beans"],
    "budget": ["cheap", "budget", "affordable", "inexpensive", "deal"],
    "price": ["price", "cost", "how much"],
    "menu": ["menu", "drinks", "food", "offers", "serves"],
    "compare": ["compare", "versus", "vs", "difference"],
    "drink_recommendation": ["recommend", "suggest", "latte", "cappuccino", "cold brew", "mocha", "iced coffee"]
}

FLAVORS = [
    "caramel", "vanilla", "mocha", "hazelnut",
    "chocolate", "strawberry", "pumpkin", "cinnamon"
]

DIETARY = ["dairy free", "vegan", "gluten free", "sugar free"]

# Finds the customer's main request
def identify_intent(user_query):
    query = user_query.lower()

    for intent, keywords in INTENTS.items():
        if any(word in query for word in keywords):
            return intent

    return "general"


# Extracts preferences from the customer's message
def extract_preferences(user_query):
    query = user_query.lower()

    price_match = re.search(
        r"(?:under|below|less than|up to)\s*\$?\s*(\d+(?:\.\d{1,2})?)",
        query
    )

    return {
        "temperature": (
            "Iced" if any(x in query for x in ["iced", "cold"])
            else "Hot" if any(x in query for x in ["hot", "warm"])
            else None
        ),
        "flavors": [x for x in FLAVORS if x in query],
        "dietary": [x for x in DIETARY if x in query],
        "caffeine": (
            "Decaf" if any(x in query for x in ["decaf", "no caffeine"])
            else "Low Caffeine" if "low caffeine" in query
            else None
        ),
        "max_price": float(price_match.group(1)) if price_match else None,
        "seating": any(x in query for x in ["sit", "seating", "study", "work"]),
        "wifi": any(x in query for x in ["wifi", "wi-fi", "internet"])
    }


# Finds relevant keywords in the customer's message
def identify_keywords(user_query):
    query = user_query.lower()
    keywords = [word for words in INTENTS.values() for word in words]
    keywords += FLAVORS + DIETARY

    return list(dict.fromkeys(
        word for word in keywords if word in query
    ))
