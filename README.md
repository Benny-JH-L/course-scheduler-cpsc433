# team zapdos

run the program by doing `python main.py <file_path> <weights & penalties>`
  Ex: `python main.py hudson_tests/starter.txt 1 1 1 1 1 1 1 1`

## notes

- Our search system is an And-tree, that goes through all unique/possible schedules and outputs the most optimal solution.

- Due to the nature of how we stored leaves, our search could not get a solution from the large inputs 1 or 2 because at some point when the search used up too much memory it would crash the system, or the operating system would terminate the program, (We tried the search on systems with 32GB of RAM).

- in the input file, there is an `unwanted` section, which lists lectures/tutorials we don't want to be assigned to a specific spot. i don't think we should remove the possibility of assigning a lecture/tutorial to a slot, because there would be a case where the most optimal schedule would need at least one of them to be assigned to an "unwanted" slot.

- to turn on debug statements:
  - Windows: $Env:DEBUG = "1"; python main.py <file_path> <weights & penalties> ; Remove-Item Env:DEBUG
  - Linux: env "DEBUG=1"; python main.py <file_path> <weights & penalties>

