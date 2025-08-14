const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('\n🔍 Quick Diagnosis - Timeline Mapping Project\n');
console.log('=' .repeat(50));

// 1. セッション状態
const metaFile = path.join(__dirname, '..', 'ACTIVE', '.meta.json');
if (fs.existsSync(metaFile)) {
  const meta = JSON.parse(fs.readFileSync(metaFile, 'utf8'));
  console.log('\n📊 Session Status:');
  console.log(`  ID: ${meta.session_id}`);
  console.log(`  Started: ${meta.session_started || 'Unknown'}`);
  console.log(`  Ended: ${meta.session_ended ? 'Yes' : 'No (Active or CRASHED!)'}`);
  console.log(`  Last update: ${meta.last_updated}`);
}

// 2. プロジェクト状態
const stateFile = path.join(__dirname, '..', 'ACTIVE', 'STATE.json');
if (fs.existsSync(stateFile)) {
  const state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
  console.log('\n📈 Project Progress:');
  console.log(`  Progress: ${state.metrics.progress_percentage}%`);
  console.log(`  Routes tested: ${state.metrics.routes_tested}`);
  console.log(`  API success rate: ${state.metrics.api_success_rate}%`);
  console.log(`  Known issues: ${state.metrics.known_issues}`);
}

// 3. タスク状態
const tasksFile = path.join(__dirname, '..', 'ACTIVE', 'TASKS.json');
if (fs.existsSync(tasksFile)) {
  const tasks = JSON.parse(fs.readFileSync(tasksFile, 'utf8'));
  console.log('\n📋 Task Status:');
  console.log(`  Total: ${tasks.task_metrics.total}`);
  console.log(`  Completed: ${tasks.task_metrics.completed}`);
  console.log(`  In Progress: ${tasks.task_metrics.in_progress}`);
  console.log(`  Pending: ${tasks.task_metrics.pending}`);
}

// 4. Dockerコンテナ状態
console.log('\n🐳 Docker Container Status:');
try {
  const dockerStatus = execSync('docker ps | grep -E "(scraper|apache)" || echo "No relevant containers"', 
                                { encoding: 'utf8' });
  if (dockerStatus.includes('scraper')) {
    console.log('  ✅ Scraper container is running');
  } else {
    console.log('  ⚠️ Scraper container not found');
  }
  if (dockerStatus.includes('apache')) {
    console.log('  ✅ Apache container is running');
  } else {
    console.log('  ⚠️ Apache container not found');
  }
} catch {
  console.log('  ❌ Could not check Docker status');
}

// 5. APIサーバー状態
console.log('\n🌐 API Server Status:');
try {
  execSync('curl -s http://localhost:8000/health >/dev/null 2>&1', { timeout: 3000 });
  console.log('  ✅ API server (port 8000) is responding');
} catch {
  console.log('  ⚠️ API server (port 8000) not responding');
}

// 6. 重要ファイルの存在確認
console.log('\n📁 Key Files:');
const keyFiles = [
  '/var/www/japandatascience.com/timeline-mapping/api/google_maps_integration.php',
  '/var/www/japandatascience.com/timeline-mapping/json-generator.html',
  '/var/www/japandatascience.com/timeline-mapping/api/google_maps_unified.py'
];

keyFiles.forEach(file => {
  if (fs.existsSync(file)) {
    const stats = fs.statSync(file);
    const hours = (Date.now() - stats.mtime) / 3600000;
    console.log(`  ✅ ${path.basename(file)} (modified ${hours.toFixed(1)}h ago)`);
  } else {
    console.log(`  ❌ ${path.basename(file)} (missing)`);
  }
});

// 7. Git状態
console.log('\n📝 Git Status:');
try {
  const changes = execSync('cd /var/www/japandatascience.com/timeline-mapping && git status --short 2>/dev/null || echo "Not a git repo"', 
                          { encoding: 'utf8' });
  if (changes.includes('Not a git repo')) {
    console.log('  ⚠️ Not a git repository');
  } else if (changes.trim()) {
    const fileCount = changes.split('\n').filter(Boolean).length;
    console.log(`  ${fileCount} files with changes`);
  } else {
    console.log('  ✅ No uncommitted changes');
  }
} catch {
  console.log('  ⚠️ Git not available');
}

// 8. 未完了タスク
console.log('\n⚠️ Incomplete Work:');
const { WorkLogger } = require('./work-logger');
const logger = new WorkLogger();
const incomplete = logger.getIncompleteTasks();
if (incomplete.length === 0) {
  console.log('  ✅ No incomplete file edits');
} else {
  incomplete.forEach(t => console.log(`  - ${t.target} (started ${t.timestamp})`));
}

// 9. 最近のエラー
const recentLogs = logger.getLastLogs(50);
const errors = recentLogs.filter(l => l.status === 'error' || l.error);
if (errors.length > 0) {
  console.log('\n❌ Recent Errors:');
  errors.slice(0, 3).forEach(err => {
    console.log(`  - ${err.timestamp}: ${err.error || err.message || 'Unknown error'}`);
  });
}

// 10. 推奨アクション
console.log('\n💡 Recommended Actions:');
if (!meta || !meta.session_ended) {
  console.log('  1. If starting new work: node api/docs/handover/system/start-session.js');
  console.log('  2. If ending work: node api/docs/handover/system/end-session.js');
}
if (incomplete.length > 0) {
  console.log('  3. Review and complete unfinished file edits');
}
if (errors.length > 0) {
  console.log('  4. Investigate recent errors');
}

console.log('\n' + '=' .repeat(50));
console.log('✅ Diagnosis complete\n');