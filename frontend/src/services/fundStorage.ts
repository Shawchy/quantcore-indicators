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
class FundStorageService {
  private db: IDBDatabase | null = null;
  private dbName = 'FundDataDB';
  private dbVersion = 1;
  private storeName = 'fundData';

  constructor() {
    this.initIndexedDB();
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
  async setRealtimeRate(fundCodes: string[], data: any[]): Promise<void> {
    const timestamp = Date.now();
    
    // 存储每个基金的数据
    const promises = fundCodes.map((code, index) => {
      const key = `${STORAGE_PREFIXES.REALTIME_RATE}${code}`;
      const tsKey = `${STORAGE_PREFIXES.RATE_TIMESTAMP}${code}`;
      
      return Promise.all([
        this.set(key, data[index], 'realtime', code, CACHE_EXPIRY.REALTIME_RATE / (24 * 60 * 60 * 1000)),
        localStorage.setItem(tsKey, timestamp.toString()),
      ]);
    });

    await Promise.all(promises);
  }

  /**
   * 获取实时估算数据
   */
  async getRealtimeRate(fundCode: string): Promise<any | null> {
    const key = `${STORAGE_PREFIXES.REALTIME_RATE}${fundCode}`;
    const tsKey = `${STORAGE_PREFIXES.RATE_TIMESTAMP}${fundCode}`;
    
    const timestamp = localStorage.getItem(tsKey);
    if (!timestamp) {
      return null;
    }

    const cacheAge = Date.now() - parseInt(timestamp);
    if (cacheAge > CACHE_EXPIRY.REALTIME_RATE) {
      // 缓存过期
      localStorage.removeItem(tsKey);
      await this.delete(key);
      return null;
    }

    return await this.get(key);
  }

  /**
   * 批量存储历史净值数据
   */
  async setHistory(fundCode: string, data: any[]): Promise<void> {
    const key = `${STORAGE_PREFIXES.HISTORY}${fundCode}`;
    const tsKey = `${STORAGE_PREFIXES.HISTORY_TIMESTAMP}${fundCode}`;
    
    await Promise.all([
      this.set(key, data, 'history', fundCode, CACHE_EXPIRY.HISTORY / (24 * 60 * 60 * 1000)),
      localStorage.setItem(tsKey, Date.now().toString()),
    ]);
  }

  /**
   * 获取历史净值数据
   */
  async getHistory(fundCode: string): Promise<any[] | null> {
    const key = `${STORAGE_PREFIXES.HISTORY}${fundCode}`;
    const tsKey = `${STORAGE_PREFIXES.HISTORY_TIMESTAMP}${fundCode}`;
    
    const timestamp = localStorage.getItem(tsKey);
    if (!timestamp) {
      return null;
    }

    const cacheAge = Date.now() - parseInt(timestamp);
    if (cacheAge > CACHE_EXPIRY.HISTORY) {
      // 缓存过期
      localStorage.removeItem(tsKey);
      await this.delete(key);
      return null;
    }

    return await this.get(key);
  }

  /**
   * 存储基金基本信息
   */
  async setBaseInfo(fundCode: string, data: any): Promise<void> {
    const key = `${STORAGE_PREFIXES.BASE_INFO}${fundCode}`;
    const tsKey = `${STORAGE_PREFIXES.BASE_INFO_TIMESTAMP}${fundCode}`;
    
    await Promise.all([
      this.set(key, data, 'base', fundCode, CACHE_EXPIRY.BASE_INFO / (24 * 60 * 60 * 1000)),
      localStorage.setItem(tsKey, Date.now().toString()),
    ]);
  }

  /**
   * 获取基金基本信息
   */
  async getBaseInfo(fundCode: string): Promise<any | null> {
    const key = `${STORAGE_PREFIXES.BASE_INFO}${fundCode}`;
    const tsKey = `${STORAGE_PREFIXES.BASE_INFO_TIMESTAMP}${fundCode}`;
    
    const timestamp = localStorage.getItem(tsKey);
    if (!timestamp) {
      return null;
    }

    const cacheAge = Date.now() - parseInt(timestamp);
    if (cacheAge > CACHE_EXPIRY.BASE_INFO) {
      localStorage.removeItem(tsKey);
      await this.delete(key);
      return null;
    }

    return await this.get(key);
  }

  /**
   * 批量存储基金基本信息
   */
  async setBaseInfoBatch(fundCodes: string[], dataList: any[]): Promise<void> {
    const promises = fundCodes.map((code, index) => 
      this.setBaseInfo(code, dataList[index])
    );
    await Promise.all(promises);
  }

  /**
   * 存储阶段涨跌幅数据
   */
  async setPeriodChange(fundCode: string, data: any[]): Promise<void> {
    const key = `${STORAGE_PREFIXES.PERIOD_CHANGE}${fundCode}`;
    const tsKey = `${STORAGE_PREFIXES.PERIOD_CHANGE_TIMESTAMP}${fundCode}`;
    
    await Promise.all([
      this.set(key, data, 'period', fundCode, CACHE_EXPIRY.PERIOD_CHANGE / (24 * 60 * 60 * 1000)),
      localStorage.setItem(tsKey, Date.now().toString()),
    ]);
  }

  /**
   * 获取阶段涨跌幅数据
   */
  async getPeriodChange(fundCode: string): Promise<any[] | null> {
    const key = `${STORAGE_PREFIXES.PERIOD_CHANGE}${fundCode}`;
    const tsKey = `${STORAGE_PREFIXES.PERIOD_CHANGE_TIMESTAMP}${fundCode}`;
    
    const timestamp = localStorage.getItem(tsKey);
    if (!timestamp) {
      return null;
    }

    const cacheAge = Date.now() - parseInt(timestamp);
    if (cacheAge > CACHE_EXPIRY.PERIOD_CHANGE) {
      localStorage.removeItem(tsKey);
      await this.delete(key);
      return null;
    }

    return await this.get(key);
  }

  /**
   * 存储资产配置数据
   */
  async setAssets(fundCode: string, data: any[]): Promise<void> {
    const key = `${STORAGE_PREFIXES.ASSETS}${fundCode}`;
    const tsKey = `${STORAGE_PREFIXES.ASSETS_TIMESTAMP}${fundCode}`;
    
    await Promise.all([
      this.set(key, data, 'assets', fundCode, CACHE_EXPIRY.ASSETS / (24 * 60 * 60 * 1000)),
      localStorage.setItem(tsKey, Date.now().toString()),
    ]);
  }

  /**
   * 获取资产配置数据
   */
  async getAssets(fundCode: string): Promise<any[] | null> {
    const key = `${STORAGE_PREFIXES.ASSETS}${fundCode}`;
    const tsKey = `${STORAGE_PREFIXES.ASSETS_TIMESTAMP}${fundCode}`;
    
    const timestamp = localStorage.getItem(tsKey);
    if (!timestamp) {
      return null;
    }

    const cacheAge = Date.now() - parseInt(timestamp);
    if (cacheAge > CACHE_EXPIRY.ASSETS) {
      localStorage.removeItem(tsKey);
      await this.delete(key);
      return null;
    }

    return await this.get(key);
  }

  /**
   * 管理自选基金列表
   */
  getWatchlist(): string[] {
    const stored = localStorage.getItem(STORAGE_PREFIXES.WATCHLIST);
    return stored ? JSON.parse(stored) : [];
  }

  addToWatchlist(fundCode: string): void {
    const watchlist = this.getWatchlist();
    if (!watchlist.includes(fundCode)) {
      watchlist.push(fundCode);
      localStorage.setItem(STORAGE_PREFIXES.WATCHLIST, JSON.stringify(watchlist));
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
