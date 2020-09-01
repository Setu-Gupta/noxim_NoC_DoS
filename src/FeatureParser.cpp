#include "FeatureParser.h"

vector <int> FeatureParser::get_features(int router, int port)
{

	Feature_t raw_features_current;
	Feature_t raw_features_neighbour;

	// Get neighbour
	int other_router, other_port;
	pair <int, int> neighbour = __get_neighbour(router, port);
	other_router = neighbour.first;
	other_port = neighbour.second;

	// Calculate x and y coordinates
	int router_x = router % GlobalParams::mesh_dim_y;
	int router_y = router / GlobalParams::mesh_dim_y;
	int other_x = other_router % GlobalParams::mesh_dim_y;
	int other_y = other_router / GlobalParams::mesh_dim_y;

	// Fetch raw features
	raw_features_current = (noc->t)[router_x][router_y]->r->current_features;
	raw_features_neighbour = (noc->t)[other_x][other_y]->r->current_features;

	// Store the features of the required ports
	vector <int> raw_features_current_port;
	vector <int> raw_features_neighbour_port;

	raw_features_current_port.push_back(raw_features_current.data[port].buffer_status[VC]);
	raw_features_current_port.push_back(raw_features_current.data[port].cycles_since_last_flit[VC]);
	raw_features_current_port.push_back(raw_features_current.data[port].stalled_flits[VC]);
	raw_features_current_port.push_back(raw_features_current.data[port].transmitted_flits[VC]);
	raw_features_current_port.push_back(raw_features_current.data[port].cumulative_latency[VC]);

	raw_features_neighbour_port.push_back(raw_features_neighbour.data[other_port].buffer_status[VC]);
	raw_features_neighbour_port.push_back(raw_features_neighbour.data[other_port].cycles_since_last_flit[VC]);
	raw_features_neighbour_port.push_back(raw_features_neighbour.data[other_port].stalled_flits[VC]);
	raw_features_neighbour_port.push_back(raw_features_neighbour.data[other_port].transmitted_flits[VC]);
	raw_features_neighbour_port.push_back(raw_features_neighbour.data[other_port].cumulative_latency[VC]);

	// Parse data 
	vector <int> output;
	output.push_back(1);	// This is done so that perceptron can calculate bias. the eqution becomes 1*bias + feature1*weight1 + ...
	// Rx features
	output.push_back(raw_features_current_port[PARSED_BUFFER_STATUS]);
	output.push_back(raw_features_current_port[PARSED_CYCLES_SINCE_LAST_FLIT]);
	// Tx features
	output.push_back(raw_features_neighbour_port[PARSED_STALLED_FLITS]);
	output.push_back(raw_features_neighbour_port[PARSED_TRANSMITTED_FLITS]);
	// Calculate avg latency
	int avg_latency = raw_features_neighbour_port[PARSED_BUFFER_WAITING_TIME];
	if(output[PARSED_TRANSMITTED_FLITS])
		avg_latency /= output[PARSED_TRANSMITTED_FLITS];
	output.push_back(avg_latency);

	return output;
}

pair <int, int> FeatureParser::__get_neighbour(int router, int port)
{
	// Find x and y coordinates
	int router_x = router % GlobalParams::mesh_dim_y;
	int router_y = router / GlobalParams::mesh_dim_y;

	int other_x = router_x;
	int other_y = router_y;
	int other_port = port;

	// Calculate neighbour
	switch(port)
	{
		case FEATURE_NORTH:
			other_y--;
			other_port = FEATURE_SOUTH;
			break;
		case FEATURE_SOUTH:
			other_y++;
			other_port = FEATURE_NORTH;
			break;
		case FEATURE_EAST:
			other_x++;
			other_port = FEATURE_WEST;
			break;
		case FEATURE_WEST:
			other_x--;
			other_port = FEATURE_EAST;
			break;
	}

	// Manage mesh boundary; This should never happen
	if(other_x < 0 || other_x > GlobalParams::mesh_dim_x)
		assert(false);
	if(other_y < 0 || other_y > GlobalParams::mesh_dim_y)
		assert(false);

	int other_router = other_y * GlobalParams::mesh_dim_y + other_x;

	return make_pair(other_router, other_port);
}

void FeatureParser::set_noc(NoC * _noc)
{
	noc = _noc;
}