#!/usr/bin/env python3
"""
bike
====

This command line tool maintains a simple database of bike rides. For each
ride, the distance and the duration are stored. It is then possible to ask
``bike`` to calculate simple statistics for the rides.

The database is stored in a plain text CSV file called ``.bikerides`` located
in the users home folder. Each ride takes a single line. The first column is
the timestamp, the second column is the distance in kilometers, the third
column is the time in hours, the fourth column is a comment, and the fifth
column if a URL for the itinerary.

Here is an example file::

    2012-06-23 15:32:12,12,0.60,Around the house,
    2012-07-04 13:21:48,75,4.00,"Commute to work, with visit at grocery",http://www.mymap.com/1234
    2012-07-12 20:10:35,24,1.25,,http://www.yourmap.com/4321

The timestamp is the date and time at which the ride was added to the database.
It is added automatically by the script but can be modified as needed using any
text editor.

"""


from __future__ import print_function
import argparse
import datetime
import csv
import locale
import os
import sys
import time
import webbrowser

__author__ = "Loïc Séguin-C. <loicseguin@gmail.com>"
__license__ = "BSD"
__version__ = '0.2'


RIDEDB = os.path.expanduser('~/.bikerides')
TIMESTR = "%Y-%m-%d %H:%M:%S"
MINUTES_PER_HOUR = 60.
SECONDS_PER_HOUR = 3600.
KILO = 1000.


