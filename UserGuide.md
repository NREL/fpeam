# Graphical user interface

FPEAM was built to run primarily as a command-line tool but is bundled with a graphical user interface (GUI) that manages user options and input data files. Options entered into the GUI populate config (.ini) files that pass the options into FPEAM. The options available in the GUI are considered basic options that will allow the average user to construct FPEAM scenarios. Additional user options are available directly in the config files and may be changed directly by the user for additional scenario customization.

## MOVES user options

Run MOVES or not

Scale at which MOVES is run (region, state, state by crop)

Specify input files discussed below.

## NONROAD user options

The only NONROAD options available through the GUI is the run_nonroad flag that controls whether NONROAD is run.

## EmissionFactors user options

The only GUI option for the chemical module is the run_chemical flag that controls whether the module is run. 

## FugitiveDust user options

The only GUI option for the fugitive dust module is the run_fugdust flag that controls whether the module is run.