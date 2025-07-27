from homeworks.space_battle.actions import Move, Rotate
from homeworks.space_battle.adapters import MovingObjectAdapter, RotatableObjectAdapter
from homeworks.space_battle.models import Point, Angle
from homeworks.space_battle.uobject import UObject


def print_ship_state(ship: UObject):
    location: Point = ship.get_property('location')
    angle: Angle = ship.get_property('angle')
    velocity: float = ship.get_property('velocity')
    print(f"Location: {location}, Angle: {angle}, Velocity: {velocity}")


def main():
    # Создаем космический корабль
    ship = UObject()
    ship.set_property(property_='location', value=Point(12, 5))
    ship.set_property(property_='angle', value=Angle(45))
    ship.set_property(property_='velocity', value=10)  # Модуль скорости

    print("== INITIAL STATE ==")
    print_ship_state(ship)

    # Двигаем корабль
    move_adapter = MovingObjectAdapter(ship)
    move_action = Move(move_adapter)
    move_action.execute()
    print("\n== AFTER MOVE ==")
    print_ship_state(ship)

    # Поворачиваем корабль
    rotate_adapter = RotatableObjectAdapter(ship)
    rotate_action = Rotate(rotate_adapter)
    rotate_action.execute(Angle(15))
    print("\n== AFTER ROTATE +15° ==")
    print_ship_state(ship)

    # Двигаем снова (с новым углом)
    move_action.execute()
    print("\n== AFTER SECOND MOVE ==")
    print_ship_state(ship)


if __name__ == "__main__":
    main()
