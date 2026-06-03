from lib.scenes import compose_scene_text


def test_compose_full() -> None:
    text = compose_scene_text(
        title="Kitchen Chase",
        description="Lex and Tim are hunted by raptors in the kitchen.",
        mood="tense, terrifying",
        characters=["Lex", "Tim"],
    )
    assert text == (
        "Kitchen Chase. Lex and Tim are hunted by raptors in the kitchen. "
        "Mood: tense, terrifying. Characters: Lex, Tim."
    )


def test_compose_skips_empty_mood_and_characters() -> None:
    text = compose_scene_text(
        title="Opening", description="A quiet morning.", mood="", characters=[]
    )
    assert text == "Opening. A quiet morning."


def test_compose_mood_only() -> None:
    text = compose_scene_text(title="Duel", description="A standoff.", mood="tense", characters=[])
    assert text == "Duel. A standoff. Mood: tense."


def test_compose_characters_only() -> None:
    text = compose_scene_text(
        title="Duel", description="A standoff.", mood="", characters=["Shane"]
    )
    assert text == "Duel. A standoff. Characters: Shane."


def test_compose_strips_and_drops_blank_characters() -> None:
    text = compose_scene_text(
        title="Duel", description="A standoff.", mood="", characters=["  Shane ", "", "  "]
    )
    assert text == "Duel. A standoff. Characters: Shane."
