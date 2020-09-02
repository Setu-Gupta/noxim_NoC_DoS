/*
 * Noxim - the NoC Simulator
 *
 * (C) 2005-2018 by the University of Catania
 * For the complete list of authors refer to file ../doc/AUTHORS.txt
 * For the license applied to these sources refer to file ../doc/LICENSE.txt
 *
 * This file contains the implementation of the processing element
 */

#include "ProcessingElement.h"

int ProcessingElement::randInt(int min, int max)
{
    return min +
	(int) ((double) (max - min + 1) * rand() / (RAND_MAX + 1.0));
}

void ProcessingElement::rxProcess()
{
    if (reset.read()) {
	ack_rx.write(0);
	current_level_rx = 0;
	dataAvailable = false;
	attack_pipeline_filled = false;
	
	// Initialize Rx features
	if(!features_setup)
	{
		cycles_since_last_flit.clear();
		cycles_since_last_flit.resize(GlobalParams::n_virtual_channels, CYCLES_SINCE_LAST_FLIT_INITIAL);
		features_setup = true;
	}
    } else {
	for(int vc = 0; vc < GlobalParams::n_virtual_channels; vc++)
	   	if(cycles_since_last_flit[vc] != INT_MAX)
	   		cycles_since_last_flit[vc]++;

	if (req_rx.read() == 1 - current_level_rx) {
	    Flit flit_tmp = flit_rx.read();
	    // receive(flit_tmp);


	    int vc = flit_tmp.vc_id;
	    if(!buffer_rx[vc].IsFull())
	   	{	
	   		buffer_rx[vc].Push(flit_tmp);
	   		LOG << "Received flit " << flit_tmp << endl;
	   		cycles_since_last_flit[vc] = 0;
	   		current_level_rx = 1 - current_level_rx;	// Negate the old value for Alternating Bit Protocol (ABP)
	   	}
	}
	receive();

	// Update buffer status
	TBufferFullStatus bfs;
	for (int vc=0;vc<GlobalParams::n_virtual_channels;vc++)
		bfs.mask[vc] = buffer_rx[vc].IsFull();
	buffer_full_status_rx.write(bfs);
	ack_rx.write(current_level_rx);
    }
}

void ProcessingElement::txProcess()
{
    if (reset.read()) {
	req_tx.write(0);
	current_level_tx = 0;
	transmittedAtPreviousCycle = false;
	data = -1;
	attack_started = false;
	attack_partner = -1;
    } else {
	Packet packet;

	if (canShot(packet) && !disable) {
	    packet_queue.push(packet);
	    transmittedAtPreviousCycle = true;
	} else
	    transmittedAtPreviousCycle = false;

	// Reset tx params
	transmitted_flits.clear();
	transmitted_flits.resize(GlobalParams::n_virtual_channels, 0);
	stalled_flits.clear();
	stalled_flits.resize(GlobalParams::n_virtual_channels, 0);
	cumulative_latency.clear();
	cumulative_latency.resize(GlobalParams::n_virtual_channels, 0);

	int now = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;
	__update_packet_queue();
	if(!packet_queue.empty() && ack_tx.read() == current_level_tx)
	{
		int vc = getNextVC();
		if(!buffer_full_status_tx.read().mask[vc])
		{
			Flit flit = nextFlit();	// Generate a new flit
			flit_tx->write(flit);	// Send the generated flit
			current_level_tx = 1 - current_level_tx;	// Negate the old value for Alternating Bit Protocol (ABP)
			req_tx.write(current_level_tx);
			transmitted_flits[vc]++;
			cumulative_latency[vc] += (now - flit.timestamp);
		}
		else
			stalled_flits[vc]++;
	}
	// if (ack_tx.read() == current_level_tx) {
	//     if (!packet_queue.empty()) {
	// 	Flit flit = nextFlit();	// Generate a new flit
	// 	flit_tx->write(flit);	// Send the generated flit
	// 	current_level_tx = 1 - current_level_tx;	// Negate the old value for Alternating Bit Protocol (ABP)
	// 	req_tx.write(current_level_tx);
	//     }
	// }
    }
}

