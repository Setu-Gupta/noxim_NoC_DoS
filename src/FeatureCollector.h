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

	port_feature()
	{
		buffer_capacity.resize(GlobalParams::n_virtual_channels, -1);
		buffer_status.resize(GlobalParams::n_virtual_channels, -1);
		cycles_since_last_flit.resize(GlobalParams::n_virtual_channels, -1);
	}

	vector <int> buffer_capacity;	// Maximum size for the buffer
	vector <int> buffer_status;	// Current status of buffer i.e how much the buffer is free currently
	vector <int> cycles_since_last_flit; // Contains the number of cycles since the last flit. It is set as -1 initially

	string print()
	{
		string op = "";
		for(int i = 0; i < GlobalParams::n_virtual_channels; i++)
			op += to_string(buffer_capacity[i]) + ", " + to_string(buffer_status[i]) + ", " + to_string(cycles_since_last_flit[i]) + ", ";
		return op;
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
		int last_comma_idx = info.rfind(",");
		info = info.substr(0, last_comma_idx);	// Remove the last comma
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
