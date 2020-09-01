#include "Predictor.h"

using namespace std;

// std::istream& operator>>(std::istream& inp_stream, CSVParser& data)
// {
// 	data.read_line(inp_stream);
// 	return inp_stream;
// }

void Predictor::setup()
{
	// Setup feature parsers
	parser = new FeatureParser("FeatureParser");
	parser->set_noc(noc);

	// Setup operations
	ifstream accuracy_op(GlobalParams::accuracy_op_file_name);
	while(accuracy_op >> csvparser)
	{
		int rtr_id = stoi(csvparser[0]);
		int port = stoi(csvparser[1]);
		bool op = (bool)stoi(csvparser[2]);

		operations[make_pair(rtr_id, port)] = op;	// Append to operations
	}

	// Setup weights
	ifstream weights_file(GlobalParams::weights_file_name);
	while(weights_file >> csvparser)
	{
		int rtr_id = stoi(csvparser[0]);
		int dir = stoi(csvparser[1]);

		vector <float> w; // Read weights
		for(int idx = 2; idx < (int)csvparser.size(); idx++)
			w.push_back(stof(csvparser[idx]));
		
		weights[make_pair(rtr_id, dir)] = w;	// Append to weights
	}

	// Setup perceptron grid
	for(int x = 0; x < GlobalParams::mesh_dim_x; x++)
	{
		perceptron_grid.push_back(vector <pair <Perceptron*, Perceptron*>>());
		for(int y = 0; y < GlobalParams::mesh_dim_y; y++)
		{
			int rtr_id = y * GlobalParams::mesh_dim_y + x;
			string input_name = "Perceptron[" + to_string(x) + "][" + to_string(y) + "]_#" + to_string(rtr_id) + "_input";
			string output_name = "Perceptron[" + to_string(x) + "][" + to_string(y) + "]_#" + to_string(rtr_id) + "_output";
			perceptron_grid[x].push_back(make_pair(new Perceptron(input_name.c_str()), new Perceptron(output_name.c_str())));
			if(weights.find(make_pair(rtr_id, 1)) != weights.end())
	 			perceptron_grid[x][y].first->set_weights(weights[make_pair(rtr_id, 1)]);	// Input one
			if(weights.find(make_pair(rtr_id, 0)) != weights.end())
				perceptron_grid[x][y].second->set_weights(weights[make_pair(rtr_id, 0)]);	// Output one
		}
	}

}

bool Predictor::predict(int router, int port)
{

	int dbg_cycle = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;
	bool dbg = dbg_cycle == 5020;
	dbg &= router == 55;
	dbg &= port == 0;
	dbg &= false;
	if(dbg)
		LOG << "debugging" << endl;

	if(dbg)
		LOG << "router, port " << router << ", " << port << endl;

	int router_x = router % GlobalParams::mesh_dim_y;
	int router_y = router / GlobalParams::mesh_dim_y;

	// Calculate other router
	pair <int, int> other = __get_output_router(router, port);
	int other_x = other.first;
	int other_y = other.second;

	// Fetch features
	vector <int> port_features = parser->get_features(router, port);

	if(dbg)
		LOG << "Got features" << endl;
	if(dbg)
	{
		string dbgstr = "";
		for(int v: port_features)
			dbgstr += to_string(v) + " ";
		LOG << "Features are: " << dbgstr << endl;
	}

	// Get predictions
	bool input_prediction = perceptron_grid[router_x][router_y].first->get_prediction(port_features);
	if(dbg)
		LOG << "Got IP prediction " << input_prediction << endl;
	// if(dbg)
		// LOG << "I predict: " << input_prediction << endl;
	if(router_x == other_x && router_y == other_y)
		return input_prediction;	// Handle case of loacal PE, local PE's Rx. In both cases, router is same. No need to fuse.		

	if(dbg)
		LOG << "Other is " << other_x << "," << other_y << endl;

	if(dbg)
		LOG << "Trying for op prediction" << endl;
	bool output_prediction = perceptron_grid[other_x][other_y].second->get_prediction(port_features);
	if(dbg)
		LOG << "Got op prediction " << output_prediction << endl;

	if(dbg)
		LOG << "Operation: " << operations[make_pair(router, port)] << endl;
	// Fuse predictions
	bool fused_prediction = false;
	if(operations[make_pair(router, port)])
		fused_prediction = input_prediction && output_prediction;
	else
		fused_prediction = input_prediction || output_prediction;

	if(dbg)
		LOG << "Returning" << endl;

	return fused_prediction;
}

pair <int, int> Predictor::__get_output_router(int router, int port)
{
	// Find x and y coordinates
	int router_x = router % GlobalParams::mesh_dim_y;
	int router_y = router / GlobalParams::mesh_dim_y;

	int other_x = router_x;
	int other_y = router_y;

	// Calculate neighbour
	switch(port)
	{
		case DIRECTION_NORTH:
			other_y--;
			break;
		case DIRECTION_SOUTH:
			other_y++;
			break;
		case DIRECTION_EAST:
			other_x++;
			break;
		case DIRECTION_WEST:
			other_x--;
			break;
	}

	// Manage mesh boundary; This should never happen
	if(other_x < 0 || other_x > GlobalParams::mesh_dim_x)
		assert(false);
	if(other_y < 0 || other_y > GlobalParams::mesh_dim_y)
		assert(false);


	return make_pair(other_x, other_y);
}

void Predictor::__tester()
{
	LOG << "Called __tester" << endl;
	LOG << "Weights are: " << endl;
	for(pair <pair <int, int>, vector <float>> kv : weights)
	{
		string op  = "";
		op += to_string(kv.first.first) + ", " + to_string(kv.first.second) + "\t->\t";
		for(int idx = 0; idx < (int)kv.second.size() - 1; idx++)
			// LOG << kv.second[idx] << ", ";
			op += to_string(kv.second[idx]) + ", ";
		op += to_string(kv.second[kv.second.size() -  1]);
		LOG << op << endl;
	}

	LOG << "Operations are: " << endl;
	for(pair <pair <int, int>, bool> kv : operations)
	{
		LOG << kv.first.first << ", " << kv.first.second << "\t->\t" << kv.second << endl;
	}
}