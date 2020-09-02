#include "LocalizerRouter.h"

using namespace std;

void LocalizerRouter::set_local_id(int _id)
{
	id = _id;
	x = id % GlobalParams::mesh_dim_y;
	y = id / GlobalParams::mesh_dim_y;
}

void LocalizerRouter::set_noc(NoC* _noc)
{
	noc = _noc;
	assert(x != -1);
	assert(y != -1);
	pe = (noc->t)[x][y]->pe;
}

void LocalizerRouter::set_localizer_grid(LocalizerRouter*** _localizer_grid)
{
	localizer_grid = _localizer_grid;
}

void LocalizerRouter::set_predictor(Predictor* _predictor)
{
	predictor = _predictor;
}

bool LocalizerRouter::is_empty(int port)
{
	assert(port < 4);
	assert(port > -1);
	return Tx[port].empty();
}

TrackerPacket LocalizerRouter::fetch_packet(int port)
{
	assert(port < 4);
	assert(port > -1);
	TrackerPacket tp = Tx[port].front();
	Tx[port].pop_front();
	return tp;
}

void LocalizerRouter::__update_timer()
{
	if(timeout)
		timeout--;
}

void LocalizerRouter::gather_packets()	// Injests at most one packet
{
 	__update_timer();
	bool prediction = false;
	assert(predictor != nullptr);
	prediction = predictor->predict(id, ROUTER_DIR_PE_RX);


	int cur_cycle = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;
	bool tester = (cur_cycle >= 5500);
	tester &= (id == 62);	// Manual triggering
	// tester &= false;
	if(cur_cycle > 5500)
		tester &= prediction;
	
	if(tester && !timeout)
	{
		timeout = TIMEOUT;	// Reset timer to prevent unneccessary packet generation
		LOG << "ATTACK SUSPECTED" << endl;
		Rx.push_front(TrackerPacket());
		return;
	}

	if(!timeout && false)
	{
		if(prediction)
		{
			timeout = TIMEOUT;	// Reset timer to prevent unneccessary packet generation
			LOG << "ATTACK SUSPECTED" << endl;
			Rx.push_front(TrackerPacket());
			return;
		}
	}

	int other_x = x;
	int other_y = y;
	int other_port = -1;
	int other_id = id;

	// North of me
	other_y = y - 1;
	other_x = x;
	other_port = ROUTER_DIR_SOUTH;
	other_id = other_y * GlobalParams::mesh_dim_y + other_x;
	if(other_y >= 0)
	{
		if(!(localizer_grid[other_x][other_y]->is_empty(other_port)))
		{
			LOG << "Injesting from " << other_id << " from north" << endl;
			Rx.push_front(localizer_grid[other_x][other_y]->fetch_packet(other_port));
			return;
		}
	}

	// South of me
	other_y = y + 1;
	other_x = x;
	other_port = ROUTER_DIR_NORTH;
	other_id = other_y * GlobalParams::mesh_dim_y + other_x;
	if(other_y < GlobalParams::mesh_dim_y)
	{
		if(!(localizer_grid[other_x][other_y]->is_empty(other_port)))
		{
			LOG << "Injesting from " << other_id << " from south" << endl;
			Rx.push_front(localizer_grid[other_x][other_y]->fetch_packet(other_port));
			return;
		}
	}

	// East of me
	other_y = y;
	other_x = x + 1;
	other_port = ROUTER_DIR_WEST;
	other_id = other_y * GlobalParams::mesh_dim_y + other_x;
	if(other_x < GlobalParams::mesh_dim_x)
	{
		if(!(localizer_grid[other_x][other_y]->is_empty(other_port)))
		{
			LOG << "Injesting from " << other_id << " from east" << endl;
			Rx.push_front(localizer_grid[other_x][other_y]->fetch_packet(other_port));
			return;
		}
	}

	// West of me
	other_y = y;
	other_x = x - 1;
	other_port = ROUTER_DIR_EAST;
	other_id = other_y * GlobalParams::mesh_dim_y + other_x;
	if(other_x >= 0)
	{
		if(!(localizer_grid[other_x][other_y]->is_empty(other_port)))
		{
			LOG << "Injesting from " << other_id << " from east" << endl;
			Rx.push_front(localizer_grid[other_x][other_y]->fetch_packet(other_port));
			return;
		}
	}
}

