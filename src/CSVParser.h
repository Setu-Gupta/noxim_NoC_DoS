#ifndef _CSVPARSER_H__
#define _CSVPARSER_H__

#include <vector>
#include <string>
#include <iostream>

class CSVParser
{
public:
	void read_line(std::istream& inp_stream)
	{
		std::getline(inp_stream, source);	// read a line from stream

		parsed.clear();

		std::size_t start_idx = 0;
		std::size_t end_idx = 0;

		while((end_idx = source.find(',', start_idx)) != std::string::npos)
		{
			std::string parsed_substr = source.substr(start_idx, end_idx - start_idx);
			parsed_substr = clean_string(parsed_substr);

			if(parsed_substr.length())
				parsed.push_back(parsed_substr);

			start_idx = end_idx + 1;
		}

		if(start_idx < source.length())
		{
			std::string parsed_substr = source.substr(start_idx, end_idx - start_idx);
			parsed_substr = clean_string(parsed_substr);

			if(parsed_substr.length())
				parsed.push_back(parsed_substr);	
		}

	}

	std::size_t size() const
	{
		return parsed.size();
	}

	std::string operator[](std::size_t idx) const
	{
		if(idx < size())
			return parsed[idx];
		return std::string("");
	}

private:
	std::vector< std::string > parsed;	// Vector of parsed strings
	std::string source;	// Input string

	// Removes whitespace from front and end
	std::string clean_string(std::string source) const
	{
		std::size_t first_char = source.find_first_not_of(" \t\n\r\v\0");
		std::size_t last_char = source.find_last_not_of(" \t\n\r\v\0");

		return source.substr(first_char, last_char - first_char + 1);
	}
};

std::istream& operator>>(std::istream& inp_stream, CSVParser& data);

#endif