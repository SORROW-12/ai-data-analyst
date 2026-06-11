from locust import HttpUser, task, between
from locust import events
import os

CSV_PATH = r"C:\Users\26817\online_retail_II.csv"

class DataAnalystUser(HttpUser):
    wait_time = between(1, 3)  # 每次请求间隔1-3秒

    def on_start(self):
        """每个虚拟用户启动时先上传文件"""
        with open(CSV_PATH, 'rb') as f:
            resp = self.client.post(
                "/upload",
                files={"file": ("online_retail_II.csv", f, "text/csv")}
            )
        if resp.status_code == 200:
            self.filename = resp.json()["filename"]
        else:
            self.filename = "online_retail_II.csv"

    @task(3)
    def query_brand_sales(self):
        """高频任务：查询品牌销售额（权重3）"""
        self.client.post(
            "/query",
            json={
                "filename": self.filename,
                "question": "哪个品牌销售额最高？"
            },
            name="/query [品牌销售]"
        )

    @task(2)
    def query_event_count(self):
        """中频任务：查询事件分布（权重2）"""
        self.client.post(
            "/query",
            json={
                "filename": self.filename,
                "question": "每个event_type各有多少条记录？"
            },
            name="/query [事件统计]"
        )

    @task(1)
    def query_price_stats(self):
        """低频任务：查询价格统计（权重1）"""
        self.client.post(
            "/query",
            json={
                "filename": self.filename,
                "question": "price字段的平均值和最大值是多少？"
            },
            name="/query [价格统计]"
        )

    @task(1)
    def upload_file(self):
        """上传接口压测"""
        with open(CSV_PATH, 'rb') as f:
            self.client.post(
                "/upload",
                files={"file": ("online_retail_II.csv", f, "text/csv")},
                name="/upload"
            )