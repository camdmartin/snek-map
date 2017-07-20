import asciimatics
import asciimatics.widgets as widgets
from asciimatics.screen import Screen
from asciimatics.scene import Scene
import voromap
import os
import copy


class ConsoleView(widgets.Widget):
    # a console display for text output
    # may eventually handle text input as well?
    # text_lines holds all current text, 0 is bottom line

    def __init__(self, height):
        super(ConsoleView, self).__init__(name="Console")

        self.height = height
        self.text_lines = []
        for h in range(0, height):
            self.text_lines.append('')

    def reset(self):
        self.text_lines = []
        for h in range(0, self.height):
            self.text_lines.append('')

    def process_event(self, event):
        if isinstance(event, asciimatics.event.KeyboardEvent):
            global_shortcuts()
        return

    def required_height(self, offset, width):
        return self.height

    def update(self, frame_no):
        line_index = self.height - 1
        for l in self.text_lines:
            self._frame.canvas.print_at("> " + l, self._x, self._y + line_index, colour=Screen.COLOUR_WHITE,
                                        bg=Screen.COLOUR_BLACK)
            line_index -= 1

    def add_line(self, text: str):
        self.text_lines.pop()
        self.text_lines.insert(0, text)
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

    def __init__(self, world_map: voromap.WorldMap, display: ConsoleView):
        super(VoromapView, self).__init__(name="World")

        # self._is_tab_stop = False
        self.world_map = world_map
        self.display = display
        self.apply_color_filter(self.world_map.color_filter)

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
                l = "  "
                color = j.color

                if j is self.world_map.selected_tile:
                    color = 201
                    l = f'{j.icon}{j.height}'

                self._frame.canvas.print_at(l, self._x + x_index * 2, self._y + y_index,
                                            colour=Screen.COLOUR_BLACK, bg=color)
                x_index += 1
            y_index += 1

    def apply_color_filter(self, filter: str):
        for i in self.world_map.world:
            for j in i:
                if filter is 'Terrain':
                    color = self.get_terrain_color(j)
                elif filter is 'Continent':
                    c = self.world_map.get_continent_of_tile(j)
                    if c is not None:
                        color = c.color
                    else:
                        color = 17

                j.color = color

    def get_terrain_color(self, tile):
        forest_colors = [23, 29, 22, 28, 34, 40, 46, 83, 85]
        ocean_colors = [17, 18, 19, 20, 21, 33, 45, 201, 201, 201]
        mountain_colors = [201, 201, 201, 233, 235, 237, 241, 248, 252, 255]
        desert_colors = [3, 186, 190, 226, 227, 228, 229, 230, 252, 255]
        # orange desert colors [130, 136, 172, 178, 220, 226, 228, 230, 252, 255]

        color_table = [201, 201, 201, 201, 201, 201, 201, 201, 201]

        if tile.type is not 'Land':
            color_table = ocean_colors
        elif tile.terrain is 'Desert':
            color_table = desert_colors
        elif tile.height < 6:
            color_table = forest_colors
        elif tile.height >= 6:
            color_table = mountain_colors

        return color_table[tile.height]

    def handle_arrow_input(self, key_code):
        t = self.world_map.selected_tile

        try:
            if key_code is Screen.KEY_LEFT:
                self.world_map.selected_tile = self.world_map.world[t.y][t.x - 1]
            elif key_code is Screen.KEY_RIGHT:
                self.world_map.selected_tile = self.world_map.world[t.y][t.x + 1]
            elif key_code is Screen.KEY_UP:
                self.world_map.selected_tile = self.world_map.world[t.y - 1][t.x]
            elif key_code is Screen.KEY_DOWN:
                self.world_map.selected_tile = self.world_map.world[t.y + 1][t.x]
            elif key_code == 393:
                self.world_map.selected_tile = self.world_map.world[t.y][t.x - 10]
            elif key_code == 402:
                self.world_map.selected_tile = self.world_map.world[t.y][t.x + 10]
            elif key_code == 337:
                self.world_map.selected_tile = self.world_map.world[t.y - 10][t.x]
            elif key_code == 336:
                self.world_map.selected_tile = self.world_map.world[t.y + 10][t.x]
        except IndexError:
            ()

        self.display.add_line(text=f"Selected: ({self.world_map.selected_tile.x}, {self.world_map.selected_tile.y})")
        self.update(0)

    def handle_enter_input(self, key_code):
        if key_code == 10:
            self.display.reset()
            self.display.update(1)

    def process_event(self, event):
        if isinstance(event, asciimatics.event.KeyboardEvent):
            global_shortcuts(event)
            self.handle_arrow_input(event.key_code)
            self.handle_enter_input(event.key_code)
            # print(event.key_code)
        return

    def required_height(self, offset, width):
        return self.world_map.height


class TextInputView(widgets.Text):
    def __init__(self, model):
        super(TextInputView, self).__init__(name='Input')
        self._label = '>'
        self._model = model
        self.custom_colour = 'edit_text'


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
        self.palette['label'] = (Screen.COLOUR_CYAN, Screen.A_BOLD, Screen.COLOUR_BLACK)

        self._model = model
        # self._map_label = widgets.Label(label=f"Selected: ({model.selected_tile.x}, {model.selected_tile.y})")
        self._map_console = ConsoleView(screen.height - self._model.height - 1)
        self._map_view = VoromapView(model, self._map_console)
        self._text_input = TextInputView(model)

        layout = widgets.Layout([1], fill_frame=True)
        # layout2 = widgets.Layout([1])

        self.add_layout(layout)
        # self.add_layout(layout2)

        layout.add_widget(self._map_view)
        layout.add_widget(self._map_console)
        layout.add_widget(self._text_input)
        # layout2.add_widget(widgets.Button("Quit", self._quit), 0)

        self._map_view.focus()
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
