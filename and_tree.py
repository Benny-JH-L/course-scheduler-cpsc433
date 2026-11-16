import heapq as hq
import input_classes
from input_classes import InputModel
from schedule import Schedule
import os, time
import copy
import re

DEBUG = os.environ.get("DEBUG")
DEBUG and print(f"[and_tree.py] DEBUG = {DEBUG}") # note it doesn't matter the value, if it exists it is `True`

# use these to index into the weight and penalty arrays
WEIGHT_MINFILLED_INDEX = 0
WEIGHT_PREFERENCE_INDEX = 1
WEIGHT_PAIR_INDEX = 2
WEIGHT_SECTION_DIFF_INDEX = 3 
PEN_LECTURE_MIN_INDEX = 0
PEN_TUTORIAL_MIN_INDEX = 1 
PEN_NOT_PAIRED_INDEX = 2 
PEN_SECTION_INDEX = 3 

SAVE_SCHEDULE_FOLDER = "OUTPUT_SCHEDULE"
SAVE_SCHEDULE_NAME = "best_schedule"


def _get_slot_time_ranges(slot) -> list[tuple[str, int, int]]:
  parts = slot.start_time.split(':')
  start_min = int(parts[0]) * 60 + int(parts[1])
  ranges = []
  
  if isinstance(slot, input_classes.LectureSlot):
    duration = 60
    if slot.day == "MO":
      for day in ["MO", "WE", "FR"]:
        ranges.append((day, start_min, start_min + duration))
    elif slot.day == "TU":
      for day in ["TU", "TH"]:
        ranges.append((day, start_min, start_min + duration))
  else:
    if slot.day == "FR": duration = 120
    else: duration = 60
    ranges.append((slot.day, start_min, start_min + duration))
  
  return ranges


def _slots_overlap(slot1, slot2) -> bool:
  ranges1 = _get_slot_time_ranges(slot1)
  ranges2 = _get_slot_time_ranges(slot2)
  
  for day1, start1, end1 in ranges1:
    for day2, start2, end2 in ranges2:
      if day1 == day2:
        if start1 < end2 and start2 < end1:
          return True
  
  return False


'''
example of how to envoke debugging on;
Windows: $Env:DEBUG = "1"; python main.py testinputs/input.txt 1 0 1 0 10 10 10 10 ; Remove-Item Env:DEBUG | remove the environment varable: `Remove-Item Env:DEBUG`
Linux: env "DEBUG=1"; python main.py testinputs/input.txt 1 0 1 0 10 10 10 10  | `env` -> temporary 
if you don't want debugging then just run as normal.
Note: use proper weights :)

Measure-Command{$Env:DEBUG = "1"; python main.py testinputs/input.txt 1 0 1 0 10 10 10 10 ; Remove-Item Env:DEBUG} | time it
Measure-Command{python main.py testinputs/input.txt 1 0 1 0 10 10 10 10 }  
Measure-Command{python main.py testinputs/input2.txt 1 0 1 0 10 10 10 10 }  
$Env:DEBUG = "1"; python main.py testinputs/input2.txt 1 0 1 0 10 10 10 10 ; Remove-Item Env:DEBUG

$Env:DEBUG = "1"; python main.py testinputs/input_5xx_3.txt 1 1 1 1 1 1 1 1 ; Remove-Item Env:DEBUG
$Env:DEBUG = "1"; python main.py testinputs/input_pref.txt 1 1 1 1 1 1 1 1 ; Remove-Item Env:DEBUG
$Env:DEBUG = "1"; python main.py testinputs/input_minfilled.txt 1 0 0 0 10 10 0 0 ; Remove-Item Env:DEBUG
python main.py testinputs/input_minfilled.txt 1 0 0 0 10 10 0 0 
python main.py testinputs/input_sectiondiff.txt 1 0 0 0 10 10 0 0 


# large inputs
python main.py largeinputs/largeinput1.txt 1 1 1 1 1 1 1 1 
python main.py largeinputs/largeinput2.txt 1 1 1 1 1 1 1 1 

python main.py testinputs/input.txt 1 0 1 0 10 10 10 10

# hudson tests
python main.py hudson_tests/starter.txt 1 1 1 1 1 1 1 1
python main.py hudson_tests/HC1-LS.txt 1 1 1 1 1 1 1 1 
python main.py hudson_tests/HC2-TS.txt 1 1 1 1 1 1 1 1
python main.py hudson_tests/HC3-AL.txt 1 1 1 1 1 1 1 1 
python main.py hudson_tests/HC4-LT1.txt 1 1 1 1 1 1 1 1 
python main.py hudson_tests/HC5-LT2.txt 1 1 1 1 1 1 1 1  
python main.py hudson_tests/HC6-NC1.txt 1 1 1 1 1 1 1 1 
python main.py hudson_tests/HC7-NC2.txt 1 1 1 1 1 1 1 1 
python main.py hudson_tests/HC8-NCA.txt 1 1 1 1 1 1 1 1 
python main.py hudson_tests/HC9-PA1.txt 1 1 1 1 1 1 1 1 
python main.py hudson_tests/HC10-PA2.txt 1 1 1 1 1 1 1 1
python main.py hudson_tests/HC11-EV1.txt 1 1 1 1 1 1 1 1 
python main.py hudson_tests/HC12-5XX.txt 1 1 1 1 1 1 1 1 
python main.py hudson_tests/HC13-MEET.txt 1 1 1 1 1 1 1 1 
python main.py hudson_tests/HC14-SPTU.txt 1 1 1 1 1 1 1 1
python main.py hudson_tests/HC15-UW.txt 1 1 1 1 1 1 1 1
python main.py hudson_tests/HC16-NCUW.txt 1 1 1 1 1 1 1 1
python main.py hudson_tests/SC1-MINF.txt 1 1 1 1 1 1 1 1
python main.py hudson_tests/SC2-SECD.txt 1 1 1 1 1 1 1 1
python main.py hudson_tests/SC3-PREF.txt 1 1 1 1 1 1 1 1
python main.py hudson_tests/SC4-PAIR.txt 1 1 1 1 1 1 1 1

$Env:DEBUG = "1"; python main.py hudson_tests/HC9-PA1.txt 1 1 1 1 1 1 1 1 ; Remove-Item Env:DEBUG
$Env:DEBUG = "1"; python main.py hudson_tests/HC14-SPTU2.txt 1 1 1 1 1 1 1 1 ; Remove-Item Env:DEBUG
$Env:DEBUG = "1"; python main.py hudson_tests/SC2-SECD.txt 1 1 1 1 1 1 1 1 ; Remove-Item Env:DEBUG


'''

