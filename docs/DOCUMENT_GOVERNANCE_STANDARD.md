# 文档管理规范 v1.0

**生效日期**: 2026-04-27

---

## 1. 文档分类体系

| 目录 | 内容 | 维护频率 |
|------|------|---------|
| `docs/architecture/` | 架构设计、ADR、数据流图 | 架构变更时 |
| `docs/guides/` | 使用指南、开发指南、API 参考 | 功能更新时 |
| `docs/features/` | 功能实现、集成方案、选型报告 | 功能上线时 |
| `docs/changelogs/` | 版本更新日志 | 每次发布 |
| `docs/reports/` | 检查报告、实施总结、性能报告 | 季度/项目结束 |

---

## 2. 命名规范

- **统一使用英文小写 + 下划线**: `data_classification_storage_plan.md`
- **CHANGELOG 按版本**: `CHANGELOG_MODULE_V1.0.md`
- **ADR 按序号**: `ADR-001.md`
- **报告含日期**: `code_review_20260427.md`

---

## 3. 文档模板

每个文档开头应包含：

```markdown
# 文档标题

**版本**: v1.0 | **最后更新**: YYYY-MM-DD | **作者**: XXX

简短描述...
```

---

## 4. 定期审查

| 周期 | 操作 |
|------|------|
| 每月 | 检查新文档是否放在正确目录 |
| 每季度 | 审查过时文档，标记并移至 archive/ |
| 每半年 | 合并同类文档，减少冗余 |

---

## 5. 贡献流程

1. 新功能 → 同步更新 `docs/features/`
2. 架构变更 → 创建/更新 `docs/architecture/ADR-XXX.md`
3. Bug 修复 → 更新相关功能文档
4. 提交代码前 → 检查文档完整性

---

## 6. 归档策略

| 条件 | 操作 |
|------|------|
| 超过 6 个月的修复记录 | 移至 `archive/fix_reports/` |
| 过时的架构设计 | 移至 `archive/old_architecture/` |
| 已被替代的功能文档 | 移至 `archive/legacy_features/` |
