import json
import os

def load_coffee_data():
    """Loads and normalizes all shop JSON files from backend/JSON/"""
    data = {}
    paths_to_try = ["backend/JSON", "JSON", "./JSON"]
    
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
                with open(filepath, "r") as f:
                    data[shop_key] = json.load(f)
            except Exception:
                pass
                
    return data

def search_and_recommend(user_query: str):
    """Parses JSON files, scores each cafe based on user query keywords, 
    and generates a tailored recommendation."""
    shops = load_coffee_data()
    if not shops:
        return "⚠️ Error: Could not load JSON files from `backend/JSON/`."
        
    query = user_query.lower()
    scores = {shop: 0 for shop in shops}
    matched_reasons = {shop: [] for shop in shops}
    
    # Keyword Scoring Engine
    keywords = {
        "study": ["study", "laptop", "wifi", "work", "quiet", "sit", "seating", "table"],
        "drivethru": ["drive", "thru", "fast", "quick", "car", "speed", "rush"],
        "craft": ["craft", "pour over", "roast", "espresso", "artisanal", "beans", "single origin"],
        "budget": ["cheap", "budget", "price", "affordable", "deal", "donut", "breakfast"]
    }
    
    # 1. Parse query and calculate shop scores dynamically
    for category, terms in keywords.items():
        if any(term in query for term in terms):
            for shop_name, content in shops.items():
                content_str = str(content).lower()
                for term in terms:
                    if term in content_str:
                        scores[shop_name] += 2
                        matched_reasons[shop_name].append(term)
                        
    # Sort shops by top score
    ranked_shops = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_shop_key, top_score = ranked_shops[0]
    
    # 2. Format Response using actual JSON data fields
    top_shop_data = shops.get(top_shop_key, {})
    shop_display_name = top_shop_key.replace("_", " ").title()
    
    if top_score > 0:
        response = f"🎯 **Top Match Based on Your Search:** **{shop_display_name}**\n\n"
        
        if isinstance(top_shop_data, dict):
            if "description" in top_shop_data:
                response += f"• **Overview:** {top_shop_data['description']}\n"
            if "address" in top_shop_data or "location" in top_shop_data:
                loc = top_shop_data.get("address") or top_shop_data.get("location")
                response += f"• **Location:** {loc}\n"
            if "popular_items" in top_shop_data or "menu" in top_shop_data:
                items = top_shop_data.get("popular_items") or top_shop_data.get("menu")
                response += f"• **Featured Menu Items:** {items}\n"
                
        response += f"\n*(Scored against **{len(shops)}** JSON files in `backend/JSON/`)*"
    else:
        response = (
            f"🔍 **DeLand Coffee Assistant:** I searched across all {len(shops)} coffee shop profiles (`{', '.join([s.title() for s in shops.keys()])}`).\n\n"
            "Tell me a bit more about what you're looking for! For example:\n"
            "• *\"Where is a good spot to sit with a laptop and study?\"*\n"
            "• *\"I need a quick drive-thru iced latte.\"*\n"
            "• *\"Who has the best locally roasted craft coffee?\"*"
        )
        
    return response
