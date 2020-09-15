for f in *_in
	do
	echo "Doing $f"
	shuf -n 5 $f >> random_data
done

for f in *_out
	do
	echo "Doing $f"
	shuf -n 5 $f >> random_data
done
