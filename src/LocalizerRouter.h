#ifndef _LOCALIZER_ROUTER_H_
#define _LOCALIZER_ROUTER_H_

#include <systemc>
#include "TrackerPacket.h"
#include "ProcessingElement.h"
#include "NoC.h"
#include "GlobalParams.h"
#include "Utils.h"
#include "Predictor.h"
#include <list>
#include <assert.h>

#define TIMEOUT	5000

#define ROUTER_DIR_NORTH	0
#define ROUTER_DIR_EAST		1
#define ROUTER_DIR_SOUTH	2
#define ROUTER_DIR_WEST		3
#define ROUTER_DIR_LOCAL	4	// PE -> Router
#define ROUTER_DIR_PE_RX	5	// Router-> PE

SC_MODULE(LocalizerRouter)
{
	list <TrackerPacket> Rx;	// Input packets are put into this buffer
	list <TrackerPacket> Tx[4];	// Output packets are out into these buffers
	bool stop = false;
	Predictor* predictor;
	ProcessingElement* pe;	// Used to stop PE
	NoC* noc;	// Used to get PE
	LocalizerRouter*** localizer_grid;	// Used to access neighbouring localizer_routers to fetch packets
	int id = -1;	// ID and coordinates
	int x = -1;
	int y = -1;

	int timeout = 0;	// Local IP is only checked if timeout = 0;

	void __route(TrackerPacket tp);	// Find the saturated ports and inserts packets in those lists
	void __update_timer();	// updates timeout
	bool __cycle_present(TrackerPacket tp);	// Check if cycle is present
	void __stop_cycle(TrackerPacket tp);	// Stops the PEs of all routers mentioned in tracker packet
	void __stop_current();	// Stops current router
	void __clean_Rx();	// Removes unneccessary packets. Only cycle packets are kept. If no cycle packets are available, at most one normal packet is kept
	void __forward_packet(TrackerPacket tp);	// Handles the main logic to forward packets

public:

	SC_CTOR(LocalizerRouter) {}

	// Called at setup
	void set_local_id(int _id);
	void set_noc(NoC* _noc);
	void set_localizer_grid(LocalizerRouter*** _localizer_grid);
	void set_predictor(Predictor* _predictor);
	
	// Called during localization by routers
	bool is_empty(int port);	// Checks if port queue is empty or not.
	TrackerPacket fetch_packet(int port);	// Fetches packets from port
	
	// Called by localizer
	void gather_packets();	// Calls neighbours and local IP to add packets to Rx list
	void transmit_packets();	// Updates Tx lists
};

#endif