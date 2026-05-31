from app.explain.sse import sse_event


def test_sse_event_formats_event_and_json_data() -> None:
    out = sse_event("chunk", {"text": "hello"})
    assert out == 'event: chunk\ndata: {"text": "hello"}\n\n'


def test_sse_event_keeps_unicode_readable() -> None:
    out = sse_event("chunk", {"text": "café"})
    assert "café" in out
    assert out.endswith("\n\n")
