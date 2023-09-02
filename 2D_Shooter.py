import pygame
from pygame import mixer
import os
import random
import csv
import button

pygame.init()
mixer.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = int(SCREEN_WIDTH * 0.8)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('pew pew')

#FPS
clock = pygame.time.Clock()
FPS = 60

#Game Variables
GRAVITY = 0.75
SCROLL_TRESH = 200
ROWS = 16
COLS = 150
TILE_SIZE = SCREEN_HEIGHT // ROWS
TILE_TYPES = 21
MAX_LEVELS = 3

game_start = False
game_intro = False
screen_scroll = 0
bg_scroll = 0
level = 1

BG = (144, 201, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
PINK = (235, 65, 54)

moving_left = False
moving_right = False
fire = False
grenade = False
grenade_thrown = False

#Load the Audio for the game
pygame.mixer.music.load(r"audio/music2.mp3")
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1, 0.0, 5000) #Loop, Delay, Fade Duration

#Jump Sound Effect
jump_fx = pygame.mixer.Sound(r"audio/jump.wav")
jump_fx.set_volume(0.5)

#Shooting Sound Effect
fire_fx = pygame.mixer.Sound(r"audio/shot.wav")
fire_fx.set_volume(0.5)

#Grenade Sound Effect
grenade_fx = pygame.mixer.Sound(r"audio/grenade.wav")
grenade_fx.set_volume(0.5)

#Load Images
#Button Images
start_img = pygame.image.load('img/start_btn.png').convert_alpha()
exit_img = pygame.image.load('img/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('img/restart_btn.png').convert_alpha()

#Background Images
pine1_img = pygame.image.load('img/Background/pine1.png').convert_alpha()
pine2_img = pygame.image.load('img/Background/pine2.png').convert_alpha()
mountain_img = pygame.image.load('img/Background/mountain.png').convert_alpha()
sky_img = pygame.image.load('img/Background/sky_cloud.png').convert_alpha()

img_list = []
for x in range(TILE_TYPES):
	img = pygame.image.load(f'img/Tile/{x}.png')
	img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
	img_list.append(img)
#bullet
bullet_img = pygame.image.load('img/icons/bullet.png').convert_alpha()
#grenade
grenade_img = pygame.image.load('img/icons/grenade.png').convert_alpha()
#pick up boxes
health_box_img = pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('img/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('img/icons/grenade_box.png').convert_alpha()
item_boxes = {
	'Health'	: health_box_img,
	'Ammo'		: ammo_box_img,
	'Grenade'	: grenade_box_img
}

#define font
font = pygame.font.SysFont('Futura', 30)

def draw_text(text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))


def draw_bg():
	screen.fill(BG)
	width = sky_img.get_width()
	for x in range(5):
		screen.blit(sky_img, ((x * width) - bg_scroll * 0.5, 0))
		screen.blit(mountain_img, ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - mountain_img.get_height() - 300))
		screen.blit(pine1_img, ((x * width) - bg_scroll * 0.7, SCREEN_HEIGHT - pine1_img.get_height() - 150))
		screen.blit(pine2_img, ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - pine2_img.get_height()))

#Function for level resets
def reset_level():
	enemy_group.empty()
	projectile_group.empty()
	grenade_group.empty()
	explosion_group.empty()
	item_box_group.empty()
	decoration_group.empty()
	water_group.empty()
	exit_group.empty()

	#Clear the world
	clear_world = []
	for rows in range(ROWS):
		row = [-1] * COLS
		clear_world.append(row)

	return clear_world

