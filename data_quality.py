import pandas as pd
import json
from openai import OpenAI

client = OpenAI(
    api_key="sk-fa7c456063a747a587233dc1effa4439",  
    base_url="https://api.deepseek.com"
)

def check_data_quality(file_path: str) -> dict:
    """自动检测数据质量问题"""
    df = pd.read_csv(file_path, encoding='latin-1')
    
    report = {}
    
    # 1. 基础信息
    report['basic'] = {
        '总行数': len(df),
        '总列数': len(df.columns),
        '列名': df.columns.tolist()
    }
    
    # 2. 缺失值检测
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    report['missing_values'] = {
        col: f"{missing[col]}行缺失 ({missing_pct[col]}%)"
        for col in df.columns if missing[col] > 0
    }
    
    # 3. 重复数据检测
    duplicates = df.duplicated().sum()
    report['duplicates'] = f"共{duplicates}行重复数据"
    
    # 4. 异常值检测（数值列）
    numeric_cols = df.select_dtypes(include='number').columns
    outliers = {}
    for col in numeric_cols:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_count = ((df[col] < lower) | (df[col] > upper)).sum()
        if outlier_count > 0:
            outliers[col] = f"{outlier_count}个异常值 (正常范围: {lower:.2f}~{upper:.2f})"
    report['outliers'] = outliers
    
    # 5. 负值检测（销售数据不应有负值）
    negatives = {}
    for col in numeric_cols:
        neg_count = (df[col] < 0).sum()
        if neg_count > 0:
            negatives[col] = f"{neg_count}个负值"
    report['negative_values'] = negatives
    
    return report, df

def ai_fix_suggestions(report: dict) -> str:
    """用LLM对质量问题给出修复建议"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": "你是数据工程师，根据数据质量检测报告给出具体的修复建议和处理优先级，用中文回答。"
            },
            {
                "role": "user",
                "content": f"数据质量报告：\n{json.dumps(report, ensure_ascii=False, indent=2)}\n\n请给出：1.问题严重程度评估 2.修复优先级 3.每个问题的具体修复方案"
            }
        ]
    )
    return response.choices[0].message.content

def generate_data_dict(file_path: str) -> str:
    """用LLM自动生成数据字典"""
    df = pd.read_csv(file_path, encoding='latin-1')
    sample = df.head(3).to_string()
    cols_info = {col: str(df[col].dtype) for col in df.columns}
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": "你是数据分析师，根据列名、数据类型和样本数据，生成规范的数据字典，包含字段名、数据类型、字段含义、取值范围。"
            },
            {
                "role": "user",
                "content": f"列信息：{cols_info}\n\n样本数据：\n{sample}\n\n请生成完整的数据字典。"
            }
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    file_path = r"C:\Users\26817\online_retail_II.csv"
    
    print("=" * 50)
    print("数据质量检测报告")
    print("=" * 50)
    
    report, df = check_data_quality(file_path)
    
    print(f"\n【基础信息】")
    print(f"总行数：{report['basic']['总行数']}，总列数：{report['basic']['总列数']}")
    
    print(f"\n【缺失值】")
    for col, info in report['missing_values'].items():
        print(f"  {col}: {info}")
    
    print(f"\n【重复数据】{report['duplicates']}")
    
    print(f"\n【异常值】")
    for col, info in report['outliers'].items():
        print(f"  {col}: {info}")
    
    print(f"\n【负值检测】")
    for col, info in report['negative_values'].items():
        print(f"  {col}: {info}")
    
    print("\n" + "=" * 50)
    print("AI修复建议")
    print("=" * 50)
    suggestions = ai_fix_suggestions(report)
    print(suggestions)
    
    print("\n" + "=" * 50)
    print("自动生成数据字典")
    print("=" * 50)
    data_dict = generate_data_dict(file_path)
    print(data_dict)