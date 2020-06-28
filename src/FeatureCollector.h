#ifndef _FEATURES_H__
#define _FEATURES_H__

#include <iostream>
#include <bits/stdc++.h>
#include <GlobalParams.h>

#define TOTAL_DIRECTIONS	5 // Five directions as {North, East, South, West, Local}

using namespace std;

/*
port_feature_t contains data for an particualar port of a particular router at a particular cycle
*/
typedef struct port_feature
{
	port_feature() : buffer_capacity(-1), buffer_status(-1) , cycles_since_last_packet(-1) { };
	
	int buffer_capacity;	// Maximum size for the buffer
	int buffer_status;	// Current status of buffer i.e how much the buffer is filled currently
	int cycles_since_last_packet; // Contains the number of cycles since the last packet. It is set as -1 initially

	string print()
	{
		return to_string(buffer_capacity) + ", " + to_string(buffer_status) + ", " + to_string(cycles_since_last_packet);
	}
} port_feature_t;

/*
Every router inserts one instance of Feature_t for every cycle.
*/
typedef struct Feature
{
	Feature() : cycle(-1), local_id(-1) { };

	port_feature_t data[TOTAL_DIRECTIONS];	// Features for individual ports
	int cycle;	// Cycle at which the feature was inserted
	int local_id;	// Local ID of the router which inserted this feature

	string print()
	{
		string info = "";
		info += to_string(local_id) + ", " +to_string(cycle);
		for(int i = 0; i < TOTAL_DIRECTIONS; i++)
			info += ", " + data[i].print();
		return info + "\n";
	} 

} Feature_t;


class FeatureCollector
{
	public:

		void testPrint();	// Prints features on stdout

		void exportFeatures();	// TODO: exports features to text files

		map < int, vector < Feature_t > > features; // Map between local_id of router and its features.
};

#endif
