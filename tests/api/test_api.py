import pytest
import requests
import os

BASE_URL = "http://127.0.0.1:5000"
CSV_PATH = r"C:\Users\26817\online_retail_II.csv"

class TestUploadAPI:
    """上传接口测试"""

    def test_upload_valid_csv(self):
        """正常上传CSV文件"""
        with open(CSV_PATH, 'rb') as f:
            resp = requests.post(
                f"{BASE_URL}/upload",
                files={"file": ("2019-Oct.csv", f, "text/csv")}
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] == True
        assert "filename" in data
        assert "quality" in data
        print(f"\n上传成功，文件名：{data['filename']}")

    def test_upload_quality_report_structure(self):
        """验证数据质量报告结构完整"""
        with open(CSV_PATH, 'rb') as f:
            resp = requests.post(
                f"{BASE_URL}/upload",
                files={"file": ("2019-Oct.csv", f, "text/csv")}
            )
        quality = resp.json()["quality"]
        assert "rows" in quality
        assert "cols" in quality
        assert "missing" in quality
        assert "duplicates" in quality
        assert quality["rows"] > 0
        assert quality["cols"] > 0
        print(f"\n数据质量：{quality['rows']}行，{quality['cols']}列，"
              f"{quality['duplicates']}行重复")

    def test_upload_no_file(self):
        """上传时不带文件应返回400"""
        resp = requests.post(f"{BASE_URL}/upload")
        assert resp.status_code == 400


class TestQueryAPI:
    """查询接口测试"""

    FILENAME = "online_retail_II.csv"

    def test_query_sales_ranking(self):
        """测试销售排名查询"""
        resp = requests.post(
            f"{BASE_URL}/query",
            json={
                "filename": self.FILENAME,
                "question": "哪个品牌销售额最高？"
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert len(data["answer"]) > 0
        print(f"\n回答：{data['answer'][:100]}...")

    def test_query_returns_sql(self):
        """验证查询返回SQL语句"""
        resp = requests.post(
            f"{BASE_URL}/query",
            json={
                "filename": self.FILENAME,
                "question": "每个event_type各有多少条记录？"
            }
        )
        data = resp.json()
        assert "sql" in data
        print(f"\n执行SQL：{data['sql']}")

    def test_query_missing_filename(self):
        """缺少filename参数应返回错误"""
        resp = requests.post(
            f"{BASE_URL}/query",
            json={"question": "销售额是多少？"}
        )
        assert resp.status_code in [400, 500]

    def test_query_empty_question(self):
        """空问题应返回错误"""
        resp = requests.post(
            f"{BASE_URL}/query",
            json={"filename": self.FILENAME, "question": ""}
        )
        assert resp.status_code == 400


class TestAPIPerformance:
    """接口性能测试"""

    def test_upload_response_time(self):
        """上传接口响应时间应在10秒内"""
        import time
        start = time.time()
        with open(CSV_PATH, 'rb') as f:
            requests.post(
                f"{BASE_URL}/upload",
                files={"file": ("2019-Oct.csv", f, "text/csv")}
            )
        elapsed = time.time() - start
        assert elapsed < 10, f"上传耗时{elapsed:.2f}秒，超过10秒阈值"
        print(f"\n上传响应时间：{elapsed:.2f}秒")