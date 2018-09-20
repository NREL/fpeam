from setuptools import setup

setup(
        name='fpeam',
        version='2.0.0-beta',
        packages=['FPEAM'],
        entry_points={'console_scripts': ['fpeam = FPEAM.scripts.fpeam:main']
                      }
)
