from random import randint, random
import pygame
import os
import math
import sys
import neat
import argparse

SCREEN_WIDTH = 1244
SCREEN_HEIGHT = 1016
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

MAX_SPEED = 10
MAX_LIFETIME = 1000
MAX_SENSOR_LENGTH = 200

TRACK = pygame.image.load(os.path.join("Assets", "grand_prix.png"))

class Car(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        random_car_colour = self.get_random_car_image_filepath()

        self.original_image = pygame.image.load(os.path.join("Assets", random_car_colour))
        self.image = self.original_image
        self.rect = self.image.get_rect(center=(490, 820))
        self.vel_vector = pygame.math.Vector2(0.8, 0)
        self.angle = 0
        self.rotation_vel = 5
        self.direction = 0
        self.alive = True
        self.radars = []
        self.laps = 0
        self.passed_finish_line = False
        self.passed_halfway_point = False
        self.current_speed = 0
        self.acceleration = 0
        self.lifetime = MAX_LIFETIME

    # TODO: Refactor
    def get_random_car_image_filepath(self):
        random_int = randint(0, 6)
        if random_int == 0:
            return "car.png"
        elif random_int == 1:
            return "yellow_car.png"
        elif random_int == 2:
            return "blue_car.png"
        elif random_int == 3:
            return "green_car.png"
        elif random_int == 4:
            return "pink_car.png"
        elif random_int == 5:
            return "purple_car.png"
        
        return "car.png"

    def update(self):
        self.radars.clear()
        self.drive()
        self.rotate()
        for radar_angle in (-60, -30, 0, 30, 60):
            self.radar(radar_angle)
        self.collision()
        self.data()
        self.check_race_position()
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def drive(self):
        self.current_speed += self.acceleration

        # Max Speed
        if self.current_speed > MAX_SPEED:
            self.current_speed = MAX_SPEED
        elif self.current_speed < -MAX_SPEED:
            self.current_speed = -MAX_SPEED

        self.rect.center += self.vel_vector * self.current_speed # Default Speed: 6 units

    def adjust_pos_against_bounds(self, coordinates):
        if coordinates[0] < 0:
            coordinates[0] = 0
        elif coordinates[0] >= SCREEN_WIDTH:
            coordinates[0] = SCREEN_WIDTH - 1

        if coordinates[1] < 0:
            coordinates[1] = 0
        elif coordinates[1] >= SCREEN_HEIGHT:
            coordinates[1] = SCREEN_HEIGHT - 1

        return coordinates

    def collision(self):
        length = 40
        collision_point_right_front = self.adjust_pos_against_bounds([int(self.rect.center[0] + math.cos(math.radians(self.angle + 18)) * length),
                                 int(self.rect.center[1] - math.sin(math.radians(self.angle + 18)) * length)])
        collision_point_left_front = self.adjust_pos_against_bounds([int(self.rect.center[0] + math.cos(math.radians(self.angle - 18)) * length),
                                int(self.rect.center[1] - math.sin(math.radians(self.angle - 18)) * length)])
        collision_point_right_side = self.adjust_pos_against_bounds([int(self.rect.center[0] + math.cos(math.radians(self.angle + 90)) * 20),
                                     int(self.rect.center[1] - math.sin(math.radians(self.angle + 90)) * 20)])

        collision_point_left_side = self.adjust_pos_against_bounds([int(self.rect.center[0] + math.cos(math.radians(self.angle - 90)) * 20),
                                     int(self.rect.center[1] - math.sin(math.radians(self.angle - 90)) * 20)])

        collision_point_right_rear = self.adjust_pos_against_bounds([int(self.rect.center[0] + math.cos(math.radians(self.angle - 160)) * length),
                                     int(self.rect.center[1] - math.sin(math.radians(self.angle - 160)) * length)])

        collision_point_left_rear = self.adjust_pos_against_bounds([int(self.rect.center[0] + math.cos(math.radians(self.angle + 160)) * length),
                                     int(self.rect.center[1] - math.sin(math.radians(self.angle + 160)) * length)])

        # Die on Collision
        if SCREEN.get_at(collision_point_right_front) == pygame.Color(2, 105, 31, 255) \
                or SCREEN.get_at(collision_point_left_front) == pygame.Color(2, 105, 31, 255) \
                    or SCREEN.get_at(collision_point_right_side) == pygame.Color(2, 105, 31, 255) \
                        or SCREEN.get_at(collision_point_left_side) == pygame.Color(2, 105, 31, 255) \
                            or SCREEN.get_at(collision_point_right_rear) == pygame.Color(2, 105, 31, 255) \
                                or SCREEN.get_at(collision_point_left_rear) == pygame.Color(2, 105, 31, 255):
            self.alive = False

        # Draw Collision Points
        pygame.draw.circle(SCREEN, (0, 255, 255, 0), collision_point_right_front, 4)
        pygame.draw.circle(SCREEN, (0, 255, 255, 0), collision_point_left_front, 4)

        pygame.draw.circle(SCREEN, (0, 255, 255, 0), collision_point_right_side, 4)
        pygame.draw.circle(SCREEN, (0, 255, 255, 0), collision_point_left_side, 4)

        pygame.draw.circle(SCREEN, (0, 255, 255, 0), collision_point_right_rear, 4)
        pygame.draw.circle(SCREEN, (0, 255, 255, 0), collision_point_left_rear, 4)

    def rotate(self):
        if self.direction == 1:
            self.angle -= self.rotation_vel
            self.vel_vector.rotate_ip(self.rotation_vel)
        if self.direction == -1:
            self.angle += self.rotation_vel
            self.vel_vector.rotate_ip(-self.rotation_vel)

        self.image = pygame.transform.rotozoom(self.original_image, self.angle, 0.1)
        self.rect = self.image.get_rect(center=self.rect.center)

    def radar(self, radar_angle):
        length = 0
        x = int(self.rect.center[0])
        y = int(self.rect.center[1])
        
        # TODO: Allow for longer sensors/more sensors
        while not SCREEN.get_at((x, y)) == pygame.Color(2, 105, 31, 255) and length < MAX_SENSOR_LENGTH:
            length += 1
            x = int(self.rect.center[0] + math.cos(math.radians(self.angle + radar_angle)) * length)
            y = int(self.rect.center[1] - math.sin(math.radians(self.angle + radar_angle)) * length)

            if x >= SCREEN_WIDTH:
                x = SCREEN_WIDTH - 1
            elif x < 0:
                x = 0

            if y >= SCREEN_HEIGHT:
                y = SCREEN_HEIGHT - 1
            elif y < 0:
                y = 0

        # Draw Radar
        pygame.draw.line(SCREEN, (255, 255, 255, 255), self.rect.center, (x, y), 1)
        pygame.draw.circle(SCREEN, (0, 255, 0, 0), (x, y), 3)

        dist = int(math.sqrt(math.pow(self.rect.center[0] - x, 2)
                             + math.pow(self.rect.center[1] - y, 2)))

        self.radars.append([radar_angle, dist])

    def data(self):
        input = [0, 0, 0, 0, 0]
        for i, radar in enumerate(self.radars):
            input[i] = int(radar[1])
        return input

    def check_race_position(self):
        if self.passed_halfway_point == False and (int(self.rect.center[0]) < 490 and int(self.rect.center[1]) < 300):
            self.passed_halfway_point = True
        elif self.passed_halfway_point == True and (int(self.rect.center[0]) > 490 and int(self.rect.center[1]) > 300):
            self.passed_halfway_point = False
            self.passed_finish_line = True

def eval_genomes(genomes, config):
    global car, net

    # TODO: Find way of getting best genome.
    # best_genome_id = -1
    # best_fitness = 0
    # for genome_id, genome in genomes:
    #     if genome.fitness > best_fitness:
    #         best_fitness = genome.fitness
    #         best_genome_id = genome_id

    # if best_genome_id == -1:
    #     return

    random_index = randint(0, len(genomes))

    car = pygame.sprite.GroupSingle(Car())
    net = neat.nn.FeedForwardNetwork.create(genomes[random_index][1], config)

    run = True
    while car.sprite.alive:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        SCREEN.blit(TRACK, (0, 0))

        if car.sprite.passed_finish_line == True:
            car.sprite.laps += 1
            car.sprite.passed_finish_line = False
        if car.sprite.laps >= 2:
            car.sprite.alive = False
            
        output = net.activate(car.sprite.data())
        if output[0] > 0.7:
            car.sprite.direction = 1
        if output[1] > 0.7:
            car.sprite.direction = -1
        if output[0] <= 0.7 and output[1] <= 0.7:
            car.sprite.direction = 0
        car.sprite.acceleration = output[0] + output[1]

        # Update
        car.draw(SCREEN)
        car.update()
        pygame.display.update()

# Setup NEAT Neural Network
def run(config_path, args):
    global pop
    #models = open(args.model_list)
    models = [
        #"models/neat-checkpoint-84",
        #"models/wiggly_checkpoint-119",
        "models/hundred_genomes-855"
    ]

    for model in models:
        pop = neat.Checkpointer.restore_checkpoint(model)
        print(f"Model Loaded: {model}")
        #pop.add_reporter(neat.StdOutReporter(True))
        #stats = neat.StatisticsReporter()
        #pop.add_reporter(stats)
        pop.run(eval_genomes, 1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model_list', type=str, default="model.txt",
        help="A .txt file with all models to be used in this demo.")

    args = parser.parse_args(sys.argv[1:])

    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config.txt')
    run(config_path, args)

if __name__ == '__main__':
    main()
