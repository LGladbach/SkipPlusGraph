import json


class Package:
    def __init__(self, package_type:str, package_content:str):
        self.package_type = package_type
        self.package_content = package_content

    def to_json(self):
        return json.dumps({"package_type": self.package_type, "package_content": self.package_content})

    @staticmethod
    def from_json(message:str):
        data = json.loads(message)
        return Package(data["package_type"], data["package_content"])