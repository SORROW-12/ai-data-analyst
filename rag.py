import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI
import json

# 初始化客户端
client = OpenAI(
    api_key="sk-fa7c456063a747a587233dc1effa4439",
    base_url="https://api.deepseek.com"
)

# 初始化ChromaDB（本地向量数据库）
chroma_client = chromadb.Client()

# 使用本地免费embedding模型
ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)

def build_knowledge_base(file_path: str) -> chromadb.Collection:
    """把CSV数据转成向量知识库"""
    print("正在构建知识库，请稍候...")
    
    df = pd.read_csv(file_path, encoding='latin-1')
    df['Revenue'] = df['Quantity'] * df['Price']
    
    # 生成多维度数据摘要文本块
    chunks = []
    ids = []
    
    # 1. 整体概览
    chunks.append(f"数据集共{len(df)}条记录，{df['Customer ID'].nunique():.0f}个客户，"
                  f"{df['Country'].nunique()}个国家，{df['StockCode'].nunique()}个商品，"
                  f"总销售额£{df['Revenue'].sum():,.0f}")
    ids.append("overview")
    
    # 2. 各国家销售额
    country_sales = df.groupby('Country')['Revenue'].sum().sort_values(ascending=False)
    for i, (country, revenue) in enumerate(country_sales.head(10).items()):
        chunks.append(f"国家{country}的总销售额为£{revenue:,.0f}，排名第{i+1}")
        ids.append(f"country_{i}")
    
    # 3. 月度趋势
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['YearMonth'] = df['InvoiceDate'].dt.to_period('M').astype(str)
    monthly = df.groupby('YearMonth')['Revenue'].sum()
    for ym, rev in monthly.items():
        chunks.append(f"{ym}月的销售额为£{rev:,.0f}")
        ids.append(f"monthly_{ym}")
    
    # 4. 热销商品
    top_products = df.groupby('Description')['Quantity'].sum().sort_values(ascending=False)
    for i, (product, qty) in enumerate(top_products.head(10).items()):
        chunks.append(f"商品{product}的总销售数量为{qty:,}件，是第{i+1}畅销商品")
        ids.append(f"product_{i}")
    
    # 5. 用户价值分析
    customer_value = df.groupby('Customer ID')['Revenue'].sum().sort_values(ascending=False)
    chunks.append(f"最高价值客户消费额为£{customer_value.iloc[0]:,.0f}，"
                  f"前10%客户贡献了约{customer_value.head(int(len(customer_value)*0.1)).sum()/customer_value.sum()*100:.1f}%的销售额")
    ids.append("customer_value")
    
    # 存入向量数据库
    collection = chroma_client.get_or_create_collection(
        name="sales_data",
        embedding_function=ef
    )
    
    collection.add(documents=chunks, ids=ids)
    print(f"知识库构建完成，共{len(chunks)}个知识块")
    return collection

def rag_query(collection: chromadb.Collection, question: str) -> str:
    """RAG查询：检索相关知识 + AI生成答案"""
    
    # 1. 从向量库检索最相关的知识块
    results = collection.query(
        query_texts=[question],
        n_results=5
    )
    
    retrieved_docs = results['documents'][0]
    context = "\n".join(retrieved_docs)
    
    print(f"\n检索到的相关知识：")
    for doc in retrieved_docs:
        print(f"  · {doc}")
    
    # 2. 让AI基于检索结果生成答案
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": "你是专业数据分析师。根据以下检索到的数据知识回答问题，用中文回答，给出具体数字和洞察。"
            },
            {
                "role": "user",
                "content": f"检索到的相关数据：\n{context}\n\n问题：{question}"
            }
        ]
    )
    
    return response.choices[0].message.content

# 主程序
if __name__ == "__main__":
    file_path = r"C:\Users\26817\online_retail_II.csv"
    
    # 构建知识库
    collection = build_knowledge_base(file_path)
    
    # 测试问题
    questions = [
        "哪个国家的销售额最高？",
        "销售额最好的月份是什么时候？",
        "最畅销的商品是什么？",
        "高价值客户贡献了多少销售额？"
    ]
    
    print("\n" + "="*50)
    print("RAG知识库问答系统启动")
    print("="*50)
    
    for q in questions:
        print(f"\n问题：{q}")
        print("-"*30)
        answer = rag_query(collection, q)
        print(f"答案：{answer}")