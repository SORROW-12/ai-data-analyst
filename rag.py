import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI

client = OpenAI(
    api_key="sk-fa7c456063a747a587233dc1effa4439",  # 换成你的DeepSeek key
    base_url="https://api.deepseek.com"
)

# 初始化向量数据库和embedding模型
chroma_client = chromadb.Client()
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def build_knowledge_base(file_path: str):
    """从CSV构建RAG知识库"""
    print("正在构建知识库...")
    df = pd.read_csv(file_path, encoding='latin-1')
    
    # 生成数据洞察文本片段
    docs = []
    
    # 国家销售额分析
    country_sales = df.groupby('Country').apply(
        lambda x: (x['Quantity'] * x['Price']).sum()
    ).sort_values(ascending=False)
    docs.append(f"各国销售额排名：{country_sales.head(5).to_dict()}")
    
    # 月度趋势
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['Month'] = df['InvoiceDate'].dt.to_period('M')
    monthly = df.groupby('Month').apply(
        lambda x: (x['Quantity'] * x['Price']).sum()
    )
    docs.append(f"月度销售趋势：{monthly.to_dict()}")
    
    # 热销商品
    top_products = df.groupby('Description')['Quantity'].sum().sort_values(ascending=False).head(10)
    docs.append(f"热销商品TOP10：{top_products.to_dict()}")
    
    # 基础统计
    total_revenue = (df['Quantity'] * df['Price']).sum()
    total_orders = df['Invoice'].nunique()
    total_countries = df['Country'].nunique()
    docs.append(f"总体统计：总销售额£{total_revenue:.2f}，总订单数{total_orders}，覆盖{total_countries}个国家")
    
    # 存入向量数据库
    collection = chroma_client.get_or_create_collection("retail_knowledge")
    embeddings = embedding_model.encode(docs).tolist()
    collection.add(
        documents=docs,
        embeddings=embeddings,
        ids=[f"doc_{i}" for i in range(len(docs))]
    )
    print(f"知识库构建完成，共{len(docs)}个知识片段")
    return collection

def rag_query(collection, question: str) -> str:
    """用RAG回答问题"""
    # 检索相关知识
    query_embedding = embedding_model.encode([question]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=2)
    context = "\n".join(results['documents'][0])
    
    # 调用LLM生成答案
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是专业数据分析师，基于提供的数据背景回答问题，给出业务洞察。用中文回答。"},
            {"role": "user", "content": f"数据背景：\n{context}\n\n问题：{question}"}
        ]
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    file_path = r"C:\Users\26817\online_retail_II.csv"
    
    collection = build_knowledge_base(file_path)
    
    questions = [
        "为什么11月销售额最高？有什么业务解释？",
        "哪些国家是核心市场？应该如何针对性运营？",
    ]
    
    for q in questions:
        print(f"\n{'='*50}")
        print(f"问题：{q}")
        print('='*50)
        result = rag_query(collection, q)
        print(f"回答：\n{result}")