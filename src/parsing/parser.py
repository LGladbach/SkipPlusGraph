import json

from src.parsing.flood import Flood
from src.parsing.linearize import Linearize
from src.parsing.package import Package
from src.parsing.package_number import PackageNumber


class Parser:
    package_parser = {"package_number":PackageNumber, "linearize":Linearize, "flood":Flood}
    @staticmethod
    def parse_package(package:str) -> Package:
        try:
            p = Package.from_json(package)
            return Parser.package_parser[p.package_type].from_json(p.package_content)
        except json.JSONDecodeError:
            return Package("none", "")
        except KeyError:
            return Package("none", "")