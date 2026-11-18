from dataclasses import dataclass

@dataclass
class User:
    token: str
    valid: bool

    @staticmethod
    def from_dict(d: dict) -> 'User':
        return User(token = d['token'],
                    valid = d['valid'])