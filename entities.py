import game

# *Necessary*
# name: name of entity class, defaults to 'NULL_ENTITY'
# icon: single character displayed on screen, defaults to '/'
# type: entity child class to be created as, type has handlers for unique abilities, default entity
# cost: construction cost in minerals, default 0
# upkeep: per-turn cost in currency, default 0

# *Structures*
# energy_cost: amount of energy necessary to be active, defaults to 0; negative values means it's a power generator
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
                   'energy_cost': -2}
city_structure = {'name': 'City Center', 'icon': 'ʘ', 'type': 'structure', 'cost': 200, 'upkeep': 50,
                  'energy_cost': -1, 'produces_currency': 1000, 'pop_cap': 25000}
population_structure = {'name': 'Habitat', 'icon': 'Ҧ', 'type': 'structure', 'cost': 50, 'upkeep': 50,
                        'energy_cost': 1, 'pop_cap': 10000}

constructor = {'name': 'Constructor', 'icon': 'Ɣ', 'type': 'unit', 'cost': 50, 'upkeep': 25,
               'move_distance': 2, 'terrain': 'Land',
               'size': 5, 'strength': 2, 'armor': 10,
               'constructs': [mine_structure, solar_structure, population_structure]}


class Entity:

    data = {'name': '', 'icon': '/', 'type': 'entity', 'cost': 0, 'upkeep': 0}

    def __init__(self, owner, location, new_data: dict):
        self.owner = owner
        self.location = location
        self.data = new_data

        # print(self.data)

    def handle_abilities(self):
        return

    def start_turn(self):
        return

    def end_turn(self):
        self.owner.currency -= self.data['upkeep']

    def display_quick(self):
        return [f"{self.data['icon']} {self.data['name']}"]

    def display_details(self):
        return [f'{self.data["icon"]} {self.data["name"]}',
                f'  Cost: {self.data["cost"]}',
                f'  Upkeep: {self.data["upkeep"]}']


class Structure(Entity):

    structure_data = {'energy_cost': 0}

    def __init__(self, owner, location, data: dict):
        for k in self.structure_data.keys():
            self.data[k] = self.structure_data[k]

        super().__init__(owner, location, data)

        for k in self.structure_data.keys():
            if not self.data.keys().__contains__(k):
                self.data[k] = self.structure_data[k]

    def start_turn(self):
        if self.data.keys().__contains__('produces_minerals'):
            self.owner.minerals += self.data['produces_minerals']

        if self.data.keys().__contains__('produces_currency'):
            self.owner.currency += self.data['produces_currency']

        super().start_turn()

    def display_quick(self):
        quick = super().display_quick()

        quick[0] += f' (Energy: {-1 * self.data["energy_cost"]})'
        return quick

    def display_details(self):
        details = super().display_details()

        details[0] += f' (Energy: {-1 * self.data["energy_cost"]})'

        if self.data.keys().__contains__('produces_minerals'):
            details.append(f'   +{self.data["produces_minerals"]} minerals/turn')

        if self.data.keys().__contains__('pop_cap'):
            details.append(f'   +{self.data["pop_cap"]} max population')

        if self.data.keys().__contains__('produces_currency'):
            details.append(f'   +{self.data["produces_currency"]} currency/turn')

        return details


class Unit(Entity):
    used_movement = 0

    unit_data = {'size': 1, 'strength': 1, 'armor': 1, 'move_distance': 1, 'terrain': 'Land'}

    def __init__(self, owner, location, data: dict):
        super().__init__(owner, location, data)

        for k in self.unit_data.keys():
            if not self.data.keys().__contains__(k):
                self.data[k] = self.unit_data[k]

    def end_turn(self):
        self.used_movement = 0

        super().end_turn()

    def handle_abilities(self, event):
        if self.data.keys().__contains__('constructs'):
            if (49 + len(self.data['constructs'])) >= event.key_code >= 49:
                game.create_owned_entity(self.owner, self.location, self.data['constructs'][event.key_code - 49])

    def display_quick(self):
        quick = super().display_quick()

        quick.append(f'   Moved {self.used_movement}/{self.data["move_distance"]}')
        return quick

    def display_details(self):
        details = super().display_details()

        if self.data.keys().__contains__('constructs'):
            details.append('   Constructs:')
            for c in self.data['constructs']:
                details.append(f'      {c["name"]}')

        return details


def create_entity(owner, location, data: dict):
    entity_type = data['type']

    if entity_type is 'unit':
        return Unit(owner, location, data)
    elif entity_type is 'structure':
        return Structure(owner, location, data)
    else:
        return Entity(owner, location, data)
