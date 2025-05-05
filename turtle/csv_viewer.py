import streamlit as st
import pandas as pd

def main():
    st.title("CSV 文件查看器")
    
    # 上传 CSV 文件
    # uploaded_file = st.file_uploader("请上传 CSV 文件", type=["csv"])
    
    # if uploaded_file is not None:
        # 读取 CSV
        # df = pd.read_csv(uploaded_file)
    df = pd.read_csv('data/hs300_stocks.csv')
    
    # 展示数据框
    st.write("### 文件内容：")
    st.dataframe(df)

if __name__ == "__main__":
    main()