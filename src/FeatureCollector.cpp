 #include <FeatureCollector.h>
 using namespace std;

 void FeatureCollector::testPrint()
 {
 	map < int, vector < Feature_t > > :: iterator it = features.begin();
 	for(it = features.begin(); it != features.end(); it++)
 	{
 		vector < Feature_t > f_vect = it->second;
 		if(f_vect.size() != 0)
 			cout << f_vect[0].print();
  	}
 }