int ProcessingElement::getNextVC()
{
	Packet packet = packet_queue.front();
	return packet.vc_id;
}

void ProcessingElement::__update_packet_queue()
{
	if(packet_queue.empty())
		return;
	Packet packet = packet_queue.front();
	if(packet.size == packet.flit_left)	// New packet
		if(disable)	// Clear packet queue
    		while(!packet_queue.empty())
    			packet_queue.pop();
}

Flit ProcessingElement::nextFlit()
{
    Flit flit;
    Packet packet = packet_queue.front();

    flit.src_id = packet.src_id;
    flit.dst_id = packet.dst_id;
    flit.vc_id = packet.vc_id;
    flit.timestamp = packet.timestamp;
    flit.sequence_no = packet.size - packet.flit_left;
    flit.sequence_length = packet.size;
    flit.hop_no = 0;
    flit.payload = packet.payload;

    flit.hub_relay_node = NOT_VALID;

    if (packet.size == packet.flit_left)
	flit.flit_type = FLIT_TYPE_HEAD;
    else if (packet.flit_left == 1)
	flit.flit_type = FLIT_TYPE_TAIL;
    else
	flit.flit_type = FLIT_TYPE_BODY;

    if(flit.flit_type == FLIT_TYPE_HEAD && flit.payload.type == PAYLOAD_MALICIOUS)
	LOG << "Sending MALICIOUS packet!" << endl;

    packet_queue.front().flit_left--;
    if (packet_queue.front().flit_left == 0)
    {
    	packet_queue.pop();
    	if(disable)	// Clear packet queue
    		while(!packet_queue.empty())
    			packet_queue.pop();
    }
	

    return flit;
}

