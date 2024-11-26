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
void process_template_matching(cv::Mat& img, const cv::Mat& templ, cv::Mat& matchRegion, cv::Point& minloc) {
    cv::Mat result;
    cv::Mat gray_img, gray_templ;

    // Проверяем, что изображения не пустые
    if (img.empty() || templ.empty()) {
        std::cerr << "Error: Image or template is empty!" << std::endl;
        return;
    }

    // Преобразование в градации серого
    cv::cvtColor(img, gray_img, cv::COLOR_BGR2GRAY);
    cv::cvtColor(templ, gray_templ, cv::COLOR_BGR2GRAY);

    // Выполняем подстановку шаблона
    cv::matchTemplate(gray_img, gray_templ, result, cv::TM_SQDIFF_NORMED);

    // Поиск максимального совпадения
    double minval, maxval;
    cv::Point maxloc;
    cv::minMaxLoc(result, &minval, &maxval, &minloc, &maxloc);

    // Рисуем прямоугольник вокруг найденного региона
    cv::rectangle(img, minloc, cv::Point(minloc.x + templ.cols, minloc.y + templ.rows), cv::Scalar(0, 255, 0), 2);

    // Проверка на допустимые координаты для создания ROI
    if (minloc.x >= 0 && minloc.y >= 0 &&
        minloc.x + templ.cols <= img.cols &&
        minloc.y + templ.rows <= img.rows) {
        // Сохраняем найденный регион
        matchRegion = img(cv::Rect(minloc.x, minloc.y, templ.cols, templ.rows));
        cv::imshow("img", img);
        cv::waitKey(1);
    }
    else {
        std::cerr << "Error: Invalid ROI dimensions!" << std::endl;
    }
}
void capture_and_process_async(std::atomic<bool>& toggle, int top, int left, int width, int height, const cv::Scalar& low_white, const cv::Scalar& high_white, const cv::Scalar& low_red, const cv::Scalar& high_red) {
    while (toggle) {
        cv::Mat img = capture_screen(top, left, width, height);
        if (!img.empty()) {
            auto async_result = std::async(std::launch::async, process_image, img, low_white, high_white, low_red, high_red);
            async_result.wait();
        }
    }
}
void auto_skillcheck(std::atomic<bool>& toggle, std::atomic<bool>& is_target_active, const std::vector<int>& window_rect, const std::variant<std::string, std::map<std::string, int>>& sct_monitor, int& keycode,
    std::atomic<bool>& DoctorMode, int& slp, int& DcOgr, int& DefOgr, int& DCwhiteOgrMin, int& DCwhiteOgrMax, int& DefwhiteOgrMin, int& DefwhiteOgrMax, int& DefredOgr) {

    cv::Mat templ = cv::imread("template.jpg");
    cv::Scalar low_white(250, 250, 250), high_white(255, 255, 255);
    cv::Scalar low_red(160, 0, 0), high_red(255, 30, 30);

    int screen_width = GetSystemMetrics(SM_CXSCREEN);
    int screen_height = GetSystemMetrics(SM_CYSCREEN);
    int center_x = screen_width / 2;
    int center_y = screen_height / 2;

    int capture_width = DoctorMode ? DcOgr : DefOgr;
    int capture_height = DoctorMode ? DcOgr : DefOgr;
    int top = center_y - (capture_height / 2);
    int left = center_x - (capture_width / 2);

    std::vector<cv::Point> white_cords_buffer; // Буфер для белых точек

    while (toggle) {
        if (is_target_active) {
            // Асинхронный захват экрана
            std::future<cv::Mat> async_capture = std::async(std::launch::async, [&]() {
                return capture_screen(top, left, capture_width, capture_height);
                });

            cv::Mat img = async_capture.get(); // Получение результата захвата

            if (img.empty()) continue; // Проверка на пустое изображение

            cv::Mat matchRegion;
            cv::Point minloc;

            // Шаблонное сопоставление
            process_template_matching(img, templ, matchRegion, minloc);

            // Асинхронная обработка изображения
            std::future<std::pair<std::vector<cv::Point>, std::vector<cv::Point>>> async_process = std::async(std::launch::async, [&]() {
                return process_image(matchRegion, low_white, high_white, low_red, high_red);
                });

            // Получаем обработанные данные
            auto [white_cords, red_cords] = async_process.get();

            // Буферизация белых точек
            if (white_cords.size() > (DoctorMode ? DCwhiteOgrMin : DefwhiteOgrMin) &&
                white_cords.size() < (DoctorMode ? DCwhiteOgrMax : DefwhiteOgrMax)) {
                white_cords_buffer.insert(white_cords_buffer.end(), white_cords.begin(), white_cords.end());
            }

            // Поиск пересечений с красными точками
            if (!white_cords_buffer.empty() && red_cords.size() > DefredOgr) {
                std::unordered_set<cv::Point> red_set(red_cords.begin(), red_cords.end());
                std::unordered_set<cv::Point> white_set(white_cords_buffer.begin(), white_cords_buffer.end());
                std::unordered_set<cv::Point> intersection;

                for (const auto& red_point : red_set) {
                    if (white_set.count(red_point)) {
                        intersection.insert(red_point);
                    }
                }

                // Если пересечения найдены, нажимаем кнопку
                if (!intersection.empty()) {
                    std::this_thread::sleep_for(std::chrono::nanoseconds(slp));
                    PressKey(keycode);
                    std::this_thread::sleep_for(std::chrono::milliseconds(5));
                    white_cords_buffer.clear();
                }
            }

            // Очистка буфера, если нет красных точек
            if (red_cords.empty()) {
                white_cords_buffer.clear();
            }
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(5)); // Небольшая пауза для снижения нагрузки
    }
}
