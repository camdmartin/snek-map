from random import randint
from random import shuffle
from asciimatics.screen import Screen
import matplotlib.path as mplpath
from math import hypot
from math import ceil
from math import sqrt
from scipy import spatial
from scipy.ndimage.filters import gaussian_filter
from numpy import array
import noise
import copy


# TODO:
# terrain types
# precipitation map
# river erosion
# get random tile in continent/region

# terrain_grid = [['Frozen', 'Frozen', 'Frozen', 'Frozen', 'Desert', 'Desert', 'Desert', 'Desert', 'Desert', 'Desert'],
#                 ['Void', 'Frozen', 'Frozen', 'Frozen', 'Desert', 'Desert', 'Desert', 'Desert', 'Desert', 'Desert'],
#                 ['Void', 'Void', 'Frozen', 'Frozen', 'Desert', 'Desert', 'Desert', 'Desert', 'Desert', 'Desert'],
#                 ['Void', 'Void', 'Void', 'Frozen', 'Desert', 'Desert', 'Desert', 'Desert', 'Desert', 'Desert'],
#                 ['Void', 'Void', 'Void', 'Void', 'Forest', 'Forest', 'Forest', 'Rainforest', 'Rainforest', 'Rainforest'],
#                 ['Void', 'Void', 'Void', 'Void', 'Void', 'Forest', 'Forest', 'Rainforest', 'Rainforest', 'Rainforest'],
#                 ['Void', 'Void', 'Void', 'Void', 'Void', 'Void', 'Rainforest', 'Rainforest', 'Rainforest', 'Rainforest'],
#                 ['Void', 'Void', 'Void', 'Void', 'Void', 'Void', 'Void', 'Rainforest', 'Rainforest', 'Rainforest'],
#                 ['Void', 'Void', 'Void', 'Void', 'Void', 'Void', 'Void', 'Void', 'Rainforest', 'Rainforest'],
#                 ['Void', 'Void', 'Void', 'Void', 'Void', 'Void', 'Void', 'Void', 'Void', 'Rainforest']]


class Tile:
    icon = '~'
    type = 'Void'  # Land vs Sea
    terrain = 'Void'  # Desert/Coast/Mountain/Forest/Barren
    color = 15

    temperature = 0
    precipitation = 0

    def __init__(self, x: int, y: int, height: int):
        self.x = x
        self.y = y
        self.height = height
        self.entities = []


class Region:
    terrain = 'None'

    def __init__(self, icon: str, base_height: int, max_height: int, vertices: [[int, int]], tiles: [Tile]):
        self.icon = icon
        self.base_height = base_height
        self.max_height = max_height
        self.vertices = vertices
        self.tiles = tiles

        for t in tiles:
            t.height = self.base_height

    def update_tiles(self):
        for t in self.tiles:
            t.icon = self.icon
            t.type = 'Land'
            if t.height < self.base_height:
                t.height = self.base_height

    def update_tile_terrains(self):
        for t in self.tiles:
            t.terrain = self.terrain

    def get_region_center(self):
        x = [p[0] for p in self.vertices]
        y = [p[1] for p in self.vertices]
        center = (int(sum(x) / len(self.vertices)), int(sum(y) / len(self.vertices)))

        return center

    def set_tile_altitudes(self):
        c = self.get_region_center()
        for t in self.tiles:
            t.height = self.base_height + self.negative_to_zero(
                (self.max_height - self.base_height - int(hypot(c[0] - t.x, c[1] - t.y))))

    def negative_to_zero(self, i: int):
        if i < 0:
            return 0
        else:
            return i


class Continent:
    def __init__(self, regions: [Region], icon: str, color: int):
        self.regions = regions
        self.icon = icon
        self.color = color

    def set_tile_icons_to_continent_icon(self):
        for r in self.regions:
            for t in r.tiles:
                t.icon = self.icon

    def set_tile_icons_to_region_icon(self):
        for r in self.regions:
            for t in r.tiles:
                t.icon = r.icon


