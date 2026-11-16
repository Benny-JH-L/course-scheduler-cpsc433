from input_classes import InputModel
from input_classes import Lecture as Lec
from input_classes import LectureSlot as LS
from input_classes import Tutorial as Tut
from input_classes import TutorialSlot as TS
import os
import copy
import sys

DEBUG = os.environ.get("DEBUG")
DEBUG and print(f"[and_tree.py] DEBUG = {DEBUG}") # note it doesn't matter the value, if it exists it is `True`
# example of how to envoke debugging on;
# Windows: $Env:DEBUG = "1"; python main.py input.txt 1 1 1 1 1 1 1 1 ; Remove-Item Env:DEBUG | remove the environment varable: `Remove-Item Env:DEBUG`
# Linux: env "DEBUG=1"; python main.py input.txt 1 1 1 1 1 1 1 1  | `env` -> temporary 
# if you don't want debugging then just run as normal.
# Note: use proper weights :)

class Schedule():
  _static_map_lec_tut_to_index: dict[str, int] = {}   # key: <Tutorial> or <Lecture> id | value: index (int)
    # static variable, contains the index mappings for the Lectures and Tutorials, 
    # ex. 
    # _static_map_lec_tut_to_index[<lecture id>] = 4; self.schedule[4] = int representation of <lecture slot>, similarily, 
    # _static_map_lec_tut_to_index[<tutorial id>] = 5; self.schedule[5] = int representation of <tutorial slot>
    
  _static_map_time_slots_to_int: dict[str, int] = {}  # key: <Tutorial> or <Lecture> slot string | value: int
  _static_map_int_to_time_slot_str: dict[int, str] = {}  # key: int | value: <Tutorial> or <Lecture> slot string
  # instead of havin this mapping, we can map the int straight to the lec/tut slot (but it will be instance specific!)?
  
  # for partial assignment check, if a lec/tut exists
  _static_lec_ids: set[str] = set()
  _static_tut_ids: set[str] = set()
  
  # lec and tut shared for all schedule instances
  _static_lecs_array: list[Lec] = []
  _static_tuts_array: list[Tut] = []
  
  _static_map_int_to_day_time: dict[int, tuple[str, str]] = {}    # key: int (integer representation of a tut/lec slot) | value: (day, time)
  
  def __init__(self, model:InputModel):
    '''
    Takes in an `InputModel` and deep copies the `lec_slots`, `tut_slots`, and preprocess
    '''
    # index of the list represent the Lecture/Tutorial and the value inside contain the assigned Lecture/Tutorial slot
    self._schedule: int[int] = []
    self.eval_value = 0
    self.num_assigned_classes = 0

    # precompute _static variables
    # Map Lectures and Tutorials to an index if the mapping hasn't been done yet
    if (len(Schedule._static_map_lec_tut_to_index) == 0):    
      index = 0
      
      if (DEBUG):
        print(f"\n\n---Assigning indicies to Lecture/Tutorials for schedule---")
        print(f"---Lecture (size: {len(model.lecs)})---")
        
      for lec in model.lecs:
        if (DEBUG):
          print(f" lecture_id: '{lec.lecture_id}'")
          print(f"   alrequired: '{lec.alrequired}'")
          # print(f"   is_assigned: '{lec.is_assigned}'")
          print(f"   assigned index: '{index}'")
        Schedule._static_map_lec_tut_to_index[lec.lecture_id] = index
        index += 1
      
      DEBUG and print(f"---Tutorial --- (size: {len(model.tuts)})")
      for tut in model.tuts:
        if (DEBUG):
          print(f" tutorial_id: '{tut.tutorial_id}'")
          print(f"   alrequired: '{tut.alrequired}'")
          # print(f"   is_assigned: '{tut.is_assigned}'")
          print(f"   assigned index: '{index}'")
        Schedule._static_map_lec_tut_to_index[tut.tutorial_id] = index
        index += 1
    # map time slots to an integer
    if (len(Schedule._static_map_time_slots_to_int) == 0):
      index = 0
      
      if (DEBUG):
        print(f"\n\n---Assigning indicies to Time Slots of Lecture/Tutorials for schedule---")
        print(f"---Lecture slots (size: {len(model.lec_slots)})---")
        
      for slot in model.lec_slots:
        if (DEBUG):
          print(f"   slot: '{str(slot)}'")
          print(f"   assigned index: '{index}'")
        Schedule._static_map_time_slots_to_int[str(slot)] = index
        Schedule._static_map_int_to_time_slot_str[index] = str(slot)
        index += 1
      
      DEBUG and print(f"---Tutorial slots --- (size: {len(model.tut_slots)})")
      for slot in model.tut_slots:
        if (DEBUG):
          print(f"   slot: '{str(slot)}'")
          print(f"   assigned index: '{index}'")
        Schedule._static_map_time_slots_to_int[str(slot)] = index
        Schedule._static_map_int_to_time_slot_str[index] = str(slot)
        index += 1
    # create static tuts and lecs
    if (len(Schedule._static_lec_ids) == 0):
      for lec in model.lecs:
        Schedule._static_lec_ids.add(lec.lecture_id)
      for tut in model.tuts:
        Schedule._static_tut_ids.add(tut.tutorial_id)
    # build this cache (for key computation later)
    if (len(Schedule._static_map_int_to_day_time) == 0):
      for slot_int, slot_str in Schedule._static_map_int_to_time_slot_str.items():
        parts = slot_str.split(", ")
        day = parts[0].split()[-1]
        time = parts[1]
        Schedule._static_map_int_to_day_time[slot_int] = (day, time)
    
    self.lec_slots_dict: dict[str, LS] = {}           # key: str(<Lecture Slot>), val: <Lecture Slot>
    for slot in copy.deepcopy(model.lec_slots):
      self.lec_slots_dict[str(slot)] = slot
      # print(f"lec slot dict key: '{str(slot)}'")
      
    self.tut_slots_dict: dict[str, TS] = {}           # key: str(<Tutorial Slot>), val: <Tutorial Slot>
    for slot in copy.deepcopy(model.tut_slots):
      self.tut_slots_dict[str(slot)] = slot
      # print(f"tut slot dict key: '{str(slot)}'")
    
    if (len(Schedule._static_lecs_array) == 0):
      Schedule._static_lecs_array = model.lecs
      Schedule._static_tuts_array = model.tuts
      
    # self.lecs_dict: dict[str, Lec] = {}               # key: str(<Lecture id>), val: <Lecture>
    # for lec in copy.deepcopy(model.lecs):
    #   self.lecs_dict[lec.lecture_id] = lec
    # #   print(f"lec dict key: '{lec.lecture_id}'")
    # # print(f"size of lecs_dict: {len(self.lecs_dict)}")
    
    # self.tuts_dict: dict[str, Tut] = {}               # key: str(<Tutorial id>), val: <Tutorial>
    # for tut in copy.deepcopy(model.tuts):
    #   self.tuts_dict[tut.tutorial_id] = tut
    # #   print(f"tut dict key: '{tut.tutorial_id}'")
    # # print(f"size of tuts_dict: {len(self.tuts_dict)}")

    # Initialize the `schedule` to `None` (ie empty)
    DEBUG and print(f"---Initializing schedule ---")
    # for x in range(0, len(Schedule._static_map_lec_tut_to_index) + 1):
    #   self._schedule.append(None)
    self._schedule = [None] * len(Schedule._static_map_lec_tut_to_index) 
    
    # assign partial assignments
    for item in model.partials: # for each class that needs to be partially assigned
      # if item.class_id in self.lecs_dict: # if it's a lecture
      if (self.is_class_id_a_lec(item.class_id)):
      # if (item in self._lecs_array):
        for lecItem in model.lecs: 
          if lecItem.lecture_id == item.class_id: # retrieve the lecture in the model.lecs
            # retrieve the timeslot from the timeslot dictionary
            for lecSlot in model.lec_slots:
              if lecSlot.day == item.slot_day and lecSlot.start_time == item.slot_time:
                  result = self.assign_lec(lecItem, lecSlot)
                  if (not result): # assignment failed (returned false)
                    sys.exit("Partial assignment failed: Lecture slot over flowed!")
      
      # elif item.class_id in self.tuts_dict: # do it again for tutorial
      elif (self.is_class_id_a_tut(item.class_id)):
      # elif (item in self._tuts_array):
        for tutItem in model.tuts:
          if tutItem.tutorial_id == item.class_id:
            for tutSlot in model.tut_slots:
              if tutSlot.day == item.slot_day and tutSlot.start_time == item.slot_time:
                result = self.assign_tut(tutItem, tutSlot)
                if (not result): # assignment failed (returned false)
                  sys.exit("Partial assignment failed: Tutorial slot over flowed!")
    
   
  def assign_lec(self, lec:Lec, lec_slot:LS) -> bool:
    '''
    `lec` is the lecture to assign, `lec_slot` is the slot you wish to assign it to.
      Returns `True` if the assignment was successful, `False` otherwise.  
    '''
    # if (DEBUG):
    #   print(f"--assigning lec--")
    #   print(f"'{lec.lecture_id}' assign to '{lec_slot}' ?")    
    
    idx = Schedule._static_map_lec_tut_to_index[lec.lecture_id]
    # DEBUG and print(f"'{lec.lecture_id}' has schedule index: '{idx}'")
    
    # check if lecture was already assigned
    if (self._schedule[idx] != None):
      # DEBUG and print(f"'{lec.lecture_id}' is already assigned to: '{self._schedule[idx]}'")
      return False 

    # grab the specific slot and lecture that's instance specific to this schedule
    my_lec_slot = self.lec_slots_dict[str(lec_slot)]
    # my_lec = self.lecs_dict[lec.lecture_id]
    # my_lec = self.get_lec_instance(lec)
    
    try:
      # my_lec_slot.add_lecture(my_lec) # try to add the lecture to this slot 
      my_lec_slot.add_lecture(lec) # try to add the lecture to this slot 
    except Exception as e:
      if (DEBUG):
        print(f"Failed to assign '{lec.lecture_id}' to '{str(my_lec_slot)}'")
        print(f"Execption: '{e}'")     
      return False                # if an exception occurs, then the assignment is not possible
    
    # do assignment
    # self._schedule[idx] = my_lec_slot
    self._schedule[idx] = Schedule._static_map_time_slots_to_int[str(my_lec_slot)]
    self.num_assigned_classes += 1
    DEBUG and print(f"'{lec.lecture_id}' assigned to slot: '{my_lec_slot}')") # | is_assigned = {my_lec.is_assigned}")

    return True   # assigned successfully
  
   
  def assign_tut(self, tut:Tut, tut_slot:TS) -> bool:
    '''
    `tut` is the tutorial to assign, `tut_slot` is the slot you wish to assign it to.
    Returns `True` if the assignment was successful, `False` otherwise.
    '''
    
    # if (DEBUG):
    #   print(f"--assigning tut--")
    #   print(f"'{tut.tutorial_id}' assign to '{tut_slot}' ?")
    
    idx = Schedule._static_map_lec_tut_to_index[tut.tutorial_id]
    # DEBUG and print(f"tut '{tut.tutorial_id}' has schedule index: '{idx}'")
    
    # check if tutorial was already assigned
    if (self._schedule[idx] != None):
      # DEBUG and print(f"'{tut.tutorial_id}' is already assigned to: '{self._schedule[idx]}'")
      return False
    
    # grab the specific slot and tutorial that's instance specific to this schedule
    my_tut_slot = self.tut_slots_dict[str(tut_slot)]
    # my_tut = self.tuts_dict[tut.tutorial_id]
    # my_tut = self.get_tut_instance(tut)

    try:
      # my_tut_slot.add_tutorial(my_tut)  # try to add the tutorial to this slot
      my_tut_slot.add_tutorial(tut)  # try to add the tutorial to this slot
    except Exception as e:
      if (DEBUG):
        print(f"Failed to assign '{tut.tutorial_id}' to '{str(my_tut_slot)}'")
        print(f"Execption: '{e}'")    
      return False                # if an exception occurs, then the assignment is not possible
    
    # do assignment
    # self._schedule[idx] = my_tut_slot
    self._schedule[idx] = Schedule._static_map_time_slots_to_int[str(my_tut_slot)]
    self.num_assigned_classes += 1
    DEBUG and print(f"tut '{tut.tutorial_id}' assigned to slot: '{my_tut_slot}'") # | is_assigned = {my_tut.is_assigned}")
    
    return True   # assigned successfully


  def create_child_with_assigned_lec(self, lec:Lec, lec_slot:LS):
    '''
    `lec` is the lecture to assign, `lec_slot` is the slot you wish to assign it to.
    Returns a `schedule` with the assignment if it was successful, `None` otherwise.
    NOTE: it does not matter if the `lec` or `lec_slot` is instance specific to this schedule or the output schedule, this function
    will gurantee that the assignment will use instance specific lecture slot for the outputted schedule.
    '''
    
    lec_id = lec.lecture_id
    idx = Schedule._static_map_lec_tut_to_index[lec_id]
    
    # check if lecture was already assigned
    if (self._schedule[idx] != None):
      DEBUG and print(f"[Schedule.py] '{lec_id}' is already assigned to: '{self._schedule[idx]}'")
      return None
    
    new_schedule: Schedule = Schedule.__new__(Schedule)    # make a schedule instance
    new_schedule._schedule = self._schedule.copy()
    new_schedule.num_assigned_classes = self.num_assigned_classes
    # new_schedule._schedule = copy.deepcopy(self._schedule)
    
    
    # keep shared values that wont change when assigning
    new_schedule._static_map_lec_tut_to_index = self._static_map_lec_tut_to_index
    new_schedule._static_map_time_slots_to_int = self._static_map_time_slots_to_int
    new_schedule._static_map_int_to_time_slot_str = self._static_map_int_to_time_slot_str
    new_schedule._static_tuts_array = self._static_tuts_array
    new_schedule._static_lecs_array = self._static_lecs_array
    
    new_schedule.tut_slots_dict = self.tut_slots_dict
    # new_schedule.tuts_dict = self.tuts_dict
    
    # make copies of values that will change
    new_schedule.lec_slots_dict = self.lec_slots_dict.copy()
    # new_schedule.lec_slots_dict = copy.deepcopy(self.lec_slots_dict)
    # new_schedule.lecs_dict = copy.deepcopy(self.lecs_dict)
    # new_schedule._lecs_array = copy.deepcopy(self._lecs_array)
    
    # only deep copy the changed slot
    slot_key = str(lec_slot)
    new_schedule.lec_slots_dict[slot_key] = copy.deepcopy(self.lec_slots_dict[slot_key])
    
    # grab the specific slot and lecture that's instance specific to this schedule
    my_lec_slot = new_schedule.lec_slots_dict[slot_key]
    # my_lec = new_schedule.lecs_dict[lec_id]
    # my_lec = new_schedule.get_lec_instance(lec)
    
    try:
      # my_lec_slot.add_lecture(my_lec) # try to add the lecture to this slot 
      my_lec_slot.add_lecture(lec) # try to add the lecture to this slot 
    except Exception as e:
      if (DEBUG):
        print(f"[Schedule.py] Failed to assign '{lec_id}' to '{slot_key}'")
        print(f"[Schedule.py] Execption: '{e}'")     
      return None                # if an exception occurs, then the assignment is not possible
    
    # do assignment
    # new_schedule._schedule[idx] = my_lec_slot
    new_schedule._schedule[idx] = Schedule._static_map_time_slots_to_int[slot_key]
    new_schedule.num_assigned_classes += 1
    DEBUG and print(f"[Schedule.py] '{lec_id}' assigned to slot: '{my_lec_slot}'")# | is_assigned = {my_lec.is_assigned}")
    
    # new_schedule.eval_value = copy.deepcopy(self.eval_value)  # will be changed later in f_leaf()
    new_schedule.eval_value = 0
    return new_schedule
  
  
  def create_child_with_assigned_tut(self, tut:Tut, tut_slot:TS):
    '''
    `tut` is the tutorial to assign, `tut_slot` is the slot you wish to assign it to.
    Returns a `schedule` with the assignment if it was successful, `None` otherwise.
    NOTE: it does not matter if the `tut` or `tut_slot` is instance specific to this schedule or the output schedule, this function
    will gurantee that the assignment will use instance specific tutorial slot for the outputted schedule.
    '''
    
    tut_id = tut.tutorial_id
    idx = Schedule._static_map_lec_tut_to_index[tut_id]
    
    # check if tutorial was already assigned
    if (self._schedule[idx] != None):
      DEBUG and print(f"[Schedule.py] '{tut_id}' is already assigned to: '{self._schedule[idx]}'")
      return None
    
    new_schedule: Schedule = Schedule.__new__(Schedule)    # make a schedule instance
    new_schedule._schedule = self._schedule.copy()
    new_schedule.num_assigned_classes = self.num_assigned_classes
    # new_schedule._schedule = copy.deepcopy(self._schedule)
    
    
    # keep shared values that wont change when assigning
    new_schedule._static_map_lec_tut_to_index = self._static_map_lec_tut_to_index
    new_schedule._static_map_time_slots_to_int = self._static_map_time_slots_to_int
    new_schedule._static_map_int_to_time_slot_str = self._static_map_int_to_time_slot_str
    new_schedule._static_lecs_array = self._static_lecs_array
    new_schedule._static_tuts_array = self._static_tuts_array
    
    new_schedule.lec_slots_dict = self.lec_slots_dict
    # new_schedule.lecs_dict = self.lecs_dict
    
    # make copies of values that will change
    new_schedule.tut_slots_dict = self.tut_slots_dict.copy()
    # new_schedule.tut_slots_dict = copy.deepcopy(self.tut_slots_dict)
    # new_schedule.tuts_dict = copy.deepcopy(self.tuts_dict)
    # new_schedule._tuts_array = copy.deepcopy(self._tuts_array)
    
    # deep copy the changed slot
    slot_key = str(tut_slot)
    new_schedule.tut_slots_dict[slot_key] = copy.deepcopy(self.tut_slots_dict[slot_key])
    
    # grab the specific slot and tutorial that's instance specific to this schedule
    my_tut_slot = new_schedule.tut_slots_dict[slot_key]
    # my_tut = new_schedule.tuts_dict[tut_id]
    # my_tut = new_schedule.get_tut_instance(tut)
    
    try:
      # my_tut_slot.add_tutorial(my_tut) # try to add the tutorial to this slot 
      my_tut_slot.add_tutorial(tut) # try to add the tutorial to this slot 
    except Exception as e:
      if (DEBUG):
        print(f"[Schedule.py] Failed to assign '{tut_id}' to '{slot_key}'")
        print(f"[Schedule.py] Execption: '{e}'")     
      return None                # if an exception occurs, then the assignment is not possible
    
    # do assignment
    # new_schedule._schedule[idx] = my_tut_slot
    new_schedule._schedule[idx] = Schedule._static_map_time_slots_to_int[slot_key]
    new_schedule.num_assigned_classes += 1
    
    DEBUG and print(f"[Schedule.py] tut '{tut_id}' assigned to slot: '{my_tut_slot}'")# | is_assigned = {my_tut.is_assigned}")
    
    # new_schedule.eval_value = copy.deepcopy(self.eval_value)  # will be changed later in f_leaf()
    new_schedule.eval_value = 0
    return new_schedule
  

  def get_schedule(self):
    '''
    Return's a dictionary representation of our `schedule` {lecture/tutorial: time slot}
    '''
    rtn_Dict = {}
    # DEBUG and print("---[Schedule] getting schedule---")
    
    for key, idx in sorted(Schedule._static_map_lec_tut_to_index.items()):
      # rtn_Dict[key] = self._schedule[idx]   # get the assigned time slot
      rtn_Dict[key] = self.get_time_slot_from_int(self._schedule[idx])   # get the assigned time slot
      
      # DEBUG and print(f"{key}: {self._schedule[idx]}")
    
    # DEBUG and print("---[Schedule] end schedule---\n")

    return rtn_Dict

  def get_time_slot_from_int(self, int_map:int):
    '''returns a time slot instance from the `int_map`, please ensure that this int_map comes from computing: _schedule[#] '''
    # print(f"int to time slots")
    # for key, val in Schedule._static_map_int_to_time_slot_str.items():
    #   print(f"{key}: {val}")
    # print(f"int_map: {int_map}")
    
    if (int_map is None):
      return None
    
    int_key = Schedule._static_map_int_to_time_slot_str[int_map]
    
    if (int_key in self.lec_slots_dict):
      return self.lec_slots_dict[int_key]
    elif (int_key in self.tut_slots_dict):
      return self.tut_slots_dict[int_key]
    
  
  def to_string(self):
    return str(self.get_schedule())
  
    # old
    # dict = self.get_schedule()
    # string= "{"
    # for key, idx in dict.items():
    #   string += f"'{key}': '{str(idx)}', "
    # string = string[0:len(string)-2]  # remove the trailing ", "
    # string += "}"
    # return string
    
  def get_key(self) -> frozenset:
    '''
    returns a `frozenset` of a tuple containing lec/tut id and their assigned slot (if slot is not `None`), day and time. (lec/tut id, day, time)
    Use this as the `key` instead of `to_string()` when using this schedule as a key into a dictionary!
    Return's a frozenset(list), list is empty if all assigned slots are `None`.
    '''
    
    assignments = []
    for class_id, idx in Schedule._static_map_lec_tut_to_index.items():   # go though built schedule
      int_slot_rep = self._schedule[idx]
      if (int_slot_rep is not None):
        # get time and day
        day, time = Schedule._static_map_int_to_day_time[int_slot_rep]
        assignments.append((class_id, day, time))
        
      # old -> getting from objects are expensive
      # slot = self.get_time_slot_from_int(self._schedule[idx])
      # if (slot is not None):
      #   assignments.append((class_id, slot.day, slot.start_time))
        
    # print(f"s key: {str(frozenset(assignments))}")
    return frozenset(assignments)
  
  
  def is_filled(self) -> bool:
    '''
    Return's True if the schedule is filled (ie all lectures and tutorials have been assigned a lecture slot, or tutorial slot, respectivley), False otherwise.
    '''
    # DEBUG and print(f"---[Schedule] is_filled---")
    
    if (self.num_assigned_classes == len(self._schedule)):
      return True
    return False
    
    # old
    # for clazz in self._schedule:  # `clazz` is a tutorial or lecture
    #   if (clazz is None):         # if `clazz` is `None` then it wasn't assigned a lecture/tutorial slot 
    #     # DEBUG and print(f"   not filled! (False)")
    #     return False

    #   # DEBUG and print(f"   filled! (True)")
    # return True

  def is_class_id_a_lec(self, id: str):
    '''
    for partial assignment
    '''
    return id in Schedule._static_lec_ids
  
    # old
    # for x in self._lecs_array:
    #   if (id == x.lecture_id):
    #     return True
    # return False

  def is_class_id_a_tut(self, id: str):
    '''
    for partial assignment
    '''
    return id in Schedule._static_tut_ids
  
    # old
    # for x in self._tuts_array:
    #   if (id == x.tutorial_id):
    #     return True
    # return False

  def __lt__(self, other):
    return self.eval_value < other.eval_value
  