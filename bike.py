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

    23/Jun/2012-15:32:12 12 0.60 Around the house
    23/Jun/2012-15:32:12 75 4.00 Commute to work

The timestamp is the date and time at which the ride was added to the database.

"""


from __future__ import print_function


__author__ = "Loïc Séguin-C. <loicseguin@gmail.com>"
__license__ = "BSD"
__version__ = '0.1'


import argparse
import os
import sys
import time


RIDEDB = os.path.expanduser('~/.bikerides')
TIMESTR = "%d/%b/%Y-%H:%M:%S"
MINUTES_PER_HOUR = 60.


try:
    if raw_input:
        input = raw_input
except NameError:
    pass


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
    distance = float(input("Enter distance: "))
    duration = parse_duration(input("Enter duration: "))
    comment = input("Comment (optional): ")

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
    """Print statistics about the rides.

    """
    rides = read_db_file()
    tot_distance = 0.0
    tot_duration = 0.0
    for ride in rides:
        tot_distance += ride['distance']
        tot_duration += ride['duration']
    print("Distance: %6.1f km" % tot_distance)
    print("Duration: %6.1f h" % tot_duration)
    print("Average speed: %6.2f km/h" % (tot_distance / tot_duration))


def run(argv=sys.argv[1:]):
    """Parse the command line arguments and run the appropriate command.

    """
    clparser = argparse.ArgumentParser(
            description='Gather statistics about bike rides.')
    clparser.add_argument('-v', '--version', action='version',
            version='%(prog)s ' + __version__)

    subparsers = clparser.add_subparsers()
    statsparser = subparsers.add_parser('stats',
            help='print statistics about all rides')
    statsparser.set_defaults(func=print_stats)

    addparser = subparsers.add_parser('add', help='add a new ride')
    addparser.set_defaults(func=add_ride)

    args = clparser.parse_args(argv)
    args.func(args)


if __name__ == '__main__':
    run()
