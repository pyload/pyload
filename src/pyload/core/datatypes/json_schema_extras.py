INT64_JSON_SCHEMA = {
    "type": "integer",
    "format": "int64"
}

OPTIONAL_INT64_JSON_SCHEMA = {
    "anyOf": [
        INT64_JSON_SCHEMA,
        {
            "type": "null"
        }
    ]
}

FLOAT_JSON_SCHEMA = {
    "type": "number",
    "format": "float"
}

OPTIONAL_FLOAT_JSON_SCHEMA = {
    "anyOf": [
        FLOAT_JSON_SCHEMA,
        {
            "type": "null"
        }
    ]
}
