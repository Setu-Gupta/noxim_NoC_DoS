#include <FeatureCollector.h>
using namespace std;

void FeatureCollector::testPrint()
{
	map < int, vector < Feature_t > > :: iterator it = features.begin();
	for(it = features.begin(); it != features.end(); it++)
	{
		vector < Feature_t > f_vect = it->second;
		if(f_vect.size() >= 2)
			cout << f_vect[1].print();
	}
}


void FeatureCollector::exportFeatures()
{
	if(GlobalParams::feature_file_name != NO_FEATURES)
	{
		ofstream feature_file;
		feature_file.open(GlobalParams::feature_file_name, ios::out | ios::trunc);	// Open a file to write data to

		map < int, vector < Feature_t > > :: iterator it = features.begin();
		for(it = features.begin(); it != features.end(); it++)
		{
			vector < Feature_t > f_vect = it->second;
			for(Feature_t f: f_vect)
				feature_file << f.print();
		}

		feature_file.close();
	}
}