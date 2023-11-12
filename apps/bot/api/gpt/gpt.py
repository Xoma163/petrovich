class GPT:
    def __init__(self, model):
        self.model = model

    def completions(self, messages: list):
        raise NotImplementedError
