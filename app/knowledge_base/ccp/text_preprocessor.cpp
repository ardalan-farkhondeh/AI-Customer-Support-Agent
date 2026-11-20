
#include <string>
#include <cctype>
#include <cstring>

extern "C" __declspec(dllexport)
int preprocess_text(
    const char* input,
    char* output,
    int output_size
) {
    if (!input || !output || output_size <= 0) {
        return -1;
    }

    std::string result;
    bool previous_space = true;

    for (unsigned char c : std::string(input)) {

        if (c < 32 || c == 127) {
            if (c == '\n' || c == '\t' || c == '\r') {
                if (!previous_space) {
                    result += ' ';
                    previous_space = true;
                }
            }
            continue;
        }

        if (std::isspace(c)) {
            if (!previous_space) {
                result += ' ';
                previous_space = true;
            }
        } else {
            result += static_cast<char>(c);
            previous_space = false;
        }
    }

    if (!result.empty() && result.back() == ' ') {
        result.pop_back();
    }

    if (result.size() + 1 > static_cast<size_t>(output_size)) {
        return -2;
    }

    std::memcpy(output, result.c_str(), result.size() + 1);

    return static_cast<int>(result.size());
}
