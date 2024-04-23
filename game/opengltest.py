import pygame

pygame.init()
display = pygame.display.set_mode((1920, 1080), flags=pygame.FULLSCREEN | pygame.OPENGL)
while True:
	pygame.draw.rect(display, (100, 100, 100), (100, 100, 200, 200))
	pygame.display.flip()

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			if self.game and self.game.p1.is_alive():
				save_game(self.game, 'savefile')
			self.running = False