class game_body(pygame.sprite.Sprite):
	def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
		pygame.sprite.Sprite.__init__(self)
		self.alive = True
		self.char_type = char_type
		self.speed = speed
		self.ammo = ammo
		self.start_ammo = ammo
		self.shoot_cooldown = 0
		self.grenades = grenades
		self.health = 100
		self.max_health = self.health
		self.direction = 1
		self.vel_y = 0
		self.jump = False
		self.in_air = True
		self.flip = False

		self.animation_list = []
		self.frame_index = 0
		self.action = 0
		self.update_time = pygame.time.get_ticks()

		#ai specific variables
		self.move_counter = 0
		self.vision = pygame.Rect(0, 0, 150, 20)
		self.idling = False
		self.idling_counter = 0

		#load all images for the players
		#Action Types:
		# 0 = Idling
		# 1 = Running
		# 2 = Jumping
		# 3 = Death
		animation_types = ['Idle', 'Run', 'Jump', 'Death']
		for animation in animation_types:
			#reset temporary list of images
			temp_list = []
			#count number of files in the folder
			num_of_frames = len(os.listdir(f'img/{self.char_type}/{animation}'))
			for i in range(num_of_frames):
				img = pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha()
				img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
				temp_list.append(img)
			self.animation_list.append(temp_list)

		self.image = self.animation_list[self.action][self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()


	def update(self):
		self.update_animation()
		self.check_alive()
		#update cooldown
		if self.shoot_cooldown > 0:
			self.shoot_cooldown = self.shoot_cooldown - 1


	def movement(self, moving_left, moving_right):
		#reset movement variables
		dx = 0
		dy = 0

		screen_scroll = 0

		#assign movement variables if moving left or right
		if moving_left:
			dx = -self.speed
			self.flip = True
			self.direction = -1
		if moving_right:
			dx = self.speed
			self.flip = False
			self.direction = 1

		#jump
		if self.jump == True and self.in_air == False:
			self.vel_y = -11
			self.jump = False
			self.in_air = True

		#apply gravity
		self.vel_y = self.vel_y + GRAVITY
		if self.vel_y > 10:
			self.vel_y
		dy = dy + self.vel_y

		#check for collision with the environment
		#list all the blocaks that are interactable with the game_body class
		for tile in world.obstacle_list:
			#X axis check
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				dx = 0
				#For Enemies
				if self.char_type == "enemy":
					self.direction = self.direction * -1
					self.move_counter = 0
			#Y axis check
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				#Check position if below and above ground tiles
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				#Check if game body is falling
				elif self.vel_y >= 0:
					self.vel_y = 0
					self.in_air = False
					dy = tile[1].top - self.rect.bottom

		#Temporary Ground
		#if self.rect.bottom + dy > 300:
		#	dy = 300 - self.rect.bottom
		#	self.in_air = False

		#Check if body collides with the exit sign
		level_complete = False
		if pygame.sprite.spritecollide(self, exit_group, False):
			level_complete = True

		#Environmental Deaths
		if pygame.sprite.spritecollide(self, water_group, False):
			self.health = 0

		if self.rect.bottom > SCREEN_HEIGHT:
			self.health = 0

		#Check if player is going off bounds
		if self.char_type == "player":
			if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
				dx = 0

		#update rectangle position
		self.rect.x = self.rect.x + dx
		self.rect.y = self.rect.y + dy

		#Update scroll based on game_body's position
		if self.char_type == "player":
			if( self.rect.right > SCREEN_WIDTH - SCROLL_TRESH and bg_scroll < (world.level_length * TILE_SIZE) - SCREEN_WIDTH) \
			or (self.rect.left < SCROLL_TRESH and bg_scroll > abs(dx)):
				self.rect.x = self.rect.x - dx
				screen_scroll = -dx

		return screen_scroll, level_complete


	def fire(self):
		if self.shoot_cooldown == 0 and self.ammo > 0:
			self.shoot_cooldown = 20
			bullet = projectile_class(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery, self.direction)
			projectile_group.add(bullet)
			#reduce ammo
			self.ammo = self.ammo - 1
			fire_fx.play()


	def ai(self):
		if self.alive and player.alive:
			if self.idling == False and random.randint(1, 200) == 1:
				self.update_action(0)
				self.idling = True
				self.idling_counter = 50
			#check if the ai in near the player
			if self.vision.colliderect(player.rect):
				#stop running and face the player
				self.update_action(0)
				#shoot
				self.fire()
			else:
				if self.idling == False:
					if self.direction == 1:
						ai_moving_right = True
					else:
						ai_moving_right = False
					ai_moving_left = not ai_moving_right
					self.movement(ai_moving_left, ai_moving_right)
					self.update_action(1)
					self.move_counter = self.move_counter + 1
					#update ai vision as the enemy moves
					self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)

					if self.move_counter > TILE_SIZE:
						self.direction = self.move_counter * -1
						self.move_counter = self.move_counter * -1
				else:
					self.idling_counter = self.idling_counter - 1
					if self.idling_counter <= 0:
						self.idling = False

		#Scroll
		self.rect.x = self.rect.x + screen_scroll


	def update_animation(self):
		#update animation
		ANIMATION_COOLDOWN = 100
		#update image depending on current frame
		self.image = self.animation_list[self.action][self.frame_index]
		#check if enough time has passed since the last update
		if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
			self.update_time = pygame.time.get_ticks()
			self.frame_index = self.frame_index + 1
		#if the animation has run out the reset back to the start
		if self.frame_index >= len(self.animation_list[self.action]):
			if self.action == 3:
				self.frame_index = len(self.animation_list[self.action]) - 1
			else:
				self.frame_index = 0



	def update_action(self, new_action):
		#check if the new action is different to the previous one
		if new_action != self.action:
			self.action = new_action
			#update the animation settings
			self.frame_index = 0
			self.update_time = pygame.time.get_ticks()



	def check_alive(self):
		if self.health <= 0:
			self.health = 0
			self.speed = 0
			self.alive = False
			self.update_action(3)


	def draw(self):
		screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


