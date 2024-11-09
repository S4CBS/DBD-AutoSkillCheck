#include <atomic>
#include <vector>
#include <map>
#include <thread>
#include <iostream>
#include "ASK.h"
#include <string>

std::atomic<bool> toggle(false);           // Toggle to activate check
std::atomic<bool> is_target_active(true);  // Check if target is active
std::atomic<bool> DoctorMode(false);       // DoctorMode
int keycode = 0xA4;
std::vector<int> window_rect = { 0, 0, 1920, 1080 };
std::map<std::string, int> monitor = { {"top", 0}, {"left", 0}, {"width", 400}, {"height", 400 } };
int slp = 2;

void auto_skillcheck_wrapper() {
    while (toggle) {  // Цикл для авто-чека с проверкой флага toggle
        auto_skillcheck(toggle, is_target_active, window_rect, monitor, keycode, DoctorMode, slp);
        Sleep(50);  // Добавлен небольшой интервал для снижения нагрузки
    }
}

void control_keys(std::atomic<bool>& toggle, std::atomic<bool>& DoctorMode) {
    std::thread skillcheck_thread;

    while (true) {
        if (GetAsyncKeyState(VK_INSERT) & 0x8000) {
            if (!toggle) {
                toggle = true;
                std::cout << "Start auto_skillcheck. DoctorMode: " << (DoctorMode ? "ON" : "OFF") << std::endl;

                if (!skillcheck_thread.joinable()) {  // Запускаем поток только если он не активен
                    skillcheck_thread = std::thread(auto_skillcheck_wrapper);
                }
            }
            else {
                toggle = false;
                std::cout << "auto_skillcheck stopped." << std::endl;

                if (skillcheck_thread.joinable()) {
                    skillcheck_thread.join();  // Ждем завершения потока
                }
            }
            Sleep(300);
        }

        if (GetAsyncKeyState(VK_HOME) & 0x8000) {
            DoctorMode = !DoctorMode;
            std::cout << "Doctor Mode " << (DoctorMode ? "enabled" : "disabled") << std::endl;
            Sleep(200);
        }

        Sleep(50);
    }
}

int main() {
    std::thread control_thread(control_keys, std::ref(toggle), std::ref(DoctorMode));
    control_thread.join();

    return 0;
}
