import sys
from parser import parse_input
from and_tree import AndTree
from input_classes import InputModel as IM
import os
import time

DEBUG = os.environ.get("DEBUG")
DEBUG and print(f"[main.py] DEBUG = {DEBUG}") # note it doesn't matter the value, if it exists it is `True`
# example of how to envoke debugging on;
# Windows: $Env:DEBUG = "1"; python main.py input.txt 1 1 1 1 1 1 1 1 ; Remove-Item Env:DEBUG | remove the environment varable: `Remove-Item Env:DEBUG`
# Linux: env "DEBUG=1"; python main.py input.txt 1 1 1 1 1 1 1 1
# if you don't want debugging then just run as normal.
# Note: use proper weights :)

def Print_Input_Model(input_model: IM):
  '''
  Prints the `input_model` variables
  '''
  print(f"model name: '{input_model.name}'")
  
  print(f"---Lecture Slots (size: {len(input_model.lec_slots)})---")
  for item in input_model.lec_slots:
    print(f" day: '{item.day}' | type: {type(item.day)}")
    print(f"   start_time: '{item.start_time}' | type: {type(item.start_time)}")
    print(f"   lecture_max: '{item.lecture_max}' | type: {type(item.lecture_max)}")
    print(f"   lecture_min: '{item.lecture_min}' | type: {type(item.lecture_min)}")
    print(f"   allecturemax: '{item.allecturemax}' | type: {type(item.allecturemax)}")
    print(f"   assigned_al_lectures: '{item.assigned_al_lectures}' | type: {type(item.assigned_al_lectures)}")
    print(f"   assigned_lectures: '{item.assigned_lectures}' | type: {type(item.assigned_lectures)}")
  
  print(f"---Tutorial Slots--- (size: {len(input_model.tut_slots)})")
  for item in input_model.tut_slots:
    print(f" day: '{item.day}' | type: {type(item.day)}")
    print(f"   start_time: '{item.start_time}' | type: {type(item.start_time)}")
    print(f"   tutorial_max: '{item.tutorial_max}' | type: {type(item.tutorial_max)}")
    print(f"   tutorial_min: '{item.tutorial_min}' | type: {type(item.tutorial_min)}")
    print(f"   altutorialmax: '{item.altutorial_max}' | type: {type(item.altutorial_max)}")
    print(f"   assigned_al_tutorials: '{item.assigned_al_tutorials}' | type: {type(item.assigned_al_tutorials)}")
    print(f"   assigned_tutorials: '{item.assigned_tutorials}' | type: {type(item.assigned_tutorials)}")
  
  print(f"---Lectures (size: {len(input_model.lecs)})---")
  for item in input_model.lecs:
    print(f" lecture_id: '{item.lecture_id}' | type: {type(item.lecture_id)}")
    print(f"   alrequired: '{item.alrequired}' | type: {type(item.alrequired)}")
    print(f"   is_assigned: '{item.is_assigned}' | type: {type(item.is_assigned)}")
  
  print(f"---Tutorials (size: {len(input_model.tuts)})---")
  for item in input_model.tuts:
    print(f" tutorial_id: '{item.tutorial_id}' | type: {type(item.tutorial_id)}")
    print(f"   alrequired: '{item.alrequired}' | type: {type(item.alrequired)}")
    print(f"   is_assigned: '{item.is_assigned}' | type: {type(item.is_assigned)}")
    
  print(f"---Not Compatible (size: {len(input_model.not_compat)})---")
  for item in input_model.not_compat:
    print(f"'{item.id1}' AND '{item.id2}' | type (id1, id2): ({type(item.id1)}, {type(item.id2)})")

  print(f"---Unwanted (size: {len(input_model.unwanted)})---")
  for item in input_model.unwanted:
    print(f" class_id: '{item.class_id}' | type: {type(item.class_id)}")
    print(f"   slot_day: '{item.slot_day}' | type: {type(item.slot_day)}")
    print(f"   slot_time: '{item.slot_time}' | type: {type(item.slot_time)}")
    
  print(f"---Preference (size: {len(input_model.prefs)})---")
  for item in input_model.prefs:
    print(f" slot_day: '{item.slot_day}' | type: {type(item.slot_day)}")
    print(f"   slot_time: '{item.slot_time}' | type: {type(item.slot_time)}")
    print(f"   class_id: '{item.class_id}' | type: {type(item.class_id)}")
    print(f"   preference_value: '{item.preference_value}' | type: {type(item.preference_value)}")
    
  print(f"---Pair (size: {len(input_model.pair)})---")
  for item in input_model.pair:
    print(f"'{item.id1}' AND '{item.id2}' | type (id1, id2): ({type(item.id1)}, {type(item.id2)})")
    
  print(f"---Partial Assignment (size: {len(input_model.partials)})---")
  for item in input_model.partials:
    print(f" class_id: '{item.class_id}' | type: {type(item.class_id)}")
    print(f"   slot_day: '{item.slot_day}' | type: {type(item.slot_day)}")
    print(f"   slot_time: '{item.slot_time}' | type: {type(item.slot_time)}")

def main():
  if len(sys.argv) < 2:
    print("please provide the path to input file")
    sys.exit(-1)
  if len(sys.argv) < 10:
    print("please provide the penalty values and weightings")
    sys.exit(-1)

  weightings = sys.argv[2:6]
  penalty_values = sys.argv[6:]
  
  # convert to floats
  for x in range(0, len(weightings)):
    weightings[x] = float(weightings[x])
  
  for x in range(0, len(penalty_values)):
    penalty_values[x] = float(penalty_values[x])
    
  input_obj = parse_input(sys.argv[1])
  
  # remove tuesday 11am lectures, faculty meetings constraint
  for item in input_obj.lec_slots:
    if item.day == "TU" and item.start_time == "11:00":
      input_obj.lec_slots.remove(item)
      print(type(item))

  if (DEBUG):
    # Print_Input_Model(input_obj)
    print("\nBeginning Search")
  
  # start timer
  start_time = time.perf_counter()

  and_tree = AndTree(input_obj, weightings, penalty_values)
  del input_obj
  schedule = and_tree.search()

  end_time = time.perf_counter()

  print(f"\n\ntime elapsed: {(end_time - start_time):0.4f} seconds")

  if (schedule is None):
    print("oh no the returned schedule is 'None'... Now it could be right but are u sure?")
  else:
    print(f"---Best Schedule:")
    print(f"Eval-value: {schedule.eval_value}")
    
    # print schedule neatly
    beginning = "lec slot "
    sch_dict = schedule.get_schedule()
    max_key_len = max(len(key) for key in sch_dict) + 1
    for _class, slot in sch_dict.items():
      print(f"{_class:<{max_key_len}}: {str(slot)[len(beginning):]}")

if __name__ == "__main__":
  main()
  