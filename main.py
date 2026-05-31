import pandas as pd
import json
from openai import OpenAI
from pandasql import sqldf

# 初始化客户端
client = OpenAI(
    api_key="sk-fa7c456063a747a587233dc1effa4439",
    base_url="https://api.deepseek.com"
)

# 全局存储dataframe，让SQL函数能访问
df_global = None

def run_sql(sql: str) -> str:
    """执行SQL查询，返回结果"""
    global df_global
    try:
        result = sqldf(sql, {"df": df_global})
        return result.to_string(index=False)
    except Exception as e:
        return f"SQL执行错误：{str(e)}"

def analyze_with_agent(file_path: str, question: str) -> str:
    global df_global
    
    # 读取数据
    df_global = pd.read_csv(file_path, encoding='latin-1')
    
    # 数据结构摘要
    schema = f"""
表名：df
列名及类型：
{df_global.dtypes.to_string()}
数据行数：{len(df_global)}
前3行样本：
{df_global.head(3).to_string()}
    """
    
    # 定义工具
    tools = [
        {
            "type": "function",
            "function": {
                "name": "run_sql",
                "description": "对数据集执行SQL查询，返回精确的查询结果。表名固定为df。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "要执行的SQL语句，表名为df"
                        }
                    },
                    "required": ["sql"]
                }
            }
        }
    ]
    
    messages = [
        {
            "role": "system",
            "content": f"你是专业数据分析师。数据结构如下：\n{schema}\n\n请用SQL查询获取精确数据后回答问题，用中文回答。"
        },
        {
            "role": "user",
            "content": question
        }
    ]
    
    print("AI正在思考并执行查询...")
    
    # Agent循环：让AI反复调用工具直到得出答案
    while True:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        msg = response.choices[0].message
        
        # 如果AI调用了工具
        if msg.tool_calls:
            messages.append(msg)
            
            for tool_call in msg.tool_calls:
                sql = json.loads(tool_call.function.arguments)["sql"]
                print(f"\n执行SQL：{sql}")
                
                result = run_sql(sql)
                print(f"查询结果：\n{result}")
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            # AI给出最终答案
            return msg.content

# 测试
if __name__ == "__main__":
    file_path = r"C:\Users\26817\online_retail_II.csv"
    
    questions = [
        "一共有多少个国家？哪个国家销售额最高？给出具体金额。",
        "销售数量最多的前5个商品是什么？",
        "每个月的总销售额是多少？哪个月最高？"
    ]
    
    for q in questions:
        print(f"\n{'='*50}")
        print(f"问题：{q}")
        print('='*50)
        result = analyze_with_agent(file_path, q)
        print(f"\n最终答案：\n{result}")