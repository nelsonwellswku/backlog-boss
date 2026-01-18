# export_openapi.py
import json
import os
from main import app

def generate_openapi_json():
    # get the OpenAPI schema from the app instance
    openapi_content = app.openapi()

    # clean up the operation ids so that the generated functions are more ergonomically named
    # the expected invocation on the front-end should be "Tag.BackendFunctionName"
    for path_data in openapi_content["paths"].values():
        for operation in path_data.values():
            tag:str = operation["tags"][0]
            operation_id:str = operation["operationId"]
            index_where_path_starts = operation_id.find("_api_")
            new_operation_id = operation_id[:index_where_path_starts]
            operation["operationId"] = f"{tag}_{new_operation_id}".lower()

    # define the output file path
    output_file = "openapi.json"

    # write the schema to the file
    with open(output_file, "w") as f:
        json.dump(openapi_content, f, indent=2)

    print(f"Successfully generated OpenAPI schema to {os.path.abspath(output_file)}")

if __name__ == "__main__":
    generate_openapi_json()
