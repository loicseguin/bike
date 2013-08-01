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

    23-06-2012 15:32:12,12,0.60,Around the house,
    23-08-2012 13:21:48,75,4.00,"Commute to work, with visit at grocery",http://www.mymap.com/1234
    23-11-2012 20:10:35,24,1.25,,http://www.yourmap.com/4321

The timestamp is the date and time at which the ride was added to the database.
It is added automatically by the script but can be modified as needed using any
text editor.
