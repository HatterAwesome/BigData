
# This file takes recommendations and turns them into
# a readable, user-friendly chatbot response.


def generate_response(user_input, recommendations):
    """
    Generates a conversational response based on the user's
    question and the coffee shop recommendations.

    Parameters:
        user_input (str): The customer's original question.
        recommendations (list): Menu recommendations returned by agent.py.

    Returns:
        str: A formatted response for the chatbot.
    """

    # Check if any recommendations were found
    if not recommendations:

        return (
            "I'm sorry, I couldn't find any coffee shops "
            "that match your request. Try asking another question!"
        )

    # Start building the response
    response = "☕ Here are some recommendations for you:\n\n"

    # Format each recommendation
    for item in recommendations:

        # Get restaurant name
        shop_name = item.get(
            "_shop",
            item.get("restaurant", "Unknown Coffee Shop")
        )

        # Get menu item name
        item_name = item.get(
            "name",
            "Menu item"
        )

        response += f"**{item_name}**\n"

        response += f"Restaurant: {shop_name}\n"

        # Include category
        category = item.get("_category")

        if category:
            response += f"Category: {category}\n"

        # Include description
        description = item.get("description")

        if description:
            response += f"Description: {description}\n"

        # Include price
        prices = []

        for key in ["price", "price_usd", "price_each"]:

            value = item.get(key)

            if isinstance(value, (int, float)):
                prices.append(float(value))

        if prices:

            price_text = ", ".join(
                f"${price:.2f}" for price in sorted(set(prices))
            )

            response += f"Price: {price_text}\n"

        response += "\n---\n\n"

    return response.strip()
