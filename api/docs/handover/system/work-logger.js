const fs = require('fs');
const path = require('path');

class WorkLogger {
  constructor() {
    this.logFile = path.join(__dirname, '..', 'ACTIVE', 'WORK_LOG.jsonl');
    this.sessionId = process.env.SESSION_ID || `session-${Date.now()}`;
    this.ensureLogFile();
  }
  
  ensureLogFile() {
    const dir = path.dirname(this.logFile);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    if (!fs.existsSync(this.logFile)) {
      fs.writeFileSync(this.logFile, '');
    }
  }
  
  log(action, details = {}) {
    const entry = {
      timestamp: new Date().toISOString(),
      session_id: this.sessionId,
      action: action,
      ...details
    };
    
    // 即座に書き込み（クラッシュしても残る）
    fs.appendFileSync(this.logFile, JSON.stringify(entry) + '\n');
    return true;
  }
  
  // ファイル編集の記録
  logFileEdit(file, status = 'in_progress', details = {}) {
    return this.log('file_edit', {
      target: file,
      status,
      ...details
    });
  }
  
  // API呼び出しの記録
  logAPICall(endpoint, status = 'called', details = {}) {
    return this.log('api_call', {
      endpoint,
      status,
      ...details
    });
  }
  
  // ルート検索の記録
  logRouteSearch(origin, destination, status = 'searching', details = {}) {
    return this.log('route_search', {
      origin,
      destination,
      status,
      ...details
    });
  }
  
  // 未完了タスクの検出
  getIncompleteTasks() {
    if (!fs.existsSync(this.logFile)) return [];
    
    const logs = fs.readFileSync(this.logFile, 'utf8')
      .split('\n')
      .filter(Boolean)
      .map(line => {
        try { return JSON.parse(line); } 
        catch { return null; }
      })
      .filter(Boolean);
    
    const incomplete = {};
    logs.forEach(log => {
      if (log.action === 'file_edit' && log.target) {
        if (log.status === 'in_progress') {
          incomplete[log.target] = log;
        } else if (log.status === 'complete') {
          delete incomplete[log.target];
        }
      }
    });
    
    return Object.values(incomplete);
  }
  
  // 最後のログを表示
  getLastLogs(n = 10) {
    if (!fs.existsSync(this.logFile)) return [];
    
    const logs = fs.readFileSync(this.logFile, 'utf8')
      .split('\n')
      .filter(Boolean)
      .slice(-n)
      .map(line => {
        try { return JSON.parse(line); }
        catch { return null; }
      })
      .filter(Boolean);
    
    return logs;
  }
  
  // プロジェクト固有のサマリー
  getProjectSummary() {
    if (!fs.existsSync(this.logFile)) return {};
    
    const logs = fs.readFileSync(this.logFile, 'utf8')
      .split('\n')
      .filter(Boolean)
      .map(line => {
        try { return JSON.parse(line); }
        catch { return null; }
      })
      .filter(Boolean);
    
    const summary = {
      total_logs: logs.length,
      route_searches: logs.filter(l => l.action === 'route_search').length,
      api_calls: logs.filter(l => l.action === 'api_call').length,
      file_edits: logs.filter(l => l.action === 'file_edit').length,
      sessions: [...new Set(logs.map(l => l.session_id))].length
    };
    
    return summary;
  }
}

// グローバル関数（どこからでも使える）
const logger = new WorkLogger();
function logWork(action, details) {
  return logger.log(action, details);
}

// CLIとして実行された場合
if (require.main === module) {
  const command = process.argv[2];
  
  if (command === 'show') {
    const n = parseInt(process.argv[3]) || 10;
    const logs = logger.getLastLogs(n);
    console.log(`📋 Last ${n} work logs:\n`);
    logs.forEach(log => {
      const target = log.target || log.endpoint || 
                    (log.origin && log.destination ? `${log.origin} → ${log.destination}` : '');
      console.log(`  ${log.timestamp} [${log.action}] ${target}`);
    });
  } else if (command === 'incomplete') {
    const tasks = logger.getIncompleteTasks();
    if (tasks.length === 0) {
      console.log('✅ No incomplete tasks');
    } else {
      console.log('⚠️ Incomplete tasks:');
      tasks.forEach(t => console.log(`  - ${t.target}`));
    }
  } else if (command === 'summary') {
    const summary = logger.getProjectSummary();
    console.log('📊 Project Summary:');
    console.log(`  Total logs: ${summary.total_logs}`);
    console.log(`  Route searches: ${summary.route_searches}`);
    console.log(`  API calls: ${summary.api_calls}`);
    console.log(`  File edits: ${summary.file_edits}`);
    console.log(`  Sessions: ${summary.sessions}`);
  } else {
    console.log('Usage: node work-logger.js [show|incomplete|summary] [n]');
  }
}

module.exports = { WorkLogger, logWork, logger };