FR_DICT = {
    "Distance:      %8.2f km":   "Distance :        %8.2f km",
    "Duration:      %8.2f h":    "Durée :           %8.2f h",
    "Average speed: %s km/h": "Vitesse moyenne : %s km/h",
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
    "yyyy-mm-dd hh:mm": "aaaa-mm-jj hh:mm",
    "Error: no URL for ride {}": "Erreur: pas d'URL pour la randonnée {}",
    "Opened %s": "Ouverture de %s",
    "User interrupted program, no changes were recorded in the "
    "database.": "L'usager a interrompu le programme, aucun changement "
                 "enregistré dans la base de données.",
    "No rides for year(s): ": "Aucune randonnée pour ",
    "Error: no ride with index {}": "Erreur: aucune randonnée avec indice {}"
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


def add_ride(timestamp, distance, duration, comment='', url=''):
    """Add a ride to the database."""
    with open(RIDEDB, 'a') as rides_file:
        rides_writer = csv.writer(rides_file, delimiter=',', quotechar='"',
                                  quoting=csv.QUOTE_MINIMAL)
        rides_writer.writerow(
            [timestamp.strftime(TIMESTR),
             str(distance), str(duration), comment, url])


def add_ride_interactive(args):
    """Ask the user for information about ride to add to the database.

    Let the user interactively specify the distance and the time as well as an
    optional comment.

    """
    timestamp = datetime.datetime.now()
    distance = float(input(_("Enter distance: ")))
    duration = parse_duration(input(_("Enter duration: ")))
    comment = input(_("Comment (optional): "))
    url = input(_("Ride URL (optional): "))
    add_ride(timestamp, distance, duration, comment, url)


def read_wahoo_csv(args):
    """Get a ride information from a Wahoo csv file and add it to the
    database.

    """
    try:
        import pandas as pd
    except ImportError as e:
        print(_("Pandas must be installed to be able to import Wahoo "
                "CSV files."))
        return

    ride_info = pd.read_csv(args.filename)
    ride_info = ride_info[ride_info['WorkoutActive'] == True].iloc[[0, -1]]
    ride_info['Timestamp'] = pd.to_datetime(ride_info['Timestamp'], unit='ms')
    begining = ride_info.iloc[0]
    end = ride_info.iloc[-1]
    duration = (end['Timestamp'] -
                begining['Timestamp']).seconds / SECONDS_PER_HOUR
    distance = (end['TotalDistance'] - begining['TotalDistance']) / KILO
    timestamp = end['Timestamp'].to_datetime()
    if args.comment:
        comment = ' '.join(args.comment)
    else:
        comment = 'Imported from Wahoo'
    add_ride(timestamp, distance, duration, comment)


def read_db_file(sep=',', year=False):
    """Read ride data file and store information in a list of dictionaries.  By
    default, return only rides for the current year.  If ``year`` is set to a
    single year of a list of years, return rides for the specified years.

    """
    rides = []
    if not year:
        years = [time.localtime().tm_year]
    elif not hasattr(year, '__contains__'):
        years = [year]
    else:
        years = year

    with open(RIDEDB) as rides_file:
        rides_reader = csv.reader(rides_file, delimiter=sep, quotechar='"')
        for id, ride_row in enumerate(rides_reader):
            ride = {'timestamp': time.strptime(ride_row[0], TIMESTR),
                    'distance': float(ride_row[1]),
                    'duration': float(ride_row[2]),
                    'comment': ride_row[3],
                    'url': ride_row[4],
                    'id': id}
            if ride['timestamp'].tm_year in years:
                rides.append(ride)
    return rides


def print_stats(args):
    """Print statistics about the rides."""
    rides = read_db_file(year=args.year)
    if len(rides) == 0:
        print(_("No rides for year(s): ") + ', '.join(map(str, args.year)))
        return
    tot_distance = 0.0
    tot_duration = 0.0
    for ride in rides:
        tot_distance += ride['distance']
        tot_duration += ride['duration']
    if tot_duration != 0:
        speed = '{:8.2f}'.format(tot_distance / tot_duration)
    else:
        speed = 'nan'
    print(_("Distance:      %8.2f km") % tot_distance)
    print(_("Duration:      %8.2f h") % tot_duration)
    print(_("Average speed: %s km/h") % speed)


def print_rides(args):
    """Print rides in database.  By default, only print rides for the current
    year. If ``year`` is set to a single year of a list of years, print rides
    for the specified years.

    """
    rides = read_db_file(year=args.year)
    if len(rides) == 0:
        print(_("No rides for year(s): ") + ', '.join(map(str, args.year)))
        return
    comment_width = 30
    header_format = '{id:4s}  {0:16s}  {1:%ds}  {2:%ds}  {3:%ds}  {4:%ds}  {5:3s}' % (
            len(_('Distance')), len(_('Duration')), len(_('Speed')),
            comment_width)
    ride_format = '{id:4d}  {0:16s}  {1:%d.1f}  {2:%d.1f}  {3:>%ds}  {4:%ds}  {5:3d}' % (
            len(_('Distance')), len(_('Duration')), len(_('Speed')),
            comment_width)
    sep_format = '{id:=<4s}  {0:=<16s}  {1:=<%ds}  {2:=<%ds}  {3:=<%ds}  {4:=<%ds}  {5:=<3s}' % (
            len(_('Distance')), len(_('Duration')), len(_('Speed')),
            comment_width)
    print(header_format.format(
        _('Date'), _('Distance'), _('Duration'), _('Speed'), _('Comment'),
        _('URL'), id='id'))
    print(header_format.format(
        _('yyyy-mm-dd hh:mm'), '(km)', '(h)', '(km/h)', '', '', id=''))
    time_str_format = '%Y-%m-%d %H:%M'
    print(sep_format.format('', '', '', '', '', '', id=''))

    for id, ride in enumerate(rides):
        if ride['duration'] != 0:
            speed = '{:.1f}'.format(ride['distance'] / ride['duration'])
        else:
            speed = 'nan'
        elements = [time.strftime(time_str_format, ride['timestamp']),
                    ride['distance'], ride['duration'], speed]
        if len(ride['comment']) <= comment_width:
            elements.append(ride['comment'])
        else:
            elements.append(ride['comment'][:comment_width - 3] + '...')
        elements.append(ride['url'] != '')
        print(ride_format.format(*elements, id=ride['id']))


def migrate(args):
    """Migrate the database file to new version."""
    rides = read_db_file()
    new_time_str = "%Y-%m-%d %H:%M:%S"
    with open(RIDEDB, 'w') as rides_file:
        rides_writer = csv.writer(rides_file, delimiter=',', quotechar='"',
                                  quoting=csv.QUOTE_MINIMAL)
        for ride in rides:
            rides_writer.writerow(
                [time.strftime(new_time_str, ride['timestamp']),
                 str(ride['distance']), str(ride['duration']),
                 ride['comment'], ride['url']])


def view(args):
    """View ride URL in default browser."""
    rides = read_db_file(year=args.year)
    for ride in rides:
        if ride['id'] == args.ride_id:
            break
    else:
        print(_('Error: no ride with index {}').format(args.ride_id),
              file=sys.stderr)
        return
    if ride['url']:
        print(_('Opened %s') % ride['url'])
        webbrowser.open(ride['url'])
    else:
        print(_('Error: no URL for ride {}').format(args.ride_id),
              file=sys.stderr)


def run(argv=sys.argv[1:]):
    """Parse the command line arguments and run the appropriate command."""
    clparser = argparse.ArgumentParser(
            description=_('Gather statistics about bike rides.'))
    clparser.add_argument('-v', '--version', action='version',
                          version='%(prog)s ' + __version__)

    year_parser = argparse.ArgumentParser(add_help=False)
    year_parser.add_argument('year', help=_('year or list of years'),
                             nargs='*', default=time.localtime().tm_year,
                             type=int)

    subparsers = clparser.add_subparsers()
    statsparser = subparsers.add_parser(_('stats'),
                                        help=_('print statistics for all rides'),
                                        parents=[year_parser])
    statsparser.set_defaults(func=print_stats)

    addparser = subparsers.add_parser(_('add'), help=_('add a new ride'))
    addparser.set_defaults(func=add_ride_interactive)

    printparser = subparsers.add_parser(_('rides'), help=_('print all rides'),
                                        parents=[year_parser])
    printparser.set_defaults(func=print_rides)

    migrateparser = subparsers.add_parser(_('migrate'),
                                          help=_('migrate rides file'))
    migrateparser.set_defaults(func=migrate)

    viewparser = subparsers.add_parser(_('view'),
                                       help=_('view ride in web browser'),
                                       parents=[year_parser])
    viewparser.add_argument('ride_id', help='numerical id of the ride to view',
                            type=int)
    viewparser.set_defaults(func=view)

    importparser = subparsers.add_parser(_('import'),
                                         help=_('import ride from Wahoo csv'))
    importparser.add_argument('filename', help='file name to import')
    importparser.add_argument('comment', help='comment to add to ride',
                              nargs=argparse.REMAINDER)
    importparser.set_defaults(func=read_wahoo_csv)

    args = clparser.parse_args(argv)
    if 'func' not in args:
        clparser.error("You must specify one of 'add', 'rides', 'stats', "
                       "'view' or 'import'.")

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
