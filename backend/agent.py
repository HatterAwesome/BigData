import json
import os

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

        if filename.endswith(".json"):

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

    location = shop_data.get("location", "")

    if isinstance(location, dict):

        city = location.get("city", "")
        state = location.get("state", "")

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

    if isinstance(data, dict):

        name = data.get("name")

        if name and any(
            key in data for key in [
                "price", "prices", "price_each",
                "available_as", "flavors"
            ]
        ) and "items" not in data and "subcategories" not in data:

            item = data.copy()
            item["_category"] = " > ".join(category_path)
            item["_prices"] = inherited_prices

            items.append(item)

        for key, value in data.items():

            if key in ["items", "subcategories"]:

                if isinstance(value, list):

                    for entry in value:

                        if isinstance(entry, dict):

                            new_path = category_path.copy()

                            if entry.get("name"):
                                new_path.append(entry["name"])

                            items.extend(
                                get_menu_items(
                                    entry,
                                    new_path,
                                    inherited_prices
                                )
                            )

            elif isinstance(value, (dict, list)):

                items.extend(
                    get_menu_items(
                        value,
                        category_path,
                        inherited_prices
                    )
                )

    elif isinstance(data, list):

        for entry in data:

            items.extend(
                get_menu_items(
                    entry,
                    category_path,
                    inherited_prices
                )
            )

    return items


# Get prices from menu items
def get_item_prices(item):

    prices = []

    if isinstance(item.get("price"), (int, float)):
        prices.append(float(item["price"]))

    if isinstance(item.get("price_each"), (int, float)):
        prices.append(float(item["price_each"]))

    for price_data in item.get("prices", []):

        if isinstance(price_data, (int, float)):
            prices.append(float(price_data))

        elif isinstance(price_data, dict):

            for value in price_data.values():

                if isinstance(value, (int, float)):
                    prices.append(float(value))

    for price_data in item.get("_prices", []):

        if isinstance(price_data, (int, float)):
            prices.append(float(price_data))

    return prices


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

    all_items = []

    # Search every restaurant that matches the location
    for shop_name, shop_data in shops.items():

        restaurant_name = (
            shop_data.get("restaurant", shop_name)
            if isinstance(shop_data, dict)
            else shop_name
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

            score = 0

            for word in query.split():

                if len(word) > 2 and word in searchable_text:
                    score += 1

            # Apply maximum price preference
            prices = get_item_prices(item)
            max_price = preferences.get("max_price")

            if max_price is not None:

                if not prices or min(prices) > max_price:
                    continue

                score += 2

            # Apply flavor preferences
            for flavor in preferences.get("flavors", []):

                if flavor in searchable_text:
                    score += 3

            item["_score"] = score

            all_items.append(item)

    # Sort recommendations by relevance
    all_items.sort(
        key=lambda item: item["_score"],
        reverse=True
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

    # No matching menu items
    if not recommendations:
        return (
            "I couldn't find matching menu items "
            + (f"in {location}." if location else ".")
        )

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
                + ", ".join(f"${price:.2f}" for price in prices)
                + "\n\n"
            )

        response += "---\n\n"

    return response
