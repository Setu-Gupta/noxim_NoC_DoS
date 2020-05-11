# Iterates over files in paths and uses them as traffic tables for noxim
shopt -s xpg_echo	# Expand \n in echo

# paths=("./../traffic_tables/to_test/generated_files/with_attack" "./../traffic_tables/to_test/FFT_pir/with_attack")
paths=("./../traffic_tables/to_test/FFT_pir_por")
# paths=("./../traffic_tables/to_test/FFT_pir_por/with_attack")
# paths=("./../traffic_tables/to_test/generated_files" "./../traffic_tables/to_test/FFT_pir")
# log_dir_path="./../tmp_logs/with_attack"
log_dir_path="./../tmp_logs"
noxim_path="./../noxim"
config_path="./../../personal_configs/my_config.yaml"
power_path="./../power.yaml"

echo "Picking up files from following paths:"
for path in "${paths[@]}"
do
	echo $path
done

echo "\nLog directory is\n$log_dir_path"
echo "Noxim executable at\n$noxim_path"
echo "Config file at\n$config_path"
echo "Power config at\n$power_path"
echo ""

for path in "${paths[@]}"
do
	echo "Entering $path"
	for file in $path/*
	do
		if [ ! -f "$file" ]
		then
			continue
		fi
		echo "Executing for file: $file"
		file_name=${file##*/}
		log="$log_dir_path/log_$file_name"
		cmd="$noxim_path -topology MESH -dimx 8 -dimy 8 -traffic table $file -config ./../../personal_configs/my_config.yaml -power $power_path"
		# echo $cmd
		$cmd > $log &
	done
done

wait
echo "Done!"