bool ProcessingElement::canShot(Packet & packet)
{
   // assert(false);
    if(never_transmit) return false;
   
    //if(local_id!=16) return false;
    /* DEADLOCK TEST 
	double current_time = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;

	if (current_time >= 4100) 
	{
	    //if (current_time==3500)
	         //cout << name() << " IN CODA " << packet_queue.size() << endl;
	    return false;
	}
	//*/

#ifdef DEADLOCK_AVOIDANCE
    if (local_id%2==0)
	return false;
#endif
    bool shot;
    double threshold;

    double now = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;

    if (GlobalParams::traffic_distribution != TRAFFIC_TABLE_BASED) {
	if (!transmittedAtPreviousCycle)
	    threshold = GlobalParams::packet_injection_rate;
	else
	    threshold = GlobalParams::probability_of_retransmission;

	shot = (((double) rand()) / RAND_MAX < threshold);
	if (shot) {
	    if (GlobalParams::traffic_distribution == TRAFFIC_RANDOM)
		    packet = trafficRandom();
        else if (GlobalParams::traffic_distribution == TRAFFIC_TRANSPOSE1)
		    packet = trafficTranspose1();
        else if (GlobalParams::traffic_distribution == TRAFFIC_TRANSPOSE2)
    		packet = trafficTranspose2();
        else if (GlobalParams::traffic_distribution == TRAFFIC_BIT_REVERSAL)
		    packet = trafficBitReversal();
        else if (GlobalParams::traffic_distribution == TRAFFIC_SHUFFLE)
		    packet = trafficShuffle();
        else if (GlobalParams::traffic_distribution == TRAFFIC_BUTTERFLY)
		    packet = trafficButterfly();
        else if (GlobalParams::traffic_distribution == TRAFFIC_LOCAL)
		    packet = trafficLocal();
        else if (GlobalParams::traffic_distribution == TRAFFIC_ULOCAL)
		    packet = trafficULocal();
        else {
            cout << "Invalid traffic distribution: " << GlobalParams::traffic_distribution << endl;
            exit(-1);
        }
	}
    } else {			// Table based communication traffic
	if (never_transmit)
	    return false;

	bool use_pir = (transmittedAtPreviousCycle == false);
	vector < tuple < int, double, Payload > > dst_prob;
	double threshold =
	    traffic_table->getCumulativePirPor(local_id, (int) now, use_pir, dst_prob);

	double prob = (double) rand() / RAND_MAX;
	shot = (prob < threshold);
	int tmp_dst = -1;	// Temporary variable to store destination
	if (shot) {
	    for (unsigned int i = 0; i < dst_prob.size(); i++) {
		if (prob < get<1>(dst_prob[i])) {
                    int vc = randInt(0,GlobalParams::n_virtual_channels-1);
		    Payload pl = get<2>(dst_prob[i]);
		    packet.make(local_id, get<0>(dst_prob[i]), vc, now, getRandomSize(), pl);
		    tmp_dst = get<0>(dst_prob[i]);
		    break;
		}
	    }
	    if(packet.payload.type == PAYLOAD_MALICIOUS)
	    {
		    LOG << "Started MALICIOUS pipeline!" << endl;
		    assert(tmp_dst != -1);
		    attack_started = true;	// Start attack at first malicious payload
		    attack_partner = tmp_dst;	// Set the partner
	    }
	}

	// Fill malicioous pipeline
	if(attack_started && !attack_pipeline_filled)
	{
		assert(attack_partner != -1);
		Payload pl;	// Make payload 
		pl.data = 0;	// Initialize packet count
		pl.type = PAYLOAD_MALICIOUS;
       		int vc = randInt(0, GlobalParams::n_virtual_channels-1);
		packet.make(local_id, attack_partner, vc, now, getRandomSize(), pl);
		shot = true;
	}
	


    	//cout << "Shot value at cycle:" << (int) now << " is:" << (int) shot;
    	//if(shot)
    	//{
    	//        cout << "----------------------------------\n";
    	//}
    	//else
    	//{
    	//        cout << " threshold is:" << threshold << " prob is:" << prob << endl;
    	//}
    }

    return shot;
}


Packet ProcessingElement::trafficLocal()
{
    Packet p;
    p.src_id = local_id;
    double rnd = rand() / (double) RAND_MAX;

    vector<int> dst_set;

    int max_id = (GlobalParams::mesh_dim_x * GlobalParams::mesh_dim_y);

    for (int i=0;i<max_id;i++)
    {
	if (rnd<=GlobalParams::locality)
	{
	    if (local_id!=i && sameRadioHub(local_id,i))
		dst_set.push_back(i);
	}
	else
	    if (!sameRadioHub(local_id,i))
		dst_set.push_back(i);
    }


    int i_rnd = rand()%dst_set.size();

    p.dst_id = dst_set[i_rnd];
    p.timestamp = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;
    p.size = p.flit_left = getRandomSize();
    p.vc_id = randInt(0,GlobalParams::n_virtual_channels-1);
    
    return p;
}


int ProcessingElement::findRandomDestination(int id, int hops)
{
    assert(GlobalParams::topology == TOPOLOGY_MESH);

    int inc_y = rand()%2?-1:1;
    int inc_x = rand()%2?-1:1;
    
    Coord current =  id2Coord(id);
    


    for (int h = 0; h<hops; h++)
    {

	if (current.x==0)
	    if (inc_x<0) inc_x=0;

	if (current.x== GlobalParams::mesh_dim_x-1)
	    if (inc_x>0) inc_x=0;

	if (current.y==0)
	    if (inc_y<0) inc_y=0;

	if (current.y==GlobalParams::mesh_dim_y-1)
	    if (inc_y>0) inc_y=0;

	if (rand()%2)
	    current.x +=inc_x;
	else
	    current.y +=inc_y;
    }
    return coord2Id(current);
}


