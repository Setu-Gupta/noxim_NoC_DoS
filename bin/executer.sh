./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/FFT_baseline -config ../personal_configs/my_config.yaml > logs/FFT_baseline &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/FFT_attack -config ../personal_configs/my_config.yaml > logs/FFT_attack &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/FFT_attack -config ../personal_configs/my_config.yaml -accuracy test_vectors/accuracy_setup -weights test_vectors/weights > logs/FFT_loc &;

./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/Barnes_0.00001 -config ../personal_configs/my_config.yaml > logs/Barnes_baseline &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/Barnes_0.00001_attack -config ../personal_configs/my_config.yaml > logs/Barnes_attack &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/Barnes_0.00001_attack -config ../personal_configs/my_config.yaml -accuracy test_vectors/accuracy_setup -weights test_vectors/weights > logs/Barnes_loc &;

./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/Radix_0.00001 -config ../personal_configs/my_config.yaml > logs/Radix_baseline &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/Radix_0.00001_attack -config ../personal_configs/my_config.yaml > logs/Radix_attack &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/Radix_0.00001_attack -config ../personal_configs/my_config.yaml -accuracy test_vectors/accuracy_setup -weights test_vectors/weights > logs/Radix_loc &;

./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/kmeans_traces_64_Network_File.txt -config ../personal_configs/my_config.yaml > logs/kmeans_baseline &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/kmeans_traces_64_Network_File.txt_attack -config ../personal_configs/my_config.yaml > logs/kmeans_attack &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/kmeans_traces_64_Network_File.txt_attack -config ../personal_configs/my_config.yaml -accuracy test_vectors/accuracy_setup -weights test_vectors/weights > logs/kmeans_loc &;

./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/gaussian_traces_64_Network_File.txt -config ../personal_configs/my_config.yaml > logs/gaussian_baseline &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/gaussian_traces_64_Network_File.txt_attack -config ../personal_configs/my_config.yaml > logs/gaussian_attack &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/gaussian_traces_64_Network_File.txt_attack -config ../personal_configs/my_config.yaml -accuracy test_vectors/accuracy_setup -weights test_vectors/weights > logs/gaussian_loc &;

./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/hotspot_traces_64_Network_File.txt -config ../personal_configs/my_config.yaml > logs/hotspot_baseline &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/hotspot_traces_64_Network_File.txt_attack -config ../personal_configs/my_config.yaml > logs/hotspot_attack &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/hotspot_traces_64_Network_File.txt_attack -config ../personal_configs/my_config.yaml -accuracy test_vectors/accuracy_setup -weights test_vectors/weights > logs/hotspot_loc &;

./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/mummergpu_traces_64_Network_File.txt -config ../personal_configs/my_config.yaml > logs/mummergpu_baseline &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/mummergpu_traces_64_Network_File.txt_attack -config ../personal_configs/my_config.yaml > logs/mummergpu_attack &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/mummergpu_traces_64_Network_File.txt_attack -config ../personal_configs/my_config.yaml -accuracy test_vectors/accuracy_setup -weights test_vectors/weights > logs/mummergpu_loc &;

./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/lud_traces_64_Network_File.txt -config ../personal_configs/my_config.yaml > logs/lud_baseline &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/lud_traces_64_Network_File.txt_attack -config ../personal_configs/my_config.yaml > logs/lud_attack &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/lud_traces_64_Network_File.txt_attack -config ../personal_configs/my_config.yaml -accuracy test_vectors/accuracy_setup -weights test_vectors/weights > logs/lud_loc &;

./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/backprop_traces_64_Network_File.txt -config ../personal_configs/my_config.yaml > logs/backprop_baseline &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/backprop_traces_64_Network_File.txt_attack -config ../personal_configs/my_config.yaml > logs/backprop_attack &;
./noxim -topology MESH -dimx 8 -dimy 8 -traffic table test_vectors/backprop_traces_64_Network_File.txt_attack -config ../personal_configs/my_config.yaml -accuracy test_vectors/accuracy_setup -weights test_vectors/weights > logs/backprop_loc &;