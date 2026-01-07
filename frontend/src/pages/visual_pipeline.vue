<template>
  <div>
    <h2>DAG 可视化流水线</h2>
    <div class="pipeline-controls">
      <button @click="createNewPipeline" class="btn-primary">新建流水线</button>
      <button @click="loadPipeline" class="btn-secondary">加载流水线</button>
      <button @click="savePipeline" class="btn-secondary">保存流水线</button>
      <button @click="runPipeline" class="btn-success">运行流水线</button>
    </div>
    <div class="pipeline-canvas" ref="canvas">
      <div class="node-palette">
        <h3>节点类型</h3>
        <div class="node-type" v-for="nodeType in nodeTypes" :key="nodeType.id" @click="addNode(nodeType)">
          <div class="node-icon" :class="nodeType.icon"></div>
          <span>{{ nodeType.name }}</span>
        </div>
      </div>
      <div class="canvas-area" @drop="onDrop" @dragover.prevent>
        <div class="pipeline-node"
             v-for="node in nodes"
             :key="node.id"
             :style="{ left: node.x + 'px', top: node.y + 'px' }"
             @mousedown="startDrag($event, node)"
             draggable="true">
          <div class="node-header" :class="node.type">
            <span>{{ node.name }}</span>
            <button @click="removeNode(node.id)" class="remove-btn">×</button>
          </div>
          <div class="node-content">
            <p>{{ node.description }}</p>
            <div class="node-params">
              <div v-for="param in node.params" :key="param.name" class="param-item">
                <label>{{ param.name }}:</label>
                <input v-model="param.value" :type="param.type" :placeholder="param.placeholder">
              </div>
            </div>
          </div>
          <div class="node-ports">
            <div class="input-port" v-for="input in node.inputs" :key="input.id" @mousedown="startConnection($event, node, input, 'input')"></div>
            <div class="output-port" v-for="output in node.outputs" :key="output.id" @mousedown="startConnection($event, node, output, 'output')"></div>
          </div>
        </div>
        <svg class="connections" v-if="connections.length > 0">
          <path v-for="conn in connections" :key="conn.id" :d="getConnectionPath(conn)" class="connection-line"></path>
        </svg>
      </div>
    </div>
    <div class="pipeline-info">
      <h3>流水线信息</h3>
      <p>节点数量: {{ nodes.length }}</p>
      <p>连接数量: {{ connections.length }}</p>
      <p>状态: {{ pipelineStatus }}</p>
    </div>
  </div>
    <WorkflowDeployPlaceholder />
    <AdvancedFeaturePlaceholder />
