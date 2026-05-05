//! 绩效报告生成器

use super::metrics::PerformanceMetrics;
use crate::core::Trade;

/// 报告格式
pub enum ReportFormat {
    Html,
    Pdf,
    Markdown,
    Json,
}

/// 绩效报告生成器
pub struct ReportGenerator {
    trades: Vec<Trade>,
    metrics: PerformanceMetrics,
}

impl ReportGenerator {
    pub fn new(trades: Vec<Trade>, metrics: PerformanceMetrics) -> Self {
        Self { trades, metrics }
    }

    pub fn generate_html(&self) -> String {
        format!(
            r#"<!DOCTYPE html>
<html><head><title>Performance Report</title>
<style>body{{font-family:sans-serif;margin:20px}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px;text-align:right}}th{{background:#f5f5f5}}</style>
</head><body>
<h1>Performance Report</h1>
<h2>Summary</h2>
<table>
<tr><th>Total Return</th><td>{:.2}%</td></tr>
<tr><th>Annual Return</th><td>{:.2}%</td></tr>
<tr><th>Sharpe Ratio</th><td>{:.2}</td></tr>
<tr><th>Max Drawdown</th><td>{:.2}%</td></tr>
<tr><th>Total Trades</th><td>{}</td></tr>
</table>
</body></html>"#,
            self.metrics.total_return * 100.0,
            self.metrics.annual_return * 100.0,
            self.metrics.sharpe_ratio,
            self.metrics.max_drawdown * 100.0,
            self.trades.len(),
        )
    }

    pub fn generate_pdf(&self) -> Vec<u8> {
        Vec::new()
    }

    pub fn generate_markdown(&self) -> String {
        format!(
            r#"# Performance Report

## Summary

| Metric | Value |
|--------|-------|
| Total Return | {:.2}% |
| Annual Return | {:.2}% |
| Sharpe Ratio | {:.2} |
| Max Drawdown | {:.2}% |
| Total Trades | {} |
"#,
            self.metrics.total_return * 100.0,
            self.metrics.annual_return * 100.0,
            self.metrics.sharpe_ratio,
            self.metrics.max_drawdown * 100.0,
            self.trades.len(),
        )
    }
}
