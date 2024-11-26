#include <opencv2/opencv.hpp>
#include <Windows.h>
#include <iostream>

class Utility {
public:
    static cv::Mat get_sct(int top, int left, int width, int height) {
        HDC hdcScreen = GetDC(NULL);
        HDC hdcMemDC = CreateCompatibleDC(hdcScreen);
        HBITMAP hbmScreen = CreateCompatibleBitmap(hdcScreen, width, height);
        SelectObject(hdcMemDC, hbmScreen);
        BitBlt(hdcMemDC, 0, 0, width, height, hdcScreen, left, top, SRCCOPY);
        BITMAPINFOHEADER bi;
        bi.biSize = sizeof(BITMAPINFOHEADER);
        bi.biWidth = width;
        bi.biHeight = -height;
        bi.biPlanes = 1;
        bi.biBitCount = 32;
        bi.biCompression = BI_RGB;
        bi.biSizeImage = 0;
        bi.biXPelsPerMeter = 0;
        bi.biYPelsPerMeter = 0;
        bi.biClrUsed = 0;
        bi.biClrImportant = 0;
        cv::Mat mat(height, width, CV_8UC4);
        GetDIBits(hdcMemDC, hbmScreen, 0, height, mat.data, (BITMAPINFO*)&bi, DIB_RGB_COLORS);
        DeleteObject(hbmScreen);
        DeleteDC(hdcMemDC);
        ReleaseDC(NULL, hdcScreen);
        return mat;
    }
};
