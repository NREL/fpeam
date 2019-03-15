import pandas as pd

from . import utils
from .IO import load

LOGGER = utils.logger(name=__name__)


class Data(pd.DataFrame):
    """
    FPEAM data representation.
    """

    COLUMNS = []

    INDEX_COLUMNS = []

    def __init__(self, df=None, fpath=None, columns=None):

        _df = pd.DataFrame({}) if df is None and fpath is None else load(fpath=fpath,
                                                                         columns=columns)

        super(Data, self).__init__(data=_df)

        self.source = fpath or 'DataFrame'

        _valid = self.validate()

        try:
            assert _valid is True
        except AssertionError:
            if df is not None or fpath is not None:
                raise RuntimeError('{} failed validation'.format(__name__, ))
            else:
                pass

        # error if mandatory missing
        # coerce types
        # error if not able to coerce
        # backfill non-mandatory missing
        for _column in self.COLUMNS:
            if _column['backfill'] is not None:
                self.backfill(column=_column['name'], value=_column['backfill'])

    def backfill(self, column, value=0):
        """
        Replace NaNs in <column> with <value>.

        :param column: [string]
        :param value: [any]
        :return:
        """

        _dataset = str(type(self)).split("'")[1]

        _backfilled = False

        # if any values are missing,
        if self[column].isna().any():
            # count the missing values
            _count_missing = sum(self[column].isna())
            # count the total values
            _count_total = self[column].__len__()

            # fill the missing values with zeros
            self[column].fillna(value, inplace=True)

            # log a warning with the number of missing values
            LOGGER.warning('%s of %s %s.%s values were backfilled as %s' %
                           (_count_missing, _count_total, _dataset,
                            column, value))

            _backfilled = True

        else:
            # log if no values are missing
            LOGGER.info('no missing %s.%s values' % (_dataset, column))

        return _backfilled

    def summarize(self):
        # @TODO: add summarization methods
        raise NotImplementedError

    def validate(self):

        # @TODO: add validation methods
        _name = type(self).__name__

        _valid = True

        LOGGER.debug('validating %s' % (_name, ))

        if self.empty:
            LOGGER.warning('no data provided for %s' % (_name, ))
            _valid = False

        LOGGER.debug('validated %s' % (_name, ))

        return _valid

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # process exceptions
        if exc_type is not None:
            LOGGER.exception('%s\n%s\n%s' % (exc_type, exc_val, exc_tb))
            return False
        else:
            return self


class Equipment(Data):

    COLUMNS = ({'name': 'feedstock', 'type': str, 'index': True, 'backfill': None},
               {'name': 'tillage_type', 'type': str, 'index': True, 'backfill': None},
               {'name': 'equipment_group', 'type': str, 'index': True, 'backfill': None},
               {'name': 'rotation_year', 'type': int, 'index': True, 'backfill': None},
               {'name': 'activity', 'type': str, 'index': True, 'backfill': None},
               {'name': 'equipment_name', 'type': str, 'index': True, 'backfill': None},
               {'name': 'equipment_horsepower', 'type': float, 'index': True, 'backfill': None},
               {'name': 'resource', 'type': str, 'index': True, 'backfill': None},
               {'name': 'rate', 'type': float, 'index': False, 'backfill': 0},
               {'name': 'unit_numerator', 'type': str, 'index': True, 'backfill': None},
               {'name': 'unit_denominator', 'type': str, 'index': True, 'backfill': None})

    def __init__(self, df=None, fpath=None, columns=(_['name'] for _ in COLUMNS)):
        super(Equipment, self).__init__(df=df, fpath=fpath, columns=columns)


class Production(Data):

    COLUMNS = ({'name': 'feedstock', 'type': str, 'index': True, 'backfill': None},
               {'name': 'tillage_type', 'type': str, 'index': True, 'backfill': None},
               {'name': 'region_production', 'type': str, 'index': True, 'backfill': None},
               {'name': 'region_destination', 'type': str, 'index': True, 'backfill': None},
               {'name': 'equipment_group', 'type': str, 'index': True, 'backfill': None},
               {'name': 'feedstock_measure', 'type': str, 'index': True, 'backfill': None},
               {'name': 'feedstock_amount', 'type': float, 'index': False, 'backfill': 0},
               {'name': 'unit_numerator', 'type': str, 'index': True, 'backfill': None},
               {'name': 'unit_denominator', 'type': str, 'index': True, 'backfill': None})

    def __init__(self, df=None, fpath=None, columns=(_['name'] for _ in COLUMNS)):
        super(Production, self).__init__(df=df, fpath=fpath, columns=columns)

    # @todo validate: feedstock, region_production, feedstock_measure missing values trigger runtime error


