import requests


class EdubovitLabyrinthAPI:
    BASE_URL = "https://labyrinth.edubovit.net/api"

    def __init__(self):
        pass

    def init(self, width=20, height=20):
        """
        Создаёт новую игру и возвращает её id
        """
        r = requests.post(f"{self.BASE_URL}/game/create", json={'width': width, 'height': height})
        # id mapUrl finish
        return r.json()

    def do_the_move(self, game_id, direction):
        if direction not in ['up', 'down', 'left', 'right']:
            raise RuntimeError("Некорректное направление движения")
        r = requests.post(f"{self.BASE_URL}/game/{game_id}/{direction}")
        # id mapUrl finish successMove
        return r.json()