int roulette()
{
    int slices = GlobalParams::mesh_dim_x + GlobalParams::mesh_dim_y -2;


    double r = rand()/(double)RAND_MAX;


    for (int i=1;i<=slices;i++)
    {
	if (r< (1-1/double(2<<i)))
	{
	    return i;
	}
    }
    assert(false);
    return 1;
}


Packet ProcessingElement::trafficULocal()
{
    Packet p;
    p.src_id = local_id;

    int target_hops = roulette();

    p.dst_id = findRandomDestination(local_id,target_hops);

    p.timestamp = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;
    p.size = p.flit_left = getRandomSize();
    p.vc_id = randInt(0,GlobalParams::n_virtual_channels-1);

    return p;
}

Packet ProcessingElement::trafficRandom()
{
    Packet p;
    p.src_id = local_id;
    double rnd = rand() / (double) RAND_MAX;
    double range_start = 0.0;
    int max_id;

    if (GlobalParams::topology == TOPOLOGY_MESH)
	max_id = (GlobalParams::mesh_dim_x * GlobalParams::mesh_dim_y) - 1; //Mesh 
    else    // other delta topologies
	max_id = GlobalParams::n_delta_tiles-1; 

    // Random destination distribution
    do {
	p.dst_id = randInt(0, max_id);

	// check for hotspot destination
	for (size_t i = 0; i < GlobalParams::hotspots.size(); i++) {

	    if (rnd >= range_start && rnd < range_start + GlobalParams::hotspots[i].second) {
		if (local_id != GlobalParams::hotspots[i].first ) {
		    p.dst_id = GlobalParams::hotspots[i].first;
		}
		break;
	    } else
		range_start += GlobalParams::hotspots[i].second;	// try next
	}
#ifdef DEADLOCK_AVOIDANCE
	assert((GlobalParams::topology == TOPOLOGY_MESH));
	if (p.dst_id%2!=0)
	{
	    p.dst_id = (p.dst_id+1)%256;
	}
#endif

    } while (p.dst_id == p.src_id);

    p.timestamp = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;
    p.size = p.flit_left = getRandomSize();
    p.vc_id = randInt(0,GlobalParams::n_virtual_channels-1);

    return p;
}
// TODO: for testing only
Packet ProcessingElement::trafficTest()
{
    Packet p;
    p.src_id = local_id;
    p.dst_id = 10;

    p.timestamp = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;
    p.size = p.flit_left = getRandomSize();
    p.vc_id = randInt(0,GlobalParams::n_virtual_channels-1);

    return p;
}

Packet ProcessingElement::trafficTranspose1()
{
    assert(GlobalParams::topology == TOPOLOGY_MESH);
    Packet p;
    p.src_id = local_id;
    Coord src, dst;

    // Transpose 1 destination distribution
    src.x = id2Coord(p.src_id).x;
    src.y = id2Coord(p.src_id).y;
    dst.x = GlobalParams::mesh_dim_x - 1 - src.y;
    dst.y = GlobalParams::mesh_dim_y - 1 - src.x;
    fixRanges(src, dst);
    p.dst_id = coord2Id(dst);

    p.vc_id = randInt(0,GlobalParams::n_virtual_channels-1);
    p.timestamp = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;
    p.size = p.flit_left = getRandomSize();

    return p;
}

Packet ProcessingElement::trafficTranspose2()
{
    assert(GlobalParams::topology == TOPOLOGY_MESH);
    Packet p;
    p.src_id = local_id;
    Coord src, dst;

    // Transpose 2 destination distribution
    src.x = id2Coord(p.src_id).x;
    src.y = id2Coord(p.src_id).y;
    dst.x = src.y;
    dst.y = src.x;
    fixRanges(src, dst);
    p.dst_id = coord2Id(dst);

    p.vc_id = randInt(0,GlobalParams::n_virtual_channels-1);
    p.timestamp = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;
    p.size = p.flit_left = getRandomSize();

    return p;
}

