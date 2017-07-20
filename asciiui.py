import asciimatics
import asciimatics.widgets as widgets
from asciimatics.screen import Screen
from asciimatics.scene import Scene
import voromap
import os

# TODO:
# wrapping on bottom and right of map
# fix map cutoff 1 space before edge
# allow user to view and change map generator constants


class ConsoleView(widgets.Widget):
    # a console display for text output
    # may eventually handle text input as well?
    # text_lines holds all current text, 0 is bottom line

    def __init__(self, height):
        super(ConsoleView, self).__init__(name="Console")

        self.height = height
        self.text_lines = []
        # self._is_tab_stop = False
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
        # self.text_lines.pop()
        self.text_lines.insert(0, text)
        self.view_bottom = 0
        self.update(0)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value


class VoromapView(widgets.Widget):
    # generation variables eventually
    # color filter supports Terrain, Continent
    show_heights = False
    show_icons = False

    def __init__(self, world_map: voromap.WorldMap, display: ConsoleView):
        super(VoromapView, self).__init__(name="World")

        # self._is_tab_stop = False
        self.world_map = world_map
        self.display = display

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    def reset(self):
        return None

    def update(self, frame_no):
        for c in self.world_map.continents:
            c.set_tile_icons_to_continent_icon()

        y_index = 0
        for i in self.world_map.world:
            x_index = 0
            for j in i:
                icon1 = ' '
                icon2 = ' '

                if self.show_icons is True:
                    icon1 = j.icon

                if self.show_heights is True:
                    icon2 = j.height

                l = f'{icon1}{icon2}'

                color = j.color

                if j is self.world_map.selected_tile:
                    if self._has_focus is True:
                        color = 201
                    else:
                        color = 219
                    l = f'{j.icon}{j.height}'

                self._frame.canvas.print_at(l, self._x + x_index * 2, self._y + y_index,
                                            colour=Screen.COLOUR_BLACK, bg=color)
                x_index += 1
            y_index += 1

    def handle_arrow_input(self, event):
        key_code = event.key_code
        t = self.world_map.selected_tile
        location_changed = False

        try:
            if key_code is Screen.KEY_LEFT:
                self.world_map.selected_tile = self.world_map.world[t.y][t.x - 1]
                location_changed = True
            elif key_code is Screen.KEY_RIGHT:
                self.world_map.selected_tile = self.world_map.world[t.y][t.x + 1]
                location_changed = True
            elif key_code is Screen.KEY_UP:
                self.world_map.selected_tile = self.world_map.world[t.y - 1][t.x]
                location_changed = True
            elif key_code is Screen.KEY_DOWN:
                self.world_map.selected_tile = self.world_map.world[t.y + 1][t.x]
                location_changed = True
            elif key_code == 393:
                self.world_map.selected_tile = self.world_map.world[t.y][t.x - 10]
                location_changed = True
            elif key_code == 402:
                self.world_map.selected_tile = self.world_map.world[t.y][t.x + 10]
                location_changed = True
            elif key_code == 337:
                self.world_map.selected_tile = self.world_map.world[t.y - 10][t.x]
                location_changed = True
            elif key_code == 336:
                self.world_map.selected_tile = self.world_map.world[t.y + 10][t.x]
                location_changed = True

        except IndexError:
            location_changed = False

        if location_changed:
            self.display.add_line(
                text=f"Selected: ({self.world_map.selected_tile.x}, {self.world_map.selected_tile.y})")
            self.update(0)

    def handle_enter_input(self, event):
        if event.key_code == 10:
            self.display.reset()
            self.display.update(1)
            return None
        return event

    def process_event(self, event):
        if isinstance(event, asciimatics.event.KeyboardEvent):

            global_shortcuts(event)

            t = self.world_map.selected_tile

            if event.key_code in (Screen.KEY_LEFT, Screen.KEY_RIGHT, Screen.KEY_UP, Screen.KEY_DOWN,
                                  393, 402, 337, 336):
                self.handle_arrow_input(event)
                return None
            elif event.key_code == 10:
                self.display.reset()
                self.display.update(0)
                return None
            else:
                return event
                # self.display.add_line(str(event.key_code))
        else:
            return event

        return event

    def required_height(self, offset, width):
        return self.world_map.generation_dict['height']


class TextInputView(widgets.Text):
    commands = ['filter', 'f', 'Filter', 'F',
                'regen', 'rg', 'Regen', 'RG',
                'height', 'h', 'Height', 'H',
                'icon', 'i', 'Icon', 'I',
                'genvars', 'gv', 'GenVars', 'GV',
                'edit', 'e', 'Edit', 'E']
    raw_command = ''

    def __init__(self, model, map_display, console):
        super(TextInputView, self).__init__(name='Input')
        self._label = '>'
        self._model = model
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
                        self._model.terrain_filter()
                        self.console.add_line('Terrain filter on.')
                    elif command_array[0] in ('continent', 'c', "Continent", 'C'):
                        self._model.continent_filter()
                        self.console.add_line('Continent filter on.')
                    else:
                        self.console.add_line('Invalid filter type.')

                elif main_command in ('regen', 'rg', 'Regen', 'RG'):
                    self._model.regenerate()
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

            if event.key_code in (Screen.KEY_UP, Screen.KEY_DOWN):
                return None
            if event.key_code == 10:
                raw_command = self._value
                self.handle_command(raw_command)
                self._value = ''
                self.update(0)
                self.map_display.update(0)
            else:
                super(TextInputView, self).process_event(event)
        else:
            return event

        return event


class TestView(widgets.Frame):
    def __init__(self, screen, model):
        super(TestView, self).__init__(screen,
                                       width=int(screen.width * .75),
                                       height=screen.height,
                                       on_load=self._reload_map,
                                       hover_focus=True,
                                       title="World Map",
                                       has_border=False
                                       )

        self.palette['background'] = (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK)
        self.palette['edit_text'] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK)
        self.palette['label'] = (Screen.COLOUR_WHITE, Screen.A_BOLD, Screen.COLOUR_BLACK)

        self._model = model
        # self._map_label = widgets.Label(label=f"Selected: ({model.selected_tile.x}, {model.selected_tile.y})")
        self._map_console = ConsoleView(screen.height - self._model.generation_dict['height'] - 1)
        self._map_view = VoromapView(model, self._map_console)
        self._text_input = TextInputView(model, self._map_view, self._map_console)

        layout = widgets.Layout([1], fill_frame=True)
        # layout2 = widgets.Layout([1])

        self.add_layout(layout)
        # self.add_layout(layout2)

        layout.add_widget(self._map_view)
        layout.add_widget(self._map_console)
        layout.add_widget(self._text_input)
        # layout2.add_widget(widgets.Button("Quit", self._quit), 0)

        # self._map_view.focus()
        self.fix()

    def _reload_map(self):
        self._map_view.world = self._model

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
    t = voromap.WorldMap(80, 40, 0, 3, 9, 100)

    scenes = [
        Scene([TestView(screen, t)], -1, name="Main")
    ]

    screen.play(scenes, stop_on_resize=True, start_scene=scene, unhandled_input=global_shortcuts)

last_scene = None
os.environ['TERM'] = 'xterm-256color'

while True:
    try:
        Screen.wrapper(demo, catch_interrupt=True, arguments=[last_scene])
        exit(0)
    except asciimatics.exceptions.ResizeScreenError as e:
        last_scene = e.scene
