from collections import Sequence
from .protocol import Coordinates, AttackResponse, BOARD_ROW_RANGE, BOARD_COLUMN_RANGE
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


class InteractivePlayer(BasePlayer):
    """
    An interactive player, which uses the console for I/O.
    This object does not hold any state, and relies on the player using the console to manage the board.
    """

    def initialize_board(self, ship_sizes: Sequence[int]):
        print(f"Place the ships on your board. Available ship sizes: {', '.join(str(size) for size in ship_sizes)}")
        input("Press enter when you're done.")

    def _parse_attack_coordinates(self):
        attack_input = input().split(",")
        try:
            attack_input = [int(number) for number in attack_input]
        except ValueError:
            return None

        if len(attack_input) != 2:
            return None

        coordinates = Coordinates(*attack_input)
        if not (BOARD_COLUMN_RANGE.min <= coordinates.horizontal <= BOARD_COLUMN_RANGE.max
                and BOARD_ROW_RANGE.min <= coordinates.vertical <= BOARD_ROW_RANGE.max):
            return None
        return coordinates

    def attack(self) -> Coordinates:
        print("Where would you like to attack? Enter the row number and column number separated by a "
              "comma:")
        while (parsed_coordinates := self._parse_attack_coordinates()) is None:
            print("Invalid coordinates. Please try again.")
        return parsed_coordinates

    def _parse_attack_response(self):
        user_response = input()

        try:
            return AttackResponse(int(user_response))
        except ValueError:
            return None

    def respond_to_attack(self, coordinates: Coordinates) -> AttackResponse:
        print(f"You were attacked at row {coordinates.vertical} and column {coordinates.horizontal}")
        print("Enter the input fitting for the result:  (Note: An attack on a previous hit is considered a miss, "
              "and also an out-of-bounds attack)")
        for response, response_value in AttackResponse.__members__.items():
            print(f"{response}: {response_value}")
        while (attack_response := self._parse_attack_response()) is None:
            print("Invalid input. Please try again.")
        return attack_response

    def process_attack_result(self, coordinates: Coordinates, response: AttackResponse):
        print(f"You last attack resulted in {str(response)}")
        if response == AttackResponse.GAME_END:
            print("The game ended. You won!")
