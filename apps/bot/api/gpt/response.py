class GPTAPIResponse:
    def __init__(self):
        self.text: str
        self.images_url: list[str]
        self.images_prompt: str
        self.images_bytes: list[bytes]
