from textual.suggester import Suggester


class TagSuggester(Suggester):
    """Completes the tag being typed after the last comma.

    SuggestFromList would try to complete the whole field, which is a comma-separated
    list, so only the trailing segment is matched.
    """

    def __init__(self, tags: list[str]) -> None:
        # case_sensitive keeps the value as typed; stored tags are already lowercase
        super().__init__(case_sensitive=True)
        self.tags = tags

    async def get_suggestion(self, value: str) -> str | None:
        current = value[value.rfind(",") + 1:].lstrip()
        if not current:
            return None
        match = next((tag for tag in self.tags if tag.startswith(current.lower())), None)
        # Input renders the suggestion as value + suggestion[len(value):], so appending
        # the missing tail is what keeps the ghost text lined up with what was typed.
        return value + match[len(current):] if match else None
