bike
====

This command line tool maintains a simple database of bike rides. For each
ride, the distance and the duration are stored. It is then possible to ask
`bike` to calculate simple statistics for the rides.

The database is stored in a plain text file called `.bikerides` located in
the users home folder. It has a very simple structure. Each ride takes a single
line. The first column is the timestamp, the second column is the distance in
kilometers, the third column is the time in hours and the rest of the line is
considered a comment.

Here is an example file:

    23/Jun/2012-15:32:12 12 0.60 Around the house
    23/Jun/2012-15:32:12 75 4.00 Commute to work

The timestamp is the date and time at which the ride was added to the database.
It is added automatically by the script but can be modified as needed using any
text editor.
