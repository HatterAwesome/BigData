
import json
import os
import re

from intent_handler import extract_preferences, identify_intent


# Load all restaurant JSON files
def load_coffee_data():

    json_folder = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "JSON"
    )

    coffee_shops = {}

    if not os.path.exists(json_folder):
        print("JSON folder not found:", json_folder)
        return coffee_shops

    for filename in os.listdir(json_folder):

        if filename.lower().endswith(".json"):

            file_path = os.path.join(json_folder, filename)

            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    data = json.load(file)

                shop_name = os.path.splitext(filename)[0].lower()
                coffee_shops[shop_name] = data

            except (json.JSONDecodeError, OSError) as error:
                print(f"Error loading {filename}: {error}")

    return coffee_shops


# Get a restaurant's location from its JSON data
def get_restaurant_location(shop_data):

    if not isinstance(shop_data, dict):
        return ""

    # Original JSON location format
    location = shop_data.get("location", {})

    if isinstance(location, dict):

        city = location.get("city", "")
        state = location.get("state", "")

        if city or state:
            return f"{city} {state}".lower()

    # Expanded Starbucks JSON location format
    locations = shop_data.get("locations", {})

    if isinstance(locations, dict):

        city = locations.get("city", "")
        state = locations.get("state", "")

        return f"{city} {state}".lower()

    return str(location).lower()


# Filter restaurants by requested location
def filter_restaurants_by_location(shops, location):

    if not location:
        return shops

    matching_shops = {}
    requested_location = location.lower().strip()

    for shop_name, shop_data in shops.items():

        restaurant_location = get_restaurant_location(shop_data)

        if requested_location in restaurant_location:
            matching_shops[shop_name] = shop_data

    return matching_shops


# Extract menu items from restaurant data
def get_menu_items(data, category_path=None, inherited_prices=None):

    if category_path is None:
        category_path = []

    if inherited_prices is None:
        inherited_prices = []

    items = []

    if isinstance(data, list):

        for entry in data:
            items.extend(
                get_menu_items(
                    entry,
                    category_path,
                    inherited_prices
                )
            )

    elif isinstance(data, dict):

        name = data.get("name")

        # Support multiple menu price formats
        price_keys = [
            "price",
            "price_usd",
            "prices",
            "price_each",
            "available_as",
            "flavors"
        ]

        is_menu_item = (
            isinstance(name, str)
            and any(key in data for key in price_keys)
            and "items" not in data
            and "subcategories" not in data
        )

        if is_menu_item:

            item = data.copy()
            item["_category"] = " > ".join(category_path)
            item["_prices"] = inherited_prices.copy()

            items.append(item)

        else:

            new_path = category_path.copy()

            if name:
                new_path.append(name)

            # Search nested menu sections and categories
            for key, value in data.items():

                if key in [
                    "items",
                    "subcategories",
                    "sections"
                ]:

                    items.extend(
                        get_menu_items(
                            value,
                            new_path,
                            inherited_prices
                        )
                    )

                elif key == "menu":

                    items.extend(
                        get_menu_items(
                            value,
                            new_path,
                            inherited_prices
                        )
                    )

    return items


# Get prices from menu items
def get_item_prices(item):

    prices = []

    # Standard price fields, including Starbucks price_usd
    for key in ["price", "price_usd", "price_each"]:

        value = item.get(key)

        if isinstance(value, (int, float)):
            prices.append(float(value))

    # Handle multiple price formats
    price_data = item.get("prices", [])

    if isinstance(price_data, (int, float)):
        prices.append(float(price_data))

    elif isinstance(price_data, dict):

        for value in price_data.values():

            if isinstance(value, (int, float)):
                prices.append(float(value))

    elif isinstance(price_data, list):

        for entry in price_data:

            if isinstance(entry, (int, float)):
                prices.append(float(entry))

            elif isinstance(entry, dict):

                for value in entry.values():

                    if isinstance(value, (int, float)):
                        prices.append(float(value))

    # Handle inherited prices
    for value in item.get("_prices", []):

        if isinstance(value, (int, float)):
            prices.append(float(value))

    return list(set(prices))


