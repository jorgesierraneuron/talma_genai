import os
import re
import pandas as pd
from PyPDF2 import PdfReader

def count_tokens_in_all_files(directory, output_csv):
    """
    Reads all files in the specified directory, counts tokens for each file, 
    and exports a CSV with file name and token count.

    Parameters:
        directory (str): The path to the directory containing files.
        output_csv (str): The path to save the output CSV file.
    """
    # Initialize an empty list to store results
    results = []

    # Iterate through all files in the directory
    for file_name in os.listdir(directory):
        file_path = os.path.join(directory, file_name)
        
        try:
            # Read file content based on file type
            if file_name.endswith('.pdf'):
                # Process PDF files
                reader = PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
            else:
                # Process other text-based files
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                    text = file.read()

            # Tokenize the text by splitting on whitespace
            tokens = re.findall(r'\w+', text)
            token_count = len(tokens)

            # Append results to the list
            results.append({
                'file_name': file_name,
                'number_of_tokens': token_count
            })
        except Exception as e:
            print(f"Error processing {file_name}: {e}")

    # Create a DataFrame from the results
    df = pd.DataFrame(results)

    # Export the DataFrame to a CSV file
    df.to_csv(output_csv, index=False)
    print(f"Token counts exported to {output_csv}")

# Example usage
directory_path = "manuales"
output_csv_path = "output.csv"
count_tokens_in_all_files(directory_path, output_csv_path)
