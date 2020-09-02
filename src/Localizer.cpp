#include "Localizer.h"

using namespace std;

void Localizer::setup_grid()
{

	// Return if localization is not enabled
	if(GlobalParams::weights_file_name == NO_LOCALIZATION)
		return;
	if(GlobalParams::accuracy_op_file_name == NO_ACCURACY_OP)
		return;


	localizer_grid = new LocalizerRouter**[GlobalParams::mesh_dim_x];
	for(int x = 0; x < GlobalParams::mesh_dim_x; x++)
	{
		localizer_grid[x] = new LocalizerRouter*[GlobalParams::mesh_dim_y];
		for(int y = 0; y < GlobalParams::mesh_dim_y; y++)
		{
			int id = y * GlobalParams::mesh_dim_y + x;
			string loc_name = "LocalizerRouter[" + to_string(x) + "][" + to_string(y) + "]_#" + to_string(id);
			localizer_grid[x][y] = new LocalizerRouter(loc_name.c_str());
			localizer_grid[x][y]->set_local_id(id);
			localizer_grid[x][y]->set_noc(noc);
			localizer_grid[x][y]->set_localizer_grid(localizer_grid);
			localizer_grid[x][y]->set_predictor(predictor);			
		}
	}
}

void Localizer::run_localization()
{
	// Return if localization is not enabled
	if(GlobalParams::weights_file_name == NO_LOCALIZATION)
		return;
	if(GlobalParams::accuracy_op_file_name == NO_ACCURACY_OP)
		return;


	if(reset.read())
		return;
	
	// Fetch packets
	for(int x = 0; x < GlobalParams::mesh_dim_x; x++)
		for(int y = 0; y < GlobalParams::mesh_dim_y; y++)
			localizer_grid[x][y]->gather_packets();
	
	// Route packets
	for(int x = 0; x < GlobalParams::mesh_dim_x; x++)
		for(int y = 0; y < GlobalParams::mesh_dim_y; y++)
			localizer_grid[x][y]->transmit_packets();
}

void Localizer::__test_run_localization()
{
	// Return if localization is not enabled
	if(GlobalParams::weights_file_name == NO_LOCALIZATION)
		return;
	if(GlobalParams::accuracy_op_file_name == NO_ACCURACY_OP)
		return;

	if(reset.read())
	{
		// reset state
	}
	else
	{
		int cur_cycle = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;
		if(cur_cycle == 1001)
		{
			LOG << "yella" << endl;
			LOG << (noc->t)[2][1]->r->current_features.print() << endl;
			LOG << "Yo!" << endl;
		}
		if(cur_cycle == 5002)
			(noc->t)[7][0]->pe->disable = true;
	}
}