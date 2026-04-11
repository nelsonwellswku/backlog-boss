from pydantic import BaseModel, ConfigDict

# API models use snake_case in Python and camelCase on the wire.
# Requests accept aliases only to keep the client contract strict.
# Responses still serialize aliases, but allow Python field names when
# constructing models inside the server.


def to_camel_case(value: str) -> str:
    if not value:
        return value

    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class ApiResponseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel_case,
        validate_by_alias=True,
        validate_by_name=True,
        serialize_by_alias=True,
    )


class ApiRequestModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel_case,
        validate_by_alias=True,
        validate_by_name=False,
        serialize_by_alias=True,
    )
