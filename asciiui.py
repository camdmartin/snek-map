import asciimatics
import asciimatics.widgets as widgets
from asciimatics.screen import Screen
from asciimatics.scene import Scene
import voromap
import game
import entities
import os
import copy

# TODO:
# resize console on map regeneration
# restrict map generation variables to positive integers
# fix odd backspace behavior on text input field
# help command
# continent icon missing from tile display
# biomes (precipitation and temperature maps)
# resource spread
# mining/energy generation/construction


vm = voromap.WorldMap(80, 40, 0, 3, 9, 100)
model = game.Game(vm, 6)


class InfoBar(widgets.Widget):

    def __init__(self, game_model):
        super(InfoBar, self).__init__(name='InfoBar')
        self._model = game_model

    def reset(self):
        self._model = model
        return

    def process_event(self, event):
        return event

    def update(self, frame_no):
        player_faction = next((f for f in self._model.factions if f.is_player), self._model.factions[0])
        offset = 0

        self._frame.canvas.print_at(f'Turn {self._model.turn}', self._x + offset, self._y, colour=Screen.COLOUR_CYAN)
        offset += 10

        self._frame.canvas.print_at(f'₡{player_faction.currency}', self._x + offset, self._y,
                                    colour=Screen.COLOUR_YELLOW)
        offset += 10

        self._frame.canvas.print_at(f'Ѫ{player_faction.minerals}', self._x + offset, self._y, colour=Screen.COLOUR_RED)
        offset += 10

        self._frame.canvas.print_at(f'Population {player_faction.population}/{player_faction.population_cap}', self._x + offset, self._y,
                                    colour=Screen.COLOUR_GREEN)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    def required_height(self, offset, width):
        return 1


class ConsoleView(widgets.Widget):
    def __init__(self, height):
        super(ConsoleView, self).__init__(name="Console")

        self.height = height
        self.text_lines = []
        for h in range(0, height):
            self.text_lines.append('')

        self.view_bottom = 0

    def reset(self):
        self.text_lines = []
        for h in range(0, self.height):
            self.text_lines.append('')
        self.view_bottom = 0

    def process_event(self, event):
        if isinstance(event, asciimatics.event.KeyboardEvent):
            global_shortcuts(event)

            if event.key_code == Screen.KEY_UP:
                if self.view_bottom < len(self.text_lines):
                    self.view_bottom += 1
                return None
            elif event.key_code == Screen.KEY_DOWN:
                if self.view_bottom > 0:
                    self.view_bottom -= 1
                return None
        return event

    def required_height(self, offset, width):
        return self.height

    def update(self, frame_no):
        if self._has_focus is True:
            style = Screen.A_BOLD
        else:
            style = Screen.A_NORMAL

        if self.view_bottom + self.height > len(self.text_lines):
            view_top = len(self.text_lines) - 1
        else:
            view_top = self.view_bottom + self.height

        line_index = self.height - 1
        for l in self.text_lines[self.view_bottom:view_top]:
            self._frame.canvas.print_at("> " + l, self._x, self._y + line_index, colour=Screen.COLOUR_WHITE, attr=style,
                                        bg=Screen.COLOUR_BLACK)
            line_index -= 1

    def add_line(self, text: str):
        self.text_lines.insert(0, text)
        self.view_bottom = 0
        self.update(0)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value


