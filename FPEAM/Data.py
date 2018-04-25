import pandas as pd
import logging
from IO import load
from collections import OrderedDict


class Data(pd.DataFrame):
    """
    FPEAM data representation.
    """

    COLUMNS = {}

    def __init__(self, df=None, fpath=None, columns=COLUMNS, logger=logging.getLogger(__name__)):

        self._logger = logger

        _df = df or load(fpath=fpath, columns=columns)

        super(Data, self).__init__(data=_df, index=None)

        # error if mandatory missing
        # coerce types
        # error if not able to coerce
        # backfill non-mandatory missing

    def __enter__(self):
        return self

    def backfill(self):
        # @TODO: add backfill methods
        raise NotImplementedError

    def summarize(self):
        # @TODO: add summarization methods
        raise NotImplementedError

    def validate(self):

        # @TODO: add validation methods
        return True

    def __exit__(self, exc_type, exc_val, exc_tb):
        # process exceptions
        if exc_type is not None:
            self._logger.exception('%s\n%s\n%s' % (exc_type, exc_val, exc_tb))
            return False
        else:
            return self


class Budget(Data):

    COLUMNS = OrderedDict((('id', str),
                           ('feedstock', str),
                           ('tillage_type', str),
                           ('equipment_region', str),
                           ('rotation_year', str),
                           ('operation_unit', str),
                           ('activity', str),
                           ('equipment_name', str),
                           ('equipment_hp', float),
                           ('capacity', float),
                           ('module', str),
                           ('resource', str),
                           ('rate', float),
                           ('unit', str)))

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(Budget, self).__init__(df=df, fpath=fpath, columns=columns)


class Production(Data):

    COLUMNS = OrderedDict((('scenario', str),
                           ('year', int),
                           ('feedstock', str),
                           ('tillage_type', str),
                           ('production_region', str),
                           ('equipment_region', str),
                           ('nonroad_fips', str),
                           ('moves_fips', str),
                           ('planted', float),
                           ('harvested', float),
                           ('produced', float),
                           ('yield', float),
                           ('production_unit', str),
                           ('yield_unit', str)))

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(Production, self).__init__(df=df, fpath=fpath, columns=columns)


class Fertilizer(Data):

    COLUMNS = OrderedDict((('resource', str),
                           ('type', str),
                           ('chemical_id', str),
                           ('pollutant', str),
                           ('emission_factor', float)))

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(Fertilizer, self).__init__(df=df, fpath=fpath, columns=columns)


class EmissionFactor(Data):

    COLUMNS = OrderedDict((('resource', str),
                           ('type', str),
                           ('pollutant', str),
                           ('rate', float)))

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(EmissionFactor, self).__init__(df=df, fpath=fpath, columns=columns)


class FugitiveDust(Data):

    COLUMNS = OrderedDict((('feedstock', str),
                           ('tillage_type', str),
                           ('source_category', str),
                           ('budget_year', int),
                           ('pollutant', str),
                           ('rate', float),
                           ('unit', str)))

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(FugitiveDust, self).__init__(df=df, fpath=fpath, columns=columns)


class SCC(Data):

    COLUMNS = OrderedDict((('name', str),
                           ('scc', str)))

    def __init__(self, df=None, fpath=None, columns=COLUMNS):
        super(SCC, self).__init__(df=df, fpath=fpath, columns=columns)
