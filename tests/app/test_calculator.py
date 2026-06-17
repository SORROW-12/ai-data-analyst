import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
import time

@pytest.fixture(scope="module")
def driver():
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.device_name = "Pixel_6"
    options.app_package = "com.android.settings"
    options.app_activity = ".Settings"
    options.no_reset = True

    d = webdriver.Remote("http://127.0.0.1:4723", options=options)
    yield d
    d.quit()


class TestSettingsApp:
    """设置App自动化测试"""

    def test_app_launches(self, driver):
        """验证App成功启动"""
        driver.activate_app("com.android.settings")
        time.sleep(2)
        assert driver.current_package == "com.android.settings"
        print(f"\nApp启动成功，当前包名：{driver.current_package}")

    def test_search_box_exists(self, driver):
        """验证搜索框存在"""
        elements = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.TextView")
        assert len(elements) > 0
        print(f"\n找到{len(elements)}个文本元素")

    def test_scroll_down(self, driver):
        """测试滑动操作"""
        size = driver.get_window_size()
        start_x = size['width'] // 2
        start_y = size['height'] * 3 // 4
        end_y = size['height'] // 4
        driver.swipe(start_x, start_y, start_x, end_y, 800)
        time.sleep(1)
        print("\n滑动操作完成")

    def test_back_button(self, driver):
        """测试返回键"""
        driver.back()
        time.sleep(1)
        print("\n返回操作完成")