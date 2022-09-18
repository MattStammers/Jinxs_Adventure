"""
Jinx and Gravity Game

This is the main game script
"""
import os
import math
import arcade
import random
# from signal import pause
from sys import builtin_module_names
from tokenize import Name
from typing import Optional
from unicodedata import name

from arcade import Point

file_path = os.path.dirname(os.path.abspath(__file__))

SCREEN_TITLE = "Jinx & Gravity"
DEFAULT_LINE_HEIGHT = 45
DEFAULT_FONT_SIZE = 20

# Key Game Layer Variables - central source of control
LAYER_NAME_PLATFORMS = "Platforms"
LAYER_NAME_PLAYER = "Player"
LAYER_NAME_BACKGROUND = "Background"
LAYER_NAME_FOREGROUND = "Foreground"
LAYER_NAME_COINS = "Coins"
LAYER_NAME_HEARTS = "Hearts"
LAYER_NAME_DONT_TOUCH = "Don't Touch"
LAYER_NAME_LADDERS = "Ladders"
LAYER_NAME_MOVING_PLATFORMS = "Moving Platforms"
LAYER_NAME_ENEMIES = "Enemies"
LAYER_NAME_DYNAMIC_ITEMS = "Dynamic Items"
LAYER_NAME_DYNAMIC_TILES = "Dynamic Tiles"
LAYER_NAME_PLAYER_BULLETS = "Player Bullets"
LAYER_NAME_PLAYER_GRENADES = "Player Grenades"
LAYER_NAME_ENEMY_BULLETS = "Enemy Bullets"
LAYER_NAME_ALLIES = "Allies"
LAYER_NAME_SHIELD = "Shield"
LAYER_NAME_POWER_UPS = "Power Ups"

# This script contains all the player features (and most of the physics variables)

# How big are our image tiles?
SPRITE_IMAGE_SIZE = 128

# Scale sprites up or down
SPRITE_SCALING_PLAYER = 0.4
SPRITE_SCALING_TILES = 0.4

# Scaled sprite size for tiles
SPRITE_SIZE = int(SPRITE_IMAGE_SIZE * SPRITE_SCALING_PLAYER)

# Size of grid to show on screen, in number of tiles
SCREEN_GRID_WIDTH = 25
SCREEN_GRID_HEIGHT = 13

# Size of screen to show, in pixels
SCREEN_WIDTH = SPRITE_SIZE * SCREEN_GRID_WIDTH
SCREEN_HEIGHT = SPRITE_SIZE * SCREEN_GRID_HEIGHT

# Calculate Grid Pixel Size
GRID_PIXEL_SIZE = SPRITE_IMAGE_SIZE * SPRITE_SCALING_TILES

# Player Start Location
start_grid_x = 1
start_grid_y = 1

# --- Physics forces. Higher number, faster accelerating.

# Gravity
GRAVITY = 1500

# Damping - Amount of speed lost per second
DEFAULT_DAMPING = 1.0
PLAYER_DAMPING = 0.4

# Friction between objects
PLAYER_FRICTION = 1.0
WALL_FRICTION = 0.7
DYNAMIC_ITEM_FRICTION = 0.6

# Mass (defaults to 1)
PLAYER_MASS = 2.0

# Keep player from going too fast
PLAYER_MAX_HORIZONTAL_SPEED = 450
PLAYER_MAX_VERTICAL_SPEED = 1600

# Force applied while on the ground
PLAYER_MOVE_FORCE_ON_GROUND = 8000

# Force applied when moving left/right in the air
PLAYER_MOVE_FORCE_IN_AIR = 900

# Strength of a jump
PLAYER_JUMP_IMPULSE = 1200

# Close enough to not-moving to have the animation go to idle.
DEAD_ZONE = 1

# Death Cooldown
DEATH_PROTECT = 15

# Constants used to track if the player is facing left or right
RIGHT_FACING = 0
LEFT_FACING = 1

# How many pixels to move before we change the texture in the walking animation
DISTANCE_TO_CHANGE_TEXTURE = 20

# Main Player Class
class PlayerSprite(arcade.Sprite):
    """ Player Sprite """
    def __init__(self,
                 ladder_list: arcade.SpriteList,
                 hit_box_algorithm):
        """ Init """
        # Let parent initialize
        super().__init__()

        # Set our scale
        self.scale = SPRITE_SCALING_PLAYER

        # Images from Character pack
        main_path = file_path + "\\src\\resources\\images\\animated_characters\\jinx\\jinx"

        # Load textures for idle standing
        self.idle_texture_pair = arcade.load_texture_pair(f"{main_path}_idle.png",
                                                          hit_box_algorithm=hit_box_algorithm)
        self.jump_texture_pair = arcade.load_texture_pair(f"{main_path}_jump.png")
        self.fall_texture_pair = arcade.load_texture_pair(f"{main_path}_fall.png")

        # Load textures for walking
        self.walk_textures = []
        for i in range(8):
            texture = arcade.load_texture_pair(f"{main_path}_walk{i}.png")
            self.walk_textures.append(texture)

        # Load textures for climbing
        self.climbing_textures = []
        texture = arcade.load_texture(f"{main_path}_climb0.png")
        self.climbing_textures.append(texture)
        texture = arcade.load_texture(f"{main_path}_climb1.png")
        self.climbing_textures.append(texture)

        # Set the initial texture
        self.texture = self.idle_texture_pair[0]

        # Hit box will be set based on the first image used.
        self.hit_box = self.texture.hit_box_points

        # Default to face-right
        self.character_face_direction = RIGHT_FACING

        # Index of our current texture
        self.cur_texture = 0

        # How far have we traveled horizontally since changing the texture
        self.x_odometer = 0
        self.y_odometer = 0

        self.ladder_list = ladder_list
        self.is_on_ladder = False

    def pymunk_moved(self, physics_engine, dx, dy, d_angle):
        """ Handle being moved by the pymunk engine """
        # Figure out if we need to face left or right
        if dx < -DEAD_ZONE and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif dx > DEAD_ZONE and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        # Are we on the ground?
        is_on_ground = physics_engine.is_on_ground(self)

        # Are we on a ladder?
        if len(arcade.check_for_collision_with_list(self, self.ladder_list)) > 0:
            if not self.is_on_ladder:
                self.is_on_ladder = True
                self.pymunk.gravity = (0, 0)
                self.pymunk.damping = 0.0001
                self.pymunk.max_vertical_velocity = PLAYER_MAX_HORIZONTAL_SPEED
        else:
            if self.is_on_ladder:
                self.pymunk.damping = 1.0
                self.pymunk.max_vertical_velocity = PLAYER_MAX_VERTICAL_SPEED
                self.is_on_ladder = False
                self.pymunk.gravity = None

        # Add to the odometer how far we've moved
        self.x_odometer += dx
        self.y_odometer += dy

        if self.is_on_ladder and not is_on_ground:
            # Have we moved far enough to change the texture?
            if abs(self.y_odometer) > DISTANCE_TO_CHANGE_TEXTURE:

                # Reset the odometer
                self.y_odometer = 0

                # Advance the walking animation
                self.cur_texture += 1

            if self.cur_texture > 1:
                self.cur_texture = 0
            self.texture = self.climbing_textures[self.cur_texture]
            return

        # Jumping animation
        if not is_on_ground:
            if dy > DEAD_ZONE:
                self.texture = self.jump_texture_pair[self.character_face_direction]
                return
            elif dy < -DEAD_ZONE:
                self.texture = self.fall_texture_pair[self.character_face_direction]
                return

        # Idle animation
        if abs(dx) <= DEAD_ZONE:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return

        # Have we moved far enough to change the texture?
        if abs(self.x_odometer) > DISTANCE_TO_CHANGE_TEXTURE:

            # Reset the odometer
            self.x_odometer = 0

            # Advance the walking animation
            self.cur_texture += 1
            if self.cur_texture > 7:
                self.cur_texture = 0
            self.texture = self.walk_textures[self.cur_texture][self.character_face_direction]

SPRITE_SCALING_ENEMIES = 0.8
ENEMY_SPRITE_IMAGE_SIZE = 64
ALLY_SPRITE_IMAGE_SIZE = 64
SPRITE_SCALING_ALLIES = 0.8

def load_texture_pair(filename):
    """
    Load a texture pair, with the second being a mirror image.
    """
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True),
    ]

# Base enemy class
class Entity(arcade.Sprite):
    def __init__(self, name_folder, name_file):
        super().__init__()

        # Default to facing right
        self.facing_direction = RIGHT_FACING

        # Used for image sequences
        self.cur_texture = 0
        self.scale = SPRITE_SCALING_ENEMIES

        main_path = file_path + f"/src/resources/images/animated_characters/{name_folder}/{name_file}"

        self.idle_texture_pair = load_texture_pair(f"{main_path}_idle.png")
        self.jump_texture_pair = load_texture_pair(f"{main_path}_jump.png")
        self.fall_texture_pair = load_texture_pair(f"{main_path}_fall.png")

        # Load textures for walking
        self.walk_textures = []
        for i in range(8):
            texture = load_texture_pair(f"{main_path}_walk{i}.png")
            self.walk_textures.append(texture)

        # Load textures for climbing
        self.climbing_textures = []
        texture = arcade.load_texture(f"{main_path}_climb0.png")
        self.climbing_textures.append(texture)
        texture = arcade.load_texture(f"{main_path}_climb1.png")
        self.climbing_textures.append(texture)

        # Set the initial texture
        self.texture = self.idle_texture_pair[0]

        # Hit box will be set based on the first image used. If you want to specify
        # a different hit box, you can do it like the code below.
        # self.set_hit_box([[-22, -64], [22, -64], [22, 28], [-22, 28]])
        self.set_hit_box(self.texture.hit_box_points) 

