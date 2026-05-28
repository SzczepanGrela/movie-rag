from datetime import UTC, date, datetime

from app.models import (
    Atmosphere,
    CharacterDescription,
    Genre,
    Movie,
    MovieCast,
    MovieCrew,
    Person,
    PlotVariant,
    Quote,
    Scene,
    SourceText,
    Theme,
)
from app.movies.service import to_detail


def _make_person(person_id: int, name: str, tmdb_id: int) -> Person:
    p = Person(id=person_id, tmdb_id=tmdb_id, name=name)
    p.cast_roles = []
    p.crew_roles = []
    return p


def _make_minimal_movie(*, schema_c_status: str = "done") -> Movie:
    m = Movie(
        id=1,
        tmdb_id=27205,
        imdb_id="tt1375666",
        title="Inception",
        original_title="Inception",
        year=2010,
        runtime=148,
        release_date=date(2010, 7, 16),
        overview="A thief who steals corporate secrets...",
        tagline="Your mind is the scene of the crime.",
        vote_average=8.4,
        vote_count=35000,
        original_language="en",
        etl_status="done",
        schema_c_status=schema_c_status,
    )
    m.genres = []
    m.cast = []
    m.crew = []
    m.source_texts = []
    m.plot_variants = []
    m.scenes = []
    m.themes = []
    m.atmosphere = None
    m.quotes = []
    m.character_descriptions = []
    return m


