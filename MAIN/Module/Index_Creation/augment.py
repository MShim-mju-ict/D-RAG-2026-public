import json
import re
from MAIN.Module.Metadata_Augmentation.metadata_aug import augment_metadata1, augment_metadata2

def augment_document(data):
    """
    Augments a single document dictionary with metadata.

    :param data: The original document dictionary.
    :return: The augmented document dictionary.
    """
    try:
        # Extract only specific fields for augmentation
        fields_to_extract = ["name", "alternateName", "description", "keywords"]
        extracted_data = {key: data.get(key) for key in fields_to_extract if key in data}
        
        # Get augmentation from external function using only the extracted fields
        json_string = json.dumps(extracted_data, ensure_ascii=False)

        ## CHANGE AUG MODEL HERE *******
        # augmented_metadata = augment_metadata1(json_string)
        augmented_metadata = augment_metadata2(json_string)
        
        # Ensure augmented_metadata is a string before cleaning
        if not isinstance(augmented_metadata, str):
            # If the API returns a non-string (like None or an error object), handle it
            print(f"Warning: Metadata augmentation returned a non-string value: {augmented_metadata}. Skipping cleaning.")
            augmented_metadata = "" # Default to an empty string to avoid crashing re.sub

        # 1. Clean the string: remove ", \, /, newlines
        cleaned = re.sub(r'[\"\\/\n\[\]\,]', ' ', augmented_metadata)
        
        # Replace multiple spaces with a single space
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # 2. Split by space into words
        words = cleaned.split(' ')
        
        # 3. Only keep unique words (preserve order by using dict.fromkeys)
        unique_words = list(dict.fromkeys(words))
        
        # Add new field as a list of words instead of a string
        data["augmeta"] = unique_words
        return data

    except Exception as e:
        print(f"Error augmenting document: {str(e)}")
        return data