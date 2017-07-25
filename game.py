import voromap
from random import randint
from random import shuffle
from random import seed
from asciimatics.event import KeyboardEvent
import copy


faction_icons = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
                 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
                 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '!', '@', '#', '$', '%',
                 '^', '&', '*', '(', ')', '-', '_', '=', '+', '?']

faction_colors = [1, 3, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15]

optional_entity_keys = ['Energy', 'Minerals', 'Currency', 'Population', 'Construct']

entity_dict = {
    'null_entity': {'name': '', 'icon': ' ', 'cost': 0, 'upkeep': 0,
                    'movement': [0, []], 'size': 0, 'strength': 0, 'armor': 0}, # has all mandatory keys
    'Solar Array': {'name': 'Solar Array', 'icon': 'Ξ', 'cost': 50, 'upkeep': 50,
                    'movement': [0, []], 'size': 1, 'strength': 0, 'armor': 20,
                    'Energy': 2},
    'Mine': {'name': 'Mine', 'icon': 'Ѫ', 'cost': 50, 'upkeep': 50,
             'movement': [0, []], 'combat': {'size': 1, 'strength': 0, 'armor': 20},
             'Minerals': 10},
    'Habitat': {'name': 'Habitat', 'icon': 'Ҧ', 'cost': 50, 'upkeep': 50,
                'movement': [0, []], 'combat': {'size': 1, 'strength': 0, 'armor': 20},
                'Population': 10000},
    'City Center': {'name': 'City Center', 'icon': 'ʘ', 'cost': 50, 'upkeep': 50,
                    'movement': [0, []], 'size': 1, 'strength': 0, 'armor': 20,
                    'Population': 25000, 'Energy': 1, 'Currency': 100},
    'Constructor': {'name': 'Constructor', 'icon': 'Ɣ', 'cost': 100, 'upkeep': 50,
                    'movement': [3, ['Land']], 'size': 10, 'strength': 1, 'armor': 2,
                    'Construct': ['Solar Array', 'Mine', 'Habitat']}
}


class Faction:
    is_player = False
    currency = 10000
    minerals = 500
    population = 10000
    population_cap = 10000

    def __init__(self, faction_icon: str, faction_color: int, landing_site: voromap.Tile):
        self.faction_color = faction_color
        self.faction_icon = faction_icon
        self.origin = landing_site
        self.entities = []

    def start_turn(self):
        self.population_cap = 0
        for e in self.entities:
            if e.abilities.keys().__contains__('Population'):
                self.population_cap += e.abilities['Population']

        if self.population < self.population_cap:
            self.population = int(self.population * 1.02)

        for e in self.entities:
            e.start_turn()
        return

    def end_turn(self):
        for e in self.entities:
            e.end_turn()
        return

    def create_base(self):
        e = Entity(self, entity_dict['City Center'])
        self.entities.append(e)
        return e

    def create_entity(self, entity_info):
        e = Entity(self, entity_info)
        self.entities.append(e)
        return e


class Entity:
    icon = 'Ϫ'
    name = 'Entity'
    move_data = [2, ['Land']]
    cost = 0
    upkeep = 0
    used_movement = 0

    def __init__(self, owner: Faction, entity_info: dict):
        self.owner = owner
        self.faction_color = owner.faction_color
        self.name = entity_info['name']
        self.icon = entity_info['icon']
        self.cost = entity_info['cost']
        self.upkeep = entity_info['upkeep']
        self.move_data = entity_info['movement']
        self.size = entity_info['size']
        self.strength = entity_info['strength']
        self.armor = entity_info['armor']
        self.abilities = {}

        for k in entity_info.keys():
            if optional_entity_keys.__contains__(k):
                self.abilities[k] = entity_info[k]

    def start_turn(self):
        if self.abilities.keys().__contains__('Minerals'):
            self.owner.minerals += self.abilities['Minerals']

        if self.abilities.keys().__contains__('Currency'):
            self.owner.currency += self.abilities['Currency']

        return

    # def process_event(self, event):
    #   if isinstance(event, KeyboardEvent):
    #      if self.abilities.__contains__('constructor') and event.key_code is ':

    def end_turn(self):
        self.owner.currency -= self.upkeep
        self.used_movement = 0


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
            place_entity(f.create_base(), f.origin)
            place_entity(f.create_entity(entity_dict['Constructor']), f.origin)

            faction_colors_c.remove(faction_colors_c[c])
            faction_icons_c.remove(faction_icons_c[i])

        self.factions[0].is_player = True

        self.start_turn()


def create_entity(owner: Faction, tile, icon='#'):
    e = Entity(owner, icon)
    tile.entities.append(e)
    owner.entities.append(e)


def place_entity(entity: Entity, tile: voromap.Tile):
    tile.entities.append(entity)
