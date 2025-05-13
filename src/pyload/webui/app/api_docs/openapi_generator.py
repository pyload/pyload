# -*- coding: utf-8 -*-
#       ____________
#   ___/       |    \_____________ _                 _ ___
#  /        ___/    |    _ __ _  _| |   ___  __ _ __| |   \
# /    \___/  ______/   | '_ \ || | |__/ _ \/ _` / _` |    \
# \            ◯ |      | .__/\_, |____\___/\__,_\__,_|    /
#  \_______\    /_______|_|   |__/________________________/
#           \  /
#            \/
import inspect
from enum import IntEnum, Enum
from typing import get_origin, get_args, Union, Any, Type, Optional

import flask
from pydantic import BaseModel

from pyload.core.api import legacy_map

PRIMITIVE_TYPE_MAP = {
    str: {"type": "string"},
    int: {"type": "integer"},
    float: {"type": "number", "format": "float"},
    bool: {"type": "boolean"},
}

"""
This will build an OpenAPI specification based on the existing api functions
* Parameter types and return types are parsed from the method signature
* Descriptions are parsed from the docstring
* Data models are registered as components via Pydantic's inbuilt conversion
To conform with OpenAPI standards, the following logic is used to determine the appropriate REST method:
* Functions requiring no parameters will use a GET method
* Functions with primitive parameters will use a POST method with query params
* Functions with non-primitive parameters (e.g. arrays) will use a POST method with json request body
* File uploads will use a POST method with multipart request body
"""
class OpenAPIGenerator:
    def __init__(self):
        self.spec: dict[str, Any] = {
            "info": {
                "title": "pyLoad API Documentation - OpenAPI",
                "version": "1.0.0"
            },
            "openapi": "3.1.1",
            "tags": [{
                "name": "pyLoad Authentication",
                "description": ""
            }, {
                "name": "pyLoad REST",
                "description": ""
            }],
            "paths": {
                "/api/login": {
                    "post": {
                        "security": [],
                        "summary": "Login into pyLoad, this must be called when using rpc before any methods can be used.",
                        "tags": [
                            "pyLoad Authentication"
                        ],
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/x-www-form-urlencoded": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "username": {
                                                "type": "string",
                                                "default": "pyload"
                                            },
                                            "password": {
                                                "type": "string",
                                                "default": "pyload"
                                            }
                                        },
                                        "required": [
                                            "username",
                                            "password"
                                        ]
                                    }
                                }
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Session data if successful, False otherwise",
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {},
                "securitySchemes": {
                    "cookieAuth": {
                        "type": "apiKey",
                        "in": "cookie",
                        "name": flask.current_app.config["SESSION_COOKIE_NAME"]
                    }
                }
            },
            "security": [{"cookieAuth": []}]
        }

    def generate_openapi_json(self) -> dict[str, Any]:
        """Generate OpenAPI documentation by introspecting the API module"""
        api = flask.current_app.config["PYLOAD_API"]

        for name, method in inspect.getmembers(api, predicate=inspect.ismethod):
            if name.startswith('_') or name in legacy_map.values() or name == "login":
                continue

            docstring = inspect.getdoc(method) or "No documentation available"
            docstring_lines = docstring.split("\n")

            summary = docstring.split(":param", 1)[0].split(":return", 1)[0].replace("\n", " ").strip()

            operation: dict[str, Any] = {
                "summary": summary,
                "description": summary,
                "tags": ["pyLoad REST"]
            }
            rest_method = "post"

            method_params = dict(inspect.signature(method).parameters)
            method_params.pop("self", None)

            if not method_params:
                rest_method = "get"
            elif all(self._is_primitive_type(param_type.annotation) for param_type in method_params.values()):
                query_params = self._build_post_request_with_query_params(docstring_lines, method_params)
                operation.update({
                    "parameters": query_params,
                })
            else:
                request_body = self._build_post_request_with_request_body(docstring_lines, method_params)
                operation.update(request_body)

            response = self._build_response(docstring_lines, method)
            operation.update({
                "responses": {"200": response}
            })
            self.spec["paths"][f"/api/{name}"] = {rest_method: operation}

        return self.spec

    def _build_post_request_with_query_params(self, docstring_lines, method_params) -> list[dict[str, Any]]:
        query_params = []
        for param_name, param in method_params.items():
            param_info: dict[str, Any] = {
                "name": param_name,
                "in": "query"
            }

            schema_type = self._get_openapi_type_for_annotation(param.annotation)
            param_info["required"] = True
            param_info["schema"] = schema_type

            if param.default != inspect.Parameter.empty:
                param_info["required"] = False
                param_info["schema"]["default"] = param.default

            if param_description := self._parse_parameter_docstring(docstring_lines, param_name):
                param_info["description"] = param_description

            query_params.append(param_info)

        return query_params

    def _build_post_request_with_request_body(self, docstring_lines, method_params) -> dict[str, Any]:
        request_body_schema: dict[str, Any] = {
            "type": "object",
            "properties": {}
        }
        content_type = "application/json"
        for param_name, param in method_params.items():
            param_info: dict[str, Any] = {}

            schema_type = self._get_openapi_type_for_annotation(param.annotation)
            param_info["required"] = True
            param_info.update(schema_type)

            if schema_type.get("format", None) == "binary":
                content_type = "multipart/form-data"

            if param.default != inspect.Parameter.empty:
                param_info["required"] = False
                param_info["default"] = param.default

            if param_description := self._parse_parameter_docstring(docstring_lines, param_name):
                param_info["description"] = param_description

            request_body_schema["properties"][param_name] = param_info

            if param_info.pop("required", None):
                required_properties = request_body_schema.get("required", [])
                required_properties.append(param_name)
                request_body_schema["required"] = required_properties

        return {
            "requestBody": {
                "content": {
                    content_type: {
                        "schema": request_body_schema
                    }
                }
            }
        }

    def _is_primitive_type(self, annotation) -> bool:
        return annotation in PRIMITIVE_TYPE_MAP or (isinstance(annotation, type) and issubclass(annotation, Enum))

    def _parse_parameter_docstring(self, docstring_lines, param_name) -> Optional[str]:
        for line in docstring_lines:
            if "".join([":param ", param_name, ": "]) in line:
                return line.split(": ", 1)[1]
        return None

    def _build_response(self, docstring_lines, method) -> dict[str, Any]:
        response: dict[str, Any] = {"description": ""}

        if response_description := self._parse_response_docstring(docstring_lines):
            response["description"] = response_description

        return_type = inspect.signature(method).return_annotation
        response_schema = self._get_openapi_type_for_annotation(return_type)
        if isinstance(return_type, type) and issubclass(return_type, BaseModel):
            self._register_pydantic_model(return_type)
            response_schema = {
                "$ref": "#/components/schemas/" + return_type.__name__
            }
        if response_schema:
            response["content"] = {
                "application/json": {
                    "schema": response_schema
                }
            }
        else:
            response["description"] = "No response"

        return response

    def _parse_response_docstring(self, docstring_lines) -> Optional[str]:
        for line in docstring_lines:
            if ":return: " in line:
                return line.split(": ", 1)[1]
        return None

    def _register_pydantic_model(self, model: Type[BaseModel]):
        model_name = model.__name__

        if model_name in self.spec["components"]["schemas"].keys():
            return

        # Inspect fields for nested models
        for field in model.model_fields.values():
            field_type = field.annotation
            # Handle nested Pydantic models
            if isinstance(field_type, type) and issubclass(field_type, BaseModel):
                self._register_pydantic_model(field_type)
            # Handle generic types like List[InnerModel], Optional[InnerModel], etc.
            elif hasattr(field_type, '__args__'):
                for arg in field_type.__args__:
                    if isinstance(arg, type) and issubclass(arg, BaseModel):
                        self._register_pydantic_model(arg)
            elif isinstance(field_type, type) and issubclass(field_type, IntEnum):
                self._register_enum(field_type)

        schema = model.model_json_schema(ref_template="#/components/schemas/{model}")
        schema.pop('$defs', None)  # Remove duplicate inner model definitions if present

        self.spec["components"]["schemas"][model_name] = schema

    def _register_enum(self, model: Type[IntEnum]):
        enum_members = inspect.getmembers(model, lambda m: isinstance(m, model))
        if model.__name__ not in self.spec["components"]["schemas"].keys():
            self.spec["components"]["schemas"][model.__name__] = {
                "type": "integer",
                "enum": [member for _, member in enum_members],
                "x-enum-varnames": [name for name, _ in enum_members]
            }

    def _get_openapi_type_for_annotation(self, annotation) -> Optional[dict[str, Any]]:
        """Convert Python type annotation to OpenAPI schema"""
        if annotation is None:
            return None

        if annotation in PRIMITIVE_TYPE_MAP:
            return PRIMITIVE_TYPE_MAP[annotation].copy()

        # Pydantic models
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            self._register_pydantic_model(annotation)
            return {"$ref": "#/components/schemas/" + annotation.__name__}

        if annotation == bytes:
            return {"type": "string", "format": "binary"}

        origin = get_origin(annotation)
        args = get_args(annotation)

        if origin is list:
            return {
                "type": "array",
                "items": self._get_openapi_type_for_annotation(args[0]) if args else {}
            }

        if origin is dict:
            value_type = args[1] if len(args) == 2 else object
            return {
                "type": "object",
                "additionalProperties": self._get_openapi_type_for_annotation(value_type)
            }

        # Union types (Optional is Union[T, None])
        if origin is Union:
            # If one of the types is None, treat it as nullable
            no_none_types = [arg for arg in args if arg is not type(None)]
            if len(no_none_types) == 1 and len(args) == 2:
                schema = self._get_openapi_type_for_annotation(no_none_types[0])
                schema["nullable"] = True
                return schema

            # Otherwise, use oneOf for true unions
            return {
                "oneOf": [self._get_openapi_type_for_annotation(arg) for arg in args]
            }

        object_types = [Any, object]
        if annotation in object_types:
            return {"type": "object"}

        if isinstance(annotation, type) and issubclass(annotation, IntEnum):
            self._register_enum(annotation)
            return {"$ref": "#/components/schemas/" + annotation.__name__}

        raise ValueError(f"Unexpected type annotation {annotation} with origin {origin}")
