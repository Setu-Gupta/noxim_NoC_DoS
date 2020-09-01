#ifndef _PERCEPTRON_H__
#define _PERCEPTRON_H__

#include <systemc.h>
#include <vector>
#include <string>
#include <assert.h>
#include "Utils.h"

using namespace std;

SC_MODULE(Perceptron)
{

	SC_CTOR(Perceptron) {}

	vector <float> weights;

	void set_weights(vector <float> _weights);	// Setter to fix weights
	bool get_prediction(vector <int> features);	// Executes perceptrons and gives prediction
};

#endif