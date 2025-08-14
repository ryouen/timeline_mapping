const fs = require('fs');
const path = require('path');
const { logWork } = require('./work-logger');

class SessionEnder {
  constructor() {
    this.activeDir = path.join(__dirname, '..', 'ACTIVE');
    this.stateFile = path.join(this.activeDir, 'STATE.json');
    this.tasksFile = path.join(this.activeDir, 'TASKS.json');
    this.metaFile = path.join(this.activeDir, '.meta.json');
    this.sessionId = process.env.SESSION_ID || `session-${Date.now()}`;
  }
  
  async end() {
    console.log('📝 Ending Timeline Mapping session...\n');
    
    // 状態を更新
    await this.updateState();
    
    // タスクの進捗を更新
    await this.updateTasks();
    
    // メタデータ更新（最重要）
    await this.updateMeta();
    
    // サマリー表示
    await this.showSummary();
    
    // アーカイブ作成
    await this.createArchive();
    
    console.log('\n✅ Session ended successfully!');
    console.log('💡 Next: node api/docs/handover/system/start-session.js\n');
  }
  
  async updateState() {
    try {
      const state = JSON.parse(fs.readFileSync(this.stateFile, 'utf8'));
      
      state.last_updated = new Date().toISOString();
      state.updated_by = this.sessionId;
      
      // 作業ログから最近の変更を抽出
      const { WorkLogger } = require('./work-logger');
      const logger = new WorkLogger();
      const recentLogs = logger.getLastLogs(50);
      
      // ファイル編集を記録
      const editedFiles = recentLogs
        .filter(log => log.action === 'file_edit' && log.status === 'complete')
        .map(log => log.target);
      
      if (editedFiles.length > 0) {
        state.recent_changes.unshift(`Edited files: ${editedFiles.join(', ')}`);
        state.recent_changes = state.recent_changes.slice(0, 10); // 最新10件のみ
      }
      
      fs.writeFileSync(this.stateFile, JSON.stringify(state, null, 2));
      console.log('  ✓ State updated');
    } catch (error) {
      console.error('  ❌ Could not update state:', error.message);
    }
  }
  
  async updateTasks() {
    try {
      const tasks = JSON.parse(fs.readFileSync(this.tasksFile, 'utf8'));
      
      tasks.last_updated = new Date().toISOString();
      
      // メトリクスを再計算
      tasks.task_metrics = {
        total: tasks.tasks.length,
        pending: tasks.tasks.filter(t => t.status === 'pending').length,
        in_progress: tasks.tasks.filter(t => t.status === 'in_progress').length,
        completed: tasks.tasks.filter(t => t.status === 'completed').length
      };
      
      fs.writeFileSync(this.tasksFile, JSON.stringify(tasks, null, 2));
      console.log('  ✓ Tasks updated');
    } catch (error) {
      console.error('  ❌ Could not update tasks:', error.message);
    }
  }
  
  async updateMeta() {
    try {
      const meta = JSON.parse(fs.readFileSync(this.metaFile, 'utf8'));
      
      // 最重要: 正常終了フラグを設定
      meta.session_ended = true;
      meta.session_end_time = new Date().toISOString();
      meta.last_updated = new Date().toISOString();
      
      fs.writeFileSync(this.metaFile, JSON.stringify(meta, null, 2));
      
      // ログに記録
      logWork('session_end', {
        session_id: this.sessionId,
        status: 'ended',
        project: 'timeline-mapping'
      });
      
      console.log('  ✓ Session marked as ended');
    } catch (error) {
      console.error('  ❌ Could not update meta:', error.message);
    }
  }
  
  async showSummary() {
    const { WorkLogger } = require('./work-logger');
    const logger = new WorkLogger();
    const logs = logger.getLastLogs(100);
    const summary = logger.getProjectSummary();
    
    console.log('\n📊 Session Summary:');
    console.log(`  Total actions: ${logs.length}`);
    console.log(`  Route searches: ${summary.route_searches}`);
    console.log(`  API calls: ${summary.api_calls}`);
    console.log(`  File edits: ${summary.file_edits}`);
    
    const incomplete = logger.getIncompleteTasks();
    if (incomplete.length > 0) {
      console.log(`  ⚠️ Incomplete tasks: ${incomplete.length}`);
      incomplete.forEach(task => {
        console.log(`    - ${task.target}`);
      });
    } else {
      console.log('  ✅ All tasks completed');
    }
    
    // プロジェクト固有のサマリー
    const routeSearches = logs.filter(l => l.action === 'route_search');
    if (routeSearches.length > 0) {
      console.log('\n🗺️ Route Search Summary:');
      const successful = routeSearches.filter(r => r.status === 'success').length;
      const failed = routeSearches.filter(r => r.status === 'error').length;
      console.log(`  Successful: ${successful}`);
      console.log(`  Failed: ${failed}`);
    }
  }
  
  async createArchive() {
    try {
      const archiveDir = path.join(__dirname, '..', 'archive', 'sessions');
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const archivePath = path.join(archiveDir, `${this.sessionId}_${timestamp}`);
      
      // アーカイブディレクトリ作成
      if (!fs.existsSync(archivePath)) {
        fs.mkdirSync(archivePath, { recursive: true });
      }
      
      // ACTIVE内のファイルをコピー
      const files = fs.readdirSync(this.activeDir);
      files.forEach(file => {
        if (file !== 'WORK_LOG.jsonl') { // ログは累積なのでコピーしない
          const src = path.join(this.activeDir, file);
          const dest = path.join(archivePath, file);
          fs.copyFileSync(src, dest);
        }
      });
      
      console.log(`  ✓ Archive created: ${path.basename(archivePath)}`);
    } catch (error) {
      console.error('  ⚠️ Could not create archive:', error.message);
    }
  }
}

if (require.main === module) {
  new SessionEnder().end().catch(console.error);
}

module.exports = SessionEnder;