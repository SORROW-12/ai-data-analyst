from flask import Flask, request, jsonify, render_template
import pandas as pd
import sqlite3
import json
import os
import requests

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DEEPSEEK_KEY = "sk-fa7c456063a747a587233dc1effa4439"  
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

def call_llm(messages, tools=None):
    headers = {
        "Authorization": "Bearer " + DEEPSEEK_KEY,
        "Content-Type": "application/json"
    }
    payload = {"model": "deepseek-chat", "messages": messages}
    if tools:
        payload["tools"] = tools
    resp = requests.post(DEEPSEEK_URL, json=payload, headers=headers)
    return resp.json()

def run_sql(df, sql):
    conn = sqlite3.connect(':memory:')
    df.to_sql('data', conn, index=False, if_exists='replace')
    try:
        result = pd.read_sql_query(sql, conn)
        return result.to_string()
    except Exception as e:
        return "SQL error: " + str(e)
    finally:
        conn.close()

def check_quality(df):
    report = {}
    missing = df.isnull().sum()
    report['missing'] = {col: int(missing[col]) for col in df.columns if missing[col] > 0}
    report['duplicates'] = int(df.duplicated().sum())
    report['rows'] = len(df)
    report['cols'] = len(df.columns)
    numeric_cols = df.select_dtypes(include='number').columns
    outliers = {}
    for col in numeric_cols:
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        count = int(((df[col] < q1 - 1.5*iqr) | (df[col] > q3 + 1.5*iqr)).sum())
        if count > 0:
            outliers[col] = count
    report['outliers'] = outliers
    return report

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(path)
    df = pd.read_csv(path, encoding='latin-1')
    report = check_quality(df)
    return jsonify({'success': True, 'filename': file.filename, 'quality': report})

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    filename = data['filename']
    question = data['question']
    path = os.path.join(UPLOAD_FOLDER, filename)
    df = pd.read_csv(path, encoding='latin-1')
    cols = [str(c) for c in df.columns.tolist()]

    tools = [
        {
            "type": "function",
            "function": {
                "name": "run_sql_query",
                "description": "Execute SQL query on the data",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "SQL query, table name is data"}
                    },
                    "required": ["sql"]
                }
            }
        }
    ]

    messages = [
        {"role": "system", "content": "You are a data analyst. Column names: " + str(cols) + ". Use SQL to query data and answer in Chinese."},
        {"role": "user", "content": question}
    ]

    result = call_llm(messages, tools)
    msg = result["choices"][0]["message"]

    if msg.get("tool_calls"):
        sql = json.loads(msg["tool_calls"][0]["function"]["arguments"])["sql"]
        sql_result = run_sql(df, sql)
        messages.append(msg)
        messages.append({
            "role": "tool",
            "tool_call_id": msg["tool_calls"][0]["id"],
            "content": sql_result
        })
        final = call_llm(messages)
        return jsonify({'answer': final["choices"][0]["message"]["content"], 'sql': sql})

    return jsonify({'answer': msg["content"], 'sql': ''})

if __name__ == '__main__':
    app.run(debug=True, port=5000)