from player import *

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

        main_path = file_path + f"/resources/images/animated_characters/{name_folder}/{name_file}"

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

class SilverSlime(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("slimeSilver", "slimeSilver")

        self.health = 250

class PrimarySlime(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("primaryslime", "primaryslime")

        self.health = 2000

class SecondarySlime(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("secondaryslime", "secondaryslime")

        self.health = 4000

class BlueSlimeBoss(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("slimeBlueBoss", "slimeBlueBoss")

        self.health = 10000

class Thunderer(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("thunderer", "thunderer")

        self.health = 100

class Chomper(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("chomper", "chomper")

        self.health = 300

class DiamondShooter(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("diamondshooter", "diamondshooter")

        self.health = 150

class RobotEnemy(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("robot", "robot")

        self.health = 500

class RolyPolyBot(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("rolypolybot", "rolypolybot")

        self.health = 500

class MasterVerse(Enemy):
    def __init__(self):

        # Set up parent class
        super().__init__("masterverse", "masterverse")

        self.health = 500

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

        self.health = 1000

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

        self.health = 25000

class RolyPolyBot(Ally):
    def __init__(self):

        # Set up parent class
        super().__init__("rolypolybot", "rolypolybot")

        self.health = 500

class SecondarySlime(Ally):
    def __init__(self):

        # Set up parent class
        super().__init__("secondaryslime", "secondaryslime")

        self.health = 400