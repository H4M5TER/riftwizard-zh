import pygame
from Level import *

canvas_size = 16*28
class GlowingStar():

	def __init__(self):
		self.cur_color = (0, 0, 0) 
		self.end_color = Tags.Ice.color
		self.x = 16 * random.randint(0, 28) + 8
		self.y = 16 * random.randint(0, 28) + 8
		self.radius = 0

		self.frame = 0
		self.lifetime = 1200

		self.dx = 0
		self.dy = 0

	def draw(self, surface):
		self.frame += 1

		self.x += self.dx
		self.x %= canvas_size
		

		self.y += self.dx
		self.y %= canvas_size

		high_point = self.lifetime // 2
		intensity = (high_point - abs(self.frame - high_point)) / high_point
		color = tween_color(COLOR_BLACK, self.end_color, intensity)

		radius = 1
		
		draw_x = math.floor(self.x)
		draw_y = math.floor(self.y)

		for i in range(-radius, radius+1):
			surface.set_at((draw_x+i, draw_y), color.to_tup())
			surface.set_at((draw_x, draw_y+i), color.to_tup())

class StarAnim():

	def __init__(self):
		self.stars = []
		self.spawn_chance = .15
		self.surface = pygame.Surface((canvas_size, canvas_size))

	def advance(self):

		if random.random() < self.spawn_chance and len(self.stars) < 100:
			self.stars.append(GlowingStar())

		self.surface.fill((0, 0, 0))
		for star in self.stars:
			star.draw(self.surface)

		self.stars = [s for s in self.stars if s.frame < s.lifetime]




