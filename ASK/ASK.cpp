#include <atomic>
#include <vector>
#include <map>
#include <thread>
#include <iostream>
#include "ASK.h"
#include <string>
#include <sstream>
#include <fstream>
#include <filesystem>
#include <locale>
#include <codecvt>
#include "resource.h"
std::atomic<bool> toggle(false);
std::atomic<bool> is_target_active(true);
std::atomic<bool> DoctorMode(false);
int keycode;
int autoskillcheck_key;
int doctormode_key;
std::vector<int> window_rect;
std::map<std::string, int> monitor;
int slp;
int DcOgr;
int DefOgr;
std::atomic <bool> info(false);
int DCwhiteOgrMin;
int DCwhiteOgrMax;
int DefwhiteOgrMin;
int DefwhiteOgrMax;
int DefredOgr;
void create_default_config(const std::string& filename) {
    std::ofstream file(filename);
    file << "; Задержка в миллисекундах для цикла авто-чека\n";
    file << "slp = 0\n";
    file << "\n";
    file << "; Код клавиши для авто-скилчека (в hex, например, 0x2D для Insert) (https://snipp.ru/handbk/vk-code)\n";
    file << "autoskillcheck_key = 0x2D\n";  // По умолчанию Insert
    file << "\n";
    file << "; Код клавиши для активации режима доктора (в hex, например, 0x24 для Home) (https://snipp.ru/handbk/vk-code)\n";
    file << "doctormode_key = 0x24\n";      // По умолчанию Home
    file << "\n";
    file << "; Код клавиши для активации действия (например, 0xA4 для Left Alt) (https://snipp.ru/handbk/vk-code)\n";
    file << "keycode = 0xA4\n";
    file << "\n";
    file << "; Разрешение монитора [left, top, right, bottom]\n";
    file << "window_rect = 0, 0, 550, 550\n";
    file << "\n";
    file << "; Область монитора для проверки [top, left, width, height]\n";
    file << "monitor = 0, 0, 550, 550\n";
    file << "; Doctor mode Ограничение и Default Ограничения\n";
    file << "DcOgr = 550\n";
    file << "DefOgr = 250\n";
    file << "DCwhiteOgrMin = 5\n";
    file << "DCwhiteOgrMax = 600\n";
    file << "; Default Mode\n";
    file << "DefwhiteOgrMin = 5\n";
    file << "DefwhiteOgrMax = 600\n";
    file << "DefredOgr = 50\n";
    file.close();
    std::cout << "Файл config.ini создан с настройками по умолчанию.\n";
}
void load_config(const std::string& filename) {
    std::ifstream file(filename);
    std::string line;
    while (std::getline(file, line)) {
        if (line.empty() || line[0] == ';') continue;
        std::istringstream iss(line);
        std::string key;
        if (std::getline(iss, key, '=')) {
            std::string value;
            if (std::getline(iss, value)) {
                key = key.substr(0, key.find_last_not_of(" \t") + 1);
                value = value.substr(value.find_first_not_of(" \t"));
                if (key == "slp") {
                    slp = std::stoi(value);
                }
                else if (key == "autoskillcheck_key") {
                    autoskillcheck_key = std::stoi(value, nullptr, 16);
                }
                else if (key == "doctormode_key") {
                    doctormode_key = std::stoi(value, nullptr, 16);
                }
                else if (key == "keycode") {
                    keycode = std::stoi(value, nullptr, 16);
                }
                else if (key == "window_rect") {
                    std::istringstream valstream(value);
                    std::string val;
                    window_rect.clear();
                    while (std::getline(valstream, val, ',')) {
                        window_rect.push_back(std::stoi(val));
                    }
                }
                else if (key == "monitor") {
                    std::istringstream valstream(value);
                    std::string val;
                    std::vector<int> monitor_vals;
                    while (std::getline(valstream, val, ',')) {
                        monitor_vals.push_back(std::stoi(val));
                    }
                    monitor["top"] = monitor_vals[0];
                    monitor["left"] = monitor_vals[1];
                    monitor["width"] = monitor_vals[2];
                    monitor["height"] = monitor_vals[3];
                }
                else if (key == "DcOgr") {
                    DcOgr = std::stoi(value);
                }
                else if (key == "DefOgr") {
                    DefOgr = std::stoi(value);
                }
                else if (key == "DCwhiteOgrMin") {
                    DCwhiteOgrMin = std::stoi(value);
                }
                else if (key == "DCwhiteOgrMax") {
                    DCwhiteOgrMax = std::stoi(value);
                }
                else if (key == "DefwhiteOgrMin") {
                    DefwhiteOgrMin = std::stoi(value);
                }
                else if (key == "DefwhiteOgrMax") {
                    DefwhiteOgrMax = std::stoi(value);
                }
                else if (key == "DefredOgr") {
                    DefredOgr = std::stoi(value);
                }
            }
        }
    }
}
void auto_skillcheck_wrapper() {
    while (toggle) {
        auto_skillcheck(toggle, is_target_active, window_rect, monitor, keycode, DoctorMode, slp, DcOgr, DefOgr, DCwhiteOgrMin, DCwhiteOgrMax, DefwhiteOgrMin, DefwhiteOgrMax,
            DefredOgr);
        Sleep(50);
    }
}
void control_keys(std::atomic<bool>& toggle, std::atomic<bool>& DoctorMode) {
    std::thread skillcheck_thread;
    while (true) {
        if (GetAsyncKeyState(autoskillcheck_key) & 0x8000) {  // Используем autoskillcheck_key
            if (!toggle) {
                toggle = true;
                std::cout << "Start auto_skillcheck. DoctorMode: " << (DoctorMode ? "ON" : "OFF") << std::endl;
                if (!skillcheck_thread.joinable()) {
                    skillcheck_thread = std::thread(auto_skillcheck_wrapper);
                }
            }
            else {
                toggle = false;
                std::cout << "auto_skillcheck stopped." << std::endl;
                if (skillcheck_thread.joinable()) {
                    skillcheck_thread.join();
                }
            }
            Sleep(300);
        }
        if (GetAsyncKeyState(doctormode_key) & 0x8000) {  // Используем doctormode_key
            DoctorMode = !DoctorMode;
            std::cout << "Doctor Mode " << (DoctorMode ? "enabled" : "disabled") << std::endl;
            Sleep(200);
        }
        Sleep(50);
    }
}
int main() {
    setlocale(LC_ALL, "ru");
    std::string config_filename = "config.ini";
    if (!std::filesystem::exists(config_filename)) {
        create_default_config(config_filename);
    }
    load_config(config_filename);
    std::thread control_thread(control_keys, std::ref(toggle), std::ref(DoctorMode));
    control_thread.join();
    return 0;
}
