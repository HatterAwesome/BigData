import json
import os

from intent_handler import extract_preferences, identify_intent


def load_coffee_data():
    """Loads and normalizes all shop JSON files from backend/JSON/"""
    data = {}
    paths_to_try = [
        os.path.join(os.path.dirname(__file__), "JSON"),
        "backend/JSON",
        "JSON",
        "./JSON"
    ]

    target_dir = None
    for p in paths_to_try:
        if os.path.exists(p):
            target_dir = p
            break

    if not target_dir:
        return {}

    for filename in os.listdir(target_dir):
        if filename.endswith(".json"):
            shop_key = filename.replace(".json", "").lower()
            filepath = os.path.join(target_dir, filename)

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data[shop_key] = json.load(f)
            except Exception as e:
                print(f"Error loading {filename}: {e}")

    return data


def get_menu_items(data, category_path=None, inherited_prices=None):
    """Extracts individual menu items from nested JSON categories."""

    if category_path is None:
        category_path = []

    if isinstance(data, list):
        items = []

        for entry in data:
            items.extend(
                get_menu_items(entry, category_path, inherited_prices)
            )

        return items

    if not isinstance(data, dict):
        return []

    items = []

    current_name = data.get("name")
    current_prices = data.get("size_prices", inherited_prices)

    # Identify actual menu items, not category containers
    is_menu_item = (
        current_name
        and not any(key in data for key in ["items", "subcategories"])
        and any(
            key in data
            for key in ["price", "prices", "price_each",
                        "available_as", "flavors"]
        )
        and "size_prices" not in data
    )

    if is_menu_item:
        menu_item = data.copy()
        menu_item["_category"] = " > ".join(category_path)
        menu_item["_prices"] = current_prices
        items.append(menu_item)

    # Add category names to the search context
    next_path = category_path

    if current_name and not is_menu_item:
        next_path = category_path + [current_name]

    # Search nested JSON fields
    for key, value in data.items():

        if key in ["size_prices", "price_completeness"]:
            continue

        if isinstance(value, (dict, list)):
            items.extend(
                get_menu_items(value, next_path, current_prices)
            )

    return items


def get_item_prices(item):
    """Gets all available prices for a menu item."""

    prices = []

    if isinstance(item.get("price"), (int, float)):
        prices.append(item["price"])

    if isinstance(item.get("price_each"), (int, float)):
        prices.append(item["price_each"])

    price_data = item.get("prices") or item.get("_prices") or []

    if isinstance(price_data, list):
        for option in price_data:
            if isinstance(option, dict):
                price = option.get("price")

                if isinstance(price, (int, float)):
                    prices.append(price)

    return prices


def search_and_recommend(user_query: str):
    """Searches nested coffee shop menus and recommends matching items."""

    shops = load_coffee_data()

    if not shops:
        return "⚠️ Error: Could not load JSON files from backend/JSON/."

    query = user_query.lower()

    intent = identify_intent(user_query)
    preferences = extract_preferences(user_query)

    # Collect all individual menu items
    all_items = []

    for shop_name, shop_data in shops.items():
        if isinstance(shop_data, dict):
            menu_items = get_menu_items(shop_data)

            for item in menu_items:
                item["_shop"] = shop_data.get(
                    "restaurant",
                    shop_name.replace("_", " ").title()
                )
                all_items.append(item)

    if not all_items:
        return "I couldn't find individual menu items in the JSON files."

    # Identify meaningful search terms
    stop_words = {
        "what", "are", "the", "is", "a", "an", "i", "want",
        "need", "have", "do", "you", "me", "some", "please",
        "recommend", "suggest", "find", "show", "give",
        "under", "below", "less", "than", "up", "to",
        "price", "cost", "much", "with", "for", "and",
        "or", "of", "in", "on", "at", "can", "get",
        "coffee", "drink", "drinks", "food", "menu", "item"
    }

    search_words = [
        word.strip(".,!?$") for word in query.split()
        if word.strip(".,!?$") not in stop_words
        and len(word.strip(".,!?$")) > 2
    ]

    max_price = preferences["max_price"]

    ranked_items = []

    for item in all_items:

        # Build searchable text from the entire item
        searchable_text = (
            str(item) + " " + str(item.get("_category", ""))
        ).lower()

        score = 0

        # Match customer keywords against menu information
        for word in search_words:
            if word in searchable_text:
                score += 2

        # Match customer flavors
        for flavor in preferences["flavors"]:
            if flavor in searchable_text:
                score += 4

        # Match the requested price
        prices = get_item_prices(item)

        if max_price is not None:

            affordable_prices = [
                price for price in prices
                if price <= max_price
            ]

            if not affordable_prices:
                continue

            score += 3

        if score > 0:
            ranked_items.append((score, item))

    # If no specific item matched, use the price filter
    # to find affordable options instead of asking again.
    if not ranked_items and max_price is not None:

        for item in all_items:
            prices = get_item_prices(item)

            if any(price <= max_price for price in prices):
                ranked_items.append((1, item))

    if not ranked_items:
        if any(word in query for word in [
            "study", "quiet", "wifi", "wi-fi", "seating",
            "drive", "drive-thru", "drive thru"
        ]):
            return (
                "I can search the Boston Coffee House menu, "
                "but the current JSON does not contain information "
                "about seating, Wi-Fi, noise levels, or drive-thru services."
                "\n\nTry asking me about drinks, flavors, food, or prices!"
            )

        return (
            "I couldn't find an exact menu match. "
            "Here are some things you can ask me:\n\n"
            "- Recommend a caramel drink.\n"
            "- What coffee is under $5?\n"
            "- Show me breakfast items under $8.\n"
            "- What iced drinks do you have?\n"
            "- What has vanilla flavor?"
        )

    # Sort by relevance
    ranked_items.sort(key=lambda x: x[0], reverse=True)

    # Keep the top three recommendations
    top_items = ranked_items[:3]

    restaurant_name = top_items[0][1]["_shop"]

    response = (
        f"☕ **Recommendations from {restaurant_name}**\n\n"
    )

    for score, item in top_items:

        name = item.get("name", "Unknown Item")
        category = item.get("_category", "")
        prices = get_item_prices(item)

        response += f"### {name}\n"

        if category:
            response += f"**Category:** {category}\n\n"

        description = item.get("description")

        if description:
            response += f"**Description:** {description}\n\n"

        flavors = item.get("flavors")

        if flavors:
            response += f"**Flavors:** {', '.join(flavors)}\n\n"

        if prices:
            price_options = (
                item.get("prices") or item.get("_prices") or []
            )

            if isinstance(price_options, list) and price_options:
                displayed = []

                for option in price_options:
                    if not isinstance(option, dict):
                        continue

                    price = option.get("price")

                    if not isinstance(price, (int, float)):
                        continue

                    if max_price is None or price <= max_price:
                        size = option.get("size", "")
                        displayed.append(
                            f"{size}: ${price:.2f}"
                            if size else f"${price:.2f}"
                        )

                if displayed:
                    response += (
                        "**Prices:** " + ", ".join(displayed) + "\n\n"
                    )
                else:
                    response += (
                        f"**Price:** ${min(prices):.2f}\n\n"
                    )

            else:
                affordable = [
                    price for price in prices
                    if max_price is None or price <= max_price
                ]

                if affordable:
                    response += (
                        f"**Price:** ${min(affordable):.2f}\n\n"
                    )

        elif item.get("price") is None:
            response += (
                "**Price:** Not listed on the supplied menu.\n\n"
            )

        response += "---\n\n"

    return response
