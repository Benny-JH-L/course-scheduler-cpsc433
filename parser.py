import re, sys
import input_classes

def parse_input(file_path: str) -> input_classes.InputModel:
  """returns an object of all the input stuffs"""

  # this is for determining which part of the input we are on, just in case they are not in the same order
  # as shown in the example
  headers = {
    "name": 0,
    "lectureslots": 1,
    "tutorialslots": 2,
    "lectures": 3,
    "tutorials": 4,
    "notcompatible": 5,
    "unwanted": 6,
    "preferences": 7,
    "pair": 8,
    "partialassignments": 9
  }

  name = ""
  lec_slots: list[input_classes.LectureSlot] = []
  tut_slots: list[input_classes.TutorialSlot] = []
  lecs: list[input_classes.Lecture] = []
  tuts: list[input_classes.Tutorial] = []
  not_compatible_classes: list[input_classes.NotCompatible] = []
  unwanted_classes: list[input_classes.Unwanted] = []
  prefs: list[input_classes.Preference] = []
  pairs: list[input_classes.Pair] = []
  partials: list[input_classes.PartialAssignment] = []

  section_parsed = -1

  f = open(file_path)
  header_line_regex = re.compile(r'[\s:]')
  value_line_regex = re.compile(r',\s*')
  multi_space_regex = re.compile(r'\s+')

  for line in f:
    header_line_formatted = re.sub(header_line_regex, '', line).lower()
    value_line_formatted = re.sub(multi_space_regex, ' ', re.sub(value_line_regex, ',', line))

    # if it is None, then it is either a value line or an empty line and we process it
    # if it isn't None, then it's a header and we change the section we are parsing, and skip so we don't process it
    if headers.get(header_line_formatted) != None:
      section_parsed = headers.get(header_line_formatted)
      continue

    # skip empty lines
    if value_line_formatted == " " or value_line_formatted == "":
      continue

    match section_parsed:
      case 0:
        name = value_line_formatted
      case 1:
        lec_slot = input_classes.LectureSlot()

        # hard constraint to have no lectures at 11:00-12:30
        if lec_slot.day == "TU" and lec_slot.start_time == "11:00":
          continue
        
        _append_to_specific_section(value_line_formatted, lec_slot, lec_slots)
      case 2:
        tut_slot = input_classes.TutorialSlot()
        _append_to_specific_section(value_line_formatted, tut_slot, tut_slots)
      case 3:
        lec = input_classes.Lecture()
        _append_to_specific_section(value_line_formatted, lec, lecs)
      case 4:
        tut = input_classes.Tutorial()
        _append_to_specific_section(value_line_formatted, tut, tuts)
      case 5:
        not_compatible = input_classes.NotCompatible()
        _append_to_specific_section(value_line_formatted, not_compatible, not_compatible_classes)
      case 6:
        unwanted = input_classes.Unwanted()
        _append_to_specific_section(value_line_formatted, unwanted, unwanted_classes)
      case 7:
        pref = input_classes.Preference()
        _append_to_specific_section(value_line_formatted, pref, prefs)
      case 8:
        pair = input_classes.Pair()
        _append_to_specific_section(value_line_formatted, pair, pairs)
      case 9:
        partial = input_classes.PartialAssignment()
        _append_to_specific_section(value_line_formatted, partial, partials)
      case _:
        print("we are not on any particular section") # i don't think this runs anyway, just here for backup

  tutorial_slot_created_for_851_and_913 = False

  # ensure the correct data types
  for slot in lec_slots:
    slot.lecture_max = int(slot.lecture_max)
    slot.lecture_min = int(slot.lecture_min)
    slot.allecturemax = int(slot.allecturemax)
  
  tut_813_slot = None
  for slot in tut_slots:
    slot.tutorial_max = int(slot.tutorial_max)
    slot.tutorial_min = int(slot.tutorial_min)
    slot.altutorial_max = int(slot.altutorial_max)
    if slot.start_time == "18:00" and slot.day == "TU":
      print("slot created")
      tutorial_slot_created_for_851_and_913 = True
      tut_813_slot = slot
  
  created_851 = False
  created_913 = False
  
  cpsc_351_ids = []
  cpsc_413_ids = []
  for _class in lecs:
    if _class.lecture_id[:8] == "CPSC 351":
      cpsc_351_ids.append(_class.lecture_id)
    if _class.lecture_id[:8] == "CPSC 413":
      cpsc_413_ids.append(_class.lecture_id)
  for _class in tuts:
    if _class.tutorial_id[:8] == "CPSC 351":
      cpsc_351_ids.append(_class.tutorial_id)
    if _class.tutorial_id[:8] == "CPSC 413":
      cpsc_413_ids.append(_class.tutorial_id)
  
  for _class in lecs:
    _class.alrequired = (_class.alrequired.lower() == "true") # turn it to a bool
    # _class.is_assigned = False
    if _class.lecture_id[:8] == "CPSC 413" and not created_913:
      if not tutorial_slot_created_for_851_and_913:
        sys.exit("bad happened")
      if tut_813_slot != None and tut_813_slot.tutorial_max <= 0:
        sys.exit("bad happened")
      # print("THIS IS CPSC 413")
      # create a custom tutorial 913
      newTut = input_classes.Tutorial()
      newTut.tutorial_id = "CPSC 913 TUT 01"
      newTut.alrequired = "false"
      # newTut.is_assigned = True
      tuts.append(newTut)
      # assign it to the tutorial slot
      newPartial = input_classes.PartialAssignment()
      newPartial.class_id = "CPSC 913 TUT 01"
      newPartial.slot_day = "TU"
      newPartial.slot_time = "18:00"
      partials.append(newPartial)
      for cpsc_413_id in cpsc_413_ids:
        not_compat = input_classes.NotCompatible()
        not_compat.id1 = "CPSC 913 TUT 01"
        not_compat.id2 = cpsc_413_id
        not_compatible_classes.append(not_compat)
      created_913 = True
    if _class.lecture_id[:8] == "CPSC 351" and not created_851:
      if not tutorial_slot_created_for_851_and_913:
        sys.exit("bad happened")
      if tut_813_slot != None and tut_813_slot.tutorial_max <= 0:
        sys.exit("bad happened")
      # print("THIS IS CPSC 351")
      # create a custom tutorial 851
      newTut = input_classes.Tutorial()
      newTut.tutorial_id = "CPSC 851 TUT 01"
      newTut.alrequired = "false"
      # newTut.is_assigned = True
      tuts.append(newTut)
      # assign it to the tutorial slot
      newPartial = input_classes.PartialAssignment()
      newPartial.class_id = "CPSC 851 TUT 01"
      newPartial.slot_day = "TU"
      newPartial.slot_time = "18:00"
      partials.append(newPartial)
      for cpsc_351_id in cpsc_351_ids:
        not_compat = input_classes.NotCompatible()
        not_compat.id1 = "CPSC 851 TUT 01"
        not_compat.id2 = cpsc_351_id
        not_compatible_classes.append(not_compat)
      created_851 = True

  for _class in tuts:
    _class.alrequired = (_class.alrequired.lower() == "true") # turn it to a bool
    _class.is_assigned = False
    
  for p in prefs:
    p.preference_value = float(p.preference_value)
  
  parsed_input = input_classes.InputModel(name, lec_slots, tut_slots, lecs, tuts, not_compatible_classes, unwanted_classes, prefs, pairs, partials)
  f.close()
    
  return parsed_input


def _append_to_specific_section(line: str, section_obj: input_classes.Section, section_list: list) -> None:
  """
  takes a line as a string, a section object like lectures,
  tutorials, not compatible, etc. and appends it to its corresponding list.
  """

  line_list = line.split(',')
  
  # change all "LAB" occurances with "TUT"
  # print(f"line list: {line_list}")
  # if (len(line_list) >= 3):
  #   change = line_list[2].replace("LAB", "TUT")
  #   line_list[2] = change
  # print(f"new line list: {line_list}")
  
  attribute_names = list(vars(section_obj).keys())

  for attr_name, value in zip(attribute_names, line_list):
    setattr(section_obj, attr_name, value.strip())

  section_list.append(section_obj)