void LocalizerRouter::__route(TrackerPacket tp)
{
	int port = -1;
	bool routed = false;

	// North
	port = ROUTER_DIR_NORTH;
	if(y > 0)
	{
		if(predictor->predict(id, port))
		{
			LOG << "Forwarding to north" << endl;
			Tx[port].push_back(tp);
			routed = true;
		}
	}

	// South
	port = ROUTER_DIR_SOUTH;
	if(y < GlobalParams::mesh_dim_y - 1)
	{
		predictor->predict(id, port);
		if(predictor->predict(id, port))
		{
			LOG << "Forwarding to south" << endl;
			Tx[port].push_back(tp);
			routed = true;
		}
	}
	
	// East
	port = ROUTER_DIR_EAST;
	if(x < GlobalParams::mesh_dim_x - 1)
	{
		if(predictor->predict(id, port))
		{
			LOG << "Forwarding to east" << endl;
			Tx[port].push_back(tp);
			routed = true;
		}
	}
	
	// West
	port = ROUTER_DIR_WEST;
	if(x > 0)
	{
		if(predictor->predict(id, port))
		{
			LOG << "Forwarding to west" << endl;
			Tx[port].push_back(tp);
			routed = true;
		}
	}

	if(!routed)
		LOG << "Digested packet" << endl;
	
	if(!routed && timeout == TIMEOUT)	// This means that a packet was generated at current cycle by it wasn't forwarded. Maybe a false +ve. Henece allow generation on next cycle as well.
	{
		timeout = 0;
		LOG << "False trigger" << endl;
	}
}


bool LocalizerRouter::__cycle_present(TrackerPacket tp)
{
	for(int r : tp)
	{
		if(r == id)
			return true;
	}
	return false;
}

void LocalizerRouter::__stop_current()
{
	pe->disable = true;
	stop = true;
	LOG << "Disabled " << id << endl;
}

void LocalizerRouter::__stop_cycle(TrackerPacket tp)
{
	__stop_current();
	for(int other_id : tp)
	{
		int other_x = other_id % GlobalParams::mesh_dim_y;
		int other_y = other_id / GlobalParams::mesh_dim_y;

		(noc->t)[other_x][other_y]->pe->disable = true;
		localizer_grid[other_x][other_y]->stop = true;

		LOG << "Disabled " << other_id << endl;
 	}
}

void LocalizerRouter::__clean_Rx()
{
	bool at_least_one_saved = false;
	list <TrackerPacket> saved;
	for(TrackerPacket tp : Rx)
	{
		if(tp.size())
		{
			at_least_one_saved = true;
			saved.push_back(tp);
		}
		else if(!at_least_one_saved)
		{
			at_least_one_saved = true;
			saved.push_back(tp);
		}
	}

	Rx.clear();
	for(TrackerPacket tp : saved)
		Rx.push_back(tp);
}

void LocalizerRouter::__forward_packet(TrackerPacket tp)
{
	bool local_IP_output_conjested = predictor->predict(id, ROUTER_DIR_LOCAL);
	if(local_IP_output_conjested)
	{
		// Current IP is an attacker
		LOG << "Local IP is attacker" << endl;
		bool local_IP_input_conjested = predictor->predict(id, ROUTER_DIR_PE_RX);
		if(local_IP_input_conjested)
		{
			// Cyclic attacker
			if(__cycle_present(tp))
			{
				// Cycle completed
				LOG << "Complete cycle detected. Stopping" << endl;
				__stop_cycle(tp);
			}
			else
			{
				// Cycle not completed
				LOG << "Partial cycle detected. Routing" << endl;
				tp.push_back(id);	// Add cuurent id
				__route(tp);
			}
		}
		else
		{
			// Generic attacker
			LOG << "Local IP is generic attacker. Stopping" << endl;
			__stop_current();
		}
	}
	else
	{
		// Current IP is not an attacker
		LOG << "Local IP not an attacker. Routing packet" << endl;
		__route(tp);
	}
}


void LocalizerRouter::transmit_packets()
{
	__clean_Rx();

	if(Rx.empty())
		return;

	TrackerPacket tp = Rx.front();
	Rx.pop_front();

	if(stop)
	{
		// Router flagged as attacker
		LOG << "Received packet after stopping." << endl;
		if(tp.size())
		{
			// Forward if cycle type
			LOG << "Cycle type. Forwarding" << endl;
			__forward_packet(tp);
		}
		else
			LOG << "Normal type. Digesting" << endl;
	}
	else
		__forward_packet(tp);
}