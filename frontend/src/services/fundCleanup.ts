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
    }
  }

  /**
   * 执行数据清理
   * - 清理过期缓存
   * - 清理无用的时间戳
   * - 输出统计信息
   */
  async cleanup(): Promise<void> {
    try {
      // 1. 清理 IndexedDB 中的过期数据
      await fundStorage.cleanupExpiredData();

      // 2. 清理 localStorage 中无用的时间戳
      this.cleanupLocalStorage();

      // 3. 获取统计信息
      const stats = await fundStorage.getStats();

      console.log('[数据清理] 清理完成，统计:', stats);

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
    }
  }

  /**
   * 强制刷新指定基金的所有缓存
   * @param fundCode 基金代码
   */
  async refreshFundCache(fundCode: string): Promise<void> {
    
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

  }

  /**
   * 清空所有基金缓存数据
   */
  async clearAllCache(): Promise<void> {
    
    await fundStorage.clearAll();
    
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
      return;
    }
    
    try {
      // 只更新传入的自选基金列表，不获取所有基金代码
      // 这样可以避免一次性更新 2 万多只基金
      await this.updateWithValidation(fundCodes, onUpdate);
    } catch (error) {
      console.error('[数据更新] 更新失败:', error);
    }
  }
  
  /**
   * 执行数据更新（带验证）
   * @param fundCodes 基金代码列表
   * @param onUpdate 更新回调
   */
  private async updateWithValidation(
    fundCodes: string[],
    onUpdate?: (code: string, data: any) => void
  ): Promise<void> {
    // 过滤掉无效的基金代码
    const validCodes = fundCodes.filter((code) => {
      // 必须是字符串
      if (typeof code !== 'string') return false;
      // 不能包含 'nan'（不区分大小写）
      if (code.toLowerCase().includes('nan')) return false;
      // 必须是 6 位数字
      if (!/^\d{6}$/.test(code)) return false;
      return true;
    });
    
    if (validCodes.length === 0) {
      return;
    }
    
    if (validCodes.length < fundCodes.length) {
      console.warn(`[数据更新] 过滤了 ${fundCodes.length - validCodes.length} 只无效基金代码`);
    }


    try {
      // 分批更新，每批 50 只
      const batchSize = 50;
      for (let i = 0; i < validCodes.length; i += batchSize) {
        const batch = validCodes.slice(i, i + batchSize);
        
        // 强制刷新缓存
        const fundModule = await import('./fund');
        const response = await fundModule.fundApi.getFundRealtimeRate(batch);
        
        const dataList = Array.isArray(response.data) ? response.data : [response.data];
        
        // 调用更新回调
        if (onUpdate) {
          dataList.forEach((item: any) => onUpdate(item.code, item));
        }
      }

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


    try {
      // 先从后端获取全部有效基金代码
      const fundModule = await import('./fund');
      const allValidCodes = await fundModule.fundApi.getAllFundCodes();
      
      if (allValidCodes.length === 0) {
        console.warn('[数据更新] 未能从后端获取有效基金代码，使用传入的列表');
        // 降级处理：使用传入的列表（但会过滤无效代码）
        await this.performBackgroundUpdate(fundCodes);
        return;
      }
      
      // 使用从后端获取的有效代码列表
      
      // 使用 requestIdleCallback 在浏览器空闲时执行
      if ('requestIdleCallback' in window) {
        (window as any).requestIdleCallback(() => {
          this.performBackgroundUpdate(allValidCodes);
        });
      } else {
        // 降级处理
        setTimeout(() => {
          this.performBackgroundUpdate(allValidCodes);
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
    const fundModule = await import('./fund');
    
    // 过滤掉无效的基金代码
    const validCodes = fundCodes.filter((code) => {
      // 必须是字符串
      if (typeof code !== 'string') return false;
      // 不能包含 'nan'（不区分大小写）
      if (code.toLowerCase().includes('nan')) return false;
      // 必须是 6 位数字
      if (!/^\d{6}$/.test(code)) return true;
    });
    
    if (validCodes.length === 0) {
      return;
    }
    
    
    const updatePromises = validCodes.map(async (code) => {
      try {
        // 并行更新不同类型的数据
        await Promise.all([
          fundModule.fundApi.getFundHistory(code).catch((e) => { console.warn(`[fundCleanup] 获取 ${code} 历史净值失败:`, e) }),
          fundModule.fundApi.getFundPeriodChange(code).catch((e) => { console.warn(`[fundCleanup] 获取 ${code} 阶段涨跌幅失败:`, e) }),
        ]);
      } catch (error) {
        console.warn(`[数据更新] 更新基金 ${code} 失败:`, error);
      }
    });

    await Promise.all(updatePromises);
  }
}

// 导出单例
export const fundCleanup = new FundDataCleanup();
export const fundUpdater = new FundDataUpdater();

export default {
  cleanup: fundCleanup,
  updater: fundUpdater,
};
