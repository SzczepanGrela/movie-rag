import httpx

from lib.config import EtlSettings
from lib.wikipedia_client import WikipediaClient


def _sections_response(sections: list[dict[str, object]]) -> dict[str, object]:
    return {"parse": {"sections": sections}}


def _text_response(html: str) -> dict[str, object]:
    return {"parse": {"text": {"*": html}}}


async def test_get_plot_returns_text_when_plot_section_found(
    etl_settings: EtlSettings,
) -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        action = request.url.params.get("prop")
        if action == "sections":
            return httpx.Response(
                200,
                json=_sections_response(
                    [
                        {"index": "1", "line": "Cast"},
                        {"index": "2", "line": "Plot"},
                        {"index": "3", "line": "Reception"},
                    ]
                ),
            )
        return httpx.Response(200, json=_text_response("<p>The narrator meets Tyler.</p>"))

    async with WikipediaClient(etl_settings, transport=httpx.MockTransport(handler)) as client:
        plot = await client.get_plot("Fight Club (film)")

    assert plot == "<p>The narrator meets Tyler.</p>"
    assert len(captured) == 2
    assert captured[1].url.params["section"] == "2"
    assert captured[0].headers["user-agent"].startswith("movie-rag/")


async def test_get_plot_returns_none_when_no_plot_section(
    etl_settings: EtlSettings,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=_sections_response(
                [{"index": "1", "line": "Cast"}, {"index": "2", "line": "Reception"}]
            ),
        )

    async with WikipediaClient(etl_settings, transport=httpx.MockTransport(handler)) as client:
        plot = await client.get_plot("Some Title")

    assert plot is None


async def test_get_plot_accepts_plot_summary_heading(etl_settings: EtlSettings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("prop") == "sections":
            return httpx.Response(
                200, json=_sections_response([{"index": "4", "line": "Plot summary"}])
            )
        return httpx.Response(200, json=_text_response("<p>Body.</p>"))

    async with WikipediaClient(etl_settings, transport=httpx.MockTransport(handler)) as client:
        plot = await client.get_plot("Other Title")

    assert plot == "<p>Body.</p>"
