class DurationMixin:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.duration: int | None = None
