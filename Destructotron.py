import rg
from random import choice

#Finds center of all destructotron bros
def center_location(player_id, game):
  loc_avg = (0,0)
  robot_count = 0
  for loc, bot in game['robots'].iteritems():
    if bot.player_id == player_id:
      loc_avg = map(sum,zip(loc_avg,loc))
      robot_count += 1
  return tuple(i / robot_count  for i in loc_avg)

def closest_enemy(player_id, location, game):
  closest_dist = 1000
  for loc, bot in game['robots'].iteritems():
    if bot.player_id != player_id and rg.wdist(location, loc) < closest_dist:
      closest = bot
      closest_dist = rg.wdist(location,loc)
  return closest

#Make the obstacle clause conditional on if they're likely to move
def location_score(player_id, location, game):
  loc_types = rg.loc_types(location)
  score = 4
  if 'invalid' not in loc_types and 'spawn' not in loc_types and 'obstacle' not in loc_types:
    for loc in rg.locs_around(location):
      surr_loc_types = rg.loc_types(loc)
      if loc in game.robots:
        if game.robots[loc].player_id != player_id:
          score -= 1
        else:
          score += 1
      if 'invalid' in surr_loc_types or 'spawn' in surr_loc_types:
        score -= 1
    return score
  else:
    return -1

class Robot:

  def act(self,game):
    avoiding = self.avoid(game)
    if self.location != avoiding:
      return ['move', avoiding]
    else:
      return ['guard']
  #Finds closes destructotron bro and returns his object and his distance as a tuple
  def closest_bro(self,game):
    closest_dist = 1000
    for loc, bot in game['robots'].iteritems():
      if self.location != loc and bot.player_id == self.player_id and rg.wdist(self.location, loc) < closest_dist:
        closest = bot
        closest_dist = rg.wdist(self.location,loc)
    return closest, closest_dist

  def should_suicide(self,game):
    surrounding_bots = 0
    around_us = rg.locs_around(self.location,filter_out=('invalid'))
    for location in around_us:
      if location in game['robots'] and game['robots'][location].player_id != self.player_id:
        surrounding_bots += 1
    if self.hp <= surrounding_bots * 9:
      return True
    return False

  def in_danger(self,game):
    if 'spawn' in rg.loc_types(self.location):
      return True
    for location in rg.locs_around(self.location):
      if location in game['robots']:
        return True
    return False

  def safest_loc(self,game):
    #Holds the distance of the space farthest away from any enemies
    furthest_enemy = 0
    current_closest = self.closest_enemy_dist(self.location,game) 
    for location in rg.locs_around(self.location,filter_out=('invalid','spawn','obstacle')):
      if self.closest_enemy_dist(location,game) > current_closest:
        return location
    return  self.location

  def closest_enemy_dist(self,location,game):
    closest_dist = 1000
    for loc, bot in game['robots'].iteritems():
      if bot.player_id != self.player_id and rg.wdist(location, loc) < closest_dist:
        closest_dist = rg.wdist(location,loc)
    return closest_dist

  def attack_direction(self,game):
    for location in rg.locs_around(self.location,filter_out=('invalid')):
      if location in game['robots'] and game['robots'][location].player_id != self.player_id:
        return location
    return self.nearest_enemy_direction(game)

  def nearest_enemy_direction(self,game):
    for loc, bot in game['robots'].iteritems():
      if bot.player_id != self.player_id and rg.wdist(self.location, loc) == 2:
        if 'invalid' not in rg.loc_types(rg.toward(self.location,loc)):
          return rg.toward(self.location,loc);
    return self.location

  def square_location(self,game):
    #Find the nearest three robots
    distance = {}
    bot_count = 0
    for loc, bot in game.robots.iteritems():
      if bot.player_id == self.player_id:
        bot_count += 1
        dist_to_bot = rg.wdist(self.location,bot.location) 
        if dist_to_bot not in distance:
          distance[dist_to_bot] = []
        distance[dist_to_bot].append(bot)
    bots = []
    index = 1
    while len(bots) < min(2,bot_count):
      if index in distance:
        bots += distance[index]
      index += 1
    return self.center(bots)

  def center(self, bots):
    loc_avg = (0,0)
    robot_count = 0
    for bot in bots:
      loc_avg = map(sum,zip(loc_avg,bot.location))
      robot_count += 1
    return tuple(i / robot_count  for i in loc_avg)

  def avoid(self, game):
    valid = {}
    if self.in_danger(game):
      for loc in rg.locs_around(self.location,filter_out=('invalid','spawn','obstacle')):
        if loc not in game.robots:
          valid[loc] = location_score(self.player_id,loc,game);
    if len(valid) > 0:
      return max(valid, key=valid.get)
    else:
      return self.location;

#Make a method that scores the quality of a space. Ex. +4 for no enemies, +3 for 1, etc, +
