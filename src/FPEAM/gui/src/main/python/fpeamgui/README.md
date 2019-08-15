# FPEAM - GUI

This is a simple UI for FPEAM. It contains total six tabs, namely, HOME, MOVES, NONROAD, EMISSION FACTORS, FUGITIVE DUST and RESULT.


### HOME Tab 

It contains mandatory fields such as Scenario Name and Project Path. Also, it has common fields which are required by each module to run. These common fields are optional. If user don't mention them, they are set to their default values. 

HOME Tab screenshot

![HomeTab](screenshots/HomeTab.png)

![HomeTabWithExpansion](screenshots/HomeTabWithExpansion.png)

If user don't mention mandatory fields, then those fields will get highlighted in red color.

![HomeTabWithoutMandatoryFields](screenshots/HomeTabWithoutMandatoryFields.png)

### MOVES Tab

It contains fields which are required to run MOVES module along with the fields in HOME tab.

![MovesTab](screenshots/MovesTab.png)

![MoveaTabWithExpansionPart1](screenshots/MoveaTabWithExpansionPart1.png)

![MovesTabWithExpansionPart2](screenshots/MovesTabWithExpansionPart2.png)

### NONROAD Tab

It contains fields which are required to run NONROAD module along with the fields in HOME tab.

![NonroadTab](screenshots/NonroadTab.png)

![NonroadTabWithExpansionPart1](screenshots/NonroadTabWithExpansionPart1.png)

![NonroadTabWithExpansionPart2](screenshots/NonroadTabWithExpansionPart2.png)

![NonroadTabWithExpansionPart3](screenshots/NonroadTabWithExpansionPart3.png)

The value of 'Analysis Year' field from MOVES tab and NONROAD tab should match. If user enters different values for 'Analysis Year' field in MOVES and NONROAD tab, then it shows error message in red color as -

![AnalysisYearInputValidationMOVES](screenshots/AnalysisYearInputValidationMOVES.png)

![AnalysisYearInputValidationNONROAD](screenshots/AnalysisYearInputValidationNONROAD.png)


### EMISSION FACTORS Tab

It contains fields which are required to run EMISSION FACTORS module along with the fields in HOME tab.

![EmissionFactorsTab](screenshots/EmissionFactorsTab.png)

### FUGITIVE DUST Tab

It contains fields which are required to run FUGITIVE DUST module along with the fields in HOME tab.

![FugitiveDustTab](screenshots/FugitiveDustTab.png)

### RESULT Tab

It displays the result in box plots along with logs. When the module is running, logs are printed simultaneously. The progress bar indicates that modules are running. While running any module, all tabs will be disabled so that user can't make any changes in inputs, while it's running.

![ResultTabWhileRunningModule](screenshots/ResultTabWhileRunningModule.png)

When the execution is done, the progress bar will be disabled and box plots will be displayed along with the log messages.

![ResultTabAfterRun](screenshots/ResultTabAfterRun.png)