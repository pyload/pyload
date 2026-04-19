from openapi_spec_validator import validate


class TestOpenAPISpec:
    def test_openapi_spec_is_valid(self, client):
        response = client.get("/api/openapi.json", auth=("pyload", "pyload"))

        assert response.status_code == 200
        # If no exception is raised by validate(), the spec is valid.
        validate(response.json)
