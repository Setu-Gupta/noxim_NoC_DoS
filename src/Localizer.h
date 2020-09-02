#ifndef _LOCALIZER_H__
#define _LOCALIZER_H__

#include <systemc.h>
#include "Utils.h"
#include "NoC.h"
#include "GlobalParams.h"
#include "Predictor.h"
#include "LocalizerRouter.h"

SC_MODULE(Localizer)
{
	NoC* noc = nullptr;

	Predictor* predictor = nullptr;

	LocalizerRouter ***localizer_grid;

	sc_in_clk clock;	// Input signal for clock
	sc_in < bool > reset;	// Reset signal

	SC_HAS_PROCESS(Localizer);

	Localizer(sc_module_name _name, NoC * _noc) : sc_module(_name), noc(_noc)
	{
			// Return if localization is not enabled
		if(GlobalParams::weights_file_name == NO_LOCALIZATION)
			return;
		if(GlobalParams::accuracy_op_file_name == NO_ACCURACY_OP)
			return;

		predictor = new Predictor("Predictor", _noc);
		LOG << "Setting up grid" << endl;
		setup_grid();
		LOG << "Initialized Localizer" << endl;
		SC_METHOD(run_localization);
		sensitive << reset;
		sensitive << clock.pos();
	}

	void setup_grid();	// Creates grid of LocalizerRouters
	void run_localization();	// Runs localization
	void __test_run_localization();	// Depreciated

};

#endif