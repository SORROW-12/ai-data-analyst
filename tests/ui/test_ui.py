import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import os
import time

CHROMEDRIVER_PATH = r"C:\Users\26817\Desktop\data-analyst-ai\chromedriver.exe"
BASE_URL = "http://127.0.0.1:5000"
CSV_PATH = r"C:\Users\26817\online_retail_II.csv"

@pytest.fixture(scope="class")
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(CHROMEDRIVER_PATH)
    d = webdriver.Chrome(service=service, options=options)
    d.implicitly_wait(10)
    yield d
    d.quit()

class TestPageLoad:
    """页面加载测试"""

    def test_homepage_loads(self, driver):
        """首页正常加载"""
        driver.get(BASE_URL)
        assert "AI数据分析助手" in driver.title or "AI" in driver.page_source
        print("\n首页加载成功")

    def test_upload_area_visible(self, driver):
        """上传区域可见"""
        driver.get(BASE_URL)
        upload_area = driver.find_element(By.CLASS_NAME, "upload-area")
        assert upload_area.is_displayed()
        print("\n上传区域可见")

    def test_query_card_hidden_initially(self, driver):
        """初始状态查询区域隐藏"""
        driver.get(BASE_URL)
        query_card = driver.find_element(By.ID, "queryCard")
        assert query_card.get_attribute("style") != "display: block"
        print("\n查询区域初始隐藏，符合预期")


class TestUploadFlow:
    """上传功能UI测试"""

    def test_upload_csv_file(self, driver):
        """上传CSV文件后显示数据质量报告"""
        driver.get(BASE_URL)
        file_input = driver.find_element(By.ID, "fileInput")
        file_input.send_keys(CSV_PATH)

        wait = WebDriverWait(driver, 30)
        quality_card = wait.until(
            EC.visibility_of_element_located((By.ID, "qualityCard"))
        )
        assert quality_card.is_displayed()
        print("\n上传成功，数据质量报告已显示")

    def test_quality_report_shows_data(self, driver):
        """数据质量报告显示行数和列数"""
        wait = WebDriverWait(driver, 15)
        quality_grid = wait.until(
            EC.presence_of_element_located((By.ID, "qualityGrid"))
        )
        grid_text = quality_grid.text
        assert len(grid_text) > 0
        print(f"\n数据质量报告内容：{grid_text[:100]}")

    def test_query_card_appears_after_upload(self, driver):
        """上传后查询区域出现"""
        wait = WebDriverWait(driver, 15)
        query_card = wait.until(
            EC.visibility_of_element_located((By.ID, "queryCard"))
        )
        assert query_card.is_displayed()
        print("\n查询区域已显示")


class TestQueryFlow:
    """查询功能UI测试"""

    def test_preset_question_tags(self, driver):
        """预设问题标签可点击"""
        driver.get(BASE_URL)
        file_input = driver.find_element(By.ID, "fileInput")
        file_input.send_keys(CSV_PATH)

        wait = WebDriverWait(driver, 30)
        wait.until(EC.visibility_of_element_located((By.ID, "queryCard")))

        tags = driver.find_elements(By.CLASS_NAME, "tag")
        assert len(tags) > 0
        tags[0].click()

        question_input = driver.find_element(By.ID, "questionInput")
        assert len(question_input.get_attribute("value")) > 0
        print(f"\n点击标签后输入框内容：{question_input.get_attribute('value')}")

    def test_ask_button_clickable(self, driver):
        """分析按钮可点击"""
        ask_btn = driver.find_element(By.ID, "askBtn")
        assert ask_btn.is_enabled()
        print("\n分析按钮可点击")

    def test_answer_appears_after_query(self, driver):
        """提交问题后答案区域出现"""
        question_input = driver.find_element(By.ID, "questionInput")
        question_input.clear()
        question_input.send_keys("每个event_type各有多少条？")

        ask_btn = driver.find_element(By.ID, "askBtn")
        ask_btn.click()

        wait = WebDriverWait(driver, 60)
        answer_box = wait.until(
            EC.visibility_of_element_located((By.ID, "answerBox"))
        )
        assert answer_box.is_displayed()
        answer_text = answer_box.text
        assert len(answer_text) > 0
        print(f"\nAI回答：{answer_text[:100]}...")