void ProcessingElement::setBit(int &x, int w, int v)
{
    int mask = 1 << w;

    if (v == 1)
	x = x | mask;
    else if (v == 0)
	x = x & ~mask;
    else
	assert(false);
}

int ProcessingElement::getBit(int x, int w)
{
    return (x >> w) & 1;
}

inline double ProcessingElement::log2ceil(double x)
{
    return ceil(log(x) / log(2.0));
}

Packet ProcessingElement::trafficBitReversal()
{

    int nbits =
	(int)
	log2ceil((double)
		 (GlobalParams::mesh_dim_x *
		  GlobalParams::mesh_dim_y));
    int dnode = 0;
    for (int i = 0; i < nbits; i++)
	setBit(dnode, i, getBit(local_id, nbits - i - 1));

    Packet p;
    p.src_id = local_id;
    p.dst_id = dnode;

    p.vc_id = randInt(0,GlobalParams::n_virtual_channels-1);
    p.timestamp = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;
    p.size = p.flit_left = getRandomSize();

    return p;
}

Packet ProcessingElement::trafficShuffle()
{

    int nbits =
	(int)
	log2ceil((double)
		 (GlobalParams::mesh_dim_x *
		  GlobalParams::mesh_dim_y));
    int dnode = 0;
    for (int i = 0; i < nbits - 1; i++)
	setBit(dnode, i + 1, getBit(local_id, i));
    setBit(dnode, 0, getBit(local_id, nbits - 1));

    Packet p;
    p.src_id = local_id;
    p.dst_id = dnode;

    p.vc_id = randInt(0,GlobalParams::n_virtual_channels-1);
    p.timestamp = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;
    p.size = p.flit_left = getRandomSize();

    return p;
}

Packet ProcessingElement::trafficButterfly()
{

    int nbits = (int) log2ceil((double)
		 (GlobalParams::mesh_dim_x *
		  GlobalParams::mesh_dim_y));
    int dnode = 0;
    for (int i = 1; i < nbits - 1; i++)
	setBit(dnode, i, getBit(local_id, i));
    setBit(dnode, 0, getBit(local_id, nbits - 1));
    setBit(dnode, nbits - 1, getBit(local_id, 0));

    Packet p;
    p.src_id = local_id;
    p.dst_id = dnode;

    p.vc_id = randInt(0,GlobalParams::n_virtual_channels-1);
    p.timestamp = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;
    p.size = p.flit_left = getRandomSize();

    return p;
}

void ProcessingElement::fixRanges(const Coord src,
				       Coord & dst)
{
    // Fix ranges
    if (dst.x < 0)
	dst.x = 0;
    if (dst.y < 0)
	dst.y = 0;
    if (dst.x >= GlobalParams::mesh_dim_x)
	dst.x = GlobalParams::mesh_dim_x - 1;
    if (dst.y >= GlobalParams::mesh_dim_y)
	dst.y = GlobalParams::mesh_dim_y - 1;
}

int ProcessingElement::getRandomSize()
{
    return randInt(GlobalParams::min_packet_size,
		   GlobalParams::max_packet_size);
}

unsigned int ProcessingElement::getQueueSize() const
{
    return packet_queue.size();
}

void ProcessingElement::receive()
{
	for(int vc = 0; vc < GlobalParams::n_virtual_channels; vc++)
	{
		if(!buffer_rx[vc].IsEmpty())
		{
			Flit flit = buffer_rx[vc].Pop();
			if(flit.flit_type == FLIT_TYPE_TAIL)
			{
				LOG << "Received at " << local_id << " " << flit << " dataAvailable = " << dataAvailable << endl;
				switch(flit.payload.type)
				{
					case PAYLOAD_DEFAULT:
						LOG << "type default\n";
						handleDefault(flit);
						break;
					case PAYLOAD_WRITE_DATA:
						LOG << "type write\n";
						handleWrite(flit);
						break;
					case PAYLOAD_READ_REQ:
						LOG << "type read_request\n";
						handleReadReq(flit);
						break;
					case PAYLOAD_READ_ANS:
						LOG << "type read_reply\n";
						handleReadReply(flit);
						break;
					case PAYLOAD_MALICIOUS:
						LOG << "UNDER ATTACK!\n";
						handleAttack(flit);
						break;
					default:
						LOG << "type Not reserved!\n";
						handleDefault(flit);
				}
			}
		}
	}
}