class Enemy(Entity):
    def __init__(self, name_folder, name_file):

        # Setup parent class
        super().__init__(name_folder, name_file)

        self.should_update_walk = 0
        self.scale = SPRITE_SCALING_ENEMIES

    def update_animation(self, delta_time: float = 1 / 60):

        # Figure out if we need to flip face left or right
        if self.change_x < 0 and self.facing_direction == RIGHT_FACING:
            self.facing_direction = LEFT_FACING
        elif self.change_x > 0 and self.facing_direction == LEFT_FACING:
            self.facing_direction = RIGHT_FACING

        # Idle animation
        if self.change_x == 0:
            self.texture = self.idle_texture_pair[self.facing_direction]
            return

        # Walking animation
        if self.should_update_walk == 3:
            self.cur_texture += 1
            if self.cur_texture > 7:
                self.cur_texture = 0
            self.texture = self.walk_textures[self.cur_texture][self.facing_direction]
            self.should_update_walk = 0
            return

        self.should_update_walk += 1

class GreenWorm(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("wormGreen", "wormGreen")

        self.health = 10

class BlueSlime(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("slimeBlue", "slimeBlue")

        self.health = 20

class LavaSnake(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("snakeLava", "snakeLava")

        self.health = 50

class GreenSlime(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("slimeGreen", "slimeGreen")

        self.health = 50

class PurpleSlime(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("slimePurple", "slimePurple")

        self.health = 100

class Thunderer(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("thunderer", "thunderer")

        self.health = 150

class BlueSlimeBoss(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("slimeBlueBoss", "slimeBlueBoss")

        self.health = 2500

class Chomper(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("chomper", "chomper")

        self.health = 350

class SilverSlime(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("slimeSilver", "slimeSilver")

        self.health = 1000

class DiamondShooter(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("diamondshooter", "diamondshooter")

        self.health = 500

class PrimarySlime(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("primaryslime", "primaryslime")

        self.health = 1500

class SecondarySlime(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("secondaryslime", "secondaryslime")

        self.health = 3000

class SuperThunderer(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("superthunderer", "superthunderer")

        self.health = 10000

class RobotEnemy(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("robot", "robot")

        self.health = 5000

class RolyPolyBot(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("rolypolybot", "rolypolybot")

        self.health = 10000

class MasterVerse(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("masterverse", "masterverse")

        self.health = 50000

class FlufflePop(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("flufflepop", "flufflepop")

        self.health = 100000

# Now for ally characters
class Ally(Entity):
    def __init__(self, name_folder, name_file):

        # Setup parent class
        super().__init__(name_folder, name_file)

        self.should_update_walk = 0
        self.scale = SPRITE_SCALING_ALLIES

    def update_animation(self, delta_time: float = 1 / 60):

        # Figure out if we need to flip face left or right
        if self.change_x < 0 and self.facing_direction == RIGHT_FACING:
            self.facing_direction = LEFT_FACING
        elif self.change_x > 0 and self.facing_direction == LEFT_FACING:
            self.facing_direction = RIGHT_FACING

        # Idle animation
        if self.change_x == 0:
            self.texture = self.idle_texture_pair[self.facing_direction]
            return

        # Walking animation
        if self.should_update_walk == 3:
            self.cur_texture += 1
            if self.cur_texture > 7:
                self.cur_texture = 0
            self.texture = self.walk_textures[self.cur_texture][self.facing_direction]
            self.should_update_walk = 0
            return

        self.should_update_walk += 1

class Hooboo(Ally):
    def __init__(self):

        # Set up parent class
        super().__init__("hooboo", "hooboo")

        self.health = 500

class FlufflePop(Ally):
    def __init__(self):

        # Set up parent class
        super().__init__("flufflepop", "flufflepop")

        self.health = 100000

class Pumbean(Ally):
    def __init__(self):

        # Set up parent class
        super().__init__("pumbean", "pumbean")

        self.health = 1500

class Excalibur(Ally):
    def __init__(self):

        # Set up parent class
        super().__init__("excalibur", "excalibur")

        self.health = 2500

class MasterVerse(Ally):
    def __init__(self):

        # Set up parent class
        super().__init__("masterverse", "masterverse")

        self.health = 50000

class RolyPolyBot(Ally):
    def __init__(self):

        # Set up parent class
        super().__init__("rolypolybot", "rolypolybot")

        self.health = 10000

class SecondarySlime(Ally):
    def __init__(self):

        # Set up parent class
        super().__init__("secondaryslime", "secondaryslime")

        self.health = 3000

# This is the main weapons script

# Adding coin scaling
COIN_SCALING = 0.5

# Shooting Constants
SPRITE_SCALING_PROJECTILES = 0.6
SHOOT_SPEED = 100
BULLET_SPEED = 2
SHIELD_SPEED = 1000
PLAYER_BULLET_DAMAGE = 10

# How much force to put on the bullet
BULLET_MOVE_FORCE = 1000

# Mass of the bullet
BULLET_MASS = 0.1

# Make bullet less affected by gravity
BULLET_GRAVITY = 300

class GrenadeSprite(arcade.SpriteSolidColor):
    """ Bullet Sprite """
    def pymunk_moved(self, physics_engine, dx, dy, d_angle):
        """ Handle when the sprite is moved by the physics engine. """
        # If the bullet falls below the screen, remove it
        if self.center_y < -100:
            self.remove_from_sprite_lists()

class MenuView(arcade.View):
    def on_show_view(self):
        arcade.set_background_color(arcade.color.GRAY_BLUE)

    def on_draw(self):
        self.clear()
        arcade.draw_text("Welcome to Jinx's Adventure", self.window.width / 2, self.window.height / 2,
                         arcade.color.BLACK, font_size=50, anchor_x="center")
        arcade.draw_text("A crazy physics platformer", self.window.width / 2, self.window.height / 2 - 75,
                         arcade.color.RED_BROWN, font_size=25, anchor_x="center")
        arcade.draw_text("Click to see the instructions", self.window.width / 2, self.window.height / 2 - 150,
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
        arcade.draw_text("Game Instructions", self.window.width / 2, self.window.height / 2,
                         arcade.color.WHITE, font_size=50, anchor_x="center")
        arcade.draw_text("ASDW or arrows to move, Q/N for bullets", self.window.width / 2, self.window.height / 2-80,
                         arcade.color.PINK_LAVENDER, font_size=25, anchor_x="center")
        arcade.draw_text("E/M to shield, Mouse for grenades. Points increase your level", self.window.width / 2, self.window.height / 2-120,
                         arcade.color.YELLOW_GREEN, font_size=25, anchor_x="center")
        arcade.draw_text("Increasing your level improves bullets, damage and jump", self.window.width / 2, self.window.height / 2-160,
                         arcade.color.DARK_CHESTNUT, font_size=25, anchor_x="center")
        arcade.draw_text("Grenades activate at level one. Keep an eye out for power ups", self.window.width / 2, self.window.height / 2-200,
                         arcade.color.PINK_LAVENDER, font_size=25, anchor_x="center")

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        """ If the user presses the mouse button, start the game. """
        game_view = GameView()
        game_view.setup()
        self.window.show_view(game_view)

class GameOverView(arcade.View):
    """ View to show when game is over """

    def __init__(self):
        """ This is run once when we switch to this view """
        super().__init__()
        self.texture = arcade.load_texture(file_path + "/src/resources/images/tiles/custom_tiles/pizzaman2.png")

        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        arcade.set_viewport(0, SCREEN_WIDTH - 1, 0, SCREEN_HEIGHT - 1)

    def on_draw(self):
        """ Draw this view """
        self.clear()
        self.texture.draw_sized(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2,
                                SCREEN_WIDTH, SCREEN_HEIGHT)

    def on_mouse_press(self, _x, _y, _button, _modifiers):
        """ If the user presses the mouse button, re-start the game. """
        game_view = GameView()
        game_view.setup()
        self.window.show_view(game_view)

class GameView(arcade.View):
    """ Main Window """

    def __init__(self):
        """ Create the variables """

        # Init the parent class
        super().__init__()

        # Don't show the mouse cursor
        self.window.set_mouse_visible(True)

        # Add width and height
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT

        # Initialise Frame Count
        self.frame_count = 0

        # Add the screen title
        # If wanted later on can be added here

        # Sprite lists we need
        self.wall_list: Optional[arcade.SpriteList] = None
        self.grenade_list: Optional[arcade.SpriteList] = None
        self.item_list: Optional[arcade.SpriteList] = None
        self.block_list: Optional[arcade.SpriteList] = None
        self.moving_sprites_list: Optional[arcade.SpriteList] = None
        self.ladder_list: Optional[arcade.SpriteList] = None
        self.coin_list: Optional[arcade.SpriteList] = None
        self.heart_list: Optional[arcade.SpriteList] = None
        self.enemies_list: Optional[Enemy] = None
        self.allies_list: Optional[Enemy] = None
        self.player_bullets: Optional[arcade.SpriteList] = None
        self.player_list: Optional[arcade.SpriteList] = None

        # Player sprite
        self.player_sprite: Optional[PlayerSprite] = None

        # Track the current state of what key is pressed
        self.left_pressed: bool = False
        self.right_pressed: bool = False
        self.up_pressed: bool = False
        self.down_pressed: bool = False
        self.shoot_pressed: bool = False
        self.shield_pressed: bool = False
        self.mouse_pressed: bool = False

        # Physics engine
        self.physics_engine: Optional[arcade.PymunkPhysicsEngine] = None

        # Add camera
        self.camera = None

        # A Camera that can be used to draw GUI elements
        self.gui_camera = None

        # Our TileMap Object
        self.tile_map = None

        # Our Scene Object
        self.scene = None

        # Shooting mechanics
        self.can_shoot = False
        self.shoot_timer = 0

        # Shielding mechanics
        self.can_shield = False
        self.shield_timer = 0

        # Life mechanics
        self.can_die = False
        self.death_timer = 0
        self.invincibility_timer = 0

        # Super bullet mode
        self.grenade_booster = 0

        # Keep track of the score
        self.score = 0

        # Do we need to reset the score?
        self.reset_score = True

        # Set background color
        arcade.set_background_color(arcade.color.BLEU_DE_FRANCE)

        # Where is the right edge of the map?
        self.end_of_map = 0

        # Selfs
        self.x = 0
        self.y = 0

        # Level
        self.level = 0

        # Level_Up
        self.level_up = 0

        # Lives
        self.lives = 3

        # Load sounds
        self.game_over = arcade.load_sound(file_path+"/src/resources/sounds/gameover2.wav")
        self.collect_coin_sound = arcade.load_sound(file_path+"/src/resources/sounds/coin1.wav")
        self.jump_sound = arcade.load_sound(file_path+"/src/resources/sounds/jump3.wav")
        self.hit_sound = arcade.load_sound(file_path+"/src/resources/sounds/hit2.wav")
        self.shoot_sound = arcade.load_sound(file_path+"/src/resources/sounds/hurt3.wav")

        # Add messages
        self.message1 = None
        self.message2 = None
        self.message3 = None
        self.message4 = None
        self.message5 = None

    def setup(self):
        """ Set up everything with the game """

        # Layer Specific Options for the Tilemap
        layer_options = {
            LAYER_NAME_PLATFORMS: {
                "use_spatial_hash": True,
            },
            LAYER_NAME_ENEMIES: {
                "use_spatial_hash": False,
            },
            LAYER_NAME_ALLIES: {
                "use_spatial_hash": False,
            },
            LAYER_NAME_MOVING_PLATFORMS: {
                "use_spatial_hash": False,
            },
            LAYER_NAME_SHIELD: {
                "use_spatial_hash": True,
            },
            LAYER_NAME_LADDERS: {
                "use_spatial_hash": True,
            },
            LAYER_NAME_COINS: {
                "use_spatial_hash": True,
            },
            LAYER_NAME_DONT_TOUCH: {
                "use_spatial_hash": True,
            },
        }

        # Set up the GUI Camera
        self.gui_camera = arcade.Camera(self.width, self.height)

        # Keep track of the score
        self.score = self.score

        # Level_Up
        self.level_up = 0

        # Lives at the start of each level
        self.lives = self.lives

        # Life mechanics
        self.can_die = True
        self.death_timer = 0
        self.invincibility_timer = 0

        # Super bullet mode
        self.grenade_booster = 0

        # Shielding mechanics
        self.can_shield = True
        self.shield_timer = 0

        # Shooting mechanics
        self.can_shoot = True
        self.shoot_timer = 0

        # Shooting mechanics
        self.mouse_pressed = False

        # Keep track of the score, make sure we keep the score if the player finishes a level
        if self.reset_score:
            self.score = 0
        self.reset_score = False

        # Set up the Camera
        self.camera = arcade.Camera(self.width, self.height)

        # Create the sprite lists
        self.player_list = arcade.SpriteList()
        self.grenade_list = arcade.SpriteList()

        # Map name
        map_name = file_path + f"/src/resources/images/tiled_maps/level_{self.level}.json"

        # Load in TileMap
        self.tile_map = arcade.load_tilemap(map_name, SPRITE_SCALING_TILES, layer_options)
        
        # Initiate New Scene with our TileMap, this will automatically add all layers
        # from the map as SpriteLists in the scene in the proper order.
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # Pull the sprite layers out of the tile map
        self.background_list = self.tile_map.sprite_lists[LAYER_NAME_BACKGROUND]
        self.wall_list = self.tile_map.sprite_lists[LAYER_NAME_PLATFORMS]
        self.coin_list = self.tile_map.sprite_lists[LAYER_NAME_COINS]
        self.heart_list = self.tile_map.sprite_lists[LAYER_NAME_HEARTS]
        self.dont_touch_list = self.tile_map.sprite_lists[LAYER_NAME_DONT_TOUCH]
        self.item_list = self.tile_map.sprite_lists[LAYER_NAME_DYNAMIC_ITEMS]
        self.block_list = self.tile_map.sprite_lists[LAYER_NAME_DYNAMIC_TILES]
        self.ladder_list = self.tile_map.sprite_lists[LAYER_NAME_LADDERS]
        self.moving_sprites_list = self.tile_map.sprite_lists[LAYER_NAME_MOVING_PLATFORMS]
        self.power_ups_list = self.tile_map.sprite_lists[LAYER_NAME_POWER_UPS]

        # Create player sprite
        self.player_sprite = PlayerSprite(self.ladder_list, hit_box_algorithm="Detailed")

        # Set player start location
        self.player_sprite.center_x = SPRITE_SIZE * start_grid_x + SPRITE_SIZE / 2
        self.player_sprite.center_y = SPRITE_SIZE * start_grid_y + SPRITE_SIZE / 2
        
        # Add to player sprite list
        self.player_list.append(self.player_sprite)

        # Make sure that forground is added afterwards
        self.foreground_list = self.tile_map.sprite_lists[LAYER_NAME_FOREGROUND]

        # Calculate the right edge of the my_map in pixels
        self.end_of_map = self.tile_map.width * GRID_PIXEL_SIZE

        # -- Enemies
        self.enemies_list = self.tile_map.object_lists[LAYER_NAME_ENEMIES]
        self.allies_list = self.tile_map.object_lists[LAYER_NAME_ALLIES]

        # Speech
        speech_list = []

        # Map Allies
        for my_object in self.allies_list:
            cartesian = self.tile_map.get_cartesian(
                my_object.shape[0], my_object.shape[1]
            )
            ally_type = my_object.properties["type"]
            if ally_type == "hooboo":
                ally = Hooboo()
            elif ally_type == "flufflepop":
                ally = FlufflePop()
            elif ally_type == "pumbean":
                ally = Pumbean()
            elif ally_type == "excalibur":
                ally = Excalibur()
            elif ally_type == "masterverse":
                ally = MasterVerse()
            elif ally_type == "rolypolybot":
                ally = RolyPolyBot()
            elif ally_type == "secondaryslime":
                ally = SecondarySlime()
            else:
                raise Exception(f"Unknown ally type {ally_type}.")
            ally.center_x = math.floor(
                cartesian[0] * SPRITE_SCALING_ALLIES * ALLY_SPRITE_IMAGE_SIZE
            )
            ally.center_y = math.floor(
                (cartesian[1] + 1) * (SPRITE_SCALING_ALLIES * ALLY_SPRITE_IMAGE_SIZE)
            )
            if "boundary_left" in my_object.properties:
                ally.boundary_left = my_object.properties["boundary_left"]
            if "boundary_right" in my_object.properties:
                ally.boundary_right = my_object.properties["boundary_right"]
            if "change_x" in my_object.properties:
                ally.change_x = my_object.properties["change_x"]
            if "speech" in my_object.properties:
                self.speech = arcade.Text(
                text = my_object.properties["speech"],
                start_x=ally.center_x,
                start_y=ally.top,
                color = arcade.color.BLACK,
                font_size = DEFAULT_FONT_SIZE)
                speech_list.append(self.speech)
            self.scene.add_sprite(LAYER_NAME_ALLIES, ally)
        
        # Assign speech objects
        self.message1 = speech_list[0]
        self.message2 = speech_list[1]
        self.message3 = speech_list[2]
        self.message4 = speech_list[3]
        self.message5 = speech_list[4]

        # Map Enemy Objects
        for my_object in self.enemies_list:
            cartesian = self.tile_map.get_cartesian(
                my_object.shape[0], my_object.shape[1]
            )
            enemy_type = my_object.properties["type"]
            if enemy_type == "wormGreen":
                enemy = GreenWorm()
            elif enemy_type == "slimeBlue":
                enemy = BlueSlime()
            elif enemy_type == "snakeLava":
                enemy = LavaSnake()  
            elif enemy_type == "slimeGreen":
                enemy = GreenSlime() 
            elif enemy_type == "slimePurple":
                enemy = PurpleSlime() 
            elif enemy_type == "slimeSilver":
                enemy = SilverSlime()   
            elif enemy_type == "slimeBlueBoss":
                enemy = BlueSlimeBoss()  
            elif enemy_type == "primaryslime":
                enemy = PrimarySlime() 
            elif enemy_type == "secondaryslime":
                enemy = SecondarySlime()     
            elif enemy_type == "thunderer":
                enemy = Thunderer()
            elif enemy_type == "superthunderer":
                enemy = SuperThunderer()
            elif enemy_type == "chomper":
                enemy = Chomper()
            elif enemy_type == "diamondshooter":
                enemy = DiamondShooter()
            elif enemy_type == "robot":
                enemy = RobotEnemy()
            elif enemy_type == "rolypolybot":
                enemy = RolyPolyBot()
            elif enemy_type == "masterverse":
                enemy = MasterVerse()
            elif enemy_type == "flufflepop":
                enemy = FlufflePop()
            else:
                raise Exception(f"Unknown enemy type {enemy_type}.")
            enemy.center_x = math.floor(
                cartesian[0] * SPRITE_SCALING_ENEMIES * ENEMY_SPRITE_IMAGE_SIZE
            )
            enemy.center_y = math.floor(
                (cartesian[1] + 1) * (SPRITE_SCALING_ENEMIES * ENEMY_SPRITE_IMAGE_SIZE)
            )
            if "boundary_left" in my_object.properties:
                enemy.boundary_left = my_object.properties["boundary_left"]
            if "boundary_right" in my_object.properties:
                enemy.boundary_right = my_object.properties["boundary_right"]
            if "change_x" in my_object.properties:
                enemy.change_x = my_object.properties["change_x"]
            self.scene.add_sprite(LAYER_NAME_ENEMIES, enemy)

        # Add bullet spritelist to Scene
        self.scene.add_sprite_list(LAYER_NAME_PLAYER_BULLETS)

        # Add enemy bullets and shields
        self.scene.add_sprite_list(LAYER_NAME_ENEMY_BULLETS)
        self.scene.add_sprite_list(LAYER_NAME_SHIELD)

        # Add grenade spritelist to Scene
        self.scene.add_sprite_list(LAYER_NAME_PLAYER_GRENADES)

        # --- Pymunk Physics Engine Setup ---

        # The default damping for every object controls the percent of velocity
        # the object will keep each second. A value of 1.0 is no speed loss,
        # 0.9 is 10% per second, 0.1 is 90% per second.
        # For top-down games, this is basically the friction for moving objects.
        # For platformers with gravity, this should probably be set to 1.0.
        # Default value is 1.0 if not specified.
        damping = DEFAULT_DAMPING

        # Set the gravity. (0, 0) is good for outer space and top-down.
        gravity = (0, -GRAVITY)

        # Create the physics engine
        self.physics_engine = arcade.PymunkPhysicsEngine(damping=damping,
                                                         gravity=gravity)

        def wall_hit_handler(grenade_sprite, _wall_sprite, _arbiter, _space, _data):
            """ Called for grenade/wall collision """
            grenade_sprite.remove_from_sprite_lists()

        self.physics_engine.add_collision_handler("grenade", "wall", post_handler=wall_hit_handler)

        def block_hit_handler(grenade_sprite, block_sprite, _arbiter, _space, _data):
            """ Called for bullet/wall collision """
            grenade_sprite.remove_from_sprite_lists()
            block_sprite.remove_from_sprite_lists()

        self.physics_engine.add_collision_handler("grenade", "block", post_handler=block_hit_handler)

        # Add the player.
        # For the player, we set the damping to a lower value, which increases
        # the damping rate. This prevents the character from traveling too far
        # after the player lets off the movement keys.
        # Setting the moment to PymunkPhysicsEngine.MOMENT_INF prevents it from
        # rotating.
        # Friction normally goes between 0 (no friction) and 1.0 (high friction)
        # Friction is between two objects in contact. It is important to remember
        # in top-down games that friction moving along the 'floor' is controlled
        # by damping.
        self.physics_engine.add_sprite(self.player_sprite,
                                       friction=PLAYER_FRICTION,
                                       mass=PLAYER_MASS,
                                       moment=arcade.PymunkPhysicsEngine.MOMENT_INF,
                                       collision_type="player",
                                       max_horizontal_velocity=PLAYER_MAX_HORIZONTAL_SPEED,
                                       max_vertical_velocity=PLAYER_MAX_VERTICAL_SPEED)

        # Create the walls.
        # By setting the body type to PymunkPhysicsEngine.STATIC the walls can't
        # move.
        # Movable objects that respond to forces are PymunkPhysicsEngine.DYNAMIC
        # PymunkPhysicsEngine.KINEMATIC objects will move, but are assumed to be
        # repositioned by code and don't respond to physics forces.
        # Dynamic is default.
        self.physics_engine.add_sprite_list(self.wall_list,
                                            friction=WALL_FRICTION,
                                            collision_type="wall",
                                            body_type=arcade.PymunkPhysicsEngine.STATIC)

        # Add Coins
        self.physics_engine.add_sprite_list(self.coin_list,
                                            friction=DYNAMIC_ITEM_FRICTION,
                                            collision_type="coin")

        # Add Hearts
        self.physics_engine.add_sprite_list(self.heart_list,
                                            friction=DYNAMIC_ITEM_FRICTION,
                                            collision_type="heart")

        # Add Power Ups
        self.physics_engine.add_sprite_list(self.power_ups_list,
                                            friction=DYNAMIC_ITEM_FRICTION,
                                            collision_type="power_up")

        # Create the items
        self.physics_engine.add_sprite_list(self.item_list,
                                            friction=DYNAMIC_ITEM_FRICTION,
                                            collision_type="item")

        # Create the blocks
        self.physics_engine.add_sprite_list(self.block_list,
                                            friction=DYNAMIC_ITEM_FRICTION,
                                            collision_type="block",
                                            body_type=arcade.PymunkPhysicsEngine.STATIC)

        # Add kinematic sprites
        self.physics_engine.add_sprite_list(self.moving_sprites_list,
                                            body_type=arcade.PymunkPhysicsEngine.KINEMATIC)

        # self.physics_engine.add_sprite_list(self.enemies_list,
        #                                     body_type=arcade.PymunkPhysicsEngine.KINEMATIC)

        # self.physics_engine.add_sprite_list(self.allies_list,
        #                                     body_type=arcade.PymunkPhysicsEngine.KINEMATIC)

        # Set background color
        if self.level == 0:
            arcade.set_background_color(arcade.color.BLEU_DE_FRANCE)
        elif self.level == 1:
            arcade.set_background_color(arcade.color.DARK_BLUE)
        elif self.level == 2:
            arcade.set_background_color(arcade.color.ASH_GREY)
        elif self.level == 3:
            arcade.set_background_color(arcade.color.PURPLE_MOUNTAIN_MAJESTY)
        elif self.level == 4:
            arcade.set_background_color(arcade.color.DARK_BROWN)
        elif self.level == 5:
            arcade.set_background_color(arcade.color.ORANGE_PEEL)
        elif self.level == 6:
            arcade.set_background_color(arcade.color.YELLOW_GREEN)
        elif self.level == 7:
            arcade.set_background_color(arcade.color.VANILLA)
        elif self.level == 8:
            arcade.set_background_color(arcade.color.PINK)
        elif self.level == 9:
            arcade.set_background_color(arcade.color.DARK_PINK)
        elif self.level == 10:
            arcade.set_background_color(arcade.color.GRAY_BLUE)
        elif self.level == 11:
            arcade.set_background_color(arcade.color.CADET_GREY)
        elif self.level == 12:
            arcade.set_background_color(arcade.color.DAVY_GREY)
        elif self.level == 13:
            arcade.set_background_color(arcade.color.BLACK_OLIVE)
        elif self.level == 14:
            arcade.set_background_color(arcade.color.CARROT_ORANGE)
        elif self.level == 15:
            arcade.set_background_color(arcade.color.ORIOLES_ORANGE)
        elif self.level == 16:
            arcade.set_background_color(arcade.color.DARK_BLUE)
        elif self.level == 17:
            arcade.set_background_color(arcade.color.RED_DEVIL)
        else:
            arcade.set_background_color(arcade.color.BLEU_DE_FRANCE)


    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed. """

        if key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = True
        elif key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = True
            arcade.play_sound(self.jump_sound)
            # find out if player is standing on ground, and not on a ladder
            if self.physics_engine.is_on_ground(self.player_sprite) \
                    and not self.player_sprite.is_on_ladder:
                # if on ground use control flow to filter jump speed based on player level
                if self.level_up <= 0:
                    # Go ahead and jump
                    impulse = (0, PLAYER_JUMP_IMPULSE//2)
                    self.physics_engine.apply_impulse(self.player_sprite, impulse)
                elif self.level_up <= 1:
                    # Go ahead and jump
                    impulse = (0, PLAYER_JUMP_IMPULSE//1.75)
                    self.physics_engine.apply_impulse(self.player_sprite, impulse)
                elif self.level_up <= 2:
                    # Go ahead and jump
                    impulse = (0, PLAYER_JUMP_IMPULSE//1.5)
                    self.physics_engine.apply_impulse(self.player_sprite, impulse)
                elif self.level_up <= 3:
                    # Go ahead and jump
                    impulse = (0, PLAYER_JUMP_IMPULSE//1.25)
                    self.physics_engine.apply_impulse(self.player_sprite, impulse)
                elif self.level_up <= 4:
                    # Go ahead and jump
                    impulse = (0, PLAYER_JUMP_IMPULSE)
                    self.physics_engine.apply_impulse(self.player_sprite, impulse)
                elif self.level_up <= 5:
                    # Go ahead and jump
                    impulse = (0, PLAYER_JUMP_IMPULSE*1.25)
                    self.physics_engine.apply_impulse(self.player_sprite, impulse)
                elif self.level_up <= 6:
                    # Go ahead and jump
                    impulse = (0, PLAYER_JUMP_IMPULSE*1.5)
                    self.physics_engine.apply_impulse(self.player_sprite, impulse)
                elif self.level_up <= 7:
                    # Go ahead and jump
                    impulse = (0, PLAYER_JUMP_IMPULSE*1.75)
                    self.physics_engine.apply_impulse(self.player_sprite, impulse)
                elif self.level_up <= 8:
                    # Go ahead and jump
                    impulse = (0, PLAYER_JUMP_IMPULSE*2)
                    self.physics_engine.apply_impulse(self.player_sprite, impulse)
                elif self.level_up <= 9:
                    # Go ahead and jump
                    impulse = (0, PLAYER_JUMP_IMPULSE*2.25)
                    self.physics_engine.apply_impulse(self.player_sprite, impulse)
                elif self.level_up <= 10:
                    # Go ahead and jump
                    impulse = (0, PLAYER_JUMP_IMPULSE*2.5)
                    self.physics_engine.apply_impulse(self.player_sprite, impulse)

        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = True
        
        # Adding shoot button
        if key == arcade.key.Q or key == arcade.key.N:
            self.shoot_pressed = True

        # Adding shield button
        if key == arcade.key.E or key == arcade.key.M:
            self.shield_pressed = True

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key. """

        if key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False
        elif key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = False
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = False

        # Adding shoot button
        if key == arcade.key.Q or key == arcade.key.N:
            self.shoot_pressed = False

        # Adding shield button
        if key == arcade.key.E or key == arcade.key.M:
            self.shield_pressed = False


    def on_mouse_press(self, x, y, button, modifiers):
        """ Called whenever the mouse button is clicked. """

        self.mouse_pressed = True
        try:
            self.x = self.player_centered[0] + x
            self.y = self.player_centered[1] + y
        except:
            print("An mouse exception occurred")

    def center_camera_to_player(self):
        screen_center_x = self.player_sprite.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (
            self.camera.viewport_height / 2
        )

        # Don't let camera travel past 0
        if screen_center_x < 0:
            screen_center_x = 0
        if screen_center_y < 0:
            screen_center_y = 0
        self.player_centered = screen_center_x, screen_center_y
        self.camera.move_to(self.player_centered)

    def on_update(self, delta_time):
        """ Movement and game logic """

        # Position the camera
        self.center_camera_to_player()

        # Add Frame Counter
        self.frame_count += 1

        # Calculate Jinx's level
        if self.score > 100:
            # Advance to the next level
            self.level_up = 1
            if self.score >= 500:
                # Advance to the next level
                self.level_up = 2
                if self.score >= 1250:
                    # Advance to the next level
                    self.level_up = 3
                    if self.score >= 4000:
                        # Advance to the next level
                        self.level_up = 4
                        if self.score >= 10000:
                            # Advance to the next level
                            self.level_up = 5
                            if self.score >= 25000:
                            # Advance to the next level
                                self.level_up = 6
                                if self.score >= 100000:
                                    # Advance to the next level
                                    self.level_up = 7
                                    if self.score >= 250000:
                                        # Advance to the next level
                                        self.level_up = 8
                                        if self.score >= 1000000:
                                            # Advance to the next level
                                            self.level_up = 9
                                            # level 10 to be reserved - needs debugging
                                            #  if self.score >= 10000000:
                                            #    # Advance to the next level
                                            #    self.level_up = 10

        # Calculate if Jinx on ground
        is_on_ground = self.physics_engine.is_on_ground(self.player_sprite)
        # Update player forces based on keys pressed
        if self.left_pressed and not self.right_pressed:
            # Create a force to the left. Apply it.
            if is_on_ground or self.player_sprite.is_on_ladder:
                force = (-PLAYER_MOVE_FORCE_ON_GROUND, 0)
            else:
                force = (-PLAYER_MOVE_FORCE_IN_AIR, 0)
            self.physics_engine.apply_force(self.player_sprite, force)
            # Set friction to zero for the player while moving
            self.physics_engine.set_friction(self.player_sprite, 0)
        elif self.right_pressed and not self.left_pressed:
            # Create a force to the right. Apply it.
            if is_on_ground or self.player_sprite.is_on_ladder:
                force = (PLAYER_MOVE_FORCE_ON_GROUND, 0)
            else:
                force = (PLAYER_MOVE_FORCE_IN_AIR, 0)
            self.physics_engine.apply_force(self.player_sprite, force)
            # Set friction to zero for the player while moving
            self.physics_engine.set_friction(self.player_sprite, 0)
        elif self.up_pressed and not self.down_pressed:
            # Create a force to the right. Apply it.
            if self.player_sprite.is_on_ladder:
                force = (0, PLAYER_MOVE_FORCE_ON_GROUND)
                self.physics_engine.apply_force(self.player_sprite, force)
                # Set friction to zero for the player while moving
                self.physics_engine.set_friction(self.player_sprite, 0)
        elif self.down_pressed and not self.up_pressed:
            # Create a force to the right. Apply it.
            if self.player_sprite.is_on_ladder:
                force = (0, -PLAYER_MOVE_FORCE_ON_GROUND)
                self.physics_engine.apply_force(self.player_sprite, force)
                # Set friction to zero for the player while moving
                self.physics_engine.set_friction(self.player_sprite, 0)

        else:
            # Player's feet are not moving. Therefore up the friction so we stop.
            self.physics_engine.set_friction(self.player_sprite, 1.0)

        # Move items in the physics engine
        self.physics_engine.step()

        # For each moving sprite, see if we've reached a boundary and need to
        # reverse course.
        for moving_sprite in self.moving_sprites_list:
            if moving_sprite.boundary_right and \
                    moving_sprite.change_x > 0 and \
                    moving_sprite.right > moving_sprite.boundary_right:
                moving_sprite.change_x *= -1
            elif moving_sprite.boundary_left and \
                    moving_sprite.change_x < 0 and \
                    moving_sprite.left > moving_sprite.boundary_left:
                moving_sprite.change_x *= -1
            if moving_sprite.boundary_top and \
                    moving_sprite.change_y > 0 and \
                    moving_sprite.top > moving_sprite.boundary_top:
                moving_sprite.change_y *= -1
            elif moving_sprite.boundary_bottom and \
                    moving_sprite.change_y < 0 and \
                    moving_sprite.bottom < moving_sprite.boundary_bottom:
                moving_sprite.change_y *= -1

            # Figure out and set our moving platform velocity.
            # Pymunk uses velocity is in pixels per second. If we instead have
            # pixels per frame, we need to convert.
            velocity = (moving_sprite.change_x * 1 / delta_time, moving_sprite.change_y * 1 / delta_time)
            self.physics_engine.set_velocity(moving_sprite, velocity)

        if self.can_shoot:
            if self.shoot_pressed:
                arcade.play_sound(self.shoot_sound)
                if self.level_up <= 3:
                    player_bullet = arcade.Sprite(
                        file_path + "/src/resources/images/weapons/swordBronze.png",
                        SPRITE_SCALING_PROJECTILES/1.5,
                    )
                    
                elif self.level_up <= 6:
                    arcade.play_sound(self.shoot_sound)
                    player_bullet = arcade.Sprite(
                        file_path + "/src/resources/images/weapons/swordSilver.png", 
                        SPRITE_SCALING_PROJECTILES/1.25,
                    )
                
                elif self.level_up <= 8:
                    arcade.play_sound(self.shoot_sound)
                    player_bullet = arcade.Sprite(
                        file_path + "/src/resources/images/weapons/swordGold.png", 
                        SPRITE_SCALING_PROJECTILES,
                    )
                
                elif self.level_up <= 10:
                    arcade.play_sound(self.shoot_sound)
                    player_bullet = arcade.Sprite(
                        file_path + "/src/resources/images/weapons/laserGreenHorizontal.png", 
                        SPRITE_SCALING_PROJECTILES,
                    )

                if self.player_sprite.character_face_direction == RIGHT_FACING:
                    player_bullet.change_x = round(BULLET_SPEED*(self.level_up+1),0)
                else:
                    player_bullet.change_x = round(-BULLET_SPEED*(self.level_up+1),0)
                    player_bullet.angle = -180

                player_bullet.center_x = self.player_sprite.center_x
                player_bullet.center_y = self.player_sprite.center_y

                self.scene.add_sprite(LAYER_NAME_PLAYER_BULLETS, player_bullet)

                self.can_shoot = False

        else:
            self.shoot_timer += 1
            if self.shoot_timer >= SHOOT_SPEED+10:
                self.shoot_timer = 0
            elif self.shoot_timer == SHOOT_SPEED//(self.level_up*self.level_up+1):
                self.can_shoot = True
                self.shoot_timer = 0
            

        # Add shielding
        if self.can_shield:
            if self.shield_pressed:
                if self.level_up <=3:
                    shield = arcade.Sprite(file_path + "/src/resources/images/weapons/shieldBronze.png", 
                        SPRITE_SCALING_PROJECTILES/1.25,
                        )
                elif self.level_up <=6:
                    shield = arcade.Sprite(file_path + "/src/resources/images/weapons/shieldSilver.png", 
                        SPRITE_SCALING_PROJECTILES,
                        )
                elif self.level_up <=9:
                    shield = arcade.Sprite(file_path + "/src/resources/images/weapons/shieldGold.png", 
                        SPRITE_SCALING_PROJECTILES*1.25,
                        )
                elif self.level_up <=10:
                    shield = arcade.Sprite(file_path + "/src/resources/images/weapons/chomper_bullet.png", 
                        SPRITE_SCALING_PROJECTILES*1.25,
                        )

                if self.player_sprite.character_face_direction == RIGHT_FACING:
                    shield.change_x = 1
                    shield.center_x = self.player_sprite.center_x + 25
                else:
                    shield.change_x = -1
                    shield.center_x = self.player_sprite.center_x - 25
                
                shield.center_y = self.player_sprite.center_y

                self.scene.add_sprite(LAYER_NAME_SHIELD, shield)

                self.can_shield = False
        else:
            self.shield_timer += 1
            if self.shield_timer >= SHIELD_SPEED + 10:
                self.shield_timer = 0
            elif self.shield_timer == SHIELD_SPEED//(self.level_up*self.level_up+1):
                self.can_shield = True
                self.shield_timer = 0

        # Add mouse shooting
        if self.mouse_pressed:
            if self.grenade_booster >=1:
                self.grenade_booster -=1
                for x in range(0,self.level_up):
                    grenade = GrenadeSprite((5+self.level_up), self.level_up, arcade.color.PURPLE_HEART)
                    self.grenade_list.append(grenade)

                    # Position the grenade at the player's current location
                    start_x = self.player_sprite.center_x
                    start_y = self.player_sprite.center_y
                    grenade.position = self.player_sprite.position

                    # Get from the mouse the destination location for the grenade
                    # IMPORTANT! If you have a scrolling screen, you will also need
                    # to add in self.view_bottom and self.view_left.
                    dest_x = self.x
                    dest_y = self.y

                    # Do math to calculate how to get the grenade to the destination.
                    # Calculation the angle in radians between the start points
                    # and end points. This is the angle the grenade will travel.
                    x_diff = dest_x - start_x
                    y_diff = dest_y - start_y
                    angle = math.atan2(y_diff, x_diff)

                    # What is the 1/2 size of this sprite, so we can figure out how far
                    # away to spawn the grenade
                    size = max(self.player_sprite.width, self.player_sprite.height) / 2

                    # Use angle to to spawn bullet away from player in proper direction
                    grenade.center_x += size * math.cos(angle)
                    grenade.center_y += size * math.sin(angle)

                    # Set angle of bullet
                    grenade.angle = math.degrees(angle)

                    # Gravity to use for the bullet
                    # If we don't use custom gravity, bullet drops too fast, or we have
                    # to make it go too fast.
                    # Force is in relation to bullet's angle.
                    grenade_gravity = (0, -BULLET_GRAVITY)

                    # Add the sprite. This needs to be done AFTER setting the fields above.
                    self.physics_engine.add_sprite(grenade,
                                                mass=BULLET_MASS,
                                                damping=1.0,
                                                friction=0.6,
                                                collision_type="grenade",
                                                gravity=grenade_gravity,
                                                elasticity=0.9)

                    # Add force to bullet
                    force = (BULLET_MOVE_FORCE*self.level_up, 0)
                    self.physics_engine.apply_force(grenade, force)
                    self.scene.add_sprite(LAYER_NAME_PLAYER_GRENADES, grenade)

                    # Reset
                    self.mouse_pressed = True

            elif self.level_up>=1:
                for x in range(0,self.level_up):
                    grenade = GrenadeSprite((5+self.level_up), self.level_up, arcade.color.PURPLE_HEART)
                    self.grenade_list.append(grenade)

                    # Position the grenade at the player's current location
                    start_x = self.player_sprite.center_x
                    start_y = self.player_sprite.center_y
                    grenade.position = self.player_sprite.position

                    # Get from the mouse the destination location for the grenade
                    # IMPORTANT! If you have a scrolling screen, you will also need
                    # to add in self.view_bottom and self.view_left.
                    dest_x = self.x
                    dest_y = self.y

                    # Do math to calculate how to get the grenade to the destination.
                    # Calculation the angle in radians between the start points
                    # and end points. This is the angle the grenade will travel.
                    x_diff = dest_x - start_x
                    y_diff = dest_y - start_y
                    angle = math.atan2(y_diff, x_diff)

                    # What is the 1/2 size of this sprite, so we can figure out how far
                    # away to spawn the grenade
                    size = max(self.player_sprite.width, self.player_sprite.height) / 2

                    # Use angle to to spawn bullet away from player in proper direction
                    grenade.center_x += size * math.cos(angle)
                    grenade.center_y += size * math.sin(angle)

                    # Set angle of bullet
                    grenade.angle = math.degrees(angle)

                    # Gravity to use for the bullet
                    # If we don't use custom gravity, bullet drops too fast, or we have
                    # to make it go too fast.
                    # Force is in relation to bullet's angle.
                    grenade_gravity = (0, -BULLET_GRAVITY)

                    # Add the sprite. This needs to be done AFTER setting the fields above.
                    self.physics_engine.add_sprite(grenade,
                                                mass=BULLET_MASS,
                                                damping=1.0,
                                                friction=0.6,
                                                collision_type="grenade",
                                                gravity=grenade_gravity,
                                                elasticity=0.9)

                    # Add force to bullet
                    force = (BULLET_MOVE_FORCE*self.level_up, 0)
                    self.physics_engine.apply_force(grenade, force)
                    self.scene.add_sprite(LAYER_NAME_PLAYER_GRENADES, grenade)

                    # Reset
                    self.mouse_pressed = False

        # Check lives. If it is zero, flip to the game over view.
        if self.lives == 0:
            view = GameOverView()
            self.window.show_view(view)

        # Update Animations
        self.scene.update_animation(
            delta_time,
            [
                LAYER_NAME_ENEMIES,
                LAYER_NAME_ALLIES],
        )

        # Update enemies and bullets
        self.scene.update(
            [LAYER_NAME_ENEMIES, 
            LAYER_NAME_ENEMY_BULLETS, 
            LAYER_NAME_PLAYER_BULLETS, 
            LAYER_NAME_PLAYER_GRENADES,
            LAYER_NAME_ALLIES]
        )

        # See if the enemy hit a boundary and needs to reverse direction.
        for enemy in self.scene[LAYER_NAME_ENEMIES]:
            if (
                enemy.boundary_right
                and enemy.right > enemy.boundary_right
                and enemy.change_x > 0
            ):
                enemy.change_x *= -1

            if (
                enemy.boundary_left
                and enemy.left < enemy.boundary_left
                and enemy.change_x < 0
            ):
                enemy.change_x *= -1

        # See if the ally hit a boundary and needs to reverse direction.
        for ally in self.scene[LAYER_NAME_ALLIES]:
            if (
                ally.boundary_right
                and ally.right > ally.boundary_right
                and ally.change_x > 0
            ):
                ally.change_x *= -1

            if (
                ally.boundary_left
                and ally.left < ally.boundary_left
                and ally.change_x < 0
            ):
                ally.change_x *= -1

        for projectile in self.scene[LAYER_NAME_PLAYER_BULLETS] or self.scene[LAYER_NAME_PLAYER_GRENADES]:
            hit_list = arcade.check_for_collision_with_lists(
                projectile,
                [
                    self.scene[LAYER_NAME_ENEMIES],
                    self.scene[LAYER_NAME_PLATFORMS],
                    self.scene[LAYER_NAME_MOVING_PLATFORMS],
                    self.scene[LAYER_NAME_DYNAMIC_ITEMS],
                    self.scene[LAYER_NAME_SHIELD],
                    self.scene[LAYER_NAME_DYNAMIC_TILES],
                ],
            )

            if hit_list:
                projectile.remove_from_sprite_lists()

                for collision in hit_list:
                    if (
                        self.scene[LAYER_NAME_ENEMIES]
                        in collision.sprite_lists
                    ):
                        # The collision was with an enemy
                        if self.level_up == 0:
                            collision.health -= PLAYER_BULLET_DAMAGE/5
                        elif self.level_up == 1:
                            collision.health -= PLAYER_BULLET_DAMAGE/4
                        elif self.level_up == 2:
                            collision.health -= PLAYER_BULLET_DAMAGE/3
                        elif self.level_up == 3:
                            collision.health -= PLAYER_BULLET_DAMAGE/2
                        elif self.level_up == 4:
                            collision.health -= PLAYER_BULLET_DAMAGE 
                        elif self.level_up == 5:
                            collision.health -= PLAYER_BULLET_DAMAGE*1.5
                        elif self.level_up == 6:
                            collision.health -= PLAYER_BULLET_DAMAGE*2
                        elif self.level_up == 7:
                            collision.health -= PLAYER_BULLET_DAMAGE*4  
                        elif self.level_up == 8:
                            collision.health -= PLAYER_BULLET_DAMAGE*6 
                        elif self.level_up == 9:
                            collision.health -= PLAYER_BULLET_DAMAGE*8  
                        elif self.level_up == 10:
                            collision.health -= PLAYER_BULLET_DAMAGE*10             

                        if collision.health <= 0:
                            collision.remove_from_sprite_lists()
                            if type(enemy) == type(GreenWorm()):
                                self.score += int(getattr(GreenWorm(),"health"))
                            elif type(enemy) == type(BlueSlime()):
                                self.score += int(getattr(BlueSlime(),"health"))
                            elif type(enemy) == type(GreenSlime()):
                                self.score += int(getattr(GreenSlime(),"health"))
                            elif type(enemy) == type(PurpleSlime()):
                                self.score += int(getattr(PurpleSlime(),"health"))
                            elif type(enemy) == type(SilverSlime()):
                                self.score += int(getattr(SilverSlime(),"health"))
                            elif type(enemy) == type(LavaSnake()):
                                self.score += int(getattr(LavaSnake(),"health"))
                            elif type(enemy) == type(BlueSlimeBoss()):
                                self.score += int(getattr(BlueSlimeBoss(),"health"))
                            elif type(enemy) == type(RobotEnemy()):
                                self.score += int(getattr(RobotEnemy(),"health"))
                            elif type(enemy) == type(Chomper()):
                                self.score += int(getattr(Chomper(),"health"))
                            elif type(enemy) == type(DiamondShooter()):
                                self.score += int(getattr(DiamondShooter(),"health"))
                            elif type(enemy) == type(PrimarySlime()):
                                self.score += int(getattr(PrimarySlime(),"health"))
                            elif type(enemy) == type(SecondarySlime()):
                                 self.score += int(getattr(SecondarySlime(),"health"))
                            elif type(enemy) == type(Thunderer()):
                                self.score += int(getattr(Thunderer(),"health"))
                            elif type(enemy) == type(SuperThunderer()):
                                self.score += int(getattr(SuperThunderer(),"health"))
                            elif type(enemy) == type(RolyPolyBot()):
                                self.score += int(getattr(RolyPolyBot(),"health"))
                            elif type(enemy) == type(MasterVerse()):
                                self.score += int(getattr(MasterVerse(),"health"))
                            elif type(enemy) == type(FlufflePop()):
                                self.score += int(getattr(FlufflePop(),"health"))

                        # Hit sound
                        arcade.play_sound(self.hit_sound)

                return

            if (projectile.right < 0) or (
                projectile.left
                > (self.tile_map.width * self.tile_map.tile_width) * SPRITE_SCALING_TILES
            ):
                projectile.remove_from_sprite_lists()     

        # Randfire function
        def randfire(odds, x, y, angle, origin_x, origin_top, weapon = "meteorGrey_tiny2.png"):
            odds = 2000
            adj_odds = int(odds * (1 / 60) / delta_time)
            if random.randrange(adj_odds) == 0:
                bullet2 = arcade.Sprite(file_path + f"/src/resources/images/weapons/{weapon}")
                bullet2.center_x = origin_x
                bullet2.angle = angle
                bullet2.top = origin_top
                bullet2.change_x = x
                bullet2.change_y = y
                return self.scene.add_sprite(LAYER_NAME_ENEMY_BULLETS, bullet2) 

        # Aimingfire function
        def aimingfire(rate, bullet_speed, origin_x, origin_y, aim_x, aim_y, weapon = "laserRed02.png"):
            start_x = origin_x
            start_y = origin_y

            # Get the destination location for the bullet
            dest_x = aim_x
            dest_y = aim_y

            # Do math to calculate how to get the bullet to the destination.
            # Calculation the angle in radians between the start points
            # and end points. This is the angle the bullet will travel.
            x_diff = dest_x - start_x
            y_diff = dest_y - start_y
            angle = math.atan2(y_diff, x_diff)

            # Set the enemy to face the player. Not Required Presently
            # enemy.angle = math.degrees(angle) - 0
            
            # Shoot every 60 frames change of shooting each frame
            if self.frame_count % rate == 0:
                bullet2 = arcade.Sprite(file_path + f"/src/resources/images/weapons/{weapon}")
                bullet2.center_x = start_x
                bullet2.center_y = start_y

                # Angle the bullet sprite
                bullet2.angle = math.degrees(angle)

                # Taking into account the angle, calculate our change_x
                # and change_y. Velocity is how fast the bullet travels.
                bullet2.change_x = math.cos(angle) * bullet_speed
                bullet2.change_y = math.sin(angle) * bullet_speed

                self.scene.add_sprite(LAYER_NAME_ENEMY_BULLETS, bullet2)  

        # Loop through each enemy that we have to work out shooting mechanics
        for enemy in self.scene[LAYER_NAME_ENEMIES]:
            if type(enemy) == type(GreenWorm()):
                randfire(odds =2000, x=-1, y=0, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "meteorGrey_tiny1.png")
                randfire(odds =2000, x=1, y=0, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "meteorGrey_tiny1.png")

            elif type(enemy) == type(BlueSlime()):
                randfire(odds =1000, x=-2, y=0, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "candyBlue.png")
                randfire(odds =1000, x=2, y=0, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "candyBlue.png")

            elif type(enemy) == type(LavaSnake()):
                randfire(odds =500, x=-4, y=0, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "lava_ball_small.png")
                randfire(odds =500, x=4, y=0, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "lava_ball_small.png")
                randfire(odds =500, x=-4, y=-1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "lava_ball_small.png")
                randfire(odds =500, x=4, y=-1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "lava_ball_small.png")
                randfire(odds =500, x=-4, y=1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "lava_ball_small.png")
                randfire(odds =500, x=4, y=1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "lava_ball_small.png")

            elif type(enemy) == type(GreenSlime()):
                randfire(odds =500, x=-3, y=0, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "candyGreen.png")
                randfire(odds =500, x=-3, y=1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "candyGreen.png")
                randfire(odds =500, x=3, y=0, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "candyGreen.png")
                randfire(odds =500, x=3, y=1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "candyGreen.png")


            elif type(enemy) == type(PurpleSlime()):
                randfire(odds =250, x=-4, y=0, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "candyRed.png")
                randfire(odds =250, x=4, y=0, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "candyRed.png")
                randfire(odds =250, x=-4, y=1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "candyRed.png")
                randfire(odds =250, x=4, y=1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "candyRed.png")
            
            elif type(enemy) == type(SilverSlime()):    
                aimingfire(rate = 120, bullet_speed=8, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "spinner.png")

            elif type(enemy) == type(Thunderer()):
                randfire(odds =500, x=1, y=-3, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "thunderbullet1.png")
                randfire(odds =500, x=-1, y=-3, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "thunderbullet1.png")
                randfire(odds =500, x=-2, y=-6, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "thunderbullet2.png")
                randfire(odds =500, x=2, y=-6, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "thunderbullet2.png")
                randfire(odds =500, x=0, y=-10, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "sparky.png")
                aimingfire(rate = 360, bullet_speed=6, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "thunderbullet.png")

            elif type(enemy) == type(SuperThunderer()):
                randfire(odds =100, x=1, y=-3, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "thunderbullet1.png")
                randfire(odds =100, x=-1, y=-3, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "thunderbullet1.png")
                randfire(odds =100, x=-2, y=-6, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "thunderbullet2.png")
                randfire(odds =100, x=2, y=-6, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "thunderbullet2.png")
                randfire(odds =100, x=0, y=-10, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "sparky.png")
                aimingfire(rate = 30, bullet_speed=12, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "thunderbullet.png")

            elif type(enemy) == type(Chomper()):    
                aimingfire(rate = 100, bullet_speed=8, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "chomper_bullet.png")

            elif type(enemy) == type(PrimarySlime()):   
                aimingfire(rate = 360, bullet_speed=12, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "mupBiggest.png")
                aimingfire(rate = 120, bullet_speed=8, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "mupBig.png")
                aimingfire(rate = 60, bullet_speed=4, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "mupSmall.png")

            elif type(enemy) == type(SecondarySlime()):   
                aimingfire(rate = 120, bullet_speed=12, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "mupBiggest2.png")
                aimingfire(rate = 60, bullet_speed=8, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "mupBig2.png")
                aimingfire(rate = 30, bullet_speed=4, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "mupSmall2.png")

            elif type(enemy) == type(DiamondShooter()):
                randfire(odds =1000, x=-10, y=2, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "gemYellow.png")
                randfire(odds =1000, x=-20, y=-1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "gemGreen.png")
                randfire(odds =1000, x=-30, y=1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "gemBlue.png")
                randfire(odds =1000, x=-20, y=-2, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "gemGreen.png")
                randfire(odds =1000, x=-30, y=2, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "gemBlue.png")
                randfire(odds =1000, x=-40, y=0, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "gemRed.png")
                randfire(odds =1000, x=10, y=2, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "gemYellow.png")
                randfire(odds =1000, x=20, y=-1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "gemGreen.png")
                randfire(odds =1000, x=30, y=1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "gemBlue.png")
                randfire(odds =1000, x=20, y=-2, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "gemGreen.png")
                randfire(odds =1000, x=30, y=2, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "gemBlue.png")
                randfire(odds =1000, x=40, y=0, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "gemRed.png")
                randfire(odds =1000, x=0, y=10, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "gemYellow.png")

            elif type(enemy) == type(BlueSlimeBoss()):    
                aimingfire(rate = 60, bullet_speed=6, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "spinner.png")
                randfire(odds =1000, x=-10, y=0, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=-10, y=1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=-10, y=2, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=-10, y=3, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=-10, y=4, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=-10, y=-1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=-10, y=-2, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=-10, y=-3, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=-10, y=-4, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=0, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=2, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=3, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=4, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=-1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=-2, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=-3, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=-4, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
    
            elif type(enemy) == type(RobotEnemy()):    
                aimingfire(rate = 60, bullet_speed=5, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "laserRed02.png")
                aimingfire(rate = 20, bullet_speed=2, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "laserBlue01.png")
               
            elif type(enemy) == type(RolyPolyBot()):    
                aimingfire(rate = 40, bullet_speed=10, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "laserGreenHorizontal.png")
                aimingfire(rate = 30, bullet_speed=5, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "laserRed02.png")
                aimingfire(rate = 20, bullet_speed=2, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "laserBlue01.png")
 
            elif type(enemy) == type(MasterVerse()): 
                aimingfire(rate = 60, bullet_speed=20, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "laserPurple.png") 
                aimingfire(rate = 30, bullet_speed=10, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "laserGreenHorizontal.png")
                aimingfire(rate = 20, bullet_speed=5, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "laserRed02.png")
                aimingfire(rate = 10, bullet_speed=2, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "laserBlue01.png")

            elif type(enemy) == type(FlufflePop()): 
                aimingfire(rate = 20, bullet_speed=20, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "laserPurple.png") 
                aimingfire(rate = 10, bullet_speed=10, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "laserGreenHorizontal.png")
                aimingfire(rate = 5, bullet_speed=5, origin_x=enemy.center_x, origin_y=enemy.center_y, aim_x=self.player_sprite.center_x, aim_y=self.player_sprite.center_y, weapon = "laserRed02.png")
                randfire(odds =1000, x=-10, y=0, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=-10, y=1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=-10, y=2, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=-10, y=3, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=-10, y=4, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=-10, y=-1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=-10, y=-2, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=-10, y=-3, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=-10, y=-4, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=0, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=2, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=3, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=4, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=-1, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=-2, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=-3, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
                randfire(odds =1000, x=10, y=-4, angle=0, origin_x = enemy.center_x, origin_top = enemy.top, weapon = "spinner.png")
  
                 
        # See if we hit any coins
        coin_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.coin_list
        )

        # See if we hit any hearts
        heart_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.heart_list
        )

        # See if we hit any power ups
        power_up_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.power_ups_list
        )

        # See if we hit any enemies
        enemy_collision_list = arcade.check_for_collision_with_lists(
            self.player_sprite,
            [
                self.scene[LAYER_NAME_ENEMIES],
                self.scene[LAYER_NAME_ENEMY_BULLETS],
            ],
        )

        # Loop Through Enemy Bullets and check for collisions

        for bullet2 in self.scene[LAYER_NAME_ENEMY_BULLETS]:
            hit_list = arcade.check_for_collision_with_lists(
                bullet2,
                [
                    self.scene[LAYER_NAME_DYNAMIC_ITEMS],
                    self.scene[LAYER_NAME_PLATFORMS],
                    self.scene[LAYER_NAME_MOVING_PLATFORMS],
                    self.scene[LAYER_NAME_SHIELD],
                    self.scene[LAYER_NAME_ALLIES],
                    self.scene[LAYER_NAME_DYNAMIC_TILES],
                ],
            )

            if hit_list:
                bullet2.remove_from_sprite_lists()

        # Loop through each coin we hit (if any) and remove it
        
        for coin in coin_hit_list:
            # Figure out how many points this coin is worth
            if "Points" not in coin.properties:
                print("Warning, collected a coin without a Points property.")
            else:
                points = int(coin.properties["Points"])
                self.score += points
            # Remove the coin
            coin.remove_from_sprite_lists()
            # Play a sound
            arcade.play_sound(self.collect_coin_sound)

        for heart in heart_hit_list:
            # Figure out how many lives this heart is worth
            if "Lives" not in heart.properties:
                print("Warning, collected a heart without a Lives property.")
            else:
                lives = int(heart.properties["Lives"])
                self.lives += lives
            # Remove the coin
            heart.remove_from_sprite_lists()
            # Play a sound
            arcade.play_sound(self.collect_coin_sound)

        for power_up in power_up_hit_list:
            # Figure out the attributes of this power up
            if "Shield" in power_up.properties:
                self.invincibility_timer = int(power_up.properties["Shield"])
                self.can_die = False
            elif "Grenades" in power_up.properties:
                self.grenade_booster = int(power_up.properties["Grenades"]) 
                self.mouse_pressed = True
            elif "Speed" in power_up.properties:
                speed = int(power_up.properties["Speed"])       
            elif "Gravity" in power_up.properties:
                gravity = int(power_up.properties["Gravity"])
            else:
                print("Warning, collected a power_up without a property.")
            
                
            # Remove the coin
            power_up.remove_from_sprite_lists()
            # Play a sound
            arcade.play_sound(self.collect_coin_sound)

        # Look through the enemies to see if we hit any:
        for collision in enemy_collision_list:
            if self.can_die:
                if self.scene[LAYER_NAME_ENEMIES] in collision.sprite_lists:
                # If we collide with an enemy then we lose a life
                    arcade.play_sound(self.game_over)
                    self.lives -=1
                    self.can_die = False
                    return
                elif self.scene[LAYER_NAME_ENEMY_BULLETS] in collision.sprite_lists:
                    arcade.play_sound(self.game_over)
                    self.lives -=1
                    self.can_die = False
                    return
            else:
                self.death_timer +=1
                self.invincibility_timer -= 1
                if self.invincibility_timer > 0:
                    self.can_die = False
                elif self.death_timer > DEATH_PROTECT + 200 :
                    self.death_timer = 0
                elif self.invincibility_timer <= 0 and self.death_timer >= DEATH_PROTECT:
                    self.can_die = True
                    self.invincibility_timer = 0 
                    self.death_timer = 0
                elif self.invincibility_timer <= 0:
                    self.invincibility_timer = 0 

        # Did the player fall off the map?
        if self.player_sprite.center_y < -100:
            arcade.play_sound(self.game_over)
            self.lives -=1
            self.setup()

        # Did the player touch something they should not?
        if arcade.check_for_collision_with_list(
            self.player_sprite, self.dont_touch_list
        ):
            arcade.play_sound(self.game_over)
            self.lives -=1
            self.setup()

        # See if the user got to the end of the level
        if self.player_sprite.center_x >= self.end_of_map:
            # Advance to the next level
            self.level += 1

            # Make sure to keep the score from this level when setting up the next level
            self.reset_score = False

            # Load the next level
            self.setup()

        # # Allies Text Talk - this bit is a bit dodgy atm
        # if type(ally) in self.scene[LAYER_NAME_ALLIES] == type(Hooboo()):
        #     self.hooboo_message = arcade.Text(
        #     text = ally.speech,
        #     start_x=ally.center_x,
        #     start_y=ally.top,
        #     color = arcade.color.BLACK,
        #     font_size = DEFAULT_FONT_SIZE    
        #     )
        #     return self.hooboo_message
        # elif type(ally) in self.scene[LAYER_NAME_ALLIES] == type(Pumbean()):
        #     self.pumbean_message = arcade.Text(
        #     text = ally.speech,
        #     start_x=ally.center_x,
        #     start_y=ally.top,
        #     color = arcade.color.RED,
        #     font_size = DEFAULT_FONT_SIZE    
        #     )
        #     return self.pumbean_message
            
    def on_draw(self):
        """ Draw everything """
        self.clear()

        # Behind items
        self.background_list.draw()
        self.foreground_list.draw()
        self.wall_list.draw()
        self.ladder_list.draw()
        self.item_list.draw()
        self.block_list.draw()
        self.coin_list.draw()
        self.heart_list.draw()
        self.power_ups_list.draw()
        # This variable contains the enemies and bullets
        self.scene.draw()

        self.moving_sprites_list.draw()
        self.dont_touch_list.draw()
        self.grenade_list.draw()
        self.player_list.draw()
        # self.enemies_list.draw()

        # Activate the GUI camera before drawing GUI elements
        self.gui_camera.use()

        # Draw grenade booster count on the screen, scrolling it with the viewport
        score_text = f"Grenade Booster Remaining: {self.grenade_booster}"
        arcade.draw_text(
            score_text,
            10,
            160,
            arcade.csscolor.DARK_GREEN,
            18,
        )
        # Draw invincibility on the screen, scrolling it with the viewport
        score_text = f"Invincibility Shield Remaining: {self.invincibility_timer}"
        arcade.draw_text(
            score_text,
            10,
            130,
            arcade.csscolor.ORANGE_RED,
            18,
        )
        # Draw lives on the screen, scrolling it with the viewport
        score_text = f"Remaining Life Points: {self.lives}"
        arcade.draw_text(
            score_text,
            10,
            100,
            arcade.csscolor.LIGHT_GOLDENROD_YELLOW,
            18,
        )
        # Draw our score on the screen, scrolling it with the viewport
        score_text = f"Score: {self.score}"
        arcade.draw_text(
            score_text,
            10,
            70,
            arcade.csscolor.BLACK,
            18,
        )

        # Draw our score on the screen, scrolling it with the viewport
        level_text = f"Current Level: {self.level}"
        arcade.draw_text(
            level_text,
            10,
            40,
            arcade.csscolor.DARK_BLUE,
            18,
        )

        # Draw our score on the screen, scrolling it with the viewport
        levelup_text = f"Player Level Up: {self.level_up}"
        arcade.draw_text(
            levelup_text,
            10,
            10,
            arcade.csscolor.DARK_RED,
            18,
        )

        # Activate our Camera
        self.camera.use()

        # Add Text
        self.message1.draw()
        self.message2.draw()
        self.message3.draw()
        self.message4.draw()
        self.message5.draw()

def main():
    """ Main function """
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    start_view = MenuView()
    window.show_view(start_view)
    arcade.run()


if __name__ == "__main__":
    main()