class AndTree():
  
  def __init__(self, model:InputModel, weightings: list[float], penalty_values: list[float]):
    self._static_model = model    # used later for hard constraint checks (need this for `not_compat`, `unwanted`, etc.)
    self.priority_queue = []  # this is supposed to be a heap, we use heapq methods on this
    self.leaves_list = []     # list to contain our leaves generated from `div()`
    self.best_schedule = None # set the best schedule found
    self.weights = weightings
    self.penalties = penalty_values
    self._valid_preferences: list[(str, str, str, float)] = []    # (class id, day, time, preference value)
    
    self.unique_schedules_cache: dict[frozenset, int] = {}          # key: string of the schedule, val: number of times this schedule has been found
    self.hard_constraint_check_cache: dict[frozenset, bool] = {}    # key: string of the schedule, val: result of calling `_hard_constraint_check()`
      # saves the value (bool) of the hard constraint check for a given schedule
    # self.preference_eval_cache: dict[str, float] = {}         # key: string of the schedule, val: its preference value computed from `_eval_pref()`
      # ^ this cache is prolly not needed due to the fact that div() only outputs unique schedules (no repeats), so the eval() is only calculated once ever
    
    preprocessed_schedule = Schedule(model)     # create a starting schedule (+ do preprocessing)
    self.leaves_list.append(preprocessed_schedule)  
    
    # get valid preferences (must happen after Schedule creation)
    for p in model.prefs:
      pref_key = f"lec slot {p.slot_day}, {p.slot_time}"
      # is_lec = pref_key in Schedule._static_map_time_slots_to_int
      is_lec = pref_key in preprocessed_schedule.lec_slots_dict and p.class_id in preprocessed_schedule._static_lec_ids
      
      # check is it a tut
      if (not is_lec):
        pref_key = f"tut slot {p.slot_day}, {p.slot_time}"
        # is_tut = pref_key in Schedule._static_map_time_slots_to_int
        is_tut = pref_key in preprocessed_schedule.tut_slots_dict and p.class_id in preprocessed_schedule._static_tut_ids
        
        if (not is_tut):
          continue        # not a valid preference
      
      self._valid_preferences.append((p.class_id, p.slot_day, p.slot_time, p.preference_value))
    # print(self._valid_preferences)
    # print(preprocessed_schedule.lec_slots_dict)
    # print(preprocessed_schedule.tut_slots_dict)
    
    # print(f"len of weights: {len(weightings)}") # should always be size 4
    
    # testing ONLY--
    # schedule = Schedule(model)
    # schedule2 = copy.deepcopy(schedule)
    # schedule.assign_lec(model.lecs[1], model.lec_slots[1])
    # schedule2.assign_tut(model.tuts[0], model.tut_slots[2])
    # schedule2.assign_lec(model.lecs[2], model.lec_slots[2])
    # schedule2.assign_lec(model.lecs[1], model.lec_slots[1])
    # schedule.eval_value += 10
    # schedule2.eval_value += 100
    # hq.heappush(self.priority_queue, (schedule.eval_value, schedule))
    # hq.heappush(self.priority_queue, (schedule2.eval_value, schedule2))
    
    # while self.priority_queue:
    #   eval, sch = hq.heappop(self.priority_queue)
    #   print(f"eval: `{eval}`") # | sch:\n{sch.get_schedule()}")
    #   dict = sch.get_schedule() # will do the printing for us
    
    # testing ONLY
    # self.schedule.assign_lec(model.lecs[2], model.lec_slots[2])
    # self.schedule.get_schedule()
    
    self.counter = 0
    self.full_schedules_found = 0
    self.largest_pq_size = 0
    self.largest_leaf_size = 0    # will be the first div() (ie div() on root)
    
    '''
    [inside __init()__]
    make list to contain all the leaves -> preprocess -> then add root (ie preprocessed schedule) to list of leaves
    (then we can run the `search()` in calling code)
    
    [inside search(), iteration 1 (ie with root)]
    1. f-leaf() goes through our list of leaves, and sees only `root`. It then puts it into the heap with `_eval(`root`)` `priority`.
    2. f-trans() pops from the heap and get's `root` (a `schedule`). 
        -Checks if this is a valid, no hard constrain violations, (and complete) schedule; and sets the global `best_schedule` if the e_val score is less than it. Then it returns (goes to `div()` afterwards).
        -if the schedule is invalid (note: we will try to make `div` not output invalid schedules to help with runtime and memory) then we 
        keep popping from the heap until it's empty or until we get an incomplete (but still valid) schedule.
    3. div(`root`), creates the available transitions from `root` (ie possible schedules) and puts them into the list of leaves
        -if it recieves a complete & valid `schedule` or `None` then it creates no leaves.
    repeat 1-3 until heap is empty (heap check is empty is done after `div()`)
    
    if the heap and the list of leaves is empty we terminate search!
    '''
    
  def search(self) -> Schedule:
    DEBUG and print(f"---search()---")
        
    while (True):
      pq_size_before_fleaf = len(self.priority_queue)
      self._f_leaf()
      DEBUG and print(f"size of PQ (before f_leaf): {pq_size_before_fleaf}")
      DEBUG and print(f"size of PQ (after f_leaf): {len(self.priority_queue)}")      

      selected_leaf = self._f_trans()   # the selected schedule
      self._div(selected_leaf)          # generate leaves from selected schedule
      # self._div_OLD(selected_leaf)
      
      # if (DEBUG):
      #   print(f"size of PQ (after div): {len(self.priority_queue)}")
      #   print(f"size of leaves_list (after div): {len(self.leaves_list)}")
        
      if (len(self.priority_queue) == 0 and len(self.leaves_list) == 0):   # stop the search when there are no more leaves to check
        # print(f"PQ and leaves[] is empty, stopping search...")
        
        # # comment out these print statements when you run :)
        # print(f"unique schedules found!: {len(self.unique_schedules_dict)}")
        # for key, item in self.unique_schedules_dict.items():
        #   print(f"'{key}': {item} times")
        # print("---")
        # print(f"largest pq size ever was: {self.largest_pq_size}")
        # print(f"largest leaves size ever was: {self.largest_leaf_size}")
        return self.best_schedule           # return the best schedule we've found

      # debug
      # print(f"counter = {self.counter}")
      # if (DEBUG):
      #   print(f"---printing all leaves")
      #   for x in self.leaves_list:
      #     print(f"schedule: {x.to_string()}")
      #   print(f"---")

      #   print(f"--- (before adding above leaves) PQ:")
      #   for x in self.priority_queue:
      #     print(f"PQ schedule: {x.to_string()}")
      #   print(f"---PQ size {len(self.priority_queue)}")
      
      self.counter += 1
      
    return self.best_schedule
  
  def _f_leaf(self):
    '''
    Goes through the list of leaves and adds them to the heap with `priority` generated from _eval(`element of list`).
    Clears the list of leaves `leaves_list` afterwards.
    '''
    DEBUG and print(f"---f_leaf()---")
    
    for schedule in self.leaves_list:
      eval_val = self._eval(schedule)
      # hq.heappush(self.priority_queue, (eval_val, schedule))    # push the `schedule` into the heap with its eval-value
      hq.heappush(self.priority_queue, schedule)    # push the `schedule` into the heap with its eval-value (built-into the schedule's comparison function)

    # debug
    if (len(self.priority_queue) > self.largest_pq_size):
      self.largest_pq_size = len(self.priority_queue)
    if (len(self.leaves_list) > self.largest_leaf_size):
      self.largest_leaf_size = len(self.leaves_list)
      
    self.leaves_list = []   # clear the list after putting them into the priority queue
    
  
  def _f_trans(self) -> Schedule:
    '''
    keeps poping a `Schedule` from the priority queue until it:
    1. selects one that does not violate hard constraints, and returns it, or
    2. until the priority queue is empty.
    
    Return `None` if the `Schedule` is complete (filled), or when the priority queue is empty,
    otherwise it returns an incomplete and valid `Schedule`.
    '''
    
    DEBUG and print(f"---f_trans()---")
    while (len(self.priority_queue) > 0):   # go through heap
      schedule:Schedule = None
      # eval_val, schedule = hq.heappop(self.priority_queue)              # get selected leaf
      schedule = hq.heappop(self.priority_queue)              # get selected leaf
      DEBUG and print(f"   schedule popped: '{schedule.to_string()}'")
      violated_hard_constraint = self._hard_constraint_check(schedule)  
      
      if (violated_hard_constraint):  # get another leaf that does not violate hard constraints
        DEBUG and print(f"violated hc, continue")
        continue
      
      '''
      check if this schedule has a eval-score > the eval-score of the best schedule found.
      if this schedule has a larger eval-score, then there is no way for this schedule to be better than the one we've found currently.
      Skip this schedule and find another.
      
      bc of minfilled penalizing not fully filled schedules, it will result in not filled schedules to be axed early when we find a best-so-far schedule.
      so a half-filled schedule will be axed early when we've found a best-so-far schedule, even though that half-filled schedule had the potential to be even better
      when more slots were filled.
      
      (this causes hill-climbing)
      '''
      # if (self.best_schedule is not None):
      #   if (schedule.eval_value > self.best_schedule.eval_value): # note a full schedule can enter here and the counter for full_schedules_found wont be incremented
      #     # print(f"schedule cannot beat the best one we've found so far, continuing! schedule: {schedule.to_string()} | eval-val: {schedule.eval_value}")
      #     continue  
      
      if (not violated_hard_constraint):
        
        if (schedule.is_filled()):    # check if this is a completed (filled) schedule
          # set best schedule found
          if (self.best_schedule is None):
            self.best_schedule = schedule
            self.save_schedule_to_file(self.best_schedule)
          elif (schedule.eval_value < self.best_schedule.eval_value):   # can make it '<'
            self.best_schedule = schedule
            self.save_schedule_to_file(self.best_schedule)
          
          # print(f"   best schedule found so far: {self.best_schedule.to_string()} | eval-val: {self.best_schedule.eval_value}")
          self.full_schedules_found += 1
          # print(f"   full_schedules_found: {self.full_schedules_found}")
          return None                 # the selected leaf is a completed schedule, return `None`
        
        DEBUG and print(f"   returning incomplete schedule: '{schedule.to_string()}'")
        
        return schedule               # return the selected leaf (incomplete schedule)

    return None # if we've gone through the entire heap and didn't `select` a leaf return `None`

  
  def _div(self, schedule: Schedule):
    '''
    Takes in the selected `schedule` from `f_trans()` and creates leaves (possible transitions, ie schedules)
    that will be stored in the list of leaves, `leaves_list`.
    DOES NOT create any leaves if the `schedule` is `None`.
    DOES NOT store schedules that were already encountered (ie we wont search through repeated schedules). 
    '''
    
    start_time = time.perf_counter()
    DEBUG and print(f"---div() start---")
    
    if (schedule is None):
      DEBUG and print(f"   schedule is `None`, returning...")
      return
    
    # create the leaves
    
    # create possible lecture assignments
    DEBUG and print("  --assigning lectures to lec slots...")
    # for clazz_id, clazz in schedule.lecs_dict.items():              # go through all lectures
    for clazz in schedule._static_lecs_array:
      int_slot_rep = schedule._schedule[Schedule._static_map_lec_tut_to_index[clazz.lecture_id]] # get assigned slot
      if (int_slot_rep is not None): # if the lecture was assigned already, continue
        DEBUG and print(f"[div()] '{clazz.lecture_id}' is already assigned, continuing...")
        continue
      
      for key, lec_slot in schedule.lec_slots_dict.items():         # go through possible lecture slots
        try:
          new_schedule = schedule.create_child_with_assigned_lec(clazz, lec_slot)
          
          if (new_schedule is None):    # assignment failed
            DEBUG and print(f"   [div()] (lec assignment not successful) continuing...")
            continue
          
          # print(f"[div()] new_schedule: {new_schedule.to_string()}")
          
          if (self._hard_constraint_check(new_schedule)):     # check if its a valid schedule after assignment
            # clazz.is_assigned = False                         # assignment was invalid, don't assign
            raise Exception(f"violated a hard constraint!")

          if (not self.is_schedule_unique(new_schedule)):     # check if the schedule is unique, so we don't repeat branches
            continue
          
          # DEBUG and print(f"   new schedule added to leaves: {new_schedule.to_string()}")
          
          self.leaves_list.append(new_schedule)           # assignment is valid, add the leaf to the list
        except Exception as e:
          # this assignment violated a hard constraint
          if (DEBUG):
            print(f"   [div()] Could not assign '{clazz.lecture_id}' to '{str(lec_slot)}'")
            print(f"   [div()] Exepction: '{e}'")
          continue
    
    # create possible tutorial assignments
    DEBUG and print("  --assigning tutorials to tut slots...")
    # for clazz_id, clazz in schedule.tuts_dict.items():              # go through all tutorials
    for clazz in schedule._static_tuts_array:
      int_slot_rep = schedule._schedule[Schedule._static_map_lec_tut_to_index[clazz.tutorial_id]] # get assigned slot
      if (int_slot_rep is not None): # if the tutorial was assigned already, continue
        DEBUG and print(f"[div()] '{clazz.tutorial_id}' is already assigned, continuing...")
        continue
      
      for key, tut_slot in schedule.tut_slots_dict.items():         # go through possible tutorial slots
        try:
          new_schedule = schedule.create_child_with_assigned_tut(clazz, tut_slot)
          
          if (new_schedule is None):    # assignment failed
            DEBUG and print(f"   [div()] (tut assignment not successful) continuing...")
            continue
          
          if (self._hard_constraint_check(new_schedule)):     # check if its a valid schedule after assignment
            # clazz.is_assigned = False                         # assignment was invalid, don't assign
            raise Exception(f"violated a hard constraint!")

          if (not self.is_schedule_unique(new_schedule)):     # check if the schedule is unique, so we don't repeat branches
            continue
          
          DEBUG and print(f"   new schedule added to leaves: {new_schedule.to_string()}")
          
          self.leaves_list.append(new_schedule)           # assignment is valid, add the leaf to the list
        except Exception as e:
          # this assignment violated a hard constraint
          if (DEBUG):
            print(f"   [div()] Could not assign '{clazz.tutorial_id}' to '{str(tut_slot)}'")
            print(f"   [div()] Exepction: '{e}'")
          continue
    
    del schedule
    end_time = time.perf_counter()
    DEBUG and print(f"---div() end, took {end_time - start_time:.4f} seconds---")
    
  
  def _div_OLD(self, schedule: Schedule):
    '''
    Takes in the selected `schedule` from `f_trans()` and creates leaves (possible transitions, ie schedules)
    that will be stored in the list of leaves, `leaves_list`.
    DOES NOT create any leaves if the `schedule` is `None`.
    DOES NOT store schedules that were already encountered (ie we wont search through repeated schedules). 
    '''
    
    start_time = time.perf_counter()
    DEBUG and print(f"---div() start---")
    
    if (schedule is None):
      DEBUG and print(f"   schedule is `None`, returning...")
      return
    
    # create the leaves
    
    # create possible lecture assignments
    DEBUG and print("  --assigning lectures to lec slots...")
    # for clazz_id, clazz in schedule.lecs_dict.items():              # go through all lectures
    for clazz in schedule._lecs_array:
      if (clazz.is_assigned): # if the lecture was assigned already, continue
        DEBUG and print(f"[OLD div()] '{clazz.lecture_id}' is already assigned, continuing...")
        continue
      
      for key, lec_slot in schedule.lec_slots_dict.items():         # go through possible lecture slots
        try:
          DEBUG and print(f"[OLD div()] making deep copy of schedule: '{schedule.to_string()}'")
          
          # could benefit with a cheaper check up here 
          
          new_schedule = copy.deepcopy(schedule)          # copy the current schedule
          
          if (not new_schedule.assign_lec(clazz, lec_slot)):     # assign the `clazz` to `lec_slot`, check if assignment was successful
            DEBUG and print(f"   [OLD div()] (assignment not successful) continuing...")
            continue      # assignment not successful, continue
          
          hard_constraint_start_time = time.perf_counter()
          if (self._hard_constraint_check(new_schedule)):        # check if its a valid schedule after assignment
            clazz.is_assigned = False                            # assignment was invalid, don't assign
            raise Exception(f"violated a hard constraint!")
          
          schedule_unique_constraint_start_time = time.perf_counter()
          if (not self.is_schedule_unique(new_schedule)):           # check if the schedule is unique, so we don't repeat branches
            continue
          
          DEBUG and print(f"   new schedule added to leaves: {new_schedule.to_string()}")
          
          self.leaves_list.append(new_schedule)           # assignment is valid, add the leaf to the list
        except Exception as e:
          # this assignment violated a hard constraint
          if (DEBUG):
            print(f"   [OLD div()] Could not assign '{clazz.lecture_id}' to '{str(lec_slot)}'")
            print(f"   [OLD div()] Exepction: '{e}'")
          continue
    
    # create possible tutorial assignments
    DEBUG and print("  --assigning tutorials to tut slots...")
    # for clazz_id, clazz in schedule.tuts_dict.items():              # go through all tutorials
    for clazz in schedule._tuts_array:
      if (clazz.is_assigned): # if the tutorial was assigned already, continue
        DEBUG and print(f"[OLD div()] '{clazz.tutorial_id}' is already assigned, continuing...")
        continue
      
      for key, tut_slot in schedule.tut_slots_dict.items():         # go through possible tutorial slots
        try:
          DEBUG and print(f"[OLD div()] making deep copy of schedule: '{schedule.to_string()}'")
          new_schedule = copy.deepcopy(schedule)          # copy the current schedule
          
          if (not new_schedule.assign_tut(clazz, tut_slot)):        # assign the `tut` to `tut_slot`, check if assignment was successful
            DEBUG and print(f"   (assignment not successful) continuing...")
            continue      # assignment not successful, continue
          
          hard_constraint_start_time = time.perf_counter()
          if (self._hard_constraint_check(new_schedule)):        # check if its a valid schedule before adding it as a leaf
            clazz.is_assigned = False                            # assignment was invalid, don't assign
            raise Exception(f"violated a hard constraint!")
          
          schedule_unique_constraint_start_time = time.perf_counter()
          if (not self.is_schedule_unique(new_schedule)):          # check if the schedule is unique, so we don't repeat branches
            continue
          
          # print schedule added
          DEBUG and print(f"   new schedule added to leaves: {new_schedule.to_string()}")
          
          self.leaves_list.append(new_schedule)           # assignment is valid, add the leaf to the list
        except Exception as e:
          # this assignment violated a hard constraint
          if (DEBUG):
            print(f"   Could not assign '{clazz.tutorial_id}' to '{str(tut_slot)}'")
            print(f"   Exepction: '{e}'")
          continue
    
    end_time = time.perf_counter()
    DEBUG and print(f"---div() end, took {end_time - start_time:.4f} seconds---")
  
  def _eval(self, schedule: Schedule):
    '''
    Assigns an `eval` value to `schedule`. From the formula:
    `eval` value = Eval_minfilled(`schedule`) * Weight_minfilled +
                   Eval_preference(`schedule`) * Weight_preference + 
                   Eval_pair(`schedule`) * Weight_pair + 
                   Eval_sectionDiff(`schedule`) * Weight_sectionDiff
    '''
    
    DEBUG and print(f"---eval function---")
    
    # old
    # minfilled_val = 0
    # if (schedule.is_filled()):
    #   minfilled_val = self._eval_minfilled(schedule) * self.weights[WEIGHT_MINFILLED_INDEX]
    
    minfilled_val = self._eval_minfilled(schedule) * self.weights[WEIGHT_MINFILLED_INDEX]
    pref_val = self._eval_pref(schedule) * self.weights[WEIGHT_PREFERENCE_INDEX]
    pair_val = self._eval_pair(schedule) * self.weights[WEIGHT_PAIR_INDEX]
    sec_diff_val = self._eval_section_diff(schedule) * self.weights[WEIGHT_SECTION_DIFF_INDEX]
    
    eval_val = minfilled_val + pref_val + pair_val + sec_diff_val
    
    # if (DEBUG):
      # print(f"schedule: {schedule.to_string()}")
      # print(f"minfilled_val eval: {minfilled_val}")
      # print(f"pref_val eval: {pref_val}")
      # print(f"pair_val eval: {pair_val}")
      # print(f"sec_diff_val eval: {sec_diff_val}")
      # print(f"---eval val: {eval_val}---\n")
    
    schedule.eval_value = eval_val
    return eval_val
  
  
  def _eval_minfilled(self, schedule: Schedule) -> float:
    DEBUG and print(f"    eval minfilled:")    
    minfilled_val: float = 0
    
    # go thorough lec slots and tut slots
    # compare the # of assigned with lecture min
    for _, slot in schedule.lec_slots_dict.items():
      # print(f"slot: {str(slot)}")
      # print(f"\tassigned_lectures: {len(slot.assigned_lectures)}")
      # print(f"\tmin: {slot.lecture_min}")
      
      # if the # of assigned lecs to a slot is less than the lecture min, add penalty
      # if (len(slot.assigned_lectures) < slot.lecture_min):
        # minfilled_val += (slot.lecture_min - len(slot.assigned_lectures)) * self.penalties[PEN_LECTURE_MIN_INDEX]
      if (slot.assigned_lectures < slot.lecture_min):
        minfilled_val += (slot.lecture_min - slot.assigned_lectures) * self.penalties[PEN_LECTURE_MIN_INDEX]
        # print(f"\tpenalty so far = {minfilled_val}")
    
    for _, slot in schedule.tut_slots_dict.items():
      # print(f"slot: {str(slot)}")
      # print(f"\tassigned_tutorials: {len(slot.assigned_tutorials)}")
      # print(f"\tmin: {slot.tutorial_min}")
      
      # if the # of assigned tuts to a slot is less than the tutorial min, add penalty
      # if (len(slot.assigned_tutorials) < slot.tutorial_min):
      #   minfilled_val += (slot.tutorial_min - len(slot.assigned_tutorials)) * self.penalties[PEN_TUTORIAL_MIN_INDEX]
      if (slot.assigned_tutorials < slot.tutorial_min):
        minfilled_val += (slot.tutorial_min - slot.assigned_tutorials) * self.penalties[PEN_TUTORIAL_MIN_INDEX]
        # print(f"penalty so far = {minfilled_val}")
    
    DEBUG and print(f"\tmin penalty = {minfilled_val}")
    return minfilled_val
  
  
  def _eval_pref(self, schedule: Schedule) -> float:
    
    # if (schedule.to_string() in self.preference_eval_cache):
    #   print(f"preference cache used! For: {schedule.to_string()}")
    #   return self.preference_eval_cache[schedule.to_string()]
    
    pref_val: float = 0
    
    # Eval preference
    # DEBUG and print(f"   preferences:")        
    for (classid, pref_day, pref_time, preference_value) in self._valid_preferences:
      try:
        slot_int_rep = schedule._schedule[schedule._static_map_lec_tut_to_index[classid]]
      except KeyError:
        # DEBUG and print(f"\t[ERROR] No class `{p.class_id}` exist!")
        # DEBUG and print(f"\t[KEY ERROR] {e}")
        # print("bruh")
        # print(f"\t[KEY ERROR] {e}")
        continue
      
      if (slot_int_rep is None):
        # DEBUG and print("\tassigned slot is None! adding NO penalty, continuing...")
        continue
      
      assigned_day, assigned_time = Schedule._static_map_int_to_day_time[slot_int_rep]
      if (assigned_day != pref_day or assigned_time != pref_time):
        pref_val += preference_value
        # DEBUG and print("\tassigned slot is not the preference.. adding penalty")
    
    # old
    # for p in self._static_model.prefs:
    #   assigned_slot = None
      
    #   try:
    #     assigned_slot = schedule.get_time_slot_from_int(schedule._schedule[schedule._static_map_lec_tut_to_index[p.class_id]])
    #   except KeyError as e:
    #     # DEBUG and print(f"\t[ERROR] No class `{p.class_id}` exist!")
    #     # DEBUG and print(f"\t[KEY ERROR] {e}")
    #     # print("bruh")
    #     # print(f"\t[KEY ERROR] {e}")
    #     continue
      
    #   # DEBUG and print(f"   `{p.class_id}`:")
    #   # if (DEBUG):
    #   #   if (assigned_slot is not None):
    #   #     DEBUG and print(f"\tassigned slot is: `{assigned_slot.day}` at `{assigned_slot.start_time}`")
    #   #   else:
    #   #     DEBUG and print(f"\tassigned slot is: None")
      
    #   # DEBUG and print(f"\tpreference slot is: `{p.slot_day}` at `{p.slot_time}` | pref val: {p.preference_value}")
    #   preference_slot_exists = False
      
    #   if (assigned_slot is None):
    #     # pref_val += float(p.preference_value)
    #     # DEBUG and print("\tassigned slot is None! adding NO penalty, continuing...")
    #     continue
    #   # check if the prefered (tut/lec) slot actually exists 
    #   # if (assigned_slot is not None):
    #   else:
    #     if (type(assigned_slot) == input_classes.LectureSlot):    # is the slot a `LectureSlot`
    #       lec_slot = input_classes.LectureSlot()
    #       lec_slot.day = p.slot_day
    #       lec_slot.start_time = p.slot_time
          
    #       if (str(lec_slot) not in schedule.lec_slots_dict):  # slot does not exist
    #         # DEBUG and print(f"\t--this preference LEC slot does not exist! adding no penalty, continuing...")
    #         continue
    #       preference_slot_exists = True
            
    #     else:                                                       # slot a `TutorialSlot`
    #       tut_slot = input_classes.TutorialSlot()
    #       tut_slot.day = p.slot_day
    #       tut_slot.start_time = p.slot_time
          
    #       if (str(tut_slot) not in schedule.tut_slots_dict):  # slot does not exist
    #         # DEBUG and print(f"\t--this preference TUT slot does not exist! adding no penalty, continuing...")
    #         continue
    #       preference_slot_exists = True

    #   # check the start time and day for the existing slot
    #   if (preference_slot_exists):
    #     if (p.slot_day == assigned_slot.day and p.slot_time == assigned_slot.start_time): # preference slot is the same as assigned slot
    #       DEBUG and print(f"\tassigned same as preference! adding NO penalty")
        
    #     # elif (p.slot_day != assigned_slot.day or p.slot_time != assigned_slot.start_time):
    #     else:
    #       pref_val += float(p.preference_value)
    #       # DEBUG and print("\tassigned slot is not the preference.. adding penalty")
    
    #   # DEBUG and print(f"\t-pref val so far: {pref_val}")
        
    # if (DEBUG):
      # print(f"\n\tcomputed pref_eval (NO weight applied): {pref_val}")
      # print(f"\ton schedule: {schedule.to_string()}")
    
    # self.preference_eval_cache[schedule.to_string()] = pref_val # store the calculated value
    return pref_val
  
  
  def _eval_pair(self, schedule: Schedule) -> float:
    eval_pair_val = 0

    for pair in self._static_model.pair:
      class1 = pair.id1
      class2 = pair.id2
      
      try:
        class1Slot = schedule.get_time_slot_from_int(schedule._schedule[schedule._static_map_lec_tut_to_index[class1]])
        class2Slot = schedule.get_time_slot_from_int(schedule._schedule[schedule._static_map_lec_tut_to_index[class2]])
      except KeyError as e:
        continue
      
      # remove this if we want to penalize class1 not being assigned but class2 being assigned.
      # technically they're not assigned together
      if class1Slot is None or class2Slot is None:
        continue
      
      # TODO: NEED FIXING
      # JUST LIKE IN COMPACT WE ARE NOT CHECKING OVERLAP PROPERLY! (see example `input_notcompat.txt`)
      # if class1Slot != class2Slot:
      if not _slots_overlap(class1Slot, class2Slot):
        eval_pair_val += self.penalties[PEN_NOT_PAIRED_INDEX]

    return eval_pair_val
  
    
  def _eval_section_diff(self, schedule: Schedule) -> float:
    eval_section_diff = 0
    groups = []

    # for c in schedule.lecs_dict:
    #   parts = c.split()
    #   course_id = f"{parts[0]} {parts[1]}"
    #   # print(f"parts: {parts}")
    #   # print(f"course_id: {course_id}")
    
    for c in schedule._static_lecs_array:
      parts = c.lecture_id.split()
      course_id = f"{parts[0]} {parts[1]}"
      # print(f"parts: {parts}")
      # print(f"course_id: {course_id}")
      
      # c_slot = schedule._schedule[schedule._static_map_lec_tut_to_index[c.lecture_id]]
      slot_int_representation = schedule._schedule[schedule._static_map_lec_tut_to_index[c.lecture_id]]
      c_slot = schedule.get_time_slot_from_int(slot_int_representation)
      
      if c_slot is None:
        continue

      slot_key = (c_slot.day, c_slot.start_time)

      bigger_course_id = (course_id, slot_key)

      if bigger_course_id not in groups:
        groups.append(bigger_course_id)
      else:
        for item in groups:
          if item == bigger_course_id:
            eval_section_diff += self.penalties[PEN_SECTION_INDEX]
        groups.append(bigger_course_id)

    # print(f"eval_section_diff {eval_section_diff}")
    # print(f"groups: {groups}")
    return eval_section_diff
  
  
  def _hard_constraint_check(self, schedule :Schedule) -> bool:
    '''
    Returns False if no hard constraints were violated, True otherwise.
    '''
    # TODO: check `not compatible`, `unwanted`, (`pair` -?).
    # Note: Some hard constraints are checked when `assigning` under classes 
    # LectureSlot and TutorialSlot (where `Schedule` emulates their outputs)
    # Note: use the `_static_model` to get those inputs!
    
    DEBUG and print("---Hard constraint check---")
    schedule_key = schedule.get_key()
    
    # check if we've already computed this schedule's hard constraints
    if (schedule_key in self.hard_constraint_check_cache):
      # DEBUG and print(f"hard constraint cache used! For: {schedule.to_string()}")
      # print(f"hard constraint cache used! This schedule appeared: {self.unique_schedules_cache[schedule_key]} times")
      # DEBUG and print(f"returning: {self.hard_constraint_check_cache[schedule_key]}")
      return self.hard_constraint_check_cache[schedule_key]
    
    # check for 5xx class time slot overlap
    # DEBUG and print(f" --5xx lecture overlap check")
    count_dict: dict[str, int] = {}   # key: time slot (string) | value: count (# of occurances)
    for lec in self._static_model.lecs:
      
      if bool(re.search(r".*\s5.*\sLEC", lec.lecture_id)):    # check if this is a 5xx lecture
        
        # slot = schedule._schedule[schedule._static_map_lec_tut_to_index[lec.lecture_id]]  # get the assigned slot for the 5xx lecture  
        int_slot_rep = schedule._schedule[schedule._static_map_lec_tut_to_index[lec.lecture_id]]
        slot = schedule.get_time_slot_from_int(int_slot_rep)  # get the assigned slot for the 5xx lecture  
        
        # if (DEBUG):
        #   print(f"\tlec id: `{lec.lecture_id}`")
        #   print(f"\tslot: `{slot}`")
        
        if (slot == None):    # skip, if this lec does not have a slot assignment
          # DEBUG and print(f"   slot is None... continuing")
          continue
        
        str_slot = str(slot)
        
        # update the count for time slot used by 5xx
        if (str_slot not in count_dict):
          count_dict[str_slot] = 1
          DEBUG and print(f"")
        else:
          count_dict[str_slot] += 1
        
        if (count_dict[str_slot] >= 2):
          # if (DEBUG):
          #   print(f"     5xx overlap detected!")
          #   print(f"\toverlap schedule: {schedule.to_string()}")
          #   print(f"\tshared 5xx slots: {count_dict}")
            
          self.hard_constraint_check_cache[schedule_key] = True   # add to the cache
          return True

    # check for non-compatible classes
    for classPair in self._static_model.not_compat:
      class1 = classPair.id1
      class2 = classPair.id2 # get two classes that are not compat w/ each other
      
      class1Slot = schedule.get_time_slot_from_int(schedule._schedule[schedule._static_map_lec_tut_to_index[class1]])
      class2Slot = schedule.get_time_slot_from_int(schedule._schedule[schedule._static_map_lec_tut_to_index[class2]])

      if class1Slot != None and class2Slot != None:
        if _slots_overlap(class1Slot, class2Slot):
          DEBUG and print(f"not-compatible violation: {class1} and {class2} overlap!")
          self.hard_constraint_check_cache[schedule_key] = True
          return True

    # check for unwanted classes
    for currClass in self._static_model.unwanted:
      # classSlot = schedule._schedule[schedule._static_map_lec_tut_to_index[currClass.class_id]] # retrieve the tentative assignment
      classSlot = schedule.get_time_slot_from_int(schedule._schedule[schedule._static_map_lec_tut_to_index[currClass.class_id]]) # retrieve the tentative assignment
      
      if classSlot != None: # only test tentative assignments that exist
        if classSlot.day == currClass.slot_day and classSlot.start_time == currClass.slot_time: # if it's the unwanted time
          self.hard_constraint_check_cache[schedule_key] = True
          return True
        
    # check for 9xx classes
    for item in self._static_model.lecs:
      if bool(re.search(r"LEC\s+9", item.lecture_id)): # if there is a LEC 9 in the lecture_id
        # classSlot = schedule._schedule[schedule._static_map_lec_tut_to_index[item.lecture_id]] # retrieve the tentative assignment
        classSlot = schedule.get_time_slot_from_int(schedule._schedule[schedule._static_map_lec_tut_to_index[item.lecture_id]]) # retrieve the tentative assignment
        
        if classSlot != None: # if it's been assigned
          intStartTime = int(classSlot.start_time.replace(":", "")) # turn the start time into a string
          if intStartTime < 1800: # make sure that the start time is at 18:00 or later
            self.hard_constraint_check_cache[schedule_key] = True
            return True

    
    for tutItem in self._static_model.tuts:
      #print(item.tutorial_id)
      # tutSlot = schedule._schedule[schedule._static_map_lec_tut_to_index[tutItem.tutorial_id]]
      tutSlot = schedule.get_time_slot_from_int(schedule._schedule[schedule._static_map_lec_tut_to_index[tutItem.tutorial_id]])
      
      if tutSlot != None: # the tutorial has been assigned, so we need to check it's assignment
        for lecItem in self._static_model.lecs: 
          # print(f"tutItem.tutorial_id[:15]: {tutItem.tutorial_id[:15]}")
          # print(f"lecItem.lecture_id[:15]: {lecItem.lecture_id[:15]}")
          if tutItem.tutorial_id[:15] == lecItem.lecture_id[:15]: # when the course id's match
            # lecSlot = schedule._schedule[schedule._static_map_lec_tut_to_index[lecItem.lecture_id]]
            lecSlot = schedule.get_time_slot_from_int(schedule._schedule[schedule._static_map_lec_tut_to_index[lecItem.lecture_id]])
            
            if lecSlot != None and tutSlot != None and tutSlot == lecSlot: # bug here? -> do not do: tutSlot == lecSlot
              if _slots_overlap(lecSlot, tutSlot): 
                self.hard_constraint_check_cache[schedule_key] = True
                return True
            # elif lecSlot != None and lecSlot.day == "TU" and tutSlot == lecSlot:
            #   lecHours, lecMinutes = map(int, lecSlot.start_time.split(":"))
            #   lecStart = lecHours * 60 + lecMinutes
            #   tutHours, tutMinutes = map(int, tutSlot.start_time.split(":"))
            #   tutStart = tutHours * 60 + tutMinutes
            #   if lecStart < tutStart + 90 and tutStart < lecStart + 90:
            #     self.hard_constraint_check_cache[schedule_key] = True
            #     return True


    # returns False if no hard constraints were violated
    self.hard_constraint_check_cache[schedule_key] = False    # save it in the cache
    DEBUG and print("---[END] Hard constraint check---")
    return False
  
  
  def is_schedule_unique(self, schedule:Schedule):
    '''
    Checks if `schedule` is unique (ie have we encountered something like this already in the search).
    If we've encountered this schedule before (ie not unique) return False, otherwise True.
    Also add's this `schedule` to the unique schedules dictionary if its new.
    '''
    
    # convert the schedule to a key      
    sch_key = schedule.get_key()
    
    if (sch_key not in self.unique_schedules_cache):  # set the new entry
      self.unique_schedules_cache[sch_key] = 1
      return True
    
    self.unique_schedules_cache[sch_key] += 1
    return False
    
    
  def save_schedule_to_file(self, schedule:Schedule):
    '''
    Saves the `schedule` to a file (only call this if the schedule is completed and is the best one currently found!)
    '''
    
    try:
      os.makedirs(SAVE_SCHEDULE_FOLDER, exist_ok=True)  # create the folder if it does not already exist
      
      # save the schedule neatly
      sch_dict = schedule.get_schedule()
      max_key_len = max(len(key) for key in sch_dict) + 1

      # attempt to save the `schedule` to a tmp file
      tmp_file_path = SAVE_SCHEDULE_FOLDER + "/tmp_file.txt"
      beginning = "lec slot "
      with open(tmp_file_path, 'w') as f:
        f.write(f"Eval-value: {schedule.eval_value}\n")
        for _class, slot in sch_dict.items():
          f.write(f"{_class:<{max_key_len}}: {str(slot)[len(beginning):]}\n")
      
      os.replace(tmp_file_path, SAVE_SCHEDULE_FOLDER + "/" + SAVE_SCHEDULE_NAME)  # override the previous best schedule 
      
    except KeyboardInterrupt:
      print("[EXCEPTION - KeyboardInterrupt] Stopped writing to file...")
    except:
      print("[EXCEPTION] dunno what caused it, prolly nothing too serious :)")