class FeedstockLossFactors(Data):

    COLUMNS = ({'name': 'feedstock', 'type': str, 'index': True, 'backfill': None},
               {'name': 'activity', 'type': str, 'index': True, 'backfill': None},
               {'name': 'supply_chain_stage', 'type': str, 'index': True, 'backfill': None},
               {'name': 'dry_matter_loss', 'type': float, 'index': False, 'backfill': 0},)

    def __init__(self, df=None, fpath=None, columns=(_['name'] for _ in COLUMNS)):
        super(FeedstockLossFactors, self).__init__(df=df, fpath=fpath, columns=columns)

    # @todo validate: feedstock or supply_chain_stage missing values trigger runtime error


class ResourceDistribution(Data):

    COLUMNS = ({'name': 'feedstock', 'type': str, 'index': True, 'backfill': None},
               {'name': 'resource', 'type': str, 'index': True, 'backfill': None},
               {'name': 'resource_subtype', 'type': str, 'index': True, 'backfill': None},
               {'name': 'distribution', 'type': float, 'index': True, 'backfill': 0})

    def __init__(self, df=None, fpath=None, columns=(_['name'] for _ in COLUMNS)):
        super(ResourceDistribution, self).__init__(df=df, fpath=fpath, columns=columns)

    # @todo validate: distribution column values sum to one within unique feedstock-resource combos
    # @todo validate: resource and resource_subtype values match those in EmissionFactor


class EmissionFactor(Data):
    COLUMNS = ({'name': 'resource', 'type': str, 'index': True, 'backfill': None},
               {'name': 'resource_subtype', 'type': str, 'index': True, 'backfill': None},
               {'name': 'activity', 'type': str, 'index': True, 'backfill': None},
               {'name': 'pollutant', 'type': str, 'index': True, 'backfill': None},
               {'name': 'rate', 'type': float, 'index': False, 'backfill': 0},
               {'name': 'unit_numerator', 'type': str, 'index': True, 'backfill': None},
               {'name': 'unit_denominator', 'type': str, 'index': True, 'backfill': None},)

    def __init__(self, df=None, fpath=None, columns=(_['name'] for _ in COLUMNS)):
        super(EmissionFactor, self).__init__(df=df, fpath=fpath, columns=columns)

    # @todo validate: resource, resource_subtype values match those in ResourceDistribution


class FugitiveDust(Data):

    COLUMNS = ({'name': 'feedstock', 'type': str, 'index': True, 'backfill': None},
               {'name': 'tillage_type', 'type': str, 'index': True, 'backfill': None},
               {'name': 'pollutant', 'type': str, 'index': True, 'backfill': None},
               {'name': 'rate', 'type': float, 'index': False, 'backfill': 0},
               {'name': 'unit_numerator', 'type': str, 'index': True, 'backfill': None},
               {'name': 'unit_denominator', 'type': str, 'index': True, 'backfill': None})

    def __init__(self, df=None, fpath=None, columns=(_['name'] for _ in COLUMNS)):
        super(FugitiveDust, self).__init__(df=df, fpath=fpath, columns=columns)

    # @todo validate: missing feedstock, pollutant generate error


class SCCCodes(Data):

    COLUMNS = ({'name': 'resource_subtype', 'type': str, 'index': True, 'backfill': None},
               {'name': 'scc', 'type': str, 'index': False, 'backfill': None})

    def __init__(self, df=None, fpath=None, columns=(_['name'] for _ in COLUMNS)):
        super(SCCCodes, self).__init__(df=df, fpath=fpath, columns=columns)

    # @todo validate: any missing values generate error
    # @todo validate: resource_subtypes match those in ResourceDistribution, EmissionFactor


class NONROADEquipment(Data):

    COLUMNS = ({'name': 'equipment_name', 'type': str, 'index': True, 'backfill': None},
               {'name': 'equipment_description', 'type': str, 'index': False, 'backfill': None},
               {'name': 'nonroad_equipment_scc', 'type': str, 'index': False, 'backfill': None})

    def __init__(self, df=None, fpath=None, columns=(_['name'] for _ in COLUMNS)):
        super(NONROADEquipment, self).__init__(df=df, fpath=fpath, columns=columns)

    # @todo validate: equipment_name values match those in Equipment
    # @todo validate: any missing SCC codes for provided equipment_name generates error


