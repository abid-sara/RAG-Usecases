import json
import os

class JsonAppender:
    """
    A class to append JSON objects to a file containing a JSON list.
    """
    def __init__(self, file_path):
        """
        Initializes the JsonAppender with the target file path.

        Args:
            file_path (str): The path to the JSON file.
        """
        self.file_path = file_path

    def append(self, json_object):
        """
        Appends a JSON object (Python dictionary) to the file.

        Args:
            json_object (dict): The Python dictionary to append.

        Returns:
            bool: True if appending was successful, False otherwise.
        """
        data = []
        try:
            # Check if file exists and is not empty
            if os.path.exists(self.file_path) and os.path.getsize(self.file_path) > 0:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    try:
                        data = json.load(f)
                        # Ensure the loaded data is a list
                        if not isinstance(data, list):
                            print(f"Error: Existing content in {self.file_path} is not a JSON list. Initializing with an empty list.")
                            data = []
                    except json.JSONDecodeError:
                        print(f"Error: Could not decode JSON from {self.file_path}. Initializing with an empty list.")
                        data = [] # Start with an empty list if file is corrupted or not valid JSON
            else:
                 # If file doesn't exist or is empty, initialize with empty list
                 print(f"File {self.file_path} not found or empty. Creating a new list.")
                 data = []


            # Append the new object
            data.append(json_object)

            # Write the updated list back to the file
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True

        except IOError as e:
            print(f"Error accessing file {self.file_path}: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return False