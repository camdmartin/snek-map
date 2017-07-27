# *Necessary*
# name: name of entity class, defaults to 'NULL_ENTITY'
# icon: single character displayed on screen, defaults to '/'
# type: entity child class to be created as, type has handlers for unique abilities, default entity
# cost: construction cost in minerals, default 0
# upkeep: per-turn cost in currency, default 0

# *Structures*
# energy_consumption: amount of energy necessary to be active, defaults to 0
# produces_energy: amount of energy given to City Center to be distributed between buildings
# produces_minerals or produces_currency: adds minerals or currency to faction stockpile
#       (note: eventually currency will be produced by population only)
# pop_cap: increases faction pop_cap

# *Entities*
# move_distance: tiles moved per turn
# terrain: what type of terrain it can cross
# size: combat stat, health
# strength: combat stat, power multiplier
# armor: combat stat, casualty divisor

mine_structure = {'name': 'Mine', 'icon': 'Ѫ', 'type': 'structure', 'cost': 50, 'upkeep': 50,
                  'produces_minerals': 10}
solar_structure = {'name': 'Solar Array', 'icon': 'Ξ', 'type': 'structure', 'cost': 50, 'upkeep': 50,
                   'produces_energy': 2}
city_structure = {'name': 'City Center', 'icon': 'ʘ', 'type': 'structure', 'cost': 200, 'upkeep': 50,
                  'produces_energy': 1, 'produces_currency': 1000, 'pop_cap': 25000}
population_structure = {'name': 'Habitat', 'icon': 'Ҧ', 'type': 'structure', 'cost': 50, 'upkeep': 50,
                        'energy_consumption': 1, 'pop_cap': 10000}

constructor = {'name': 'Constructor', 'icon': 'Ɣ', 'type': 'unit', 'cost': 50, 'upkeep': 25,
               'move_distance': 2, 'terrain': 'Land',
               'size': 5, 'strength': 2, 'armor': 10,
               'constructs': [mine_structure, solar_structure, population_structure]}


class Entity:

    data = {'name': '', 'icon': '/', 'type': 'entity', 'cost': 0, 'upkeep': 0}

    def __init__(self, owner, data: dict):
        self.owner = owner
        self.data = data

        for k in data.keys():
            self.data[k] = data[k]

    def start_turn(self):
        return

    def end_turn(self):
        self.owner.currency -= self.data['upkeep']


class Structure(Entity):
    energy_cost = 0
    energy_produced = 0

    structure_data = {'energy_consumption': 0}

    def __init__(self, owner, data: dict):
        for k in self.structure_data.keys():
            self.data[k] = self.structure_data[k]

        super().__init__(owner, data)

    def start_turn(self):
        if self.data.keys().__contains__('produces_minerals'):
            self.owner.minerals += self.data['produces_minerals']

        if self.data.keys().__contains__('produces_currency'):
            self.owner.currency += self.data['produces_currency']

        super().start_turn()


class Unit(Entity):
    used_movement = 0

    unit_data = {'size': 1, 'strength': 1, 'armor': 1, 'move_distance': 1, 'terrain': 'Land'}

    def __init__(self, owner, data: dict):
        for k in self.unit_data.keys():
            self.data[k] = self.unit_data[k]

        super().__init__(owner, data)

    def end_turn(self):
        self.used_movement = 0

        super().end_turn()


def create_entity(owner, data: dict):
    entity_type = data['type']

    if entity_type is 'unit':
        return Unit(owner, data)
    elif entity_type is 'structure':
        return Structure(owner, data)
    else:
        return Entity(owner, data)
