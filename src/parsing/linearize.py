import json

from src.parsing.package import Package


class Linearize(Package):
    def __init__(self, address:tuple[str, int]):
        self.address = address
        super().__init__("linearize", self.prepare_json())

    def prepare_json(self):
        return json.dumps({"address": self.address})

    @staticmethod
    def from_json(message:str):
        data = json.loads(message)
        return Linearize(tuple(data["address"]))