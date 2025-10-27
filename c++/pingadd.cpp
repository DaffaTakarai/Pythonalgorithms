// ping_cmd.cpp
// Versi portable: memanggil utilitas 'ping' dari sistem dan mengambil waktu round-trip.
// Works on Linux/macOS. On Windows change "-c 1" to "-n 1".
// Compile: g++ -std=c++11 ping_cmd.cpp -o ping_cmd

#include <iostream>
#include <string>
#include <array>
#include <memory>
#include <regex>
#include <cstdio>

int main(int argc, char* argv[]) {
    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " <host-or-ip>\n";
        return 1;
    }

    std::string host = argv[1];

    // For Linux/macOS use "-c 1". For Windows change to "-n 1".
    std::string cmd = "ping -c 1 " + host + " 2>&1";

    // Run command and capture output
    std::array<char, 128> buffer;
    std::string result;
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd.c_str(), "r"), pclose);
    if (!pipe) {
        std::cerr << "Failed to run ping command\n";
        return 1;
    }
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr) {
        result += buffer.data();
    }

    // Print raw output if you want:
    // std::cout << result << "\n";

    // Try to extract time=... ms using regex (common ping output)
    std::smatch m;
    std::regex r_time("time=([0-9]+\\.?[0-9]*)\\s?ms");
    if (std::regex_search(result, m, r_time)) {
        std::cout << "Reply from " << host << ": time=" << m[1] << " ms\n";
        return 0;
    }

    // On some systems ping prints "Average = Xms" in a different line
    std::regex r_time_win("Average = ([0-9]+)ms");
    if (std::regex_search(result, m, r_time_win)) {
        std::cout << "Reply from " << host << ": time=" << m[1] << " ms (avg)\n";
        return 0;
    }

    // If nothing matched, show failure and raw output snippet
    std::cout << "No reply / unable to parse time. Raw output:\n";
    std::cout << result << "\n";

    return 2;
}
