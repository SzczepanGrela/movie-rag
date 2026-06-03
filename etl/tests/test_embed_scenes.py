import importlib

mod = importlib.import_module("08_embed_scenes")


def test_plan_scene_chunks_builds_rows() -> None:
    meta = {7: mod.MovieMeta(title="Jurassic Park", year=1993)}
    scenes_by_movie = {
        7: [(900, 0, "Kitchen Chase", "Raptors hunt the kids.", "tense", ["Lex"])]
    }
    plans = mod.plan_scene_chunks(meta, scenes_by_movie)
    assert len(plans) == 1
    p = plans[0]
    assert p.scene_id == 900
    assert p.movie_id == 7
    assert p.scene_index == 0
    assert p.content == "Kitchen Chase. Raptors hunt the kids. Mood: tense. Characters: Lex."
    assert p.embed_input == (
        "title: Jurassic Park (1993) | text: "
        "Kitchen Chase. Raptors hunt the kids. Mood: tense. Characters: Lex."
    )


def test_plan_scene_chunks_skips_unknown_movie() -> None:
    plans = mod.plan_scene_chunks({}, {7: [(900, 0, "T", "D", "", [])]})
    assert plans == []
