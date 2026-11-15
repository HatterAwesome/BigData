
# Connect the existing backend files
from agent import search_and_recommend
from intent_handler import (
    identify_intent,
    extract_preferences,
    identify_keywords,
    extract_location
)


def get_chatbot_response(user_query):
    """
    Processes the customer's message using the intent handler
    and generates a coffee shop recommendation using the agent.
    """

    # Step 1: Understand what the customer is asking
    intent = identify_intent(user_query)

    # Step 2: Extract customer preferences
    preferences = extract_preferences(user_query)

    # Step 3: Identify relevant keywords
    keywords = identify_keywords(user_query)

    # Step 4: Identify the requested location
    location = extract_location(user_query)

    # Step 5: Get recommendations from the agent
    recommendation = search_and_recommend(
        user_query,
        location=location
    )

    # Step 6: Return the response and extracted information
    return {
        "response": recommendation,
        "intent": intent,
        "preferences": preferences,
        "keywords": keywords,
        "location": location
    }