# Get the restaurant's display name
def get_restaurant_name(shop_name, shop_data):

    if isinstance(shop_data, dict):

        restaurant = shop_data.get("restaurant")

        if restaurant:
            return restaurant

        menu = shop_data.get("menu", {})

        if isinstance(menu, dict):

            title = menu.get("title", "")

            if title:
                return title.replace("Menu - ", "").strip()

    return shop_name.replace("_", " ").replace("-", " ").title()


# Search and recommend menu items
def search_and_recommend(user_query, location=None):

    shops = load_coffee_data()

    if not shops:
        return "Sorry, I couldn't find any restaurant databases."

    # Filter restaurants by requested location
    if location:

        shops = filter_restaurants_by_location(
            shops,
            location
        )

        if not shops:
            return (
                f"Sorry, I couldn't find any restaurants "
                f"in {location}. Please try another location."
            )

    # Extract customer preferences
    preferences = extract_preferences(user_query)

    query = user_query.lower()

    # Remove punctuation and common question words
    query_words = re.findall(r"[a-z0-9]+", query)

    ignored_words = {
        "where", "can", "i", "get", "find", "buy",
        "order", "some", "a", "an", "the", "please",
        "recommend", "recommendation", "would", "like",
        "want", "me", "is", "there", "any", "for",
        "near", "in", "at", "do", "you", "have"
    }

    search_words = [
        word for word in query_words
        if word not in ignored_words and len(word) > 1
    ]

    all_items = []

    # Search every restaurant that matches the location
    for shop_name, shop_data in shops.items():

        restaurant_name = get_restaurant_name(
            shop_name,
            shop_data
        )

        menu_items = get_menu_items(shop_data)

        for item in menu_items:

            item["_shop"] = restaurant_name

            searchable_text = " ".join([
                str(item.get("name", "")),
                str(item.get("description", "")),
                str(item.get("_category", "")),
                str(item.get("flavors", ""))
            ]).lower()

            searchable_text = searchable_text.replace("-", " ")

            score = 0

            # Match individual words
            for word in search_words:

                if word in searchable_text:
                    score += 2

            # Give extra points for matching the full phrase
            item_name = str(item.get("name", "")).lower()

            if item_name and item_name in query:
                score += 8

            # Match the requested words against the item name
            if search_words:

                matched_name_words = sum(
                    1 for word in search_words
                    if word in item_name
                )

                if matched_name_words == len(search_words):
                    score += 5

            # Apply maximum price preference
            prices = get_item_prices(item)
            max_price = preferences.get("max_price")

            if max_price is not None:

                if not prices or min(prices) > max_price:
                    continue

            # Apply flavor preferences
            for flavor in preferences.get("flavors", []):

                if flavor.lower() in searchable_text:
                    score += 3

            item["_score"] = score

            # Only keep items that actually match the query
            if score > 0:
                all_items.append(item)

    # Sort recommendations by relevance
    all_items.sort(
        key=lambda item: item["_score"],
        reverse=True
    )

    if not all_items:
        return (
            "I couldn't find a matching menu item"
            + (f" in {location}." if location else ".")
            + " Try searching for a different drink or food item."
        )

    # Select the best item from each restaurant first
    recommendations = []
    selected_restaurants = set()

    for item in all_items:

        restaurant = item["_shop"]

        if restaurant not in selected_restaurants:

            recommendations.append(item)
            selected_restaurants.add(restaurant)

        if len(recommendations) == 4:
            break

    # Format recommendations for Streamlit
    response = "☕ **Coffee Recommendations**\n\n"

    for item in recommendations:

        response += f"### {item.get('name', 'Menu Item')}\n"

        response += (
            f"**Restaurant:** {item.get('_shop', 'Unknown')}\n\n"
        )

        if item.get("_category"):
            response += (
                f"**Category:** {item['_category']}\n\n"
            )

        if item.get("description"):
            response += (
                f"**Description:** {item['description']}\n\n"
            )

        prices = get_item_prices(item)

        if prices:
            response += (
                "**Price:** "
                + ", ".join(
                    f"${price:.2f}" for price in sorted(prices)
                )
                + "\n\n"
            )

        response += "---\n\n"

    return response
