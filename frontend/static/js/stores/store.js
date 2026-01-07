import { defineStore } from 'pinia';

export const useAppStore = defineStore('app', {
  state: () => ({
    user: null,
    tasks: [],
    wsConnected: false,
    crawlerProgress: {}
  }),
  actions: {
    setUser(user) {
      this.user = user;
    },
    addTask(task) {
      this.tasks.push(task);
    },
    updateCrawlerProgress(progress) {
      this.crawlerProgress = { ...this.crawlerProgress, ...progress };
    },
    setWsConnected(connected) {
      this.wsConnected = connected;
    }
  }
});