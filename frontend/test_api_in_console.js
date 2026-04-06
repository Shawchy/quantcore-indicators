// 在浏览器控制台执行此脚本，测试 API 数据

console.log("=".repeat(60));
console.log("测试前端 API 数据获取");
console.log("=".repeat(60));

// 测试 1: 直接 fetch API
console.log("\n📡 测试 1: 直接 fetch API");
fetch('http://localhost:8000/api/v1/screener/market-stats')
  .then(response => {
    console.log(`✅ 响应状态码：${response.status}`);
    return response.json();
  })
  .then(data => {
    console.log("\n✅ API 响应数据:");
    console.log(JSON.stringify(data, null, 2));

    console.log("\n📊 数据分析:");
    console.log(`  - total_stocks: ${data.data?.total_stocks}`);
    console.log(`  - industry_distribution: ${Object.keys(data.data?.industry_distribution || {}).length} 个行业`);
    console.log(`  - turnover: ${data.data?.turnover}`);

    if (data.data?.total_stocks === 5497) {
      console.log("\n✅ 数据正确！后端返回 5497 只股票");
    } else {
      console.log("\n❌ 数据异常！total_stocks 不是 5497");
    }
  })
  .catch(error => {
    console.error("\n❌ 请求失败:", error);
  });

// 测试 2: 检查 React Query 缓存
console.log("\n\n📦 测试 2: 检查 React Query 缓存");
setTimeout(() => {
  if (window.__REACT_QUERY_CLIENT__) {
    const cache = window.__REACT_QUERY_CLIENT__.getQueryCache();
    const queries = cache.getAll();

    console.log(`React Query 缓存中有 ${queries.length} 个查询`);

    const marketStatsQuery = queries.find(q => q.queryKey?.includes('marketStats'));
    if (marketStatsQuery) {
      console.log("\n✅ 找到 marketStats 查询:");
      console.log(`  - 状态：${marketStatsQuery.state.status}`);
      console.log(`  - 数据：`, marketStatsQuery.state.data);

      if (marketStatsQuery.state.data) {
        console.log(`  - total_stocks: ${marketStatsQuery.state.data.total_stocks}`);
      }
    } else {
      console.log("\n❌ 未找到 marketStats 查询");
    }
  } else {
    console.log("❌ 未找到 React Query 客户端");
  }
}, 2000);

console.log("\n" + "=".repeat(60));
console.log("测试完成，请查看上面的输出");
console.log("=".repeat(60));
