from pysc2.agents import base_agent
from pysc2.lib import actions
from pysc2.lib import features
from pysc2.lib import units
import numpy as np
import random
    
#Nom:         BALIT
#Prenom:      Habib
#N etudiant:  17801913

#Nom:         CHALI
#Prenom       Anis
#N etudiant: 15612337

# la strategie est de construire 4 supply depots pour augmenter la population (nombre de marines)
# parce que les marines de la race terran sont faibles en petit nombre, puis construire 3 barracks
# pour pouvoir produire le maximum de marines rapidement, sachant que toutes ses construction sont 
# entre l entree de la base de la base et le command center pour retarder sa destruction.
# deuxieme phase c est l'envoi de patrouil a la fois pour attaquer et revenir pour securiser
# le chemin de la base vers l ennemie et deffendre aussi la base et permettre la destruction
# de toute reconstruction de la base adverse. 
# concernant son efficacite elle gagne tout le temps en difficultie very_easy
# gagne tout le temps en easy
# gagne 7 fois sur 10 en medium
# gagne 1 fois sur 10 en medium hard
# perd pour tout le reste

# Functions
_PLAYER_RELATIVE = features.SCREEN_FEATURES.player_relative.index
_SELECT_IDLE_WORKER = actions.FUNCTIONS.select_idle_worker.id
_HARVEST_GATHER_SCREEN = actions.FUNCTIONS.Harvest_Gather_screen.id
# id de l action patrouille 
_PATROL_MINIMAP = 334
_SELECT_POINT = actions.FUNCTIONS.select_point.id
_TRAIN_MARINE_QUICK = actions.FUNCTIONS.Train_Marine_quick.id
_BUILD_SUPPLYDEPOT_SCREEN = actions.FUNCTIONS.Build_SupplyDepot_screen.id
_BUILD_BARRACKS_SCREEN = actions.FUNCTIONS.Build_Barracks_screen.id

# Features
_UNIT_TYPE = features.SCREEN_FEATURES.unit_type.index

# Parameters
_NOT_QUEUED = [0]
_PLAYER_SELF = 1

