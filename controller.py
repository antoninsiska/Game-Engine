import pygame
import time

pygame.init()
pygame.joystick.init()

if pygame.joystick.get_count() == 0:
    Exception("no controller conected")
    exit()

joystick = pygame.joystick.Joystick(0)
joystick.init()

    
class _values:
    pygame.event.pump()
    axes = [joystick.get_axis(i) for i in range(joystick.get_numaxes())]
    buttons = [joystick.get_button(i) for i in range(joystick.get_numbuttons())]
    hat = joystick.get_hat(0) if joystick.get_numhats() > 0 else (0, 0)

class rightJoystickY:
    axes = _values.axes
    pygame.event.pump()
    @classmethod
    def plus(cls):
        if cls.axes[1] > 0.99:
            return True
        elif cls.axes[1] < -0.99:
            return False
    @classmethod
    def minus(cls):
        if cls.axes[1] > 0.99:
            return False
        elif cls.axes[1] < -0.99:
            return True

def get():
    axes = _values.axes

    if axes[1] > 0.99:
        return rightJoystickY
    else:
        return axes[1]