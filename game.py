import voromap
import entities
from random import randint
from random import shuffle
from random import seed
import copy


faction_icons = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
                 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
                 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '!', '@', '#', '$', '%',
                 '^', '&', '*', '(', ')', '-', '_', '=', '+', '?']

faction_colors = [1, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15]


class Faction:
    is_player = False
    currency = 10000
    minerals = 500
    population = 10000
    population_cap = 10000

    def __init__(self, faction_icon: str, color: int, landing_site: voromap.Tile):
        self.color = color
        self.faction_icon = faction_icon
        self.origin = landing_site
        self.entities = []

    def start_turn(self):
        self.population_cap = 0
        for e in self.entities:
            if e.data.keys().__contains__('pop_cap'):
                self.population_cap += e.data['pop_cap']

        if self.population < self.population_cap:
            self.population = int(self.population * 1.02)

        for e in self.entities:
            e.start_turn()
        return

    def end_turn(self):
        for e in self.entities:
            e.end_turn()
        return


class Game:
    turn = 0

    def __init__(self, world_map: voromap.WorldMap, faction_count):
        self.world_map = world_map
        self.factions = []
        self.faction_count = faction_count

        self.create_new_game(False)

    def start_turn(self):
        for f in self.factions:
            f.start_turn()

    def end_turn(self):
        for f in self.factions:
            f.end_turn()

        self.turn += 1

    def create_new_game(self, regenerate_world: bool):
        seed(randint(0, 100))

        self.factions = []

        if regenerate_world:
            self.world_map.regenerate()

        faction_icons_c = copy.copy(faction_icons)
        shuffle(faction_icons_c)
        faction_colors_c = copy.copy(faction_colors)
        shuffle(faction_colors_c)

        for i in range(0, self.faction_count):
            c = randint(0, len(faction_colors_c) - 1)
            i = randint(0, len(faction_icons_c) - 1)

            f = Faction(faction_icons_c[i], faction_colors_c[c], self.world_map.get_random_land_tile())

            self.factions.append(f)
            create_owned_entity(f, f.origin, entities.city_structure)
            create_owned_entity(f, f.origin, entities.constructor)

            faction_colors_c.remove(faction_colors_c[c])
            faction_icons_c.remove(faction_icons_c[i])

        self.factions[0].is_player = True

        self.start_turn()


def create_owned_entity(owner: Faction, tile, data):
    e = entities.create_entity(owner, tile, data)
    tile.entities.append(e)
    owner.entities.append(e)

    return e


def place_entity(entity: entities.Entity, tile: voromap.Tile):
    tile.entities.append(entity)
    entity.location = tile
