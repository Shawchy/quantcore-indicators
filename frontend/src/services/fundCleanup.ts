/**
 * 基金数据清理和更新工具
 * 
 * 提供定期清理过期数据、更新缓存等功能
 */
import fundStorage from './fundStorage'

/**
 * 数据清理工具类
 */
class FundDataCleanup {
  private cleanupInterval: NodeJS.Timeout | null = null;
  private readonly DEFAULT_CLEANUP_INTERVAL = 60 * 60 * 1000; // 1 小时

  /**
   * 启动定期清理任务
   * @param intervalMs 清理间隔（毫秒），默认 1 小时
   */
  startPeriodicCleanup(intervalMs: number = this.DEFAULT_CLEANUP_INTERVAL): void {
    if (this.cleanupInterval) {
      this.stopPeriodicCleanup();
    }

    console.log(`[数据清理] 启动定期清理任务，间隔：${intervalMs / 1000}秒`);
    
    // 立即执行一次
    this.cleanup();
    
    // 定期执行
    this.cleanupInterval = setInterval(() => {
      this.cleanup();
    }, intervalMs);
  }

  /**
   * 停止定期清理任务
   */
  stopPeriodicCleanup(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
      console.log('[数据清理] 停止定期清理任务');
    }
  }

  /**
   * 执行数据清理
   * - 清理过期缓存
   * - 清理无用的时间戳
   * - 输出统计信息
   */
  async cleanup(): Promise<void> {
    console.log('[数据清理] 开始清理过期数据...');
    const startTime = Date.now();

    try {
      // 1. 清理 IndexedDB 中的过期数据
      await fundStorage.cleanupExpiredData();

      // 2. 清理 localStorage 中无用的时间戳
      this.cleanupLocalStorage();

      // 3. 获取统计信息
      const stats = await fundStorage.getStats();

      const duration = Date.now() - startTime;
      console.log(`[数据清理] 清理完成，耗时：${duration}ms`);
      console.log('[数据清理] 存储统计:', stats);

    } catch (error) {
      console.error('[数据清理] 清理失败:', error);
    }
  }

  /**
   * 清理 localStorage 中的无用时间戳
   */
  private cleanupLocalStorage(): void {
    const timestampPrefixes = [
      'fund:realtime:ts:',
      'fund:history:ts:',
      'fund:base:ts:',
      'fund:period:ts:',
      'fund:assets:ts:',
    ];

    const now = Date.now();
    let removedCount = 0;

    // 遍历所有 localStorage 项
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (!key) continue;

      // 检查是否是时间戳键
      const isTimestampKey = timestampPrefixes.some(prefix => key.startsWith(prefix));
      if (!isTimestampKey) continue;

      // 检查是否过期
      const timestamp = parseInt(localStorage.getItem(key) || '0', 10);
      const cacheAge = now - timestamp;

      // 根据键类型判断过期时间
      let isExpired = false;
      if (key.includes('realtime')) {
        isExpired = cacheAge > 60 * 1000; // 60 秒
      } else if (key.includes('history') || key.includes('period') || key.includes('assets')) {
        isExpired = cacheAge > 7 * 24 * 60 * 60 * 1000; // 7 天
      } else if (key.includes('base')) {
        isExpired = cacheAge > 30 * 24 * 60 * 60 * 1000; // 30 天
      }

      if (isExpired) {
        localStorage.removeItem(key);
        removedCount++;
        
        // 同时删除对应的数据键
        const dataKey = key.replace(':ts:', ':');
        fundStorage.delete(dataKey).catch(err => {
          console.warn(`[数据清理] 删除数据键失败 ${dataKey}:`, err);
        });
      }
    }

    if (removedCount > 0) {
      console.log(`[数据清理] 清理了 ${removedCount} 个过期的 localStorage 时间戳`);
    }
  }

  /**
   * 强制刷新指定基金的所有缓存
   * @param fundCode 基金代码
   */
  async refreshFundCache(fundCode: string): Promise<void> {
    console.log(`[数据清理] 强制刷新基金 ${fundCode} 的缓存`);
    
    const prefixes = [
      'fund:realtime:',
      'fund:history:',
      'fund:base:',
      'fund:period:',
      'fund:assets:',
    ];

    const promises = prefixes.map(prefix => 
      fundStorage.delete(`${prefix}${fundCode}`)
    );

    await Promise.all(promises);
    
    // 清理时间戳
    Object.keys(localStorage).forEach(key => {
      if (key.includes(fundCode) && key.includes('fund:')) {
        localStorage.removeItem(key);
      }
    });

    console.log(`[数据清理] 基金 ${fundCode} 的缓存已刷新`);
  }

  /**
   * 清空所有基金缓存数据
   */
  async clearAllCache(): Promise<void> {
    console.log('[数据清理] 清空所有缓存数据...');
    
    await fundStorage.clearAll();
    
    console.log('[数据清理] 所有缓存数据已清空');
  }
}

