/**
 * 基金数据存储服务
 * 
 * 提供基金数据的本地存储和缓存管理
 * - 实时估算数据：短期缓存（60 秒）
 * - 历史净值数据：持久化存储（7 天）
 * - 基金基本信息：持久化存储（30 天）
 * - 阶段涨跌幅数据：持久化存储（7 天）
 * - 资产配置数据：持久化存储（7 天）
 */

// 存储键前缀
const STORAGE_PREFIXES = {
  // 实时估算数据（短期缓存）
  REALTIME_RATE: 'fund:realtime:',
  RATE_TIMESTAMP: 'fund:realtime:ts:',
  
  // 历史数据（持久化）
  HISTORY: 'fund:history:',
  HISTORY_TIMESTAMP: 'fund:history:ts:',
  
  // 基本信息（持久化）
  BASE_INFO: 'fund:base:',
  BASE_INFO_TIMESTAMP: 'fund:base:ts:',
  
  // 阶段涨跌幅（持久化）
  PERIOD_CHANGE: 'fund:period:',
  PERIOD_CHANGE_TIMESTAMP: 'fund:period:ts:',
  
  // 资产配置（持久化）
  ASSETS: 'fund:assets:',
  ASSETS_TIMESTAMP: 'fund:assets:ts:',
  
  // 自选基金列表
  WATCHLIST: 'fund:watchlist',
} as const;

// 缓存过期时间（毫秒）
const CACHE_EXPIRY = {
  REALTIME_RATE: 60 * 1000,      // 60 秒 - 实时估算
  HISTORY: 7 * 24 * 60 * 60 * 1000,    // 7 天 - 历史净值
  BASE_INFO: 30 * 24 * 60 * 60 * 1000, // 30 天 - 基本信息
  PERIOD_CHANGE: 7 * 24 * 60 * 60 * 1000, // 7 天 - 阶段涨跌
  ASSETS: 7 * 24 * 60 * 60 * 1000,      // 7 天 - 资产配置
} as const;

/**
 * 数据存储服务类
 */
interface FundRealtimeData {
  code: string;
  name: string;
  net_value?: number;
  nav_date?: string;
  estimate_time?: string;
  estimate_change_pct?: number;
  gszzl?: string;
  gztime?: string;
  dwjz?: string;
}

interface FundHistoryItem {
  fund_code: string;
  date?: string;
  unit_nav?: number;
  accumulated_nav?: number;
  change_pct?: number;
  nav?: number;
  accNav?: number;
}

interface FundBaseInfo {
  code: string;
  name: string;
  establish_date?: string;
  change_pct?: number;
  net_asset_value?: number;
  fund_company?: string;
  nav_update_date?: string;
  description?: string;
  type?: string;
  fund_scale?: number;
  rank?: number;
}

interface FundPeriodItem {
  fund_code: string;
  period: string;
  return_rate?: number;
  avg_return?: number;
  rank?: number;
  total_count?: number;
  rank_rate?: number;
}

interface FundAssetItem {
  fund_code: string;
  report_date?: string;
  stock_ratio?: number;
  bond_ratio?: number;
  cash_ratio?: number;
  other_ratio?: number;
  total_scale?: number;
  asset_name?: string;
  ratio?: number;
}

class FundStorageService {
  private db: IDBDatabase | null = null;
  private dbName = 'FundDataDB';
  private dbVersion = 1;
  private storeName = 'fundData';

  constructor() {
    this.initIndexedDB();
  }

  private async getCached<T>(
    dataPrefix: string,
    tsPrefix: string,
    fundCode: string,
    expiry: number,
  ): Promise<T | null> {
    const key = `${dataPrefix}${fundCode}`;
    const tsKey = `${tsPrefix}${fundCode}`;

    const timestamp = localStorage.getItem(tsKey);
    if (!timestamp) {
      return null;
    }

    const cacheAge = Date.now() - parseInt(timestamp);
    if (cacheAge > expiry) {
      localStorage.removeItem(tsKey);
      await this.delete(key);
      return null;
    }

    return await this.get<T>(key);
  }

