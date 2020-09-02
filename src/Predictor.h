#ifndef _PREDICTOR_H_
#define _PREDICTOR_H_

#include <systemc.h>
#include <vector>
#include <utility>
#include <map>
#include "Utils.h"
#include "GlobalParams.h"
#include "Perceptron.h"
#include "NoC.h"
#include "FeatureParser.h"
#include "CSVParser.h"
#include <fstream>
#include <string>

SC_MODULE(Predictor)
{
	map <pair <int, int>, vector <float>> weights;	// Map between router direction pair and weights
	map <pair <int, int>, bool> operations;	// Map between router port (Input side) pair and operation
	vector <vector <pair <Perceptron*, Perceptron*>>> perceptron_grid;	// 2D grid of perceptrons. first is input and second is output

	NoC* noc;	// NoC for FetaureParser
	FeatureParser* parser;
	CSVParser csvparser;


	SC_HAS_PROCESS(Predictor);
	void setup();
	pair <int, int> __get_output_router(int router, int port);	// Gets output side router and port. <x, y> format

public:
	Predictor(sc_module_name _name, NoC* _noc) : sc_module(_name), noc(_noc)
	{
		setup();
		// __tester();
	}

	bool predict(int router, int port);	// Get prediction. (generates fused prediction)
	void __tester();	// Prints parsed data to log. Used to test working
	void __dump_features();	// Prints features of all router and ports
};

#endif