# This is the main weapons script

from enemies import *
from objects import *
import random

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


# Randfire function
def randfire(odds, x, y, angle, origin_x, origin_top, weapon = "meteorGrey_tiny2.png"):
    odds = 2000
    adj_odds = int(odds * (1 / 60) / delta_time)
    if random.randrange(adj_odds) == 0:
        bullet2 = arcade.Sprite(file_path + f"/resources/images/weapons/{weapon}")
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
        bullet2 = arcade.Sprite(file_path + f"/resources/images/weapons/{weapon}")
        bullet2.center_x = start_x
        bullet2.center_y = start_y

        # Angle the bullet sprite
        bullet2.angle = math.degrees(angle)

        # Taking into account the angle, calculate our change_x
        # and change_y. Velocity is how fast the bullet travels.
        bullet2.change_x = math.cos(angle) * bullet_speed
        bullet2.change_y = math.sin(angle) * bullet_speed

        self.scene.add_sprite(LAYER_NAME_ENEMY_BULLETS, bullet2)  

class GrenadeSprite(arcade.SpriteSolidColor):
    """ Bullet Sprite """
    def pymunk_moved(self, physics_engine, dx, dy, d_angle):
        """ Handle when the sprite is moved by the physics engine. """
        # If the bullet falls below the screen, remove it
        if self.center_y < -100:
            self.remove_from_sprite_lists()