class EntityView(widgets.Widget):

    def __init__(self, entity_list, location, game_model):
        super(EntityView, self).__init__('Entities')
        self._entity_list = entity_list
        self.location = location
        self.selected_entity = entities.Entity(game_model.factions[0], {})
        self._model = game_model

        self._is_tab_stop = False

    def update(self, frame_no):
        if len(self.location.entities) > 0 and not self.location.entities.__contains__(self.selected_entity):
            self.selected_entity = self.location.entities[0]

        line = 0

        self._frame.canvas.print_at('Selected', self._x, self._y + line, colour=Screen.COLOUR_WHITE, attr=Screen.A_BOLD)
        line += 1

        self._frame.canvas.print_at(f'({self.location.x}, {self.location.y})',
                                    self._x, self._y + line, colour=Screen.COLOUR_WHITE)
        line += 1
        self._frame.canvas.print_at(f'({self.location.type}, Height {self.location.height})',
                                    self._x, self._y + line, colour=Screen.COLOUR_WHITE, attr=Screen.A_BOLD)

        line += 1
        ci = vm.get_continent_of_tile(self.location).icon
        self._frame.canvas.print_at(f'Region: {self.location.icon}, '
                                    f'Continent: {ci}',
                                    self._x, self._y + line, colour=Screen.COLOUR_WHITE, attr=Screen.A_BOLD)
        line += 2

        self._frame.canvas.print_at('Factions', self._x, self._y + line, colour=Screen.COLOUR_WHITE, attr=Screen.A_BOLD)
        line += 1

        for f in self._model.factions:
            c = copy.copy(f.color)
            self._frame.canvas.paint(f'{f.faction_icon} {f.color}: ({f.origin.x}, {f.origin.y})',
                                     self._x, self._y + line, colour=c)
            line += 1

        line += 1

        self._frame.canvas.print_at(f'Entities', self._x, self._y + line, colour=Screen.COLOUR_WHITE,
                                    attr=Screen.A_BOLD)
        line += 1

        temp_list = []

        if self._model.world_map.is_anchored:
            temp_list.append(self._model.world_map.selected_entity)
        else:
            temp_list = self._entity_list

        for e in temp_list:
            color = e.owner.color

            if e is self.selected_entity and self._has_focus:
                e_color = Screen.COLOUR_BLACK
                e_bg = color
            else:
                e_color = color
                e_bg = Screen.COLOUR_BLACK

            icon = e.data['icon']
            name = e.data['name']

            self._frame.canvas.print_at(f'{icon}: {name}', self._x, self._y + line, colour=e_color,
                                        bg=e_bg)
            line += 1

            self._frame.canvas.print_at(f'    Owner: {color}', self._x, self._y + line,
                                        colour=e_color, bg=e_bg)

            line += 1

            if isinstance(e, entities.Unit):
                move = e.data['move_distance']
                self._frame.canvas.print_at(f'    Moved {e.used_movement}/{move}', self._x, self._y + line,
                                            colour=e_color, bg=e_bg)
                line += 1

        line += 1

        name = self.selected_entity.data.get('name', 'null')
        color = self.selected_entity.owner.color

        self._frame.canvas.print_at(f'{name}', self._x, self._y + line,
                                    colour=color, attr=Screen.A_BOLD)
        line += 1

        # for a in self.selected_entity.abilities.keys():
        #     if isinstance(self.selected_entity.abilities[a], list):
        #         self._frame.canvas.print_at(f'{a}:', self._x, self._y + line, colour=self.selected_entity.color)
        #         line += 1
        #
        #         for b in self.selected_entity.abilities[a]:
        #             self._frame.canvas.print_at(f'  {b}', self._x, self._y + line,
        #                                         colour=self.selected_entity.color)
        #             line += 1
        #     else:
        #         self._frame.canvas.print_at(f'{a}: {self.selected_entity.abilities[a]}', self._x, self._y + line,
        #                                     colour=self.selected_entity.color)
        #         line += 1

    def reset(self):
        self.selected_entity = entities.Entity(self._model.factions[0], {})
        self._entity_list = []

    def process_event(self, event):
        if isinstance(event, asciimatics.event.KeyboardEvent):
            global_shortcuts(event)

            if self.selected_entity.data.get('name', '/') != '/':
                entity_index = self.location.entities.index(self.selected_entity)

                if event.key_code == Screen.KEY_DOWN:
                    if entity_index != len(self.location.entities) - 1:
                        self.selected_entity = self.location.entities[entity_index + 1]
                    else:
                        self.selected_entity = self.location.entities[0]
                    return None
                elif event.key_code == Screen.KEY_UP:
                    if entity_index != 0:
                        self.selected_entity = self.location.entities[entity_index - 1]
                    else:
                        self.selected_entity = self.location.entities[-1]

                    return None
                elif event.key_code == 10 and isinstance(self.selected_entity, entities.Unit) :
                    self._model.world_map.start_movement(self.location, self.selected_entity)
                    self._frame.switch_focus(self._frame._layouts[0], 0, 0)
                    return event
                elif event.key_code == Screen.KEY_ESCAPE:
                    self._frame.switch_focus(self._frame._layouts[0], 0, 0)
                    return None

        return event

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    def required_height(self, offset, width):
        return len(self._entity_list) * 4