# python3 -m pysc2.bin.agent --map Simple64 --agent pysc2_terran.SimpleAgent --agent_race terran
class SimpleAgent(base_agent.BaseAgent): 
  prev_total_value_structures = 400
  #variable pour controller les etats de construction
  state = 0
  #variable pour controller les etats de jeu entre construction et envoi des marines
  state_one = 0
  #index des barrack a dessiner
  index_b = 0
  #index des supply depots a dessiner 
  index_sd = 0
  #les barrack ou cas ou la base est en haut a gauche
  barracks_top = [[75,35],[75,45],[75,55]]
  #les barrack ou cas ou la base est en bas a droite
  barracks_buttom = [[9,25],[9,36],[9,46]]
  #les supply depots ou cas ou la base est en haut a gauche
  supply_depots_top = [[65,30],[65,40],[65,50],[65,60]]
  #les supply depots ou cas ou la base est en bas a droite
  supply_depots_buttom = [[20,23],[20,33],[20,43],[20,53]]
  #le point vers lequelle patrouiller quand la base est en bas 
  patrol_point_top = [10,10]
  #le point vers lequelle patrouiller quand la base est en haut
  patrol_point_buttom = [60, 55]
  #variable de controle pour determiner la base si c est en bas ou en haut
  top_pos = None
  #variable de controle pour savoir si tout est bien construit
  structures_ok = None
  #variable pour organiser la selection et le depart des marines 
  state_attack = 0

  def reset(self):
    super(SimpleAgent,self).reset()
    self.prev_total_value_structures = 400
    self.state = 0
    self.state_one = 0
    self.index_b = 0
    self.index_sd = 0
    self.barracks_top = [[75,35],[75,45],[75,55]]
    self.barracks_buttom = [[9,25],[9,36],[9,46]]
    self.supply_depots_top = [[65,30],[65,40],[65,50],[65,60]]
    self.supply_depots_buttom = [[20,23],[20,33],[20,43],[20,53]]
    self.patrol_point_top = [10,10]
    self.patrol_point_buttom = [60, 55]
    self.top_pos = None
    self.barrack_selected = False
    self.structures_ok = None
    self.state_attack = 0

  # la fonction qui assure l envoi des marines en patrouille
  def attack_with_patrol(self, obs):
    if self.state_attack == 0:
      unit_type = obs.observation["feature_screen"][_UNIT_TYPE]
      marine_y, marine_x = (unit_type == units.Terran.Marine).nonzero() 
      if not marine_x.any():
        return actions.FUNCTIONS.no_op()
      target = (marine_x[0], marine_y[0])
      self.state_attack = 1
      self.state = 2
      return actions.FUNCTIONS.select_army("select", target)
    if self.state_attack == 1:
      if _PATROL_MINIMAP in obs.observation["available_actions"]:
        target = self.patrol_point_top
        if self.top_pos == True:
          target = self.patrol_point_buttom
        self.state = 0
        self.state_attack = 0
        return actions.FunctionCall(_PATROL_MINIMAP, [_NOT_QUEUED, target])
      return actions.FUNCTIONS.no_op()
    return actions.FUNCTIONS.no_op()

  def train_MARINES(self, obs):
    if self.state == 0:
      self.state_attack = 0
      target = [0,0]
      if self.top_pos == False:
        target = self.barracks_buttom[0]
      if self.top_pos == True:
        target = self.barracks_top[0]
      self.state = 1
      return actions.FUNCTIONS.select_point("select_all_type", target)
    if self.state == 1:
      unit_type = obs.observation["feature_screen"][_UNIT_TYPE]
      marine_y, marine_x = (unit_type == units.Terran.Marine).nonzero() 
      # l equivalent de plus de 20 marines
      if len(marine_y) > 180:
        self.state = 2 
      if _TRAIN_MARINE_QUICK in obs.observation["available_actions"]:
        return actions.FUNCTIONS.Train_Marine_quick("now")
      return actions.FUNCTIONS.no_op()
    if self.state == 2:
      return self.attack_with_patrol(obs)
    return actions.FUNCTIONS.no_op()


  def select_SCV(self,obs):
    if _SELECT_IDLE_WORKER in obs.observation["available_actions"]:
      return actions.FUNCTIONS.select_idle_worker("select")
    unit_type = obs.observation["feature_screen"][_UNIT_TYPE]
    scv_y, scv_x = (unit_type == units.Terran.SCV).nonzero() 
    if not scv_x.any():
      return actions.FUNCTIONS.no_op()  
    target = [scv_x[0], scv_y[0]]
    if _SELECT_POINT in obs.observation["available_actions"]:
      return actions.FunctionCall(_SELECT_POINT, [_NOT_QUEUED, target])
    return actions.FUNCTIONS.no_op()

  # controle les coordonnees en fontion de type et de l emplacement de la base dans la minimap
  def generate_coord(self,obs, type_build):
    target = [0,0]
    if (self.top_pos == True):
      if (type_build == 0):
        target = self.supply_depots_top[self.index_sd]
        self.index_sd = self.index_sd + 1
      else:
        target = self.barracks_top[self.index_b]
        self.index_b = self.index_b + 1
    else:
      if (type_build == 0):
        target = self.supply_depots_buttom[self.index_sd]
        self.index_sd = self.index_sd + 1      
      else:
        target = self.barracks_buttom[self.index_b]
        self.index_b = self.index_b + 1
    return target


  # fonction de constructions des structures
  def build_supply_depot_and_barracks(self,obs):
    total_value_structures = obs.observation["score_cumulative"]["total_value_structures"]
    # retourne no_op() tant que la structures en cours de construction n est pas termine
    if self.prev_total_value_structures != total_value_structures:
      return actions.FUNCTIONS.no_op()

    if self.state == 0:
      self.state = 1 
      return self.select_SCV(obs)  
    
    if self.state == 1:
      # inferieur a 800 pour construire les quatre supply depots (un supply = 100) 
      if _BUILD_SUPPLYDEPOT_SCREEN in obs.observation["available_actions"] and self.prev_total_value_structures < 800:
        target = self.generate_coord(obs, 0)
        self.prev_total_value_structures = total_value_structures + 100
        if self.prev_total_value_structures == 800:
          self.state = 2
        return actions.FunctionCall(_BUILD_SUPPLYDEPOT_SCREEN, [_NOT_QUEUED, target])
    if self.state == 2:
      if _BUILD_BARRACKS_SCREEN in obs.observation["available_actions"]:
        target = self.generate_coord(obs,1)
        self.prev_total_value_structures = total_value_structures + 150
        return actions.FunctionCall(_BUILD_BARRACKS_SCREEN, [_NOT_QUEUED, target])
      return actions.FUNCTIONS.no_op()


  def step(self, obs):
    super(SimpleAgent, self).step(obs)
    total_value_structures = obs.observation["score_cumulative"]["total_value_structures"]
    collected_minerals = obs.observation["score_cumulative"]["collected_minerals"]
    # determiner la position de la base
    if (self.top_pos == None):
      player_y, player_x = (obs.observation["feature_minimap"][_PLAYER_RELATIVE] == _PLAYER_SELF).nonzero()
      self.top_pos = player_y.mean() <= 31
    # 1250 correspond au 3 barracks + 4 supply depots
    if (total_value_structures == 1250) and (self.structures_ok == None):
      self.state = 0
      self.state_one = 1
      self.structures_ok = True
      return actions.FUNCTIONS.no_op()
    # ne rien faire tant que ya pas assez de mineraux    
    if collected_minerals < 50:
      return actions.FUNCTIONS.no_op()
    if self.state_one == 0:
      return self.build_supply_depot_and_barracks(obs)
    if self.state_one == 1:
      return self.train_MARINES(obs)
    return actions.FUNCTIONS.no_op()
      
