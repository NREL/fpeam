import pandas as pd

from . import utils
from .IO import load

LOGGER = utils.logger(name=__name__)


class Data(pd.DataFrame):
    """
    FPEAM data representation.
    """

    COLUMNS = {}
    # @TODO: add method to warn users if column names don't match and what name we choose

    INDEX_COLUMNS = []

    def __init__(self, df=None, fpath=None, columns=COLUMNS):

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
        # else:
        #     if index_columns:
        #         self.set_index(keys=index_columns, inplace=True, drop=True)

        # error if mandatory missing
        # coerce types
        # error if not able to coerce
        # backfill non-mandatory missing

    def backfill(self):
        # @TODO: add backfill methods
        raise NotImplementedError

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

    COLUMNS = {'feedstock': str,
               'tillage_type': str,
               'equipment_group': str,
               'rotation_year': int,
               'activity': str,
               'equipment_name': str,
               'equipment_horsepower': float,
               'resource': str,
               'rate': float,
               'unit_numerator': str,
               'unit_denominator': str}

    INDEX_COLUMNS = ('equipment_group', 'feedstock', 'tillage_type', 'equipment_group',
                     'rotation_year', 'activity',
                     'equipment_name', 'equipment_horsepower',
                     'resource', 'unit_numerator', 'unit_denominator')

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(Equipment, self).__init__(df=df, fpath=fpath, columns=columns)


class Production(Data):

    COLUMNS = {'feedstock': str,
               'tillage_type': str,
               'region_production': str,
               'region_destination': str,
               'equipment_group': str,
               'feedstock_measure': str,
               'feedstock_amount': float,
               'unit_numerator': str,
               'unit_denominator': str}

    # @TODO: moves_fips and nonroad_fips columns should be optional and backfilled with NaN if not present

    INDEX_COLUMNS = ('region_production', 'feedstock', 'tillage_type',
                     'equipment_group')

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(Production, self).__init__(df=df, fpath=fpath, columns=columns)


class ResourceDistribution(Data):

    COLUMNS = {'feedstock': str,
               'resource': str,
               'resource_subtype': str,
               'distribution': float}

    INDEX_COLUMNS = ('feedstock', 'resource', 'resource_subtype')

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(ResourceDistribution, self).__init__(df=df, fpath=fpath, columns=columns)


class EmissionFactor(Data):
    COLUMNS = {'resource': str,
               'resource_subtype': str,
               'activity': str,
               'pollutant': str,
               'rate': float,
               'unit_numerator': str,
               'unit_denominator': str,}

    INDEX_COLUMNS = ('resource', 'resource_subtype', 'activity', 'pollutant')

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(EmissionFactor, self).__init__(df=df, fpath=fpath, columns=columns)


class FugitiveDust(Data):

    COLUMNS = {'feedstock': str,
               'tillage_type': str,
               'pollutant': str,
               'rate': float,
               'unit_numerator': str,
               'unit_denominator': str}

    INDEX_COLUMNS = ('feedstock', 'tillage_type', 'pollutant',)

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(FugitiveDust, self).__init__(df=df, fpath=fpath, columns=columns)


class SCCCodes(Data):

    COLUMNS = {'resource_subtype': str,
               'scc': str}

    INDEX_COLUMNS = ('resource_subtype', )

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(SCCCodes, self).__init__(df=df, fpath=fpath, columns=columns)


class NONROADEquipment(Data):

    COLUMNS = {'equipment_name': str,
               'equipment_description': str,
               'nonroad_equipment_scc': str}

    INDEX_COLUMNS = ('equipment_name', )

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(NONROADEquipment, self).__init__(df=df, fpath=fpath, columns=columns)


class Irrigation(Data):

    COLUMNS = {'feedstock': str,
               'state_fips': str,
               'activity': str,
               'equipment_name': str,
               'equipment_horsepower': float,
               'irrigation_water_source': str,
               'acreage_fraction': float,
               'resource': str,
               'rate': float,
               'unit_numerator': str,
               'unit_denominator': str}

    INDEX_COLUMNS = {'feedstock', 'state_fips'}

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(Irrigation, self).__init__(df=df, fpath=fpath, columns=columns)


class TransportationGraph(Data):

    COLUMNS = {'edge_id': int,
               'statefp': str,
               'countyfp': str,
               'u_of_edge': int,
               'v_of_edge': int,
               'weight': float}

    INDEX_COLUMNS = ('edge_id', )

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(TransportationGraph, self).__init__(df=df, fpath=fpath, columns=columns)


class CountyNode(Data):

    COLUMNS = {'fips': str,
               'node_id': int}

    INDEX_COLUMNS = ('fips', )

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(CountyNode, self).__init__(df=df, fpath=fpath, columns=columns)

        if 'fips' not in self.index.names:
            self.set_index('fips', inplace=True)


class RegionFipsMap(Data):

    COLUMNS = {'region': str,
               'fips': str}

    INDEX_COLUMNS = ('region', )

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
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

    COLUMNS = {'state_abbreviation': str,
               'state_fips': str}

    INDEX_COLUMNS = ('state_abbreviation', )

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(StateFipsMap, self).__init__(df=df, fpath=fpath, columns=columns)


class TruckCapacity(Data):

    COLUMNS = {'feedstock': str,
               'truck_capacity': float,
               'unit_numerator': str,
               'unit_denominator': str}

    INDEX_COLUMNS = ('feedstock', )

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(TruckCapacity, self).__init__(df=df, fpath=fpath, columns=columns)


class AVFT(Data):

    COLUMNS = {'sourceTypeID': int,
               'modelYearID': int,
               'fuelTypeID': int,
               'engTechID': int,
               'fuelEngFraction': float}

    INDEX_COLUMNS = ('sourceTypeID', 'modelYearID', 'fuelTypeID', 'engTechID')

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(AVFT, self).__init__(df=df, fpath=fpath, columns=columns)