class game_world():
	def __init__(self):
		self.obstacle_list = []

	def process_data(self, data):
		self.level_length = len(data[0])
		#iterate through each value in level data file
		for row_num, row in enumerate(data):
			for col_num, tile in enumerate(row):
				if tile >= 0:
					img = img_list[tile]
					img_rect = img.get_rect()
					img_rect.x = col_num * TILE_SIZE
					img_rect.y = row_num * TILE_SIZE
					tile_data = (img, img_rect)
					#Ground tiles
					if tile >= 0 and tile <= 8:
						self.obstacle_list.append(tile_data)
					#Water tile
					elif tile >= 9 and tile <= 10:
						water = water_class(img, col_num * TILE_SIZE, row_num * TILE_SIZE)
						water_group.add(water)
					#Decortaion tiles
					elif tile >= 11 and tile <= 14:
						decoration = decoration_class(img, col_num * TILE_SIZE, row_num * TILE_SIZE)
						decoration_group.add(decoration)
					#Player Tile
					elif tile == 15:
						player = game_body('player', col_num * TILE_SIZE, row_num * TILE_SIZE, 1.65, 5, 20, 5)
						health_bar = health_bar_class(10, 10, player.health, player.health)
					#Enemy Tile
					elif tile == 16:
						enemy = game_body('enemy', col_num * TILE_SIZE, row_num * TILE_SIZE, 1.65, 2, 20, 0)
						enemy_group.add(enemy)
					#Item box tiles
					elif tile == 17:
						item_box = item_box_class('Ammo', col_num * TILE_SIZE, row_num * TILE_SIZE)
						item_box_group.add(item_box)
					elif tile == 18:
						item_box = item_box_class('Grenade', col_num * TILE_SIZE, row_num * TILE_SIZE)
						item_box_group.add(item_box)
					elif tile == 19:
						item_box = item_box_class('Health', col_num * TILE_SIZE, row_num * TILE_SIZE)
						item_box_group.add(item_box)
					#Exit tile
					elif tile == 20:
						exit = exit_class(img, col_num * TILE_SIZE, row_num * TILE_SIZE)
						exit_group.add(exit)

		return player, health_bar


	def draw(self):
		for tile in self.obstacle_list:
			tile[1][0] = tile[1][0] + screen_scroll
			screen.blit(tile[0], tile[1])


