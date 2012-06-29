#!/usr/bin/env python3
#-*- coding: utf-8 -*-
"""
bike
====

This command line tool maintains a simple database of bike rides. For each
ride, the distance and the duration are stored. It is then possible to ask
``bike`` to calculate simple statistics for the rides.

The database is stored in a plain text file called ``.bikerides`` located in
the users home folder. It has a very simple structure. Each ride takes a single
line. The first column is the timestamp, the second column is the distance in
kilometers, the third column is the time in hours and the rest of the line is
considered a comment.

Here is an example file::

    23/06/2012-15:32:12 12 0.60 Around the house
    23/06/2012-15:32:12 75 4.00 Commute to work

The timestamp is the date and time at which the ride was added to the database.
It is added automatically by the script but can be modified as needed using any
text editor.

"""


from __future__ import print_function


__author__ = "Loïc Séguin-C. <loicseguin@gmail.com>"
__license__ = "BSD"
__version__ = '0.1'


import argparse
import locale
import os
import sys
import time


RIDEDB = os.path.expanduser('~/.bikerides')
TIMESTR = "%d/%m/%Y-%H:%M:%S"
MINUTES_PER_HOUR = 60.


FR_DICT = {
    "Distance: %6.1f km": "Distance : %6.1f km",
    "Duration: %6.1f h": "Durée : %6.1f h",
    "Average speed: %6.2f km/h": "Vitesse moyenne : %6.2f km/h",
    "Gather statistics about bike rides.":
        "Collecte des données sur des randonnées à bicyclette.",
    "add a new ride": "ajouter une nouvelle randonnée",
    "print statistics about all rides": "imprimer les statistiques",
    "Enter distance: ": "Entrer la distance : ",
    "Enter duration: ": "Entrer la durée : ",
    "Comment (optional): ": "Commentaire (optionnel) : ",
    "stats": "stats",
    "add": "add",
    "Date": "Date",
    "Distance": "Distance",
    "Duration": "Durée",
    "Comment": "Commentaire"
    }
TRANS_DICT = {}


try:
    if raw_input:
        input = raw_input
except NameError:
    pass


def init_locale():
    """Set the locale to the user's preference."""
    locale.setlocale(locale.LC_ALL, '')
    lang = locale.getlocale()[0][:2]
    global TRANS_DICT
    if lang == 'fr':
        TRANS_DICT = FR_DICT


def _(astring):
    """Translate ``astring`` to the current locale if translation is
    available."""
    return TRANS_DICT.get(astring, astring)


def parse_duration(duration_str):
    """Parse a string that represents a duration.

    Accepted formats are a float that specified the number of hours, HH:MM or
    HHhMM.

    """
    duration_str = duration_str.strip()
    try:
        duration = float(duration_str)
    except ValueError:
        if ':' in duration_str:
            sep = ':'
        elif 'h' in duration_str:
            sep = 'h'
        else:
            raise ValueError('Invalid duration string')
        hours, minutes = duration_str.split(sep)
        duration = float(hours) + float(minutes) / MINUTES_PER_HOUR
    return duration


def add_ride(args):
    """Add a ride to the database.

    Let the user interactively specify the distance and the time as well as an
    optional comment.

    """
    timestamp = time.localtime()
    distance = float(input(_("Enter distance: ")))
    duration = parse_duration(input(_("Enter duration: ")))
    comment = input(_("Comment (optional): "))

    rides_file = open(RIDEDB, 'a')
    rides_file.write(' '.join([time.strftime(TIMESTR, timestamp),
                               str(distance), str(duration), comment])
                     + '\n')
    rides_file.close()


def read_db_file():
    """Read ride data file and store information in a list of dictionaries.

    """
    rides = []
    for line in open(RIDEDB):
        tokens = line.split()
        ride = {'timestamp': time.strptime(tokens[0], TIMESTR),
                'distance': float(tokens[1]),
                'duration': float(tokens[2]),
                'comment': ' '.join(tokens[3:])}
        rides.append(ride)
    return rides


def print_stats(args):
    """Print statistics about the rides."""
    rides = read_db_file()
    tot_distance = 0.0
    tot_duration = 0.0
    for ride in rides:
        tot_distance += ride['distance']
        tot_duration += ride['duration']
    print(_("Distance: %6.1f km") % tot_distance)
    print(_("Duration: %6.1f h") % tot_duration)
    print(_("Average speed: %6.2f km/h") % (tot_distance / tot_duration))


def print_rides(args):
    """Print all rides in database."""
    rides = read_db_file()
    print('{0:16s}  {1:13s}  {2:13s}  {3:30s}'.format(
          _('Date'), _('Distance') + ' (km)', _('Duration') + ' (h)', _('Comment')))
    print('{0:=<16s}  {1:=<13s}  {2:=<13s}  {3:=<30s}'.format('', '', '', ''))
    for ride in rides:
        print('{0:16s}  {1:13.1f}  {2:13.1f}  {3:30s}'.format(
            time.strftime('%d/%m/%Y %H:%M', ride['timestamp']),
            ride['distance'], ride['duration'], ride['comment']))


def run(argv=sys.argv[1:]):
    """Parse the command line arguments and run the appropriate command."""
    clparser = argparse.ArgumentParser(
            description=_('Gather statistics about bike rides.'))
    clparser.add_argument('-v', '--version', action='version',
            version='%(prog)s ' + __version__)

    subparsers = clparser.add_subparsers()
    statsparser = subparsers.add_parser(_('stats'),
            help=_('print statistics about all rides'))
    statsparser.set_defaults(func=print_stats)

    addparser = subparsers.add_parser(_('add'), help=_('add a new ride'))
    addparser.set_defaults(func=add_ride)

    printparser = subparsers.add_parser(_('rides'), help=_('print all rides'))
    printparser.set_defaults(func=print_rides)

    args = clparser.parse_args(argv)
    args.func(args)


if __name__ == '__main__':
    init_locale()
    run()