class WorldMap:
    world: [[Tile]]
    voronoi_diagram: spatial.Voronoi
    continents: [Continent]
    regions: [Region]
    seeds: [(int, int)]

    selected_entity = 0
    is_anchored = False
    anchor: Tile

    region_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
                      'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
                      'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4',
                      '5', '6', '7', '8', '9', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '=', '+',
                      '`', '[', '{', ']', '}', '|', '\\', '/', '<', ',', '.', '>', '?']

    generation_dict = {'width': 80, 'height': 40,
                       'min_altitude': 0, 'max_altitude': 9,
                       'sea_level': 3,
                       'seed_count': 100,
                       'fuzz_percent': 5,
                       'mountains_per_continent': 1, 'mountain_range_length': 3,
                       'continent_count': 4, 'percent_land': 50,
                       'noise_weight': 3, 'noise_scale': 0.1,
                       'heat_noise_scale': 0.075, 'max_temp': 7, 'temp_variance': 3, 'min_temp': 3,
                       'base_precip': 5, 'precip_variance': 5, 'precip_noise_scale': 0.05}

    selected_tile: Tile
    color_filter = 'Terrain'

    def __init__(self, width: int, height: int, min_altitude: int, sea_level: int, max_altitude: int, seed_count: int):
        self.generation_dict['width'] = width
        self.generation_dict['height'] = height
        self.generation_dict['min_altitude'] = min_altitude
        self.generation_dict['max_altitude'] = max_altitude
        self.generation_dict['sea_level'] = sea_level
        self.generation_dict['seed_count'] = seed_count

        self.seeds = []
        self.set_seeds()

        self.voronoi_diagram = spatial.Voronoi(self.seeds)
        self.world = self.create_base_map(self.generation_dict['width'], self.generation_dict['height'],
                                          self.generation_dict['min_altitude'])
        self.regions = []
        self.continents = []

        self.regenerate()

        self.selected_tile = self.tile_at_point(0, 0)

        self.terrain_filter()

        self.anchor = self.tile_at_point(0, 0)

    # basic generation methods

    def regenerate(self):
        self.regions = []
        self.continents = []
        self.seeds = []

        self.set_seeds()

        self.voronoi_diagram = spatial.Voronoi(self.seeds)
        self.world = self.create_base_map(self.generation_dict['width'], self.generation_dict['height'],
                                          self.generation_dict['min_altitude'])

        self.regions = self.set_world_regions(self.voronoi_diagram)

        self.regions = self.generate_continents()

        self.assign_tiles_to_regions()
        self.update_region_tiles()

        self.gen_mountain_ranges()

        self.world = self.apply_simplex_noise()
        self.world = self.gaussian_smooth()

        # self.set_heat_map()
        # ;self.set_precipitation_map()
        # self.set_tile_terrains()

        self.set_sea_tiles()

        self.truncate_tile_heights()

        self.terrain_filter()

        self.selected_tile = self.world[0][0]

    def set_seeds(self):
        for i in range(0, self.generation_dict['seed_count']):
            self.seeds.append([randint(0, self.generation_dict['width'] - 1), randint(0, self.generation_dict['height'] - 1)])

    def create_base_map(self, width: int, height: int, min_altitude: int):
        new_map = []
        for i in range(0, height):
            new_map.append([])
            for j in range(0, width):
                t = Tile(j, i, min_altitude)
                new_map[i].append(t)
        return new_map

    def filter_valid_regions(self, vor: spatial.Voronoi):
        valid_regions = []

        for r in vor.regions:
            region_x_vertices = []
            region_y_vertices = []
            for i in r:
                region_x_vertices.append(vor.vertices[i][0])
                region_y_vertices.append(vor.vertices[i][1])

            if -1 not in r and all(0 < i < self.generation_dict['width'] for i in region_x_vertices) \
                    and all(0 < i < self.generation_dict['height'] for i in region_y_vertices) and len(r) > 0:
                valid_regions.append(r)

        # print(valid_regions)

        return valid_regions

    def set_world_regions(self, vor: spatial.Voronoi):
        valid_regions = self.filter_valid_regions(vor)

        temp_regions = []

        a = 0
        for r in valid_regions:
            t = []
            v = []
            for i in r:
                v.append([int(s) for s in self.voronoi_diagram.vertices[i].tolist()])

            reg = Region(self.region_letters[a], self.generation_dict['sea_level'] + 1,
                         randint(self.generation_dict['sea_level'] + 1, self.generation_dict['max_altitude']),
                         v, t)
            temp_regions.append(reg)
            a += 1

        return temp_regions

    def assign_tiles_to_regions(self):
        for i in self.world:
            for j in i:
                in_region = False
                for r in self.regions:
                    if len(r.vertices) > 0:
                        path = mplpath.Path(r.vertices)

                        if path.contains_point((j.x, j.y)):
                            j.icon = r.icon
                            r.tiles.append(j)
                            in_region = True
                            break
                if in_region is False:
                    j = Tile(j.x, j.y, self.generation_dict['min_altitude'])

        # self.update_region_tiles()

    # climate generation

    def set_heat_map(self):
        noise_map = self.world

        equator = int(self.generation_dict['height'] / 2)
        min_t = self.generation_dict['min_temp']

        for i in noise_map:
            for j in i:
                j.temperature = int(self.generation_dict['max_temp'] - (min_t * (abs(j.y - equator) / equator))**1.1 +
                                    int(self.generation_dict['temp_variance'] *
                                        (noise.snoise2(j.x * self.generation_dict['heat_noise_scale'],
                                                       j.y * self.generation_dict['heat_noise_scale']))))

    def set_precipitation_map(self):
        noise_map = self.world

        for i in noise_map:
            for j in i:
                j.precipitation = int(self.generation_dict['base_precip'] + int(self.generation_dict['precip_variance'] *
                                      noise.snoise2(j.x * self.generation_dict['precip_noise_scale'],
                                                    j.y * self.generation_dict['precip_noise_scale'])))
                if j.precipitation > j.temperature:
                    j.precipitation = j.temperature

    # def set_tile_terrains(self):
        # for i in self.world:
            # for j in i:
                # j.terrain = terrain_grid[j.precipitation][j.temperature]

    # updating methods

    def update_region_tiles(self):
        for r in self.regions:
            r.update_tiles()
            for t in r.tiles:
                t.icon = self.world[t.y][t.x].icon
                t.height = self.world[t.y][t.x].height

    def update_world_tiles(self):
        for r in self.regions:
            r.update_tiles()
            for t in r.tiles:
                self.world[t.y][t.x].icon = t.icon
                self.world[t.y][t.x].height = t.height

    def update_tile_terrains(self):
        for c in self.continents:
            for r in c.regions:
                r.update_tile_terrains()

    # a few helper methods

    def tile_at_point(self, x: int, y: int):
        if x >= self.generation_dict['width']:
            x -= self.generation_dict['width']

        if y >= self.generation_dict['height']:
            y -= self.generation_dict['height']

        return self.world[y][x]

    def distance(self, a: (int, int), b: (int, int)):
        return sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def is_between(self, a: (int, int), c: (int, int), b: (int, int)):
        return int(self.distance(a, c) + self.distance(c, b)) == int(self.distance(a, b))

    def adjacent_tiles(self, t: Tile):
        adjacent = [
            self.tile_at_point(t.x - 1, t.y - 1),
            self.tile_at_point(t.x, t.y - 1),
            self.tile_at_point(t.x + 1, t.y - 1),
            self.tile_at_point(t.x - 1, t.y),
            self.tile_at_point(t.x + 1, t.y),
            self.tile_at_point(t.x + 1, t.y - 1),
            self.tile_at_point(t.x + 1, t.y),
            self.tile_at_point(t.x + 1, t.y + 1)
        ]
        shuffle(adjacent)
        return adjacent

    def adjacent_regions(self, r: Region):
        adjacent = []

        for s in self.regions:
            if any(i in s.vertices for i in r.vertices):
                adjacent.append(s)

        return adjacent

    def get_region_of_tile(self, t: Tile):
        for r in self.regions:
            if len(r.vertices) > 0:
                path = mplpath.Path(r.vertices)

                if path.contains_point((t.x, t.y)):
                    return r
        return None

    def get_continent_of_region(self, r: Region):
        for c in self.continents:
            if c.regions.__contains__(r):
                return c
        return None

    def get_continent_of_tile(self, t: Tile):
        for c in self.continents:
            all_tiles = []
            for r in c.regions:
                for t in r.tiles:
                    all_tiles.append(t)
            if all_tiles.__contains__(t):
                return c

        return None

    def get_random_land_tile(self):
        c = self.continents[randint(0, len(self.continents) - 1)]
        r = c.regions[randint(0, len(c.regions) - 1)]
        while len(r.tiles) <= 0:
            r = c.regions[randint(0, len(c.regions) - 1)]
        t = r.tiles[randint(0, len(r.tiles) - 1)]

        return t

    def swap_tile_region(self, t: Tile, swap_to: Region):
        swap_from = self.get_region_of_tile(t)
        swap_from.tiles.remove(t)
        swap_to.tiles.append(t)

    # tile color filters
    def continent_filter(self):
        for c in self.continents:
            all_tiles = []
            for r in c.regions:
                for t in r.tiles:
                    t.color = c.color

    def heat_filter(self):
        temperature_colors = [15, 195, 87, 86, 84, 46, 40, 190, 226, 184, 178]

        for i in self.world:
            for j in i:
                if j.type is 'Land':
                    j.color = temperature_colors[j.temperature]

    def rain_filter(self):
        precipitation_colors = [224, 222, 227, 190, 119, 120, 48, 46, 34, 28, 22]

        for i in self.world:
            for j in i:
                if j.type is 'Land':
                    j.color = precipitation_colors[j.precipitation]

    def get_terrain_color(self, tile):
        forest_colors = [23, 29, 22, 28, 34, 40, 46, 47, 48]
        ocean_colors = [17, 18, 19, 20, 21, 33, 45, 201, 201, 201]
        mountain_colors = [201, 201, 201, 233, 235, 237, 241, 248, 252, 255]
        desert_colors = [3, 186, 190, 226, 227, 228, 229, 230, 252, 255]
        rainforest_colors = [24, 30, 36, 35, 41, 47, 83, 77]
        frozen_colors = [63, 69, 75, 81, 87, 253, 255]

        color_table = [201, 201, 201, 201, 201, 201, 201, 201, 201]

        if tile.type is not 'Land':
            color_table = ocean_colors
        elif tile.height >= 6:
            color_table = mountain_colors
        elif tile.terrain is 'Desert':
            color_table = desert_colors
        elif tile.terrain is 'Forest':
            color_table = forest_colors
        elif tile.terrain is 'Rainforest':
            color_table = rainforest_colors
        elif tile.terrain is 'Frozen':
            color_table = frozen_colors
        else:
            color_table = forest_colors

        return color_table[tile.height]

    def terrain_filter(self):
        for i in self.world:
            for j in i:
                j.color = self.get_terrain_color(j)

    # region modification

    def get_seed_regions(self):
        temp_regions = copy.deepcopy(self.regions)
        seed_regions = []

        # pick initial region
        picked_region = False
        while picked_region is False:
            i = self.world[randint(0, self.generation_dict['height'] - 1)][randint(0, self.generation_dict['width'] - 1)]
            r = self.get_region_of_tile(i)

            if r is not None:
                picked_region = True
                seed_regions.append(r)

                for t in temp_regions:
                    if t.icon is r.icon:
                        temp_regions.remove(t)
                        break

                for a in self.adjacent_regions(r):
                    for t in temp_regions:
                        if t.icon is a.icon:
                            temp_regions.remove(t)
                            break

        while len(seed_regions) < self.generation_dict['continent_count']:
            shuffle(temp_regions)
            r = temp_regions[0]

            seed_regions.append(r)

            for t in temp_regions:
                if t.icon is r.icon:
                    temp_regions.remove(t)
                    break

            for a in self.adjacent_regions(r):
                for t in temp_regions:
                    if t.icon is a.icon:
                        temp_regions.remove(t)
                        break

        for s in seed_regions:
            for t in s.tiles:
                t.height = 9

        return seed_regions

    def generate_continents(self):
        total_regions = []
        seed_regions = self.get_seed_regions()

        for r in seed_regions:
            self.continents.append(Continent([r], r.icon, randint(0, 256)))
            total_regions.append(r)

        region_quota = int(len(self.regions) * (self.generation_dict['percent_land'] / 100))

        while len(total_regions) < region_quota:
            shuffle(self.continents)

            for c in self.continents:
                append_to_c = []

                for r in c.regions:
                    adjacent = self.adjacent_regions(r)
                    temp = adjacent

                    invalid_regions = []
                    for d in self.continents:
                        if d is not c:
                            adjacent_to_continent = []
                            for s in d.regions:
                                adjacent_to_continent += self.adjacent_regions(s)
                            invalid_regions += adjacent_to_continent

                    for a in temp:
                        if invalid_regions.__contains__(a):
                            adjacent.remove(a)

                    for a in adjacent:
                        if len(total_regions) < region_quota and not total_regions.__contains__(a) \
                                and not append_to_c.__contains__(a):
                            total_regions.append(a)
                            append_to_c.append(a)
                            # print(len(total_regions))

                c.regions += append_to_c

        return total_regions

    def set_continent_mountain_ranges(self, continent: Continent):
        generated_regions = []

        for i in range(0, self.generation_dict['mountains_per_continent']):
            range_lines = []
            i = randint(0, len(continent.regions) - 1)
            continent.regions[i].terrain = 'Mountain'
            t = continent.regions[i]
            generated_regions.append(t)
            c = t.get_region_center()
            previous_point = c

            for j in range(0, self.generation_dict['mountain_range_length']):
                adjacent = self.adjacent_regions(t)
                shuffle(adjacent)
                for r in generated_regions:
                    if adjacent.__contains__(r):
                        adjacent.remove(r)

                if len(adjacent) > 0:
                    adjacent[0].terrain = 'Mountain'
                    t = adjacent[0]
                    generated_regions.append(t)
                    c = t.get_region_center()
                    range_lines.append((previous_point, c))
                    previous_point = c

            # print(range_lines)

            for k in self.world:
                for l in k:
                    for m in range_lines:
                        if self.is_between(m[0], (l.x, l.y), m[1]):
                            l.height = self.generation_dict['max_altitude']

    def gen_mountain_ranges(self):
        for c in self.continents:
            self.set_continent_mountain_ranges(c)

    def set_sea_tiles(self):
        for i in self.world:
            for j in i:
                if j.type != 'Land':
                    j.type = 'Sea'
                    if j.height > self.generation_dict['sea_level']:
                        j.height = self.generation_dict['sea_level']

    def truncate_tile_heights(self):
        for i in self.world:
            for j in i:
                if j.height > self.generation_dict['max_altitude']:
                    j.height = self.generation_dict['max_altitude']
                elif j.height < self.generation_dict['min_altitude']:
                    j.height = self.generation_dict['min_altitude']

    def gaussian_smooth(self):
        blur_world = self.world
        height_map = []

        for i in blur_world:
            height_map.append([])
            for j in i:
                height_map[-1].append(j.height)

        blurred = gaussian_filter(array(height_map), sigma=0.5)

        y_index = 0
        for i in blurred:
            x_index = 0
            for j in i:
                blur_world[y_index][x_index].height = j
                x_index += 1
            y_index += 1

        return blur_world

    def apply_simplex_noise(self):
        noise_map = self.world

        for i in noise_map:
            for j in i:
                j.height += int(
                    self.generation_dict['noise_weight'] *
                    (noise.snoise2(j.x * self.generation_dict['noise_scale'],
                                   j.y * self.generation_dict['noise_scale'])))

        return noise_map

    # entity manipulation

    def start_movement(self, location, entity):
        self.is_anchored = True
        self.anchor = location

        self.selected_entity = entity

    def end_movement(self):
        self.move_entity(self.selected_entity, self.anchor, self.selected_tile)
        self.is_anchored = False

    def move_entity(self, entity, origin, destination):
        if origin.entities.__contains__(entity) and entity.used_movement < entity.data['move_distance']:
            origin.entities.remove(entity)
            destination.entities.append(entity)
            entity.location = destination
            entity.used_movement += ceil(self.distance((origin.x, origin.y), (destination.x, destination.y)))
            return True

        return False

    def reconcile_entity_locations(self):
        for i in self.world:
            for j in i:
                for e in j.entities:
                    e.location = j

    # printing methods

    def print_region_icons(self, screen: Screen):
        while True:
            y_index = 0
            for i in self.world:
                x_index = 0
                for j in i:
                    screen.print_at(f'{j.icon}', x_index * 2, y_index)
                    x_index += 1
                y_index += 1

            ev = screen.get_key()
            if ev in (ord('Q'), ord('q')):
                return
            screen.refresh()

    def print_continent_icons(self, screen: Screen):
        for c in self.continents:
            c.set_tile_icons_to_continent_icon()

        while True:
            y_index = 0
            for i in self.world:
                x_index = 0
                for j in i:
                    screen.print_at(f'{j.icon}', x_index * 2, y_index)
                    x_index += 1
                y_index += 1

            ev = screen.get_key()
            if ev in (ord('Q'), ord('q')):
                for c in self.continents:
                    c.set_tile_icons_to_region_icon()
                return
            screen.refresh()

    def print_world_heights(self, screen: Screen):
        for c in self.continents:
            c.set_tile_icons_to_continent_icon()

        forest_colors = [23, 29, 22, 28, 34, 40, 46, 83, 85]
        ocean_colors = [17, 18, 19, 20, 21, 33, 45, 201, 201, 201]
        mountain_colors = [201, 201, 201, 233, 235, 237, 241, 248, 252, 255]
        desert_colors = [3, 186, 190, 226, 227, 228, 229, 230, 252, 255]  # [130, 136, 172, 178, 220, 226, 228, 230, 252, 255]

        color_table = [201, 201, 201, 201, 201, 201, 201, 201, 201]

        while True:
            y_index = 0
            for i in self.world:
                x_index = 0
                for j in i:
                    if j.type is not 'Land':
                        color_table = ocean_colors
                    elif j.terrain is 'Desert':
                        color_table = desert_colors
                    elif j.height < 6:
                        color_table = forest_colors
                    elif j.height >= 6:
                        color_table = mountain_colors

                    color = color_table[j.height]

                    screen.print_at(f'{j.height}{j.icon}', x_index * 2, y_index, colour=16, bg=color)
                    x_index += 1
                y_index += 1

            ev = screen.get_key()
            if ev in (ord('Q'), ord('q')):
                # for c in self.continents:
                    # c.set_tile_icons_to_region_icon()
                return
            screen.refresh()

    def print_world_tile_types(self, screen: Screen):
        while True:
            y_index = 0
            for i in self.world:
                x_index = 0
                for j in i:
                    if j.type == 'Land':
                        color = Screen.COLOUR_GREEN
                    else:
                        color = Screen.COLOUR_BLUE

                    screen.print_at(f'{j.height}', x_index * 2, y_index, color)
                    x_index += 1
                y_index += 1

            ev = screen.get_key()
            if ev in (ord('Q'), ord('q')):
                return
            screen.refresh()

    def print_map_to_console(self):
        for i in self.world:
            for j in i:
                print(f'{j.icon}' + ' ')
            print('\n')