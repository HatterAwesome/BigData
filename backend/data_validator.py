
# Makes sure your coffee shop data is usable
# Checks JSON files

import json
import os


# Validate the coffee shop JSON files
def validate_coffee_shops():

    json_folder = os.path.join(os.path.dirname(__file__), "JSON")

    # Check if JSON folder exists
    if not os.path.exists(json_folder):
        print("Error: JSON folder was not found.")
        return False

    # Get all JSON files
    json_files = [
        file for file in os.listdir(json_folder)
        if file.endswith(".json")
    ]

    if not json_files:
        print("Error: No JSON files found.")
        return False

    all_valid = True

    # Check each JSON file
    for file_name in json_files:

        file_path = os.path.join(json_folder, file_name)

        print(f"\nChecking: {file_name}")

        try:
            # Load JSON data
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            # Check if the file contains data
            if not data:
                print("Error: JSON file is empty.")
                all_valid = False
                continue

            # Get the coffee shop locations
            if isinstance(data, dict):

                restaurant_info = data.get("restaurant_info", {})
                locations = restaurant_info.get("locations", [])

                if locations:
                    shops = locations

                elif "name" in data:
                    shops = [data]

                else:
                    print("Error: No coffee shop locations or name found.")
                    all_valid = False
                    continue

            elif isinstance(data, list):
                shops = data

            else:
                print("Error: Unexpected JSON structure.")
                all_valid = False
                continue

            # Check each coffee shop
            file_valid = True

            for index, shop in enumerate(shops):

                if not isinstance(shop, dict):
                    print(f"Error: Entry {index + 1} is not an object.")
                    file_valid = False
                    continue

                # Check coffee shop name
                if not isinstance(shop.get("name"), str) or not shop["name"].strip():
                    print(f"Error: Entry {index + 1} has an invalid name.")
                    file_valid = False

                # Check address
                if not isinstance(shop.get("address"), str) or not shop["address"].strip():
                    print(f"Warning: Entry {index + 1} has no address.")

            if file_valid:
                print("Validation successful!")
                print("Locations checked:", len(shops))
            else:
                print("Validation failed.")
                all_valid = False

        except json.JSONDecodeError as error:
            print("Error: Invalid JSON formatting.")
            print(error)
            all_valid = False

        except OSError as error:
            print("Error reading file:", error)
            all_valid = False

    # Display final results
    print("\n----- VALIDATION RESULTS -----")

    if all_valid:
        print("All JSON files passed validation!")
    else:
        print("Some JSON files need to be fixed.")

    return all_valid


# Run validation
if __name__ == "__main__":
    validate_coffee_shops()