class decoration_class(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		# Sroll
		self.rect.x = self.rect.x + screen_scroll


class water_class(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		# Sroll
		self.rect.x = self.rect.x + screen_scroll


class exit_class(pygame.sprite.Sprite):
	def __init__(self, img, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = img
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		# Sroll
		self.rect.x = self.rect.x + screen_scroll



class item_box_class(pygame.sprite.Sprite):
	def __init__(self, item_type, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.item_type = item_type
		self.image = item_boxes[self.item_type]
		self.rect = self.image.get_rect()
		self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

	def update(self):
		# Sroll
		self.rect.x = self.rect.x + screen_scroll
		#check if the player has picked up the box
		if pygame.sprite.collide_rect(self, player):
			#check what kind of box it was
			if self.item_type == 'Health':
				player.health = player.health + 25
				if player.health > player.max_health:
					player.health = player.max_health
			elif self.item_type == 'Ammo':
				player.ammo = player.ammo + 15
			elif self.item_type == 'Grenade':
				player.grenades = player.grenades + 3
			#delete the item box
			self.kill()


class health_bar_class():
	def __init__(self, x, y, health, max_health):
		self.x = x
		self.y = y
		self.health = health
		self.max_health = max_health

	def draw(self, health):
		#update with new health
		self.health = health
		#calculate health ratio
		ratio = self.health / self.max_health
		pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
		pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
		pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))


class projectile_class(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.speed = 10
		self.image = bullet_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.direction = direction

	def update(self):
		#move bullet
		self.rect.x = self.rect.x + (self.direction * self.speed) + screen_scroll
		#check if bullet has gone off screen
		if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
			self.kill()

		for tile in world.obstacle_list:
			if tile[1].colliderect(self.rect):
				self.kill()

		#check collision with characters
		if pygame.sprite.spritecollide(player, projectile_group, False):
			if player.alive:
				player.health = player.health - 5
				self.kill()
		for enemy in enemy_group:
			if pygame.sprite.spritecollide(enemy, projectile_group, False):
				if enemy.alive:
					enemy.health = enemy.health - 25
					self.kill()



class grenade_class(pygame.sprite.Sprite):
	def __init__(self, x, y, direction):
		pygame.sprite.Sprite.__init__(self)
		self.timer = 100
		self.vel_y = -11
		self.speed = 7
		self.image = grenade_img
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.width = self.image.get_width()
		self.height = self.image.get_height()
		self.direction = direction

	def update(self):
		self.vel_y = self.vel_y + GRAVITY
		dx = self.direction * self.speed
		dy = self.vel_y

		#Check collision with the game world
		for tile in world.obstacle_list:
			# check collision with walls
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				self.direction = self.direction * -1
				dx = self.direction * self.speed
			# Y axis check
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				self.speed = 0
				# Check position if below and above ground tiles
				if self.vel_y < 0:
					self.vel_y = 0
					dy = tile[1].bottom - self.rect.top
				# Check if grenade is falling
				elif self.vel_y >= 0:
					self.vel_y = 0
					dy = tile[1].top - self.rect.bottom

		#update grenade position
		self.rect.x = self.rect.x + dx + screen_scroll
		self.rect.y = self.rect.y + dy + screen_scroll

		#countdown timer
		self.timer = self.timer - 1
		if self.timer <= 0:
			self.kill()
			grenade_fx.play()
			explosion = explosion_class(self.rect.x, self.rect.y, 0.5)
			explosion_group.add(explosion)
			#do damage to anyone that is nearby
			if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and \
				abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
				player.health = player.health - 50
			for enemy in enemy_group:
				if abs(self.rect.centerx - enemy.rect.centerx) < TILE_SIZE * 2 and \
					abs(self.rect.centery - enemy.rect.centery) < TILE_SIZE * 2:
					enemy.health = enemy.health - 50



class explosion_class(pygame.sprite.Sprite):
	def __init__(self, x, y, scale):
		pygame.sprite.Sprite.__init__(self)
		self.images = []
		for num in range(1, 6):
			img = pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
			img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
			self.images.append(img)
		self.frame_index = 0
		self.image = self.images[self.frame_index]
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
		self.counter = 0


	def update(self):
		#SCroll
		self.rect.x = self.rect.x + screen_scroll
		EXPLOSION_SPEED = 4
		#update explosion amimation
		self.counter = self.counter + 1

		if self.counter >= EXPLOSION_SPEED:
			self.counter = 0
			self.frame_index = self.frame_index + 1
			#if the animation is complete then delete the explosion
			if self.frame_index >= len(self.images):
				self.kill()
			else:
				self.image = self.images[self.frame_index]

class screen_fade_class():
	def __init__(self, direction, color, speed):
		self.direction = direction
		self.color = color
		self.speed = speed
		self.fade_counter = 0

	def fade(self):
		fade_complete = False
		self.fade_counter = self.fade_counter + self.speed

		if self.direction == 1: # 1 = Next Level Fade
			pygame.draw.rect(screen, self.color, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
			pygame.draw.rect(screen, self.color, (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
			pygame.draw.rect(screen, self.color, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
			pygame.draw.rect(screen, self.color, (0, SCREEN_HEIGHT // 2 +self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))

		if self.direction == 2: # 2 = Death Fade
			pygame.draw.rect(screen, self.color, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))

		if self.fade_counter >= SCREEN_WIDTH:
			fade_complete = True

		return fade_complete

#Screen Fades
intro_fade = screen_fade_class(1, BLACK, 4)
death_fade = screen_fade_class(2, PINK, 4)

#Buttons
start_button = button.button_class(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_img, 1)
exit_button = button.button_class(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_img, 1)
restart_button = button.button_class(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_img, 2)

#Sprite Groups
#Basically arrays but for sprites
enemy_group = pygame.sprite.Group()
projectile_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()


#create empty tile list
world_data = []
for rows in range(ROWS):
	row = [-1] * COLS
	world_data.append(row)
#load in level data and create world
with open(f'level{level}_data.csv', newline='') as csvfile:
	reader = csv.reader(csvfile, delimiter=',')
	for row_num, row in enumerate(reader):
		for col_num, tile in enumerate(row):
			world_data[row_num][col_num] = int(tile)

world = game_world()
player, health_bar = world.process_data(world_data)



run = True
while run == True:

	clock.tick(FPS)
	#Main Menu
	if game_start == False:
		screen.fill(BG)

		if start_button.draw(screen):
			game_start = True
			game_intro = True

		elif exit_button.draw(screen):
			run = False

	#Game
	else:
		#update background
		draw_bg()
		#draw world map
		world.draw()
		#show player health
		health_bar.draw(player.health)
		#show ammo
		draw_text('AMMO: ', font, WHITE, 10, 35)
		for bullet_count in range(player.ammo):
			screen.blit(bullet_img, (90 + (bullet_count * 10), 40))
		#show grenades
		draw_text('GRENADES: ', font, WHITE, 10, 60)
		for grenade_count in range(player.grenades):
			screen.blit(grenade_img, (135 + (grenade_count * 15), 60))

		player.update()
		player.draw()

		for enemy in enemy_group:
			enemy.ai()
			enemy.update()
			enemy.draw()

		#update and draw groups
		projectile_group.update()
		grenade_group.update()
		explosion_group.update()
		item_box_group.update()
		decoration_group.update()
		water_group.update()
		exit_group.update()
		projectile_group.draw(screen)
		grenade_group.draw(screen)
		explosion_group.draw(screen)
		item_box_group.draw(screen)
		decoration_group.draw(screen)
		water_group.draw(screen)
		exit_group.draw(screen)

		#Intro
		if game_intro == True:
			if intro_fade.fade():
				game_intro = False
				intro_fade.fade_counter = 0

		#update player actions
		if player.alive:
			#shoot bullets
			if fire:
				player.fire()
			#throw grenades
			elif grenade and grenade_thrown == False and player.grenades > 0:
				grenade = grenade_class(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction),\
							player.rect.top, player.direction)
				grenade_group.add(grenade)
				#reduce grenades
				player.grenades = player.grenades -  1
				grenade_thrown = True
			if player.in_air:
				player.update_action(2)#2: jump
			elif moving_left or moving_right:
				player.update_action(1)#1: run
			else:
				player.update_action(0)#0: idle
			screen_scroll, level_complete = player.movement(moving_left, moving_right)
			bg_scroll = bg_scroll - screen_scroll

			#Check if body has collided with exit sign
			if level_complete:
				game_intro = True
				level = level + 1
				bg_scroll = 0
				world_data = reset_level()

				if level <= MAX_LEVELS:
					# load in level data and create world
					with open(f'level{level}_data.csv', newline='') as csvfile:
						reader = csv.reader(csvfile, delimiter=',')
						for row_num, row in enumerate(reader):
							for col_num, tile in enumerate(row):
								world_data[row_num][col_num] = int(tile)

					world = game_world()
					player, health_bar = world.process_data(world_data)

		#Restart function 
		else:
			screen_scroll = 0
			if death_fade.fade() == True:
				if restart_button.draw(screen):
					death_fade.fade_counter = 0
					game_intro = True
					bg_scroll = 0

					world_data = reset_level()
					# load in level data and create world
					with open(f'level{level}_data.csv', newline='') as csvfile:
						reader = csv.reader(csvfile, delimiter=',')
						for row_num, row in enumerate(reader):
							for col_num, tile in enumerate(row):
								world_data[row_num][col_num] = int(tile)

					world = game_world()
					player, health_bar = world.process_data(world_data)


	for event in pygame.event.get():
		#quit game
		if event.type == pygame.QUIT:
			run = False

		#On Key press
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_a:
				moving_left = True
			if event.key == pygame.K_d:
				moving_right = True
			if event.key == pygame.K_SPACE:
				fire = True
			if event.key == pygame.K_c:
				grenade = True
			if event.key == pygame.K_w and player.alive:
				player.jump = True
				jump_fx.play()

			#if event.key == pygame.K_ESCAPE:
			#	run = False


		#On Key release
		if event.type == pygame.KEYUP:
			if event.key == pygame.K_a:
				moving_left = False
			if event.key == pygame.K_d:
				moving_right = False
			if event.key == pygame.K_SPACE:
				fire = False
			if event.key == pygame.K_c:
				grenade = False
				grenade_thrown = False


	pygame.display.update()

pygame.quit()