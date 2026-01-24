class SizedMixin:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.width: int | None = None
        self.height: int | None = None
