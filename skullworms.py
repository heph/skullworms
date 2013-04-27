#!/usr/bin/env python

import random, pygame, sys, threading
from pygame.locals import *

NUM_WORMS = 50
FPS = 30
CELL_HEIGHT = 20
CELL_WIDTH = 25
BORDER = 5

CELLS_HIGH = 25
CELLS_WIDE = 40

GRID = []
for x in range(CELLS_WIDE):
  GRID.append([0] * CELLS_HIGH)

GRID_LOCK = threading.Lock()

COLORS = []
COLORS.append((40,40,40))   # dark gray
COLORS.append((20,95,137))  # dark teal
COLORS.append((36,191,255)) # medium teal
COLORS.append((87,255,255)) # light teal

WINDOWWIDTH = CELL_WIDTH * CELLS_WIDE
WINDOWHEIGHT = CELL_HEIGHT * CELLS_HIGH

UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

HEAD = 0
BUTT = -1

WORMS_RUNNING = True

class Worm(threading.Thread):
  def __init__(self, name='Worm', maxsize=None, speed=None):
    threading.Thread.__init__(self)

    self.name = name
    if maxsize is None:
      self.maxsize = random.randint(4,6)
    else:
      self.maxsize = maxsize

    if speed is None:
      self.speed = random.randint(20,80)
    else:
      self.speed = speed

    GRID_LOCK.acquire()

    while True:
      startx = random.randint(0, CELLS_WIDE - 1)
      starty = random.randint(0, CELLS_HIGH - 1)
      if GRID[startx][starty] < COLORS.__len__() and GRID[startx][starty] >= 0:
        break # found a non-full cell

    GRID[startx][starty] += 1

    GRID_LOCK.release()

    self.body = [{'x': startx, 'y': starty}]
    self.direction = random.choice((UP, DOWN, LEFT, RIGHT))

  def run(self):
    while True:
      if not WORMS_RUNNING:
        return

      if random.randint(0, 100) < 10:
        self.direction = random.choice((UP, DOWN, LEFT, RIGHT))

      GRID_LOCK.acquire()

      nextx, nexty = self.getNextPosition()

      if nextx in (-1, CELLS_WIDE) or nexty in (-1, CELLS_HIGH) or GRID[nextx][nexty] >= COLORS.__len__():
        self.direction = self.getNewDirection()

        if self.direction is None:
          self.body.reverse()
          self.direction = self.getNewDirection()

        if self.direction is not None:
          nextx, nexty = self.getNextPosition()

      if self.direction is not None:
        if GRID[nextx][nexty] < COLORS.__len__() and GRID[nextx][nexty] >= 0:
          GRID[nextx][nexty] += 1
        else:
          self.body.reverse()

        self.body.insert(0, {'x': nextx, 'y': nexty})

        if len(self.body) > self.maxsize:
          if GRID[self.body[BUTT]['x']][self.body[BUTT]['y']] >= 0:
            GRID[self.body[BUTT]['x']][self.body[BUTT]['y']] -= 1
          else:
            GRID[self.body[BUTT]['x']][self.body[BUTT]['y']] = None

          del self.body[BUTT]

      else:
        self.direction = random.choice((UP, DOWN, LEFT, RIGHT))

      GRID_LOCK.release()

      pygame.time.wait(self.speed)

  def getNextPosition(self):
    if self.direction == UP:
      nextx = self.body[HEAD]['x']
      nexty = self.body[HEAD]['y'] - 1
    elif self.direction == DOWN:
      nextx = self.body[HEAD]['x']
      nexty = self.body[HEAD]['y'] + 1
    elif self.direction == LEFT:
      nextx = self.body[HEAD]['x'] - 1
      nexty = self.body[HEAD]['y']
    elif self.direction == RIGHT:
      nextx = self.body[HEAD]['x'] + 1
      nexty = self.body[HEAD]['y']
    else:
      assert False, 'Bad value for self.direction: %s' % self.direction

    return nextx, nexty

  def getNewDirection(self):
    x = self.body[HEAD]['x'] # syntactic sugar, makes the code below more readable
    y = self.body[HEAD]['y']

    # Compile a list of possible directions the worm can move.
    newDirection = []
    if y - 1 not in (-1, CELLS_HIGH) and GRID[x][y - 1] < COLORS.__len__() and GRID[x][y - 1] >= 0:
      newDirection.append(UP)
    if y + 1 not in (-1, CELLS_HIGH) and GRID[x][y + 1] < COLORS.__len__() and GRID[x][y + 1] >= 0:
      newDirection.append(DOWN)
    if x - 1 not in (-1, CELLS_WIDE) and GRID[x - 1][y] < COLORS.__len__() and GRID[x - 1][y] >= 0:
      newDirection.append(LEFT)
    if x + 1 not in (-1, CELLS_WIDE) and GRID[x + 1][y] < COLORS.__len__() and GRID[x + 1][y] >= 0:
      newDirection.append(RIGHT)

    if newDirection == []:
      return None # None is returned when there are no possible ways for the worm to move

    return random.choice(newDirection)

