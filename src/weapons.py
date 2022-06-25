# This is the main weapons script

from enemies import *
from objects import *

# Shooting Constants
SPRITE_SCALING_PROJECTILES = 0.6
SHOOT_SPEED = 10
BULLET_SPEED = 10
SHIELD_SPEED = 100
PLAYER_BULLET_DAMAGE = 10

# How much force to put on the bullet
BULLET_MOVE_FORCE = 4500

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