class VoromapView(widgets.Widget):

    show_heights = False
    show_icons = False

    def __init__(self, world_map: voromap.WorldMap, console: ConsoleView, entity_display: EntityView):
        super(VoromapView, self).__init__(name="World")

        self.world_map = world_map
        self.console = console
        self.entity_display = entity_display

        self.world_map.terrain_filter()
        self.anchor = self.world_map.tile_at_point(0, 0)
        self.generation_dict_backup = copy.copy(self.world_map.generation_dict)

        self.reduce_cpu = True

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    def reset(self):
        self.world_map.generation_dict = self.generation_dict_backup

        return None

    def update(self, frame_no):

        for i in self.world_map.world:
            for j in i:
                icon1 = icon2 = '█'
                icon1_color = icon2_color = j.color
                icon1_attr = icon2_attr = Screen.A_NORMAL
                icon1_bg = icon2_bg = j.color

                if len(j.entities) > 0:
                    structures = []
                    units = []

                    for e in j.entities:
                        if isinstance(e, entities.Structure):
                            structures.append(e)
                        elif isinstance(e, entities.Unit):
                            units.append(e)

                    if len(structures) > 0 and len(units) == 0:
                        icon2 = structures[-1].data['icon']
                        icon2_color = 0
                        icon2_bg = structures[-1].owner.color

                        icon1 = ' '
                        icon1_bg = icon2_bg
                    elif len(units) > 0 and len(structures) == 0:
                        icon1 = units[-1].data['icon']
                        icon1_color = 0
                        icon1_bg = units[-1].owner.color

                        icon2 = ' '
                        icon2_bg = icon1_bg
                    else:
                        icon1 = units[-1].data['icon']
                        icon1_color = 0
                        icon1_bg = units[-1].owner.color

                        icon2 = structures[-1].data['icon']
                        icon2_color = 0
                        icon2_bg = structures[-1].owner.color
                elif self.show_icons:
                    icon1 = j.icon
                    icon1_color = 0

                if self.show_heights:
                    icon2 = j.precipitation
                    icon2_color = 0

                if j is self.world_map.selected_tile:
                    if self._has_focus:
                        sel_color = 201
                    else:
                        sel_color = 219

                    icon1_bg = icon2_bg = sel_color
                    if icon1 == '█':
                        icon1_color = sel_color
                    if icon2 == '█':
                        icon2_color = sel_color

                self._frame.canvas.paint(f'{icon1}{icon2}', (self._x + j.x) * 2, self._y + j.y,
                                         colour_map=[(icon1_color, icon1_attr, icon1_bg),
                                                     (icon2_color, icon2_attr, icon2_bg)])

                if self.world_map.is_anchored and isinstance(self.world_map.selected_entity, entities.Unit):
                    move_distance = self.world_map.selected_entity.data['move_distance']
                    move_terrain = self.world_map.selected_entity.data['terrain']

                    if move_distance > 0 and vm.distance((j.x, j.y),
                                                             (self.world_map.anchor.x, self.world_map.anchor.y)) \
                            <= move_distance and move_terrain is j.type:
                        self._frame.canvas.highlight(j.x * 2, j.y, 2, 1, fg=226, bg=icon1_bg, blend=70)

    def handle_arrow_input(self, event):
        key_code = event.key_code
        t = self.world_map.selected_tile
        location_changed = False
        anchored = self.world_map.is_anchored

        if key_code is Screen.KEY_LEFT:
            location_changed = self.move_cursor(-1, 0, anchored)
        elif key_code is Screen.KEY_RIGHT:
            location_changed = self.move_cursor(1, 0, anchored)
        elif key_code is Screen.KEY_UP:
            location_changed = self.move_cursor(0, -1, anchored)
        elif key_code is Screen.KEY_DOWN:
            location_changed = self.move_cursor(0, 1, anchored)
        elif key_code == 393:
            location_changed = self.move_cursor(-10, 0, anchored)
        elif key_code == 402:
            location_changed = self.move_cursor(10, 0, anchored)
        elif key_code == 337:
            location_changed = self.move_cursor(0, -10, anchored)
        elif key_code == 336:
            location_changed = self.move_cursor(0, 10, anchored)

        if location_changed:
            self.entity_display.reset()

            self.entity_display.location = self.world_map.selected_tile
            self.entity_display._entity_list = self.world_map.selected_tile.entities

            self.entity_display.update(0)

            # self.console.add_line(
            # text=f"Selected: ({self.world_map.selected_tile.x}, {self.world_map.selected_tile.y})")
            self.update(0)

    def move_cursor(self, dx, dy, anchored):
        s = self.world_map.selected_tile
        d = self.world_map.tile_at_point(s.x + dx, s.y + dy)

        if anchored:
            a = self.world_map.anchor
            if self.world_map.distance((a.x, a.y), (s.x + dx, s.y + dy)) > \
                    self.world_map.selected_entity.data['move_distance'] \
                    or not self.world_map.selected_entity.data['terrain'] is d.type:
                return False

        try:
            self.world_map.selected_tile = self.world_map.tile_at_point(s.x + dx, s.y + dy)
            location_changed = True
        except IndexError:
            location_changed = False

        return location_changed

    def process_event(self, event):
        if self._has_focus and isinstance(event, asciimatics.event.KeyboardEvent):
            global_shortcuts(event)

            t = self.world_map.selected_tile

            if event.key_code in (Screen.KEY_LEFT, Screen.KEY_RIGHT, Screen.KEY_UP, Screen.KEY_DOWN,
                                  393, 402, 337, 336):
                self.handle_arrow_input(event)
                return None
            elif event.key_code == 10:
                if self.world_map.is_anchored:
                    self.world_map.end_movement()
                    self.update(0)
                    return None
                else:
                    self.blur()
                    self._frame.switch_focus(self._frame._layouts[0], 1, 0)
                return event
            elif event.key_code == Screen.KEY_ESCAPE:
                if self.world_map.is_anchored:
                    self.world_map.is_anchored = False
                    self.update(0)
                    return None
            else:
                self.console.add_line(str(event.key_code))
                return event
        else:
            return event

    def required_height(self, offset, width):
        return self.world_map.generation_dict['height']