  private async setCached(
    dataPrefix: string,
    tsPrefix: string,
    fundCode: string,
    data: unknown,
    type: string,
    expiryMs: number,
  ): Promise<void> {
    const key = `${dataPrefix}${fundCode}`;
    const tsKey = `${tsPrefix}${fundCode}`;

    await Promise.all([
      this.set(key, data, type, fundCode, expiryMs / (24 * 60 * 60 * 1000)),
      localStorage.setItem(tsKey, Date.now().toString()),
    ]);
  }

  /**
   * 初始化 IndexedDB
   */
  private initIndexedDB(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => {
        console.error('IndexedDB 打开失败:', request.error);
        reject(request.error);
      };

      request.onsuccess = () => {
        this.db = request.result;
        console.log('IndexedDB 初始化成功');
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        
        // 创建对象仓库
        if (!db.objectStoreNames.contains(this.storeName)) {
          const store = db.createObjectStore(this.storeName, { keyPath: 'key' });
          store.createIndex('type', 'type', { unique: false });
          store.createIndex('timestamp', 'timestamp', { unique: false });
          store.createIndex('fundCode', 'fundCode', { unique: false });
        }
      };
    });
  }

  /**
   * 等待 DB 初始化完成
   */
  private async ensureDB(): Promise<void> {
    if (!this.db) {
      await this.initIndexedDB();
    }
  }

  /**
   * 存储数据到 IndexedDB
   */
  async set<T>(
    key: string,
    data: T,
    type: string,
    fundCode?: string,
    expiryDays?: number
  ): Promise<void> {
    await this.ensureDB();

    const transaction = this.db!.transaction([this.storeName], 'readwrite');
    const store = transaction.objectStore(this.storeName);

    const record = {
      key,
      data,
      type,
      fundCode,
      timestamp: Date.now(),
      expiryDays,
    };

    return new Promise((resolve, reject) => {
      const request = store.put(record);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * 从 IndexedDB 获取数据
   */
  async get<T>(key: string): Promise<T | null> {
    await this.ensureDB();

    const transaction = this.db!.transaction([this.storeName], 'readonly');
    const store = transaction.objectStore(this.storeName);

    return new Promise((resolve, reject) => {
      const request = store.get(key);
      request.onsuccess = () => {
        const record = request.result;
        if (!record) {
          resolve(null);
          return;
        }

        // 检查是否过期
        if (record.expiryDays) {
          const expiryTime = record.timestamp + record.expiryDays * 24 * 60 * 60 * 1000;
          if (Date.now() > expiryTime) {
            // 已过期，删除
            this.delete(key);
            resolve(null);
            return;
          }
        }

        resolve(record.data as T);
      };
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * 删除数据
   */
  async delete(key: string): Promise<void> {
    await this.ensureDB();

    const transaction = this.db!.transaction([this.storeName], 'readwrite');
    const store = transaction.objectStore(this.storeName);

    return new Promise((resolve, reject) => {
      const request = store.delete(key);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * 批量存储实时估算数据
   */
  async setRealtimeRate(fundCodes: string[], data: FundRealtimeData[]): Promise<void> {
    const promises = fundCodes.map((code, index) =>
      this.setCached(
        STORAGE_PREFIXES.REALTIME_RATE,
        STORAGE_PREFIXES.RATE_TIMESTAMP,
        code,
        data[index],
        'realtime',
        CACHE_EXPIRY.REALTIME_RATE,
      ),
    );
    await Promise.all(promises);
  }

  async getRealtimeRate(fundCode: string): Promise<FundRealtimeData | null> {
    return this.getCached<FundRealtimeData>(
      STORAGE_PREFIXES.REALTIME_RATE,
      STORAGE_PREFIXES.RATE_TIMESTAMP,
      fundCode,
      CACHE_EXPIRY.REALTIME_RATE,
    );
  }

  /**
   * 批量存储历史净值数据
   */
  async setHistory(fundCode: string, data: FundHistoryItem[]): Promise<void> {
    await this.setCached(
      STORAGE_PREFIXES.HISTORY,
      STORAGE_PREFIXES.HISTORY_TIMESTAMP,
      fundCode,
      data,
      'history',
      CACHE_EXPIRY.HISTORY,
    );
  }

  async getHistory(fundCode: string): Promise<FundHistoryItem[] | null> {
    return this.getCached<FundHistoryItem[]>(
      STORAGE_PREFIXES.HISTORY,
      STORAGE_PREFIXES.HISTORY_TIMESTAMP,
      fundCode,
      CACHE_EXPIRY.HISTORY,
    );
  }

  /**
   * 存储基金基本信息
   */
  async setBaseInfo(fundCode: string, data: FundBaseInfo): Promise<void> {
    await this.setCached(
      STORAGE_PREFIXES.BASE_INFO,
      STORAGE_PREFIXES.BASE_INFO_TIMESTAMP,
      fundCode,
      data,
      'base',
      CACHE_EXPIRY.BASE_INFO,
    );
  }

  async getBaseInfo(fundCode: string): Promise<FundBaseInfo | null> {
    return this.getCached<FundBaseInfo>(
      STORAGE_PREFIXES.BASE_INFO,
      STORAGE_PREFIXES.BASE_INFO_TIMESTAMP,
      fundCode,
      CACHE_EXPIRY.BASE_INFO,
    );
  }

  /**
   * 批量存储基金基本信息
   */
  async setBaseInfoBatch(fundCodes: string[], dataList: FundBaseInfo[]): Promise<void> {
    const promises = fundCodes.map((code, index) =>
      this.setBaseInfo(code, dataList[index])
    );
    await Promise.all(promises);
  }

  async setPeriodChange(fundCode: string, data: FundPeriodItem[]): Promise<void> {
    await this.setCached(
      STORAGE_PREFIXES.PERIOD_CHANGE,
      STORAGE_PREFIXES.PERIOD_CHANGE_TIMESTAMP,
      fundCode,
      data,
      'period',
      CACHE_EXPIRY.PERIOD_CHANGE,
    );
  }

  async getPeriodChange(fundCode: string): Promise<FundPeriodItem[] | null> {
    return this.getCached<FundPeriodItem[]>(
      STORAGE_PREFIXES.PERIOD_CHANGE,
      STORAGE_PREFIXES.PERIOD_CHANGE_TIMESTAMP,
      fundCode,
      CACHE_EXPIRY.PERIOD_CHANGE,
    );
  }

  /**
   * 存储资产配置数据
   */
  async setAssets(fundCode: string, data: FundAssetItem[]): Promise<void> {
    await this.setCached(
      STORAGE_PREFIXES.ASSETS,
      STORAGE_PREFIXES.ASSETS_TIMESTAMP,
      fundCode,
      data,
      'assets',
      CACHE_EXPIRY.ASSETS,
    );
  }

  async getAssets(fundCode: string): Promise<FundAssetItem[] | null> {
    return this.getCached<FundAssetItem[]>(
      STORAGE_PREFIXES.ASSETS,
      STORAGE_PREFIXES.ASSETS_TIMESTAMP,
      fundCode,
      CACHE_EXPIRY.ASSETS,
    );
  }

  /**
   * 管理自选基金列表
   */
  getWatchlist(): string[] {
    const stored = localStorage.getItem(STORAGE_PREFIXES.WATCHLIST);
    if (!stored) return [];
    
    try {
      const list = JSON.parse(stored);
      if (!Array.isArray(list)) return [];
      
      // 过滤掉无效的基金代码
      return list.filter((code: string) => {
        // 必须是字符串
        if (typeof code !== 'string') return false;
        // 不能包含 'nan'（不区分大小写）
        if (code.toLowerCase().includes('nan')) return false;
        // 必须是 6 位数字或有效的基金代码格式
        if (!/^\d{6}$/.test(code)) return false;
        return true;
      });
    } catch (e) {
      console.error('[fundStorage] 解析自选列表失败:', e);
      return [];
    }
  }

  addToWatchlist(fundCode: string): void {
    // 验证基金代码有效性
    if (typeof fundCode !== 'string') {
      console.warn('[fundStorage] 无效的基金代码类型:', fundCode);
      return;
    }
    if (fundCode.toLowerCase().includes('nan')) {
      console.warn('[fundStorage] 无效的基金代码（包含 nan）:', fundCode);
      return;
    }
    if (!/^\d{6}$/.test(fundCode)) {
      console.warn('[fundStorage] 无效的基金代码格式（需要 6 位数字）:', fundCode);
      return;
    }
    
    const watchlist = this.getWatchlist();
    if (!watchlist.includes(fundCode)) {
      watchlist.push(fundCode);
      localStorage.setItem(STORAGE_PREFIXES.WATCHLIST, JSON.stringify(watchlist));
      console.log('[fundStorage] 已添加到自选列表:', fundCode);
    }
  }

  removeFromWatchlist(fundCode: string): void {
    const watchlist = this.getWatchlist();
    const index = watchlist.indexOf(fundCode);
    if (index > -1) {
      watchlist.splice(index, 1);
      localStorage.setItem(STORAGE_PREFIXES.WATCHLIST, JSON.stringify(watchlist));
    }
  }

  /**
   * 清理过期数据
   */
  async cleanupExpiredData(): Promise<void> {
    await this.ensureDB();

    const transaction = this.db!.transaction([this.storeName], 'readwrite');
    const store = transaction.objectStore(this.storeName);
    const cursorRequest = store.openCursor();

    const now = Date.now();
    const keysToDelete: string[] = [];

    return new Promise((resolve, reject) => {
      cursorRequest.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest<IDBCursorWithValue>).result;
        
        if (cursor) {
          const record = cursor.value;
          if (record.expiryDays) {
            const expiryTime = record.timestamp + record.expiryDays * 24 * 60 * 60 * 1000;
            if (now > expiryTime) {
              keysToDelete.push(record.key);
            }
          }
          cursor.continue();
        } else {
          // 删除所有过期数据
          const deletePromises = keysToDelete.map(key => this.delete(key));
          Promise.all(deletePromises)
            .then(() => {
              console.log(`清理了 ${keysToDelete.length} 条过期数据`);
              resolve();
            })
            .catch(reject);
        }
      };

      cursorRequest.onerror = () => reject(cursorRequest.error);
    });
  }

  /**
   * 清空所有缓存数据
   */
  async clearAll(): Promise<void> {
    await this.ensureDB();

    const transaction = this.db!.transaction([this.storeName], 'readwrite');
    const store = transaction.objectStore(this.storeName);

    return new Promise((resolve, reject) => {
      const request = store.clear();
      request.onsuccess = () => {
        // 同时清理 localStorage 中的时间戳
        Object.keys(localStorage).forEach(key => {
          if (key.includes('fund:')) {
            localStorage.removeItem(key);
          }
        });
        resolve();
      };
      request.onerror = () => reject(request.error);
    });
  }

  /**
   * 获取存储统计信息
   */
  async getStats(): Promise<{
    totalRecords: number;
    realtimeCount: number;
    historyCount: number;
    baseInfoCount: number;
    periodChangeCount: number;
    assetsCount: number;
  }> {
    await this.ensureDB();

    const transaction = this.db!.transaction([this.storeName], 'readonly');
    const store = transaction.objectStore(this.storeName);
    const cursorRequest = store.openCursor();

    const stats = {
      totalRecords: 0,
      realtimeCount: 0,
      historyCount: 0,
      baseInfoCount: 0,
      periodChangeCount: 0,
      assetsCount: 0,
    };

    return new Promise((resolve, reject) => {
      cursorRequest.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest<IDBCursorWithValue>).result;
        
        if (cursor) {
          stats.totalRecords++;
          const record = cursor.value;
          
          switch (record.type) {
            case 'realtime':
              stats.realtimeCount++;
              break;
            case 'history':
              stats.historyCount++;
              break;
            case 'base':
              stats.baseInfoCount++;
              break;
            case 'period':
              stats.periodChangeCount++;
              break;
            case 'assets':
              stats.assetsCount++;
              break;
          }
          
          cursor.continue();
        } else {
          resolve(stats);
        }
      };

      cursorRequest.onerror = () => reject(cursorRequest.error);
    });
  }
}

// 导出单例
export const fundStorage = new FundStorageService();
export default fundStorage;
