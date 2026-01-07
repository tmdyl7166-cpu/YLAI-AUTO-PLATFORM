<template>
  <div>
    <h2>权限管理 (RBAC)</h2>
    <div class="rbac-container">
      <div class="rbac-section">
        <h3>用户管理</h3>
        <div class="user-list">
          <div v-for="user in users" :key="user.id" class="user-item">
            <span>{{ user.name }} ({{ user.role }})</span>
            <button @click="editUser(user)" class="btn-edit">编辑</button>
            <button @click="deleteUser(user.id)" class="btn-delete">删除</button>
          </div>
        </div>
        <button @click="addUser" class="btn-add">添加用户</button>
      </div>
      <div class="rbac-section">
        <h3>角色管理</h3>
        <div class="role-list">
          <div v-for="role in roles" :key="role.id" class="role-item">
            <h4>{{ role.name }}</h4>
            <p>{{ role.description }}</p>
            <div class="permissions">
              <h5>权限:</h5>
              <div class="permission-tags">
                <span v-for="perm in role.permissions" :key="perm" class="permission-tag">{{ perm }}</span>
              </div>
            </div>
            <button @click="editRole(role)" class="btn-edit">编辑</button>
            <button @click="deleteRole(role.id)" class="btn-delete">删除</button>
          </div>
        </div>
        <button @click="addRole" class="btn-add">添加角色</button>
      </div>
      <div class="rbac-section">
        <h3>权限矩阵</h3>
        <table class="permission-matrix">
          <thead>
            <tr>
              <th>资源</th>
              <th v-for="role in roles" :key="role.id">{{ role.name }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="resource in resources" :key="resource.id">
              <td>{{ resource.name }}</td>
              <td v-for="role in roles" :key="role.id">
                <input
                  type="checkbox"
                  :checked="hasPermission(role.id, resource.id)"
                  @change="togglePermission(role.id, resource.id)"
                >
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <SystemSettingsPlaceholder />
    <!-- 用户编辑模态框 -->
    <div v-if="showUserModal" class="modal">
      <div class="modal-content">
        <h3>{{ editingUser ? '编辑用户' : '添加用户' }}</h3>
        import SystemSettingsPlaceholder from '@/components/modules/SystemSettingsPlaceholder.vue'
        <form @submit.prevent="saveUser">
          <div class="form-group">
            <label>用户名:</label>
          components: {
            SystemSettingsPlaceholder
          },
            <input v-model="userForm.name" required>
          </div>
          <div class="form-group">
            <label>角色:</label>
            <select v-model="userForm.roleId" required>
              <option value="">选择角色</option>
              <option v-for="role in roles" :key="role.id" :value="role.id">{{ role.name }}</option>
            </select>
          </div>
          <div class="modal-actions">
            <button type="button" @click="closeUserModal" class="btn-cancel">取消</button>
            <button type="submit" class="btn-save">保存</button>
          </div>
        </form>
      </div>
    </div>
    <!-- 角色编辑模态框 -->
    <div v-if="showRoleModal" class="modal">
      <div class="modal-content">
        <h3>{{ editingRole ? '编辑角色' : '添加角色' }}</h3>
        <form @submit.prevent="saveRole">
          <div class="form-group">
            <label>角色名称:</label>
            <input v-model="roleForm.name" required>
          </div>
          <div class="form-group">
            <label>描述:</label>
            <textarea v-model="roleForm.description"></textarea>
          </div>
          <div class="form-group">
            <label>权限:</label>
            <div class="permission-checkboxes">
              <label v-for="perm in availablePermissions" :key="perm.id">
                <input
                  type="checkbox"
                  :value="perm.id"
                  v-model="roleForm.permissions"
                >
                {{ perm.name }}
              </label>
            </div>
          </div>
          <div class="modal-actions">
            <button type="button" @click="closeRoleModal" class="btn-cancel">取消</button>
            <button type="submit" class="btn-save">保存</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
<script>
export default {
  name: 'RbacPage',
  data() {
    return {
      users: [
        { id: 1, name: 'admin', role: '管理员' },
        { id: 2, name: 'user1', role: '普通用户' },
        { id: 3, name: 'analyst', role: '分析师' }
      ],
      roles: [
        { id: 1, name: '管理员', description: '系统管理员，拥有所有权限', permissions: ['read', 'write', 'delete', 'admin'] },
        { id: 2, name: '普通用户', description: '普通用户，基本读写权限', permissions: ['read', 'write'] },
        { id: 3, name: '分析师', description: '数据分析师，读取和分析权限', permissions: ['read', 'analyze'] }
      ],
      resources: [
        { id: 1, name: '用户数据' },
        { id: 2, name: '系统配置' },
        { id: 3, name: '监控数据' },
        { id: 4, name: 'API接口' }
      ],
      availablePermissions: [
        { id: 'read', name: '读取' },
        { id: 'write', name: '写入' },
        { id: 'delete', name: '删除' },
        { id: 'admin', name: '管理' },
        { id: 'analyze', name: '分析' }
      ],
      rolePermissions: {
        '1-1': true, '1-2': true, '1-3': true, '1-4': true,
        '2-1': true, '2-2': false, '2-3': true, '2-4': false,
        '3-1': true, '3-2': false, '3-3': true, '3-4': true
      },
      showUserModal: false,
      showRoleModal: false,
      editingUser: null,
      editingRole: null,
      userForm: { name: '', roleId: '' },
      roleForm: { name: '', description: '', permissions: [] }
    }
  },
  methods: {
    addUser() {
      this.editingUser = null;
      this.userForm = { name: '', roleId: '' };
      this.showUserModal = true;
    },
    editUser(user) {
      this.editingUser = user;
      this.userForm = { name: user.name, roleId: this.roles.find(r => r.name === user.role)?.id || '' };
      this.showUserModal = true;
    },
    deleteUser(userId) {
      this.users = this.users.filter(u => u.id !== userId);
    },
    saveUser() {
      const role = this.roles.find(r => r.id === this.userForm.roleId);
      if (this.editingUser) {
        this.editingUser.name = this.userForm.name;
        this.editingUser.role = role.name;
      } else {
        this.users.push({
          id: Date.now(),
          name: this.userForm.name,
          role: role.name
        });
      }
      this.closeUserModal();
    },
    closeUserModal() {
      this.showUserModal = false;
    },
    addRole() {
      this.editingRole = null;
      this.roleForm = { name: '', description: '', permissions: [] };
      this.showRoleModal = true;
    },
    editRole(role) {
      this.editingRole = role;
      this.roleForm = { name: role.name, description: role.description, permissions: [...role.permissions] };
      this.showRoleModal = true;
    },
    deleteRole(roleId) {
      this.roles = this.roles.filter(r => r.id !== roleId);
      // 清理权限矩阵
      Object.keys(this.rolePermissions).forEach(key => {
        if (key.startsWith(`${roleId}-`)) {
          delete this.rolePermissions[key];
        }
      });
    },
    saveRole() {
      if (this.editingRole) {
        this.editingRole.name = this.roleForm.name;
        this.editingRole.description = this.roleForm.description;
        this.editingRole.permissions = [...this.roleForm.permissions];
      } else {
        this.roles.push({
          id: Date.now(),
          name: this.roleForm.name,
          description: this.roleForm.description,
          permissions: [...this.roleForm.permissions]
        });
      }
      this.closeRoleModal();
    },
    closeRoleModal() {
      this.showRoleModal = false;
    },
    hasPermission(roleId, resourceId) {
      return this.rolePermissions[`${roleId}-${resourceId}`] || false;
    },
    togglePermission(roleId, resourceId) {
      const key = `${roleId}-${resourceId}`;
      this.rolePermissions[key] = !this.rolePermissions[key];
    }
  }
}
</script>
<style scoped>
.rbac-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.rbac-section {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 20px;
  background-color: #f9f9f9;
}
.rbac-section h3 {
  margin-top: 0;
  color: #333;
}
.user-list, .role-list {
  margin-bottom: 15px;
}
.user-item, .role-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  margin-bottom: 5px;
  background-color: white;
  border-radius: 4px;
}
.role-item {
  flex-direction: column;
  align-items: flex-start;
}
.permissions {
  width: 100%;
  margin: 10px 0;
}
.permission-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.permission-tag {
  background-color: #2196F3;
  color: white;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
}
.btn-add, .btn-edit, .btn-delete, .btn-save, .btn-cancel {
  padding: 5px 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}
.btn-add {
  background-color: #4CAF50;
  color: white;
}
.btn-edit {
  background-color: #ff9800;
  color: white;
}
.btn-delete {
  background-color: #f44336;
  color: white;
}
.btn-save {
  background-color: #2196F3;
  color: white;
}
.btn-cancel {
  background-color: #757575;
  color: white;
}
.permission-matrix {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
}
.permission-matrix th, .permission-matrix td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: center;
}
.permission-matrix th {
  background-color: #f5f5f5;
}
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}
.modal-content {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
}
.modal-content h3 {
  margin-top: 0;
}
.form-group {
  margin-bottom: 15px;
}
.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}
.form-group input, .form-group select, .form-group textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
.form-group textarea {
  height: 80px;
  resize: vertical;
}
.permission-checkboxes {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.permission-checkboxes label {
  display: flex;
  align-items: center;
  cursor: pointer;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}
</style>