def test_to_detail_full_movie() -> None:
    m = _make_minimal_movie()
    m.genres = [Genre(id=1, tmdb_id=28, name="Action")]

    leo = _make_person(1, "Leonardo DiCaprio", 6193)
    m.cast = [
        MovieCast(id=1, movie_id=1, person_id=1, character="Cobb", billing_order=0),
    ]
    m.cast[0].person = leo

    nolan = _make_person(2, "Christopher Nolan", 525)
    m.crew = [
        MovieCrew(id=1, movie_id=1, person_id=2, job="Director", department="Directing"),
    ]
    m.crew[0].person = nolan

    m.source_texts = [
        SourceText(
            id=1,
            movie_id=1,
            source="wikipedia",
            lang="en",
            content="Lorem ipsum heavy text not included",
            source_url="https://en.wikipedia.org/wiki/Inception",
            char_count=1234,
            fetched_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
    ]
    m.plot_variants = [
        PlotVariant(id=1, movie_id=1, kind="concise", text="Concise summary"),
        PlotVariant(id=2, movie_id=1, kind="chronological", text="Long chrono"),
        PlotVariant(id=3, movie_id=1, kind="thematic", text="Themes essay"),
    ]
    m.scenes = [
        Scene(
            id=10,
            movie_id=1,
            scene_index=1,
            title="Opening",
            description="...",
            mood="tense",
            characters=["Cobb"],
        ),
        Scene(
            id=11,
            movie_id=1,
            scene_index=2,
            title="Mr. Charles",
            description="...",
            mood="anxious",
            characters=["Cobb", "Eames"],
        ),
    ]
    m.themes = [
        Theme(id=1, movie_id=1, theme_index=0, theme="reality vs dreams"),
        Theme(id=2, movie_id=1, theme_index=1, theme="guilt"),
    ]
    m.atmosphere = Atmosphere(id=1, movie_id=1, text="Dreamlike, paranoid")
    m.quotes = [
        Quote(
            id=1,
            movie_id=1,
            quote_index=0,
            quote_text="You mustn't be afraid to dream a little bigger, darling.",
            attributed_to="Eames",
        ),
    ]
    m.character_descriptions = [
        CharacterDescription(
            id=1, movie_id=1, char_index=0, character_name="Cobb", description="Skilled extractor"
        ),
    ]

    detail = to_detail(m)

    assert detail.id == 1
    assert detail.tmdb_id == 27205
    assert detail.title == "Inception"
    assert detail.schema_c_status == "done"
    assert detail.genres[0].name == "Action"
    assert len(detail.cast) == 1
    assert detail.cast[0].name == "Leonardo DiCaprio"
    assert detail.cast[0].character == "Cobb"
    assert detail.cast[0].tmdb_url == "https://www.themoviedb.org/person/6193"
    assert len(detail.crew) == 1
    assert detail.crew[0].job == "Director"
    assert detail.sources[0].source == "wikipedia"
    assert not hasattr(detail.sources[0], "content")
    assert detail.plot_summary == "Concise summary"
    assert detail.atmosphere == "Dreamlike, paranoid"
    assert detail.themes == ["reality vs dreams", "guilt"]
    assert len(detail.scenes) == 2
    assert detail.scenes[0].title == "Opening"
    assert not hasattr(detail.scenes[0], "description")
    assert detail.quotes[0].attributed_to == "Eames"
    assert detail.character_descriptions[0].character_name == "Cobb"


def test_to_detail_movie_without_schema_c() -> None:
    m = _make_minimal_movie(schema_c_status="pending")
    m.genres = [Genre(id=1, tmdb_id=28, name="Action")]
    leo = _make_person(1, "Leo", 6193)
    m.cast = [MovieCast(id=1, movie_id=1, person_id=1, character="Cobb", billing_order=0)]
    m.cast[0].person = leo

    detail = to_detail(m)

    assert detail.schema_c_status == "pending"
    assert detail.plot_summary is None
    assert detail.atmosphere is None
    assert detail.themes == []
    assert detail.scenes == []
    assert detail.quotes == []
    assert detail.character_descriptions == []
    assert len(detail.cast) == 1
    assert len(detail.genres) == 1


def test_to_detail_picks_concise_plot_variant() -> None:
    m = _make_minimal_movie()
    m.plot_variants = [
        PlotVariant(id=1, movie_id=1, kind="thematic", text="thematic text"),
        PlotVariant(id=2, movie_id=1, kind="chronological", text="chrono text"),
        PlotVariant(id=3, movie_id=1, kind="concise", text="CONCISE text"),
    ]

    detail = to_detail(m)

    assert detail.plot_summary == "CONCISE text"


def test_to_detail_cast_trimmed_to_15_and_sorted_by_billing_order() -> None:
    m = _make_minimal_movie()
    m.cast = []
    for i in range(30):
        cm = MovieCast(
            id=i + 1, movie_id=1, person_id=i + 1, character=f"Char{i}", billing_order=29 - i
        )
        cm.person = _make_person(i + 1, f"Actor{i}", 1000 + i)
        m.cast.append(cm)

    detail = to_detail(m)

    assert len(detail.cast) == 15
    assert detail.cast[0].name == "Actor29"
    assert detail.cast[14].name == "Actor15"


def test_to_detail_crew_sorted_by_dept_job_name() -> None:
    m = _make_minimal_movie()
    p_nolan = _make_person(1, "Nolan", 525)
    p_zimmer = _make_person(2, "Zimmer", 947)
    p_wally = _make_person(3, "Wally Pfister", 1296)
    m.crew = [
        MovieCrew(id=1, movie_id=1, person_id=2, job="Original Music Composer", department="Sound"),
        MovieCrew(
            id=2, movie_id=1, person_id=3, job="Director of Photography", department="Camera"
        ),
        MovieCrew(id=3, movie_id=1, person_id=1, job="Director", department="Directing"),
    ]
    m.crew[0].person = p_zimmer
    m.crew[1].person = p_wally
    m.crew[2].person = p_nolan

    detail = to_detail(m)

    assert [c.department for c in detail.crew] == ["Camera", "Directing", "Sound"]
    assert detail.crew[0].name == "Wally Pfister"
    assert detail.crew[1].name == "Nolan"
    assert detail.crew[2].name == "Zimmer"


def test_to_detail_atmosphere_none_when_missing() -> None:
    m = _make_minimal_movie()
    m.atmosphere = None

    detail = to_detail(m)

    assert detail.atmosphere is None