class TextInputView(widgets.Text):
    commands = ['filter', 'f', 'Filter', 'F',
                'regen', 'rg', 'Regen', 'RG',
                'height', 'h', 'Height', 'H',
                'icon', 'i', 'Icon', 'I',
                'genvars', 'gv', 'GenVars', 'GV',
                'edit', 'e', 'Edit', 'E',
                'end', 'n', 'End', 'N']
    raw_command = ''

    def __init__(self, game_model, map_display, console):
        super(TextInputView, self).__init__(name='Input')
        self._label = '>'
        self._model = game_model
        self.console = console
        self.map_display = map_display
        self.custom_colour = 'edit_text'

    def handle_command(self, command):
        command_array = command.split(' ')
        if len(command_array) > 0:
            if self.commands.__contains__(command_array[0]):
                main_command = command_array.pop(0)

                if main_command in ('filter', 'f', 'Filter', 'F'):
                    if command_array[0] in ('terrain', 't', 'Terrain', 'T'):
                        self._model.world_map.terrain_filter()
                        self.console.add_line('Terrain filter on.')
                    elif command_array[0] in ('continent', 'c', "Continent", 'C'):
                        self._model.world_map.continent_filter()
                        self.console.add_line('Continent filter on.')
                    elif command_array[0] in ('heat', 'h', "Heat", 'H'):
                        self._model.world_map.heat_filter()
                        self.console.add_line('Heat filter on.')
                    elif command_array[0] in ('precip', 'p', "Precip", 'P'):
                        self._model.world_map.rain_filter()
                        self.console.add_line('Precipitation filter on.')
                    else:
                        self.console.add_line('Invalid filter type.')

                elif main_command in ('regen', 'rg', 'Regen', 'RG'):
                    self._model.create_new_game(True)
                    # self.console.height = Screen.height - self._model.world_map.generation_dict['height'] - 1
                    self.console.add_line('World regenerated.')
                elif main_command in ('height', 'h', 'Height', 'H'):
                    self.map_display.show_heights = not self.map_display.show_heights
                    self.console.add_line(f'Showing heights: {self.map_display.show_heights}')
                    self.map_display.update(0)
                elif main_command in ('icon', 'i', 'Icon', 'I'):
                    self.map_display.show_icons = not self.map_display.show_icons
                    self.console.add_line(f'Showing icons: {self.map_display.show_icons}')
                    self.map_display.update(0)
                elif main_command in ('genvars', 'gv', 'GenVars', 'GV'):
                    for i in self.map_display.world_map.generation_dict:
                        self.console.add_line(f'{i}: {self.map_display.world_map.generation_dict[i]}')
                elif main_command in ('edit', 'e', 'Edit', 'E'):
                    if command_array[0] in self.map_display.world_map.generation_dict.keys() and len(command_array) > 1 \
                            and self.test_valid_int(command_array[1]):
                        self.map_display.world_map.generation_dict[command_array[0]] = int(command_array[1])
                        self.console.add_line(f'{command_array[0]} set to {command_array[1]}')
                    else:
                        self.console.add_line('Input a valid generation variable and integer value.')
                elif main_command in ('end', 'n', 'End', 'N'):
                    self._model.end_turn()
                    self._model.start_turn()
                    self.console.add_line(f'Turn {self._model.turn}')
            else:
                self.console.add_line('Invalid command.')

    def test_valid_int(self, s):
        try:
            int(s)
        except ValueError:
            return False
        return True

    def process_event(self, event):
        if isinstance(event, asciimatics.event.KeyboardEvent):
            global_shortcuts(event)

            if event.key_code == 10:
                raw_command = self._value
                self.handle_command(raw_command)
                self._value = ''
                self.update(0)
                self.map_display.update(0)
            else:
                return super(TextInputView, self).process_event(event)
        else:
            return event

        return event


