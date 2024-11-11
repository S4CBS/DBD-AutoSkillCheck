#include <variant>
#include <opencv2/opencv.hpp>
#include <Windows.h>
#include <thread>
#include <future>
#include "Utility.h"
#include <unordered_set>
#include <string.h>

namespace std {
    template <>
    struct hash<cv::Point> {
        size_t operator()(const cv::Point& p) const {
            return std::hash<int>()(p.x) ^ (std::hash<int>()(p.y) << 1);
        }
    };
}

cv::Mat capture_screen(int top, int left, int width, int height) {
    Utility utility;
    cv::Mat screenshot = utility.get_sct(top, left, width, height);

    if (!screenshot.empty()) {
        cv::cvtColor(screenshot, screenshot, cv::COLOR_BGRA2RGB);
    }
    else {
        std::cout << "Error capturing screenshot!" << std::endl;
    }

    return screenshot;
}

std::pair<std::vector<cv::Point>, std::vector<cv::Point>> process_image(const cv::Mat& img, const cv::Scalar& low_white, const cv::Scalar& high_white, const cv::Scalar& low_red, const cv::Scalar& high_red) {
    cv::Mat white_mask, red_mask;
    cv::inRange(img, low_white, high_white, white_mask);
    cv::inRange(img, low_red, high_red, red_mask);

    std::vector<cv::Point> white_cords, red_cords;
    cv::findNonZero(white_mask, white_cords);
    cv::findNonZero(red_mask, red_cords);

    return { white_cords, red_cords };
}

void PressKey(WORD key) {
    INPUT input = {};
    input.type = INPUT_KEYBOARD;
    input.ki.wVk = key;
    input.ki.dwFlags = 0;

    if (SendInput(1, &input, sizeof(INPUT)) == 0) {
        std::cerr << "01" << key << std::endl;
    }

    input.ki.dwFlags = KEYEVENTF_KEYUP;
    if (SendInput(1, &input, sizeof(INPUT)) == 0) {
        std::cerr << "02" << key << std::endl;
    }
}

void auto_skillcheck(std::atomic<bool>& toggle, std::atomic<bool>& is_target_active, const std::vector<int>& window_rect, const std::variant<std::string, std::map<std::string, int>>& sct_monitor, int keycode,
    std::atomic<bool>& DoctorMode, int slp) {
    cv::Scalar low_white(250, 250, 250), high_white(255, 255, 255);
    cv::Scalar low_red(160, 0, 0), high_red(255, 30, 30);

    std::map<std::string, int> monitor = std::get<std::map<std::string, int>>(sct_monitor);
    std::vector<cv::Point> white_cords_buffer;

    int screen_width = GetSystemMetrics(SM_CXSCREEN);
    int screen_height = GetSystemMetrics(SM_CYSCREEN);
    int center_x = screen_width / 2;
    int center_y = screen_height / 2;

    int capture_width = DoctorMode ? 450 : 200;
    int capture_height = DoctorMode ? 450 : 200;

    int top = center_y - (capture_height / 2);
    int left = center_x - (capture_width / 2);

    std::cout << "Width: " << capture_width << std::endl;
    std::cout << "Height: " << capture_height << std::endl;

    while (toggle) {
        if (is_target_active) {
            if (monitor != std::map<std::string, int>(
                {
                    {"top", top}, {"left", left}, {"width", capture_width}, {"height", capture_height}
                }
            )) {
                monitor = {
                    {"top", top}, {"left", left}, {"width", capture_width}, {"height", capture_height}
                };
            }
        }

        auto future_img = std::async(std::launch::async, capture_screen, top, left, capture_width, capture_height);
        cv::Mat img = future_img.get();

        auto future_process = std::async(std::launch::async, process_image, img, low_white, high_white, low_red, high_red);
        auto [white_cords, red_cords] = future_process.get();

        if (white_cords.size() > 0) {
            white_cords_buffer.insert(white_cords_buffer.end(), white_cords.begin(), white_cords.end());
        }

        if (!white_cords_buffer.empty() && red_cords.size() > 150) {
            std::unordered_set<cv::Point> red_set(red_cords.begin(), red_cords.end());
            std::unordered_set<cv::Point> white_set(white_cords_buffer.begin(), white_cords_buffer.end());

            std::unordered_set<cv::Point> intersection;
            for (const auto& red_point : red_set) {
                if (white_set.count(red_point)) {
                    intersection.insert(red_point);
                }
            }
            if (!intersection.empty()) {
                std::this_thread::sleep_for(std::chrono::nanoseconds(slp));
                PressKey(keycode);
                std::this_thread::sleep_for(std::chrono::nanoseconds(slp));

                white_cords_buffer.clear();
                std::this_thread::sleep_for(std::chrono::nanoseconds(1));
            }
        }

        if (red_cords.empty()) {
            white_cords_buffer.clear();
        }
    }
}