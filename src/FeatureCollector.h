#ifndef _FEATURES_H__
#define _FEATURES_H__

#include <iostream>
#include <bits/stdc++.h>
#include <GlobalParams.h>

#define TOTAL_DIRECTIONS	6 // Five directions as {North, East, South, West, Local, PE input}

using namespace std;

#define CYCLES_SINCE_LAST_FLIT_INITIAL 1000 // currently set as reset cycles

/*
port_feature_t contains data for an particualar port of a particular router at a particular cycle.
Different VCs can be accessed by different indexes of vector. 
*/
typedef struct port_feature
{

	port_feature()
	{
		// Rx statistics
		buffer_capacity.resize(GlobalParams::n_virtual_channels, -1);
		buffer_status.resize(GlobalParams::n_virtual_channels, -1);
		cycles_since_last_flit.resize(GlobalParams::n_virtual_channels, CYCLES_SINCE_LAST_FLIT_INITIAL);
		
		// Tx statistics
		stalled_flits.resize(GlobalParams::n_virtual_channels, -1);
		transmitted_flits.resize(GlobalParams::n_virtual_channels, -1);
		cumulative_latency.resize(GlobalParams::n_virtual_channels, -1);
	}

	/*
	Resets counts for Tx statistics
	*/
	void reset_counts_for_tx()
	{
		stalled_flits.clear();
		transmitted_flits.clear();
		cumulative_latency.clear();

		stalled_flits.resize(GlobalParams::n_virtual_channels, 0);
		transmitted_flits.resize(GlobalParams::n_virtual_channels, 0);
		cumulative_latency.resize(GlobalParams::n_virtual_channels, 0);
	}

	// Rx statistics
	vector <int> buffer_capacity;	// Maximum size for the buffer
	vector <int> buffer_status;	// Current status of buffer i.e how much the buffer is free currently
	vector <int> cycles_since_last_flit; // Contains the number of cycles since the last flit. It is set as -1 initially
	
	// Tx statistics
	vector <int> stalled_flits; // Contains the number of rejected flits due to filled buffers
	vector <int> transmitted_flits; // Contains the number of flits transmitted at this cycle
	vector <int> cumulative_latency; // Contains the sum of latency of all the flits which were transmitted this cycle

	string print()
	{
		string op = "";
		for(int i = 0; i < GlobalParams::n_virtual_channels; i++)
		{
			op += to_string(buffer_capacity[i]) + ", ";
			op += to_string(buffer_status[i]) + ", ";
			op += to_string(cycles_since_last_flit[i]) + ", ";
			op += to_string(stalled_flits[i]) + ", ";
			op += to_string(transmitted_flits[i]) + ", ";
			op += to_string(cumulative_latency[i]);
		}
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
	int routed_flits;	// Contains the number of flits routed till now from the beginning of the simulation

	/*
	Resets counts for Tx statistics
	*/
	void reset_counts_for_tx()
	{
		for(int i = 0; i < TOTAL_DIRECTIONS - 2; i++)	// NSEW
			data[i].reset_counts_for_tx();
		data[TOTAL_DIRECTIONS - 1].reset_counts_for_tx(); // PE's Rx
	}


	string print()
	{
		string info = "";
		info += to_string(local_id) + ", ";
		// info += to_string(cycle) + ", ";
		// info += to_string(routed_flits);
		info += to_string(cycle);
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
