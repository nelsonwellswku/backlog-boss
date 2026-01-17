# export_openapi.py
import json
import os
from main import app

def generate_openapi_json():
    # Get the OpenAPI schema from the app instance
    openapi_schema = app.openapi()

    # Define the output file path
    output_file = "openapi.json"

    # Write the schema to the file
    with open(output_file, "w") as f:
        json.dump(openapi_schema, f, indent=2)

    print(f"Successfully generated OpenAPI schema to {os.path.abspath(output_file)}")

if __name__ == "__main__":
    generate_openapi_json()
