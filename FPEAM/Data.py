import pandas as pd
from IO import load
from collections import OrderedDict

from . import utils

LOGGER = utils.logger(name=__name__)

# move logger to file-level
# move basicConfig to fpeam.py and out of module
# maybe don't use DataFrame (could have adverse side-effects)
# don't need to re-set inherited properties
# use pytest for crying out loud


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
                raise RuntimeError('{} failed validation: {}'.format(__name__, _valid))
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

    COLUMNS = {'feedstock': str, 'tillage_type': str, 'equipment_group': str, 'budget_year': int, 'operation_unit': int,
               'activity': str, 'equipment_name': str, 'equipment_horsepower': float, 'resource': str, 'rate': float, 'unit': str}

    INDEX_COLUMNS = ('equipment_group', 'feedstock', 'tillage_type', 'equipment_group',
                     'budget_year', 'operation_unit', 'activity', 'equipment_name', 'equipment_horsepower',
                     'resource', 'unit')

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(Equipment, self).__init__(df=df, fpath=fpath, columns=columns)


class Production(Data):

    COLUMNS = {'feedstock': str, 'tillage_type': str,
               'production_region': str, 'equipment_group': str,
               'nonroad_fips': str, 'moves_fips': str,
               'feedstock_measure': str, 'feedstock_amount': float, 'unit': str}

    # @TODO: moves_fips and nonroad_fips columns should be optional and backfilled with NaN if not present

    INDEX_COLUMNS = ('production_region', 'feedstock', 'tillage_type', 'equipment_group')

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(Production, self).__init__(df=df, fpath=fpath, columns=columns)


class FertilizerDistribution(Data):

    COLUMNS = {'feedstock': str,
               'chemical_id': str,
               'allocation': float}

    INDEX_COLUMNS = ('feedstock', 'chemical_id')

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(FertilizerDistribution, self).__init__(df=df, fpath=fpath, columns=columns)


class EmissionFactor(Data):
    COLUMNS = {'resource': str,
               'chemical_id': str,
               'pollutant': str,
               'rate': float,
               'unit': str}

    INDEX_COLUMNS = ('resource', 'chemical_id', 'pollutant')

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(EmissionFactor, self).__init__(df=df, fpath=fpath, columns=columns)


class FugitiveDust(Data):

    COLUMNS = {'feedstock': str,
               'tillage_type': str,
               'source_category': str,
               'budget_year': int,
               'pollutant': str,
               'rate': float,
               'unit': str}

    INDEX_COLUMNS = ('feedstock', 'tillage_type', 'source_category', 'budget_year', 'pollutant')

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(FugitiveDust, self).__init__(df=df, fpath=fpath, columns=columns)


class SCCCodes(Data):

    COLUMNS = {'name': str,
               'scc': str}

    INDEX_COLUMNS = ('name', )

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(SCCCodes, self).__init__(df=df, fpath=fpath, columns=columns)


class MoistureContent(Data):

    COLUMNS = {'feedstock': str,
               'moisture_content': str}

    INDEX_COLUMNS = ('feedstock', )

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(MoistureContent, self).__init__(df=df, fpath=fpath, columns=columns)


class NONROADEquipment(Data):

    COLUMNS = {'equipment_name': str,
               'nonroad_equipment_name': str,
               'nonroad_equipment_scc': str}

    INDEX_COLUMNS = ('equipment_name', )

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(NONROADEquipment, self).__init__(df=df, fpath=fpath, columns=columns)