def main():
  global FPSCLOCK, DISPLAYSURF

  squares = """
............222222222222222............
...........12222222222222221...........
...........12111111211111121...........
...........21    11211    12...........
...........21     121     12...........
...........2      222      2...........
...........21     222     12...........
...........22    12121    22...........
...........221   21 12.  122...........
...........1222222   2222221...........
...........1112221   1222111...........
...........1112221   1222111...........
...........1111221 1 1221111...........
............111222121222111............
.............1122222222211.............
..............12121212121..............
..............12222222221..............
..............11212121211..............
............... 1 1 1 1 ...............
.......................................
"""
  setGridSquares(squares)

  # Pygame window set up.
  pygame.init()
  FPSCLOCK = pygame.time.Clock()
  DISPLAYSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
  pygame.display.set_caption('colorworms')

  # Create the worm objects.
  worms = [] # a list that contains all the worm objects
  for i in range(NUM_WORMS):
    worms.append(Worm())
    worms[-1].start() # Start the worm code in its own thread.

  while True: # main game loop
    handleEvents()
    drawGrid()

    pygame.display.update()
    FPSCLOCK.tick(FPS)

def handleEvents():
  # The only event we need to handle in this program is when it terminates.
  global WORMS_RUNNING

  for event in pygame.event.get(): # event handling loop
    if (event.type == QUIT) or (event.type == KEYDOWN and event.key == K_ESCAPE):
      WORMS_RUNNING = False # Setting this to False tells the Worm threads to exit.
      pygame.quit()
      sys.exit()

def drawGrid():
  DISPLAYSURF.fill(COLORS[0])
  for x in range(0, WINDOWWIDTH, CELL_WIDTH):
    pygame.draw.line(DISPLAYSURF, (0,0,0), (x, 0), (x, WINDOWHEIGHT), BORDER)
  for y in range(0, WINDOWHEIGHT, CELL_HEIGHT):
    pygame.draw.line(DISPLAYSURF, (0,0,0), (0, y), (WINDOWWIDTH, y), BORDER)

  GRID_LOCK.acquire()

  for x in range(0, CELLS_WIDE):
    for y in range(0, CELLS_HIGH):
      if GRID[x][y] >= 0 and GRID[x][y] < COLORS.__len__():
        color = COLORS[GRID[x][y]]

        pygame.draw.rect(DISPLAYSURF, color, (x * CELL_WIDTH + (BORDER/2), y * CELL_HEIGHT + (BORDER/2), CELL_WIDTH - BORDER, CELL_HEIGHT - BORDER))

  GRID_LOCK.release()

def setGridSquares(squares):
  squares = squares.split('\n')
  if squares[0] == '':
    del squares[0]
  if squares[-1] == '':
    del squares[-1]

  GRID_LOCK.acquire()
  for y in range(min(len(squares), CELLS_HIGH)):
    for x in range(min(len(squares[y]), CELLS_WIDE)):
      if squares[y][x] == '.':
        pass
      elif squares[y][x] == ' ':
        GRID[x][y] = None
      else:
        GRID[x][y] = int(squares[y][x])
  GRID_LOCK.release()

if __name__ == '__main__':
  main()
