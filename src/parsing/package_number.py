import json

from src.parsing.package import Package


class PackageNumber(Package):
    def __init__(self, number_of_packages:int):
        self.number_of_packages = number_of_packages
        super().__init__("package_number", self.prepare_json())

    def prepare_json(self):
        return json.dumps({"number_of_packages": self.number_of_packages})

    @staticmethod
    def from_json(message:str):
        package = json.loads(message)
        return PackageNumber(package["number_of_packages"])