class Irrigation(Data):

    COLUMNS = ({'name': 'feedstock', 'type': str, 'index': True, 'backfill': None},
               {'name': 'state_fips', 'type': str, 'index': True, 'backfill': None},
               {'name': 'activity', 'type': str, 'index': True, 'backfill': None},
               {'name': 'equipment_name', 'type': str, 'index': True, 'backfill': None},
               {'name': 'equipment_horsepower', 'type': float, 'index': True, 'backfill': None},
               {'name': 'irrigation_water_source', 'type': str, 'index': True, 'backfill': None},
               {'name': 'acreage_fraction', 'type': float, 'index': False, 'backfill': 0},
               {'name': 'resource', 'type': str, 'index': True, 'backfill': None},
               {'name': 'rate', 'type': float, 'index': False, 'backfill': 0},
               {'name': 'unit_numerator', 'type': str, 'index': True, 'backfill': None},
               {'name': 'unit_denominator', 'type': str, 'index': True, 'backfill': None})

    def __init__(self, df=None, fpath=None, columns=(_['name'] for _ in COLUMNS)):
        super(Irrigation, self).__init__(df=df, fpath=fpath, columns=columns)

    # @todo validate: missing equipment_horsepower values triggers error


class TransportationGraph(Data):

    COLUMNS = ({'name': 'edge_id', 'type': int, 'index': True, 'backfill': None},
               {'name': 'statefp', 'type': str, 'index': False, 'backfill': None},
               {'name': 'countyfp', 'type': str, 'index': False, 'backfill': None},
               {'name': 'u_of_edge', 'type': int, 'index': False, 'backfill': None},
               {'name': 'v_of_edge', 'type': int, 'index': False, 'backfill': None},
               {'name': 'weight', 'type': float, 'index': False, 'backfill': None})

    def __init__(self, df=None, fpath=None, columns=(_['name'] for _ in COLUMNS)):
        super(TransportationGraph, self).__init__(df=df, fpath=fpath, columns=columns)


class CountyNode(Data):

    COLUMNS = ({'name': 'fips', 'type': str, 'index': True, 'backfill': None},
               {'name': 'node_id', 'type': int, 'index': False, 'backfill': None})

    def __init__(self, df=None, fpath=None, columns=(_['name'] for _ in COLUMNS)):
        super(CountyNode, self).__init__(df=df, fpath=fpath, columns=columns)

        if 'fips' not in self.index.names:
            self.set_index('fips', inplace=True)


class RegionFipsMap(Data):

    COLUMNS = ({'name': 'region', 'type': str, 'index': True, 'backfill': None},
               {'name': 'fips', 'type': str, 'index': True, 'backfill': None})

    def __init__(self, df=None, fpath=None, columns=(_['name'] for _ in COLUMNS)):
        super(RegionFipsMap, self).__init__(df=df, fpath=fpath, columns=columns)

    def validate(self):
        try:
            assert self.region.nunique() == self.fips.nunique()
        except AssertionError:
            _region_counts = self.region.value_counts()
            _dup_regions = list(_region_counts.loc[_region_counts != 1].values)
            if _dup_regions:
                LOGGER.error('Duplicated region values in region_fips_map data: %s' % _dup_regions)

            _fips_counts = self.fips.value_counts()
            _dup_fips = list(_fips_counts.loc[_region_counts != 1].values)
            if _dup_fips:
                LOGGER.error('Duplicated FIPS values in region_fips_map data: %s' % _dup_fips)
            raise ValueError('region_fips_map data must have only 1 '
                             'FIPS per region and 1 region per FIPS')
        else:
            return True


class StateFipsMap(Data):

    COLUMNS = ({'name': 'state_abbreviation', 'type': str, 'index': True, 'backfill': None},
               {'name': 'state_fips', 'type': str, 'index': False, 'backfill': None})

    def __init__(self, df=None, fpath=None, columns=(_['name'] for _ in COLUMNS)):
        super(StateFipsMap, self).__init__(df=df, fpath=fpath, columns=columns)


class TruckCapacity(Data):

    COLUMNS = ({'name': 'feedstock', 'type': str, 'index': True, 'backfill': None},
               {'name': 'truck_capacity', 'type': float, 'index': False, 'backfill': None},
               {'name': 'unit_numerator', 'type': str, 'index': True, 'backfill': None},
               {'name': 'unit_denominator', 'type': str, 'index': True, 'backfill': None})

    def __init__(self, df=None, fpath=None, columns=(_['name'] for _ in COLUMNS)):
        super(TruckCapacity, self).__init__(df=df, fpath=fpath, columns=columns)


class AVFT(Data):

    COLUMNS = ({'name': 'sourceTypeID', 'type': int, 'index': True, 'backfill': None},
               {'name': 'modelYearID', 'type': int, 'index': True, 'backfill': None},
               {'name': 'fuelTypeID', 'type': int, 'index': True, 'backfill': None},
               {'name': 'engTechID', 'type': int, 'index': True, 'backfill': None},
               {'name': 'fuelEngFraction', 'type': float, 'index': False, 'backfill': None})

    def __init__(self, df=None, fpath=None, columns=(_['name'] for _ in COLUMNS)):
        super(AVFT, self).__init__(df=df, fpath=fpath, columns=columns)

    # @todo validate: any missing values generates error (filling in with zeros or NaNs may break MOVES)
