from app.schemas.routes import RouteAccessibilityAnnotation


def unknown_annotation(message: str, source: str = "no_verified_local_data") -> RouteAccessibilityAnnotation:
    return RouteAccessibilityAnnotation(status="unknown", message=message, source=source)
