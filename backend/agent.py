
import json
import os
import re

from intent_handler import extract_preferences, identify_intent
from response_generator import generate_response


# Load all restaurant JSON files from the JSON folder
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

                print("Loaded:", filename)

            except (json.JSONDecodeError, OSError) as error:
                print(f"Error loading {filename}: {error}")

    return coffee_shops


# Get the restaurant's location information
def get_restaurant_location(shop_data):

    if not isinstance(shop_data, dict):
        return ""

    locations = []

    # Standard location format
    location = shop_data.get("location", {})

    if isinstance(location, dict):

        locations.append(
            str(location.get("city", "")) + " " +
            str(location.get("state", ""))
        )

    # Top-level locations format
    top_locations = shop_data.get("locations", [])

    if isinstance(top_locations, dict):

        locations.append(
            str(top_locations.get("city", "")) + " " +
            str(top_locations.get("state", ""))
        )

    elif isinstance(top_locations, list):

        for place in top_locations:

            if isinstance(place, dict):

                locations.append(
                    str(place.get("name", "")) + " " +
                    str(place.get("address", ""))
                )

    # Boston Coffee nested locations format
    restaurant_info = shop_data.get("restaurant_info", {})

    if isinstance(restaurant_info, dict):

        boston_locations = restaurant_info.get("locations", [])

        if isinstance(boston_locations, list):

            for place in boston_locations:

                if isinstance(place, dict):

                    locations.append(
                        str(place.get("name", "")) + " " +
                        str(place.get("address", ""))
                    )

    return " ".join(locations).lower()


# Filter restaurants by location
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


# Extract menu items from different JSON structures
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

        # Price fields used by the restaurant JSON files
        price_keys = [
            "price",
            "price_usd",
            "price_each",
            "prices",
            "price_range_usd",
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

            # Search all supported menu containers
            menu_keys = [
                "categories",
                "subcategories",
                "items",
                "sections",
                "menu"
            ]

            for key in menu_keys:

                if key in data:

                    items.extend(
                        get_menu_items(
                            data[key],
                            new_path,
                            inherited_prices
                        )
                    )

    return items


# Get prices from menu items
def get_item_prices(item):

    prices = []

    # Standard price fields
    for key in ["price", "price_usd", "price_each"]:

        value = item.get(key)

        if isinstance(value, (int, float)):
            prices.append(float(value))

    # Handle different price formats
    price_data = item.get("prices", [])

    if isinstance(price_data, (int, float)):
        prices.append(float(price_data))

    elif isinstance(price_data, dict):

        for value in price_data.values():

            if isinstance(value, (int, float)):
                prices.append(float(value))

            elif isinstance(value, dict):

                for nested_value in value.values():

                    if isinstance(nested_value, (int, float)):
                        prices.append(float(nested_value))

    elif isinstance(price_data, list):

        for entry in price_data:

            if isinstance(entry, (int, float)):
                prices.append(float(entry))

            elif isinstance(entry, dict):

                for value in entry.values():

                    if isinstance(value, (int, float)):
                        prices.append(float(value))

    # Handle price ranges
    price_range = item.get("price_range_usd", {})

    if isinstance(price_range, dict):

        for value in price_range.values():

            if isinstance(value, (int, float)):
                prices.append(float(value))

    # Remove duplicate prices
    return sorted(set(prices))


# Get restaurant display name
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

    # Extract a location if one was not provided
    if not location:
        from intent_handler import extract_location
        location = extract_location(user_query)

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

    # Remove punctuation
    query_words = re.findall(r"[a-z0-9]+", query)

    ignored_words = {
        "where", "can", "i", "get", "find", "buy",
        "order", "some", "a", "an", "the", "please",
        "recommend", "recommendation", "would", "like",
        "want", "me", "is", "there", "any", "for",
        "near", "in", "at", "do", "you", "have",
        "coffee", "shop", "shops", "restaurant",
        "restaurants", "under", "below", "less",
        "than", "up", "to", "dollar"
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

            # Match individual search words
            for word in search_words:

                if word in searchable_text:
                    score += 2

            # Give extra points for an exact menu item match
            item_name = str(item.get("name", "")).lower()

            if item_name and item_name in query:
                score += 8

            # Give extra points when all search words match the item name
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

            # Keep items that match the search
            if score > 0:
                all_items.append(item)

    # Sort by relevance
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

    # Send recommendations to the response generator
    return generate_response(
        user_query,
        recommendations
    )


# Test all four JSON files
if __name__ == "__main__":

    shops = load_coffee_data()

    print("\nJSON FILES LOADED:")

    for shop_name in shops:
        print("-", shop_name)

    print("\nMENU ITEM COUNTS:")

    for shop_name, shop_data in shops.items():

        menu_items = get_menu_items(shop_data)

        print(
            shop_name,
            ":",
            len(menu_items),
            "menu items"
        )

    print("\nTEST RECOMMENDATION:")

    print(
        search_and_recommend(
            "Recommend a mocha"
        )
    )
