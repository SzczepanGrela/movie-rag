def compose_scene_text(*, title: str, description: str, mood: str, characters: list[str]) -> str:
    names = [c.strip() for c in characters if c.strip()]
    parts = [f"{title.strip()}.", description.strip()]
    if mood.strip():
        parts.append(f"Mood: {mood.strip()}.")
    if names:
        parts.append(f"Characters: {', '.join(names)}.")
    return " ".join(p for p in parts if p and p.strip())
