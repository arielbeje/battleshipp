from collections import Sequence
from .protocol import Coordinates, AttackResponse
from abc import abstractmethod


class BasePlayer:
    @abstractmethod
    def initialize_board(self, ship_sizes: Sequence[int]):
        pass

    @abstractmethod
    def attack(self) -> Coordinates:
        pass

    @abstractmethod
    def respond_to_attack(self, coordinates: Coordinates) -> AttackResponse:
        pass

    @abstractmethod
    def process_attack_result(self, coordinates: Coordinates, response: AttackResponse):
        pass
