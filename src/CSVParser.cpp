#include "CSVParser.h"

std::istream& operator>>(std::istream& inp_stream, CSVParser& data)
{
	data.read_line(inp_stream);
	return inp_stream;
}