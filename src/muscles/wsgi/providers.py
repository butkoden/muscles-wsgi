from __future__ import annotations

from pathlib import Path

from muscles.core import GenerationRequest


class WsgiGeneratorProvider:
    name = "muscles-wsgi"

    def supports(self, generator_type: str) -> bool:
        return generator_type in {"wsgi-api", "wsgi-web"}

    def generate(self, project_root: Path, request: GenerationRequest) -> list[str]:
        app_dir = project_root / "app"
        slug = request.name.replace(".", "_").replace("-", "_").lower()

        if request.generator_type == "wsgi-api":
            path = app_dir / "api" / f"{slug}.py"
            content = (
                "from muscles.wsgi import JsonResponse\n\n"
                f"def {slug}_endpoint(request, *args, **kwargs):\n"
                f"    return JsonResponse({{'resource': '{request.name}'}})\n"
            )
        else:
            path = app_dir / "web" / f"{slug}.py"
            content = (
                "from muscles.wsgi import HtmlResponse\n\n"
                f"def {slug}_page(request, *args, **kwargs):\n"
                f"    return HtmlResponse('<h1>{request.name}</h1>')\n"
            )

        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not request.force:
            raise FileExistsError(f"File `{path}` already exists. Use force=True to overwrite.")
        path.write_text(content, encoding="utf-8")
        return [str(path.relative_to(project_root))]

