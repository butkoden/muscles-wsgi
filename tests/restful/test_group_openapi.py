from muscles import BearerAuthSecurity, JsonResponseBody
from muscles.wsgi.restful import RestApi


def test_group_metadata_is_dumped_to_openapi():
    api = RestApi(name="GroupOpenApiWsgi", prefix="/api")
    bearer = BearerAuthSecurity()
    group = api.group(
        "/documents",
        tags=["Documents"],
        security=[bearer],
        response={401: JsonResponseBody(description="Unauthorized")},
    )

    @group.init("/{id}", method="GET", summary="Show document")
    def show(request, id):
        return {"id": id}

    schema = api.swagger.dump()
    operation = schema["paths"]["/api/documents/{id}"]["get"]

    assert operation["tags"] == ["Documents"]
    assert operation["summary"] == "Show document"
    assert operation["security"] == [{"Bearer": []}]
    assert "401" in {str(key) for key in operation["responses"]}
    assert schema["components"]["securitySchemes"]["Bearer"]["scheme"] == "bearer"


def test_controller_accepts_stateful_flag_like_asgi():
    api = RestApi(name="StatefulControllerWsgi", prefix="/api")

    @api.controller("/sessions", stateful=True)
    class SessionController:
        @api.action(route="/{id}", method="GET")
        def show(self, request, id):
            return {"id": id}

    assert SessionController.stateful_controller is True