</template>
<script>
export default {
  name: 'VisualPipelinePage',
  components: {
    WorkflowDeployPlaceholder,
    AdvancedFeaturePlaceholder
  },
  data() {
    return {
      nodes: [],
      connections: [],
      nodeTypes: [
        { id: 'data_source', name: '数据源', icon: 'data-icon', inputs: [], outputs: [{ id: 'out1', name: '输出' }] },
        { id: 'processor', name: '处理器', icon: 'process-icon', inputs: [{ id: 'in1', name: '输入' }], outputs: [{ id: 'out1', name: '输出' }] },
        { id: 'ai_model', name: 'AI模型', icon: 'ai-icon', inputs: [{ id: 'in1', name: '输入' }], outputs: [{ id: 'out1', name: '输出' }] },
        { id: 'output', name: '输出', icon: 'output-icon', inputs: [{ id: 'in1', name: '输入' }], outputs: [] }
      ],
      dragging: false,
      dragNode: null,
      connecting: false,
      connectionStart: null,
      pipelineStatus: '未运行'
    }
  },
  async mounted() {
    await this.loadSamplePipeline();
    // 注册表联动校验，自动生成节点类型并高亮未实现节点
    try {
      const regResp = await fetch('/api/docs');
      const regText = await regResp.text();
      const regMatch = regText.match(/```json\s*([\s\S]*?)\s*```/);
      let regList = [];
      if (regMatch) {
        regList = JSON.parse(regMatch[1]);
      }
      // 自动生成节点类型
      this.nodeTypes = regList.map(f => {
        let icon = 'data-icon';
        if (f.tags && f.tags.includes('AI')) icon = 'ai-icon';
        if (f.tags && f.tags.includes('DAG')) icon = 'dag-icon';
        if (f.status !== 'available') icon += ' node-unavailable';
        return {
          id: f.id,
          name: f.name,
          icon,
          inputs: [],
          outputs: [{ id: 'out1', name: '输出' }]
        };
      });
    } catch (err) {
      // 忽略注册表校验错误
    }
  },
  methods: {
    createNewPipeline() {
      this.nodes = [];
      this.connections = [];
      this.pipelineStatus = '新建';
    },
    loadPipeline() {
      // 从后端加载流水线配置
      this.loadSamplePipeline();
    },
    savePipeline() {
      // 保存到后端
      console.log('保存流水线:', { nodes: this.nodes, connections: this.connections });
      alert('流水线已保存');
    },
    runPipeline() {
      this.pipelineStatus = '运行中';
      // 模拟运行
      setTimeout(() => {
        this.pipelineStatus = '完成';
      }, 2000);
    },
    loadSamplePipeline() {
      this.nodes = [
        { id: 1, type: 'data_source', name: '数据源1', x: 100, y: 100, description: '加载输入数据', params: [], inputs: [], outputs: [{ id: 'out1', name: '输出' }] },
        { id: 2, type: 'processor', name: '预处理', x: 300, y: 100, description: '数据预处理', params: [{ name: 'method', type: 'text', value: 'clean', placeholder: '处理方法' }], inputs: [{ id: 'in1', name: '输入' }], outputs: [{ id: 'out1', name: '输出' }] },
        { id: 3, type: 'ai_model', name: 'AI分析', x: 500, y: 100, description: 'AI模型分析', params: [{ name: 'model', type: 'text', value: 'gpt-4', placeholder: '模型名称' }], inputs: [{ id: 'in1', name: '输入' }], outputs: [{ id: 'out1', name: '输出' }] },
        { id: 4, type: 'output', name: '结果输出', x: 700, y: 100, description: '输出结果', params: [], inputs: [{ id: 'in1', name: '输入' }], outputs: [] }
      ];
      this.connections = [
        { id: 1, from: { nodeId: 1, portId: 'out1' }, to: { nodeId: 2, portId: 'in1' } },
        { id: 2, from: { nodeId: 2, portId: 'out1' }, to: { nodeId: 3, portId: 'in1' } },
        { id: 3, from: { nodeId: 3, portId: 'out1' }, to: { nodeId: 4, portId: 'in1' } }
      ];
    },
    addNode(nodeType) {
      const node = {
        id: Date.now(),
        type: nodeType.id,
        name: nodeType.name,
        x: 200,
        y: 200,
        description: `新建${nodeType.name}节点`,
        params: nodeType.inputs.map(() => ({ name: 'param', type: 'text', value: '', placeholder: '参数值' })),
        inputs: nodeType.inputs,
        outputs: nodeType.outputs
      };
      this.nodes.push(node);
    },
    removeNode(nodeId) {
      this.nodes = this.nodes.filter(n => n.id !== nodeId);
      this.connections = this.connections.filter(c => c.from.nodeId !== nodeId && c.to.nodeId !== nodeId);
    },
    startDrag(event, node) {
      this.dragging = true;
      this.dragNode = node;
      event.preventDefault();
    },
    onDrop(event) {
      if (this.dragging && this.dragNode) {
        const rect = this.$refs.canvas.getBoundingClientRect();
        this.dragNode.x = event.clientX - rect.left - 100;
        this.dragNode.y = event.clientY - rect.top - 50;
        this.dragging = false;
        this.dragNode = null;
      }
    },
    startConnection(event, node, port, type) {
      this.connecting = true;
      this.connectionStart = { nodeId: node.id, portId: port.id, type };
      event.stopPropagation();
    },
    getConnectionPath(conn) {
      const fromNode = this.nodes.find(n => n.id === conn.from.nodeId);
      const toNode = this.nodes.find(n => n.id === conn.to.nodeId);
      if (!fromNode || !toNode) return '';
      const x1 = fromNode.x + 150;
      const y1 = fromNode.y + 50;
      const x2 = toNode.x;
      const y2 = toNode.y + 50;
      return `M ${x1} ${y1} C ${x1 + 50} ${y1}, ${x2 - 50} ${y2}, ${x2} ${y2}`;
    }
  }
}
</script>
<style scoped>
.pipeline-controls {
  margin-bottom: 20px;
}
.btn-primary, .btn-secondary, .btn-success {
  padding: 8px 16px;
  margin-right: 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.btn-primary {
  background-color: #2196F3;
  color: white;
}
.btn-secondary {
  background-color: #757575;
  color: white;
}
.btn-success {
  background-color: #4CAF50;
  color: white;
}
.pipeline-canvas {
  display: flex;
  height: 600px;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}
.node-palette {
  width: 200px;
  background-color: #f5f5f5;
  padding: 15px;
  border-right: 1px solid #ddd;
}
.node-type {
  display: flex;
  align-items: center;
  padding: 10px;
  margin-bottom: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  background-color: white;
}
.node-type:hover {
  background-color: #e3f2fd;
}
.node-icon {
  width: 20px;
  height: 20px;
  margin-right: 10px;
  background-color: #2196F3;
  border-radius: 50%;
}
.canvas-area {
  flex: 1;
  position: relative;
  background-color: #fafafa;
}
.pipeline-node {
  position: absolute;
  width: 150px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: white;
  cursor: move;
}
.node-header {
  padding: 8px 12px;
  background-color: #2196F3;
  color: white;
  border-radius: 8px 8px 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.node-header.processor {
  background-color: #ff9800;
}
.node-header.ai_model {
  background-color: #9c27b0;
}
.node-header.output {
  background-color: #4CAF50;
}
.remove-btn {
  background: none;
  border: none;
  color: white;
  font-size: 18px;
  cursor: pointer;
}
.node-content {
  padding: 10px;
}
.node-params {
  margin-top: 10px;
}
.param-item {
  margin-bottom: 5px;
}
.param-item label {
  display: block;
  font-size: 12px;
  margin-bottom: 2px;
}
.param-item input {
  width: 100%;
  padding: 2px 4px;
  border: 1px solid #ddd;
  border-radius: 3px;
}
.node-ports {
  display: flex;
  justify-content: space-between;
  padding: 5px;
}
.input-port, .output-port {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: #666;
  cursor: pointer;
}
.input-port {
  align-self: flex-start;
}
.output-port {
  align-self: flex-end;
}
.connections {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.connection-line {
  stroke: #2196F3;
  stroke-width: 2;
  fill: none;
}
.pipeline-info {
  margin-top: 20px;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
}
</style>