class GameView(widgets.Frame):
    def __init__(self, screen, game_model):
        self._model = game_model

        super(GameView, self).__init__(screen,
                                       width=int(self._model.world_map.generation_dict['width'] * 2 + 30),
                                       height=screen.height,
                                       on_load=self._reload_map,
                                       hover_focus=False,
                                       title="World Map",
                                       has_border=False)

        self.palette['background'] = (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK)
        self.palette['edit_text'] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK)
        self.palette['label'] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK)

        layout = widgets.Layout([int(self._model.world_map.generation_dict['width'] * 2), 30])

        self._info_bar = InfoBar(self._model)
        self._entity_display = EntityView([], self._model.world_map.selected_tile, self._model)
        self._map_console = ConsoleView(screen.height - self._model.world_map.generation_dict['height'] - 2)
        self._map_view = VoromapView(self._model.world_map, self._map_console, self._entity_display)
        self._map_view.l = layout
        self._text_input = TextInputView(self._model, self._map_view, self._map_console)

        self.add_layout(layout)

        layout.add_widget(self._map_view, 0)
        layout.add_widget(self._map_console, 0)
        layout.add_widget(self._text_input, 0)
        layout.add_widget(self._info_bar, 0)
        layout.add_widget(self._entity_display, 1)

        self.fix()

    def _reload_map(self):
        self._map_view.world = self._model.world_map

    @staticmethod
    def _quit():
        raise asciimatics.exceptions.StopApplication("User pressed quit")


def global_shortcuts(event):
    if isinstance(event, asciimatics.event.KeyboardEvent):
        c = event.key_code
        # Stop on ctrl+q or ctrl+x
        if c in (17, 24):
            raise asciimatics.exceptions.StopApplication("User terminated app")


def demo(screen, scene):
    # t = voromap.WorldMap(80, 40, 0, 3, 9, 100)
    # g = game.Game(t, 6)

    scenes = [
        Scene([GameView(screen, model)], -1, name="Main")
    ]

    screen.play(scenes, stop_on_resize=True, start_scene=scene, unhandled_input=global_shortcuts)

last_scene = None
os.environ['TERM'] = 'xterm-256color'

while True:
    try:
        Screen.wrapper(demo, catch_interrupt=True, arguments=[last_scene])
        exit(0)
    except asciimatics.exceptions.ResizeScreenError as ex:
        last_scene = ex.scene
