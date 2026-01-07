// Visual Pipeline module: DAG workflow visualization and management
function ensureStyles(){
  const href = '/static/css/modules/visual_pipeline.module.css?v=__ASSET_VERSION__';
  const existed = Array.from(document.styleSheets||[]).some(ss=> ss.href && ss.href.includes('/static/css/modules/visual_pipeline.module.css'));
  if (existed) return;
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = href;
  document.head.appendChild(link);
}

function $(id) { return document.getElementById(id); }

function html(strings, ...vals) {
  const s = strings.reduce((acc, cur, i) => acc + cur + (i < vals.length ? vals[i] : ''), '');
  const tpl = document.createElement('template');
  tpl.innerHTML = s.trim();
  return tpl.content;
}

async function fetchJSON(url, opts = {}) {
  const token = localStorage.getItem('auth_token');
  if (token) {
    opts.headers = opts.headers || {};
    opts.headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(url, opts);
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = text; }
  if (!res.ok) throw new Error(typeof data === 'string' ? data : JSON.stringify(data));
  return data;
}

function showToastSafe(msg, type = 'info') {
  if (window.showToast) {
    window.showToast({ message: msg, type });
  } else {
    console[type === 'error' ? 'log']('[toast]', msg);
  }
}

let pipelineData = null;
let selectedNode = null;

function renderVisualPipelineDashboard() {
  ensureStyles();
  const root = $('app-root');
  if (!root) return;

  root.innerHTML = '';
  root.appendChild(html`
    <div class="visual-pipeline-dashboard">
      <header class="pipeline-header">
        <h1>可视化管道</h1>
        <div class="pipeline-controls">
          <button id="loadPipelineBtn" class="btn btn-primary">加载管道</button>
          <button id="savePipelineBtn" class="btn btn-secondary">保存管道</button>
          <button id="runPipelineBtn" class="btn btn-success">运行管道</button>
          <button id="clearPipelineBtn" class="btn btn-danger">清空</button>
        </div>
      </header>

      <div class="pipeline-content">
        <div class="pipeline-sidebar">
          <div class="sidebar-section">
            <h3>可用节点</h3>
            <div id="nodePalette" class="node-palette">
              <div class="node-item" data-type="start">开始节点</div>
              <div class="node-item" data-type="task">任务节点</div>
              <div class="node-item" data-type="condition">条件节点</div>
              <div class="node-item" data-type="end">结束节点</div>
            </div>
          </div>

          <div class="sidebar-section">
            <h3>节点属性</h3>
            <div id="nodeProperties" class="node-properties">
              <div class="no-selection">请先选择一个节点</div>
            </div>
          </div>
        </div>

        <div class="pipeline-canvas">
          <div id="pipelineCanvas" class="canvas-area">
            <div class="canvas-placeholder">
              <p>拖拽左侧节点到此处开始构建管道</p>
              <p>或点击"加载管道"加载现有配置</p>
            </div>
          </div>
        </div>
      </div>

      <div class="pipeline-footer">
        <div id="pipelineStatus" class="pipeline-status">
          管道状态: 未加载
        </div>
      </div>
    </div>
  `);

  // Bind events
  const loadPipelineBtn = $('loadPipelineBtn');
  const savePipelineBtn = $('savePipelineBtn');
  const runPipelineBtn = $('runPipelineBtn');
  const clearPipelineBtn = $('clearPipelineBtn');
  const nodePalette = $('nodePalette');

  if (loadPipelineBtn) {
    loadPipelineBtn.addEventListener('click', () => loadPipeline());
  }

  if (savePipelineBtn) {
    savePipelineBtn.addEventListener('click', () => savePipeline());
  }

  if (runPipelineBtn) {
    runPipelineBtn.addEventListener('click', () => runPipeline());
  }

  if (clearPipelineBtn) {
    clearPipelineBtn.addEventListener('click', () => clearPipeline());
  }

  if (nodePalette) {
    nodePalette.addEventListener('click', (e) => {
      if (e.target.classList.contains('node-item')) {
        addNodeToCanvas(e.target.dataset.type);
      }
    });
  }

  // Initialize canvas
  initializeCanvas();
}

function initializeCanvas() {
  const canvas = $('pipelineCanvas');
  if (!canvas) return;

  // Simple drag and drop for nodes
  canvas.addEventListener('dragover', (e) => {
    e.preventDefault();
  });

  canvas.addEventListener('drop', (e) => {
    e.preventDefault();
    const nodeType = e.dataTransfer.getData('text/plain');
    if (nodeType) {
      const rect = canvas.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      addNodeToCanvas(nodeType, x, y);
    }
  });
}

function addNodeToCanvas(nodeType, x = 100, y = 100) {
  const canvas = $('pipelineCanvas');
  if (!canvas) return;

  const nodeId = `node_${Date.now()}`;
  const node = document.createElement('div');
  node.className = `pipeline-node ${nodeType}`;
  node.id = nodeId;
  node.style.left = `${x}px`;
  node.style.top = `${y}px`;
  node.innerHTML = `
    <div class="node-header">
      <span class="node-type">${getNodeTypeLabel(nodeType)}</span>
      <button class="node-delete" onclick="removeNode('${nodeId}')">×</button>
    </div>
    <div class="node-content">
      <div class="node-title">${getNodeTypeLabel(nodeType)}</div>
    </div>
    <div class="node-connectors">
      <div class="connector input" data-direction="input"></div>
      <div class="connector output" data-direction="output"></div>
    </div>
  `;

  node.addEventListener('click', () => selectNode(nodeId));
  node.draggable = true;
  node.addEventListener('dragstart', (e) => {
    e.dataTransfer.setData('text/plain', nodeId);
  });

  canvas.appendChild(node);

  // Store node data
  if (!pipelineData) pipelineData = { nodes: {}, connections: [] };
  pipelineData.nodes[nodeId] = {
    id: nodeId,
    type: nodeType,
    x, y,
    title: getNodeTypeLabel(nodeType),
    properties: {}
  };

  updatePipelineStatus();
}

