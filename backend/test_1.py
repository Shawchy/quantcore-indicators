import akshare as ak

# 申万行业分类（官方最新接口）
df = ak.stock_industry_sw_new()
print(df.head())