const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const { logWork } = require('./work-logger');

class SessionManager {
  constructor() {
    this.activeDir = path.join(__dirname, '..', 'ACTIVE');
    this.stateFile = path.join(this.activeDir, 'STATE.json');
    this.tasksFile = path.join(this.activeDir, 'TASKS.json');
    this.metaFile = path.join(this.activeDir, '.meta.json');
    this.sessionId = `session-${Date.now()}`;
    process.env.SESSION_ID = this.sessionId;
  }
  
  async start() {
    console.log('🚀 Starting new session for Timeline Mapping project...\n');
    console.log('=' .repeat(60));
    
    // 最重要: クラッシュ検出
    const crashed = await this.detectCrash();
    if (crashed) {
      await this.handleCrashRecovery();
    }
    
    // 通常の状態表示
    await this.displayState();
    
    // Google Maps統合の状態確認
    await this.checkGoogleMapsIntegration();
    
    // セッション開始を記録
    this.recordSessionStart();
    
    console.log('\n' + '=' .repeat(60));
    console.log('✅ Session ready! Good luck!\n');
    console.log('📝 Remember to run: node api/docs/handover/system/end-session.js when done\n');
  }
  
  async detectCrash() {
    try {
      const meta = JSON.parse(fs.readFileSync(this.metaFile, 'utf8'));
      
      // session_ended フラグをチェック（これが鍵）
      if (!meta.session_ended && meta.session_id) {
        const hours = (Date.now() - new Date(meta.last_updated)) / 3600000;
        
        if (hours < 24) {
          console.log('\n⚠️  PREVIOUS SESSION CRASHED!');
          console.log('=' .repeat(60));
          console.log(`  Last session: ${meta.session_id}`);
          console.log(`  Time since: ${hours.toFixed(1)} hours ago`);
          console.log('=' .repeat(60) + '\n');
          return true;
        }
      }
      
      // フラグをリセット（新セッション開始）
      meta.session_ended = false;
      meta.session_id = this.sessionId;
      fs.writeFileSync(this.metaFile, JSON.stringify(meta, null, 2));
      
    } catch (error) {
      // 初回実行時
      this.initializeMeta();
    }
    
    return false;
  }
  
  async handleCrashRecovery() {
    console.log('🔧 CRASH RECOVERY for Timeline Mapping\n');
    
    // 1. プロジェクト固有の状態確認
    console.log('📝 Project-specific checks:');
    
    // APIサーバー状態確認
    try {
      execSync('curl -s http://localhost:8000/health || echo "API server not running"', 
               { encoding: 'utf8', stdio: 'pipe' });
      console.log('  ✅ API server check completed');
    } catch {
      console.log('  ⚠️ API server may not be running');
    }
    
    // json-generator.html の実行状態
    console.log('  📄 Check json-generator.html for any ongoing route searches');
    
    // 2. Git状態確認
    try {
      const gitStatus = execSync('git status --short 2>/dev/null', { encoding: 'utf8' });
      if (gitStatus) {
        console.log('\n📝 Uncommitted changes:');
        const files = gitStatus.split('\n').filter(Boolean).slice(0, 5);
        files.forEach(file => console.log(`  ${file}`));
        if (gitStatus.split('\n').length > 5) {
          console.log(`  ... and ${gitStatus.split('\n').length - 5} more`);
        }
        console.log('');
      }
    } catch {
      // Git not available
    }
    
    // 3. 未完了タスク表示
    const { WorkLogger } = require('./work-logger');
    const logger = new WorkLogger();
    const incomplete = logger.getIncompleteTasks();
    
    if (incomplete.length > 0) {
      console.log('⚠️ Incomplete tasks:');
      incomplete.forEach(task => {
        console.log(`  - ${task.target}`);
      });
      console.log('');
    }
    
    console.log('📄 Recovery options:');
    console.log('  1. Check API server: docker ps | grep scraper');
    console.log('  2. Review recent logs: node api/docs/handover/system/work-logger.js show 20');
    console.log('  3. Check json-generator.html for progress');
    console.log('  4. Continue working (recommended)\n');
  }
  
  async displayState() {
    try {
      const state = JSON.parse(fs.readFileSync(this.stateFile, 'utf8'));
      
      console.log('📊 Project Status:');
      Object.entries(state.project_status || {}).forEach(([key, value]) => {
        const icon = value === 'completed' ? '✅' : 
                     value === 'in_progress' ? '🔄' : '⭕';
        console.log(`  ${icon} ${key}: ${value}`);
      });
      
      console.log('\n📈 Metrics:');
      Object.entries(state.metrics || {}).forEach(([key, value]) => {
        console.log(`  ${key}: ${value}`);
      });
      
      if (state.critical_issues && state.critical_issues.length > 0) {
        console.log('\n⚠️ Critical Issues:');
        state.critical_issues.forEach(issue => {
          console.log(`  [${issue.id}] ${issue.description} (${issue.severity})`);
        });
      }
      
      if (state.next_actions && state.next_actions.length > 0) {
        console.log('\n📝 Next Actions:');
        state.next_actions.forEach((action, i) => {
          console.log(`  ${i + 1}. ${action}`);
        });
      }
    } catch (error) {
      console.log('⚠️ Could not read STATE.json');
    }
  }
  
  async checkGoogleMapsIntegration() {
    console.log('\n🗺️ Google Maps Integration Status:');
    
    // Check key files
    const keyFiles = [
      'api/google_maps_integration.php',
      'api/google_maps_json_converter.py',
      'api/google_maps_unified.py'
    ];
    
    keyFiles.forEach(file => {
      const fullPath = path.join('/var/www/japandatascience.com/timeline-mapping', file);
      if (fs.existsSync(fullPath)) {
        console.log(`  ✅ ${file}`);
      } else {
        console.log(`  ❌ ${file} (missing)`);
      }
    });
  }
  
  recordSessionStart() {
    // 作業ログに記録
    logWork('session_start', {
      session_id: this.sessionId,
      status: 'started',
      project: 'timeline-mapping'
    });
    
    // メタファイル更新
    try {
      const meta = JSON.parse(fs.readFileSync(this.metaFile, 'utf8'));
      meta.session_id = this.sessionId;
      meta.session_started = new Date().toISOString();
      meta.session_ended = false; // 重要
      fs.writeFileSync(this.metaFile, JSON.stringify(meta, null, 2));
    } catch {
      this.initializeMeta();
    }
  }
  
  initializeMeta() {
    const meta = {
      last_updated: new Date().toISOString(),
      updated_by: 'system',
      session_id: this.sessionId,
      session_ended: false,
      session_started: new Date().toISOString(),
      document_version: '1.0.0',
      validation: {
        last_checked: new Date().toISOString(),
        is_valid: true,
        warnings: []
      }
    };
    fs.writeFileSync(this.metaFile, JSON.stringify(meta, null, 2));
  }
}

if (require.main === module) {
  new SessionManager().start().catch(console.error);
}

module.exports = SessionManager;