/**
 * 数据更新工具类
 */
class FundDataUpdater {
  /**
   * 更新自选基金列表的实时数据
   * @param fundCodes 自选基金代码列表
   * @param onUpdate 更新回调
   */
  async updateWatchlistRealtimeData(
    fundCodes: string[],
    onUpdate?: (code: string, data: any) => void
  ): Promise<void> {
    if (fundCodes.length === 0) {
      console.log('[数据更新] 自选列表为空，跳过更新');
      return;
    }

    console.log(`[数据更新] 更新 ${fundCodes.length} 只自选基金的实时数据`);

    try {
      // 分批更新，每批 50 只
      const batchSize = 50;
      for (let i = 0; i < fundCodes.length; i += batchSize) {
        const batch = fundCodes.slice(i, i + batchSize);
        console.log(`[数据更新] 更新批次 ${Math.floor(i / batchSize) + 1}/${Math.ceil(fundCodes.length / batchSize)}`);
        
        // 强制刷新缓存
        const { data } = await import('./fund');
        const response = await data.fundApi.getFundRealtimeRate(batch);
        
        const dataList = Array.isArray(response.data) ? response.data : [response.data];
        
        // 调用更新回调
        if (onUpdate) {
          dataList.forEach(item => onUpdate(item.code, item));
        }
      }

      console.log('[数据更新] 自选基金实时数据更新完成');
    } catch (error) {
      console.error('[数据更新] 更新失败:', error);
    }
  }

  /**
   * 后台静默更新数据
   * 在页面空闲时更新常用基金的缓存
   */
  async backgroundUpdate(fundCodes: string[]): Promise<void> {
    if (fundCodes.length === 0) return;

    console.log('[数据更新] 开始后台静默更新...');

    try {
      // 使用 requestIdleCallback 在浏览器空闲时执行
      if ('requestIdleCallback' in window) {
        (window as any).requestIdleCallback(() => {
          this.performBackgroundUpdate(fundCodes);
        });
      } else {
        // 降级处理
        setTimeout(() => {
          this.performBackgroundUpdate(fundCodes);
        }, 1000);
      }
    } catch (error) {
      console.error('[数据更新] 后台更新失败:', error);
    }
  }

  /**
   * 执行后台更新
   */
  private async performBackgroundUpdate(fundCodes: string[]): Promise<void> {
    const { data } = await import('./fund');
    
    // 更新基本信息（30 天有效期，不需要频繁更新）
    // 更新历史净值（7 天有效期）
    // 更新阶段涨跌幅（7 天有效期）
    
    const updatePromises = fundCodes.map(async (code) => {
      try {
        // 并行更新不同类型的数据
        await Promise.all([
          data.fundApi.getFundHistory(code).catch(() => {}),
          data.fundApi.getFundPeriodChange(code).catch(() => {}),
        ]);
      } catch (error) {
        console.warn(`[数据更新] 更新基金 ${code} 失败:`, error);
      }
    });

    await Promise.all(updatePromises);
    console.log('[数据更新] 后台静默更新完成');
  }
}

// 导出单例
export const fundCleanup = new FundDataCleanup();
export const fundUpdater = new FundDataUpdater();

export default {
  cleanup: fundCleanup,
  updater: fundUpdater,
};
