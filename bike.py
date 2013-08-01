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
import webbrowser


RIDEDB = os.path.expanduser('~/.bikerides')
#RIDEDB = 'rides'
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
    "Ride URL (optional): ": "URL de l'itinéraire (optionnel) : ",
    "stats": "stats",
    "add": "add",
    "Date": "Date",
    "Distance": "Distance",
    "Duration": "Durée",
    "Comment": "Commentaire",
    "Speed": "Vitesse",
    "dd/mm/yyyy hh:mm": "jj/mm/aaaa hh:mm",
    "Error: no URL for ride {}": "Erreur: pas d'URL pour la randonnée {}",
    "Opened %s": "Ouverture de %s",
    "User interrupted program, no changes were recorded in the "
    "database.": "L'usager a interrompu le programme, aucun changement "
                 "enregistré dans la base de données."
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

    Accepted formats are a float that specify the number of hours, HH:MM,
    HHhMM, HHh, or HH:.

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
        hours_and_minutes = duration_str.split(sep)
        if len(hours_and_minutes) == 2:
            hours, minutes = hours_and_minutes
        elif len(hours_and_minutes) == 1:
            hours, minutes = hours_and_minutes[0], 0.0
        else:
            raise ValueError('Invalid duration string')
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
    url = input(_("Ride URL (optional): "))

    rides_file = open(RIDEDB, 'a')
    rides_file.write('|||'.join([time.strftime(TIMESTR, timestamp),
                               str(distance), str(duration), comment, url])
                     + '\n')
    rides_file.close()


def read_db_file(sep='|||'):
    """Read ride data file and store information in a list of dictionaries.

    """
    rides = []
    for line in open(RIDEDB):
        tokens = line.split(sep)
        ride = {'timestamp': time.strptime(tokens[0], TIMESTR),
                'distance': float(tokens[1]),
                'duration': float(tokens[2])}
        if sep == ' ':
            ride['comment'] = ' '.join(tokens[3:]).strip()
            ride['url'] = ''
        else:
            ride['comment'] = tokens[3].strip()
            ride['url'] = tokens[4].strip()
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
    comment_width = 30
    header_format = '{id:4s}  {0:16s}  {1:%ds}  {2:%ds}  {3:%ds}  {4:%ds}  {5:3s}' % (
            len(_('Distance')), len(_('Duration')), len(_('Speed')),
            comment_width)
    ride_format = '{id:4d}  {0:16s}  {1:%d.1f}  {2:%d.1f}  {3:%d.1f}  {4:%ds}  {5:3d}' % (
            len(_('Distance')), len(_('Duration')), len(_('Speed')),
            comment_width)
    sep_format = '{id:=<4s}  {0:=<16s}  {1:=<%ds}  {2:=<%ds}  {3:=<%ds}  {4:=<%ds}  {5:=<3s}' % (
            len(_('Distance')), len(_('Duration')), len(_('Speed')),
            comment_width)
    print(header_format.format(
        _('Date'), _('Distance'), _('Duration'), _('Speed'), _('Comment'),
        _('URL'), id='id'))
    print(header_format.format(
        _('dd/mm/yyyy hh:mm'), '(km)', '(h)', '(km/h)', '', '', id=''))
    print(sep_format.format('', '', '', '', '', '', id=''))
    for id, ride in enumerate(rides):
        if len(ride['comment']) <= comment_width:
            print(ride_format.format(
                time.strftime('%d/%m/%Y %H:%M', ride['timestamp']),
                ride['distance'], ride['duration'],
                ride['distance'] / ride['duration'], ride['comment'],
                ride['url'] != '',
                id=id))
        else:
            print(ride_format.format(
                time.strftime('%d/%m/%Y %H:%M', ride['timestamp']),
                ride['distance'], ride['duration'],
                ride['distance'] / ride['duration'], 
                ride['comment'][:comment_width - 3] + '...',
                ride['url'] != '',
                id=id))


def migrate(args):
    """Migrate the database file to new version."""
    rides = read_db_file(sep=' ')
    rides_file = open(RIDEDB, 'w')
    for ride in rides:
        rides_file.write('|||'.join([time.strftime(TIMESTR, ride['timestamp']),
                                   str(ride['distance']), str(ride['duration']),
                                   ride['comment'], ride['url']])
                         + '\n')
    rides_file.close()


def view(args):
    """View ride URL in default browser."""
    rides = read_db_file()
    if rides[args.ride_id]['url']:
        print(_('Opened %s') % rides[args.ride_id]['url'])
        webbrowser.open(rides[args.ride_id]['url'])
    else:
        print(_('Error: no URL for ride {}').format(args.ride_id), file=sys.stderr)


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

    migrateparser = subparsers.add_parser(_('migrate'),
                                          help=_('migrate rides file'))
    migrateparser.set_defaults(func=migrate)

    viewparser = subparsers.add_parser(_('view'),
                                          help=_('view ride in web browser'))
    viewparser.add_argument('ride_id', help='numerical id of the ride to view',
                            type=int)
    viewparser.set_defaults(func=view)

    args = clparser.parse_args(argv)
    if not 'func' in args:
        clparser.error("You must specify one of 'add', 'rides', 'stats', or 'view'")

    try:
        args.func(args)
    except ValueError as e:
        print(_("Error: {}").format(e), file=sys.stderr)
    except KeyboardInterrupt as e:
        print("\n" + _("User interrupted program, no changes were recorded "
                       "in the database."),
              file=sys.stderr)


if __name__ == '__main__':
    init_locale()
    run()
