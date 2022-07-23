from weapons import *
from game import *

class MenuView(arcade.View):
    def on_show_view(self):
        arcade.set_background_color(arcade.color.GRAY_BLUE)

    def on_draw(self):
        self.clear()
        arcade.draw_text("Welcome to Jinx's Adventure", self.window.width / 2, self.window.height / 2,
                         arcade.color.BLACK, font_size=50, anchor_x="center")
        arcade.draw_text("A crazy physics platformer", self.window.width / 2, self.window.height / 2 - 75,
                         arcade.color.RED_BROWN, font_size=25, anchor_x="center")
        arcade.draw_text("Click to advance", self.window.width / 2, self.window.height / 2 - 150,
                         arcade.color.REDWOOD, font_size=20, anchor_x="center")

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        instructions_view = InstructionView()
        self.window.show_view(instructions_view)

class InstructionView(arcade.View):
        
    def on_show_view(self):
        """ This is run once when we switch to this view """
        arcade.set_background_color(arcade.csscolor.DARK_SLATE_BLUE)

        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        arcade.set_viewport(0, self.window.width, 0, self.window.height)

    def on_draw(self):
        """ Draw this view """
        self.clear()
        arcade.draw_text("Instructions Screen", self.window.width / 2, self.window.height / 2,
                         arcade.color.WHITE, font_size=50, anchor_x="center")
        arcade.draw_text("ASDW or arrows to move, Q/N for bullets", self.window.width / 2, self.window.height / 2-80,
                         arcade.color.PINK_LAVENDER, font_size=25, anchor_x="center")
        arcade.draw_text("E/M to shield, Click for grenades which level up as you do", self.window.width / 2, self.window.height / 2-120,
                         arcade.color.YELLOW_GREEN, font_size=25, anchor_x="center")
        arcade.draw_text("Increasing your level improves bullets, damage and jump", self.window.width / 2, self.window.height / 2-160,
                         arcade.color.DARK_CHESTNUT, font_size=25, anchor_x="center")
        arcade.draw_text("Grenades activate at level one and become increasingly powerful", self.window.width / 2, self.window.height / 2-200,
                         arcade.color.PINK_LAVENDER, font_size=25, anchor_x="center")

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        """ If the user presses the mouse button, start the game. """
        game_view = GameView()
        game_view.setup()
        self.window.show_view(game_view)