void ProcessingElement::handleDefault(Flit flit)
{
	LOG << "Got default flit at " << local_id << ". Doing nothing. " << endl;
}

void ProcessingElement::handleWrite(Flit flit)
{
	assert(flit.payload.type == PAYLOAD_WRITE_DATA);
	dataAvailable = true;
	LOG << "Got write request at " << local_id << " from " << flit.src_id << endl;
	int old_data = data;
	data = flit.payload.data;
	LOG << "Updating data from " << old_data << " to " << data << endl;
}

void ProcessingElement::handleReadReq(Flit flit)
{
	assert(flit.payload.type == PAYLOAD_READ_REQ);
	LOG << "Got read request at " << local_id << " from " << flit.src_id << endl;
	if(!dataAvailable)
		LOG << "Data not available. Ignoring request!" << endl;
	else
	{
		LOG << "Sending data " << data << endl;
		
		Packet packet;	// Packet with reply data
    		double now = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;	// Get current time stamp
        	int vc = randInt(0,GlobalParams::n_virtual_channels-1);
		Payload pl;	// Make payload 
		pl.data = data;
		pl.type = PAYLOAD_READ_ANS;
		packet.make(local_id, flit.src_id, vc, now, 2, pl);

	    	packet_queue.push(packet);	//Push packet in queue
	    	transmittedAtPreviousCycle = true;
	}
	
}

void ProcessingElement::handleReadReply(Flit flit)
{
	assert(flit.payload.type == PAYLOAD_READ_ANS);
	LOG << "Got read reply at " << local_id << " from " << flit.src_id << " with data as " << flit.payload.data << endl;
}

void ProcessingElement::handleAttack(Flit flit)
{
	assert(flit.payload.type == PAYLOAD_MALICIOUS);
	LOG << "Attacking at " << local_id << ". Collaborating with " << flit.src_id << endl;
	
	int attack_count = flit.payload.data; 	// Keeps track of malicious packet circulated in current cycle
	LOG << "Received packet #" << attack_count << " in attack." << endl;
	
	Packet packet;	// Packet with reply data
    	double now = sc_time_stamp().to_double() / GlobalParams::clock_period_ps;	// Get current time stamp
        int vc = randInt(0,GlobalParams::n_virtual_channels-1);
	Payload pl;	// Make payload 
	pl.data = attack_count + 1;	// Increase packet count
	pl.type = PAYLOAD_MALICIOUS;
	packet.make(local_id, flit.src_id, vc, now, 2, pl);

	packet_queue.push(packet);	//Push packet in queue
	transmittedAtPreviousCycle = true;
	
	if(attack_started && !attack_pipeline_filled)
	{
		attack_pipeline_filled = true;	// Stop inserting more packets as pipeline is filled
		LOG << "Filled MALICIOUS pipeline!" << endl;
	}
}

int ProcessingElement::get_stalled_flits(int vc)
{
	return stalled_flits[vc];
}

int ProcessingElement::get_transmitted_flits(int vc)
{
	return transmitted_flits[vc];
}

int ProcessingElement::get_cumulative_latency(int vc)
{
	return cumulative_latency[vc];
}

int ProcessingElement::get_buffer_status(int vc)
{
	return buffer_rx[vc].getCurrentFreeSlots();
}

int ProcessingElement::get_cycles_since_last_flit(int vc)
{
	return cycles_since_last_flit[vc];
}