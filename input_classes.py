from abc import ABC

"""
NOTE: these classes have their attributes in the order of how it appears in the input file.
do not change it as the parser looks at the exact order of these attributes and assigns
a value to each one.
"""

class Section(ABC): 
  pass


class Lecture(Section):
  def __init__(self):
    self.lecture_id = None
    self.alrequired = None

  def __str__(self):
    al = "without AL" if self.alrequired else "with AL"
    return f"'{self.lecture_id}' {al}"
  


class LectureSlot(Section):
  def __init__(self):
    self.day = None
    self.start_time = None
    self.lecture_max = None
    self.lecture_min = None
    self.allecturemax = None
    self.assigned_al_lectures:int = 0
    self.assigned_lectures:int = 0

  def add_lecture(self, lec: Lecture) -> None:
    # print(f"inside slot: {str(self)}")
    # print(f"max AL: {self.allecturemax}")
    # print(f"assigned to AL: {len(self.assigned_al_lectures)}")
    # print(f"lec.alrequired: {lec.alrequired} | lec: {lec.lecture_id} | al_req type: {type(lec.alrequired)} | cast-> al_req type: {bool(type(lec.alrequired))} ")
    
    # print(f"inside slot: {str(self)}")
    # print(f"max AL: {self.allecturemax}")
    # print(f"assigned to AL: {self.assigned_al_lectures}")
    # print(f"lec.alrequired: {lec.alrequired} | lec: {lec.lecture_id} | al_req type: {type(lec.alrequired)} | cast-> al_req type: {bool(type(lec.alrequired))} ")
    
    
    if lec.alrequired and (self.assigned_al_lectures >= self.allecturemax):
      raise IndexError("you are trying to assign an AL lecture to a slot that has enough AL lectures!")
    elif self.assigned_lectures >= self.lecture_max:
      raise IndexError("you are trying to assign a lecture to a slot that is already full!")
    else: 
      # print("assigning...")
      self.assigned_lectures += 1
      if lec.alrequired:
        self.assigned_al_lectures += 1


  def __str__(self):
    # return f"lecture slot on {self.day} starting at {self.start_time}"
    return f"lec slot {self.day}, {self.start_time}"
    
  
  def __repr__(self):
    '''
    in dictionaries, it will display the value below instead of it's memory location.
    '''
    # return f"lecture slot on {self.day} starting at {self.start_time}"
    return f"lec slot {self.day}, {self.start_time}"



class Tutorial(Section):
  def __init__(self):
    self.tutorial_id = None
    self.alrequired = None


  def __str__(self):
    al = "without AL" if self.alrequired else "with AL"
    return f"'{self.tutorial_id}' {al}"
  

class TutorialSlot(Section):
  def __init__(self):
    self.day = None
    self.start_time = None
    self.tutorial_max = None
    self.tutorial_min = None
    self.altutorial_max = None
    self.assigned_al_tutorials:int = 0
    self.assigned_tutorials:int = 0

  def add_tutorial(self, tut: Tutorial) -> None:
    if tut.alrequired and (self.assigned_al_tutorials >= self.altutorial_max):
      raise IndexError("you are trying to assign an AL tutorial to a slot that has enough AL tutorials!")
    elif self.assigned_tutorials >= self.tutorial_max:
      raise IndexError("you are trying to assign a tutorial to a slot that is already full!")
    else: 
      self.assigned_tutorials += 1
      if tut.alrequired:
        self.assigned_al_tutorials += 1


  def __str__(self):
    # return f"tutorial slot on {self.day} starting at {self.start_time}"
    return f"tut slot {self.day}, {self.start_time}"
  
  def __repr__(self):
    '''
    in dictionaries, it will display the value below instead of it's memory location.
    '''
    # return f"tutorial slot on {self.day} starting at {self.start_time}"
    return f"tut slot {self.day}, {self.start_time}"


class NotCompatible(Section):
  def __init__(self):
    self.id1 = None
    self.id2 = None

  
  def __str__(self):
    return f"'{self.id1}' and '{self.id2}' are not compatible with each other"

class Unwanted(Section):
  def __init__(self):
    self.class_id = None
    self.slot_day = None
    self.slot_time = None


  def __str__(self):
    return f"'{self.class_id}' on {self.slot_day} at {self.slot_time} is unwanted"


class Preference(Section):
  def __init__(self):
    self.slot_day = None
    self.slot_time = None
    self.class_id = None
    self.preference_value = None


  def __str__(self):
    return f"'{self.class_id}' is preferred on {self.slot_day} at {self.slot_time} with a value of {self.preference_value}"
  

class Pair(Section):
  def __init__(self):
    self.id1 = None
    self.id2 = None


  def __str__(self):
    return f"'{self.id1}' and '{self.id2}' is a pair"


class PartialAssignment(Section):
  def __init__(self):
    self.class_id = None
    self.slot_day = None
    self.slot_time = None


  def __str__(self):
    return f"'{self.class_id}' is partially assigned on {self.slot_day} at {self.slot_time}"


class InputModel(Section):
  def __init__(self, name:str, lec_slots:list[LectureSlot], tut_slots:list[TutorialSlot], lecs:list[Lecture], tuts:list[Tutorial], not_compat:list[NotCompatible], unwanted:list[Unwanted], prefs:list[Preference], pair:list[Pair], partials:list[PartialAssignment]):
    self.name = name
    self.lec_slots = lec_slots
    self.tut_slots = tut_slots
    self.lecs = lecs
    self.tuts = tuts
    self.not_compat = not_compat
    self.unwanted = unwanted
    self.prefs = prefs
    self.pair = pair
    self.partials = partials
    
