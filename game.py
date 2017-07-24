import voromap
from random import randint


faction_icons = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
                 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
                 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '!', '@', '#', '$', '%',
                 '^', '&', '*', '(', ')', '-', '_', '=', '+', '?']


class Faction:
    is_player = False
    currency = 10000
    minerals = 500
    population = 600000

    def __init__(self, faction_icon: str, faction_color: int, landing_site: voromap.Tile):
        self.faction_color = faction_color
        self.faction_icon = faction_icon
        self.origin = landing_site
        self.entities = []

    def end_turn(self):
        for e in self.entities:
            self.currency += 100
            self.minerals += 20
            self.population += 1000
        return

    def create_base(self):
        e = Entity(self, self.faction_icon)
        self.entities.append(e)
        return e

    def create_entity(self, entity_icon):
        e = Entity(self, entity_icon)
        self.entities.append(e)
        return e


class Entity:
    icon = 'Ϫ'
    name = 'Entity'
    move_data = [2, ['Land']]
    used_movement = 0

    def __init__(self, owner: Faction, icon: str):
        self.owner = owner
        self.faction_color = owner.faction_color
        self.icon = icon

    def end_turn(self):
        self.used_movement = 0


class Structure(Entity):
    move_data = [0, []]


class Game:
    turn = 0

    def __init__(self, world_map: voromap.WorldMap, faction_count):
        self.world_map = world_map
        self.factions = []
        self.faction_count = faction_count

        self.create_new_game(False)

    def end_turn(self):
        for f in self.factions:
            f.end_turn()
            for e in f.entities:
                e.end_turn()

        self.turn += 1

    def create_entity(self, owner: Faction, tile, icon='#'):
        e = Entity(owner, icon)
        tile.entities.append(e)
        owner.entities.append(e)

    def place_entity(self, entity: Entity, tile: voromap.Tile):
        tile.entities.append(entity)

    def create_new_game(self, regenerate_world: bool):
        self.factions = []

        if regenerate_world:
            self.world_map.regenerate()

        for i in range(0, self.faction_count):
            f = Faction(faction_icons[randint(0, len(faction_icons) - 1)], randint(0, 16), self.world_map.get_random_land_tile())
            self.factions.append(f)
            self.place_entity(f.create_base(), f.origin)
            self.place_entity(f.create_base(), f.origin)

        self.factions[0].is_player = True