/**
 * Worker 池管理
 * 管理多个 Worker 实例，提高并发处理能力
 */

interface Task {
  id: string
  data: any
  resolve: (result: any) => void
  reject: (error: Error) => void
}

class WorkerPool {
  private workers: Worker[] = []
  private workerBusy: boolean[] = []
  private taskQueue: Task[] = []
  private pendingTasks: Map<string, Task> = new Map()
  private size: number
  private taskIdCounter = 0

  constructor(size?: number) {
    // 根据 CPU 核心数动态调整 Worker 数量
    const cpuCores = typeof navigator !== 'undefined' ? navigator.hardwareConcurrency : 4
    this.size = size || Math.max(2, Math.min(cpuCores - 1, 4)) // 最少 2 个，最多 4 个，保留 1 个核心给主线程
    
    // 创建 Worker 实例
    for (let i = 0; i < this.size; i++) {
      this.createWorker(i)
    }
    
    console.info(`Worker 池初始化完成：${this.size} 个 Worker (CPU 核心数：${cpuCores})`)
  }

  private createWorker(index: number) {
    const worker = new Worker(new URL('./data.worker.ts', import.meta.url))
    worker.onmessage = (e) => this.handleMessage(index, e)
    worker.onerror = (error) => this.handleError(index, error)
    
    if (index < this.workers.length) {
      this.workers[index] = worker
    } else {
      this.workers.push(worker)
      this.workerBusy.push(false)
    }
  }

  // 生成唯一任务ID
  private generateTaskId(): string {
    return `task_${++this.taskIdCounter}_${Date.now()}`
  }

  // 处理 Worker 消息
  private handleMessage(workerIndex: number, event: MessageEvent) {
    const { data, error, id } = event.data
    
    // 标记 Worker 为空闲
    this.workerBusy[workerIndex] = false
    
    // 根据任务ID查找对应的任务
    if (id && this.pendingTasks.has(id)) {
      const task = this.pendingTasks.get(id)!
      this.pendingTasks.delete(id)
      
      if (error) {
        task.reject(new Error(error))
      } else {
        task.resolve(data)
      }
    }
    
    // 处理队列中的下一个任务
    this.processQueue()
  }

  // 处理错误
  private handleError(workerIndex: number, error: ErrorEvent) {
    console.error(`Worker ${workerIndex} 错误:`, error)
    this.workerBusy[workerIndex] = false
    
    // 重启 Worker
    this.createWorker(workerIndex)
    
    this.processQueue()
  }

  // 处理任务队列
  private processQueue() {
    if (this.taskQueue.length === 0) return
    
    const availableWorker = this.workerBusy.findIndex(busy => !busy)
    if (availableWorker === -1) return
    
    const task = this.taskQueue.shift()
    if (!task) return
    
    this.workerBusy[availableWorker] = true
    this.workers[availableWorker].postMessage({ ...task.data, id: task.id })
  }

  // 提交任务
  public postMessage(data: any): Promise<any> {
    return new Promise((resolve, reject) => {
      const taskId = this.generateTaskId()
      const task: Task = { id: taskId, data, resolve, reject }
      
      // 查找空闲 Worker
      const availableWorker = this.workerBusy.findIndex(busy => !busy)
      
      if (availableWorker !== -1) {
        // 有空闲 Worker，立即执行
        this.workerBusy[availableWorker] = true
        this.pendingTasks.set(taskId, task)
        this.workers[availableWorker].postMessage({ ...data, id: taskId })
      } else {
        // 无空闲 Worker，加入队列
        this.taskQueue.push(task)
      }
    })
  }

  // 终止所有 Worker
  public terminate() {
    this.workers.forEach(worker => worker.terminate())
    this.workers = []
    this.workerBusy = []
    this.taskQueue = []
    this.pendingTasks.clear()
  }
}

// 创建全局 Worker 池实例
export const workerPool = new WorkerPool(2)
