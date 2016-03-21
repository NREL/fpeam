"""
Functions associated with allocation
"""


class Allocate(object):
    """
    The 'Allocate' class is used to write spatial indicators to .alo file for the NonRoad program to use. 
    File are written on a state-level basis. 
    """
    def __init__(self, cont):
        """
        :param cont: Container object
        """

        self.path = cont.get('path') + 'ALLOCATE/'
        self.episode_year = None
        self.run_code = None
        self.indicator_total = 0
        self.alo_file = None

    def initialize_alo_file(self, state, run_code, episode_year):
        self.episode_year = episode_year
        self.run_code = run_code
        # total harvested acre per a state.
        self.indicator_total = 0.0   # acres
        self.alo_file = open('{path}{state}_{run_code}.alo'.format(path=self.path, state=state, run_code=run_code), 'w')
        lines = """
------------------------------------------------------------------------
This is the packet that contains the allocation indicator data.  Each
indicator value is a measured or projected value such as human
population or land area.  The format is as follows.

1-3    Indicator code
6-10   FIPS code (can be global FIPS codes e.g. 06000 = all of CA)
11-15  Subregion code (blank means is entire nation, state or county)
16-20  Year of estimate or prediction
21-40  Indicator value
41-45  Blank (unused)
46+    Optional Description (unused)
------------------------------------------------------------------------
/INDICATORS/
""" 
        self.alo_file.writelines(lines)

    def write_indicator(self, fips, indicator):
        """
        Allocates land usage for each county.
        This function writes the appropriate information to each line of the file
        The indicator value is grabbed from the database in Options.py
        @param fips: County code.
        @param indicator: Harvested acres per a county.
        """
        # FR data is in produce, not acres. Need to convert into land use.
        if self.run_code.startswith('FR'):
            # convert input -> dry ton_s into cubic feet
            # (x dry_ton) * (2000 lbs / ton) * (1 ft^3 / 30 lbs) --> BT2 Report page 18 footnote.
            indicator = float(indicator) * 2000.0 * 1.0 / 30.0
            lines = """LOG  %s      %s    %s\n""" % (fips, self.episode_year, indicator)
        # add harvested acres directly to file.
        else:
            lines = """FRM  %s      %s    %s\n""" % (fips, self.episode_year, indicator)

        self.alo_file.writelines(lines)

#        print indicator, fips
        self.indicator_total += float(indicator)

    def write_sum_and_close(self, fips):
        """
        This function finishes off the .alo file

        :param fips: fips code for geographic region
        :return:
        """

        if self.run_code.startswith('FR'):
            _ = 'LOG'
        else:
            _ = 'FRM'

        # @TODO: convert to use proper string formating with spaces, etc
        lines = """%s  %s000      %s    %s\n/END/""" % (_, fips[0:2], self.episode_year, self.indicator_total)

        self.alo_file.writelines(lines)

        self.alo_file.close()
