import voromap
from random import randint


class Faction:
    def __init__(self, faction_color):
        self.faction_color = faction_color
        self.entities = []


class Entity:
    icon = '#'
    name = 'Entity'

    def __init__(self, owner: Faction):
        self.owner = owner
        self.owner.entities.append(self)
        self.faction_color = owner.faction_color


class Game:
    def __init__(self, world_map: voromap.WorldMap, faction_count):
        self.world_map = world_map
        self.factions = []
        self.faction_count = faction_count

        self.create_new_game(False)

    def create_entity(self, owner: Faction, x, y):
        self.world_map.tile_at_point(x, y).entities.append(Entity(owner))

    def create_new_game(self, regenerate_world: bool):
        self.factions = []

        if regenerate_world:
            self.world_map.regenerate()

        for i in range(0, self.faction_count - 1):
            f = Faction(randint(0, 255))
            self.factions.append(f)
            self.create_entity(f, randint(0, self.world_map.generation_dict['width']),
                               randint(0, self.world_map.generation_dict['height']))