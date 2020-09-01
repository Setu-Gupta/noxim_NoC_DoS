#ifndef _FEATUREPARSER_H__
#define _FEATUREPARSER_H__

#include <systemc.h>
#include <vector>
#include <utility>
#include <assert.h>
#include "NoC.h"
#include "GlobalParams.h"
#include "FeatureCollector.h"

using namespace std;

#define FEATURE_COUNT	6
#define FEATURE_NORTH	0
#define FEATURE_EAST	1
#define FEATURE_SOUTH	2
#define FEATURE_WEST	3
#define FEATURE_LOCAL	4
#define FEATURE_PE_RX	5

#define PARSED_BUFFER_STATUS			0
#define PARSED_CYCLES_SINCE_LAST_FLIT	1
#define PARSED_STALLED_FLITS			2
#define PARSED_TRANSMITTED_FLITS		3
#define PARSED_BUFFER_WAITING_TIME		4

#define VC	0

SC_MODULE(FeatureParser)
{
	NoC* noc;

	pair <int, int> __get_neighbour(int router, int port);	// Helper function to find neighbour

public:
	SC_CTOR(FeatureParser) {}
	void set_noc(NoC* _noc);
	vector <int> get_features(int router, int port);	// Get parsed geatures for router and port
};

#endif