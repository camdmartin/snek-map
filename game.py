import voromap
from random import randint


class Faction:
    def __init__(self, faction_color):
        self.faction_color = faction_color
        self.entities = []

    def create_entity(self, entity_icon):
        e = Entity(self, entity_icon)
        self.entities.append(e)
        return e


class Entity:
    icon = '#'
    name = 'Entity'

    def __init__(self, owner: Faction, icon: str):
        self.owner = owner
        self.faction_color = owner.faction_color


class Game:
    def __init__(self, world_map: voromap.WorldMap, faction_count):
        self.world_map = world_map
        self.factions = []
        self.faction_count = faction_count

        self.create_new_game(False)

    def create_entity(self, owner: Faction, tile, icon='#'):
        e = Entity(owner, icon)
        tile.entities.append(e)
        owner.entities.append(e)

    def create_new_game(self, regenerate_world: bool):
        self.factions = []

        if regenerate_world:
            self.world_map.regenerate()

        for i in range(0, self.faction_count):
            f = Faction(randint(0, 255))
            self.factions.append(f)
            self.create_entity(f, self.world_map.get_random_land_tile())