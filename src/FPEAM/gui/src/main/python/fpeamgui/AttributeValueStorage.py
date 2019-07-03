
class AttributeValueStorage:

    def __init__(self):

        # FPEAM home page - Attribute Initialization
        self.scenarioName = "test"
        self.projectPath = None
        self.module = 'NONROAD', 'MOVES', 'emissionfactors', 'fugitivedust'
        self.loggerLevel = "DEBUG"
        self.equipment = 'data/equipment/bts16_equipment.csv'
        self.production = 'data/production/prod_2015_bc1060.csv'
        self.feedstockLossFactors = 'data/inputs/feedstock_loss_factors.csv'
        self.transportationGraph = 'data/inputs/transportation_graph.csv'
        self.countyNodes = 'data/inputs/county_nodes.csv'
        self.backfill = True
        self.useRouterEngine = True

        # Fugitive Dust module - Attribute Initialization
        self.feedMeasureTypeFD = "Harvested"
        self.emissionFactorsFD = "../data/inputs/fugitive_dust_emission_factors.csv"

        # Emission Factors Module - Attribute Initialization
        self.feedMeasureTypeEF = "Harvested"
        self.emissionFactorsEF = None
        self.resourceDistributionEF = None

        # Nonroad Module - Attribute Initialization
        self.yearNonroad = 2017
        self.feedstockMeasureTypeNon = "Harvested"
        self.timeResourceNameNon = "time"
        self.forestryFeedstockNames = ['forest whole tree', 'forest residues']
        self.regionFipsMapNonroad = "../data/inputs/region_fips_map.csv"
        self.nonroadDatafilesPath = "C:/Nonroad"
        self.tempMin = 50.0
        self.tempMax =68.8
        self.tempMean =60.0
        self.dieselLHV = 0.12845
        self.dieselNh3Ef = 0.68
        self.dieselThcVocConversion = 1.053
        self.dieselPm10topm25 = 0.97
        self.irrigationFeedstockMeasureType = "planted"
        self.irrigatedFeedstockNames = "corn grain"
        self.irrigation = "../data/inputs/irrigation.csv"
        self.encodeNames = True

        # Moves Module - Attribute Initialization
        self.aggegationLevel = "Moves By Each County"
        self.cachedResults = "Yes"
        self.feedstockMeasureTypeMoves = "Harvested"
        self.vMTPerTruck = 20
        self.noOfTrucksUsed = 1
        self.yearMoves = 2017
        self.movesDatafilesPath = "C:\MOVESdata"
        self.movesPath = "C:\MOVES2014a"
        self.truckCapacity = "../data/inputs/truck_capacity.csv"
        self.avft = "../data/inputs/avft.csv"
        self.regionFipsMapMoves = "../data/inputs/region_fips_map.csv"
        self.ruralRestricted = 0.30
        self.ruralUnrestricted = 0.28
        self.urbanRestricted = 0.21
        self.urbanUnrestricted = 0.21
        self.month = 10
        self.date = 5
        self.beginningHr = 7
        self.endingHr = 18
        self.dayType = 5