function getNodeTypeLabel(type) {
  const labels = {
    start: '开始',
    task: '任务',
    condition: '条件',
    end: '结束'
  };
  return labels[type] || type;
}

function selectNode(nodeId) {
  // Remove previous selection
  document.querySelectorAll('.pipeline-node.selected').forEach(node => {
    node.classList.remove('selected');
  });

  const node = $(nodeId);
  if (node) {
    node.classList.add('selected');
    selectedNode = nodeId;
    showNodeProperties(nodeId);
  }
}

function showNodeProperties(nodeId) {
  const propertiesDiv = $('nodeProperties');
  if (!propertiesDiv || !pipelineData?.nodes[nodeId]) return;

  const node = pipelineData.nodes[nodeId];
  propertiesDiv.innerHTML = `
    <div class="property-group">
      <label>节点ID:</label>
      <input type="text" value="${node.id}" readonly>
    </div>
    <div class="property-group">
      <label>节点类型:</label>
      <input type="text" value="${node.type}" readonly>
    </div>
    <div class="property-group">
      <label>标题:</label>
      <input type="text" id="nodeTitle" value="${node.title}" onchange="updateNodeTitle('${nodeId}', this.value)">
    </div>
    <div class="property-group">
      <label>描述:</label>
      <textarea id="nodeDesc" placeholder="节点描述">${node.properties.description || ''}</textarea>
    </div>
    ${node.type === 'task' ? `
      <div class="property-group">
        <label>脚本:</label>
        <select id="nodeScript">
          <option value="">选择脚本...</option>
        </select>
      </div>
    ` : ''}
  `;

  // Load scripts for task nodes
  if (node.type === 'task') {
    loadScriptsForNode();
  }
}

function updateNodeTitle(nodeId, title) {
  if (pipelineData?.nodes[nodeId]) {
    pipelineData.nodes[nodeId].title = title;
    const node = $(nodeId);
    if (node) {
      node.querySelector('.node-title').textContent = title;
    }
  }
}

async function loadScriptsForNode() {
  const scriptSelect = $('nodeScript');
  if (!scriptSelect) return;

  try {
    const scripts = await fetchJSON('/api/scripts');
    scriptSelect.innerHTML = '<option value="">选择脚本...</option>';
    if (scripts.data) {
      scripts.data.forEach(script => {
        const option = document.createElement('option');
        option.value = script.id;
        option.textContent = script.name;
        scriptSelect.appendChild(option);
      });
    }
  } catch (error) {
    console.error('Failed to load scripts:', error);
  }
}

function removeNode(nodeId) {
  const node = $(nodeId);
  if (node) {
    node.remove();
  }
  if (pipelineData?.nodes[nodeId]) {
    delete pipelineData.nodes[nodeId];
  }
  updatePipelineStatus();
}

async function loadPipeline() {
  try {
    const pipelines = await fetchJSON('/api/pipelines');
    if (pipelines.data && pipelines.data.length > 0) {
      // Load first pipeline for now
      pipelineData = pipelines.data[0];
      renderPipelineFromData(pipelineData);
      showToastSafe('管道加载成功', 'success');
    } else {
      showToastSafe('暂无保存的管道', 'info');
    }
  } catch (error) {
    showToastSafe('加载管道失败: ' + error.message, 'error');
  }
}

function renderPipelineFromData(data) {
  const canvas = $('pipelineCanvas');
  if (!canvas || !data.nodes) return;

  canvas.innerHTML = '';
  Object.values(data.nodes).forEach(nodeData => {
    addNodeToCanvas(nodeData.type, nodeData.x, nodeData.y);
    // Update title if different
    if (nodeData.title !== getNodeTypeLabel(nodeData.type)) {
      updateNodeTitle(nodeData.id, nodeData.title);
    }
  });
}

async function savePipeline() {
  if (!pipelineData) {
    showToastSafe('没有管道数据可保存', 'error');
    return;
  }

  try {
    await fetchJSON('/api/pipelines', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pipelineData)
    });
    showToastSafe('管道保存成功', 'success');
  } catch (error) {
    showToastSafe('保存管道失败: ' + error.message, 'error');
  }
}

async function runPipeline() {
  if (!pipelineData) {
    showToastSafe('没有管道可运行', 'error');
    return;
  }

  try {
    const result = await fetchJSON('/api/pipelines/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(pipelineData)
    });
    showToastSafe('管道开始运行', 'success');
  } catch (error) {
    showToastSafe('运行管道失败: ' + error.message, 'error');
  }
}

function clearPipeline() {
  const canvas = $('pipelineCanvas');
  if (canvas) {
    canvas.innerHTML = '<div class="canvas-placeholder"><p>画布已清空，拖拽左侧节点开始构建新管道</p></div>';
  }
  pipelineData = null;
  selectedNode = null;
  updatePipelineStatus();
}

function updatePipelineStatus() {
  const statusDiv = $('pipelineStatus');
  if (!statusDiv) return;

  const nodeCount = pipelineData?.nodes ? Object.keys(pipelineData.nodes).length : 0;
  statusDiv.textContent = `管道状态: ${nodeCount} 个节点`;
}

export async function mount(root, options = {}) {
  console.log('Visual Pipeline module mounting...');
  renderVisualPipelineDashboard();
  return { root, options };
}

export default mount;
