import json

from src.parsing.package import Package


class Flood(Package):
    def __init__(self, payload:str, depth:int, origin:tuple[str, int]):
        self.origin = origin
        self.payload = payload
        self.depth = depth
        super().__init__("flood", self.prepare_json())

    def prepare_json(self) -> str:
        return json.dumps({"payload": self.payload, "depth":self.depth, "origin": self.origin})

    @staticmethod
    def from_json(message:str):
        data = json.loads(message)
        return Flood(data["payload"], data["depth"], data["origin"])