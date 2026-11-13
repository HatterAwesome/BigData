# This file takes the recommendations and turns them into
# a readable, user-friendly response.
def generate_response(user_input, recommendations):
    """
    Generates a conversational response based on the user's
    question and the coffee shop recommendations.

    Parameters:
        user_input (str): The customer's original question.
        recommendations (list): Coffee shop recommendations returned by agent.py.

    Returns:
        str: A formatted response for the chatbot.
    """

    # 1. Check if any recommendations were found
    if not recommendations:
        return (
            "I'm sorry, I couldn't find any coffee shops "
            "that match your request. Try asking another question!"
        )

    # 2. Start building the response
    response = "Here are some coffee shops I would recommend:\n\n"

    # 3. Format each recommendation
    for shop in recommendations:

        # Get the coffee shop name
        shop_name = shop.get("restaurant", "Unknown Coffee Shop")

        # Add the coffee shop to the response
        response += f"☕ {shop_name}\n"

        # Include a reason if one was provided
        reason = shop.get("reason")

        if reason:
            response += f"{reason}\n"

        # Include additional details if available
        description = shop.get("description")

        if description:
            response += f"{description}\n"

        response += "\n"

    # 4. Return the completed response
    return response.strip()
