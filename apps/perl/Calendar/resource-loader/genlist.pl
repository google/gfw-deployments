#!/usr/bin/perl

@locations = qw(US-CA US-WA US-NY US-MA US-DC);
@floors = qw(1 2 3 4 5 6 7 8 9);
@rooms = qw(Huge-300 Big-50 Medium-25 Small-10 Tiny-4);

my $id = 0;

foreach $loc (@locations) {
	foreach $fl (@floors) {
		foreach $room (@rooms) {
			# id,name,description,type
			my $name = $loc . "-FL" . $fl . "-" . $room;
			my $description = $name;

			print "id" . $id . "," . $name . "," . $description . "," . "Conference Room\n";

			$id++;
		}
	}
}
