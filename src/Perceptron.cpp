#include "Perceptron.h"


void Perceptron::set_weights(vector <float> _weights)
{
	// string op = "Weights are: ";
	for(float f: _weights)
	{
		weights.push_back(f);
		// op += to_string(f) + " ";
	}
	// LOG << op << endl;
}

bool Perceptron::get_prediction(vector <int> features)
{
	assert(features.size() == 6);
	assert(weights.size() == 6);
	float value = 0;
	for(size_t idx = 0; idx < features.size(); idx++)
		value += float(features[idx]) * weights[idx];
	return value > 0.0;
}